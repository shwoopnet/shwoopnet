"""QSTALE1 (workers/QSTALE1_REGISTRATION.md): a stale quote with trades printing and a wide spread, as the trigger for the cheaper side
of Bitcoin, HYPE, NEAR, Zcash, BNB and XRP 15 minute markets, held to settlement. Research only; nothing here places an order, reads a
key or decides anything live.
    PYTHONPATH=src python -m scalper.qstale1 counts   (outcome-free: eligible windows, trigger counts, thirds; reads NO result value)
    PYTHONPATH=src python -m scalper.qstale1 score    (once: W1, W2 and, only if both pass, W3; refuses a second run)
Candle = (bid_c, ask_c, volume, oi) keyed by end_ts, both candle shapes already normalised by the ingest (candlefield.py).
Fill and fee follow xoi1 / oirel / gen6: cheap side = YES first then NO whose ask at the candle ending 180 s before the close is 0.05 to
0.50, fill at that side's ask on the candle ending 120 s before the close, fee 7% x C x p x (1-p) rounded up per order (gen6.fee), C = 10.
"""
from __future__ import annotations

import bisect
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from . import gen6
from .calibration import cluster_mean_z
from .oicorex1 import load_series, BTC_THRESH
from .paths import DATA_DIR

SERIES = ["KXBTC15M", "KXHYPE15M", "KXNEAR15M", "KXZEC15M", "KXBNB15M", "KXXRP15M"]
LOOK, BACK, FILL = 180, 360, 120
MINUTES = (300, 240, 180)            # candles ending 300, 240, 180 s before the close are the 3 minutes of the signal window
LO, HI = 0.05, 0.50
STALE = 0.005                        # |change of the YES mid| in each signal minute at most half a cent
TRAIL = 86400                        # trailing 24 hours of the series' own candles, strictly before the look candle
PATH_MIN = 48                        # at least this many earlier markets (closing in the previous 24 hours) for the staleness reference
QS = 100.0 / 3.0                     # stale = path length at or below the 33.3rd percentile of the previous 24 hours' markets of the series
TRAIL_MIN = 300                      # at least this many two sided candles in the trailing day, else the window is not eligible
Q = 100.0 * 2.0 / 3.0                # top tertile: spread strictly above the 66.67th percentile of the trailing day
FLOOR_N = 150
Z_BAR = 5.27
OUT = DATA_DIR / "qstale1_score.json"
LO_TS = int(datetime(2026, 8, 6, tzinfo=timezone.utc).timestamp())
HI_TS = 2 ** 40
EPS = 1e-9


def side_ask(q, side):
    return q[1] if side == "yes" else round(1 - q[0], 6)


