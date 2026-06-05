"""Entry point. Autonomous scheduler that runs the contrarian cycle during
Korean market hours — no human in the loop.

    python src/main.py            # run forever, gated to market hours (KST)
    python src/main.py --once     # run a single cycle now (cron / testing)
    python src/main.py --dry-run  # compute + journal decisions, place no orders

Weekends are skipped. KRX public holidays are NOT handled (known v0.1 limit) —
orders simply get rejected on a closed day and are journaled as such.
"""

import argparse
import time
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from anthropic import Anthropic

import config
import trader
from journal import Journal
from kis_client import KisClient

KST = ZoneInfo("Asia/Seoul")
MARKET_OPEN = dtime(9, 0)
MARKET_CLOSE = dtime(15, 30)


def market_is_open(now: datetime) -> bool:
    if now.weekday() >= 5:  # Sat/Sun
        return False
    return MARKET_OPEN <= now.time() <= MARKET_CLOSE


def main() -> None:
    ap = argparse.ArgumentParser(description="Contrarian dumb-crowd trading bot")
    ap.add_argument("--once", action="store_true", help="run a single cycle and exit")
    ap.add_argument("--dry-run", action="store_true", help="don't place real orders")
    args = ap.parse_args()

    settings = config.load_settings()
    client = Anthropic()
    kis = KisClient(settings)
    journal = Journal()

    if args.once:
        trader.run_cycle(client, kis, settings, journal, args.dry_run)
        return

    print(f"[bot] started. interval={settings.cycle_interval_sec}s, "
          f"dry_run={args.dry_run}. 장중에만 거래합니다 (09:00-15:30 KST).")
    while True:
        now = datetime.now(KST)
        if market_is_open(now):
            try:
                trader.run_cycle(client, kis, settings, journal, args.dry_run)
            except Exception as e:  # one bad cycle shouldn't kill the bot
                print(f"[bot] cycle error: {e}")
            time.sleep(settings.cycle_interval_sec)
        else:
            print(f"[bot] {now:%Y-%m-%d %H:%M} KST 장 마감/휴장 — 대기")
            time.sleep(300)


if __name__ == "__main__":
    main()
