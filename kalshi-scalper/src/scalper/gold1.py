"""GOLD1 Part I (README, Pre-registration: GOLD1): descriptive reads of L1 on gold against Bitcoin and Ethereum. Information only: no verdict, no try.
Usage: python -m scalper.gold1
"""
from __future__ import annotations

import csv
import math
import sqlite3
import statistics as st
from collections import defaultdict
from datetime import datetime, timezone

from .lstrats import L1, hold_rule
from .paths import DATA_DIR

FEE_ACTUAL = 0.005


def load(path):
    db = sqlite3.connect(path)
    by = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
    for s, t, end, bc, ac, close_ts, res in db.execute(
            "SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, m.close_ts, m.result FROM candle c JOIN market m ON m.ticker = c.ticker ORDER BY c.ticker, c.end_ts"):
        m = by[t]; m["c"].append((end, bc, ac)); m["close"] = close_ts; m["res"] = res; m["s"] = s
    return [(t, m["s"], m["c"], m["close"], m["res"]) for t, m in by.items()]


def features(markets, entries):
    idx = {t: (c, close) for t, _, c, close, _ in markets}
    for e in entries:
        c, close = idx[e["ticker"]]
        t = close - L1["left_s"]
        k = next(i for i, x in enumerate(c) if x[0] == t)
        sign = 1 if e["side"] == "yes" else -1
        mid = lambda x: (x[1] + x[2]) / 2 if sign == 1 else 1 - (x[1] + x[2]) / 2
        e["spread"] = round(c[k][2] - c[k][1], 4)
        e["d3"] = mid(c[k]) - mid(c[k - 3]) if k >= 3 and c[k - 3][0] == t - 180 else None
        win = [mid(x) for x in c[max(0, k - 5):k + 1]]
        e["rng5"] = max(win) - min(win)
        e["hour"] = datetime.fromtimestamp(e["close_ts"] - L1["left_s"], timezone.utc).hour
        e["week"] = datetime.fromtimestamp(e["close_ts"], timezone.utc).strftime("%G-W%V")
        e["loss"] = e["gross"] < 0
    return entries


def block(h):
    return "Asia 00-07" if h < 7 else "Europe 07-13" if h < 13 else "US 13-21" if h < 21 else "late 21-24"


def jeffreys(k, n):
    # Beta(k+.5, n-k+.5) quantiles by bisection on the regularised incomplete beta via a fine grid (no scipy)
    a, b = k + 0.5, n - k + 0.5
    xs = [i / 20000 for i in range(1, 20000)]
    pdf = [math.exp((a - 1) * math.log(x) + (b - 1) * math.log(1 - x)) for x in xs]
    tot = sum(pdf); cum = 0.0; lo = hi = None
    for x, p in zip(xs, pdf):
        cum += p / tot
        if lo is None and cum >= 0.025: lo = x
        if hi is None and cum >= 0.975: hi = x
    return lo, hi


def summ(es):
    if not es: return "n=0"
    n = len(es); m = st.mean(e["net"] for e in es); l = sum(e["loss"] for e in es)
    return f"n={n:5d} net {100*m:+6.2f}c loss {l:3d} ({100*l/n:4.1f}%)"


def main():
    wins = {"l1b (Aug6-Sep2)": DATA_DIR / "l1b.sqlite", "book (Sep2-Oct12)": DATA_DIR / "book.sqlite"}
    data = {}
    for w, p in wins.items():
        mk = load(p)
        es = features(mk, hold_rule(mk, L1["left_s"], L1["band"]))
        data[w] = es
    allp = [e for es in data.values() for e in es]
    for ser in ("KXGOLD15M", "KXBTC15M", "KXETH15M"):
        print(f"\n== {ser}")
        for w, es in data.items():
            print(f"  window {w:20s}", summ([e for e in es if e['series'] == ser]))
        mine = [e for e in allp if e["series"] == ser]
        print("  pooled              ", summ(mine))
        print("  by UTC block:")
        for b in ("Asia 00-07", "Europe 07-13", "US 13-21", "late 21-24"):
            print(f"    {b:13s}", summ([e for e in mine if block(e['hour']) == b]))
        wk = defaultdict(list)
        for e in mine: wk[e["week"]].append(e)
        pos = sum(1 for v in wk.values() if st.mean(x["net"] for x in v) > 0)
        print(f"  weeks positive: {pos} of {len(wk)}; weekly net (c):", " ".join(f"{100*st.mean(x['net'] for x in v):+.1f}" for _, v in sorted(wk.items())))
        print("  features: mean price %.3f | spread>3c share %.1f%% | mean spread %.2fc | mean |d3| %.2fc | mean rng5 %.2fc | entries/day %.1f" % (
            st.mean(e["price"] for e in mine), 100 * sum(e["spread"] > 0.03 for e in mine) / len(mine), 100 * st.mean(e["spread"] for e in mine),
            100 * st.mean(abs(e["d3"]) for e in mine if e["d3"] is not None), 100 * st.mean(e["rng5"] for e in mine),
            len(mine) / len({e["day"] for e in mine})))
        print("  calibration (price bucket: avg price paid vs realised win rate):")
        for lo, hi in ((0.88, 0.91), (0.91, 0.94), (0.94, 0.9701)):
            b = [e for e in mine if lo <= e["price"] < hi]
            if b: print(f"    {lo:.2f}-{min(hi,0.97):.2f} n={len(b):4d} priced {100*st.mean(e['price'] for e in b):5.1f}%  won {100*(1-sum(e['loss'] for e in b)/len(b)):5.1f}%  net {100*st.mean(e['net'] for e in b):+5.2f}c")
        k, n = sum(e["loss"] for e in mine), len(mine)
        lo, hi = jeffreys(k, n)
        print(f"  loss rate {100*k/n:.2f}% ({k}/{n}), Jeffreys 95% {100*lo:.2f}% to {100*hi:.2f}%")
        p = st.mean(e["price"] for e in mine)
        gain = 1 - p - FEE_ACTUAL
        print(f"  break-even loss rate at mean price {100*p:.1f}c, fee 0.50c: hold {100*gain/(gain+p+FEE_ACTUAL):.2f}% | with 25c exit filling at 25c {100*gain/(gain+p+FEE_ACTUAL-0.25):.2f}%")
    print("\n== diagnostics (gold orders, depth at the touch)")
    rows = [r for r in csv.DictReader(open(DATA_DIR.parent / "studies" / "order_diagnostics_2026-10-21.csv")) if "GOLD" in r["ticker"] and r["status"] == "filled"]
    ask = [float(r["askSize"]) for r in rows if r["askSize"]]; fc = [float(r["fillCount"]) for r in rows]
    print(f"  filled gold orders {len(rows)}; contracts per order mean {st.mean(fc):.1f} max {max(fc):.0f}; ask size seen median {st.median(ask):.0f} min {min(ask):.0f}")
    print(f"  orders at least as large as the displayed ask size: {sum(1 for r in rows if r['askSize'] and float(r['fillCount']) >= float(r['askSize']))}")
    print(f"  all bot orders for comparison, ask size median: {st.median([float(r['askSize']) for r in csv.DictReader(open(DATA_DIR.parent / 'studies' / 'order_diagnostics_2026-10-21.csv')) if r['askSize']]):.0f}")


if __name__ == "__main__":
    main()
