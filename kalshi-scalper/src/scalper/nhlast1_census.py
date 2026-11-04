"""NHLAST1 census: list NHL sibling player-prop ladders (listing only; the result field is stored for the later join, never read here).
  python -m scalper.nhlast1_census SERIES...
"""
from __future__ import annotations
import json, sqlite3, sys, time
from pathlib import Path
from . import api

DB = Path("/home/user/.cache/nhlast1/nhlast1.sqlite")
CUT_ISO = "2026-10-03T16:00:00Z"


def conn():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=120)
    c.execute("CREATE TABLE IF NOT EXISTS kmarket(ticker TEXT PRIMARY KEY, series TEXT, event TEXT, strike REAL, name TEXT, close_time TEXT, volume REAL, result TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS listed(series TEXT, path TEXT, PRIMARY KEY(series,path))")
    return c


def list_series(series):
    c = conn()
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        if c.execute("SELECT 1 FROM listed WHERE series=? AND path=?", (series, path)).fetchone():
            continue
        cursor, n = None, 0
        while True:
            q = dict(series_ticker=series, limit=1000, **extra)
            if cursor:
                q["cursor"] = cursor
            d = api._get(path, q)
            time.sleep(1.0)
            for m in d.get("markets", []):
                ct = m.get("close_time") or ""
                ex = m.get("expected_expiration_time") or ct
                vol = float(m.get("volume_fp") or 0)
                if ct >= CUT_ISO or ex >= CUT_ISO or vol <= 0:
                    continue
                c.execute("INSERT OR IGNORE INTO kmarket VALUES(?,?,?,?,?,?,?,?)", (m["ticker"], series, m["event_ticker"], m.get("floor_strike"),
                          m.get("yes_sub_title"), ct, vol, m.get("result")))
                n += 1
            cursor = d.get("cursor")
            if not cursor:
                break
        c.execute("INSERT INTO listed VALUES(?,?)", (series, path))
        c.commit()
        print(series, path, "kept", n, flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        list_series(s)
