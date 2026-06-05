# Architecture — Contrarian "Dumb Crowd" Trading Bot

> Claude로 어리석은 군중을 연기시키고, 그 반대로 베팅한다. 한투 모의투자 REST 연동.

## Stack
- Runtime: Python 3.11+
- Entry point: CLI (`python src/main.py [--once] [--dry-run]`) — 무인 스케줄 루프
- Deps: `anthropic`, `requests`, `pydantic` (`requirements.txt` → session-start 훅이 설치)
- Deploy target: 장시간 실행 프로세스(로컬/서버/컨테이너). 모의투자라 무인 상시 구동.

## Model Plan
| Call | Model | Reason |
|---|---|---|
| 군중 페르소나 추론 (매 사이클·다종목) | `claude-sonnet-4-6` | 프로젝트 기본 에이전트 루프 모델. 빈번 호출이라 비용/지연이 중요하고, 페르소나 롤플레이+구조화 출력에 충분. 안정 시스템 프롬프트는 prompt caching 적용. |

> 무거운 추론(Opus)은 v0.1 핫패스에 불필요. 군중 신호는 Sonnet 4.6 + 구조화 출력으로 처리.

## Agent Loop (요지)
스케줄러가 장중에 사이클을 깨운다 → 잔고(현금·보유) 1회 조회 → 관심종목 루프:
시세 조회 → **Sonnet 4.6 군중 페르소나**(구조화 출력 `CrowdView`) → 역발상 전략이
매수/매도/보류 결정 + 사이징 → (모의)주문 → 저널 기록. `end_turn`까지 가는 멀티턴
툴 루프가 아니라, **종목당 단일 구조화 호출**이다(분류/추론형이라 1요청-1응답이 적합).

## Tools
LLM 함수콜 툴은 쓰지 않는다. 대신 한투 REST를 코드가 직접 오케스트레이션하고,
LLM 출력은 **structured outputs**(`output_config.format` via `messages.parse` + pydantic)로
강제해 자유형 JSON 파싱을 피한다.

KIS REST 표면 (모의 도메인 `https://openapivts.koreainvestment.com:29443`):
| 기능 | Method · Path | tr_id (모의) |
|---|---|---|
| OAuth 토큰 | `POST /oauth2/tokenP` | — |
| hashkey | `POST /uapi/hashkey` | — |
| 현재가 | `GET /uapi/domestic-stock/v1/quotations/inquire-price` | `FHKST01010100` |
| 일봉(최근 흐름) | `GET .../quotations/inquire-daily-itemchartprice` | `FHKST03010100` |
| 잔고 | `GET .../trading/inquire-balance` | `VTTC8434R` |
| 현금주문 매수 | `POST .../trading/order-cash` | `VTTC0802U` |
| 현금주문 매도 | `POST .../trading/order-cash` | `VTTC0801U` |

## Prompts
- **System prompt** (`crowd.py` `CROWD_SYSTEM`): "당신은 전형적인 한국 개미 군중이다 —
  고점 추격, 저점 투매, 뉴스에 늦게 반응…" 페르소나 + 출력 규칙. **안정(stable)** 텍스트라
  `cache_control: {type: "ephemeral"}`로 캐싱. (Sonnet 4.6 최소 캐시 프리픽스 ~2048토큰 —
  미달 시 무비용 무시.)
- **User turn**: 종목별 변동 데이터(코드/현재가/등락%/거래량/최근 5일). 캐시 브레이크포인트 뒤.
- **Cache layout**: system 블록 1개에 브레이크포인트. tools 없음.

## Data
- 토큰: `.kis_token.json` 파일 캐시 (모의 발급 분당 제한 회피). gitignore.
- 저널: `journal.db` (SQLite). 한 테이블 `decisions`에 시세·군중신호·결정·주문번호·상태 기록.
- 영속 상태는 위 둘뿐. 포지션/현금은 매 사이클 한투 잔고에서 새로 읽는다(소스 오브 트루스).

## Risks
- **토큰 발급 제한/만료**: 모의 토큰은 분당 1회 제한 → 파일 캐시 + 만료 600초 전 갱신.
  관찰: 인증 401 시 즉시 로그.
- **구조화 출력 일탈**: 모델이 스키마/임계치를 벗어남 → `messages.parse`로 스키마 강제,
  `conviction`은 0–100 정수. 결정 로직이 임계치로 한 번 더 필터.
- **휴장일/장 마감 직전 주문 거부**: 주말만 거르고 공휴일 미처리(알려진 한계) + 시장가
  주문이 장 마감 직후 거부될 수 있음 → rt_cd 비정상 시 저널에 실패 상태로 남기고 계속.
