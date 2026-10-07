"""Order-book recorder. READ ONLY, public endpoints, no key, never an order.

Kalshi's minute candles cannot answer questions about quoting or stale prices. This
writes the real top of the book of the open Bitcoin and gold 15 minute markets every few
seconds into data/ob.sqlite (table `ob`), so the quote ideas (L4 to L6 in the README
ledger) can be tested on depth. It describes; it never judges, and nothing here is a
strategy. Failures are stored as rows (table `err`) instead of stopping the run, because
the point of a long unattended run is to find out what breaks.

    python -m scalper.recorder --hours 24
    touch data/STOP        # asks a running recorder to finish its current cycle and exit
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time

from . import api
from .paths import DATA_DIR

DB = DATA_DIR / "ob.sqlite"
STOP = DATA_DIR / "STOP"
SERIES = ("KXBTC15M", "KXGOLD15M")
LEVELS_KEPT = 5

SCHEMA = """
CREATE TABLE IF NOT EXISTS ob(
  ts REAL, series TEXT, ticker TEXT, close_ts TEXT,
  yes_bid REAL, yes_ask REAL, no_bid REAL, no_ask REAL,
  yes_depth REAL, no_depth REAL, yes_levels TEXT, no_levels TEXT,
  list_yes_bid REAL, list_yes_ask REAL);
CREATE INDEX IF NOT EXISTS ob_t ON ob(ticker, ts);
CREATE TABLE IF NOT EXISTS err(ts REAL, series TEXT, what TEXT);
"""


def _levels(raw) -> list[tuple[float, float]]:
    out = []
    for p, q in raw or []:
        pf, qf = api.f(p), api.f(q)
        if pf is not None and qf is not None:
            out.append((pf, qf))
    return sorted(out)           # ascending price: the best bid is the LAST level


def parse_book(raw: dict) -> dict:
    """Top of book from Kalshi's two lists of resting BIDS (yes bids, no bids).
    A yes ask is what a no bid implies: 1 - the best no bid. An empty side gives None, never 0,
    because 0 would read as a free price."""
    ob = (raw or {}).get("orderbook_fp") or {}
    yes, no = _levels(ob.get("yes_dollars")), _levels(ob.get("no_dollars"))
    yb = yes[-1][0] if yes else None
    nb = no[-1][0] if no else None
    return {
        "yes_bid": yb, "no_bid": nb,
        "yes_ask": round(1 - nb, 4) if nb is not None else None,
        "no_ask": round(1 - yb, 4) if yb is not None else None,
        "yes_depth": sum(q for _, q in yes[-LEVELS_KEPT:]),
        "no_depth": sum(q for _, q in no[-LEVELS_KEPT:]),
        "yes_levels": json.dumps(yes[-LEVELS_KEPT:]), "no_levels": json.dumps(no[-LEVELS_KEPT:]),
    }


def snapshot(series: str, get=None, now=time.time) -> list[tuple]:
    """One row per open market of the series. `get` is injectable so tests never touch the network."""
    get = get or (lambda path, p=None: api._get(path, p, retries=2))
    rows = []
    listed = get("/markets", {"series_ticker": series, "status": "open", "limit": 20}).get("markets", [])
    for m in listed:
        ts = now()
        b = parse_book(get("/markets/" + m["ticker"] + "/orderbook"))
        rows.append((ts, series, m["ticker"], m.get("close_time"),
                     b["yes_bid"], b["yes_ask"], b["no_bid"], b["no_ask"],
                     b["yes_depth"], b["no_depth"], b["yes_levels"], b["no_levels"],
                     api.f(m.get("yes_bid_dollars")), api.f(m.get("yes_ask_dollars"))))
    return rows


def cycle(db, get=None, now=time.time) -> int:
    n = 0
    for s in SERIES:
        try:
            rows = snapshot(s, get, now)
            db.executemany("INSERT INTO ob VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            n += len(rows)
        except Exception as e:       # keep going: one bad cycle must not end a day-long run
            db.execute("INSERT INTO err VALUES(?,?,?)", (now(), s, str(e)[:300]))
    db.commit()
    return n


def run(hours: float, every: float = 10.0, get=None, sleep=time.sleep, now=time.time) -> int:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    end, total = now() + hours * 3600, 0
    while now() < end and not STOP.exists():
        t0 = now()
        total += cycle(db, get, now)
        sleep(max(0.0, every - (now() - t0)))
    return total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--every", type=float, default=10.0, help="seconds between cycles")
    a = ap.parse_args()
    print("rows written:", run(a.hours, a.every))
