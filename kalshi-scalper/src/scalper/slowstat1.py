"""SLOWSTAT1 (workers/SLOWSTAT1_REGISTRATION.md): cheap side brackets on slow public statistics. Research only; nothing here means trade.
    python -m scalper.slowstat1 census   market and event counts and volumes only (no result, no price, no candle) before 2026-10-03T16:00Z
The scored rule was not run: cap() shows the trade count cannot reach the 150 minimum. Verdict word: NOT_RUNNABLE."""
from __future__ import annotations

import collections
import sys
from datetime import datetime, timezone

from . import api

CUT = datetime(2026, 10, 3, 16, tzinfo=timezone.utc)
MIN_TRADES, MIN_VOLUME = 150, 20.0
SERIES = ["KXADP", "KXEGGS", "KXTEMPHELP", "KXDATACENTCON", "KXUSDINRAW", "KXCHIPBURRITO", "KXDDCOLDBREW", "KXTBCRUNCHWRAP", "KXSBUXSAR",
          "KXPOWERKWH", "KXUSHOME", "KXNFCI", "KXCFNAI", "KX10YRDIRHM"]


def cap(rows, min_volume: float = MIN_VOLUME) -> dict:
    """rows: (event_ticker, volume). Upper bound on trades: markets that traded at least min_volume; and the events they sit on."""
    ok = [(e, v) for e, v in rows if v >= min_volume]
    return {"markets": len(ok), "events": len({e for e, _ in ok})}


def verdict(total_cap: int) -> str:
    return "NOT_RUNNABLE" if total_cap < MIN_TRADES else "RUNNABLE"


def census() -> None:
    lo, hi = 0, int(CUT.timestamp())
    tot = 0
    for s in SERIES:
        rows = [(m["event_ticker"], float(m.get("volume_fp") or 0)) for m in api.settled_markets(s, lo, hi)
                if (m.get("close_time") or "") < CUT.strftime("%Y-%m-%dT%H:%M:%SZ")]
        c = cap(rows); tot += c["markets"]
        print(s, len(rows), "markets;", c)
    print("total cap", tot, verdict(tot))


if __name__ == "__main__":
    census() if sys.argv[1:] == ["census"] else print(__doc__)
