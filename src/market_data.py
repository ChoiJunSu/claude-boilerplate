"""Market data shapes + parsing of raw KIS JSON, and crowd-input formatting.

Kept separate from the HTTP client so the LLM-facing text builder has no
network concerns.
"""

from dataclasses import dataclass, field


def _i(s) -> int:
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return 0


def _f(s) -> float:
    try:
        return float(s)
    except (TypeError, ValueError):
        return 0.0


@dataclass
class PriceSnapshot:
    code: str
    name: str
    price: int
    change: int
    change_pct: float
    volume: int
    day_open: int
    day_high: int
    day_low: int
    w52_high: int
    w52_low: int


@dataclass
class Candle:
    date: str
    close: int
    volume: int


@dataclass
class Balance:
    cash: int
    holdings: dict = field(default_factory=dict)  # code -> qty


def parse_price(code: str, name: str, output: dict) -> PriceSnapshot:
    pct = _f(output.get("prdy_ctrt"))
    if output.get("prdy_vrss_sign") in ("4", "5"):  # 하한/하락
        pct = -abs(pct)
    return PriceSnapshot(
        code=code,
        name=name or output.get("hts_kor_isnm", code),
        price=_i(output.get("stck_prpr")),
        change=_i(output.get("prdy_vrss")),
        change_pct=pct,
        volume=_i(output.get("acml_vol")),
        day_open=_i(output.get("stck_oprc")),
        day_high=_i(output.get("stck_hgpr")),
        day_low=_i(output.get("stck_lwpr")),
        w52_high=_i(output.get("w52_hgpr")),
        w52_low=_i(output.get("w52_lwpr")),
    )


def parse_candles(output2: list) -> list:
    candles = []
    for row in output2 or []:
        if not row.get("stck_bsop_date"):
            continue
        candles.append(Candle(
            date=row["stck_bsop_date"],
            close=_i(row.get("stck_clpr")),
            volume=_i(row.get("acml_vol")),
        ))
    return candles  # newest-first as KIS returns


def parse_balance(output1: list, output2: list) -> Balance:
    holdings = {}
    for row in output1 or []:
        qty = _i(row.get("hldg_qty"))
        if qty > 0:
            holdings[row.get("pdno", "")] = qty
    cash = _i(output2[0].get("dnca_tot_amt")) if output2 else 0
    return Balance(cash=cash, holdings=holdings)


def format_for_crowd(snap: PriceSnapshot, candles: list) -> str:
    """Render the volatile per-ticker context the crowd persona reasons over."""
    lines = [
        f"종목: {snap.name} ({snap.code})",
        f"현재가: {snap.price:,}원  (전일대비 {snap.change:+,}원, {snap.change_pct:+.2f}%)",
        f"오늘 시가/고가/저가: {snap.day_open:,} / {snap.day_high:,} / {snap.day_low:,}",
        f"누적 거래량: {snap.volume:,}주",
    ]
    if snap.w52_high and snap.w52_low:
        span = max(snap.w52_high - snap.w52_low, 1)
        pos = (snap.price - snap.w52_low) / span * 100
        lines.append(
            f"52주 고/저: {snap.w52_high:,} / {snap.w52_low:,}  "
            f"(현재가는 52주 밴드의 {pos:.0f}% 지점)"
        )
    recent = candles[:5]  # newest-first
    if len(recent) >= 2:
        old, new = recent[-1].close, recent[0].close
        trend = (new - old) / max(old, 1) * 100
        seq = " → ".join(f"{c.close:,}" for c in reversed(recent))
        lines.append(f"최근 {len(recent)}거래일 종가: {seq}  (구간 {trend:+.1f}%)")
    return "\n".join(lines)
