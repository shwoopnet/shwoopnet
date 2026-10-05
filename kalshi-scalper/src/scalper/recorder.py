"""Record top-of-book snapshots for the 15 minute BTC and gold markets.

Run it for days before building any strategy. Everything downstream (is there
any move bigger than the cost of crossing the spread, how does the book behave
in the last minutes, how do settled results distribute) is answered from this
data, not guessed. Appends to SQLite; safe to restart.

Usage: python -m scalper.recorder [seconds_between_polls]
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

from . import api

SERIES = ("KXBTC15M", "KXGOLD15M")
DB = Path(__file__).resolve().parents[2] / "data" / "book.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS snap(
  ts REAL, series TEXT, ticker TEXT, close_time TEXT, strike REAL,
  yes_bid REAL, yes_bid_sz REAL, yes_ask REAL, yes_ask_sz REAL,
  last REAL, vol24 REAL, oi REAL);
CREATE INDEX IF NOT EXISTS snap_t ON snap(ticker, ts);
CREATE TABLE IF NOT EXISTS result(
  ticker TEXT PRIMARY KEY, series TEXT, result TEXT, close_time TEXT, seen REAL);
"""


def poll(db: sqlite3.Connection) -> int:
    now, n = time.time(), 0
    for s in SERIES:
        for m in api.markets(s, "open"):
            db.execute(
                "INSERT INTO snap VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (now, s, m["ticker"], m.get("close_time"), m.get("floor_strike"),
                 api.f(m.get("yes_bid_dollars")), api.f(m.get("yes_bid_size_fp")),
                 api.f(m.get("yes_ask_dollars")), api.f(m.get("yes_ask_size_fp")),
                 api.f(m.get("last_price_dollars")), api.f(m.get("volume_24h_fp")),
                 api.f(m.get("open_interest_fp"))))
            n += 1
    return n


def record_results(db: sqlite3.Connection) -> None:
    for s in SERIES:
        for m in api.markets(s, "settled", limit=10):
            if m.get("result"):
                db.execute("INSERT OR IGNORE INTO result VALUES(?,?,?,?,?)",
                           (m["ticker"], s, m["result"], m.get("close_time"), time.time()))


def main() -> None:
    every = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    DB.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    last_results = 0.0
    while True:
        t0 = time.time()
        try:
            n = poll(db)
            if t0 - last_results > 120:
                record_results(db)
                last_results = t0
            db.commit()
            print(time.strftime("%H:%M:%S"), f"{n} snapshots", flush=True)
        except Exception as e:  # keep recording through transient failures
            print("poll failed:", e, flush=True)
        time.sleep(max(0.0, every - (time.time() - t0)))


if __name__ == "__main__":
    main()
