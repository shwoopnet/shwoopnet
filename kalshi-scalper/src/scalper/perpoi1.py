"""PERPOI1: perp open-interest surge as the trigger for a cheap-tail trade on the hourly Bitcoin ladder (research only).

Rule and bars: workers/PERPOI1_REGISTRATION.md. Nothing here may change after the first outcome.
    python -m scalper.perpoi1 run     development window only; the last third is never computed
"""
from __future__ import annotations

import math
import os
import sqlite3
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data")
LAD = os.path.join(DATA, "conf2_lad.sqlite")
LEAD = 1500
OI_WIN = 10
HIST = 7 * 1440
MIN_HIST = 5 * 1440
PCT = 95
LO, HI = 0.03, 0.30
MIN_DEV = 100
Z_BAR = 5.27


def fee(p, c):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100.0


def surge_at(t0, c, oi, t):
    """c, oi: per-minute lists (minute i starts at t0 + 60 i, ends t0 + 60 (i+1)). Returns (surge, direction) or None if not usable."""
    i = (t - 60 - t0) // 60
    if i < 0 or i >= len(c) or i - OI_WIN < 0:
        return None
    if i - MIN_HIST < OI_WIN:
        return None
    if oi[i - OI_WIN] <= 0:
        return None
    lo = max(OI_WIN, i - HIST + 1)
    arr = np.asarray(oi[lo - OI_WIN:i + 1], dtype=float)
    d = arr[OI_WIN:] - arr[:-OI_WIN]
    thr = float(np.percentile(d, PCT))
    dt = oi[i] - oi[i - OI_WIN]
    m = c[i] - c[i - OI_WIN]
    dirn = 1 if m > 0 else (-1 if m < 0 else 0)
    return (dt > thr), dirn, c[i]


def pick(cands, direction, spot, mode):
    """cands: list of (strike, yes_bid, yes_ask). mode 'A' uses direction; 'B' picks the lower priced tail of both sides.
    Returns (strike, side, price) or None."""
    ys = [(s, a) for s, b, a in cands if s > spot and LO <= a <= HI]
    ns = [(s, 1 - b) for s, b, a in cands if s < spot and LO <= 1 - b <= HI]
    ybest = max(ys, key=lambda x: x[1]) if ys else None
    nbest = max(ns, key=lambda x: x[1]) if ns else None
    if mode == "A":
        if direction == 1 and ybest:
            return (ybest[0], "yes", ybest[1])
        if direction == -1 and nbest:
            return (nbest[0], "no", nbest[1])
        return None
    opts = []
    if ybest:
        opts.append((ybest[1], 0, ybest[0], "yes"))
    if nbest:
        opts.append((nbest[1], 1, nbest[0], "no"))
    if not opts:
        return None
    p, _, s, side = min(opts)
    return (s, side, p)


def pnl(side, price, strike, result, c):
    won = (result == "yes") == (side == "yes")
    return (c if won else 0.0) - c * price - fee(price, c), won


def load_events():
    db = sqlite3.connect(LAD)
    rows = db.execute("select ticker, close_ts, result, strike from market where series='KXBTCD'").fetchall()
    ev = {}
    for tk, ct, res, k in rows:
        if res in ("yes", "no"):
            ev.setdefault(ct, []).append((tk, res, k))
    return db, ev


def quotes(db, ev_markets, t):
    out = []
    for tk, res, k in ev_markets:
        r = db.execute("select bid_c, ask_c from candle where ticker=? and end_ts=?", (tk, t)).fetchone()
        if not r or r[0] is None or r[1] is None:
            continue
        b, a = r
        if not (a > 0 and a < 1 and b > 0):
            continue
        out.append((k, b, a, res))
    return out


def stats(tr, label):
    n = len(tr)
    if n == 0:
        return "%s n=0" % label
    w = sum(1 for x in tr if x["won"])
    g = sum(x["pnl10"] for x in tr if x["pnl10"] > 0)
    l = -sum(x["pnl10"] for x in tr if x["pnl10"] < 0)
    pf = g / l if l > 0 else float("inf")
    pf12 = None
    g2 = sum(x["pnl10x"] for x in tr if x["pnl10x"] > 0)
    l2 = -sum(x["pnl10x"] for x in tr if x["pnl10x"] < 0)
    pf12 = g2 / l2 if l2 > 0 else float("inf")
    mp = float(np.mean([x["price"] for x in tr]))
    m = float(np.mean([x["pnl10"] for x in tr])) / 10
    return "%s n=%d win=%.1f%% meanprice=%.3f mean_net_per_contract=%+.4f PF=%.2f PFx1.2=%.2f" % (label, n, 100.0 * w / n, mp, m, pf, pf12)


