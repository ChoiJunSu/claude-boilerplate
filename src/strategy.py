"""Contrarian decision layer: bet against the crowd's conviction.

Crowd euphorically buying  → we sell into strength (or stay out).
Crowd panic-selling        → we buy the dip they're dumping.
Anything lukewarm          → hold.
"""

from dataclasses import dataclass

import config
import market_data as md
from crowd import CrowdView


@dataclass
class Decision:
    code: str
    name: str
    side: str   # "buy" | "sell" | "hold"
    qty: int
    reason: str


def decide(
    view: CrowdView,
    snap: md.PriceSnapshot,
    holding_qty: int,
    cash: int,
    num_positions: int,
    risk: config.Risk,
) -> Decision:
    name = snap.name
    strong = view.conviction >= risk.conviction_threshold

    # 대중이 확신에 차 패닉 매도 → 우리는 줍는다.
    if view.urge == "panic_sell" and strong:
        if holding_qty > 0:
            return Decision(snap.code, name, "hold", 0,
                            f"대중 패닉(conv {view.conviction}) 역베팅 매수 대상이나 이미 보유 중")
        if num_positions >= risk.max_positions:
            return Decision(snap.code, name, "hold", 0,
                            f"대중 패닉이지만 보유 종목 한도({risk.max_positions}) 도달")
        budget = min(risk.max_trade_krw, int(cash * risk.max_position_pct))
        if cash - budget < risk.min_cash_krw or snap.price <= 0:
            return Decision(snap.code, name, "hold", 0, "대중 패닉이지만 현금 여력 부족")
        qty = budget // snap.price
        if qty < 1:
            return Decision(snap.code, name, "hold", 0, "대중 패닉이지만 1주 매수 예산 미달")
        return Decision(snap.code, name, "buy", qty,
                        f"대중 패닉매도(conv {view.conviction}, {view.emotion}) → 역발상 매수")

    # 대중이 확신에 차 FOMO 매수 → 우리는 강세에 판다(공매도 불가, 보유분만 정리).
    if view.urge == "fomo_buy" and strong:
        if holding_qty > 0:
            return Decision(snap.code, name, "sell", holding_qty,
                            f"대중 FOMO 추격(conv {view.conviction}, {view.emotion}) → 강세에 보유분 매도")
        return Decision(snap.code, name, "hold", 0,
                        f"대중 FOMO지만 미보유(공매도 안 함) → 관망")

    return Decision(snap.code, name, "hold", 0,
                    f"대중 충동 약함(urge {view.urge}, conv {view.conviction}) → 관망")
