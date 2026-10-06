"""Bitcoin spot price by the minute, from Coinbase's public candles (no login).

A proxy for the index Kalshi settles on, not the index itself: any gap between the two
is noise the research cannot remove. Stored next to the Kalshi history so the two can be
lined up by time. `ts` is the candle's START in unix seconds; Coinbase lists candles
newest first and returns at most 300 per request, so a long range is fetched in chunks.
Resumable: a chunk that is already stored is skipped.

Usage: python -m scalper.spot
"""
from __future__ import annotations

import json
import sqlite3
import time
import urllib.error
import urllib.request

from .paths import DB

URL = "https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=60&start=%s&end=%s"
CHUNK_MIN = 300
PAUSE_S = 0.2


def iso(ts: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def parse_rows(raw: list) -> list[tuple[int, float]]:
    """[[time, low, high, open, close, volume], ...] -> [(start, close)], oldest first."""
    out = []
    for r in raw:
        try:
            out.append((int(r[0]), float(r[4])))
        except (TypeError, ValueError, IndexError):
            continue
    return sorted(out)


def fetch(start: int, end: int, retries: int = 6) -> list[tuple[int, float]]:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(URL % (iso(start), iso(end)), headers={"User-Agent": "shwoopnet-research/1.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return parse_rows(json.load(r))
        except urllib.error.HTTPError as e:
            last = e
            time.sleep(min(2.0 * (i + 1) * (3 if e.code == 429 else 1), 30))
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"coinbase candles failed: {last}")


def run() -> None:
    db = sqlite3.connect(DB)
    db.execute("CREATE TABLE IF NOT EXISTS spot(ts INTEGER PRIMARY KEY, c REAL)")
    lo, hi = db.execute("SELECT MIN(open_ts), MAX(close_ts) FROM market WHERE series='KXBTC15M'").fetchone()
    if lo is None:
        print("No Bitcoin markets stored. Run: python -m scalper.backfill")
        return
    lo = (lo // 60) * 60 - 600  # a few minutes before the first open, for the lagged returns
    hi = (hi // 60) * 60 + 600
    stored = 0
    t = lo
    while t < hi:
        end = min(t + CHUNK_MIN * 60, hi)
        have = db.execute("SELECT COUNT(*) FROM spot WHERE ts >= ? AND ts < ?", (t, end)).fetchone()[0]
        if have < (end - t) // 60 * 0.9:  # a chunk with real holes is fetched again
            rows = fetch(t, end)
            db.executemany("INSERT OR REPLACE INTO spot VALUES(?,?)", rows)
            db.commit()
            stored += len(rows)
            time.sleep(PAUSE_S)
        t = end
    n = db.execute("SELECT COUNT(*) FROM spot").fetchone()[0]
    print(f"done: {stored} new minutes stored, {n} in the table")


if __name__ == "__main__":
    run()
