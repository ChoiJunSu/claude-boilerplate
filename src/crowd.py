"""The "dumb crowd" persona: Claude role-plays the foolish retail herd and
emits a structured read of what the crowd would do right now. The strategy
layer then bets against it.
"""

from typing import Literal

from anthropic import Anthropic
from pydantic import BaseModel

import config
import market_data as md

# Stable system prompt → cached. Describes the persona and the output contract.
CROWD_SYSTEM = """\
당신은 한국 주식시장의 '전형적인 개미 군중'을 연기합니다. 이 군중은 똑똑하지 않고,
거의 항상 최악의 타이밍에 움직입니다. 당신의 임무는 '옳은 판단'이 아니라, 지금 이
종목 앞에서 **이 어리석은 군중이 실제로 무엇을 하고 싶어 할지**를 솔직하게 재현하는 것입니다.

군중의 본성:
- 오르면 더 오를까 봐 고점에서 추격 매수(FOMO)한다. 빨간불에 흥분한다.
- 내리면 더 내릴까 봐 저점에서 공포에 투매(패닉 매도)한다. 파란불에 절망한다.
- 거래량이 터지고 급등/급락할수록 감정이 증폭된다.
- 52주 신고가 근처면 "이번엔 다르다"며 달려들고, 신저가 근처면 "끝났다"며 던진다.
- 횡보하거나 따분하면 무관심하게 관망한다.

규칙:
- 데이터에 근거해 군중의 '충동(urge)'과 그 '확신 강도(conviction, 0-100)'를 판단하라.
- urge: 강하게 사고 싶으면 fomo_buy, 강하게 팔고 싶으면 panic_sell, 미적지근하면 hold.
- conviction: 군중이 그 충동에 얼마나 휩쓸려 있는지. 애매하면 낮게(0-40), 광기면 높게(80+).
- emotion: 군중의 감정을 한 단어로 (예: 탐욕, 공포, 무관심, 환희, 절망).
- one_liner: 군중이 종목토론방에 쓸 법한 한 줄 (반말, 과장된 어조).
- 당신은 군중을 '연기'할 뿐, 올바른 투자 판단을 하지 마라."""


class CrowdView(BaseModel):
    urge: Literal["fomo_buy", "panic_sell", "hold"]
    conviction: int  # 0-100, 군중이 충동에 휩쓸린 정도
    emotion: str
    one_liner: str


def assess(client: Anthropic, snap: md.PriceSnapshot, candles: list) -> CrowdView:
    user_text = (
        "아래 종목 데이터를 보고, 지금 어리석은 개미 군중이 무엇을 하고 싶어 할지 판단해줘.\n\n"
        + md.format_for_crowd(snap, candles)
    )
    resp = client.messages.parse(
        model=config.CROWD_MODEL,
        max_tokens=1024,
        system=[{
            "type": "text",
            "text": CROWD_SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_text}],
        output_format=CrowdView,
    )
    return resp.parsed_output
