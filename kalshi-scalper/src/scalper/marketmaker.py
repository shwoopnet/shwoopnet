"""H5: quote both sides as a market maker. (Rules in the README, fixed 2026-10-06 before this was written.)

At every minute close from the first usable quote until 5 minutes before close, one contract is rested at
the YES bid and one at the YES ask. A bid fills when the tape prints strictly THROUGH it in the next minute
(a taker buying NO below our bid), an ask when a taker buying YES prints strictly above it. Inventory is
capped at 2 either way, quoting stops 5 minutes before close, and what is left is held to settlement. Every
fill pays Kalshi's taker fee formula, so a possible maker discount cannot flatter the result.

The decomposition printed beside the verdict says what a result means: profit from completed round trips
(the spread captured) against the result of the leftover inventory (adverse selection), and the fees.
A market's full tape is about 30,000 trades, so the raw trades are never stored: each market is simulated
as it is fetched and only its result is kept.

No verdict means "trade". Fewer than 300 markets is NOT_ENOUGH_DATA and crosses nothing off.

Usage: python -m scalper.marketmaker fetch    (resumable; the sample is fixed by the README)
       python -m scalper.marketmaker          (the report and the verdict)
"""
from __future__ import annotations

import os
import sqlite3
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from . import api
from .analyze import valid_quote
from .paths import DB
from .scalps import FEE_RATE, MIN_N, STRESS, judge
from .tape import parse_trade

