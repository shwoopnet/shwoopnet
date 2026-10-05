"""Pull Kalshi's own 1 minute history for settled 15 minute markets.

Why this exists: Kalshi serves 1 minute candles (with the bid and ask) for past
markets, no login needed, so history can be fetched on demand and nothing has to
be left recording. (A live snapshot recorder was tried first and retired: it only
saw what happened while a laptop was awake, and had gaps for most of its first
three days.) Checked to reach at least 45 days back and not 120; this defaults
to 30.

Stores into one SQLite file (see paths.py):
  market(ticker, series, open_ts, close_ts, result, strike, n_candles)
  candle(ticker, series, end_ts, bid_c, ask_c, ..., volume)
Resumable and idempotent: a market already stored is skipped.

Usage: python -m scalper.backfill [days]
"""
from __future__ import annotations

import sqlite3
import sys
import time
from datetime import datetime

from . import api
from .paths import DB

SERIES = ("KXBTC15M", "KXGOLD15M")
MAX_DAYS = 40
PAUSE_S = 0.25  # stay inside Kalshi's public read limits; _get also waits out any 429

SCHEMA = """
CREATE TABLE IF NOT EXISTS market(
  ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER,
  result TEXT, strike REAL, n_candles INTEGER);
CREATE TABLE IF NOT EXISTS candle(
  ticker TEXT, series TEXT, end_ts INTEGER,
  bid_o REAL, bid_h REAL, bid_l REAL, bid_c REAL,
  ask_o REAL, ask_h REAL, ask_l REAL, ask_c REAL,
  price_c REAL, volume REAL, oi REAL,
  PRIMARY KEY (ticker, end_ts));
"""


def iso_ts(iso: str | None) -> int | None:
    try:
        return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())
    except Exception:
        return None


def _d(obj: dict | None, key: str) -> float | None:
    """A dollar string out of a nested candle field, or None when absent."""
    return api.f((obj or {}).get(key))


def parse_candle(c: dict, ticker: str, series: str) -> tuple | None:
    """One API candle to a table row, or None when it carries no timestamp."""
    end = c.get("end_period_ts")
    if end is None:
        return None
    b, a, p = c.get("yes_bid"), c.get("yes_ask"), c.get("price")
    return (ticker, series, int(end),
            _d(b, "open_dollars"), _d(b, "high_dollars"), _d(b, "low_dollars"), _d(b, "close_dollars"),
            _d(a, "open_dollars"), _d(a, "high_dollars"), _d(a, "low_dollars"), _d(a, "close_dollars"),
            _d(p, "close_dollars"), api.f(c.get("volume_fp")), api.f(c.get("open_interest_fp")))


def run(days: int) -> None:
    days = max(1, min(days, MAX_DAYS))
    DB.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    have = {r[0] for r in db.execute("SELECT ticker FROM market")}
    now = int(time.time())
    lo = now - days * 86400
    stored = skipped = 0
    for series in SERIES:
        listed = list(api.settled_markets(series, lo, now))
        print(f"{series}: {len(listed)} settled markets in the last {days} days", flush=True)
        for m in listed:
            t = m["ticker"]
            if t in have:
                skipped += 1
                continue
            o, c = iso_ts(m.get("open_time")), iso_ts(m.get("close_time"))
            if o is None or c is None:
                continue
            rows = [r for r in (parse_candle(x, t, series) for x in api.candlesticks(series, t, o, c)) if r]
            db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)",
                       (t, series, o, c, m.get("result"), m.get("floor_strike"), len(rows)))
            stored += 1
            if stored % 50 == 0:
                db.commit()
                print(f"  {stored} markets stored", flush=True)
            time.sleep(PAUSE_S)
        db.commit()
    print(f"done: {stored} new markets, {skipped} already stored", flush=True)


def main() -> None:
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 30)


if __name__ == "__main__":
    main()
