"""LOCK2H: LOCK2's coincident-close locks looked for in history (registered in README.md before any pairing).
Usage: python -m scalper.lock2h run      (reads data/lad2.sqlite, data/book.sqlite, data/fresh.sqlite; public data only)
"""
from __future__ import annotations

import sqlite3
import sys
from collections import defaultdict

from .fees import taker_fee

FILES15 = ("data/book.sqlite", "data/fresh.sqlite")


def ask_ok(a):
    return a is not None and 0 < a < 0.99


def bid_ok(b):
    return b is not None and b > 0


def main() -> None:
    if sys.argv[1:] != ["run"]:
        print(__doc__)
        return
    lad = sqlite3.connect("data/lad2.sqlite")
    strikes = defaultdict(list)
    for t, c, k in lad.execute("select ticker, close_ts, strike from market"):
        strikes[c].append((t, k))
    lq = defaultdict(dict)
    for t, e, b, a, v in lad.execute("select ticker, end_ts, bid_c, ask_c, volume from candle"):
        lq[t][e] = (b, a, v)
    m15, q15 = {}, defaultdict(dict)
    for f in FILES15:
        db = sqlite3.connect(f)
        for t, c, k in db.execute("select ticker, close_ts, strike from market where series='KXBTC15M'"):
            if c in strikes and k:
                m15[c] = (t, k)
        for t, e, b, a, v in db.execute("select ticker, end_ts, bid_c, ask_c, volume from candle where series='KXBTC15M'"):
            q15[t][e] = (b, a, v)
    closes = sorted(c for c in strikes if c in m15)
    res = {1: [], 10: []}
    for C in (1, 10):
        for vol_req in (False, True):
            best_per_close, lock_closes, runs = [], 0, []
            for c in closes:
                t15, k0 = m15[c]
                best, run, maxrun = -9.0, 0, 0
                for e in range(c - 14 * 60, c - 59, 60):
                    q = q15[t15].get(e)
                    if not q:
                        run = 0
                        continue
                    b15, a15, v15 = q
                    vals = []
                    for tl, k in strikes[c]:
                        ql = lq[tl].get(e)
                        if not ql:
                            continue
                        bl, al, vl = ql
                        if vol_req and not ((v15 or 0) > 0 and (vl or 0) > 0):
                            continue
                        if k >= k0 and ask_ok(a15) and bid_ok(bl):
                            p1, p2 = a15, 1 - bl
                            vals.append(1 - p1 - p2 - (taker_fee(p1, C) + taker_fee(p2, C)) / C)
                        if k < k0 and bid_ok(b15) and ask_ok(al):
                            p1, p2 = 1 - b15, al
                            vals.append(1 - p1 - p2 - (taker_fee(p1, C) + taker_fee(p2, C)) / C)
                    m = max(vals) if vals else -9.0
                    best = max(best, m)
                    run = run + 1 if m >= 0.01 else 0
                    maxrun = max(maxrun, run)
                best_per_close.append(best)
                if best >= 0.01:
                    lock_closes += 1
                    runs.append(maxrun)
            seen = [b for b in best_per_close if b > -9]
            print(f"C={C:2d} volume>0 both={vol_req}: closes {len(closes)} (with a pairable minute {len(seen)}); "
                  f"closes with a lock >= 1.0c: {lock_closes}; largest lock {100 * max(seen):.2f}c; "
                  f"median best {100 * sorted(seen)[len(seen) // 2]:.2f}c; longest run (minutes) {max(runs) if runs else 0}")


if __name__ == "__main__":
    main()
