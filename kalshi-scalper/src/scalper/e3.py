"""E3 (README, Pre-registration: E3): L1 unchanged on seven more 15 minute series. Research only: nothing here places an order.

History goes into its OWN database (`data/alts2.sqlite`), never `book.sqlite` or `alts.sqlite`. Reuses altseries' fetcher, loader, bar and printer with this module's series and file.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED. Nothing here means trade.

Usage: python -m scalper.e3 fetch      (settled markets of the last 40 days with 1 minute candles; resumable)
       python -m scalper.e3 run        (one read; prints the signal counts first)
"""
from __future__ import annotations

import statistics as st
import sys

from . import altseries as A
from . import lstrats as L
from .paths import DATA_DIR

A.ALT_DB = DATA_DIR / "alts2.sqlite"
SERIES = ("KXXRP15M", "KXDOGE15M", "KXHYPE15M", "KXBNB15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M")
CRYPTO = SERIES[:4]
FX = SERIES[4:]
DAYS = 40


def fetch() -> None:
    A.ALTS = SERIES
    A.fetch(DAYS)


def spreads(markets: list[tuple], entries: list[dict]) -> dict:
    """Median spread (ask minus bid, YES quote) at the entry candle, per series."""
    by_t = {m[0]: m for m in markets}
    out: dict = {}
    for e in entries:
        m = by_t.get(e["ticker"])
        if m is None:
            continue
        c = next((x for x in m[2] if x[0] == e["close_ts"] - L.L1["left_s"]), None)
        if c is not None and c[1] is not None and c[2] is not None:
            out.setdefault(e["series"], []).append(c[2] - c[1])
    return {s: st.median(v) for s, v in out.items()}


def run() -> None:
    markets, vol = A.load_alts()
    print(f"{len(markets)} markets in alts2.sqlite; signal counts first")
    ents = L.hold_rule(markets, **L.L1)
    sp = spreads(markets, ents)
    for series in SERIES:
        mine = [e for e in ents if e["series"] == series]
        vols = [vol.get((e["ticker"], e["close_ts"] - L.L1["left_s"])) for e in mine]
        A._row(f"{series} (L1 unchanged)", mine, [v for v in vols if v is not None])
        if series in sp:
            print(f"    median spread at the entry candle: {sp[series] * 100:.1f}c")
    print("-- pooled, information only (not tries) --")
    for name, group in (("all seven", SERIES), ("four crypto", CRYPTO), ("three FX", FX)):
        A._row(f"pooled {name}", [e for e in ents if e["series"] in group])


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
