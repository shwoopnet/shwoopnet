"""RACELOCK fetcher: 1 minute candles for KXCRYPTOLEAD15M markets, public batch endpoint, no key.
Only the candles ending 600 s and 540 s before the close are kept (the look and the fill candle) plus
counts; the result column is NOT stored here (read only for T2 after registration).
Usage: PYTHONPATH=src python -m scalper.racelock_fetch
"""
from __future__ import annotations

import datetime
import json
import sqlite3
import time

from .api import _get, f

DB = "data/racelock/candles.sqlite"
MK = "data/newh15/mk_KXCRYPTOLEAD15M.json"


def ts(s):
    return int(datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def run():
    rows = json.load(open(MK))
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS market(ticker TEXT PRIMARY KEY, event TEXT, close_ts INTEGER)")
    c.execute("""CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid_c REAL, ask_c REAL,
        price_c REAL, volume REAL, PRIMARY KEY(ticker,end_ts))""")
    c.execute("CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY)")
    for m in rows:
        c.execute("INSERT OR REPLACE INTO market VALUES(?,?,?)", (m["ticker"], m["event_ticker"], ts(m["close_time"])))
    c.commit()
    done = {r[0] for r in c.execute("SELECT ticker FROM done")}
    todo = sorted((m for m in rows if m["ticker"] not in done), key=lambda m: m["close_time"])
    print("todo", len(todo), flush=True)
    i = 0
    while i < len(todo):
        chunk = todo[i:i + 20]
        lo = min(ts(m["close_time"]) for m in chunk) - 660
        hi = max(ts(m["close_time"]) for m in chunk) - 420
        want = {m["ticker"]: ts(m["close_time"]) for m in chunk}
        d = _get("/markets/candlesticks", {"market_tickers": ",".join(want), "start_ts": lo, "end_ts": hi,
                                           "period_interval": 1})
        for mk in d.get("markets", []):
            tk = mk.get("market_ticker") or mk.get("ticker")
            for k in mk.get("candlesticks", []):
                e = k["end_period_ts"]
                if tk in want and want[tk] - e in (600, 540, 480):
                    b, a, p = k.get("yes_bid") or {}, k.get("yes_ask") or {}, k.get("price") or {}
                    c.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?)",
                              (tk, e, f(b.get("close_dollars")), f(a.get("close_dollars")),
                               f(p.get("close_dollars")), f(k.get("volume_fp"))))
        for m in chunk:
            c.execute("INSERT OR REPLACE INTO done VALUES(?)", (m["ticker"],))
        c.commit()
        i += 20
        time.sleep(0.6)
        if (i // 20) % 25 == 0:
            print(i, "of", len(todo), flush=True)


if __name__ == "__main__":
    run()
