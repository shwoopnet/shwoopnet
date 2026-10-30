"""RACELOCK: structure of the five Coin Race books (KXCRYPTOLEAD15M). Research only, public data.
Stage t1 (info + Dutch book locks) reads NO result. Stage t2 reads the result column (after registration).
Usage: PYTHONPATH=src python -m scalper.racelock t1|t2
"""
from __future__ import annotations

import datetime
import json
import math
import sqlite3
import statistics as st
import sys
from collections import defaultdict

DB = "data/racelock/candles.sqlite"
MK = "data/newh15/mk_KXCRYPTOLEAD15M.json"
COINS = ["BTC", "ETH", "SOL", "XRP", "HYPE"]
LOOK, FILL, EARLY = 540, 480, 600
W = {"disc": (1787529600 - 0, 0)}


def utc(y, m, d):
    return int(datetime.datetime(y, m, d, tzinfo=datetime.timezone.utc).timestamp())


WINDOWS = [("discovery", utc(2026, 8, 24), utc(2026, 9, 28)), ("validation", utc(2026, 9, 28), utc(2026, 10, 18)),
           ("holdout", utc(2026, 10, 18), utc(2026, 11, 1))]


def window_of(close_ts):
    for n, a, b in WINDOWS:
        if a <= close_ts < b:
            return n
    return None


def fee(p, c):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def load():
    c = sqlite3.connect(DB)
    ev = {}
    for tk, e, cl in c.execute("SELECT ticker,event,close_ts FROM market"):
        coin = tk.rsplit("-", 1)[1]
        ev.setdefault(e, {"close": cl, "legs": {}})["legs"][coin] = tk
    q = {}
    for tk, ts_, b, a, p, v in c.execute("SELECT ticker,end_ts,bid_c,ask_c,price_c,volume FROM candle"):
        q[(tk, ts_)] = (b, a, v)
    return ev, q


def quote(q, ev, coin, off):
    tk = ev["legs"].get(coin)
    r = q.get((tk, ev["close"] - off))
    if not r:
        return None
    b, a, v = r
    if b is None or a is None or not (0 < b < a < 1):
        return None
    return b, a, v or 0.0


def five(q, ev, off):
    if set(ev["legs"]) != set(COINS):
        return None
    out = {}
    for k in COINS:
        r = quote(q, ev, k, off)
        out[k] = r
    return out


def pctl(x, p):
    x = sorted(x)
    return x[int(p * (len(x) - 1))] if x else float("nan")


def locks(legs, C):
    """legs: coin -> (bid, ask, vol), all present. Returns (yes_profit_dollars, no_profit_dollars)."""
    yes_cost = sum(C * l[1] + fee(l[1], C) for l in legs.values())
    no_cost = sum(C * (1 - l[0]) + fee(1 - l[0], C) for l in legs.values())
    return C - yes_cost, 4 * C - no_cost


def t1():
    ev, q = load()
    res = {}
    for off, name in ((EARLY, "600"), (LOOK, "540 look"), (FILL, "480 fill")):
        by = defaultdict(lambda: defaultdict(list))
        for e, x in ev.items():
            w = window_of(x["close"])
            if not w:
                continue
            by[w]["events"].append(1)
            l5 = five(q, x, off)
            if l5 is None:
                by[w]["incomplete_listing"].append(1)
                continue
            miss = sum(1 for v in l5.values() if v is None)
            by[w]["miss%d" % miss].append(1)
            for k, v in l5.items():
                if v is None:
                    by[w]["leg_missing_" + k].append(1)
                else:
                    by[w]["spread"].append(v[1] - v[0])
            if miss:
                continue
            by[w]["full"].append(1)
            sa = sum(v[1] for v in l5.values())
            sb = sum(v[0] for v in l5.values())
            by[w]["sum_ask"].append(sa)
            by[w]["sum_bid"].append(sb)
            by[w]["sum_ask_m1"].append(sa - 1)
            by[w]["no_cost_slack"].append(sb - 1)
            for C in (1, 10):
                py, pn = locks(l5, C)
                zero_vol = any(v[2] == 0 for v in l5.values())
                if py > 0:
                    by[w]["yes_lock_C%d" % C].append(py / C * 100)
                    if not zero_vol:
                        by[w]["yes_lock_vol_C%d" % C].append(py / C * 100)
                if pn > 0:
                    by[w]["no_lock_C%d" % C].append(pn / C * 100)
                    if not zero_vol:
                        by[w]["no_lock_vol_C%d" % C].append(pn / C * 100)
            # fees x1.2 at C=10
            C = 10
            ycost = sum(C * l[1] + 1.2 * fee(l[1], C) for l in l5.values())
            ncost = sum(C * (1 - l[0]) + 1.2 * fee(1 - l[0], C) for l in l5.values())
            if C - ycost > 0:
                by[w]["yes_lock_x12"].append(1)
            if 4 * C - ncost > 0:
                by[w]["no_lock_x12"].append(1)
            # fee-free lock (raw overround sign)
            if sa < 1:
                by[w]["yes_raw_under1"].append(1)
            if sb > 1:
                by[w]["no_raw_over1"].append(1)
        res[name] = by
    for name, by in res.items():
        print("== candle", name)
        for w, d in by.items():
            full = len(d["full"])
            print(" ", w, "events", len(d["events"]), "five-listed-and-quoted", full,
                  "incomplete_listing", len(d["incomplete_listing"]),
                  "miss0..5", [len(d["miss%d" % i]) for i in range(6)])
            print("    leg missing", {k: len(d["leg_missing_" + k]) for k in COINS})
            if full:
                print("    sum_ask p10/med/p90 %.3f %.3f %.3f" % (pctl(d["sum_ask"], .1), st.median(d["sum_ask"]), pctl(d["sum_ask"], .9)),
                      "min %.3f" % min(d["sum_ask"]))
                print("    sum_bid p10/med/p90 %.3f %.3f %.3f" % (pctl(d["sum_bid"], .1), st.median(d["sum_bid"]), pctl(d["sum_bid"], .9)),
                      "max %.3f" % max(d["sum_bid"]))
                print("    median spread/leg %.3f  p90 %.3f" % (st.median(d["spread"]), pctl(d["spread"], .9)))
                print("    raw sum_ask<1:", len(d["yes_raw_under1"]), " raw sum_bid>1:", len(d["no_raw_over1"]))
                for C in (1, 10):
                    ly, ln = d["yes_lock_C%d" % C], d["no_lock_C%d" % C]
                    print("    C=%d YES locks after fees %d (vol>0 all legs %d) mean cents/set %s | NO locks %d (vol>0 %d) mean cents/set %s" % (
                        C, len(ly), len(d["yes_lock_vol_C%d" % C]), "%.2f" % st.mean(ly) if ly else "-",
                        len(ln), len(d["no_lock_vol_C%d" % C]), "%.2f" % st.mean(ln) if ln else "-"))
                print("    fees x1.2 C=10: YES locks", len(d["yes_lock_x12"]), "NO locks", len(d["no_lock_x12"]))


