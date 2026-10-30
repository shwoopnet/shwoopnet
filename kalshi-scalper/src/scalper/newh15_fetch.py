"""NEWH15 fetcher: 1 minute candles for every settled 15 minute market of a series, in batches
of up to 20 tickers (100 draws a 429) through Kalshi's public batch candlestick endpoint (no key).

Reads data/newh15/mk_<SERIES>.json (market listing, written by the inventory step) and writes
data/newh15/candles.sqlite (same candle columns as the other data/*.sqlite files).
Usage: PYTHONPATH=src python -m scalper.newh15_fetch SERIES [SERIES ...]
"""
from __future__ import annotations

import datetime
import json
import sqlite3
import sys
import time

from .api import _get, f

DB = "data/newh15/candles.sqlite"


def ts(s: str) -> int:
    return int(datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def connect():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS market(ticker TEXT PRIMARY KEY, series TEXT, event TEXT,
        open_ts INTEGER, close_ts INTEGER, result TEXT, strike REAL, expval TEXT, volume REAL, oi REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS candle(ticker TEXT, series TEXT, end_ts INTEGER,
        bid_o REAL, bid_h REAL, bid_l REAL, bid_c REAL, ask_o REAL, ask_h REAL, ask_l REAL, ask_c REAL,
        price_c REAL, volume REAL, oi REAL, PRIMARY KEY(ticker,end_ts))""")
    c.execute("CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY)")
    return c


def run(series: str):
    rows = json.load(open(f"data/newh15/mk_{series}.json"))
    c = connect()
    for m in rows:
        c.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (m["ticker"], series, m["event_ticker"], ts(m["open_time"]), ts(m["close_time"]), m["result"],
                   f(m.get("floor_strike")), m.get("expiration_value"), f(m.get("volume_fp")), f(m.get("open_interest_fp"))))
    c.commit()
    done = {r[0] for r in c.execute("SELECT ticker FROM done")}
    todo = sorted((m for m in rows if m["ticker"] not in done), key=lambda m: m["close_time"])
    print(series, "markets", len(rows), "todo", len(todo), flush=True)
    i = 0
    while i < len(todo):
        chunk = todo[i:i + 20]
        lo = min(ts(m["open_time"]) for m in chunk)
        hi = max(ts(m["close_time"]) for m in chunk)
        d = _get("/markets/candlesticks", {"market_tickers": ",".join(m["ticker"] for m in chunk),
                                           "start_ts": lo, "end_ts": hi + 60, "period_interval": 1})
        for mk in d.get("markets", []):
            tk = mk.get("market_ticker") or mk.get("ticker")
            for k in mk.get("candlesticks", []):
                b, a, p = k.get("yes_bid") or {}, k.get("yes_ask") or {}, k.get("price") or {}
                c.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (tk, series, k["end_period_ts"], f(b.get("open_dollars")), f(b.get("high_dollars")),
                           f(b.get("low_dollars")), f(b.get("close_dollars")), f(a.get("open_dollars")),
                           f(a.get("high_dollars")), f(a.get("low_dollars")), f(a.get("close_dollars")),
                           f(p.get("close_dollars")), f(k.get("volume_fp")), f(k.get("open_interest_fp"))))
        for m in chunk:
            c.execute("INSERT OR REPLACE INTO done VALUES(?)", (m["ticker"],))
        c.commit()
        i += 20
        time.sleep(0.8)
        if (i // 20) % 50 == 0:
            print(series, i, "of", len(todo), flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
