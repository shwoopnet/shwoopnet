"""FWD1 (README, Pre-registration: FWD1): the live series (Bitcoin, Ethereum, gold) under L1 unchanged, on days after 2026-10-13. Rules fixed in the README before any such day existed.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

History goes into its OWN database (`data/fwd1.sqlite`). The pass bar is E3F's function, imported. Usage: python -m scalper.fwd1 fetch   then, ONCE, on or after 2026-11-16:   python -m scalper.fwd1 run
"""
from __future__ import annotations

import math
import statistics as st
import sys
import time

from . import altseries as A
from . import e3f
from . import lstrats as L
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalps import STRESS

A.ALT_DB = DATA_DIR / "fwd1.sqlite"
SERIES = ("KXBTC15M", "KXETH15M", "KXGOLD15M")
START_TS = e3f.START_TS
EARLIEST_READ_TS = e3f.EARLIEST_READ_TS


def fetch_days(now: int | None = None) -> int:
    """Days back that cover START_TS, plus one."""
    now = int(time.time()) if now is None else now
    return max(2, math.ceil((now - START_TS) / 86400) + 1)


def fetch() -> None:
    A.ALTS = SERIES
    A.fetch(fetch_days())


def forward(entries: list[dict]) -> list[dict]:
    return sorted((e for e in entries if e["series"] in SERIES and e["close_ts"] >= START_TS), key=lambda e: e["close_ts"])


def run(now_ts: int | None = None) -> None:
    now = int(time.time()) if now_ts is None else now_ts
    if now < EARLIEST_READ_TS:
        print("Too early: the registered single read is on or after 2026-11-16. Not run; nothing recorded.")
        return
    markets, _ = A.load_alts()
    es = forward(L.hold_rule(markets, **L.L1))
    f = lambda x: f"{x * 100:+.2f}c"
    print(f"{len(markets)} markets in fwd1.sqlite; {len(es)} forward entries on {len({e['day'] for e in es})} days. Signal counts first.\n")
    v, s = e3f.verdict(es)
    if "mean" in s:
        print(f"FWD1 pooled Bitcoin + Ethereum + gold: n={s['n']} on {s['days']} days, net {f(s['mean'])} per contract, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, fees x{STRESS} {f(s['stress'])}, "
              f"minimum detectable edge {f(s['mde'])} -> {v}")
    else:
        print(f"FWD1 pooled: n={s['n']} on {s['days']} days -> {v}")
    print("\nPer series (information):")
    for series in SERIES:
        mine = [e for e in es if e["series"] == series]
        if mine:
            print(f"  {series:<10} n={len(mine):>4} net {f(st.mean(e['net'] for e in mine))} z {cluster_mean_z([(e['day'], e['net']) for e in mine])[2]:+.2f}")


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
