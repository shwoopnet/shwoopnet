"""SKEW1: is the crash tail (buy NO on a strike below spot) priced differently from the rally tail (buy YES above spot)? (research only)

Registration: workers/SKEW1_REGISTRATION.md (pushed before any result was read). Result: workers/SKEW1_RESULT.md.

    PYTHONPATH=src python -m scalper.skew1 counts   (funnel counts from prices only; reads no result)
    PYTHONPATH=src python -m scalper.skew1 dv       (development, two halves, scored once; the frozen W3 is never loaded)
    PYTHONPATH=src python -m scalper.skew1 eth      (Ethereum KXETHD, information only)

Rule: hourly KXBTCD event. Look = candle ending 25 minutes before the close. Spot proxy S = the strike where the YES mid crosses 0.5
(linear interpolation between adjacent two-sided strikes, spread <= 10c). DOWN side: of strikes K < S whose look NO ask (1 - YES bid)
is in [0.03, 0.30], take the nearest to S; buy NO. UP side: of strikes K > S whose look YES ask is in [0.03, 0.30], take the nearest;
buy YES. Fill = the NEXT candle (ending 24 minutes before the close) at its ask, which must be <= 0.30 (hard limit) and two-sided with
spread <= 6c. Held to settlement. C = 10, fee 7% x C x p x (1 - p) rounded up per order.
"""
from __future__ import annotations

import calendar
import math
import sqlite3
import statistics
import sys
from collections import defaultdict

from .paths import DATA_DIR
from .newh9 import fee, pf, day

N_THIS = 4
A24 = calendar.timegm((2026, 8, 24, 0, 0, 0))
W3_START = calendar.timegm((2026, 10, 27, 0, 0, 0))     # closes at or after this are frozen and never loaded with a result
END = calendar.timegm((2026, 11, 4, 0, 0, 0))
LOOK_LEAD, FILL_LEAD = 1500, 1440
LO, HI = 0.03, 0.30
SPOT_MAX_SPREAD, TRADE_MAX_SPREAD = 0.10, 0.06
SIG_WIN, SIG_MIN = 72, 36                 # trailing hourly log changes of the implied spot used for sigma
BINS = ((0.0, 0.8), (0.8, 1.4), (1.4, 99.0))
EPS = 1e-9
BAR_PF, MIN_SIDE_N = 1.5, 150


def two_sided(q, maxsp):
    b, a = q[0], q[1]
    return 0 < b < a < 1 and a - b <= maxsp + EPS


def load(files, series="KXBTCD", frozen=False):
    """{close: {"res": {K: result}, "q": {end_ts: {K: (bid, ask, vol)}}}}; the first file holding a close wins it.
    Closes at or after W3_START are skipped unless frozen=True (so no result of them is ever read in dv)."""
    out = {}
    for fname in files:
        db = sqlite3.connect(DATA_DIR / fname)
        mk = {}
        for tk, close, res, k in db.execute("select ticker, close_ts, result, strike from market where series=? and close_ts>=? and close_ts<?",
                                            (series, A24, END)):
            if res in ("yes", "no") and k is not None and close not in out and (frozen or close < W3_START):
                mk[tk] = (close, float(k), res)
        ev = defaultdict(lambda: {"res": {}, "q": defaultdict(dict)})
        for tk, (close, k, res) in mk.items():
            ev[close]["res"][k] = res
        lead_lo = 3 * 3600 + 3600
        for tk, e, b, a, v in db.execute("select ticker, end_ts, bid_c, ask_c, volume from candle where series=?", (series,)):
            m = mk.get(tk)
            if m is None or b is None or a is None or m[0] - e > lead_lo:
                continue
            ev[m[0]]["q"][e][m[1]] = (b, a, v or 0.0)
        out.update(ev)
    return out


def implied_spot(u):
    """Strike where the YES mid crosses 0.5, interpolated; None if the two-sided strikes do not bracket it."""
    pts = sorted((k, (q[0] + q[1]) / 2) for k, q in u.items() if two_sided(q, SPOT_MAX_SPREAD))
    for (k1, m1), (k2, m2) in zip(pts, pts[1:]):
        if m1 >= 0.5 > m2:
            return k1 + (k2 - k1) * (m1 - 0.5) / (m1 - m2)
    return None


def spots(ev):
    """{close: S at the 25 minute look}"""
    out = {}
    for close, e in ev.items():
        u = e["q"].get(close - LOOK_LEAD)
        if u:
            s = implied_spot(u)
            if s:
                out[close] = s
    return out


