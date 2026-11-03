"""BOOKCH1 (workers/BOOKCH1_REGISTRATION.md): relative book imbalance, or cheap-side depth withdrawal, on the CHEAPER side of the
15 minute Bitcoin and XRP markets at the 180 s look, held to settlement. FORWARD ONLY, research only: no order, no key, no promote.

Evaluator for the forward ledger (source "r6"): `scalper.bookch1:forward_eval`, params {"definition": "ratio" | "withdrawal"}.
Polls are scalper.quote2b.Poll (exchange time; .yb/.ybs YES bids and sizes best first, .nb/.nbs NO bids and sizes best first).
"""
from __future__ import annotations

import math

from .fwdeval import NoData

LOOK, EARLY_LOOK = 180, 360          # seconds before the close
LOOK_TOL = 10.0                      # the look poll may be at most this much earlier than the look
FILL_DELAY, FILL_TOL = 1.0, 20.0     # first poll at or after look + 1 s, within 20 s
BAND = (0.05, 0.50)
MIN_SIZE = 10                        # contracts displayed at the fill ask
HIST_S, HIST_GAP = 86_400, 900       # trailing windows: closed between T-86400 and T-900
MIN_HIST = 48
Q_RATIO, Q_DROP = 2 / 3, 0.10
SERIES = ("KXBTC15M", "KXXRP15M")
N_RUNNING_BEFORE, N_THIS = 728_722, 2


def s5(sizes):
    return float(sum(sizes[:5]))


def cheaper(p):
    """('yes'|'no', ask) of the cheaper side of a poll, or None (missing best bid, or equal asks)."""
    if not p.nb or not p.yb:
        return None
    ya, na = 1 - p.nb[0], 1 - p.yb[0]
    if abs(ya - na) < 1e-12:
        return None
    return ("yes", ya) if ya < na else ("no", na)


def bids(p, side):
    return p.ybs if side == "yes" else p.nbs


def last_at(polls, t, early):
    best = None
    for p in polls:
        if p.t <= t + 1e-9:
            best = p
        else:
            break
    return best if best is not None and best.t >= t - early - 1e-9 else None


def first_at(polls, t, late):
    for p in polls:
        if p.t >= t - 1e-9:
            return p if p.t <= t + late + 1e-9 else None
    return None


def look_stats(polls, close):
    """Per window numbers at the look: cheaper side, its ask, R and D (None where undefined). Uses polls up to the look only."""
    p = last_at(polls, close - LOOK, LOOK_TOL)
    if p is None:
        return None
    ch = cheaper(p)
    if ch is None:
        return None
    side, ask = ch
    mine = s5(bids(p, side))
    other = s5(bids(p, "no" if side == "yes" else "yes"))
    ratio = mine / other if other > 0 else None
    drop = None
    q = last_at(polls, close - EARLY_LOOK, LOOK_TOL)
    if q is not None:
        then = s5(bids(q, side))
        if then > 0:
            drop = (mine - then) / then
    return {"side": side, "ask": ask, "ratio": ratio, "drop": drop, "t": p.t}


def quantile(vals, q):
    """Type 7 (linear interpolation) quantile."""
    v = sorted(vals)
    if not v:
        raise ValueError("empty")
    h = (len(v) - 1) * q
    lo = math.floor(h)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (h - lo)


def trailing_cut(hist, close, key, q):
    """hist: {close_ts: look_stats dict}. Quantile of `key` over windows that closed in [close-86400, close-900]; None if fewer than 48."""
    vals = [s[key] for c, s in hist.items() if close - HIST_S <= c <= close - HIST_GAP and s and s.get(key) is not None]
    return quantile(vals, q) if len(vals) >= MIN_HIST else None


def decide(polls, close, hist, definition="ratio"):
    """Returns (trade dict or None, reason). reason 'nodata' means the caller should raise NoData."""
    st = look_stats(polls, close)
    if st is None:
        return None, "nodata"
    key, q = ("ratio", Q_RATIO) if definition == "ratio" else ("drop", Q_DROP)
    cut = trailing_cut(hist, close, key, q)
    if cut is None:
        return None, "nodata"
    v = st[key]
    if v is None:
        return None, "undefined"
    if definition == "ratio":
        if not v > cut:
            return None, "below tertile"
    elif not (v < 0 and v < cut):
        return None, "no withdrawal"
    if not BAND[0] - 1e-9 <= st["ask"] <= BAND[1] + 1e-9:
        return None, "ask out of band"
    f = first_at(polls, close - LOOK + FILL_DELAY, FILL_TOL)
    if f is None:
        return None, "nodata"
    ch = cheaper(f)
    if ch is None:
        return None, "nodata"
    ask = (1 - f.nb[0]) if st["side"] == "yes" else (1 - f.yb[0])
    size = f.nbs[0] if st["side"] == "yes" else f.ybs[0]
    if not BAND[0] - 1e-9 <= ask <= BAND[1] + 1e-9 or size < MIN_SIZE:
        return None, "fill out of band or thin"
    return {"side": st["side"], "entry": ask, "t": f.t, "value": v, "cut": cut}, "trade"


R6_START = 1_793_311_200   # 2026-10-29 22:00 UTC, just before the recorder's first run: nothing earlier exists
_CACHE: dict = {}


def _load(series, min_close):
    """All R6 windows of one series closing after min_close, as {close_ts: look_stats}; loaded once per process and series."""
    if series not in _CACHE:
        from .fwdledger import load_r6
        _CACHE[series] = {w["close_ts"]: look_stats(w["polls"], w["close_ts"]) for w in load_r6({series}, min_close)}
    return _CACHE[series]


def history(window, params):
    """The window's trailing history. params["_history"] (tests) wins; else every R6 window of the series from params["history_from"]."""
    if "_history" in params:
        return params["_history"]
    return _load(window["series"], int(params.get("history_from", R6_START)))


def forward_eval(window, params):
    if window.get("series") not in SERIES or window["series"] != params.get("series", window["series"]):
        return None
    d, why = decide(window["polls"], window["close_ts"], history(window, params), params.get("definition", "ratio"))
    if why == "nodata":
        raise NoData("look poll, fill poll or 24 hour history missing")
    if d is None:
        return None
    return {"side": d["side"], "entry": float(d["entry"]), "exit": None, "t": int(d["t"]),
            "note": f"{params.get('definition', 'ratio')} {d['value']:.3f} vs cut {d['cut']:.3f}"}
