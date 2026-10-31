"""LADLONG1: sell the overpriced far wing of the hourly Bitcoin ladder by buying the other side at its ask, held (research only).

Registration: workers/LADLONG1_REGISTRATION.md (pushed before any scoring). Result: workers/LADLONG1_RESULT.md.

    PYTHONPATH=src python -m scalper.ladlong1 counts           (funnel counts by stage from prices only; reads no result)
    PYTHONPATH=src python -m scalper.ladlong1 dv               (discovery and validation, scored once)
    PYTHONPATH=src python -m scalper.ladlong1 holdout BAND...  (frozen holdout, read once, only for a band that passed dv)

Rule: universe = strikes of one KXBTCD hourly event whose YES mid, on the latest present candle ending 52 to 55 minutes before the
close, lies in a registered band and whose spread is at most 4c (0 < bid < ask < 1). Look = the candle ending 45 minutes before the
close (strike must still be quoted two-sided, spread <= 6c). Fill = the NEXT candle (ending 44 minutes before the close): UP bands buy
NO at 1 - YES bid, DN bands buy YES at the YES ask, one contract-leg per strike, held to settlement. Fee 7% x C x p x (1-p) rounded
up to the cent per order.
"""
from __future__ import annotations

import calendar
import math
import statistics
import sys
from collections import defaultdict

import numpy as np

from .newh9 import load_ladder, stage, day, fee, pf, zbar

N_RUNNING_BEFORE = 728_673
N_THIS = 4
A24 = calendar.timegm((2026, 8, 24, 0, 0, 0))

UNI_LEADS = (3120, 3180, 3240, 3300)    # candles ending 52, 53, 54, 55 minutes before the close; the latest present is used
LOOK_LEAD = 2700                        # the entry look: candle ending 45 minutes before the close
FILL_LEAD = 2640                        # the next candle: the fill
UNI_MAX_SPREAD = 0.04
LOOK_MAX_SPREAD = 0.06
FILL_MAX_SPREAD = 0.06
MAX_PAID = 0.99
EPS = 1e-9

# band -> (side bought, lo, hi, lo_inclusive, hi_inclusive) on the YES mid at the universe candle
BANDS = {
    "UPfar": ("NO", 0.02, 0.06, True, False),
    "UPnear": ("NO", 0.06, 0.12, True, True),
    "DNnear": ("YES", 0.88, 0.94, True, True),
    "DNfar": ("YES", 0.94, 0.98, False, True),
}
BOOT_N, BOOT_EVENTS, BOOT_SEED = 5000, 720, 20261031     # 720 hourly closes = 30 days
BAR = {"mean_c": 0.5, "z": 3.0, "pf": 1.3, "ev_disc": 300, "ev_val": 150, "worst_day": 125.0}


def in_band(m, b):
    side, lo, hi, li, hi_i = BANDS[b]
    m = round(m, 6)
    ok_lo = m >= lo - EPS if li else m > lo + EPS
    ok_hi = m <= hi + EPS if hi_i else m < hi - EPS
    return ok_lo and ok_hi


def two_sided(q, maxsp):
    b, a = q[0], q[1]
    return 0 < b < a < 1 and a - b <= maxsp + EPS


def universe(e):
    """{strike: band} from the latest present candle 52..55 minutes before the close (prices only)."""
    close = e["close"]
    for L in UNI_LEADS:
        u = e["q"].get(close - L)
        if u:
            out = {}
            for k, q in u.items():
                if not two_sided(q, UNI_MAX_SPREAD):
                    continue
                m = (q[0] + q[1]) / 2
                for bd in BANDS:
                    if in_band(m, bd):
                        out[k] = bd
            return out
    return None