def sigma_hour(close, S):
    """Std of the hourly log changes of the implied spot over the previous SIG_WIN hours (only changes that end before this event's
    own look: the change ending at close - 3600 uses spots of close - 3600 and close - 7200)."""
    rs = []
    for j in range(1, SIG_WIN + 1):
        a, b = close - 3600 * j, close - 3600 * (j + 1)
        if a in S and b in S:
            rs.append(math.log(S[a] / S[b]))
    return statistics.pstdev(rs) if len(rs) >= SIG_MIN else None


def dbin(d):
    for i, (lo, hi) in enumerate(BINS):
        if lo <= d < hi:
            return i
    return len(BINS) - 1


def build(ev, score=True):
    S = spots(ev)
    funnel = defaultdict(int)
    trades = []
    for close in sorted(ev):
        e = ev[close]
        funnel["events"] += 1
        if close not in S:
            funnel["no_spot"] += 1
            continue
        sg = sigma_hour(close, S)
        if sg is None or sg <= 0:
            funnel["no_sigma"] += 1
            continue
        s25 = sg * math.sqrt(25 / 60)
        look, fill = e["q"][close - LOOK_LEAD], e["q"].get(close - FILL_LEAD)
        spot = S[close]
        for side in ("DN", "UP"):
            cand = []
            for k, q in look.items():
                if not two_sided(q, TRADE_MAX_SPREAD):
                    continue
                if side == "DN" and k < spot:
                    ask = 1 - q[0]
                elif side == "UP" and k > spot:
                    ask = q[1]
                else:
                    continue
                if LO - EPS <= ask <= HI + EPS:
                    cand.append((abs(k - spot), k))
            if not cand:
                funnel[side + "_no_candidate"] += 1
                continue
            k = min(cand)[1]
            if not fill or k not in fill or not two_sided(fill[k], TRADE_MAX_SPREAD):
                funnel[side + "_no_fill_quote"] += 1
                continue
            b, a, v = fill[k]
            paid = round(1 - b, 6) if side == "DN" else a
            if paid > HI + EPS:
                funnel[side + "_price"] += 1
                continue
            d = abs(math.log(k / spot)) / s25
            funnel[side + "_trades"] += 1
            tr = {"close": close, "side": side, "k": k, "paid": paid, "d": d, "bin": dbin(d),
                  "zv": (look[k][2] == 0 or v == 0), "res": e["res"].get(k) if score else None}
            trades.append(tr)
    return trades, funnel


def payoff(t):
    return 1 if t["res"] == ("no" if t["side"] == "DN" else "yes") else 0


def net(t, c=10, m=1.0):
    return c * (payoff(t) - t["paid"]) - fee(t["paid"], c, m)


