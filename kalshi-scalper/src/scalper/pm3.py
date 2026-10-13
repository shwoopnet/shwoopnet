"""PM3 (README, Pre-registration: PM3): the Polymarket-disagreement filter on L1 entries, on days after 2026-10-13. Rules fixed in the README before any such day existed.
Research only: nothing here places an order and the Polymarket API is only read. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Kalshi windows come from `data/fwd1.sqlite` (FWD1's download), Polymarket prices go into `data/pm3.sqlite`. The flag is PM2's (`pm2.entries`) and the bar is VOL1's verdict function
(skipped mean below zero and below the kept mean in the whole sample and in both halves, improvement above the permutation 95th percentile), with 100 as the minimum skipped.
Usage: python -m scalper.pm3 fetch   then, ONCE, on or after 2026-11-16:   python -m scalper.pm3 run
"""
from __future__ import annotations

import sqlite3
import statistics as st
import sys
import time

from . import fwd1
from . import pm1
from . import pm2
from . import vol1
from .paths import DATA_DIR

SRC_DB = DATA_DIR / "fwd1.sqlite"
PM3_DB = DATA_DIR / "pm3.sqlite"
START_TS = fwd1.START_TS
EARLIEST_READ_TS = fwd1.EARLIEST_READ_TS
MIN_SKIPPED = 100


def windows() -> list[dict]:
    """Kalshi Bitcoin and Ethereum windows from the forward download, closing on or after START_TS only."""
    return [w for w in pm1.windows(SRC_DB) if w["close_ts"] >= START_TS]


def fetch() -> None:
    pm1.fetch_windows(PM3_DB, windows())


def run(now_ts: int | None = None) -> None:
    now = int(time.time()) if now_ts is None else now_ts
    if now < EARLIEST_READ_TS:
        print("Too early: the registered single read is on or after 2026-11-16. Not run; nothing recorded.")
        return
    wins = windows()
    pm = sqlite3.connect(PM3_DB)
    pts: dict = {}
    for s, t, p in pm.execute("SELECT slug, t, p FROM pt"):
        pts.setdefault(s, []).append((t, p))
    es = pm2.entries(pm1.observations(wins, pts))
    print(f"{len(wins)} forward Kalshi windows with a quote, {len(es)} L1 entries with a recent Polymarket point on {len({e['day'] for e in es})} days. Signal counts first.\n")
    v, s = vol1.verdict(es, pm2.null_improvements(es) if es else [], min_skipped=MIN_SKIPPED)
    c = lambda x: f"{x * 100:+.2f}c" if x is not None else "n/a"
    if "skipped_mean" in s:
        print(f"PM3: skipped {s['skipped']} of {len(es)} entries; skipped mean net {c(s['skipped_mean'])}, kept mean net {c(s['kept_mean'])}; improvement {c(s['imp'])} per entry, permutation 95th percentile {c(s['p95'])}")
        print(f"    halves (skipped / kept): {c(s['gaps'][0][0])} / {c(s['gaps'][0][1])} and {c(s['gaps'][1][0])} / {c(s['gaps'][1][1])}")
    else:
        print(f"PM3: skipped {s['skipped']}, kept {s['kept']} on {s['days']} days")
    print(f"    -> {v}")
    for series in pm1.ASSETS:
        for name, flag in (("skipped", True), ("kept", False)):
            g = [e for e in es if e["series"] == series and e["skip"] == flag]
            if g:
                print(f"    {series} {name}: n={len(g)} loss rate {sum(1 for e in g if e['net'] < 0) / len(g):.1%} mean net {c(st.mean(e['net'] for e in g))} (information only)")


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
