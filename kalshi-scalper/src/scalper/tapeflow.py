"""T1, early taker flow (ledger row L11). The rule, universe, prediction and kill criteria are fixed in README.md ("Pre-registration: T1"), before any trade was fetched.

For every settled market in the most recent 30 days, sum the taker contracts by side over the first 5 minutes after the open (trades stamped at or after the open and
strictly before open + 300 s, and nothing else). Signal: at least 50 taker contracts and |YES minus NO| / total at least 0.60. Entry: the favoured side at the candle
ending 360 s after the open (it STARTS after the signal minute, so the fill is on a later bar than the signal), a real two sided quote required, hold to settlement,
one contract, fee 0.07 p (1 - p). Public endpoint only; no account, key or order.

Usage: python -m scalper.tapeflow fetch [days]     (resumable)
       python -m scalper.tapeflow run
"""
from __future__ import annotations

import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from . import api
from .analyze import valid_quote
from .calibration import cluster_mean_z
from .paths import DB
from .scalps import MIN_N, STRESS, Z_BAR, fee

WINDOW_S = 300          # trades in the first 5 minutes only
ENTRY_END_S = 360       # the candle that ends 360 s after the open starts after the signal
MIN_TOTAL = 50          # taker contracts in the window
MIN_TOTAL_STRICT = 100  # the kill criterion: the result must survive this
MIN_IMBALANCE = 0.60
MIN_DAYS = 5
PAUSE_S = 0.12

SCHEMA = "CREATE TABLE IF NOT EXISTS tapeflow(ticker TEXT PRIMARY KEY, yes_ct REAL, no_ct REAL, n_trades INTEGER)"


def window_flow(trades: list[dict], open_ts: int) -> tuple[float, float, int]:
    """(YES contracts, NO contracts, trades) from the trades that fall in [open, open + WINDOW_S). A trade stamped later is never counted."""
    yes = no = 0.0
    n = 0
    for t in trades:
        ts = int(datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp())
        if not (open_ts <= ts < open_ts + WINDOW_S):
            continue
        c = api.f(t.get("count_fp")) or 0.0
        if t.get("taker_side") == "yes":
            yes += c
        elif t.get("taker_side") == "no":
            no += c
        n += 1
    return yes, no, n


def fetch_one(ticker: str, open_ts: int) -> tuple[float, float, int]:
    trades, cursor = [], None
    while True:
        params = {"ticker": ticker, "min_ts": open_ts, "max_ts": open_ts + WINDOW_S - 1, "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        r = api._get("/markets/trades", params)
        trades += r.get("trades", [])
        cursor = r.get("cursor")
        time.sleep(PAUSE_S)
        if not cursor or not r.get("trades"):
            break
    return window_flow(trades, open_ts)


def fetch(days: int = 30) -> None:
    db = sqlite3.connect(DB)
    db.execute(SCHEMA)
    last = db.execute("SELECT MAX(close_ts) FROM market").fetchone()[0]
    rows = db.execute("SELECT ticker, open_ts FROM market WHERE close_ts >= ? AND result IN ('yes','no') ORDER BY close_ts", (last - days * 86400,)).fetchall()
    have = {r[0] for r in db.execute("SELECT ticker FROM tapeflow")}
    todo = [r for r in rows if r[0] not in have]
    print(f"{len(rows)} markets in the last {days} days, {len(todo)} to fetch")
    for i, (ticker, open_ts) in enumerate(todo, 1):
        y, n, k = fetch_one(ticker, open_ts)
        db.execute("INSERT OR REPLACE INTO tapeflow VALUES (?,?,?,?)", (ticker, y, n, k))
        if i % 50 == 0:
            db.commit(); print(f"  {i} fetched")
    db.commit()


def signals(rows: list[tuple], min_total: float = MIN_TOTAL) -> list[tuple]:
    """rows: (ticker, yes_ct, no_ct). Returns (ticker, side) for markets that clear the volume and imbalance bars."""
    out = []
    for ticker, y, n in rows:
        tot = y + n
        if tot < min_total or tot <= 0:
            continue
        imb = (y - n) / tot
        if abs(imb) >= MIN_IMBALANCE:
            out.append((ticker, "yes" if imb > 0 else "no"))
    return out


def entries(db, min_total: float = MIN_TOTAL) -> list[dict]:
    flow = db.execute("SELECT ticker, yes_ct, no_ct FROM tapeflow").fetchall()
    out = []
    for ticker, side in signals(flow, min_total):
        open_ts, close_ts, res = db.execute("SELECT open_ts, close_ts, result FROM market WHERE ticker=?", (ticker,)).fetchone()
        c = db.execute("SELECT bid_c, ask_c FROM candle WHERE ticker=? AND end_ts=?", (ticker, open_ts + ENTRY_END_S)).fetchone()
        if c is None or not valid_quote(c[0], c[1]):
            continue
        price = c[1] if side == "yes" else round(1 - c[0], 4)
        won = (res == "yes") == (side == "yes")
        gross = (1.0 if won else 0.0) - price
        out.append({"ticker": ticker, "day": datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d"), "close_ts": close_ts, "price": price,
                    "won": won, "net": gross - fee(price), "stress": gross - fee(price, STRESS)})
    return sorted(out, key=lambda e: e["close_ts"])


def verdict(es: list[dict], es_strict: list[dict]) -> tuple[str, dict]:
    mean, se, z = cluster_mean_z([(e["day"], e["net"]) for e in es])
    days = sorted({e["day"] for e in es})
    mid = (es[0]["close_ts"] + es[-1]["close_ts"]) / 2 if es else 0
    h1 = [e["net"] for e in es if e["close_ts"] < mid]
    h2 = [e["net"] for e in es if e["close_ts"] >= mid]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    stress = sum(e["stress"] for e in es) / len(es) if es else 0.0
    strict_mean = sum(e["net"] for e in es_strict) / len(es_strict) if es_strict else 0.0
    ok = len(es) >= MIN_N and len(days) >= MIN_DAYS and z >= Z_BAR and mean > 0 and stress > 0 and m1 > 0 and m2 > 0 and strict_mean > 0
    win = sum(e["won"] for e in es) / len(es) if es else 0.0
    paid = sum(e["price"] for e in es) / len(es) if es else 0.0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": len(es), "days": len(days), "mean": mean, "z": z, "h1": m1, "h2": m2, "stress": stress,
            "strict_n": len(es_strict), "strict_mean": strict_mean, "win": win, "paid": paid}


def run() -> None:
    db = sqlite3.connect(DB)
    es, strict = entries(db), entries(db, MIN_TOTAL_STRICT)
    v, s = verdict(es, strict)
    f = lambda x: f"{x * 100:+.2f}c"
    print(f"T1 early taker flow: n={s['n']} on {s['days']} days, net {f(s['mean'])} per contract, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, "
          f"fees x{STRESS} {f(s['stress'])}, win {s['win']:.1%} against {s['paid']:.1%} paid, at 100 contracts n={s['strict_n']} net {f(s['strict_mean'])}")
    print(f"VERDICT: {v}")


if __name__ == "__main__":
    fetch(int(sys.argv[2]) if len(sys.argv) > 2 else 30) if sys.argv[1:2] == ["fetch"] else run()