def build(ev):
    """Entry candidates with the funnel; reads the settled result only where payoff is set (score=False leaves it out)."""
    funnel = defaultdict(lambda: defaultdict(int))
    trades = []
    for close, e in sorted(ev.items()):
        if close < A24:
            continue
        e = dict(e)
        e["close"] = close
        st = stage(close)
        funnel[st]["events"] += 1
        uni = universe(e)
        if uni is None:
            funnel[st]["no_universe_candle"] += 1
            continue
        look, fill = e["q"].get(close - LOOK_LEAD), e["q"].get(close - FILL_LEAD)
        for k, bd in sorted(uni.items()):
            funnel[(st, bd)]["universe"] += 1
            if not look or k not in look or not two_sided(look[k], LOOK_MAX_SPREAD):
                funnel[(st, bd)]["no_look"] += 1
                continue
            if not fill or k not in fill or not two_sided(fill[k], FILL_MAX_SPREAD):
                funnel[(st, bd)]["no_fill"] += 1
                continue
            b, a, v = fill[k]
            paid = round(1 - b, 6) if BANDS[bd][0] == "NO" else a
            if paid > MAX_PAID + EPS:
                funnel[(st, bd)]["price"] += 1
                continue
            funnel[(st, bd)]["trades"] += 1
            trades.append({"close": close, "k": k, "band": bd, "paid": paid, "stage": st,
                           "zv": (look[k][2] == 0 or v == 0), "res": e["res"].get(k)})
    return trades, funnel


def payoff(t):
    want = "no" if BANDS[t["band"]][0] == "NO" else "yes"
    return 1 if t["res"] == want else 0


def net(t, c=10, m=1.0):
    return c * (payoff(t) - t["paid"]) - fee(t["paid"], c, m)


def evsums(tr, c=10, m=1.0):
    d = defaultdict(float)
    n = defaultdict(int)
    for t in tr:
        d[t["close"]] += net(t, c, m)
        n[t["close"]] += 1
    return d, n


def cz(tr, key):
    """Cluster-robust z of mean net per contract against zero; clusters = hourly events (key=close) or US/UTC days."""
    s = defaultdict(float)
    n = defaultdict(int)
    for t in tr:
        kk = t["close"] if key == "event" else day(t["close"])
        s[kk] += net(t) / 10
        n[kk] += 1
    N = sum(n.values())
    if N == 0 or len(s) < 3:
        return float("nan")
    m = sum(s.values()) / N
    ss = sum((s[k] - m * n[k]) ** 2 for k in s)
    return (m * N) / math.sqrt(ss) if ss > 0 else float("nan")


def boot_p5(tr, all_close, seed=BOOT_SEED):
    """5th percentile of the C = 10 net over 720 hourly events drawn with replacement from ALL the window's events
    (events with no trade count as 0), strikes of one event moving together."""
    d, _ = evsums(tr)
    vals = np.array([d.get(c, 0.0) for c in all_close])
    if len(vals) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(vals), size=(BOOT_N, BOOT_EVENTS))
    s = vals[idx].sum(axis=1)
    return float(np.percentile(s, 5)), float(s.mean())


def summ(tr, all_close):
    if not tr:
        return {"n": 0, "events": 0}
    n10 = [net(t) for t in tr]
    d, _ = evsums(tr)
    dd = defaultdict(float)
    for t in tr:
        dd[day(t["close"])] += net(t)
    p5, bmean = boot_p5(tr, all_close)
    nz = [t for t in tr if not t["zv"]]
    return {
        "n": len(tr), "events": len({t["close"] for t in tr}), "days": len(dd),
        "win": sum(payoff(t) for t in tr) / len(tr), "paid": statistics.mean(t["paid"] for t in tr),
        "mean10": sum(n10) / (10 * len(tr)) * 100, "mean1": sum(net(t, 1) for t in tr) / len(tr) * 100,
        "meanx": sum(net(t, 10, 1.2) for t in tr) / (10 * len(tr)) * 100,
        "pf10": pf(n10), "pf1": pf([net(t, 1) for t in tr]), "pfx": pf([net(t, 10, 1.2) for t in tr]),
        "net10": sum(n10), "ze": cz(tr, "event"), "zd": cz(tr, "day"),
        "worst_event": min(d.values()), "worst_day": min(dd.values()), "worst_day_date": min(dd, key=dd.get),
        "p5": p5, "bmean": bmean, "losses": sum(1 for t in tr if payoff(t) == 0),
        "pf10_nz": pf([net(t) for t in nz]), "n_zv": len(tr) - len(nz), "mean_nz": (sum(net(t) for t in nz) / (10 * len(nz)) * 100) if nz else float("nan"),
    }


