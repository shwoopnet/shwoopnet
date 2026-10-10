"""E1 and E2 (README, Pre-registration: E1 and E2): L1 unchanged on the ETH and SOL 15 minute markets. Research only: nothing here places an order.

The history goes into its OWN database (`data/alts.sqlite`), never `book.sqlite`, so the Bitcoin and gold history and every earlier result stay exactly as they were.

Usage: python -m scalper.altseries fetch      (about 66 days of settled markets with 1 minute candles; resumable)
       python -m scalper.altseries run        (one read; prints the signal counts first)
"""
from __future__ import annotations

import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict

from . import backfill
from . import lstrats as L
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalps import MIN_N, STRESS, Z_BAR
from .scalps import load as load_main

ALT_DB = DATA_DIR / "alts.sqlite"
ALTS = ("KXETH15M", "KXSOL15M")
DAYS = 66            # Kalshi keeps 1 minute candles about this far back
MIN_DAYS = 5


def fetch(days: int = DAYS) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(ALT_DB)
    db.executescript(backfill.SCHEMA)
    saved, backfill.SERIES = backfill.SERIES, ALTS     # the shared fetcher walks backfill.SERIES; restored below so nothing else is affected
    try:
        now = int(time.time())
        stored, skipped, empty = backfill._fetch(db, now - days * 86400, now, f"in the last {days} days", skip_empty=True)
        print(f"done: {stored} new markets, {skipped} already stored, {empty} with no candles (not stored)", flush=True)
    finally:
        backfill.SERIES = saved


def load_alts() -> tuple[list[tuple], dict]:
    """(markets in the shape hold_rule reads, {(ticker, end_ts): traded volume of that candle})."""
    db = sqlite3.connect(ALT_DB)
    by: dict = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
    vol: dict = {}
    q = ("SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, c.bid_h, c.ask_l, c.volume, m.close_ts, m.result "
         "FROM candle c JOIN market m ON m.ticker = c.ticker ORDER BY c.ticker, c.end_ts")
    for s, t, end, bc, ac, bh, al, v, close_ts, res in db.execute(q):
        m = by[t]
        m["c"].append((end, bc, ac, bh, al)); m["close"] = close_ts; m["res"] = res; m["s"] = s
        vol[(t, end)] = v
    return [(t, m["s"], m["c"], m["close"], m["res"]) for t, m in by.items()], vol


def summarize(es: list[dict]) -> tuple[str, dict]:
    """The pre-registered pass bar, the same as every earlier test: at least MIN_N observations and MIN_DAYS days, day clustered z of at least Z_BAR, mean above
    zero, both halves of the days positive, and above zero with fees times STRESS. Anything else is FALSIFIED."""
    if not es:
        return "FALSIFIED", {"n": 0}
    es = sorted(es, key=lambda e: e["close_ts"])
    mean, se, z = cluster_mean_z([(e["day"], e["net"]) for e in es])
    days = sorted({e["day"] for e in es})
    mid = (es[0]["close_ts"] + es[-1]["close_ts"]) / 2
    h1 = [e["net"] for e in es if e["close_ts"] < mid]
    h2 = [e["net"] for e in es if e["close_ts"] >= mid]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    stress = sum(e["stress"] for e in es) / len(es)
    win = sum(1 for e in es if e["gross"] + e["price"] > 0.5) / len(es)
    ok = len(es) >= MIN_N and len(days) >= MIN_DAYS and z >= Z_BAR and mean > 0 and stress > 0 and m1 > 0 and m2 > 0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": len(es), "days": len(days), "mean": mean, "z": z, "h1": m1, "h2": m2, "stress": stress,
                                                           "win": win, "paid": sum(e["price"] for e in es) / len(es)}


def _row(name: str, es: list[dict], vols: list[float] | None = None) -> None:
    v, s = summarize(es)
    if not s["n"]:
        print(f"{name}: no observations -> {v}")
        return
    f = lambda x: f"{x * 100:+.2f}c"
    extra = f", median entry-minute volume {st.median(vols):,.0f} contracts" if vols else ""
    print(f"{name}: n={s['n']} on {s['days']} days ({s['n'] / s['days']:.1f}/day), net {f(s['mean'])} per contract, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, "
          f"fees x{STRESS} {f(s['stress'])}, win {s['win']:.1%} against {s['paid']:.1%} paid{extra} -> {v}")


def run() -> None:
    markets, vol = load_alts()
    print(f"{len(markets)} ETH and SOL markets in alts.sqlite; signal counts first")
    ents = L.hold_rule(markets, **L.L1)
    for series in ALTS:
        mine = [e for e in ents if e["series"] == series]
        vols = [vol.get((e["ticker"], e["close_ts"] - L.L1["left_s"])) for e in mine]
        _row(f"{series} (L1 unchanged)", mine, [v for v in vols if v is not None])
    print("-- reference, information only: the same rule on the Bitcoin and gold history --")
    main_markets, _ = load_main()
    ref = L.hold_rule(main_markets, **L.L1)
    for series in ("KXBTC15M", "KXGOLD15M"):
        _row(f"{series} (L1 unchanged)", [e for e in ref if e["series"] == series])


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
