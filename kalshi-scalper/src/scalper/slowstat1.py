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


MIN_EVENTS_FOR_SD = 12      # sd needs 8 changes in the first two thirds of events: 12 events
CUTS = CUT.strftime("%Y-%m-%dT%H:%M:%SZ")


def cap(rows, min_volume: float = MIN_VOLUME) -> dict:
    """rows: (event_ticker, close_time, volume) of one series. Upper bound on SCORED trades: the series needs MIN_EVENTS_FOR_SD events for an sd
    from the first two thirds; only markets of the last third of events (by close time) that traded at least min_volume can be scored."""
    first = {}
    for e, c, _ in rows:
        first[e] = min(c, first.get(e, c))
    names = sorted(first, key=lambda e: (first[e], e))
    if len(names) < MIN_EVENTS_FOR_SD:
        return {"events": len(names), "scored_events": 0, "scored_markets": 0}
    scored = set(names[2 * (len(names) // 3):])
    ok = [(e, v) for e, c, v in rows if e in scored and v >= min_volume]
    return {"events": len(names), "scored_events": len({e for e, _ in ok}), "scored_markets": len(ok)}


def verdict(total_cap: int) -> str:
    return "NOT_RUNNABLE" if total_cap < MIN_TRADES else "RUNNABLE"


def listing(series: str) -> list:
    out = {}
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cur = None
        while True:
            p = {"series_ticker": series, "limit": 1000, "max_close_ts": int(CUT.timestamp()), **extra, **({"cursor": cur} if cur else {})}
            d = api._get(path, p)
            for m in d.get("markets", []):
                if m.get("result") in ("yes", "no") and (m.get("close_time") or "") < CUTS:
                    out[m["ticker"]] = (m["event_ticker"], m["close_time"], float(m.get("volume_fp") or 0))
            cur = d.get("cursor")
            if not cur or not d.get("markets"):
                break
    return list(out.values())


def census() -> None:
    tot = 0
    for s in SERIES:
        rows = listing(s)
        c = cap(rows); tot += c["scored_markets"]
        print(s, len(rows), "markets;", c, flush=True)
    print("total cap on scored markets", tot, verdict(tot))


if __name__ == "__main__":
    census() if sys.argv[1:] == ["census"] else print(__doc__)
