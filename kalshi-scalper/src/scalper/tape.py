"""Fetch the trade tape around each H3 order, no login needed.

Kalshi's public tape lists every trade (time, side, price, size), but a market has 26,000 to
41,000 of them, so only the window after each simulated order is fetched: (order minute, +5
minutes]. Windows are fetched newest first, several at a time, and the run is resumable: a
window recorded in tape_done is skipped. A window with no trades is still recorded, because
"fetched and empty" and "never fetched" mean opposite things to the fill model.

Usage: python -m scalper.tape [max_windows]
"""
from __future__ import annotations

import calendar
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import api
from .makers import BANDS, FETCH_S, plan
from .paths import DB

WORKERS = 4

SCHEMA = """
CREATE TABLE IF NOT EXISTS tape(
  trade_id TEXT PRIMARY KEY, ticker TEXT, ts REAL, taker TEXT, yes REAL, no REAL, n REAL);
CREATE INDEX IF NOT EXISTS tape_ticker ON tape(ticker);
CREATE TABLE IF NOT EXISTS tape_done(ticker TEXT, end_ts INTEGER, PRIMARY KEY (ticker, end_ts));
"""


def parse_ts(s: str) -> float:
    """'2026-10-05T09:59:59.771854Z' to unix seconds. The fraction has any number of digits."""
    main, _, frac = s.rstrip("Z").partition(".")
    base = calendar.timegm(time.strptime(main, "%Y-%m-%dT%H:%M:%S"))
    return base + (float("0." + frac) if frac else 0.0)


def parse_trade(t: dict) -> tuple | None:
    try:
        return (t["trade_id"], t["ticker"], parse_ts(t["created_time"]), t["taker_side"],
                float(t["yes_price_dollars"]), float(t["no_price_dollars"]), float(t.get("count_fp") or 0))
    except (KeyError, TypeError, ValueError):
        return None


def fetch_window(ticker: str, end_ts: int) -> list[tuple]:
    out, cur = [], None
    while True:
        p = {"ticker": ticker, "limit": 1000, "min_ts": end_ts, "max_ts": end_ts + FETCH_S}
        if cur:
            p["cursor"] = cur
        d = api._get("/markets/trades", p)
        out += [r for r in (parse_trade(t) for t in d.get("trades", [])) if r]
        cur = d.get("cursor")
        if not cur:
            return out


def needed(db) -> list[tuple[str, int, int]]:
    """(ticker, order minute, close) for every H3 order not yet fetched, newest market first."""
    done = {(t, e) for t, e in db.execute("SELECT ticker, end_ts FROM tape_done")}
    by: dict = {}
    for t, close_ts, end, b, a in db.execute(
            "SELECT m.ticker, m.close_ts, c.end_ts, c.bid_c, c.ask_c FROM candle c JOIN market m ON m.ticker = c.ticker "
            "ORDER BY m.close_ts DESC, c.ticker, c.end_ts"):
        by.setdefault((t, close_ts), []).append((end, b, a))
    out, seen = [], set()
    for (t, close_ts), cs in by.items():
        cs.sort()
        for band in BANDS.values():
            o = plan(cs, close_ts, band)
            if o and (t, o[0]) not in done and (t, o[0]) not in seen:
                seen.add((t, o[0]))
                out.append((t, o[0], close_ts))
    return out


def run(limit: int | None) -> None:
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    todo = needed(db)
    if limit:
        todo = todo[:limit]
    print(f"{len(todo)} windows to fetch", flush=True)
    t0, n = time.time(), 0
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(fetch_window, t, e): (t, e) for t, e, _ in todo}
        for f in as_completed(futs):
            t, e = futs[f]
            try:
                rows = f.result()
            except Exception as err:      # leave the window unrecorded so a rerun retries it
                print(f"  {t}: {err}", flush=True)
                continue
            db.executemany("INSERT OR IGNORE INTO tape VALUES(?,?,?,?,?,?,?)", rows)
            db.execute("INSERT OR REPLACE INTO tape_done VALUES(?,?)", (t, e))
            n += 1
            if n % 25 == 0:
                db.commit()
                rate = n / (time.time() - t0)
                print(f"  {n}/{len(todo)} windows, {rate * 60:.0f}/min, about {(len(todo) - n) / rate / 3600:.1f}h left", flush=True)
    db.commit()
    print(f"done: {n} windows fetched", flush=True)


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else None)
