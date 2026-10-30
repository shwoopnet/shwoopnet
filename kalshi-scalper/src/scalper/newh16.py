"""NEWH16 (workers/NEWH16_REGISTRATION.md, pushed before this file ran): held coin flip entries. Research only.
    PYTHONPATH=src python -m scalper.newh16 run
"""
from __future__ import annotations

import bisect
import math
import sqlite3
import sys
from datetime import datetime, timezone

from .newh2 import fee, net, pf, dayz, summ, line, load, day
from .paths import DATA_DIR

def ts(y, m, d, h=0):
    return int(datetime(y, m, d, h, tzinfo=timezone.utc).timestamp())

D0, D1, V1, HEND = ts(2026, 8, 6), ts(2026, 9, 21), ts(2026, 10, 18), ts(2026, 11, 1)
P_D1, P_V1 = ts(2026, 9, 14), ts(2026, 10, 13)
FILES = {"KXBTC15M": ("l1b", "book", "fresh"), "KXETH15M": ("l1b", "book", "fresh"),
         "KXGOLD15M": ("l1b", "book", "fresh", "five")}
LO, HI = 0.35, 0.65


def quantile(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, int(q * len(v)))]


def side_ask(row, side):
    if row is None:
        return None
    a = row[1] if side == "yes" else round(1 - row[0], 6)
    return a if 0 < a < 1 else None


def trade(w, side, fill_off):
    r = w["c"].get(fill_off)
    a = side_ask(r, side)
    if a is None or not (LO - 1e-9 <= a <= HI + 1e-9):
        return None
    won = w["result"] == side
    return {"day": day(w["close"]), "close": w["close"], "side": side, "fill": a, "won": won,
            "n10": net(a, won, 10), "n1": net(a, won, 1), "n10x": net(a, won, 10, 1.2), "vol0": r[2] <= 0}


def ret_feature(wins, k, back):
    """ln(strike_k / strike_(k-back windows)) or None (window missing)."""
    w, p = wins.get(k), wins.get(k - 900 * back)
    if not w or not p or not w["strike"] or not p["strike"]:
        return None
    return math.log(w["strike"] / p["strike"])


def t12(series, wins, back, qtile, sign_rule):
    """sign_rule: +1 follow, -1 fade. Returns {window name: trades}, counts."""
    closes = sorted(wins)
    feats = {k: ret_feature(wins, k, back) for k in closes}
    disc = [abs(f) for k, f in feats.items() if f is not None and D0 <= k < D1]
    cut = quantile(disc, qtile)
    out = {"disc": [], "val": [], "hold": []}
    gaps = nosig = nofill = 0
    for k in closes:
        f = feats[k]
        win = "disc" if D0 <= k < D1 else "val" if D1 <= k < V1 else "hold" if V1 <= k < HEND else None
        if win is None:
            continue
        if f is None or -840 not in wins[k]["c"]:
            gaps += 1
            continue
        if abs(f) <= cut:
            nosig += 1
            continue
        side = "yes" if (f > 0) == (sign_rule > 0) else "no"
        t = trade(wins[k], side, -780)
        if t is None:
            nofill += 1
            continue
        out[win].append(t)
    return out, {"cut": cut, "gaps": gaps, "nosig": nosig, "nofill": nofill}


def pmdata(series):
    pre = "btc" if series == "KXBTC15M" else "eth"
    pts = {}
    for f in ("pm1", "pm2"):
        db = sqlite3.connect(DATA_DIR / f"{f}.sqlite")
        for s, t, p in db.execute("select slug,t,p from pt where slug like ?", (pre + "-updown-15m-%",)):
            pts.setdefault(s, []).append((t, p))
    for v in pts.values():
        v.sort()
    return pts, pre


def t3(series, wins):
    pts, pre = pmdata(series)
    out = {"disc": [], "val": [], "hold": []}
    gaps = nosig = nofill = 0
    for k in sorted(wins):
        win = "disc" if D0 <= k < P_D1 else "val" if P_D1 <= k < P_V1 else None
        if win is None:
            continue
        h = pts.get(f"{pre}-updown-15m-{k - 900}")
        w = wins[k]
        dc = w["c"].get(-600)
        if not h or dc is None:
            gaps += 1
            continue
        tt = [x[0] for x in h]
        i = bisect.bisect_right(tt, k - 600) - 1
        if i < 0 or (k - 600) - h[i][0] > 120:
            gaps += 1
            continue
        ppm = h[i][1]
        ay, an = side_ask(dc, "yes"), side_ask(dc, "no")
        if ay is None or an is None or not (0.30 <= ay <= 0.70 and 0.30 <= an <= 0.70):
            nosig += 1
            continue
        if ppm - ay >= 0.06 - 1e-12:
            side = "yes"
        elif (1 - ppm) - an >= 0.06 - 1e-12:
            side = "no"
        else:
            nosig += 1
            continue
        t = trade(w, side, -540)
        if t is None:
            nofill += 1
            continue
        out[win].append(t)
    return out, {"gaps": gaps, "nosig": nosig, "nofill": nofill}


def verdict(res):
    d, v = summ(res["disc"]), summ(res["val"])
    if d["n"] < 100:
        return "NOT_ENOUGH_DATA (discovery n %d)" % d["n"]
    if not (d["pf10"] >= 1.5 and d["netx"] > 0):
        return "FALSIFIED (discovery)"
    if v["n"] < 50:
        return "NOT_ENOUGH_DATA (validation n %d)" % v["n"]
    if not (v["pf10"] >= 1.5 and v["netx"] > 0):
        return "FALSIFIED (validation)"
    return "BOTH_PASS: holdout may be read"


def report(name, res, info):
    print(f"\n== {name}  {info}")
    for k in ("disc", "val"):
        s = summ(res[k])
        print(line(k, s) if s["n"] else f"{k:<22} n 0")
    print("  ->", verdict(res))


def run():
    cache = {}
    def W(s, a, b):
        return load(s, FILES[s], a, b)
    for s in ("KXBTC15M", "KXGOLD15M"):
        wins = W(s, D0 - 900 * 20, HEND)
        # features need the windows 16 back: loaded from 20 windows earlier; trades still limited to the three date windows
        for name, back, q, sr in (("T1 TREND4H follow", 16, 0.80, 1), ("T1 TREND4H fade", 16, 0.80, -1),
                                  ("T2 BIGMOVE fade", 1, 0.95, 1 * -1)):
            if name.startswith("T2") and False:
                pass
            if name.startswith("T2"):
                # T2: after a rise buy NO (fade the previous window): sign_rule -1 on m1
                res, info = t12(s, wins, back, q, -1)
                report(f"{name} {s}", res, info)
                res2, info2 = t12(s, wins, back, q, 1)
                print("  information (follow):", end=" ")
                a, b = summ(res2["disc"]), summ(res2["val"])
                print(f"disc n {a.get('n')} PF10 {a.get('pf10', float('nan')):.2f} | val n {b.get('n')} PF10 {b.get('pf10', float('nan')):.2f}")
            else:
                res, info = t12(s, wins, back, q, sr)
                report(f"{name} {s}", res, info)
    for s in ("KXBTC15M", "KXETH15M"):
        wins = W(s, D0, P_V1)
        res, info = t3(s, wins)
        report(f"T3 PMGAP {s}", res, info)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run()
    else:
        print(__doc__)