def t2():
    ev, q = load()
    mk = json.load(open(MK))
    resmap = {m["ticker"]: m["result"] for m in mk}
    nyes = defaultdict(int)
    for m in mk:
        nyes[m["event_ticker"]] += m["result"] == "yes"
    print("events with exactly one YES:", sum(1 for v in nyes.values() if v == 1), "of", len(nyes),
          "other counts", {k: sum(1 for v in nyes.values() if v == k) for k in set(nyes.values())})
    rows = defaultdict(list)
    funnel = defaultdict(lambda: defaultdict(int))
    for e, x in ev.items():
        w = window_of(x["close"])
        if not w or nyes.get(e) != 1:
            continue
        funnel[w]["events"] += 1
        look = five(q, x, LOOK)
        if look is None or any(v is None for v in look.values()):
            funnel[w]["look_incomplete"] += 1
            continue
        mids = {k: (v[0] + v[1]) / 2 for k, v in look.items()}
        sm = sum(mids.values())
        pad = {k: look[k][1] - mids[k] / sm for k in COINS}
        pick = sorted(COINS, key=lambda k: (-round(pad[k], 12), -look[k][1], k))[0]
        f = quote(q, x, pick, FILL)
        if f is None:
            funnel[w]["fill_missing"] += 1
            continue
        px = 1 - f[0]
        if not (0.15 <= px <= 0.85):
            funnel[w]["no_fill_price_cap"] += 1
            continue
        yes_won = resmap[x["legs"][pick]] == "yes"
        win = not yes_won
        funnel[w]["trades"] += 1
        rows[w].append((x["close"], px, win, f[2], look[pick][1] - look[pick][0]))
    def stats(trs, C, mult):
        pnl = []
        for _, px, win, v, _s in trs:
            fe = mult * fee(px, C)
            fe = math.ceil(round(fe * 100, 9)) / 100 if mult == 1 else fe
            pnl.append((C * (1 - px) if win else -C * px) - fe)
        gp = sum(p for p in pnl if p > 0)
        gl = -sum(p for p in pnl if p < 0)
        return gp / gl if gl else float("inf"), sum(pnl), pnl
    for w in ("discovery", "validation", "holdout"):
        trs = rows[w]
        print("==", w, dict(funnel[w]))
        if not trs:
            continue
        wr = sum(1 for t in trs if t[2]) / len(trs)
        mp = st.mean(t[1] for t in trs)
        print("  n", len(trs), "win rate %.4f mean fill %.4f gap %.4f" % (wr, mp, wr - mp), " median spread of picked leg %.3f" % st.median(t[4] for t in trs))
        for C in (10, 1):
            pf, net, pnl = stats(trs, C, 1)
            print("  C=%d PF %.3f net $%.2f" % (C, pf, net))
        pf12, net12, _ = stats(trs, 10, 1.2)
        print("  x1.2 C=10 PF %.3f net $%.2f" % (pf12, net12))
        nv = [t for t in trs if t[3] > 0]
        if nv:
            print("  no zero-volume fill candle: n", len(nv), "PF %.3f" % stats(nv, 10, 1)[0])
        pf, net, pnl = stats(trs, 10, 1)
        byday = defaultdict(float)
        for t, p in zip(trs, pnl):
            byday[t[0] // 86400] += p
        d = list(byday.values())
        z = st.mean(d) / (st.stdev(d) / math.sqrt(len(d))) if len(d) > 2 and st.stdev(d) > 0 else float("nan")
        print("  day-clustered z %.2f over %d days" % (z, len(d)))


if __name__ == "__main__":
    {"t1": t1, "t2": t2}[sys.argv[1]]()
