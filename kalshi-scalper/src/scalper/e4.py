"""E4 (README, Pre-registration: E4): L1 unchanged on the hourly ladders (S&P 500, Bitcoin, Ethereum above/below). Research only: nothing here places an order.

History goes into its OWN database (`data/ladders.sqlite`), never `book.sqlite`. One candles request covers 100 strikes of one hourly close, and only the minutes around the entry candle are
fetched (420 s to 300 s before the close), because the rule reads one candle. Verdict words: FALSIFIED, NOT_YET_FALSIFIED. Nothing here means trade.

Usage: python -m scalper.e4 fetch      (resumable)
       python -m scalper.e4 run        (one read; prints the signal counts first)
"""
from __future__ import annotations

import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict

from . import api, backfill
from . import lstrats as L
from .altseries import summarize
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalps import STRESS, Z_BAR

LADDER_DB = DATA_DIR / "ladders.sqlite"
SERIES_DAYS = {"KXINXU": 40, "KXBTCD": 30, "KXETHD": 30}
WINDOW_BEFORE_S = 420          # candles from this long before the close ...
WINDOW_AFTER_S = 300           # ... to this long before it: the entry candle (360 s) is inside, with a minute either side
CHUNK = 100                    # tickers per candles request (the endpoint's limit)
PAUSE_S = 0.4
MDE_FLAG = 0.010               # above this, FALSIFIED means "not shown at this sample size"
PICK_PRICE = 0.925             # the one-entry-per-hour row


def group_by_close(listed: list[dict]) -> dict[int, list[dict]]:
    """Settled markets by close time (epoch s). A market with an unreadable close time or no yes/no result is dropped."""
    out: dict[int, list[dict]] = defaultdict(list)
    for m in listed:
        c = backfill.iso_ts(m.get("close_time"))
        if c is None or m.get("result") not in ("yes", "no"):
            continue
        out[c].append(m)
    return dict(out)


def chunks(items: list, n: int):
    for i in range(0, len(items), n):
        yield items[i:i + n]


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(LADDER_DB)
    db.executescript(backfill.SCHEMA)
    have = {r[0] for r in db.execute("SELECT ticker FROM market")}
    now = int(time.time())
    for series, days in SERIES_DAYS.items():
        listed = list(api.settled_markets(series, now - days * 86400, now))
        by_close = group_by_close(listed)
        todo = sum(1 for ms in by_close.values() for m in ms if m["ticker"] not in have)
        print(f"{series}: {len(listed)} settled markets in {len(by_close)} closes over {days} days, {todo} to fetch", flush=True)
        stored = 0
        for close_ts in sorted(by_close):
            ms = [m for m in by_close[close_ts] if m["ticker"] not in have]
            for chunk in chunks(ms, CHUNK):
                got = api.batch_candlesticks([m["ticker"] for m in chunk], close_ts - WINDOW_BEFORE_S, close_ts - WINDOW_AFTER_S)
                for m in chunk:
                    t = m["ticker"]
                    rows = [r for r in (backfill.parse_candle(x, t, series) for x in got.get(t, [])) if r]
                    db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
                    db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)",
                               (t, series, backfill.iso_ts(m.get("open_time")), close_ts, m.get("result"), m.get("floor_strike"), len(rows)))
                    have.add(t)
                    stored += 1
                db.commit()
                time.sleep(PAUSE_S)
            if stored and stored % 2000 < CHUNK:
                print(f"  {stored} stored", flush=True)
    print("done:", db.execute("SELECT COUNT(*) FROM market").fetchone()[0], "markets", flush=True)


def load() -> tuple[list[tuple], dict]:
    """(markets in the shape hold_rule reads, {ticker: strike})."""
    db = sqlite3.connect(LADDER_DB)
    by: dict = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
    strike: dict = {}
    for s, t, end, bc, ac, bh, al, close_ts, res, k in db.execute(
            "SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, c.bid_h, c.ask_l, m.close_ts, m.result, m.strike "
            "FROM candle c JOIN market m ON m.ticker = c.ticker ORDER BY c.ticker, c.end_ts"):
        m = by[t]
        m["c"].append((end, bc, ac, bh, al)); m["close"] = close_ts; m["res"] = res; m["s"] = s
        strike[t] = k
    return [(t, m["s"], m["c"], m["close"], m["res"]) for t, m in by.items()], strike


def one_per_hour(entries: list[dict], strike: dict) -> list[dict]:
    """The entry whose price is nearest PICK_PRICE in each (series, close) hour, ties to the lower strike: what a live bot with a one-order-per-hour cap would take."""
    best: dict = {}
    for e in entries:
        key = (e["series"], e["close_ts"])
        k = strike.get(e["ticker"])
        rank = (abs(e["price"] - PICK_PRICE), k if k is not None else float("inf"))
        if key not in best or rank < best[key][0]:
            best[key] = (rank, e)
    return sorted((v[1] for v in best.values()), key=lambda e: e["close_ts"])


def hour_stats(entries: list[dict]) -> dict:
    """What is specific to ladders: entries per hour, the z clustered by hour, the worst single hour and the minimum detectable edge (day clustered)."""
    if not entries:
        return {"hours": 0}
    per_hour: dict = defaultdict(float)
    count: dict = defaultdict(int)
    for e in entries:
        per_hour[e["close_ts"]] += e["net"]
        count[e["close_ts"]] += 1
    _, _, zh = cluster_mean_z([(str(e["close_ts"]), e["net"]) for e in entries])
    _, se, _ = cluster_mean_z([(e["day"], e["net"]) for e in entries])
    return {"hours": len(per_hour), "per_hour": len(entries) / len(per_hour), "z_hour": zh, "worst_hour": min(per_hour.values()), "worst_n": count[min(per_hour, key=per_hour.get)],
            "mde": Z_BAR * se}


def _row(name: str, es: list[dict]) -> None:
    v, s = summarize(es)
    if not s["n"]:
        print(f"{name}: no observations -> {v}")
        return
    f = lambda x: f"{x * 100:+.2f}c"
    h = hour_stats(es)
    note = ""
    if v == "FALSIFIED" and h["mde"] > MDE_FLAG:
        note = "  (FALSIFIED here means NOT SHOWN at this sample size: the minimum detectable edge is above 1c)"
    print(f"{name}: n={s['n']} on {s['days']} days, net {f(s['mean'])} per contract, z(day) {s['z']:+.2f}, z(hour) {h['z_hour']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, "
          f"fees x{STRESS} {f(s['stress'])}, win {s['win']:.1%} against {s['paid']:.1%} paid -> {v}")
    print(f"    {h['hours']} hours with an entry ({h['per_hour']:.1f} entries each), minimum detectable edge {f(h['mde'])}, worst single hour {f(h['worst_hour'])} over its {h['worst_n']} entries{note}")


def run() -> None:
    markets, strike = load()
    print(f"{len(markets)} ladder markets in ladders.sqlite; signal counts first")
    ents = L.hold_rule(markets, **L.L1)
    for series in SERIES_DAYS:
        mine = [e for e in ents if e["series"] == series]
        _row(f"{series} (L1 unchanged)", mine)
        _row(f"{series} one entry per hour (information)", one_per_hour(mine, strike))


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
