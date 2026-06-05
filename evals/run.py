"""Eval runner for the contrarian bot.

Two layers:
  1. strategy_cases.jsonl — deterministic. Feeds a fixed CrowdView + account
     state through strategy.decide and checks the contrarian side. No API.
  2. crowd_cases.jsonl    — the Claude persona. Feeds a market snapshot through
     crowd.assess and checks the crowd's urge. Needs ANTHROPIC_API_KEY; the
     persona is generative so treat misses as soft signal, not hard failure.

Run: python evals/run.py
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import config  # noqa: E402
import strategy  # noqa: E402
from crowd import CrowdView  # noqa: E402
from market_data import Candle, PriceSnapshot  # noqa: E402

HERE = Path(__file__).resolve().parent


def _load(name):
    with open(HERE / name) as f:
        return [json.loads(line) for line in f if line.strip()]


def run_strategy() -> tuple[int, int]:
    risk = config.Risk()
    passed = 0
    cases = _load("strategy_cases.jsonl")
    print("== strategy (contrarian logic) ==")
    for c in cases:
        view = CrowdView(urge=c["view"]["urge"], conviction=c["view"]["conviction"],
                         emotion="?", one_liner="?")
        snap = PriceSnapshot("000000", "TEST", c["price"], 0, 0.0, 0, 0, 0, 0, 0, 0)
        got = strategy.decide(view, snap, c["holding_qty"], c["cash"],
                              c["num_positions"], risk).side
        ok = got == c["expect_side"]
        passed += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {c['name']}: "
              f"expected {c['expect_side']}, got {got}")
    print(f"  → {passed}/{len(cases)} passed\n")
    return passed, len(cases)


def run_crowd() -> tuple[int, int]:
    cases = _load("crowd_cases.jsonl")
    print("== crowd (Claude persona) ==")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("  skipped (no ANTHROPIC_API_KEY)\n")
        return 0, 0
    from anthropic import Anthropic
    import crowd
    client = Anthropic()
    passed = 0
    for c in cases:
        s = c["snap"]
        snap = PriceSnapshot(s["code"], s["name"], s["price"], s["change"],
                             s["change_pct"], s["volume"], s["day_open"],
                             s["day_high"], s["day_low"], s["w52_high"], s["w52_low"])
        candles = [Candle(d, close, 0) for d, close in c["candles"]]
        view = crowd.assess(client, snap, candles)
        ok = view.urge == c["expect_urge"]
        passed += ok
        print(f"  [{'PASS' if ok else 'MISS'}] {c['name']}: "
              f"expected {c['expect_urge']}, got {view.urge} "
              f"(conv {view.conviction}, {view.emotion})")
    print(f"  → {passed}/{len(cases)} matched\n")
    return passed, len(cases)


if __name__ == "__main__":
    sp, st = run_strategy()
    cp, ct = run_crowd()
    print(f"summary: strategy {sp}/{st}, crowd {cp}/{ct}")
    # Only the deterministic layer gates the exit code.
    sys.exit(0 if sp == st else 1)
