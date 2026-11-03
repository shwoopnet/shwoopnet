"""TSLM1 (workers/TSLM1_REGISTRATION.md): time since the last big one-minute move, from the 1 minute candles. Research only; nothing here
places an order, reads a key or decides anything live.
    PYTHONPATH=src python -m scalper.tslm1 counts   (outcome-free: eligible windows, trigger counts per third; reads NO result)
    PYTHONPATH=src python -m scalper.tslm1 score    (once; refuses a second run)
Candle = (bid_c, ask_c, volume, oi) keyed by end_ts. Mid change at end e = mid(e) - mid(e - 60), both candles two sided and present.
Big = absolute change (ends 840..180 s before its market's close only, AMENDMENT 1) >= the 95th percentile (and > 0) of that series' one minute absolute mid changes with end in (open - 24h, open]
(open = close - 900, so nothing from the window itself is in the threshold). Calm = absolute change <= the same trailing median.
PRIMARY (SHOCK_CALM): a big change ending 840..360 s before the close (first 9 minutes) AND the three changes ending 300, 240, 180 s
before the close are all available, all <= the median and none big. LATE (alternative, one more try): no big change in the first 9
minutes (at least 7 of 9 available) AND a big change among the three changes ending 300, 240, 180 s before the close.
Trade (both): cheaper side with ask 0.05 to 0.50 at the candle ending 180 s before the close (YES first), volume rule of XOI1, fill at that
side's ask on the candle ending 120 s before the close, C = 10, fee 7% x C x p x (1-p) rounded up, held to settlement.
"""
from __future__ import annotations

import bisect
import json
import math
import sys
from collections import defaultdict

import numpy as np

from .oicorex1 import load_series, BTC_THRESH
from .paths import DATA_DIR
from . import xoi1

SERIES = ["KXBTC15M", "KXHYPE15M", "KXNEAR15M", "KXZEC15M", "KXBNB15M", "KXXRP15M"]
BTC = "KXBTC15M"
TRAIL = 86400
MIN_TRAIL = 500                      # trailing changes needed for a threshold, else the window is not eligible
EARLY = [840 - 60 * j for j in range(9)]      # change ends (seconds before the close): 840 .. 360 (first 9 minutes)
LASTE = [300, 240, 180]                        # the three changes ending 300, 240, 180 s before the close (the last 3 minutes up to the look)
OUT = DATA_DIR / "tslm1_score.json"
FLOOR_N = 150
Z_BAR = 5.27


def mid_of(c):
    if c is None or c[0] is None or c[1] is None or not 0 <= c[0] <= c[1] <= 1:
        return None
    return (c[0] + c[1]) / 2


def change_at(cs, e):
    """Absolute one minute mid change of the candle ending at e, or None if it or the previous candle is missing / not two sided."""
    a, b = mid_of(cs.get(e)), mid_of(cs.get(e - 60))
    return None if a is None or b is None else abs(a - b)


def series_changes(markets):
    """Sorted parallel arrays (ends, abs changes) of every one minute change in the series (within each market)."""
    pairs = []
    for tk, (ct, res, cs, f) in markets.items():
        for e in cs:
            if not 180 <= ct - e <= 840:       # AMENDMENT 1: only the part of a market the trigger reads (see registration)
                continue
            d = change_at(cs, e)
            if d is not None:
                pairs.append((e, d))
    pairs.sort()
    return [p[0] for p in pairs], np.array([p[1] for p in pairs])


def thresholds(ends, vals, open_ts):
    """(p95, median) of changes with end in (open - 24h, open], or None if fewer than MIN_TRAIL."""
    lo = bisect.bisect_right(ends, open_ts - TRAIL)
    hi = bisect.bisect_right(ends, open_ts)
    if hi - lo < MIN_TRAIL:
        return None
    seg = vals[lo:hi]
    return float(np.quantile(seg, 0.95)), float(np.median(seg))


def classify(cs, ct, p95, med):
    """(primary, late, eligible_shape) booleans for one window from candles up to the look only."""
    def big(d):
        return d is not None and d >= p95 and d > 0
    early = [change_at(cs, ct - s) for s in EARLY]
    last = [change_at(cs, ct - s) for s in LASTE]
    if any(d is None for d in last):
        return False, False, False
    primary = any(big(d) for d in early) and all(d <= med and not big(d) for d in last)
    avail = [d for d in early if d is not None]
    late = len(avail) >= 7 and not any(big(d) for d in avail) and any(big(d) for d in last)
    return primary, late, True


