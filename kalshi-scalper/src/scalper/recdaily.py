"""Reader for the RECDAILY recorder (scripts/record_daily.py; workers/RECDAILY_NOTES.md). Research only, nothing here means trade.

The recorder stores the public quote of each watched daily, weekly or monthly market every 30 minutes under daily/quotes/<date>/<HHMM>.csv.gz on the `quote-data`
branch, and each settled result under daily/results/. The evaluators (USWEEP1, BARRIER1, NOWCAST1, FEDIMPL1) ask for the quote nearest a registered look:

    rows = load_quotes("/path/to/quote-data/daily")
    q = nearest_to_look(rows, "KXGOLDD-26NOV0417-T4098", minutes_before_close=360)   # a quote dict, or None when nothing is near enough

A look is never filled from a poll further than `tolerance_s` away (default 25 minutes, under the 30 minute cadence): too far is None, which the evaluator must count as
NoData, not as a price. A poll AFTER the look is never used to stand in for it unless it is within the tolerance (the recorder's own timestamp decides, not the slot)."""
from __future__ import annotations

import csv
import glob
import gzip
import os
from datetime import datetime, timezone

DEFAULT_TOLERANCE_S = 25 * 60


def _epoch(s):
    try:
        return int(datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp())
    except (TypeError, ValueError):
        return None


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _read(path):
    with gzip.open(path, "rt", newline="") as f:
        return list(csv.DictReader(f))


def _clean(r):
    return {
        "ticker": r["ticker"], "series": r["series"], "event_ticker": r.get("event_ticker"), "tests": (r.get("tests") or "").split("|"),
        "poll_ts": int(float(r["poll_ts"])), "open_ts": _epoch(r.get("open_time")), "close_ts": _epoch(r.get("close_time")), "status": r.get("status"),
        "strike_type": r.get("strike_type"), "floor_strike": _f(r.get("floor_strike")), "cap_strike": _f(r.get("cap_strike")),
        "yes_bid": _f(r.get("yes_bid")), "yes_ask": _f(r.get("yes_ask")), "last": _f(r.get("last")),
        "volume": _f(r.get("volume")), "open_interest": _f(r.get("open_interest")),
    }


def load_quotes(daily_dir, series=None):
    """Every recorded quote under <daily_dir>/quotes, as a list of dicts sorted by poll time. Unreadable files are skipped (a half written gzip must not stop a read)."""
    out = []
    for p in sorted(glob.glob(os.path.join(daily_dir, "quotes", "**", "*.csv.gz"), recursive=True)):
        try:
            for r in _read(p):
                if series is None or r["series"] == series:
                    out.append(_clean(r))
        except (OSError, EOFError, KeyError, ValueError):
            continue
    out.sort(key=lambda q: q["poll_ts"])
    return out


def load_results(daily_dir):
    """{ticker: "yes" | "no"} from the recorded settlements (a ticker seen twice keeps the first)."""
    res = {}
    for p in sorted(glob.glob(os.path.join(daily_dir, "results", "**", "*.csv.gz"), recursive=True)):
        try:
            for r in _read(p):
                if r.get("result") in ("yes", "no"):
                    res.setdefault(r["ticker"], r["result"])
        except (OSError, EOFError, KeyError):
            continue
    return res


def nearest_to_time(rows, ticker, target_ts, tolerance_s=DEFAULT_TOLERANCE_S):
    """The recorded quote of `ticker` nearest `target_ts` (unix seconds) within `tolerance_s`, else None. A quote with no two sided price is still returned: the
    evaluator decides (USWEEP1 and FEDIMPL1 raise NoData on a one sided quote); a tie goes to the earlier poll."""
    best = None
    for q in rows:
        if q["ticker"] != ticker:
            continue
        d = abs(q["poll_ts"] - target_ts)
        if d <= tolerance_s and (best is None or d < best[0]):
            best = (d, q)
    return None if best is None else dict(best[1], look_gap_s=best[0])


def nearest_to_look(rows, ticker, minutes_before_close=None, minutes_after_open=None, tolerance_s=DEFAULT_TOLERANCE_S):
    """The quote nearest a registered look: `minutes_before_close` (USWEEP1, NOWCAST1) or `minutes_after_open` (BARRIER1's open + 48 h = 2880). Exactly one is given."""
    if (minutes_before_close is None) == (minutes_after_open is None):
        raise ValueError("give exactly one of minutes_before_close, minutes_after_open")
    ref = next((q for q in rows if q["ticker"] == ticker), None)
    if ref is None:
        return None
    if minutes_before_close is not None:
        if ref["close_ts"] is None:
            return None
        target = ref["close_ts"] - minutes_before_close * 60
    else:
        if ref["open_ts"] is None:
            return None
        target = ref["open_ts"] + minutes_after_open * 60
    return nearest_to_time(rows, ticker, target, tolerance_s)


def tickers(rows, series):
    return sorted({q["ticker"] for q in rows if q["series"] == series})


def usweep1_window(rows, results, ticker, look_minutes, tolerance_s=DEFAULT_TOLERANCE_S):
    """A window in the shape scalper.usweep1.forward_eval expects: {"series", "close_ts", "candles": {end_ts: (bid, ask, volume)}} with the one look candle filled from
    the nearest recorded poll, or an empty candle map when none is near enough (forward_eval then raises NoData). `result` is the settled outcome or None."""
    q = nearest_to_look(rows, ticker, minutes_before_close=look_minutes, tolerance_s=tolerance_s)
    ref = next((r for r in rows if r["ticker"] == ticker), None)
    if ref is None or ref["close_ts"] is None:
        return None
    candles = {}
    if q is not None:
        candles[ref["close_ts"] - look_minutes * 60] = (q["yes_bid"], q["yes_ask"], q["volume"])
    return {"series": ref["series"], "ticker": ticker, "close_ts": ref["close_ts"], "candles": candles, "result": results.get(ticker)}
