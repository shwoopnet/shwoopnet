"""GEN6 (workers/GEN6_REGISTRATION.md): a generator of LATE-window underdog strategies on KXBTC15M and KXGOLD15M.
Entry at the candle ending 240, 180, 120 or 60 s before the close, the side priced 5c to 50c, 1 to 3 conditions, 51 exits.
Research only; nothing here places an order, reads a key or decides anything live.
    python -m scalper.gen6 discovery <btc|gold>    (build discovery rows, generate, dedupe, screen, write the frozen survivor file)
    python -m scalper.gen6 validate <btc|gold>     (once, after the frozen files are committed: build validation rows, score)
    python -m scalper.gen6 parity <btc|gold>       (forward_eval against the history scorer on validation windows)
forward_eval(window, params) is the forward-ledger evaluator (workers/candidates/README.md).
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from .paths import DATA_DIR

MARKETS = {"btc": "KXBTC15M", "gold": "KXGOLD15M"}
PEERS = {"KXBTC15M": ("KXETH15M", "KXGOLD15M"), "KXGOLD15M": ("KXBTC15M", "KXETH15M")}
FILES = ("l1b", "book", "fresh", "five")


def _ts(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


DISC = (_ts(2026, 8, 6), _ts(2026, 9, 21))
VAL = {"KXBTC15M": (_ts(2026, 9, 21), _ts(2026, 10, 28)), "KXGOLD15M": (_ts(2026, 9, 21), _ts(2026, 10, 30))}
LOOKS = (240, 180, 120, 60)
RANGES = [(a, b) for a in LOOKS for b in LOOKS if b <= a]
LO_ASK, HI_ASK = 0.05, 0.50
TPS = (0.03, 0.05, 0.08, 0.12, 0.20, 0.30)
STOPS = (None, 0.05, 0.10, 0.20)
EXITS = [("hold",), ("time", 120), ("time", 60)] + [("tp", i, j, fb) for i in range(len(TPS)) for j in range(len(STOPS)) for fb in ("hold", "t60")]
FEATS = ["ask", "bid", "spread", "d1", "d2", "d3", "d5", "rng5", "vol", "doi", "hour", "xa_d2", "xa_mid", "xb_d2", "xb_mid",
         "m1", "m3", "m5", "wrng", "wgap", "xa_spr", "xb_spr"]
SEED = 6
TARGET, MAX_DRAWS, MIN_TRADES = 5000, 300_000, 30
N_PRIOR = 501_174


def fee(p, c, m=1.0):
    return math.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def vfee(p, c, m=1.0):
    p = np.asarray(p, dtype=np.float64)
    return np.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def exit_allowed(e, L_lo):
    k = EXITS[e]
    if k[0] == "hold":
        return True
    if k[0] == "time":
        return k[1] < L_lo - 60
    return L_lo >= 180


def exit_near(a, b):
    x, y = EXITS[a], EXITS[b]
    if x[0] != y[0]:
        return False
    if x[0] == "hold":
        return True
    if x[0] == "time":
        return True  # only two time exits; they are adjacent
    return abs(x[1] - y[1]) <= 1 and abs(x[2] - y[2]) <= 1 and x[3] == y[3]


def _sq(q, yes):
    """(bid, ask, mid) of the side from a candle (bid_c, ask_c, vol, oi)."""
    if yes:
        return q[0], q[1], (q[0] + q[1]) / 2
    return round(1 - q[1], 4), round(1 - q[0], 4), 1 - (q[0] + q[1]) / 2


def window_rows(series, close_ts, cs, peers):
    """Every (look, side) row of one window, in entry order (240 s first, YES before NO). Shared by history and forward.
    Each row: dict(L, yes, feats (np array, NaN = missing), fill, sig_ask, zv_entry, exits = [(bid or None, zv)] per exit,
    missing = True if the signal candle was absent (no row) is reported separately via the 'gaps' list."""
    rows, gaps = [], []
    pa = peers.get(PEERS[series][0]); pb = peers.get(PEERS[series][1])
    start = close_ts - 900
    wkeys = sorted(k for k in cs if start < k <= close_ts - 60)
    for L in LOOKS:
        t = close_ts - L
        q = cs.get(t)
        if q is None:
            gaps.append(L); continue
        if L > 60:
            nq = cs.get(t + 60)
            fill_t = t + 60
        else:
            nq, fill_t = None, t
        scan = [k for k in wkeys if k > fill_t]
        hour = datetime.fromtimestamp(t, timezone.utc).hour
        oi3 = cs.get(t - 180)
        doi = (q[3] - oi3[3]) if oi3 is not None else np.nan
        for yes in (1, 0):
            bid, ask, mid = _sq(q, yes)
            if not (LO_ASK - 1e-9 <= ask <= HI_ASK + 1e-9):
                continue
            if L > 60:
                if nq is None:
                    gaps.append(L); continue
                fill = _sq(nq, yes)[1]
            else:
                fill = min(round(ask + 0.02, 4), 0.99)
            sgn = 1 if yes else -1

            def dlag(lag, i):
                p = cs.get(t - lag)
                if p is None:
                    return np.nan
                return (bid - _sq(p, yes)[0]) if i == 0 else (mid - _sq(p, yes)[2])

            marks = [cs.get(t - 60 * j) for j in range(6)]
            rng5 = (max(_sq(m, yes)[0] for m in marks) - min(_sq(m, yes)[0] for m in marks)) if all(m is not None for m in marks) else np.nan
            wm = [_sq(cs[k], yes)[2] for k in wkeys if k <= t]
            wrng = (max(wm) - min(wm)) if wm else np.nan
            wgap = (mid - max(wm)) if wm else np.nan
            px = []
            for P in (pa, pb):
                a = P.get(t) if P else None
                b = P.get(t - 120) if P else None
                if a is None:
                    px += [np.nan, np.nan, np.nan]; continue
                ma = (a[0] + a[1]) / 2
                px += [sgn * (ma - (b[0] + b[1]) / 2) if b is not None else np.nan, ma, a[1] - a[0]]
            f = np.array([ask, bid, q[1] - q[0], dlag(60, 0), dlag(120, 0), dlag(180, 0), dlag(300, 0), rng5, q[2], doi, hour,
                          px[0], px[1], px[3], px[4], dlag(60, 1), dlag(180, 1), dlag(300, 1), wrng, wgap, px[2], px[5]], dtype=np.float64)
            bids = [(k, _sq(cs[k], yes)[0], cs[k][2] <= 0) for k in scan]
            ex = []
            for e in EXITS:
                ex.append(_exit(e, bids, fill, close_ts, L))
            rows.append({"L": L, "yes": yes, "t": t, "feats": f, "fill": fill, "sig_ask": ask, "zv_entry": q[2] <= 0, "exits": ex})
    return rows, gaps


def _exit(e, bids, fill, close_ts, L):
    """(exit bid or None = held, zero-volume flag, exit end_ts or None). A bid of 0 is not a sale (held, scan continues)."""
    if e[0] == "hold" or not bids:
        return (None, False, None)
    if e[0] == "time":
        for k, b, z in bids:
            if k >= close_ts - e[1] and b > 0:
                return (b, z, k)
        return (None, False, None)
    tp, st, fb = TPS[e[1]], STOPS[e[2]], e[3]
    for k, b, z in bids:
        if b <= 0:
            continue
        if b >= fill + tp - 1e-9 or (st is not None and b <= fill - st + 1e-9):
            return (b, z, k)
    if fb == "t60":
        for k, b, z in bids:
            if k == close_ts - 60 and b > 0:
                return (b, z, k)
    return (None, False, None)


# ---------------------------------------------------------------- history

def load_windows(series, lo, hi):
    want = (series,) + PEERS[series]
    seen, M = set(), {}
    allc = {}
    for name in FILES:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        q = ",".join("?" * len(want))
        mk = db.execute(f"select ticker, series, close_ts, result from market where series in ({q}) and close_ts >= ? and close_ts < ?",
                        (*want, lo, hi)).fetchall()
        for tk, se, ct, res in mk:
            if tk in seen:
                continue
            cs = {r[0]: (r[1], r[2], r[3] or 0.0, r[4] or 0.0) for r in db.execute(
                "select end_ts, bid_c, ask_c, volume, oi from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if not cs:
                continue
            seen.add(tk)
            allc[(se, ct)] = cs
            if se == series and res in ("yes", "no"):
                M[tk] = (ct, res, cs)
    out = []
    for tk, (ct, res, cs) in sorted(M.items(), key=lambda x: x[1][0]):
        peers = {o: allc[(o, ct)] for o in PEERS[series] if (o, ct) in allc}
        out.append((tk, ct, res, cs, peers))
    return out


def build(series, lo, hi):
    W = load_windows(series, lo, hi)
    X, meta, EB, EZ = [], [], [], []
    for wid, (tk, ct, res, cs, peers) in enumerate(W):
        rows, _ = window_rows(series, ct, cs, peers)
        day = datetime.fromtimestamp(ct, timezone.utc).strftime("%Y-%m-%d")
        for r in rows:
            win = 1.0 if (res == "yes") == bool(r["yes"]) else 0.0
            X.append(r["feats"]); meta.append((wid, day, r["L"], r["yes"], r["fill"], r["sig_ask"], r["zv_entry"], win, ct))
            EB.append([np.nan if b is None else b for b, z, k in r["exits"]]); EZ.append([z for b, z, k in r["exits"]])
    days = sorted({m[1] for m in meta})
    D = {"X": np.array(X).reshape(-1, len(FEATS)), "wid": np.array([m[0] for m in meta]), "day": np.array([days.index(m[1]) for m in meta]),
         "L": np.array([m[2] for m in meta]), "yes": np.array([m[3] for m in meta]), "fill": np.array([m[4] for m in meta]),
         "sig": np.array([m[5] for m in meta]), "zve": np.array([m[6] for m in meta]), "win": np.array([m[7] for m in meta]),
         "close": np.array([m[8] for m in meta]), "EB": np.array(EB), "EZ": np.array(EZ), "days": days, "nwin": len(W),
         "tickers": [w[0] for w in W]}
    return D, W


def nets(D, idx, e, c=10, m=1.0, sig=False):
    a = (D["sig"] if sig else D["fill"])[idx]
    b = D["EB"][idx, e]
    held = np.isnan(b)
    out = np.where(held, D["win"][idx] - a - vfee(a, c, m), np.nan_to_num(b) - a - vfee(a, c, m) - vfee(np.nan_to_num(b), c, m))
    return out


def pf(v):
    w = float(v[v > 0].sum()); l = float(-v[v < 0].sum())
    return w / l if l > 0 else (99.0 if w > 0 else 0.0)


def trades(D, s):
    m = (D["L"] <= s["L_hi"]) & (D["L"] >= s["L_lo"])
    if s["side"] != "both":
        m &= D["yes"] == (1 if s["side"] == "yes" else 0)
    for f, op, th in s["conds"]:
        col = D["X"][:, FEATS.index(f)]
        with np.errstate(invalid="ignore"):
            m &= (col <= th) if op == "le" else (col > th)   # NaN compares False: a missing feature fails its condition
    idx = np.flatnonzero(m)
    if len(idx) == 0:
        return idx
    w = D["wid"][idx]
    return idx[np.r_[True, w[1:] != w[:-1]]]


def score(D, idx, e):
    v = nets(D, idx, e)
    zv = (D["zve"][idx] | D["EZ"][idx, e]) if len(idx) else np.array([])
    days = D["day"][idx]
    out = {"n": int(len(idx)), "days": int(len(set(days.tolist()))), "pf": pf(v), "pf1": pf(nets(D, idx, e, c=1)),
           "pfs": pf(nets(D, idx, e, m=1.2)), "pf_sig": pf(nets(D, idx, e, sig=True)), "zv": float(zv.mean()) if len(idx) else 1.0,
           "mean": float(v.mean()) if len(v) else 0.0, "win": float(D["win"][idx].mean()) if len(idx) else 0.0,
           "ask": float(D["fill"][idx].mean()) if len(idx) else 0.0}
    if len(idx) and zv.any():
        out["pf_nozv"] = pf(v[~zv])
    else:
        out["pf_nozv"] = out["pf"]
    if len(idx) > 1:
        from .calibration import cluster_mean_z
        out["z"] = cluster_mean_z(list(zip(days.tolist(), v.tolist())))[2]
    else:
        out["z"] = 0.0
    return out


def _order(D):
    o = np.lexsort((-D["yes"], -D["L"], D["wid"]))
    for k in ("X", "wid", "day", "L", "yes", "fill", "sig", "zve", "win", "close", "EB", "EZ"):
        D[k] = D[k][o]
    return D


def ref_sets(W, series):
    """Discovery window ids of REV1's rule (Bitcoin NO ask in (0.03, 0.45) at 180 then 120 s) and of REF_*_UNDERDOG_180."""
    rev, ref = set(), set()
    for wid, (tk, ct, res, cs, peers) in enumerate(W):
        for L in (180, 120):
            q = cs.get(ct - L)
            if q is not None and 0.03 < round(1 - q[0], 4) < 0.45:
                rev.add(wid); break
        q = cs.get(ct - 180)
        if q is not None and any(0.15 - 1e-9 <= _sq(q, y)[1] <= 0.49 + 1e-9 for y in (1, 0)):
            ref.add(wid)
    return (rev if series == "KXBTC15M" else set()), ref


def draw(rng, Q):
    L_hi, L_lo = rng.choice(RANGES)
    s = {"L_hi": L_hi, "L_lo": L_lo, "side": rng.choice(["yes", "no", "both"]), "conds": [], "e": rng.randrange(len(EXITS))}
    used = set()
    for _ in range(rng.randint(1, 3)):
        f = rng.choice([g for g in FEATS if g not in used]); used.add(f)
        s["conds"].append((f, rng.choice(["le", "gt"]), float(Q[f][rng.choice(range(10, 91, 10))])))
    return s


def desc(s):
    e = EXITS[s["e"]]
    ex = "hold" if e[0] == "hold" else (f"sell at {e[1]}s" if e[0] == "time" else
                                          f"TP +{int(TPS[e[1]] * 100)}c stop {'none' if STOPS[e[2]] is None else '-' + str(int(STOPS[e[2]] * 100)) + 'c'} else {'hold' if e[3] == 'hold' else 'sell 60s'}")
    cond = " & ".join(f"{f}{'<=' if op == 'le' else '>'}{th:.3g}" for f, op, th in s["conds"])
    return f"[{s['side']} {s['L_hi']}..{s['L_lo']}s | {cond} | {ex}]"


def discovery(key):
    series = MARKETS[key]
    D, W = build(series, *DISC)
    D = _order(D)
    print(series, "discovery windows", D["nwin"], "rows", len(D["wid"]), "days", len(D["days"]), flush=True)
    if D["nwin"] < 1000:
        print("NOT_ENOUGH_DATA"); return
    Q = {f: np.nanpercentile(D["X"][:, i], list(range(101))) for i, f in enumerate(FEATS)}
    rev, ref = ref_sets(W, series)
    nw = D["nwin"]
    rng = random.Random(SEED * 1000 + (1 if key == "btc" else 2))
    K = np.zeros((TARGET, nw), dtype=np.float32); ksz = np.zeros(TARGET); kexit = []
    kept = []
    gen = rej_exit = rej_small = rej_ref = rej_dup = 0
    while len(kept) < TARGET and gen < MAX_DRAWS:
        s = draw(rng, Q); gen += 1
        if not exit_allowed(s["e"], s["L_lo"]):
            rej_exit += 1; continue
        idx = trades(D, s)
        if len(idx) < MIN_TRADES:
            rej_small += 1; continue
        ws = set(D["wid"][idx].tolist())
        if EXITS[s["e"]][0] == "hold" and any(R and len(ws & R) / len(ws | R) > 0.5 for R in (rev, ref)):
            rej_ref += 1; continue
        v = np.zeros(nw, dtype=np.float32); v[list(ws)] = 1
        k = len(kept)
        if k:
            near = np.array([exit_near(s["e"], x) for x in kexit])
            if near.any():
                inter = K[:k][near] @ v
                jac = inter / (ksz[:k][near] + len(ws) - inter)
                if (jac > 0.5).any():
                    rej_dup += 1; continue
        K[k] = v; ksz[k] = len(ws); kexit.append(s["e"])
        kept.append((s, score(D, idx, s["e"])))
        if len(kept) % 500 == 0:
            print("distinct", len(kept), "generated", gen, flush=True)
    surv = [{"strategy": s, "disc": sc} for s, sc in kept if sc["pf"] >= 1.5 and sc["n"] >= 100 and sc["days"] >= 15 and sc["zv"] <= 0.2]
    ctrl = [{"strategy": s, "disc": sc} for s, sc in kept if sc["n"] >= 100 and sc["days"] >= 15 and not (sc["pf"] >= 1.5 and sc["zv"] <= 0.2)]
    pfs = np.array([sc["pf"] for _, sc in kept])
    big = np.array([sc["pf"] for _, sc in kept if sc["n"] >= 100 and sc["days"] >= 15])
    info = {"series": series, "generated": gen, "distinct": len(kept), "rejected": {"exit_not_allowed": rej_exit, "under_30_trades": rej_small,
            "rev1_or_ref_duplicate": rej_ref, "duplicate": rej_dup}, "disc_windows": nw, "disc_rows": int(len(D["wid"])), "disc_days": len(D["days"]),
            "pf_median": float(np.median(pfs)), "pf_p95": float(np.percentile(pfs, 95)), "at_size": int(len(big)),
            "best_at_size": float(big.max()) if len(big) else 0.0, "survivors_n": len(surv), "controls_n": len(ctrl),
            "frozen_at": datetime.now(timezone.utc).isoformat()}
    (DATA_DIR / f"gen6_{key}_distinct.json").write_text(json.dumps({"info": info, "distinct": [{"strategy": s, "disc": sc} for s, sc in kept]}))
    (DATA_DIR / f"gen6_{key}_controls.json").write_text(json.dumps({"info": info, "controls": ctrl}))
    fz = json.dumps({"info": info, "survivors": surv}, indent=1)
    (DATA_DIR / f"gen6_{key}_frozen.json").write_text(fz)
    print(json.dumps(info, indent=1))
    for r in sorted(surv, key=lambda r: -r["disc"]["pf"])[:15]:
        print(desc(r["strategy"]), {k: round(v, 3) for k, v in r["disc"].items()})
    for name in ("frozen", "controls"):
        print(name, hashlib.sha256((DATA_DIR / f"gen6_{key}_{name}.json").read_bytes()).hexdigest())


def _vpass(vs):
    return vs["pf"] >= 1.3 and vs["n"] >= 50 and vs["pfs"] > 1.0 and vs["zv"] <= 0.2


def validate(key):
    series = MARKETS[key]
    out = DATA_DIR / f"gen6_{key}_validation.json"
    if out.exists():
        print("Refusing to run again: validation already read"); return
    fz = json.loads((DATA_DIR / f"gen6_{key}_frozen.json").read_text())
    ct = json.loads((DATA_DIR / f"gen6_{key}_controls.json").read_text())
    D, W = build(series, *VAL[series])
    D = _order(D)
    print(series, "validation windows", D["nwin"], "rows", len(D["wid"]), "days", len(D["days"]), flush=True)
    res = {"windows": D["nwin"], "days": len(D["days"]), "survivors": [], "controls_pass": 0, "controls_n": len(ct["controls"])}
    for r in fz["survivors"]:
        s = r["strategy"]; s["conds"] = [tuple(c) for c in s["conds"]]
        idx = trades(D, s); vs = score(D, idx, s["e"])
        res["survivors"].append({"strategy": s, "disc": r["disc"], "valid": vs, "pass": _vpass(vs),
                                 "entries": [D["tickers"][w] for w in D["wid"][idx].tolist()]})
    cpass = []
    for r in ct["controls"]:
        s = r["strategy"]; s["conds"] = [tuple(c) for c in s["conds"]]
        vs = score(D, trades(D, s), s["e"])
        if _vpass(vs):
            res["controls_pass"] += 1
        cpass.append({"strategy": s, "disc": r["disc"], "valid": vs})
    # base cores (information): same look range, side and exit, no conditions, on both stages
    out.write_text(json.dumps(res))
    (DATA_DIR / f"gen6_{key}_controls_validation.json").write_text(json.dumps(cpass))
    sp = sum(r["pass"] for r in res["survivors"])
    print("survivors", len(res["survivors"]), "pass", sp, "controls", res["controls_n"], "pass", res["controls_pass"])


# ---------------------------------------------------------------- forward

def forward_eval(window, params):
    """One frozen GEN6 strategy (params["strategy"]) on one window (source "candles"). Same rows and selection as the history."""
    from .fwdeval import NoData
    s = params.get("strategy", params)
    series = window["series"]
    if series not in PEERS or series != params.get("series", series):
        return None
    conds = [tuple(c) for c in s["conds"]]
    rows, gaps = window_rows(series, window["close_ts"], window["candles"], window.get("peers", {}))
    missing = False
    for r in rows:
        if not (s["L_lo"] <= r["L"] <= s["L_hi"]):
            continue
        if s["side"] != "both" and r["yes"] != (1 if s["side"] == "yes" else 0):
            continue
        ok = True
        for f, op, th in conds:
            v = r["feats"][FEATS.index(f)]
            if np.isnan(v):
                missing = True; ok = False; break
            if not ((v <= th) if op == "le" else (v > th)):
                ok = False; break
        if not ok:
            continue
        b, z, k = r["exits"][s["e"]]
        return {"side": "yes" if r["yes"] else "no", "entry": float(r["fill"]), "exit": None if b is None else float(b),
                "t": int(r["t"] + (60 if r["L"] > 60 else 0)), "zero_volume": bool(r["zv_entry"] or z),
                "note": f"look {r['L']}s, signal ask {r['sig_ask']:.2f}" + ("" if k is None else f", exit at {window['close_ts'] - k}s left")}
    if missing or any(s["L_lo"] <= L <= s["L_hi"] for L in gaps):
        raise NoData("a candle or feature input the rule needs is missing")
    return None


def parity(key):
    """forward_eval against trades()/nets() on the validation windows for every validation survivor."""
    series = MARKETS[key]
    D, W = build(series, *VAL[series]); D = _order(D)
    res = json.loads((DATA_DIR / f"gen6_{key}_validation.json").read_text())
    from .fwdeval import NoData
    from .fwdledger import net_per_contract
    bad = checked = 0
    for r in res["survivors"]:
        if not r["pass"]:
            continue
        s = r["strategy"]; s["conds"] = [tuple(c) for c in s["conds"]]
        idx = trades(D, s); hv = nets(D, idx, s["e"])
        hist = {int(D["wid"][i]): float(v) for i, v in zip(idx, hv)}
        for wid, (tk, ct, rs, cs, peers) in enumerate(W):
            try:
                tr = forward_eval({"series": series, "close_ts": ct, "candles": cs, "peers": peers}, {"strategy": s})
            except NoData:
                tr = "nodata"
            checked += 1
            if tr == "nodata":
                if wid in hist:
                    bad += 1
                continue
            if tr is None:
                bad += wid in hist; continue
            fv = net_per_contract(tr, rs, 10)
            if wid not in hist or abs(fv - hist[wid]) > 1e-6:
                bad += 1
    print("parity windows checked", checked, "mismatches", bad)


if __name__ == "__main__":
    cmd, key = sys.argv[1], sys.argv[2]
    {"discovery": discovery, "validate": validate, "parity": parity}[cmd](key)