def build():
    rows = []
    for s in SERIES:
        M = load_series(s, xoi1.LO_TS, xoi1.HI_TS)
        ends, vals = series_changes(M)
        for tk, (ct, res, cs, f) in M.items():
            if res not in ("yes", "no"):
                continue
            th = thresholds(ends, vals, ct - 900)
            if th is None:
                continue
            primary, late, ok = classify(cs, ct, *th)
            if not ok:
                continue
            tr = xoi1.alt_trade(cs, ct)
            if tr is None:
                continue
            rows.append({"alt": s, "t": tk, "ct": ct, "day": xoi1.day_of(ct), "primary": primary, "late": late, "res": res, **tr,
                         "win": (res == "yes") == (tr["side"] == "yes")})
    rows.sort(key=lambda r: (r["ct"], r["alt"]))
    return rows


def counts():
    rows = build()
    w, cuts = xoi1.thirds(rows)
    days = len({r["day"] for r in rows})
    print("eligible windows (shape + side + volume rule):", len(rows), "dates", cuts)
    for key in ("primary", "late"):
        print(key, "fired", sum(r[key] for r in rows), "per day", sum(r[key] for r in rows) / days,
              "by third", [sum(1 for r in rows if r[key] and w(r["day"]) == k) for k in (1, 2, 3)])
        for s in SERIES:
            print("  ", s, sum(1 for r in rows if r["alt"] == s and r[key]), "of", sum(1 for r in rows if r["alt"] == s))


def verdict_for(A, w12, n):
    if n < FLOOR_N:
        return "NOT_ENOUGH_DATA"
    if not w12 or (A[3]["n"] and A[3]["pf"] < 1.5):
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED"


def score():
    if OUT.exists():
        print("Refusing to run again: the outcome was already read"); return
    rows = build()
    w, cuts = xoi1.thirds(rows)
    from .oicorex1 import stage_score, DISC, VAL, FWD_FROM
    oi = {}
    for lo, hi in (DISC, VAL, (FWD_FROM, xoi1.HI_TS)):
        for t in stage_score(BTC, BTC_THRESH, lo, hi)[1]:
            oi[t["t"]] = t
    out = {"cuts": cuts}
    for key in ("primary", "late"):
        T = [r for r in rows if r[key]]
        A = {k: xoi1.stats([r for r in T if w(r["day"]) == k]) for k in (1, 2, 3)}
        w12 = all(A[k]["n"] and A[k]["pf"] >= 1.5 and A[k]["pf_x12"] > 1.0 for k in (1, 2))
        used = [r for r in T if w(r["day"]) in (1, 2) or (w12 and w(r["day"]) == 3)]
        res = {"W3_read": bool(w12), "A": {str(k): (A[k] if k < 3 or w12 else {"n": None, "note": "unread"}) for k in (1, 2, 3)}}
        res["pooled"] = xoi1.stats(used)
        res["verdict"] = verdict_for(A, w12, res["pooled"]["n"])
        res["group_btc"] = xoi1.stats([r for r in used if r["alt"] == BTC])
        res["group_alts"] = xoi1.stats([r for r in used if r["alt"] != BTC])
        res["per_series"] = {s: xoi1.stats([r for r in used if r["alt"] == s]) for s in SERIES}
        res["per_series_W"] = {s: {k: xoi1.stats([r for r in T if r["alt"] == s and w(r["day"]) == k]) for k in (1, 2)} for s in SERIES}
        res["yes_share"] = sum(1 for r in used if r["side"] == "yes") / len(used) if used else None
        res["max_fill"] = max((r["fill"] for r in used), default=None)
        res["worst_loss10"] = max((-xoi1.net10(r["fill"], False) for r in used), default=None)
        btc_used = [r for r in used if r["alt"] == BTC]
        res["oicore_overlap"] = {"entries": len(used), "oicore_entries": sum(1 for r in btc_used if r["t"] in oi),
                                 "share_all": (sum(1 for r in btc_used if r["t"] in oi) / len(used)) if used else None,
                                 "btc_entries": len(btc_used),
                                 "share_btc": (sum(1 for r in btc_used if r["t"] in oi) / len(btc_used)) if btc_used else None}
        res["streaks"] = xoi1.streak_report(res["pooled"]["win"], [t["win"] for t in used]) if used else None
        res["trades_per_day"] = res["pooled"]["n"] / res["pooled"]["days"] if used else None
        out[key] = res
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    {"counts": counts, "score": score}[sys.argv[1]]()