def day_of(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def two_sided(c):
    return c is not None and c[0] is not None and c[1] is not None and 0 < c[0] < c[1] < 1


def mid(c):
    return (c[0] + c[1]) / 2


def path_vol(cs, ct):
    """(path, volume_seen, literal_stale) over the 3 signal minutes, or None if any of the 4 candles (-360 baseline, -300, -240, -180) lacks
    a two sided quote. path = sum of the 3 absolute one minute changes of the YES mid; volume_seen = at least one of the 3 minutes printed
    volume; literal_stale = no minute changed by more than half a cent (the first draft, kept only to report how rarely it fires)."""
    seq = [cs.get(ct - BACK)] + [cs.get(ct - m) for m in MINUTES]
    if not all(two_sided(c) for c in seq):
        return None
    d = [abs(mid(seq[i + 1]) - mid(seq[i])) for i in range(3)]
    return sum(d), any((c[2] or 0) > 0 for c in seq[1:]), all(x <= STALE + EPS for x in d)


def trailing_q(ts_arr, sp_arr, look_ts):
    """66.67th percentile of the spreads of this series' two sided candles with end_ts in [look_ts - 24h, look_ts); None under TRAIL_MIN."""
    lo = bisect.bisect_left(ts_arr, look_ts - TRAIL)
    hi = bisect.bisect_left(ts_arr, look_ts)
    if hi - lo < TRAIL_MIN:
        return None
    return float(np.percentile(sp_arr[lo:hi], Q))


def cheap_trade(cs, ct):
    """The cheap side trade of a window, or None (no 5c to 50c side at the look, or no fill candle). Quotes only, never the result."""
    s, f = cs.get(ct - LOOK), cs.get(ct - FILL)
    side = next((sd for sd in ("yes", "no") if LO - EPS <= side_ask(s, sd) <= HI + EPS), None)
    if side is None or not two_sided(f):
        return None
    fill = side_ask(f, side)
    if not 0 < fill < 1:
        return None
    return {"side": side, "fill": float(fill), "sig_ask": side_ask(s, side)}


def net10(fill, win, m=1.0):
    return 10 * ((1.0 if win else 0.0) - fill - gen6.fee(fill, 10, m))


def build():
    """Every eligible window of the six series (trigger fired or not). `res` is kept on the row but nothing before score() reads it."""
    rows = []
    for a in SERIES:
        M = load_series(a, LO_TS, HI_TS)
        pts = sorted((e, c[1] - c[0]) for _tk, (_ct, _r, cs, _f) in M.items() for e, c in cs.items() if two_sided(c))
        ts_arr = [p[0] for p in pts]; sp_arr = np.array([p[1] for p in pts])
        PV = {}
        for tk, (ct, res, cs, f) in M.items():
            pv = path_vol(cs, ct)
            if pv is not None:
                PV[ct] = pv[0]
        pct = sorted(PV)
        pv_arr = [PV[c] for c in pct]
        for tk, (ct, res, cs, f) in M.items():
            if res not in ("yes", "no"):
                continue
            sw = path_vol(cs, ct)
            if sw is None:
                continue
            lo_i, hi_i = bisect.bisect_left(pct, ct - TRAIL), bisect.bisect_left(pct, ct)
            if hi_i - lo_i < PATH_MIN:
                continue
            qs = float(np.percentile(pv_arr[lo_i:hi_i], QS))
            q = trailing_q(ts_arr, sp_arr, ct - LOOK)
            if q is None:
                continue
            tr = cheap_trade(cs, ct)
            if tr is None:
                continue
            sp = cs[ct - LOOK][1] - cs[ct - LOOK][0]
            rows.append({"series": a, "t": tk, "ct": ct, "day": day_of(ct), "stale": sw[0] <= qs + EPS, "lit": sw[2], "path": sw[0], "vol": sw[1], "spread": sp, "q": q,
                         "wide": sp > q + EPS, "res": res, **tr, "win": (res == "yes") == (tr["side"] == "yes")})
    rows.sort(key=lambda r: (r["ct"], r["series"]))
    for r in rows:
        r["A"] = r["stale"] and r["vol"] and r["wide"]     # primary
        r["B"] = r["stale"] and r["vol"]                   # alternative: staleness only (no spread condition)
    return rows


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


def stats(T):
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
    rows = build()
    w, cuts = thirds(rows)
    print("eligible windows (4 two sided candles, trailing day, 5c-50c side, fill candle):", len(rows), "dates", cuts)
    for a in SERIES:
        R = [r for r in rows if r["series"] == a]
        print(a, "eligible", len(R), "stale", sum(r["stale"] for r in R), "literal-half-cent+vol", sum(r["lit"] and r["vol"] for r in R), "wide", sum(r["wide"] for r in R), "stale+vol (B)", sum(r["B"] for r in R), "A", sum(r["A"] for r in R),
              "A by third", [sum(1 for r in R if r["A"] and w(r["day"]) == k) for k in (1, 2, 3)])
    print("A total", sum(r["A"] for r in rows), "B total", sum(r["B"] for r in rows),
          "A by third", [sum(1 for r in rows if r["A"] and w(r["day"]) == k) for k in (1, 2, 3)],
          "B by third", [sum(1 for r in rows if r["B"] and w(r["day"]) == k) for k in (1, 2, 3)])
    return rows


def streak_report(p, seq):
    from . import streaks
    d = streaks.longest_losing_run_distribution(p, 100)
    return {"p_win": p, "p95": d["p95"], "p99": d["p99"], "median": d["median"], "mean": d["mean"],
            "p_ge10": streaks.prob_run_at_least(10, p, 100), "empirical": streaks.empirical_streaks(seq)}


def score():
    if OUT.exists():
        print("Refusing to run again: the outcome was already read"); return
    rows = build()
    w, cuts = thirds(rows)
    TA = [r for r in rows if r["A"]]
    A = {k: stats([r for r in TA if w(r["day"]) == k]) for k in (1, 2, 3)}
    out = {"cuts": cuts, "A": {str(k): v for k, v in A.items()}}
    w12 = all(A[k]["n"] and A[k]["pf"] >= 1.5 and A[k]["pf_x12"] > 1.0 for k in (1, 2))
    pooled_T = [r for r in TA if w(r["day"]) in (1, 2)] + ([r for r in TA if w(r["day"]) == 3] if w12 else [])
    out["W3_read"] = bool(w12)
    if not w12:
        out["A"]["3"] = {"n": None, "note": "unread"}
    out["pooled"] = stats(pooled_T)
    n = out["pooled"]["n"]
    if n < FLOOR_N:
        verdict = "NOT_ENOUGH_DATA"
    elif not w12 or (A[3]["n"] and A[3]["pf"] < 1.5):
        verdict = "FALSIFIED"
    else:
        verdict = "NOT_YET_FALSIFIED"
    out["verdict"] = verdict
    out["per_series"] = {a: stats([r for r in pooled_T if r["series"] == a]) for a in SERIES}
    out["per_series_W"] = {a: {k: stats([r for r in TA if r["series"] == a and w(r["day"]) == k]) for k in (1, 2)} for a in SERIES}
    # contrary hypothesis information: stale windows that were not wide, and wide windows that were not stale (W1, W2 only, no verdict)
    out["info_wide_not_stale"] = {str(k): stats([r for r in rows if r["wide"] and not r["stale"] and r["vol"] and w(r["day"]) == k]) for k in (1, 2)}
    # Try B (alternative, separately counted): staleness with trades, no spread condition
    TB = [r for r in rows if r["B"]]
    out["B"] = {str(k): stats([r for r in TB if w(r["day"]) == k and (k < 3 or w12)]) for k in (1, 2, 3)}
    out["B_verdict_note"] = "Try B is read by the same kill rules; its W3 is read only if the primary passed (not otherwise)"
    # OICORE overlap
    from .oicorex1 import stage_score, VAL, DISC, FWD_FROM
    oi_tr = {}
    for lo, hi in (DISC, VAL, (FWD_FROM, HI_TS)):
        sc, tr = stage_score("KXBTC15M", BTC_THRESH, lo, hi)
        for t in tr:
            oi_tr[t["close"]] = t
    btc_T = [r for r in pooled_T if r["series"] == "KXBTC15M"]
    out["overlap"] = {"entries": len(pooled_T), "btc_entries": len(btc_T),
                      "btc_also_oicore": sum(1 for r in btc_T if r["ct"] in oi_tr),
                      "share_of_btc_entries": (sum(1 for r in btc_T if r["ct"] in oi_tr) / len(btc_T)) if btc_T else None,
                      "share_of_all_entries": sum(1 for r in pooled_T if r["series"] == "KXBTC15M" and r["ct"] in oi_tr) / len(pooled_T) if pooled_T else None,
                      "oicore_entries_in_sample_dates": None}
    dset = {r["day"] for r in pooled_T}
    oi_in = [c for c in oi_tr if day_of(c) in dset]
    out["overlap"]["oicore_entries_in_sample_dates"] = len(oi_in)
    btc_ct = {r["ct"] for r in btc_T}
    out["overlap"]["oicore_caught_by_qstale"] = sum(1 for c in oi_in if c in btc_ct)
    out["streaks"] = streak_report(out["pooled"]["win"], [t["win"] for t in sorted(pooled_T, key=lambda r: (r["ct"], r["series"]))]) if pooled_T else None
    out["trades_per_day"] = out["pooled"]["n"] / out["pooled"]["days"] if pooled_T else 0
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    {"counts": counts, "score": score}[sys.argv[1]]()
