"""Static config for the contrarian trading bot.

Secrets come from environment variables (set as GitHub repo/codespace secrets in
the sandbox, or a local .env you source yourself). Required:

    ANTHROPIC_API_KEY     # used implicitly by the Anthropic SDK
    KIS_APP_KEY           # 한국투자증권 OpenAPI appkey (모의투자용)
    KIS_APP_SECRET        # 〃 appsecret
    KIS_ACCOUNT_NO        # 모의 계좌번호 앞 8자리 (CANO)

Optional:
    KIS_ACCOUNT_PRODUCT   # 계좌상품코드 뒤 2자리 (default "01")
"""

import os
from dataclasses import dataclass, field

# --- KIS 모의투자(paper) endpoints ------------------------------------------
# 실전이 아니라 모의 도메인만 쓴다. 금전 리스크 0.
BASE_URL = "https://openapivts.koreainvestment.com:29443"

TR_PRICE = "FHKST01010100"   # 주식 현재가 시세
TR_DAILY = "FHKST03010100"   # 국내주식 기간별 시세(일/주/월)
TR_BALANCE = "VTTC8434R"     # 주식 잔고조회 (모의)
TR_ORDER_BUY = "VTTC0802U"   # 현금 매수 주문 (모의)
TR_ORDER_SELL = "VTTC0801U"  # 현금 매도 주문 (모의)

TOKEN_CACHE_PATH = ".kis_token.json"
DB_PATH = "journal.db"

# --- Models -----------------------------------------------------------------
# 프로젝트 기본 에이전트 루프 모델. 매 사이클·다종목 반복 호출이라 비용/지연이 중요.
CROWD_MODEL = "claude-sonnet-4-6"

# --- Watchlist: ISA에서 거래 가능한 국내 상장 주식 · ETF -----------------------
# (종목코드 6자리, 표시명). 유동성 높은 대형주/대표 ETF 위주.
WATCHLIST = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
    ("035720", "카카오"),
    ("005380", "현대차"),
    ("069500", "KODEX 200"),
    ("229200", "KODEX 코스닥150"),
]


@dataclass(frozen=True)
class Risk:
    max_positions: int = 5          # 동시 보유 종목 수 상한
    max_trade_krw: int = 1_000_000  # 1회 매수 금액 상한
    max_position_pct: float = 0.20  # 1회 매수에 현금의 최대 비율
    min_cash_krw: int = 100_000     # 이 아래로 현금을 깎는 매수는 안 함
    conviction_threshold: int = 60  # 대중 확신이 이 이상일 때만 역베팅


@dataclass(frozen=True)
class Settings:
    app_key: str
    app_secret: str
    account_no: str
    account_product: str
    cycle_interval_sec: int = 600   # 사이클 주기(초)
    risk: Risk = field(default_factory=Risk)


def load_settings() -> Settings:
    """Read secrets from env. Fails loud if a required one is missing (edge)."""
    missing = [
        k for k in ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NO")
        if not os.environ.get(k)
    ]
    if missing:
        raise SystemExit(f"missing required env vars: {', '.join(missing)}")
    return Settings(
        app_key=os.environ["KIS_APP_KEY"],
        app_secret=os.environ["KIS_APP_SECRET"],
        account_no=os.environ["KIS_ACCOUNT_NO"],
        account_product=os.environ.get("KIS_ACCOUNT_PRODUCT", "01"),
    )
