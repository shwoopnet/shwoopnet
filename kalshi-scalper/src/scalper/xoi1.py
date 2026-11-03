"""XOI1 (workers/XOI1_REGISTRATION.md): Bitcoin's open interest jump (the OIREL relative definition) as the TRIGGER, the cheaper side of
OTHER 15 minute crypto series (HYPE, NEAR, ZEC, BNB, XRP) as the TRADE, held to settlement. Research only; nothing here places an order,
reads a key or decides anything live.
    PYTHONPATH=src python -m scalper.xoi1 counts   (outcome-free: eligible windows, trigger counts, thirds; reads NO result)
    PYTHONPATH=src python -m scalper.xoi1 score    (once: W1, W2 and, only if both pass, W3; refuses a second run)
Fill and fee follow oirel / gen6: cheap side = YES first then NO whose ask at the candle ending 180 s before the close is 0.05 to 0.50,
fill at that side's ask on the candle ending 120 s before the close, fee 7% x C x p x (1-p) rounded up per order (gen6.fee), C = 10.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone

from . import gen6, oirel
from .calibration import cluster_mean_z
from .oicorex1 import load_series, BTC_THRESH
from .paths import DATA_DIR

BTC = "KXBTC15M"
ALTS = ["KXHYPE15M", "KXNEAR15M", "KXZEC15M", "KXBNB15M", "KXXRP15M"]
LOOK, BACK, FILL = 180, 360, 120
LO, HI = 0.05, 0.50
RTHR = oirel.RTHR
VOL_MIN, VOL_SPAN = 10.0, 5            # eligibility: >= 10 contracts traded in the 5 candles ending at the look
FLOOR_N = 150
Z_BAR = 5.27
OUT = DATA_DIR / "xoi1_score.json"
LO_TS = int(datetime(2026, 8, 6, tzinfo=timezone.utc).timestamp())
HI_TS = 2 ** 40


def side_ask(q, side):
    return q[1] if side == "yes" else round(1 - q[0], 6)


def day_of(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def btc_trigger(cs, ct, rthr=RTHR):
    """True / False if Bitcoin's relative open interest jump fired; None if a candle or its oi is missing (window not eligible)."""
    s, p = cs.get(ct - LOOK), cs.get(ct - BACK)
    if s is None or p is None or s[3] is None or p[3] is None or not s[3] or not p[3] or p[3] <= 0:
        return None
    return (s[3] - p[3]) / p[3] > rthr


def btc_move(cs, ct):
    """Bitcoin's YES mid at -180 minus at -360 (sign of the move in the signal window), None if missing."""
    s, p = cs.get(ct - LOOK), cs.get(ct - BACK)
    if s is None or p is None:
        return None
    return (s[0] + s[1]) / 2 - (p[0] + p[1]) / 2


def alt_trade(cs, ct, vol_min=VOL_MIN):
    """The cheap side trade of an alt window, or None if it is not eligible (no two sided signal quote, no 5c to 50c side, volume rule,
    no fill candle). Uses only quotes and volume, never the result."""
    s, f = cs.get(ct - LOOK), cs.get(ct - FILL)
    if s is None or s[0] is None or s[1] is None or not 0 < s[0] < s[1] < 1:
        return None
    vol = sum((cs.get(ct - LOOK - 60 * j) or (0, 0, 0, 0))[2] or 0.0 for j in range(VOL_SPAN))
    if vol < vol_min:
        return None
    side = next((sd for sd in ("yes", "no") if LO - 1e-9 <= side_ask(s, sd) <= HI + 1e-9), None)
    if side is None:
        return None
    if f is None or f[0] is None or f[1] is None:
        return None
    fill = side_ask(f, side)
    if not 0 < fill < 1:
        return None
    return {"side": side, "fill": float(fill), "sig_ask": side_ask(s, side), "zv": (s[2] or 0) <= 0 or (f[2] or 0) <= 0}


def net10(fill, win, m=1.0):
    """Dollars of one order of 10 contracts (per-contract result x 10); fee is gen6's rounded-up 7% x C x p x (1-p)."""
    return 10 * ((1.0 if win else 0.0) - fill - gen6.fee(fill, 10, m))


