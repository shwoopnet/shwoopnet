#!/usr/bin/env python3
"""Desk C generic kalshi-pull loader (Idea Desk C, Nov 16, 2026), build 1. Standard library only, no network.

Reads landed kalshi-pull runs (pull/<JOB>/<run>/manifest.json + NNNN.json.gz): market lists (live /markets or /historical/markets)
and candles (batched /markets/candlesticks or single /historical/markets/{t}/candlesticks).

THE WALL (what a family plugin can and cannot get):
  1. markets(): only markets of the named series whose WINDOW FIELD (close_time or the market's own occurrence_datetime) parses and lies
     in [lo, hi). That field is tested before any other field is read. Returned records hold ONLY time and identity fields
     (ticker, event_ticker, series, open, close, occurrence, expected_expiration, title words). No price, volume, open interest or result.
  2. quotes(): candle closes (yes bid, yes ask) for tickers the caller names, only candles ending at or before a caller-given cut per ticker.
  3. results(): the result field, for tickers the caller names. A plugin calls it LAST, once, for its traded tickers.
  4. truncated(): a list run whose last stored page still has a cursor is truncated, unless that page's earliest close is before lo
     (lists come newest first by close time; the caller states the order is checked by Auditor B for each list).
Only manifest rows that name a stored 'file' are read (a 429 row stores nothing)."""
import calendar
import gzip
import json
import os
import time

EPS = 1e-9
TIME_FIELDS = ("open_time", "close_time", "occurrence_datetime", "expected_expiration_time")
WORD_FIELDS = ("yes_sub_title", "title")


def iso(s):
    s = (s or "").split(".")[0].rstrip("Z")
    try:
        return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return None


def num(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def runs(root, job):
    base = os.path.join(root, "pull", job)
    if not os.path.isdir(base):
        return []
    out = []
    for r in sorted(os.listdir(base)):
        mp = os.path.join(base, r, "manifest.json")
        if os.path.isfile(mp):
            with open(mp) as fh:
                out.append((os.path.join(base, r), json.load(fh)))
    return out


def bodies(root, job, rid=None):
    for rdir, man in runs(root, job):
        for row in man.get("rows", []):
            fn = row.get("file")
            if not fn or os.path.basename(fn) != fn or (rid is not None and row.get("id") != rid):
                continue
            p = os.path.join(rdir, fn)
            if not os.path.isfile(p):
                continue
            with gzip.open(p, "rt") as fh:
                b = json.load(fh)
            if isinstance(b, dict):
                yield row, b


def markets(root, jobs, series, field, lo, hi):
    """ticker -> record of time and identity fields only, for the window [lo, hi) on `field` ('close' or 'occurrence')."""
    key = {"close": "close_time", "occurrence": "occurrence_datetime"}[field]
    out = {}
    for job in jobs:
        for _row, b in bodies(root, job):
            for m in b.get("markets") or []:
                v = iso(m.get(key))                          # the window field FIRST
                if v is None or not (lo <= v < hi):
                    continue
                t = m.get("ticker") or ""
                s = t.split("-")[0]
                if s not in series:
                    continue
                rec = {"ticker": t, "event": m.get("event_ticker") or "", "series": s}
                for f in TIME_FIELDS:
                    rec[f] = iso(m.get(f))
                for f in WORD_FIELDS:
                    rec[f] = (m.get(f) or "")
                out.setdefault(t, rec)
    return out


def truncated(root, job, rid, lo):
    last = {}
    for row, b in bodies(root, job, rid):
        if "markets" in b:
            cl = [iso(m.get("close_time")) for m in b.get("markets") or []]
            cl = [c for c in cl if c is not None]
            last[(row.get("page") or 0)] = (b.get("cursor") or "", min(cl) if cl else None)
    if not last:
        return True
    cur, earliest = last[max(last)]
    if not cur:
        return False
    return earliest is None or earliest >= lo


def _px(o):
    if not isinstance(o, dict):
        return None
    if "close_dollars" in o:
        return num(o.get("close_dollars"))
    v = num(o.get("close"))
    return None if v is None else v / 100.0


def quotes(root, jobs, cut):
    """cut: ticker -> latest allowed candle end (unix s). Returns ticker -> {end_ts: (yes_bid, yes_ask)} for candles ending <= cut[ticker]."""
    q = {}

    def add(t, cs):
        if t not in cut:
            return
        for c in cs or []:
            ts = c.get("end_period_ts")
            if isinstance(ts, int) and ts <= cut[t]:
                q.setdefault(t, {}).setdefault(ts, (_px(c.get("yes_bid")), _px(c.get("yes_ask"))))

    for job in jobs:
        for row, b in bodies(root, job):
            if isinstance(b.get("markets"), list) and b["markets"] and "candlesticks" in (b["markets"][0] or {}):
                for m in b["markets"]:
                    add(m.get("market_ticker") or m.get("ticker"), m.get("candlesticks"))
            elif "candlesticks" in b:
                parts = (row.get("path") or "").split("/")
                add(b.get("ticker") or (parts[-2] if len(parts) >= 2 else ""), b.get("candlesticks"))
    return q


def quote_at(qt, ts, lookback):
    """The latest candle ending in [ts - lookback, ts], two-sided under rule 18, as (yes_bid, yes_ask), else None."""
    k = max((x for x in qt if ts - lookback <= x <= ts), default=None)
    if k is None:
        return None
    yb, ya = qt[k]
    if yb is None or ya is None or not (yb > EPS and ya < 1 - EPS and ya - yb > EPS):
        return None
    return yb, ya


def results(root, jobs, tickers):
    """Read LAST, only for the tickers given: ticker -> 'yes' | 'no' | 'void' | ''."""
    out = {}
    for job in jobs:
        for _row, b in bodies(root, job):
            for m in b.get("markets") or []:
                t = m.get("ticker")
                if t in tickers and t not in out:
                    out[t] = (m.get("result") or "").strip().lower()
    return out
