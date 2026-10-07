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
       python -m scalper.backfill range OLDER_DAYS NEWER_DAYS    (for example: range 68 29)
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


def _fetch(db: sqlite3.Connection, lo: int, hi: int, label: str, skip_empty: bool = False) -> tuple[int, int, int]:
    """Store every settled market of both series closing in [lo, hi] that is not stored yet. skip_empty: a market with no
    candles (older than Kalshi keeps them) is not stored at all, so it cannot look like a market that traded with no quotes."""
    have = {r[0] for r in db.execute("SELECT ticker FROM market")}
    stored = skipped = empty = 0
    for series in SERIES:
        listed = list(api.settled_markets(series, lo, hi))
        print(f"{series}: {len(listed)} settled markets {label}", flush=True)
        for m in listed:
            t = m["ticker"]
            if t in have:
                skipped += 1
                continue
            o, c = iso_ts(m.get("open_time")), iso_ts(m.get("close_time"))
            if o is None or c is None:
                continue
            rows = [r for r in (parse_candle(x, t, series) for x in api.candlesticks(series, t, o, c)) if r]
            if skip_empty and not rows:
                empty += 1
                continue
            db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)",
                       (t, series, o, c, m.get("result"), m.get("floor_strike"), len(rows)))
            stored += 1
            if stored % 50 == 0:
                db.commit()
                print(f"  {stored} markets stored", flush=True)
            time.sleep(PAUSE_S)
        db.commit()
    return stored, skipped, empty


def run(days: int) -> None:
    days = max(1, min(days, MAX_DAYS))
    DB.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    now = int(time.time())
    stored, skipped, _ = _fetch(db, now - days * 86400, now, f"in the last {days} days")
    print(f"done: {stored} new markets, {skipped} already stored", flush=True)


def run_range(older_days: int, newer_days: int) -> None:
    """Markets that closed between older_days and newer_days ago (older_days > newer_days). Kalshi kept candles about 66 days back on
    2026-10-07, so older markets come back empty and are not stored."""
    if not older_days > newer_days >= 0:
        raise ValueError("older_days must be greater than newer_days")
    DB.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    now = int(time.time())
    stored, skipped, empty = _fetch(db, now - older_days * 86400, now - newer_days * 86400, f"from {older_days} to {newer_days} days ago", skip_empty=True)
    print(f"done: {stored} new markets, {skipped} already stored, {empty} with no candles (not stored)", flush=True)


def main() -> None:
    if len(sys.argv) > 3 and sys.argv[1] == "range":
        run_range(int(sys.argv[2]), int(sys.argv[3]))
    else:
        run(int(sys.argv[1]) if len(sys.argv) > 1 else 30)


if __name__ == "__main__":
    main()
