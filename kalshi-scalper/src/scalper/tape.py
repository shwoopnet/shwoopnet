"""Fetch the trade tape around each H3 order, no login needed.

Kalshi's public tape lists every trade (time, side, price, size), but a market has 26,000 to
41,000 of them, so only the window after each simulated order is fetched: (order minute, +5
minutes]. The raw trades are not kept (about 28 million rows); the order's side and price are
known before the fetch, so the fill flags are computed here and only they are stored, one
row per order, in `fills`. Windows are fetched newest first, several at a time, and the run is
resumable: an order already in `fills` is skipped. A window with no trades is still recorded,
because "fetched and empty" and "never fetched" mean opposite things to the fill model.

Usage: python -m scalper.tape [max_windows]
"""
from __future__ import annotations

import calendar
import os
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import api
from .makers import BANDS, FETCH_S, INFO_WINDOW_S, WINDOW_S, filled, plan
from .paths import DB

WORKERS = int(os.environ.get("SCALPER_WORKERS", "4"))

SCHEMA = """
DROP TABLE IF EXISTS tape;
DROP TABLE IF EXISTS tape_done;
CREATE TABLE IF NOT EXISTS fills(
  ticker TEXT, end_ts INTEGER, side TEXT, price REAL, fill INTEGER, fill_opt INTEGER, fill5 INTEGER, n_trades INTEGER,
  PRIMARY KEY (ticker, end_ts));
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


def needed(db) -> list[tuple]:
    """(ticker, order) for every H3 order not yet in `fills`, newest market first. order is
    makers.plan's (minute, side, bid, ask)."""
    done = {(t, e) for t, e in db.execute("SELECT ticker, end_ts FROM fills")}
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
                out.append((t, o))
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
        futs = {ex.submit(fetch_window, t, o[0]): (t, o) for t, o in todo}
        for f in as_completed(futs):
            t, o = futs[f]
            try:
                rows = f.result()
            except Exception as err:      # leave the order unrecorded so a rerun retries it
                print(f"  {t}: {err}", flush=True)
                continue
            tr = [(r[2], r[3], r[4], r[5]) for r in rows]
            db.execute("INSERT OR REPLACE INTO fills VALUES(?,?,?,?,?,?,?,?)",
                       (t, o[0], o[1], o[2], int(filled(o, tr, WINDOW_S)), int(filled(o, tr, WINDOW_S, strict=False)),
                        int(filled(o, tr, INFO_WINDOW_S)), len(tr)))
            n += 1
            if n % 25 == 0:
                db.commit()
                rate = n / (time.time() - t0)
                print(f"  {n}/{len(todo)} windows, {rate * 60:.0f}/min, about {(len(todo) - n) / rate / 3600:.1f}h left", flush=True)
    db.commit()
    print(f"done: {n} windows fetched", flush=True)


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else None)
