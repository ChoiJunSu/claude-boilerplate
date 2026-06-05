"""One trading cycle: read account → per ticker (price → crowd → contrarian
decision → order) → journal. The cycle is the unit the scheduler repeats.
"""

import time

from anthropic import Anthropic

import config
import crowd
import strategy
from journal import Journal
from kis_client import KisClient


def run_cycle(
    client: Anthropic,
    kis: KisClient,
    settings: config.Settings,
    journal: Journal,
    dry_run: bool,
) -> None:
    risk = settings.risk
    balance = kis.get_balance()
    cash = balance.cash
    holdings = dict(balance.holdings)
    print(f"[cycle] 현금 {cash:,}원, 보유 {len(holdings)}종목 "
          f"{'(DRY-RUN)' if dry_run else ''}")

    for code, name in config.WATCHLIST:
        snap = kis.get_price(code, name)
        candles = kis.get_daily(code)
        view = crowd.assess(client, snap, candles)
        decision = strategy.decide(
            view, snap, holdings.get(code, 0), cash, len(holdings), risk
        )

        order_no, status = "", "planned"
        if decision.side in ("buy", "sell") and decision.qty > 0:
            if dry_run:
                status = "dry_run"
            else:
                result = kis.place_order(code, decision.side, decision.qty)
                order_no = result.order_no
                status = "filled" if result.ok else f"rejected:{result.message}"
                if result.ok:
                    _apply_fill(holdings, decision, snap)
                    cash += _cash_delta(decision, snap)
        else:
            status = "hold"

        journal.record(snap, view, decision, order_no, status)
        print(f"  {name}({code}) {snap.change_pct:+.2f}% | "
              f"군중 {view.urge}/{view.conviction}({view.emotion}) → "
              f"{decision.side} {decision.qty} [{status}]")
        time.sleep(0.3)  # gentle on KIS rate limits


def _apply_fill(holdings: dict, decision: strategy.Decision, snap) -> None:
    if decision.side == "buy":
        holdings[decision.code] = holdings.get(decision.code, 0) + decision.qty
    elif decision.side == "sell":
        remaining = holdings.get(decision.code, 0) - decision.qty
        if remaining > 0:
            holdings[decision.code] = remaining
        else:
            holdings.pop(decision.code, None)


def _cash_delta(decision: strategy.Decision, snap) -> int:
    # Market-order fill price is approximated by last price for local bookkeeping.
    if decision.side == "buy":
        return -decision.qty * snap.price
    return decision.qty * snap.price
