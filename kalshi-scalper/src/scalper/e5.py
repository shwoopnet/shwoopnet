"""E5 (README, Pre-registration: E5): L1 unchanged on other commodities and two more coins, with a discovery window and a holdout fixed before looking. Research only: nothing here places an order.

History goes into its OWN database (`data/alts3.sqlite`). Reuses altseries' fetcher, loader, bar and printer. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.e5 fetch      (settled markets of the last 69 days with 1 minute candles; resumable)
       python -m scalper.e5 run        (one read; prints the signal counts first)
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone

from . import altseries as A
from . import lstrats as L
from .paths import DATA_DIR
from .scalps import MIN_N

A.ALT_DB = DATA_DIR / "alts3.sqlite"
COMMODITIES = ("KXSILVER15M", "KXWTI15M", "KXNATGAS15M", "KXCOPPER15M", "KXPLATINUM15M", "KXPALLADIUM15M")
COINS = ("KXZEC15M", "KXNEAR15M")
SERIES = COMMODITIES + COINS
SPLIT_TS = int(datetime(2026, 9, 3, 20, tzinfo=timezone.utc).timestamp())      # discovery = on or after, holdout = before (E3's cut)
DAYS = 69
AUDIT_MEAN = 0.015


def fetch() -> None:
    A.ALTS = SERIES
    A.fetch(DAYS)


def split(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    """(discovery, holdout) by close time."""
    return [e for e in entries if e["close_ts"] >= SPLIT_TS], [e for e in entries if e["close_ts"] < SPLIT_TS]


def bar(es: list[dict]) -> tuple[str, dict]:
    """The common bar on one window; too little data is NOT_ENOUGH_DATA, never a pass or a fail."""
    days = {e["day"] for e in es}
    if len(es) < MIN_N or len(days) < A.MIN_DAYS:
        return "NOT_ENOUGH_DATA", {"n": len(es), "days": len(days)}
    return A.summarize(es)


def series_verdict(disc: list[dict], hold: list[dict]) -> tuple[str, dict]:
    """Stage 1 on discovery; the holdout is read only for a series that passes it, and the series passes only if it passes both."""
    v1, s1 = bar(disc)
    out = {"stage1": v1, "s1": s1, "stage2": None, "s2": None}
    if v1 == "NOT_ENOUGH_DATA":
        return "NOT_ENOUGH_DATA", out
    if v1 != "NOT_YET_FALSIFIED":
        return "FALSIFIED", out
    v2, s2 = bar(hold)
    out.update(stage2=v2, s2=s2)
    return v2, out


def run() -> None:
    markets, vol = A.load_alts()
    print(f"{len(markets)} markets in alts3.sqlite; signal counts first")
    ents = L.hold_rule(markets, **L.L1)
    by_t = {m[0]: m for m in markets}
    for series in SERIES:
        mine = [e for e in ents if e["series"] == series]
        disc, hold = split(mine)
        vols = [vol.get((e["ticker"], e["close_ts"] - L.L1["left_s"])) for e in disc]
        A._row(f"{series} discovery (L1 unchanged)", disc, [v for v in vols if v is not None])
        sp = []
        for e in disc:
            c = next((x for x in by_t[e["ticker"]][2] if x[0] == e["close_ts"] - L.L1["left_s"]), None)
            if c is not None and c[1] is not None and c[2] is not None:
                sp.append(c[2] - c[1])
        if sp:
            print(f"    median spread at the entry candle: {st.median(sp) * 100:.1f}c")
        v, d = series_verdict(disc, hold)
        if d["stage1"] == "NOT_YET_FALSIFIED":
            A._row(f"{series} holdout (read because Stage 1 passed)", hold)
            print(f"    -> {v} (Stage 2: {d['stage2']})")
        else:
            print(f"    -> {v}")
        if d["s1"].get("mean") is not None and d["s1"]["mean"] > AUDIT_MEAN:
            print("    AUDIT TRIGGER: mean above +1.5c")
        if d["stage1"] != "NOT_YET_FALSIFIED" and hold:
            print(f"    (information: holdout not read for the verdict; {len(hold)} holdout entries exist)")
    print("-- pooled, information only (not tries) --")
    for name, group in (("six commodities", COMMODITIES), ("two coins", COINS)):
        es = [e for e in ents if e["series"] in group]
        disc, hold = split(es)
        A._row(f"pooled {name}, discovery", disc)
        A._row(f"pooled {name}, holdout", hold)


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
