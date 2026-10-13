"""E3B (README, Pre-registration: E3B): L1 unchanged on XRP and Dogecoin on the older days E3 never downloaded. Rules fixed in the README before that history was downloaded.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

History goes into its OWN database (`data/e3b.sqlite`). Usage: python -m scalper.e3b fetch   then, ONCE:   python -m scalper.e3b run
The pass bar is E3F's (same constants, same function): imported, not copied, so the two cannot drift. This module sets the database path AFTER that import.
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone

from . import altseries as A
from . import e3f
from . import lstrats as L
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalps import STRESS

A.ALT_DB = DATA_DIR / "e3b.sqlite"
SERIES = e3f.SERIES
FLOOR_TS = int(datetime(2026, 9, 3, 20, tzinfo=timezone.utc).timestamp())     # the earliest close in E3's data: nothing on or after it counts
FETCH_DAYS = 69


def fetch() -> None:
    A.ALTS = SERIES
    A.fetch(FETCH_DAYS)


def holdout(entries: list[dict]) -> list[dict]:
    """Only entries on markets that closed strictly before FLOOR_TS, only the registered series."""
    return sorted((e for e in entries if e["series"] in SERIES and e["close_ts"] < FLOOR_TS), key=lambda e: e["close_ts"])


def run() -> None:
    markets, _ = A.load_alts()
    es = holdout(L.hold_rule(markets, **L.L1))
    f = lambda x: f"{x * 100:+.2f}c"
    print(f"{len(markets)} markets in e3b.sqlite; {len(es)} holdout entries on {len({e['day'] for e in es})} days. Signal counts first.\n")
    v, s = e3f.verdict(es)
    if "mean" in s:
        print(f"E3B pooled XRP + DOGE: n={s['n']} on {s['days']} days, net {f(s['mean'])} per contract, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, fees x{STRESS} {f(s['stress'])}, "
              f"minimum detectable edge {f(s['mde'])} -> {v}")
    else:
        print(f"E3B pooled XRP + DOGE: n={s['n']} on {s['days']} days -> {v}")
    print("\nPer series (information):")
    for series in SERIES:
        mine = [e for e in es if e["series"] == series]
        if mine:
            print(f"  {series:<12} n={len(mine):>4} net {f(st.mean(e['net'] for e in mine))} z {cluster_mean_z([(e['day'], e['net']) for e in mine])[2]:+.2f}")


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
