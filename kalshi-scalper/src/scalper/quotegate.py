"""H6: H5's two sided quote, but no quote on the side a move has just made stale. (Rules in the README, fixed
2026-10-07 before this was written.)

`move` is the change in the YES mid from the previous minute close to this one, known at the quote. A fall of
1c or more means a resting bid would be hit by a price that keeps falling, so no bid is placed that minute; a
rise of 1c or more means no ask. Anything else, and a market's first quote minute, quotes both sides. The
previous minute must be the ADJACENT minute with a usable quote; if the book was unusable a minute ago we do
not know the move, so both sides are quoted (what H5 would have done).

Everything else is H5 unchanged, and H5's always-quote rule is run on the same tape as the control, so any
difference is the rule and not the markets. The sample is disjoint from H5's (positions 2, 6, 10...).

No verdict means "trade". Fewer than 300 markets is NOT_ENOUGH_DATA and crosses nothing off.

Usage: python -m scalper.quotegate fetch    (resumable)
       python -m scalper.quotegate          (the report and the verdict)
"""
from __future__ import annotations

import os
import sqlite3
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .marketmaker import CAP, MIN_LEFT_S, SAMPLE_EVERY, book, fee, fetch_trades, fills_in, load_markets, quote_minutes, verdict, walk
from .paths import DB
from .scalps import MIN_N, STRESS