def build(rthr=RTHR):
    """All eligible alt windows (trigger fired or not), outcome fields kept but not used until score."""
    B = {v_ct: cs for tk, (v_ct, res, cs, f) in load_series(BTC, LO_TS, HI_TS).items() if res in ("yes", "no")}
    res_b = {v_ct: res for tk, (v_ct, res, cs, f) in load_series(BTC, LO_TS, HI_TS).items()}
    rows = []
    for a in ALTS:
        for tk, (ct, res, cs, f) in load_series(a, LO_TS, HI_TS).items():
            if res not in ("yes", "no") or ct not in B:
                continue
            trg = btc_trigger(B[ct], ct, rthr)
            if trg is None:
                continue
            tr = alt_trade(cs, ct)
            if tr is None:
                continue
            mv = btc_move(B[ct], ct)
            rows.append({"alt": a, "t": tk, "ct": ct, "day": day_of(ct), "trig": trg, "move": mv, "res": res, **tr,
                         "win": (res == "yes") == (tr["side"] == "yes"),
                         "btc_doi": (B[ct][ct - LOOK][3] - B[ct][ct - BACK][3])})
    rows.sort(key=lambda r: (r["ct"], r["alt"]))
    return rows, B


def thirds(rows):
    days = sorted({r["day"] for r in rows})
    k = len(days) // 3
    cut1, cut2 = days[k], days[2 * k]
    def w(d):
        return 1 if d < cut1 else (2 if d < cut2 else 3)
    return w, (days[0], cut1, cut2, days[-1], len(days))


def pf(v):
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return w / l if l > 0 else (99.0 if w > 0 else 0.0)


def stats(T, label=""):
    if not T:
        return {"n": 0}
    v = [net10(t["fill"], t["win"]) for t in T]
    vs = [net10(t["fill"], t["win"], 1.2) for t in T]
    wins = [t for t in T if t["win"]]; loss = [t for t in T if not t["win"]]
    aw = sum(100 * (1 - t["fill"] - gen6.fee(t["fill"], 10)) for t in wins) / len(wins) if wins else 0.0
    al = sum(100 * (t["fill"] + gen6.fee(t["fill"], 10)) for t in loss) / len(loss) if loss else 0.0
    mean, se, z = cluster_mean_z([(t["day"], x / 10 * 100) for t, x in zip(T, v)])
    return {"n": len(T), "days": len({t["day"] for t in T}), "win": len(wins) / len(T), "avg_win_c": aw, "avg_loss_c": al,
            "payoff": aw / al if al else 0.0, "pf": pf(v), "pf_x12": pf(vs), "mean_c": mean, "z": z,
            "avg_fill": sum(t["fill"] for t in T) / len(T), "net": sum(v)}


def counts():
    rows, B = build()
    w, cuts = thirds(rows)
    print("eligible alt windows (BTC oi pair + alt side + volume rule):", len(rows), "dates", cuts)
    for a in ALTS:
        R = [r for r in rows if r["alt"] == a]
        print(a, "eligible", len(R), "trigger fired", sum(r["trig"] for r in R),
              [sum(1 for r in R if r["trig"] and w(r["day"]) == k) for k in (1, 2, 3)])
    print("trigger fired total", sum(r["trig"] for r in rows), "by third", [sum(1 for r in rows if r["trig"] and w(r["day"]) == k) for k in (1, 2, 3)])
    # outcome-free volume rule check: share of side-windows removed by the volume rule
    return rows


def run_try(rows, trig_key, wfun):
    T = [r for r in rows if trig_key(r)]
    return {k: stats([r for r in T if wfun(r["day"]) == k]) for k in (1, 2, 3)}, T


def streak_report(p, n_emp_seq):
    from . import streaks
    d = streaks.longest_losing_run_distribution(p, 100)
    return {"p_win": p, "p95": d["p95"], "p99": d["p99"], "median": d["median"], "mean": d["mean"],
            "p_ge10": streaks.prob_run_at_least(10, p, 100), "empirical": streaks.empirical_streaks(n_emp_seq)}


