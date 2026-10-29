"""Reference evaluators for the forward ledger (`scalper.fwdledger`, workers/candidates/README.md). Research only; nothing here
places an order, reads a key or decides anything live.

An evaluator is `fn(window: dict, params: dict) -> dict | None`:
  return None              the rule did not trade this window
  return {"side": "yes"|"no", "entry": ask paid (0..1), "exit": bid sold at (0..1) or None (held to settlement),
          optional "t": unix second of the entry quote, "zero_volume": bool (entry or exit candle had no volume), "note": str}
  raise NoData(reason)     the window lacks what the rule needs (a missing candle, spot, a peer market): the ledger counts the
                           window as NOT evaluated, so a data gap is never scored as "no trade".
Size is always 1 contract per decision; the ledger prices fees at 1 and 10 contracts itself.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np


class NoData(Exception):
    """The window lacks data the rule needs; the ledger skips it as unavailable (never as a no-trade)."""


def _side_quotes(q, side):
    bid_c, ask_c = q[0], q[1]
    return (bid_c, ask_c) if side == "yes" else (round(1 - ask_c, 4), round(1 - bid_c, 4))


# ---------------------------------------------------------------- (a) l1_like

def l1_like(window, params):
    """Buy the side whose ask is inside [lo, hi] at the candle ending exactly `look_s` seconds before the close; hold to settlement.
    params: look_s (default 360), lo (0.88), hi (0.97), sides (["yes", "no"], tried in that order).
    Source: "candles" (window["candles"] = {end_ts: (bid_c, ask_c, volume, oi)})."""
    look = int(params.get("look_s", 360))
    lo, hi = float(params.get("lo", 0.88)), float(params.get("hi", 0.97))
    t = window["close_ts"] - look
    q = window["candles"].get(t)
    if q is None:
        raise NoData(f"no candle at {look}s left")
    for side in params.get("sides", ["yes", "no"]):
        bid, ask = _side_quotes(q, side)
        if lo - 1e-9 <= ask <= hi + 1e-9:
            return {"side": side, "entry": float(ask), "exit": None, "t": t, "zero_volume": (q[2] or 0) <= 0}
    return None


# ---------------------------------------------------------------- (b) gen1

_CACHE = {}


def _spot():
    if "spot" not in _CACHE:
        from .gen1 import spot_load
        _CACHE["spot"] = spot_load()
    return _CACHE["spot"]


def _fut():
    if "fut" not in _CACHE:
        from . import auto3
        auto3.FUT = auto3.fut_load()
        _CACHE["fut"] = auto3.FUT
    return _CACHE["fut"]


def gen1(window, params):
    """ONE GEN1 strategy dict (as frozen in data/gen1_survivors.json: L_hi, L_lo, side, asset, conds, c) applied to one window,
    with GEN1's own features (`scalper.gen1.build_chunk`) and exits (`scalper.gen1.exits`, combo index c).
    params: {"strategy": {...}} or the strategy dict itself.
    GEN1 picks, per window, the FIRST qualifying row in its order (most seconds left first, YES before NO), so this does too.
    Features that GEN1 set to 0 when their input was missing (z, r3 from spot bars; tb1, tb5 from Binance perp bars; xa_*, xb_* from
    the other two markets) raise NoData here when a condition uses them and the input is missing, instead of silently reading 0."""
    from . import auto3
    from . import gen1 as g
    from .scalp12 import CUR, sigma1
    s = params.get("strategy", params)
    series = window["series"]
    if series not in g.ASSET or (s.get("asset") is not None and g.ASSET[series] != s["asset"]):
        return None
    conds = [tuple(c) for c in s["conds"]]
    used = {f for f, _, _ in conds}
    close_ts, strike, cs = window["close_ts"], window.get("strike"), window["candles"]
    peers = window.get("peers", {})
    keys = sorted(k for k in cs if k <= close_ts - 60)
    oth = [peers.get(o) for o in g.OTHERS[series]]
    need_spot = series in CUR and bool(used & {"z", "r3"})
    need_flow = series in CUR and bool(used & {"tb1", "tb5"})
    if (used & {"xa_d2", "xa_mid"} and oth[0] is None) or (used & {"xb_d2", "xb_mid"} and oth[1] is None):
        raise NoData("peer market missing")
    spot = _spot() if need_spot else {}
    if need_flow:
        _fut()
    sides = [1, 0] if s["side"] == "both" else ([1] if s["side"] == "yes" else [0])
    for L in g.LEFTS:
        if not (s["L_lo"] <= L <= s["L_hi"]):
            continue
        t = close_ts - L
        q = cs.get(t)
        if q is None:
            continue
        later = [k for k in keys if k > t]
        if not later:
            continue
        z0 = r30 = 0.0
        if series in CUR and need_spot:
            cur = CUR[series]; sp = spot.get((cur, t - 60)); sg = sigma1(spot, cur, t); s3 = spot.get((cur, t - 240))
            if not (sp and sg and strike and s3):
                raise NoData("spot bars missing")
            z0 = math.log(sp / strike) / (sg * math.sqrt(L / 60)); r30 = math.log(sp / s3)
        xs = []
        for o in oth:
            if o is None:
                xs += [0.0, 0.5]; continue
            a, b = o.get(t), o.get(t - 120)
            ma = (a[0] + a[1]) / 2 if a else 0.5; mb = (b[0] + b[1]) / 2 if b else ma
            xs += [ma - mb, ma]
        vol = q[2]; doi = (q[3] - cs[t - 180][3]) if (t - 180) in cs else 0.0
        ent_mid = (q[0] + q[1]) / 2
        kb = np.array(later)
        yb = np.array([cs[k][0] for k in later]); ya = np.array([cs[k][1] for k in later])
        vz = np.array([cs[k][2] <= 0 for k in later])
        for yes in sides:
            side = "yes" if yes else "no"
            bid, ask = _side_quotes(q, side)
            if not 0.03 <= ask <= 0.85:
                continue
            ds = []
            for lag in (60, 120, 180, 300):
                p = cs.get(t - lag); ds.append(bid - _side_quotes(p, side)[0] if p else 0.0)
            path = [_side_quotes(cs[t - 60 * j], side)[0] for j in range(6) if (t - 60 * j) in cs]
            rng5 = max(path) - min(path) if path else 0.0
            sgn = 1 if yes else -1
            if need_flow:
                b0 = [auto3.FUT.get((CUR[series], t - 60 * k)) for k in range(1, 12)]
                if any(x is None for x in b0):
                    raise NoData("perp bars missing")
            fl = auto3.flow(CUR[series], t, sgn) if (series in CUR and need_flow) else (0.0,) * 5
            row = [g.ASSET[series], yes, L, ask, bid, ask - bid, ds[0], ds[1], ds[2], ds[3], rng5, vol, doi,
                   datetime.fromtimestamp(t, timezone.utc).hour, sgn * xs[0], xs[1], sgn * xs[2], xs[3], sgn * z0, sgn * r30, fl[0], fl[1]]
            X = np.array(row, dtype=np.float32)          # GEN1 compares float32 columns with its thresholds
            ok = True
            for f, op, th in conds:
                v = X[g.FEATS.index(f)]
                if not ((v <= th) if op == "le" else (v > th)):
                    ok = False; break
            if not ok:
                continue
            bids = yb if yes else 1 - ya
            idx = int(g.exits(bids, ya - yb, (ya + yb) / 2, kb, ask, yes, close_ts, ent_mid)[s["c"]])
            return {"side": side, "entry": float(ask), "exit": float(bids[idx]), "t": t,
                    "zero_volume": bool(vz[idx] or vol <= 0), "note": f"exit at {close_ts - int(kb[idx])}s left"}
    return None