OFFSET = 2                 # H5 used positions 0, 4, 8...
MOVE = 0.01                # the smallest move the data can show; fixed, never tuned
WORKERS = int(os.environ.get("SCALPER_WORKERS", "4"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS mm6(
  ticker TEXT PRIMARY KEY, series TEXT, close_ts INTEGER, result TEXT, n_buy INTEGER, n_sell INTEGER, inv_end INTEGER,
  pnl REAL, pnl_stress REAL, pnl_nofee REAL, pnl_atprice REAL, rt_gross REAL, leftover REAL, fees REAL,
  ctl_pnl REAL, quotes INTEGER, skipped INTEGER, skip_gave_up REAL, n_trades INTEGER);
"""


def sides(quotes: list[tuple]) -> list[tuple]:
    """(t, bid, ask, bid_ok, ask_ok) for each quote minute under the H6 gate."""
    out, prev = [], None
    for t, bid, ask in quotes:
        mid = (bid + ask) / 2
        bid_ok = ask_ok = True
        if prev is not None and prev[0] == t - 60:
            move = round(mid - prev[1], 4)
            if move <= -MOVE:
                bid_ok = False
            elif move >= MOVE:
                ask_ok = False
        out.append((t, bid, ask, bid_ok, ask_ok))
        prev = (t, mid)
    return out


def gated_walk(sq: list[tuple], trades: list[tuple], cap: int, strict: bool = True) -> tuple[list[tuple], int]:
    inv, out = 0, []
    for t, bid, ask, bid_ok, ask_ok in sq:
        bf, af = fills_in(trades, t, bid, ask, strict)
        if bf and bid_ok and inv < cap:
            inv += 1
            out.append(("b", bid))
        if af and ask_ok and inv > -cap:
            inv -= 1
            out.append(("s", ask))
    return out, inv


def gave_up(sq: list[tuple], trades: list[tuple], yes: bool) -> float:
    """Net result, with fee, of the fills the gate refused, each valued at settlement. Ignores the cap (the gate
    changes inventory, so this is a reading of the refused fills and not an exact difference of two runs)."""
    tot, w = 0.0, 1.0 if yes else 0.0
    for t, bid, ask, bid_ok, ask_ok in sq:
        bf, af = fills_in(trades, t, bid, ask)
        if bf and not bid_ok:
            tot += w - bid - fee(bid)
        if af and not ask_ok:
            tot += ask - w - fee(ask)
    return tot


def simulate(candles: list[tuple], close_ts: int, result: str, trades: list[tuple]) -> dict | None:
    qs = quote_minutes(candles, close_ts)
    if not qs or result not in ("yes", "no"):
        return None
    yes = result == "yes"
    sq = sides(qs)
    fl, inv = gated_walk(sq, trades, CAP)
    buys = [p for k, p in fl if k == "b"]
    sells = [p for k, p in fl if k == "s"]
    k = min(len(buys), len(sells))
    rt = sum(sells[:k]) - sum(buys[:k])
    fees = sum(fee(p) for _, p in fl)
    pnl = book(fl, inv, yes)
    ctl = book(*walk(qs, trades, CAP), yes)
    fa, ia = gated_walk(sq, trades, CAP, strict=False)
    return {
        "n_buy": len(buys), "n_sell": len(sells), "inv_end": inv, "pnl": pnl,
        "pnl_stress": book(fl, inv, yes, STRESS), "pnl_nofee": book(fl, inv, yes, 0.0), "pnl_atprice": book(fa, ia, yes),
        "rt_gross": rt, "leftover": pnl + fees - rt, "fees": fees, "ctl_pnl": ctl,
        "quotes": 2 * len(sq), "skipped": sum((not b) + (not a) for _, _, _, b, a in sq),
        "skip_gave_up": gave_up(sq, trades, yes),
    }


def sample(markets: list[tuple]) -> list[tuple]:
    """Per series, markets in close-time order, positions OFFSET, OFFSET + 4, ... by position, never by result."""
    by: dict = defaultdict(list)
    for m in markets:
        by[m[1]].append(m)
    out = []
    for series in sorted(by):
        out += sorted(by[series], key=lambda m: (m[3], m[0]))[OFFSET::SAMPLE_EVERY]
    return out


def run_fetch(limit: int | None = None) -> None:
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    done = {r[0] for r in db.execute("SELECT ticker FROM mm6")}
    todo = [m for m in sample(load_markets(db)) if m[0] not in done and m[4] in ("yes", "no")]
    todo.sort(key=lambda m: -m[3])
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
            except Exception as err:     # unrecorded, so a rerun retries it
                print(f"  error: {err}", flush=True)
                continue
            if r is not None:
                db.execute("INSERT OR REPLACE INTO mm6 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (m[0], m[1], m[3], m[4], r["n_buy"], r["n_sell"], r["inv_end"], r["pnl"], r["pnl_stress"], r["pnl_nofee"],
                            r["pnl_atprice"], r["rt_gross"], r["leftover"], r["fees"], r["ctl_pnl"], r["quotes"], r["skipped"],
                            r["skip_gave_up"], nt))
            n += 1
            if n % 10 == 0:
                db.commit()
                rate = n / (time.time() - t0)
                print(f"  {n}/{len(todo)} markets, {rate * 60:.1f}/min, about {(len(todo) - n) / rate / 3600:.1f}h left", flush=True)
    db.commit()
    print(f"done: {n} markets", flush=True)


def main() -> None:
    db = sqlite3.connect(DB)
    if not db.execute("SELECT name FROM sqlite_master WHERE name='mm6'").fetchone():
        print("No H6 results. Run: python -m scalper.quotegate fetch")
        return
    rs = db.execute("SELECT close_ts, pnl, pnl_stress, pnl_nofee, pnl_atprice, rt_gross, leftover, fees, n_buy, n_sell, inv_end, "
                    "ctl_pnl, quotes, skipped, skip_gave_up FROM mm6").fetchall()
    if not rs:
        print("No H6 results. Run: python -m scalper.quotegate fetch")
        return
    allc = [r[0] for r in db.execute("SELECT close_ts FROM market")]
    mid = (min(allc) + max(allc)) / 2
    rows = [(datetime.fromtimestamp(r[0], timezone.utc).strftime("%Y-%m-%d"), r[0], r[1], r[2]) for r in rs]
    v, summ = verdict(rows, mid)
    n = len(rs)
    mean = lambda i: sum(r[i] for r in rs) / n * 100
    print(f"H6: H5's quote, no bid after a fall of {MOVE*100:.0f}c, no ask after a rise of {MOVE*100:.0f}c. {n} sampled markets. Cents per market.\n")
    if v == "NOT_ENOUGH_DATA":
        print(f"VERDICT (pre-registered): NOT_ENOUGH_DATA, {n} markets (needs {MIN_N}). Nothing is crossed off.")
    else:
        s = summ[0]
        print(f"{'markets':>8} {'mean':>7} {'se':>6} {'z':>6} {'1st half':>9} {'2nd half':>9} {'fees x1.2':>10} {'detectable':>11} {'passes':>7}")
        print(f"{s['n']:>8} {s['mean']*100:>7.2f} {s['se']*100:>6.2f} {s['z']:>6.2f} {s['h1']*100:>9.2f} {s['h2']*100:>9.2f} "
              f"{s['stress']*100:>10.2f} {s['detectable']*100:>10.2f}c {str(s['ok']):>7}")
        print(f"\nVERDICT (pre-registered, bar z>=2.1, markets>={MIN_N}, both halves, fees x{STRESS}): {v}")
        print("  " + ("The gated quote does not clear every criterion." if v == "FALSIFIED" else "Permission to test on unseen days. Not evidence of an edge."))
    print("\nWHAT IT MADE AND WHAT IT GAVE BACK (mean cents per market):")
    print(f"  completed round trips (spread captured, before fees): {mean(5):>7.2f}c")
    print(f"  leftover inventory held to settlement (adverse selection): {mean(6):>7.2f}c")
    print(f"  fees paid: {-mean(7):>7.2f}c        => net {mean(1):>7.2f}c")
    print(f"  fills per market: {sum(r[8] for r in rs)/n:.2f} buys, {sum(r[9] for r in rs)/n:.2f} sells; "
          f"{sum(1 for r in rs if r[10] == 0)/n*100:.0f}% of markets ended flat")
    print(f"  quote sides skipped by the gate: {sum(r[13] for r in rs)/max(1, sum(r[12] for r in rs))*100:.1f}%; "
          f"what the refused fills would have made: {mean(14):>7.2f}c a market (negative means the gate refused losers)")
    print("\nINFORMATION ONLY, affects nothing above. Mean net per market:")
    for name, i in (("gated (primary)", 1), ("H5 always-quote CONTROL, same markets", 11), ("gated, no fee at all", 3), ("gated, fills also AT our price", 4)):
        print(f"{name:>42}: {mean(i):>7.2f}c")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        run_fetch(int(sys.argv[2]) if len(sys.argv) > 2 else None)
    else:
        main()