def score():
    if OUT.exists():
        print("Refusing to run again: the outcome was already read"); return
    rows, B = build()
    w, cuts = thirds(rows)
    A, TA = run_try(rows, lambda r: r["trig"], w)
    out = {"cuts": cuts, "A": {str(k): v for k, v in A.items()}}
    w12 = all(A[k]["n"] and A[k]["pf"] >= 1.5 and A[k]["pf_x12"] > 1.0 for k in (1, 2))
    # W3 holdout is read only if W1 and W2 pass (the rule is frozen by the registration)
    pooled_T = [r for r in TA if w(r["day"]) in (1, 2)] + ([r for r in TA if w(r["day"]) == 3] if w12 else [])
    out["W3_read"] = bool(w12)
    if not w12:
        out["A"]["3"] = {"n": None, "note": "unread"}
    out["pooled"] = stats(pooled_T)
    out["pooled_ex_w3"] = stats([r for r in TA if w(r["day"]) in (1, 2)])
    n = out["pooled"]["n"]
    if n < FLOOR_N:
        verdict = "NOT_ENOUGH_DATA"
    elif not w12 or (A[3]["n"] and A[3]["pf"] < 1.5):
        verdict = "FALSIFIED"
    else:
        verdict = "NOT_YET_FALSIFIED"
    out["verdict"] = verdict
    # per alt (information)
    out["per_alt"] = {a: stats([r for r in pooled_T if r["alt"] == a]) for a in ALTS}
    out["per_alt_W"] = {a: {k: stats([r for r in TA if r["alt"] == a and w(r["day"]) == k]) for k in (1, 2)} for a in ALTS}
    # direction: cheaper side agrees with sign of Bitcoin's YES-mid move from -360 to -180
    def agree(r):
        m = r["move"]
        if m is None or m == 0:
            return "flat"
        return "agree" if (m > 0) == (r["side"] == "yes") else "disagree"
    ag = defaultdict(list)
    for r in pooled_T:
        ag[agree(r)].append(r)
    out["agreement"] = {k: {"n": len(v), "share": len(v) / len(pooled_T), "win": sum(t["win"] for t in v) / len(v), "pf": pf([net10(t["fill"], t["win"]) for t in v])} for k, v in ag.items()}
    out["yes_share"] = sum(1 for r in pooled_T if r["side"] == "yes") / len(pooled_T)
    # Try B (information only): trigger = OICORE's fixed count threshold doi > 86299.56
    TB = [r for r in rows if r["btc_doi"] > BTC_THRESH]
    out["B"] = {str(k): stats([r for r in TB if w(r["day"]) == k and (k < 3 or w12)]) for k in (1, 2, 3)}
    # OICORE overlap: windows where OICORE's own BTC rule (fixed threshold, BTC cheap side 5c to 50c at -180) fires
    from .oicorex1 import stage_score, VAL, DISC, FWD_FROM
    oi_tr = {}
    for lo, hi in (DISC, VAL, (FWD_FROM, HI_TS)):
        sc, tr = stage_score(BTC, BTC_THRESH, lo, hi)
        for t in tr:
            oi_tr[t["close"]] = t
    out["oicore_parity"] = {"disc": [stage_score(BTC, BTC_THRESH, *DISC)[0].get(k) for k in ("n", "pf")], "val": [stage_score(BTC, BTC_THRESH, *VAL)[0].get(k) for k in ("n", "pf")]}
    xw = sorted({r["ct"] for r in pooled_T})
    out["overlap"] = {"xoi_windows": len(xw), "oicore_fires": sum(1 for c in xw if c in oi_tr),
                      "share": sum(1 for c in xw if c in oi_tr) / len(xw)}
    # daily net correlation (XOI1 pooled trades vs OICORE trades), on dates covered by the pooled sample
    days = sorted({r["day"] for r in pooled_T}); dset = set(days)
    xd = defaultdict(float); od = defaultdict(float)
    for r in pooled_T:
        xd[r["day"]] += net10(r["fill"], r["win"])
    for c, t in oi_tr.items():
        d = day_of(c)
        if d in dset:
            od[d] += t["net10"]
    def corr(a, b):
        n = len(a)
        if n < 3:
            return None
        ma, mb = sum(a) / n, sum(b) / n
        sa = math.sqrt(sum((x - ma) ** 2 for x in a)); sb = math.sqrt(sum((y - mb) ** 2 for y in b))
        return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb) if sa and sb else None
    out["corr_all_days"] = [corr([xd[d] for d in days], [od[d] for d in days]), len(days)]
    both = [d for d in days if d in xd and d in od]
    out["corr_both_days"] = [corr([xd[d] for d in both], [od[d] for d in both]), len(both)]
    out["streaks"] = streak_report(out["pooled"]["win"], [t["win"] for t in sorted(pooled_T, key=lambda r: (r["ct"], r["alt"]))])
    out["trades_per_day"] = out["pooled"]["n"] / out["pooled"]["days"]
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    {"counts": counts, "score": score}[sys.argv[1]]()