def fmt(s):
    if s["n"] == 0:
        return "n 0"
    return (f"trades {s['n']} on {s['events']} events ({s['days']} d), win {s['win']:.2%} vs paid {s['paid']:.4f}, losses {s['losses']}; "
            f"mean net c/contract C10 {s['mean10']:+.2f} C1 {s['mean1']:+.2f} x1.2 {s['meanx']:+.2f}; PF10 {s['pf10']:.2f} PF1 {s['pf1']:.2f} "
            f"PFx1.2 {s['pfx']:.2f}; net10 ${s['net10']:+.2f}; z event {s['ze']:.2f} day {s['zd']:.2f}; worst event ${s['worst_event']:.2f}, "
            f"worst day ${s['worst_day']:.2f} ({s['worst_day_date']}); boot 30d p5 ${s['p5']:+.2f} mean ${s['bmean']:+.2f}; "
            f"zero-vol {s['n_zv']} (PF10 without {s['pf10_nz']:.2f}, mean without {s['mean_nz']:+.2f}c)")


def verdict(sd, sv):
    """Registered rule (see workers/LADLONG1_REGISTRATION.md)."""
    if sd["events"] < BAR["ev_disc"] or sv["events"] < BAR["ev_val"]:
        return "NOT_RUNNABLE"
    for s in (sd, sv):
        if s["mean10"] < BAR["mean_c"] or s["meanx"] <= 0:
            return "FALSIFIED"
    for s in (sd, sv):
        if s["ze"] < BAR["z"] or s["pf10"] < BAR["pf"] or s["worst_day"] <= -BAR["worst_day"] or s["p5"] < 0:
            return "NOT_ENOUGH_DATA"
    return "NOT_YET_FALSIFIED"


def closes_by_stage(ev):
    out = defaultdict(list)
    for c in ev:
        if c >= A24:
            out[stage(c)].append(c)
    return out


def main(argv):
    mode = argv[1] if len(argv) > 1 else "counts"
    ev = load_ladder("conf2_lad.sqlite", "lad2.sqlite")
    trades, funnel = build(ev)
    cl = closes_by_stage(ev)
    if mode == "counts":
        for st in ("disc", "val", "hold"):
            print(st, "events", len(cl[st]), dict(funnel[st]))
            for bd in BANDS:
                tr = [t for t in trades if t["stage"] == st and t["band"] == bd]
                print("  ", bd, dict(funnel[(st, bd)]), "events with a trade", len({t["close"] for t in tr}))
        return
    names = list(BANDS) if mode == "dv" else argv[2:]
    stages = ("disc", "val") if mode == "dv" else ("hold",)
    z = zbar(N_RUNNING_BEFORE + N_THIS)
    print(f"N before {N_RUNNING_BEFORE}, this round {N_THIS}, deflated z bar {z:.3f}")
    res = {}
    for bd in names:
        res[bd] = {}
        for st in stages:
            tr = [t for t in trades if t["stage"] == st and t["band"] == bd]
            res[bd][st] = summ(tr, cl[st])
            print(f"{bd} {st}: {fmt(res[bd][st])}")
            print(f"   funnel {dict(funnel[(st, bd)])}")
        if mode == "dv":
            v = verdict(res[bd]["disc"], res[bd]["val"])
            both = [t for t in trades if t["stage"] in stages and t["band"] == bd]
            sp = summ(both, cl["disc"] + cl["val"])
            print(f"{bd} pooled disc+val: {fmt(sp)}")
            print(f"{bd} VERDICT {v}; deflated z bar {z:.2f} {'met' if sp['ze'] >= z else 'NOT met'} on pooled event z {sp['ze']:.2f}")
    if mode == "dv":
        for lab, bds in (("UP both", ("UPfar", "UPnear")), ("DN both", ("DNfar", "DNnear"))):
            for st in ("disc", "val"):
                tr = [t for t in trades if t["stage"] == st and t["band"] in bds]
                print(f"INFO {lab} {st}: {fmt(summ(tr, cl[st]))}")


if __name__ == "__main__":
    main(sys.argv)
