"""L1B (README, Pre-registration: L1B): L1 unchanged on Bitcoin, Ethereum and gold on the older days `book.sqlite` never held. Rules fixed in the README before those markets were downloaded.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED. Nothing here means trade.

History goes into its OWN database (`data/l1b.sqlite`). Reuses altseries' fetcher, loader, bar and printer. Usage: python -m scalper.l1b fetch   then, ONCE:   python -m scalper.l1b run
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from . import altseries as A
from . import lstrats as L
from .paths import DATA_DIR

A.ALT_DB = DATA_DIR / "l1b.sqlite"
SERIES = ("KXBTC15M", "KXETH15M", "KXGOLD15M")
FLOOR_TS = int(datetime(2026, 9, 2, 19, 30, tzinfo=timezone.utc).timestamp())      # the earliest close in book.sqlite: nothing on or after it counts
FETCH_DAYS = 69


def fetch() -> None:
    A.ALTS = SERIES
    A.fetch(FETCH_DAYS)


def holdout(entries: list[dict]) -> list[dict]:
    """Only entries on markets that closed strictly before FLOOR_TS, only the registered series."""
    return [e for e in entries if e["series"] in SERIES and e["close_ts"] < FLOOR_TS]


def run() -> None:
    markets, vol = A.load_alts()
    print(f"{len(markets)} markets in l1b.sqlite; signal counts first")
    ents = holdout(L.hold_rule(markets, **L.L1))
    for series in SERIES:
        mine = [e for e in ents if e["series"] == series]
        vols = [vol.get((e["ticker"], e["close_ts"] - L.L1["left_s"])) for e in mine]
        A._row(f"{series} (L1 unchanged, older days)", mine, [v for v in vols if v is not None])
    print("-- pooled, information only (not a try) --")
    A._row("pooled Bitcoin, Ethereum, gold", ents)


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
