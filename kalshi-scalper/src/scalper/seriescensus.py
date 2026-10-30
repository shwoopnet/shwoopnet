"""Weekly census of Kalshi's 15 minute series (NEWH17 step 3, 2026-10-30). Public API, counts only, no outcome is read.

Once every 7 days it lists /series (frequency fifteen_min) and, for each series, asks whether Kalshi has ever settled one of its markets
(one market, `limit=1`, only for series not yet known to have settled ones). It prints ONE line: the number of fifteen_min series, how many
have at least one settled market, and the names of series that had none at the last census and have one now. A change begins the line with
"NEW SERIES" so it stands out in workers/AUTO_LOG.md. The state (a dict of series -> has settled) lives in the same state file as autoscore
(data/autoscore_state.json, key "series_census"), passed in and out by the caller. Every error is caught: a failed census returns a line
that says so and leaves the state alone (it is tried again on the next pass).
"""
from __future__ import annotations

import time

PERIOD_S = 7 * 24 * 3600
KEY = "series_census"


def _list_series() -> list[str]:
    from .api import _get
    r = _get("/series", {})
    return sorted(s["ticker"] for s in r.get("series", []) if s.get("frequency") == "fifteen_min" and s.get("ticker"))


def _has_settled(ticker: str) -> bool:
    from .api import _get
    r = _get("/markets", {"series_ticker": ticker, "status": "settled", "limit": 1})
    return bool(r.get("markets"))


def due(s: dict, now: float | None = None) -> bool:
    c = s.get(KEY) or {}
    return (now if now is not None else time.time()) - float(c.get("at", 0)) >= PERIOD_S


def census(s: dict, now: float | None = None, list_fn=None, settled_fn=None) -> str | None:
    """Run the census if due. Mutates s[KEY] on success. Returns the log line, or None when not due. Never raises."""
    now = now if now is not None else time.time()
    if not due(s, now):
        return None
    try:
        tickers = (list_fn or _list_series)()
        prev = (s.get(KEY) or {}).get("has") or {}
        first = not prev
        has, new = {}, []
        for t in tickers:
            if prev.get(t):
                has[t] = True                       # a series that has settled once keeps its flag, no call
                continue
            try:
                has[t] = bool((settled_fn or _has_settled)(t))
            except Exception:
                has[t] = False                      # unreadable counts as none this week; a later census can still catch it
            if has[t] and not first and t in prev:  # was known and empty, now has settled markets
                new.append(t)
            elif has[t] and not first and t not in prev:
                new.append(t)                       # a brand new series that already settled
            if settled_fn is None:
                time.sleep(0.5)
        s[KEY] = {"at": now, "has": has}
        line = f"{len(tickers)} fifteen_min series, {sum(has.values())} with at least one settled market"
        if first:
            line += " (first census, baseline saved)"
        if new:
            return "NEW SERIES " + ", ".join(new) + " now settled: " + line
        return "SERIES CENSUS: " + line
    except Exception as ex:
        return f"SERIES CENSUS: failed ({type(ex).__name__}: {str(ex)[:120]}), will retry next pass"
