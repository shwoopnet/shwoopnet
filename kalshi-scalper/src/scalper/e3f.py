"""E3F (README, Pre-registration: E3F): the one forward read of L1 unchanged on XRP and Dogecoin, on days after the E3 result was seen. Rules fixed in the README before any such day existed.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

History goes into its OWN database (`data/e3f.sqlite`). Usage: python -m scalper.e3f fetch   then, ONCE, on or after 2026-11-16:   python -m scalper.e3f run
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone

from . import altseries as A
from . import lstrats as L
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalps import STRESS

A.ALT_DB = DATA_DIR / "e3f.sqlite"
SERIES = ("KXXRP15M", "KXDOGE15M")
START_TS = int(datetime(2026, 10, 14, tzinfo=timezone.utc).timestamp())      # the first day that did not exist when E3 was read
EARLIEST_READ_TS = int(datetime(2026, 11, 16, tzinfo=timezone.utc).timestamp())
MIN_ENTRIES = 500
MIN_DAYS = 10
Z_BAR = 2.1
FETCH_DAYS = 60


def fetch() -> None:
    A.ALTS = SERIES
    A.fetch(FETCH_DAYS)


def forward(entries: list[dict]) -> list[dict]:
    """Only entries on markets that closed on or after START_TS, only the registered series."""
    return sorted((e for e in entries if e["series"] in SERIES and e["close_ts"] >= START_TS), key=lambda e: e["close_ts"])


def verdict(es: list[dict]) -> tuple[str, dict]:
    days = sorted({e["day"] for e in es})
    if len(es) < MIN_ENTRIES or len(days) < MIN_DAYS:
        return "NOT_ENOUGH_DATA", {"n": len(es), "days": len(days)}
    mean, se, z = cluster_mean_z([(e["day"], e["net"]) for e in es])
    mid = days[len(days) // 2]
    h1 = [e["net"] for e in es if e["day"] < mid]
    h2 = [e["net"] for e in es if e["day"] >= mid]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    stress = sum(e["stress"] for e in es) / len(es)
    ok = mean > 0 and z >= Z_BAR and m1 > 0 and m2 > 0 and stress > 0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": len(es), "days": len(days), "mean": mean, "z": z, "h1": m1, "h2": m2, "stress": stress, "mde": Z_BAR * se}


def run(now_ts: int | None = None) -> None:
    import time
    now = int(time.time()) if now_ts is None else now_ts
    if now < EARLIEST_READ_TS:
        print(f"Too early: the registered single read is on or after 2026-11-16. Not run; nothing recorded.")
        return
    markets, _ = A.load_alts()
    es = forward(L.hold_rule(markets, **L.L1))
    f = lambda x: f"{x * 100:+.2f}c"
    print(f"{len(markets)} markets in e3f.sqlite; {len(es)} forward entries on {len({e['day'] for e in es})} days. Signal counts first.\n")
    v, s = verdict(es)
    if "mean" in s:
        print(f"E3F pooled XRP + DOGE: n={s['n']} on {s['days']} days, net {f(s['mean'])} per contract, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, fees x{STRESS} {f(s['stress'])}, "
              f"minimum detectable edge {f(s['mde'])} -> {v}")
    else:
        print(f"E3F pooled XRP + DOGE: n={s['n']} on {s['days']} days -> {v}")
    print("\nPer series (information):")
    for series in SERIES:
        mine = [e for e in es if e["series"] == series]
        if mine:
            print(f"  {series:<12} n={len(mine):>4} net {f(st.mean(e['net'] for e in mine))} z {cluster_mean_z([(e['day'], e['net']) for e in mine])[2]:+.2f}")


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