MIN_LEFT_S = 300
CAP = 2
SAMPLE_EVERY = 4
WORKERS = int(os.environ.get("SCALPER_WORKERS", "4"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS mm(
  ticker TEXT PRIMARY KEY, series TEXT, close_ts INTEGER, result TEXT, n_buy INTEGER, n_sell INTEGER, inv_end INTEGER,
  pnl REAL, pnl_stress REAL, pnl_nofee REAL, pnl_atprice REAL, pnl_cap1 REAL, pnl_cap4 REAL,
  rt_gross REAL, leftover REAL, fees REAL, n_trades INTEGER);
"""


def fee(price: float, mult: float = 1.0) -> float:
    return FEE_RATE * mult * price * (1 - price)


def quote_minutes(candles: list[tuple], close_ts: int) -> list[tuple]:
    """(end, bid, ask) for every minute close with 5 or more minutes left and a usable two sided quote."""
    return [(e, b, a) for e, b, a in candles if close_ts - e >= MIN_LEFT_S and valid_quote(b, a)]


def fills_in(trades: list[tuple], t: int, bid: float, ask: float, strict: bool = True) -> tuple[bool, bool]:
    """Which of our two resting quotes the tape fills in (t, t + 60]. trades: (ts, taker_side, yes, no)."""
    bf = af = False
    for ts, taker, yes, _ in trades:
        if not (t < ts <= t + 60):
            continue
        y = round(yes, 4)
        if taker == "no" and (y < bid if strict else y <= bid):
            bf = True
        if taker == "yes" and (y > ask if strict else y >= ask):
            af = True
    return bf, af


def walk(quotes: list[tuple], trades: list[tuple], cap: int, strict: bool = True) -> tuple[list[tuple], int]:
    """The fills in order, [('b', price) or ('s', price)], and the closing inventory."""
    inv, out = 0, []
    for t, bid, ask in quotes:
        bf, af = fills_in(trades, t, bid, ask, strict)
        if bf and inv < cap:
            inv += 1
            out.append(("b", bid))
        if af and inv > -cap:
            inv -= 1
            out.append(("s", ask))
    return out, inv


def book(fl: list[tuple], inv: int, yes_won: bool, mult: float = 1.0) -> float:
    cash = sum((-p if k == "b" else p) - fee(p, mult) for k, p in fl)
    return cash + inv * (1.0 if yes_won else 0.0)


def simulate(candles: list[tuple], close_ts: int, result: str, trades: list[tuple]) -> dict | None:
    """One market. candles: (end, bid_c, ask_c) in time order. None if it never had a usable quote or did not resolve."""
    qs = quote_minutes(candles, close_ts)
    if not qs or result not in ("yes", "no"):
        return None
    yes = result == "yes"
    fl, inv = walk(qs, trades, CAP)
    buys = [p for k, p in fl if k == "b"]
    sells = [p for k, p in fl if k == "s"]
    k = min(len(buys), len(sells))
    rt = sum(sells[:k]) - sum(buys[:k])
    fees = sum(fee(p) for _, p in fl)
    pnl = book(fl, inv, yes)
    return {
        "n_buy": len(buys), "n_sell": len(sells), "inv_end": inv, "pnl": pnl,
        "pnl_stress": book(fl, inv, yes, STRESS), "pnl_nofee": book(fl, inv, yes, 0.0),
        "pnl_atprice": _atprice(qs, trades, yes),
        "pnl_cap1": _capped(qs, trades, yes, 1), "pnl_cap4": _capped(qs, trades, yes, 4),
        "rt_gross": rt, "leftover": pnl + fees - rt, "fees": fees,
    }


def _capped(qs, trades, yes, cap):
    fl, inv = walk(qs, trades, cap)
    return book(fl, inv, yes)


def _atprice(qs, trades, yes):
    fl, inv = walk(qs, trades, CAP, strict=False)
    return book(fl, inv, yes)


def sample(markets: list[tuple]) -> list[tuple]:
    """The fixed sample: per series, markets in close-time order, every SAMPLE_EVERY-th (by position, never by result)."""
    by: dict = defaultdict(list)
    for m in markets:
        by[m[1]].append(m)
    out = []
    for series in sorted(by):
        ms = sorted(by[series], key=lambda m: (m[3], m[0]))
        out += ms[::SAMPLE_EVERY]
    return out


def fetch_trades(ticker: str, lo: int, hi: int) -> list[tuple]:
    out, cur = [], None
    while True:
        p = {"ticker": ticker, "limit": 1000, "min_ts": lo, "max_ts": hi}
        if cur:
            p["cursor"] = cur
        d = api._get("/markets/trades", p)
        out += [(r[2], r[3], r[4], r[5]) for r in (parse_trade(t) for t in d.get("trades", [])) if r]
        cur = d.get("cursor")
        if not cur:
            return out


def load_markets(db) -> list[tuple]:
    by: dict = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
    q = ("SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, m.close_ts, m.result FROM candle c "
         "JOIN market m ON m.ticker = c.ticker ORDER BY c.ticker, c.end_ts")
    for s, t, end, bc, ac, close_ts, res in db.execute(q):
        m = by[t]
        m["c"].append((end, bc, ac)); m["close"] = close_ts; m["res"] = res; m["s"] = s
    return [(t, m["s"], m["c"], m["close"], m["res"]) for t, m in by.items()]


def run_fetch(limit: int | None = None) -> None:
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    done = {r[0] for r in db.execute("SELECT ticker FROM mm")}
    todo = [m for m in sample(load_markets(db)) if m[0] not in done and m[4] in ("yes", "no")]
    todo.sort(key=lambda m: -m[3])                       # newest first
    if limit:
        todo = todo[:limit]
    print(f"{len(todo)} markets to fetch", flush=True)
    t0, n = time.time(), 0

    def job(m):
        qs = quote_minutes(m[2], m[3])
        if not qs:
            return m, None, 0
        tr = fetch_trades(m[0], qs[0][0], qs[-1][0] + 60)
        return m, simulate(m[2], m[3], m[4], tr), len(tr)

    with ThreadPoolExecutor(WORKERS) as ex:
        futs = [ex.submit(job, m) for m in todo]
        for f in as_completed(futs):
            try:
                m, r, nt = f.result()
            except Exception as err:     # leave it unrecorded so a rerun retries it
                print(f"  error: {err}", flush=True)
                continue
            if r is not None:
                db.execute("INSERT OR REPLACE INTO mm VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (m[0], m[1], m[3], m[4], r["n_buy"], r["n_sell"], r["inv_end"], r["pnl"], r["pnl_stress"], r["pnl_nofee"],
                            r["pnl_atprice"], r["pnl_cap1"], r["pnl_cap4"], r["rt_gross"], r["leftover"], r["fees"], nt))
            n += 1
            if n % 10 == 0:
                db.commit()
                rate = n / (time.time() - t0)
                print(f"  {n}/{len(todo)} markets, {rate * 60:.1f}/min, about {(len(todo) - n) / rate / 3600:.1f}h left", flush=True)
    db.commit()
    print(f"done: {n} markets", flush=True)


def verdict(rows: list[tuple], midpoint: float) -> tuple[str, list[dict]]:
    """rows: (day, close_ts, pnl, pnl_stress). NOT_ENOUGH_DATA under MIN_N markets, else the README's kill criteria."""
    if len(rows) < MIN_N:
        return "NOT_ENOUGH_DATA", [{"band": "mm", "n": len(rows)}]
    return judge({"mm": rows}, midpoint)


def main() -> None:
    db = sqlite3.connect(DB)
    if not db.execute("SELECT name FROM sqlite_master WHERE name='mm'").fetchone():
        print("No market making results. Run: python -m scalper.marketmaker fetch")
        return
    rs = db.execute("SELECT close_ts, pnl, pnl_stress, pnl_nofee, pnl_atprice, pnl_cap1, pnl_cap4, rt_gross, leftover, fees, "
                    "n_buy, n_sell, inv_end FROM mm").fetchall()
    if not rs:
        print("No market making results. Run: python -m scalper.marketmaker fetch")
        return
    allc = [r[0] for r in db.execute("SELECT close_ts FROM market")]
    mid = (min(allc) + max(allc)) / 2
    rows = [(datetime.fromtimestamp(r[0], timezone.utc).strftime("%Y-%m-%d"), r[0], r[1], r[2]) for r in rs]
    v, summ = verdict(rows, mid)
    n = len(rs)
    mean = lambda i: sum(r[i] for r in rs) / n * 100
    print(f"H5: quote one contract at the YES bid and ask every minute, inventory cap {CAP}, held to settlement. {n} sampled markets. Cents per market.\n")
    if v == "NOT_ENOUGH_DATA":
        print(f"VERDICT (pre-registered): NOT_ENOUGH_DATA, {n} markets (needs {MIN_N}). Nothing is crossed off.")
    else:
        s = summ[0]
        print(f"{'markets':>8} {'mean':>7} {'se':>6} {'z':>6} {'1st half':>9} {'2nd half':>9} {'fees x1.2':>10} {'detectable':>11} {'passes':>7}")
        print(f"{s['n']:>8} {s['mean']*100:>7.2f} {s['se']*100:>6.2f} {s['z']:>6.2f} {s['h1']*100:>9.2f} {s['h2']*100:>9.2f} "
              f"{s['stress']*100:>10.2f} {s['detectable']*100:>10.2f}c {str(s['ok']):>7}")
        print(f"\nVERDICT (pre-registered, bar z>=2.1, markets>={MIN_N}, both halves, fees x{STRESS}): {v}")
        print("  " + ("The two sided quote does not clear every criterion." if v == "FALSIFIED" else "Permission to test on unseen days. Not evidence of an edge."))
    print("\nWHAT IT MADE AND WHAT IT GAVE BACK (mean cents per market):")
    print(f"  completed round trips (spread captured, before fees): {mean(7):>7.2f}c")
    print(f"  leftover inventory held to settlement (adverse selection): {mean(8):>7.2f}c")
    print(f"  fees paid: {-mean(9):>7.2f}c        => net {mean(1):>7.2f}c")
    print(f"  fills per market: {sum(r[10] for r in rs)/n:.2f} buys, {sum(r[11] for r in rs)/n:.2f} sells; "
          f"{sum(1 for r in rs if r[12] == 0)/n*100:.0f}% of markets ended flat")
    print("\nINFORMATION ONLY, affects nothing above. Mean net per market:")
    for name, i in (("primary", 1), ("no fee at all", 3), ("fills also when a print is AT our price", 4), ("inventory cap 1", 5), ("inventory cap 4", 6)):
        print(f"{name:>42}: {mean(i):>7.2f}c")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        run_fetch(int(sys.argv[2]) if len(sys.argv) > 2 else None)
    else:
        main()