def halves(closes_with_spot):
    cs = sorted(closes_with_spot)
    return cs[len(cs) // 2]          # first close of half 2


def cz(tr):
    """Cluster-robust z of mean net per contract vs zero, clusters = hourly events."""
    s, n = defaultdict(float), defaultdict(int)
    for t in tr:
        s[t["close"]] += net(t) / 10
        n[t["close"]] += 1
    N = sum(n.values())
    if N == 0 or len(s) < 3:
        return float("nan")
    m = sum(s.values()) / N
    ss = sum((s[k] - m * n[k]) ** 2 for k in s)
    return (m * N) / math.sqrt(ss) if ss > 0 else float("nan")


def summ(tr):
    if not tr:
        return {"n": 0}
    n10 = [net(t) for t in tr]
    dd = defaultdict(float)
    for t in tr:
        dd[day(t["close"])] += net(t)
    return {"n": len(tr), "events": len({t["close"] for t in tr}), "win": sum(payoff(t) for t in tr) / len(tr),
            "paid": statistics.mean(t["paid"] for t in tr), "mean": sum(n10) / (10 * len(tr)) * 100,
            "meanx": sum(net(t, 10, 1.2) for t in tr) / (10 * len(tr)) * 100, "pf": pf(n10),
            "pfx": pf([net(t, 10, 1.2) for t in tr]), "net": sum(n10), "z": cz(tr), "worst_day": min(dd.values()),
            "nzv": sum(t["zv"] for t in tr), "pf_nz": pf([net(t) for t in tr if not t["zv"]])}


def fmt(s):
    if s["n"] == 0:
        return "n 0"
    return (f"n {s['n']} on {s['events']} events, win {s['win']:.2%} vs paid {s['paid']:.4f}, mean net c/contract {s['mean']:+.2f} "
            f"(x1.2 {s['meanx']:+.2f}), PF {s['pf']:.2f} (x1.2 {s['pfx']:.2f}), net ${s['net']:+.2f}, z event {s['z']:.2f}, "
            f"worst day ${s['worst_day']:.2f}, zero-vol {s['nzv']} (PF without {s['pf_nz']:.2f})")


def diff(trD, trU, minbin=20):
    """(raw mean difference DN - UP in cents, bin-adjusted difference with equal weight over bins that have >= minbin each side,
    cluster z of the raw difference via event-level sums)."""
    def m(tr):
        return sum(net(t) for t in tr) / (10 * len(tr)) * 100 if tr else float("nan")
    raw = m(trD) - m(trU)
    ds = []
    for b in range(len(BINS)):
        a = [t for t in trD if t["bin"] == b]
        c = [t for t in trU if t["bin"] == b]
        if len(a) >= minbin and len(c) >= minbin:
            ds.append(m(a) - m(c))
    adj = sum(ds) / len(ds) if ds else float("nan")
    # paired z: per event, mean net of DN trade minus mean net of UP trade, events where both trade
    dn = {t["close"]: net(t) / 10 for t in trD}
    up = {t["close"]: net(t) / 10 for t in trU}
    x = [dn[c] - up[c] for c in dn if c in up]
    z = statistics.mean(x) / (statistics.stdev(x) / math.sqrt(len(x))) if len(x) > 2 and statistics.stdev(x) > 0 else float("nan")
    return raw, adj, z, len(ds), len(x)


def verdict(trD, trU, cut):
    """Registered rule. Halves: closes < cut, closes >= cut."""
    if len(trD) < MIN_SIDE_N or len(trU) < MIN_SIDE_N:
        return "NOT_ENOUGH_DATA"
    h = [(lambda f: ([t for t in trD if f(t)], [t for t in trU if f(t)]))(f) for f in (lambda t: t["close"] < cut, lambda t: t["close"] >= cut)]
    side_ok = {}
    for nm, i in (("DN", 0), ("UP", 1)):
        side_ok[nm] = all(summ(hh[i])["n"] > 0 and summ(hh[i])["pf"] >= BAR_PF for hh in h)
    diff_ok = all(diff(hh[0], hh[1])[0] > 0 and diff(hh[0], hh[1])[1] > 0 for hh in h)
    if (side_ok["DN"] or side_ok["UP"]) and diff_ok:
        return "PASS_DEV"
    return "FALSIFIED"


def report(trades, funnel, ev, label):
    S = spots(ev)
    cut = halves([c for c in S if sigma_hour(c, S) is not None])
    D = [t for t in trades if t["side"] == "DN"]
    U = [t for t in trades if t["side"] == "UP"]
    print(f"{label}: funnel {dict(funnel)}; half cut close >= {cut}")
    for nm, tr in (("DOWN (buy NO below spot)", D), ("UP (buy YES above spot)", U)):
        print(f"{nm} ALL: {fmt(summ(tr))}")
        for hn, f in (("H1", lambda t: t['close'] < cut), ("H2", lambda t: t['close'] >= cut)):
            print(f"  {hn}: {fmt(summ([t for t in tr if f(t)]))}")
        for b, (lo, hi) in enumerate(BINS):
            print(f"  dist bin {lo}-{hi}: {fmt(summ([t for t in tr if t['bin'] == b]))}")
        for lo, hi in ((0.03, 0.10), (0.10, 0.20), (0.20, 0.3001)):
            print(f"  paid {lo:.2f}-{hi:.2f}: {fmt(summ([t for t in tr if lo - EPS <= t['paid'] < hi]))}")
    for nm, f in (("ALL", lambda t: True), ("H1", lambda t: t['close'] < cut), ("H2", lambda t: t['close'] >= cut)):
        r, a, z, nb, npair = diff([t for t in D if f(t)], [t for t in U if f(t)])
        print(f"DIFF {nm}: DOWN minus UP raw {r:+.2f}c, bin-adjusted {a:+.2f}c ({nb} bins), paired z {z:.2f} on {npair} events")
    return cut, D, U


def main(argv):
    mode = argv[1] if len(argv) > 1 else "counts"
    if mode == "eth":
        ev = load(["ladders.sqlite"], "KXETHD")
        tr, fn = build(ev)
        report(tr, fn, ev, "INFO ETH")
        return
    ev = load(["conf2_lad.sqlite", "lad2.sqlite"])
    if mode == "counts":
        tr, fn = build(ev, score=False)
        print("closes loaded", len(ev), "funnel", dict(fn))
        return
    tr, fn = build(ev)
    cut, D, U = report(tr, fn, ev, "SKEW1 DEV")
    print("VERDICT", verdict(D, U, cut))


if __name__ == "__main__":
    main(sys.argv)
