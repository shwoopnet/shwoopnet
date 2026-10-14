"""E3C (README, Pre-registration: E5B and E3C): L1 unchanged on HYPE and BNB on the days before E3's window. Research only: nothing here places an order.

History goes into its OWN database (`data/alts4.sqlite`). Verdict words: FALSIFIED, NOT_YET_FALSIFIED. Nothing here means trade.
Usage: python -m scalper.e3c fetch   then, ONCE:   python -m scalper.e3c run
"""
from __future__ import annotations

import sqlite3
import sys
import time

from . import altseries as A
from . import backfill
from . import lstrats as L
from .paths import DATA_DIR

A.ALT_DB = DATA_DIR / "alts4.sqlite"
SERIES = ("KXHYPE15M", "KXBNB15M")
FLOOR_TS = 1_788_465_600      # 2026-09-03 20:00 UTC, the earliest close in E3's data
FETCH_DAYS = 69


def fetch() -> None:
    """Only the days before FLOOR_TS are downloaded."""
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(A.ALT_DB)
    db.executescript(backfill.SCHEMA)
    saved, backfill.SERIES = backfill.SERIES, SERIES
    try:
        stored, skipped, empty = backfill._fetch(db, int(time.time()) - FETCH_DAYS * 86400, FLOOR_TS - 1, "before E3's first day", skip_empty=True)
        print(f"done: {stored} new markets, {skipped} already stored, {empty} with no candles (not stored)", flush=True)
    finally:
        backfill.SERIES = saved


def holdout(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e["series"] in SERIES and e["close_ts"] < FLOOR_TS]


def run() -> None:
    markets, vol = A.load_alts()
    print(f"{len(markets)} markets in alts4.sqlite; signal counts first")
    ents = holdout(L.hold_rule(markets, **L.L1))
    for series in SERIES:
        mine = [e for e in ents if e["series"] == series]
        A._row(f"{series} (L1 unchanged, older days)", mine, [x for x in (vol.get((e["ticker"], e["close_ts"] - L.L1["left_s"])) for e in mine) if x is not None])


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