def build(t0, c, oi, db, ev, closes):
    res = {"A": [], "B": [], "ctrl": [], "counts": {"closes": 0, "usable": 0, "surge": 0, "surge_dir": 0, "A_noquote": 0}}
    for ct in closes:
        t = ct - LEAD
        res["counts"]["closes"] += 1
        s = surge_at(t0, c, oi, t)
        if s is None:
            continue
        res["counts"]["usable"] += 1
        surge, dirn, spot = s
        q = quotes(db, ev[ct], t)
        cands = [(k, b, a) for k, b, a, _ in q]
        resmap = {k: r for k, b, a, r in q}
        def mk(mode, dd):
            p = pick(cands, dd, spot, mode)
            if not p:
                return None
            k, side, price = p
            pn, won = pnl(side, price, k, resmap[k], 10)
            pn12 = pn - 0.2 * fee(price, 10)
            return {"close": ct, "side": side, "price": price, "won": won, "pnl10": pn, "pnl10x": pn12,
                    "pnl1": pnl(side, price, k, resmap[k], 1)[0]}
        if surge:
            res["counts"]["surge"] += 1
            if dirn != 0:
                res["counts"]["surge_dir"] += 1
                a = mk("A", dirn)
                if a:
                    res["A"].append(a)
                else:
                    res["counts"]["A_noquote"] += 1
            b = mk("B", 0)
            if b:
                res["B"].append(b)
        elif dirn != 0:
            a = mk("A", dirn)
            if a:
                res["ctrl"].append(a)
    return res


def boot_diff(a, b, rng, n=2000):
    ga, gb = {}, {}
    for x in a:
        ga.setdefault(x["close"], []).append(x["pnl10"])
    for x in b:
        gb.setdefault(x["close"], []).append(x["pnl10"])
    ka, kb = list(ga), list(gb)
    if not ka or not kb:
        return None
    va = np.array([np.mean(ga[k]) for k in ka]); vb = np.array([np.mean(gb[k]) for k in kb])
    d = []
    for _ in range(n):
        d.append(rng.choice(va, len(va)).mean() - rng.choice(vb, len(vb)).mean())
    return float(va.mean() - vb.mean()) / 10, float(np.percentile(d, 5)) / 10, float(np.percentile(d, 95)) / 10


def run(out):
    sys.path.insert(0, os.path.join(HERE, ".."))
    from scalper.snapback1 import load
    t0, o, h, l, c, oi = load("KXBTCPERP")
    db, ev = load_events()
    closes = sorted(ev)
    # usable closes: perp history present
    T0, T1 = closes[0], closes[-1]
    cut1 = T0 + (T1 - T0) // 3
    cut2 = T0 + 2 * (T1 - T0) // 3
    dev = [x for x in closes if x < cut2]
    lines = ["PERPOI1 development read (closes %d to %d; cut1 %d cut2 %d; holdout closes after cut2 NOT computed)" % (T0, T1, cut1, cut2)]
    rng = np.random.default_rng(12345)
    halves = {"all": dev, "h1": [x for x in dev if x < cut1], "h2": [x for x in dev if x >= cut1]}
    R = {k: build(t0, c, oi, db, ev, v) for k, v in halves.items()}
    for k in ("all", "h1", "h2"):
        r = R[k]
        lines.append("[%s] counts %s" % (k, r["counts"]))
        for nm in ("A", "B", "ctrl"):
            lines.append("[%s] %s" % (k, stats(r[nm], nm)))
            if r[nm]:
                lines.append("   C=1 mean net per contract %+.4f" % float(np.mean([x["pnl1"] for x in r[nm]])))
        bd = boot_diff(r["A"], r["ctrl"], rng)
        lines.append("[%s] trigger-minus-control mean net per contract (C=10) %s" % (k, ("%+.4f (boot 5%% %+.4f, 95%% %+.4f)" % bd) if bd else "n/a"))
    nA = len(R["all"]["A"])
    span_days = (cut2 - T0) / 86400.0
    rate = nA / span_days * 30.4 if span_days > 0 else 0
    lines.append("development A trades %d over %.1f days (%.1f a month); months to 150 total: %s" % (nA, span_days, rate, ("%.1f" % ((150 - nA) / rate)) if rate else "n/a"))
    lines.append("VERDICT: " + ("NOT_ENOUGH_DATA (A dev trades %d < %d)" % (nA, MIN_DEV) if nA < MIN_DEV else "n>=%d: apply registered FALSIFIED rules by hand from the lines above" % MIN_DEV))
    txt = "\n".join(lines)
    open(out, "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    if sys.argv[1:] == ["run"]:
        out = os.path.join(HERE, "..", "..", "workers", "PERPOI1_output.txt")
        if os.path.exists(out):
            raise SystemExit("output exists; delete on purpose for a second run")
        run(out)
