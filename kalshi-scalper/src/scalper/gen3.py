"""GEN3 (README, Pre-registration: GEN3): generator on the hourly Bitcoin ladder (KXBTCD), single-strike scalps and adjacent-strike
bracket spreads, all exited before the close. Research only; nothing here places an order.
    python -m scalper.gen3 build     (discovery and validation days only; the holdout days are not built)
    python -m scalper.gen3 search
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from . import auto3
from .calibration import cluster_mean_z
from .gen1 import boot_pf5, pf, _norm_ppf
from .paths import DATA_DIR
from .scalp12 import sigma1

DB = DATA_DIR / "lad1.sqlite"
NPZ = DATA_DIR / "gen3_rows.npz"
RESULT = DATA_DIR / "gen3_result.txt"
FROZEN = DATA_DIR / "gen3_survivors.json"
DISC_D, VAL_D = 15, 23
LEFTS = list(range(3300, 179, -60))
TP = (0.03, 0.05, 0.08, 0.12, 0.20, None)
ST = (None, 0.05, 0.10, 0.20)
TE = (60, 120, 300, 600)
BK = ("none", "spread3")
EXITS = [("fixed", a, b, c, d) for a in TP for b in ST for c in TE for d in BK] + [("trail", t, None, c, None) for t in (0.05, 0.10, 0.15) for c in TE]
FEATS = ["kind", "yes", "left", "ask", "bid", "spread", "d1", "d2", "d5", "rng5", "vol", "doi", "z", "r3", "tb1", "tb5", "slope", "hour", "dow"]
GRAMMAR = [f for f in FEATS if f not in ("kind", "yes", "left")]
N_PRIOR = 425_360
TARGET, MIN_DISC = 5000, 30


def vfee(p, c=10, m=1.0):
    p = np.asarray(p, dtype=np.float64)
    return np.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def exit_idx(val, spr, ks, e, close_ts):
    tp = np.array([np.inf if (x[0] == "trail" or x[1] is None) else x[1] for x in EXITS])[:, None]
    st = np.array([np.inf if (x[0] == "trail" or x[2] is None) else x[2] for x in EXITS])[:, None]
    tr = np.array([x[1] if x[0] == "trail" else np.inf for x in EXITS])[:, None]
    te = np.array([x[3] for x in EXITS])[:, None]
    bk = np.array([1 if (x[0] == "fixed" and x[4] == "spread3") else 0 for x in EXITS])[:, None]
    V, S, K = val[None, :], spr[None, :], ks[None, :]
    peak = np.maximum.accumulate(np.r_[e, val])[1:][None, :]
    hit = (V >= e + tp - 1e-9) | (V <= e - st + 1e-9) | (V <= peak - tr + 1e-9) | (K >= close_ts - te) | ((bk == 1) & (S >= 0.03 - 1e-9))
    hit[:, -1] = True
    return hit.argmax(axis=1)


def build(holdout=False):
    db = sqlite3.connect(DB)
    mk = defaultdict(list)
    for tk, close, strike, res in db.execute("select ticker, close_ts, strike, result from market"):
        mk[close].append((strike, tk))
    cd = defaultdict(dict)
    for tk, e, b, a, v, oi in db.execute("select ticker, end_ts, bid_c, ask_c, volume, oi from candle where bid_c is not null and ask_c is not null"):
        cd[tk][e] = (b, a, v or 0.0, oi or 0.0)
    spot = {ts // 1000: c for cur, ts, c in sqlite3.connect(DATA_DIR / "search5k.sqlite").execute("select cur, ts, c from bar where cur='BTC'")}
    spot2 = {("BTC", k): v for k, v in spot.items()}
    auto3.FUT = auto3.fut_load()
    days = sorted({datetime.fromtimestamp(c, timezone.utc).strftime("%Y-%m-%d") for c in mk})
    didx = {d: i for i, d in enumerate(days)}
    X, W, DY, CL, XB1, XB2, ZV, EL = [], [], [], [], [], [], [], []
    wid = 0
    for close in sorted(mk):
        day = didx[datetime.fromtimestamp(close, timezone.utc).strftime("%Y-%m-%d")]
        if (day >= VAL_D) != holdout:
            continue  # holdout days are built only by `holdout`, after the survivors are frozen
        ladder = sorted(mk[close])
        legs = [(i, None) for i in range(len(ladder))] + [(i, i + 1) for i in range(len(ladder) - 1)]
        for lo, hi in legs:
            wid += 1
            ka, kb = ladder[lo][1], (ladder[hi][1] if hi is not None else None)
            ca, cb = cd.get(ka, {}), (cd.get(kb, {}) if kb else None)
            for L in LEFTS:
                t = close - L
                qa = ca.get(t); qb = cb.get(t) if cb is not None else None
                if qa is None or (cb is not None and qb is None):
                    continue
                later = [k for k in sorted(ca) if t < k <= close - 60 and (cb is None or k in cb)]
                if not later:
                    continue
                s = spot.get(t - 60); sg = sigma1(spot2, "BTC", t)
                z0 = math.log(s / ladder[lo][0]) / (sg * math.sqrt(L / 60)) if (s and sg) else 0.0
                s3 = spot.get(t - 240); r3 = math.log(s / s3) if (s and s3) else 0.0
                below = cd.get(ladder[lo - 1][1], {}).get(t) if lo > 0 else None
                above = cd.get(ladder[(hi if hi is not None else lo) + 1][1], {}).get(t) if (hi if hi is not None else lo) + 1 < len(ladder) else None
                slope = (((below[0] + below[1]) / 2) - ((above[0] + above[1]) / 2)) if (below and above) else 0.0
                dt_ = datetime.fromtimestamp(t, timezone.utc)
                sides = ((1,), (0,)) if cb is None else ((2,),)
                for (yes,) in sides:
                    def val_at(k):
                        a = ca[k]
                        if yes == 1: return a[0], a[1]
                        if yes == 0: return 1 - a[1], 1 - a[0]
                        b = cb[k]
                        return a[0] + (1 - b[1]), a[1] + (1 - b[0])  # bracket: (sell value, buy cost)
                    bid, ask = val_at(t)
                    if not (0.03 <= ask <= (0.85 if yes != 2 else 1.6)):
                        continue
                    ds = []
                    for lag in (60, 120, 300):
                        ok = (t - lag) in ca and (cb is None or (t - lag) in cb)
                        ds.append(bid - val_at(t - lag)[0] if ok else 0.0)
                    path = [val_at(t - 60 * j)[0] for j in range(6) if (t - 60 * j) in ca and (cb is None or (t - 60 * j) in cb)]
                    sgn = -1 if yes == 0 else 1
                    fl = auto3.flow("BTC", t, sgn)
                    vals = np.array([val_at(k)[0] for k in later]); asks = np.array([val_at(k)[1] for k in later])
                    ks = np.array(later)
                    i1 = exit_idx(vals, asks - vals, ks, ask, close)
                    if yes == 2:
                        x1 = np.array([ca[later[i]][0] for i in i1]); x2 = np.array([1 - cb[later[i]][1] for i in i1])
                    else:
                        x1 = vals[i1]; x2 = np.full(len(i1), np.nan)
                    zv = np.array([ca[later[i]][2] <= 0 for i in i1]) | (qa[2] <= 0)
                    X.append([yes, yes, L, ask, bid, ask - bid, ds[0], ds[1], ds[2], (max(path) - min(path)) if path else 0.0, qa[2],
                              (qa[3] - ca[t - 180][3]) if (t - 180) in ca else 0.0, sgn * z0, sgn * r3, fl[0], fl[1], sgn * slope, dt_.hour, dt_.weekday()])
                    W.append(wid); DY.append(day); CL.append(close); XB1.append(x1); XB2.append(x2); ZV.append(zv)
                    EL.append((qa[1], 1 - qb[0]) if yes == 2 else (ask, np.nan))
    X = np.array(X, dtype=np.float32); W = np.array(W); DY = np.array(DY)
    order = np.lexsort((-X[:, 2], W))
    np.savez(DATA_DIR / "gen3_hold_rows.npz" if holdout else NPZ, X=X[order], W=W[order], day=DY[order], close=np.array(CL)[order], XB1=np.array(XB1, dtype=np.float32)[order],
             XB2=np.array(XB2, dtype=np.float32)[order], ZV=np.array(ZV, dtype=bool)[order], EL=np.array(EL, dtype=np.float64)[order])
    print("rows", len(X), "windows", wid, "days built", len(set(DY.tolist())), flush=True)


def load():
    z = np.load(NPZ)
    return {k: z[k] for k in z.files}


def nets(D, idx, ex, c=10, m=1.0):
    X = D["X"]; ask = X[idx, 3].astype(np.float64)
    x1 = D["XB1"][idx, ex].astype(np.float64); x2 = D["XB2"][idx, ex].astype(np.float64)
    single = np.isnan(x2)
    e1, e2 = D["EL"][idx, 0], D["EL"][idx, 1]
    ef = np.where(single, vfee(ask, c, m), vfee(e1, c, m) + vfee(np.nan_to_num(e2), c, m))
    xf = np.where(single, vfee(x1, c, m), vfee(np.nan_to_num(x1), c, m) + vfee(np.nan_to_num(x2), c, m))
    val = np.where(single, x1, np.nan_to_num(x1) + np.nan_to_num(x2))
    return val - ask - ef - xf, D["ZV"][idx, ex]


def mask(D, s, split):
    X = D["X"]
    m = split & (X[:, 2] <= s["L_hi"]) & (X[:, 2] >= s["L_lo"])
    m &= (X[:, 0] == 2) if s["kind"] == "bracket" else (X[:, 0] == (1 if s["side"] == "yes" else 0)) if s["side"] != "both" else (X[:, 0] < 2)
    for f, op, th in s["conds"]:
        col = X[:, FEATS.index(f)]
        m &= (col <= th) if op == "le" else (col > th)
    return m


def evaluate(D, s, split, c=10, m=1.0):
    idx = np.flatnonzero(mask(D, s, split))
    if len(idx):
        w = D["W"][idx]; idx = idx[np.r_[True, w[1:] != w[:-1]]]
    n, zv = nets(D, idx, s["ex"], c, m)
    return n, D["day"][idx], D["W"][idx], D["close"][idx], (float(zv.mean()) if len(idx) else 1.0)


def stats(net, days, closes):
    if len(net) == 0:
        return {"n": 0, "days": 0, "closes": 0, "pf": 0.0, "z": 0.0, "mean_c": 0.0}
    _, _, z = cluster_mean_z(list(zip(days.tolist(), net.tolist()))) if len(net) > 1 else (0, 0, 0.0)
    return {"n": int(len(net)), "days": int(len(set(days.tolist()))), "closes": int(len(set(closes.tolist()))), "pf": pf(net), "z": float(z), "mean_c": float(100 * net.mean())}


def draw(rng, Q):
    kind = rng.choice(["single", "single", "bracket"])
    width = rng.choice(range(60, 1801, 60)); L_hi = rng.choice([L for L in LEFTS if L - width >= 180])
    s = {"kind": kind, "side": rng.choice(["yes", "no", "both"]) if kind == "single" else "pair", "L_hi": L_hi, "L_lo": L_hi - width, "conds": [], "ex": rng.randrange(len(EXITS))}
    used = set()
    for _ in range(rng.randint(1, 4)):
        f = rng.choice([g for g in GRAMMAR if g not in used]); used.add(f)
        q = Q["bracket" if kind == "bracket" else "single"][f]
        s["conds"].append((f, rng.choice(["le", "gt"]), float(q[rng.choice(range(10, 91, 10))])))
    return s


def near(a, b):
    ea, eb = EXITS[a["ex"]], EXITS[b["ex"]]
    if a["kind"] != b["kind"] or ea[0] != eb[0]:
        return False
    if ea[0] == "fixed":
        return all(abs(sq.index(x) - sq.index(y)) <= 1 for sq, x, y in ((TP, ea[1], eb[1]), (ST, ea[2], eb[2]), (TE, ea[3], eb[3]))) and ea[4] == eb[4]
    return abs(ea[1] - eb[1]) <= 0.051 and abs(TE.index(ea[3]) - TE.index(eb[3])) <= 1


def desc(s):
    e = EXITS[s["ex"]]
    ex = f"TP {e[1]} stop {e[2]} time {e[3]}s book {e[4]}" if e[0] == "fixed" else f"trail {e[1]} time {e[3]}s"
    return f"[{s['kind']} {s['side']} {s['L_hi']}..{s['L_lo']}s | " + " & ".join(f"{f}{'<=' if op == 'le' else '>'}{th:.3g}" for f, op, th in s["conds"]) + f" | {ex}]"


def search():
    D = load(); X = D["X"]
    disc = D["day"] < DISC_D; val = (D["day"] >= DISC_D) & (D["day"] < VAL_D)
    Q = {k: {f: np.percentile(X[disc & sel][:, FEATS.index(f)], list(range(0, 101))) for f in GRAMMAR} for k, sel in (("single", X[:, 0] < 2), ("bracket", X[:, 0] == 2))}
    rng = random.Random(20261031)
    distinct, gen = [], 0
    while len(distinct) < TARGET and gen < 300_000:
        s = draw(rng, Q); gen += 1
        net, days, ws, cl, zv = evaluate(D, s, disc)
        if len(net) < MIN_DISC:
            continue
        wset = set(ws.tolist())
        if any(near(s, s2) and len(wset & w2) / len(wset | w2) > 0.5 for s2, w2, _ in distinct):
            continue
        st = stats(net, days, cl); st["zv"] = zv
        distinct.append((s, wset, st))
        if len(distinct) % 500 == 0:
            print("distinct", len(distinct), "generated", gen, flush=True)
    N = N_PRIOR + gen; zbar = _norm_ppf(1 - 0.05 / N)
    rows = []
    for s, w, d in distinct:
        fail = None
        if d["pf"] < 1.5: fail = "DISCOVERY_PF"
        elif d["n"] < 150 or d["days"] < 10: fail = "DISCOVERY_N"
        elif d["zv"] > 0.2: fail = "FILL_OPTIMISM"
        v = b5 = None
        if fail is None:
            net, days, _, cl, zv = evaluate(D, s, val); v = stats(net, days, cl)
            v["pfs"] = pf(evaluate(D, s, val, m=1.2)[0]); v["pf1"] = pf(evaluate(D, s, val, c=1)[0])
            if v["n"] < 60 or v["days"] < 6: fail = "VALIDATION_N"
            elif v["pf"] < 1.5: fail = "VALIDATION_PF"
            elif v["pfs"] < 1.2: fail = "VALIDATION_STRESS"
            elif zv > 0.2: fail = "FILL_OPTIMISM"
            else:
                b5 = boot_pf5(net, days)
                if b5 <= 1.0: fail = "VALIDATION_BOOTSTRAP"
                elif v["z"] < zbar: fail = "DEFLATION"
        rows.append({"s": s, "disc": d, "valid": v, "boot5": b5, "fail": fail})
    dp = [r for r in rows if r["valid"] is not None]; full = [r for r in rows if r["fail"] is None]
    pfs = np.array([r["disc"]["pf"] for r in rows]); big = [r for r in rows if r["disc"]["n"] >= 150]
    lines = [f"GEN3: generated {gen}, distinct {len(distinct)} (singles {sum(1 for r in rows if r['s']['kind'] == 'single')}, brackets {sum(1 for r in rows if r['s']['kind'] == 'bracket')}); N tried {N}, Bonferroni z bar {zbar:.2f}",
             f"discovery PF over distinct: median {np.median(pfs):.2f}, 95th pct {np.percentile(pfs, 95):.2f}; best with 150+ trades {max((r['disc']['pf'] for r in big), default=0):.2f}",
             f"passed discovery {len(dp)}; failed in validation: " + ", ".join(f"{k} {sum(1 for r in dp if r['fail'] == k)}" for k in ("VALIDATION_N", "VALIDATION_PF", "VALIDATION_STRESS", "FILL_OPTIMISM", "VALIDATION_BOOTSTRAP", "DEFLATION")) + f"; survivors {len(full)}"]
    order = {None: 9, "DEFLATION": 8, "VALIDATION_BOOTSTRAP": 7, "VALIDATION_STRESS": 6, "VALIDATION_PF": 5, "FILL_OPTIMISM": 4, "VALIDATION_N": 3}
    best = sorted(dp, key=lambda r: (order.get(r["fail"], 0), r["valid"]["pf"]), reverse=True) + sorted([r for r in big if r["valid"] is None], key=lambda r: -r["disc"]["pf"])
    top = []
    for r in best[:5]:
        s = r["s"]; info = r["valid"] is None
        if info:
            net, days, _, cl, _ = evaluate(D, s, val); v = stats(net, days, cl); v["pfs"] = pf(evaluate(D, s, val, m=1.2)[0]); v["pf1"] = pf(evaluate(D, s, val, c=1)[0])
        else:
            v = r["valid"]
        label = "PASSED_ALL_GATES_TO_VALIDATION (holdout not yet read)" if r["fail"] is None else "FAILED_GATE_" + r["fail"]
        top.append({"rule": desc(s), "label": label, "discovery": r["disc"], "validation": v, "validation_is_information_only": info})
        lines.append(f"  {label}: {desc(s)} | disc PF {r['disc']['pf']:.2f} n={r['disc']['n']} closes {r['disc']['closes']} days {r['disc']['days']} | valid PF {v['pf']:.2f} (1c {v.get('pf1', 0):.2f}, stress {v.get('pfs', 0):.2f}) n={v['n']} days {v['days']} z {v['z']:+.2f}{' (information only)' if info else ''}")
    FROZEN.write_text(json.dumps({"frozen_at": datetime.now(timezone.utc).isoformat(), "survivors": [r["s"] for r in full]}))
    (DATA_DIR / "gen3_top5.json").write_text(json.dumps(top, indent=1))
    lines.insert(0, "GEN3 VERDICT so far: " + ("NO_WINNER (FALSIFIED before the holdout)" if not full else f"{len(full)} survivors frozen for the holdout"))
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


def holdout():
    out = DATA_DIR / "gen3_holdout_result.txt"
    if out.exists():
        print("Refusing to run again"); return
    fz = json.loads((DATA_DIR.parent / "studies" / "gen3_survivors_FROZEN_2026-10-29.json").read_text())["survivors"]
    build(holdout=True)
    z = np.load(DATA_DIR / "gen3_hold_rows.npz"); D = {k: z[k] for k in z.files}
    alls = np.ones(len(D["X"]), bool)
    lines = [f"GEN3 HOLDOUT (days 24 onward, read once): {len(set(D['day'].tolist()))} days, {len(set(D['close'].tolist()))} hourly closes, {len(fz)} frozen survivors"]
    npass = 0
    for s in fz:
        s["conds"] = [tuple(c) for c in s["conds"]]
        net, days, _, cl, zv = evaluate(D, s, alls); h = stats(net, days, cl)
        h["pfs"] = pf(evaluate(D, s, alls, m=1.2)[0]); h["pf1"] = pf(evaluate(D, s, alls, c=1)[0])
        ok = h["n"] >= 40 and h["days"] >= 5 and h["pf"] >= 1.5 and h["pfs"] >= 1.2 and zv <= 0.2
        npass += ok
        lines.append(f"  {'HOLDOUT-PASS' if ok else 'holdout-fail'} {desc(s)}: PF {h['pf']:.2f} (1 contract {h['pf1']:.2f}, stress {h['pfs']:.2f}) n={h['n']} closes {h['closes']} days {h['days']} mean {h['mean_c']:+.2f}c z {h['z']:+.2f} zero-volume {zv:.0%}")
    lines.insert(0, f"GEN3 holdout verdict: {npass} of {len(fz)} pass")
    out.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"build": build, "search": search, "holdout": holdout}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
