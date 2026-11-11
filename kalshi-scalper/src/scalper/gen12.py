"""GEN12 (workers/GEN12_REGISTRATION.md): the GEN1/GEN2 generator on non-crypto 15 minute series, CHEAP SIDE only. Research only; no network.
    python -m scalper.gen12 build     (rows and every exit's cash net; development and held-out in separate files)
    python -m scalper.gen12 search    (300,000 draws on development only; freezes the list)
    python -m scalper.gen12 holdout   (once; reads the frozen list only)
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from multiprocessing import Pool

import numpy as np

from .calibration import cluster_mean_z
from .paths import DATA_DIR

WK = DATA_DIR.parent / "workers"
FILES = ("alts2", "alts3", "alts4", "fresh", "rep", "l1b", "book", "five")
NC = ["KXSILVER15M", "KXWTI15M", "KXCOPPER15M", "KXNATGAS15M", "KXPLATINUM15M", "KXPALLADIUM15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M",
      "KXAUDUSD15M", "KXUSDCAD15M", "KXNEAR15M", "KXZEC15M", "KXHYPE15M", "KXBNB15M"]
REFS = ["KXGOLD15M", "KXBTC15M"]
FAM = {"KXSILVER15M": 0, "KXCOPPER15M": 0, "KXPALLADIUM15M": 0, "KXPLATINUM15M": 0, "KXWTI15M": 1, "KXNATGAS15M": 1,
       "KXEURUSD15M": 2, "KXGBPUSD15M": 2, "KXUSDJPY15M": 2, "KXAUDUSD15M": 2, "KXUSDCAD15M": 2, "KXNEAR15M": 3, "KXZEC15M": 3, "KXHYPE15M": 3, "KXBNB15M": 3}
PARTNER = {"KXSILVER15M": "KXGOLD15M", "KXCOPPER15M": "KXGOLD15M", "KXPALLADIUM15M": "KXGOLD15M", "KXPLATINUM15M": "KXGOLD15M", "KXWTI15M": "KXNATGAS15M",
           "KXNATGAS15M": "KXWTI15M", "KXEURUSD15M": "KXGBPUSD15M", "KXGBPUSD15M": "KXEURUSD15M", "KXUSDJPY15M": "KXEURUSD15M", "KXAUDUSD15M": "KXEURUSD15M",
           "KXUSDCAD15M": "KXEURUSD15M", "KXNEAR15M": "KXBTC15M", "KXZEC15M": "KXBTC15M", "KXHYPE15M": "KXBTC15M", "KXBNB15M": "KXBTC15M"}
LEFTS = list(range(840, 179, -60))
TP = (0.03, 0.05, 0.08, 0.12, 0.20, None)
ST = (None, 0.05, 0.10, 0.20)
TE = (60, 120, 240)
BK = ("none", "spread3", "cross50")
SINGLE = [("fixed", a, b, c, d) for a in TP for b in ST for c in TE for d in BK] + [("trail", t, None, c, None) for t in (0.05, 0.10, 0.15) for c in TE] + [("hold",)]
NEX = len(SINGLE)
FEATS = ["series", "family", "yes", "left", "ask", "bid", "spread", "d1", "d2", "d3", "d5", "rng5", "vol", "volz", "doi", "hour", "dow", "winidx",
         "mkt_d2", "part_d2", "part_mid", "prev_won", "prev_last"]
GRAMMAR = ["ask", "bid", "spread", "d1", "d2", "d3", "d5", "rng5", "vol", "volz", "doi", "hour", "dow", "winidx", "mkt_d2", "part_d2", "part_mid", "prev_won", "prev_last"]
DEV, HOLD = DATA_DIR / "gen12_dev.npz", DATA_DIR / "gen12_hold.npz"
FROZEN = WK / "GEN12_frozen.json"
N_SHARED, DRAWS = 800_000, 300_000
SEEDS = (12000001, 12000002, 12000003, 12000004)
G = {}


def fee(p):
    p = np.asarray(p, dtype=np.float64)
    return 0.07 * p * (1 - p)


def pf(v):
    w = float(v[v > 0].sum()); l = float(-v[v < 0].sum())
    return w / l if l > 0 else (99.0 if w > 0 else 0.0)


def zbar(n):
    lo, hi = 0.0, 10.0
    p = 1 - 0.05 / n
    for _ in range(100):
        mid = (lo + hi) / 2
        if 0.5 * (1 + math.erf(mid / math.sqrt(2))) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def load_all():
    M = {}
    want = set(NC) | set(REFS)
    for name in FILES:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        new = {}
        for tk, series, strike, close_ts, res in db.execute("select ticker, series, strike, close_ts, result from market where result in ('yes','no')"):
            if series in want and tk not in M:
                new[tk] = (series, strike, close_ts, res)
        if not new:
            continue
        cs = defaultdict(dict)
        for tk, ts, b, a, v, oi in db.execute("select ticker, end_ts, bid_c, ask_c, volume, oi from candle"):
            if tk in new and b is not None and a is not None:
                cs[tk][ts] = (b, a, v or 0.0, oi or 0.0)
        for tk, m in new.items():
            if tk in cs:
                M[tk] = m + (cs[tk],)
    return M


def exits(bids, mids, spreads, ks, e, yes, close_ts, entry_mid):
    fx = [c for c in SINGLE if c[0] != "hold"]
    tp = np.array([np.inf if (c[0] == "trail" or c[1] is None) else c[1] for c in fx])[:, None]
    st = np.array([np.inf if (c[0] == "trail" or c[2] is None) else c[2] for c in fx])[:, None]
    tr = np.array([c[1] if c[0] == "trail" else np.inf for c in fx])[:, None]
    te = np.array([c[3] for c in fx])[:, None]
    bk = np.array([BK.index(c[4]) if c[0] == "fixed" else 0 for c in fx])[:, None]
    B, S, Mi, K = bids[None, :], spreads[None, :], mids[None, :], ks[None, :]
    peak = np.maximum.accumulate(np.r_[e, bids])[1:][None, :]
    against = (Mi < 0.5) if (yes and entry_mid >= 0.5) else ((Mi > 0.5) if ((not yes) and entry_mid <= 0.5) else np.zeros_like(Mi, bool))
    hit = (B >= e + tp - 1e-9) | (B <= e - st + 1e-9) | (B <= peak - tr + 1e-9) | (K >= close_ts - te) | ((bk == 1) & (S >= 0.03 - 1e-9)) | ((bk == 2) & against)
    hit[:, -1] = True
    return hit.argmax(axis=1)


def chunk(items):
    M, byclose, prev, volmed, mkt = G["M"], G["byclose"], G["prev"], G["volmed"], G["mkt"]
    X, W, D, C, NET, ZV = [], [], [], [], [], []
    for wid, tk in items:
        series, strike, close_ts, res, cs = M[tk]
        if series not in FAM:
            continue
        part = byclose.get((PARTNER[series], close_ts))
        day = close_ts // 86400
        keys = sorted(k for k in cs if k <= close_ts - 60)
        pv = prev.get((series, close_ts - 900))
        for L in LEFTS:
            t = close_ts - L; q = cs.get(t)
            if q is None or q[1] - q[0] > 0.03 + 1e-9:
                continue
            ka_ = [k for k in keys if k > t]
            if not ka_:
                continue
            mid = (q[0] + q[1]) / 2; p2 = cs.get(t - 120); own_d2 = mid - ((p2[0] + p2[1]) / 2 if p2 else mid)
            ms = mkt.get((close_ts, t), (0.0, 0))
            mkt_d2 = (ms[0] - own_d2) / (ms[1] - 1) if ms[1] > 1 else 0.0
            if part:
                a, b = part.get(t), part.get(t - 120)
                pm = (a[0] + a[1]) / 2 if a else 0.5; pd2 = pm - ((b[0] + b[1]) / 2 if b else pm)
            else:
                pm, pd2 = 0.5, 0.0
            ka = np.array(ka_); yb = np.array([cs[k][0] for k in ka_]); ya = np.array([cs[k][1] for k in ka_]); vz = np.array([cs[k][2] <= 0 for k in ka_])
            dt_ = datetime.fromtimestamp(t, timezone.utc)
            for yes in (1, 0):
                bid, ask = (q[0], q[1]) if yes else (1 - q[1], 1 - q[0])
                if not 0.04 - 1e-9 <= ask <= 0.30 + 1e-9:
                    continue
                sg_ = 1 if yes else -1
                ds = []
                for lag in (60, 120, 180, 300):
                    p = cs.get(t - lag); ds.append(bid - ((p[0] if yes else 1 - p[1]) if p else bid))
                path = [(cs[t - 60 * j][0] if yes else 1 - cs[t - 60 * j][1]) for j in range(6) if (t - 60 * j) in cs]
                pw = 0.0; pl = 0.5
                if pv:
                    pw = (1.0 if (pv[0] == "yes") == bool(yes) else -1.0)
                    pl = pv[1] if yes else 1 - pv[1]
                bids = yb if yes else 1 - ya
                i1 = exits(bids, (ya + yb) / 2, ya - yb, ka, ask, yes, close_ts, mid)
                xb = bids[i1]
                net = np.empty(NEX, np.float32)
                net[:-1] = xb - ask - fee(ask) - fee(xb)
                won = (res == "yes") == bool(yes)
                net[-1] = (1.0 if won else 0.0) - ask - fee(ask)
                z = np.empty(NEX, bool); z[:-1] = vz[i1] | (q[2] <= 0); z[-1] = q[2] <= 0
                X.append([NC.index(series), FAM[series], yes, L, ask, bid, ask - bid, ds[0], ds[1], ds[2], ds[3], max(path) - min(path) if path else 0.0,
                          q[2], q[2] / volmed.get(series, 1.0), (q[3] - cs[t - 180][3]) if (t - 180) in cs else 0.0, dt_.hour, dt_.weekday(),
                          (close_ts // 900) % 4, sg_ * mkt_d2, sg_ * pd2, pm if yes else 1 - pm, pw, pl])
                W.append(wid); D.append(day); C.append(close_ts); NET.append(net); ZV.append(z)
    out = G["tmp"] / f"{items[0][0]}.npz"
    np.savez(out, X=np.array(X, dtype=np.float32).reshape(-1, len(FEATS)), W=np.array(W, dtype=np.int64), D=np.array(D, dtype=np.int64), C=np.array(C, dtype=np.int64),
             NET=np.array(NET, dtype=np.float32).reshape(-1, NEX), ZV=np.array(ZV, dtype=bool).reshape(-1, NEX))
    return str(out)


def build():
    M = load_all()
    cuts = json.loads((WK / "GEN12_cuts.json").read_text())
    byclose = {(m[0], m[2]): m[4] for m in M.values()}
    prev = {}
    for m in M.values():
        cs = m[4]; last = cs.get(m[2] - 60) or cs[max(cs)]
        prev[(m[0], m[2])] = (m[3], (last[0] + last[1]) / 2)
    vols = defaultdict(list)
    for m in M.values():
        if m[0] in cuts and m[2] < cuts[m[0]]:
            vols[m[0]] += [v[2] for v in m[4].values()]
    volmed = {s: max(statistics.median(v), 1.0) for s, v in vols.items() if v}
    mkt = defaultdict(lambda: [0.0, 0])
    for m in M.values():
        cs = m[4]
        for L in LEFTS:
            t = m[2] - L; a, b = cs.get(t), cs.get(t - 120)
            if a:
                d2 = (a[0] + a[1]) / 2 - (((b[0] + b[1]) / 2) if b else (a[0] + a[1]) / 2)
                x = mkt[(m[2], t)]; x[0] += d2; x[1] += 1
    tmp = DATA_DIR / "gen12_chunks"; tmp.mkdir(exist_ok=True)
    for f in tmp.glob("*.npz"):
        f.unlink()
    G.update(M=M, byclose=byclose, prev=prev, volmed=volmed, mkt={k: tuple(v) for k, v in mkt.items()}, tmp=tmp)
    tk_sorted = sorted(M)
    items = list(enumerate(tk_sorted))
    with Pool(4) as p:
        files = p.map(chunk, [items[i::96] for i in range(96)])
    P = [dict(np.load(f)) for f in files]
    cat = lambda k: np.concatenate([q[k] for q in P])
    X, Wd, Dd, Cc, NET, ZV = cat("X"), cat("W"), cat("D"), cat("C"), cat("NET"), cat("ZV")
    isdev = np.array([Cc[i] < cuts[NC[int(X[i, 0])]] for i in range(len(X))])
    for path, sel in ((DEV, isdev), (HOLD, ~isdev)):
        o = np.lexsort((-X[sel][:, 2], -X[sel][:, 3], Wd[sel]))
        np.savez(path, X=X[sel][o], W=Wd[sel][o], day=Dd[sel][o], NET=NET[sel][o], ZV=ZV[sel][o])
        print(path.name, "rows", int(sel.sum()), "windows", len(set(Wd[sel].tolist())), "days", len(set(Dd[sel].tolist())), flush=True)
    for f in tmp.glob("*.npz"):
        f.unlink()


def load(path):
    z = np.load(path)
    return {k: z[k] for k in z.files}


def draw(rng, Q):
    width = rng.choice(range(60, 601, 60))
    L_hi = rng.choice([L for L in LEFTS if L - width >= 180])
    sc = rng.choice(["all", "series", "family"])
    scope = ("all", None) if sc == "all" else (("series", rng.randrange(len(NC))) if sc == "series" else ("family", rng.randrange(4)))
    s = {"L_hi": L_hi, "L_lo": L_hi - width, "side": rng.choice(["yes", "no", "both"]), "scope": scope, "conds": [], "ex": rng.randrange(NEX)}
    used = set()
    for _ in range(rng.randint(1, 4)):
        f = rng.choice([g for g in GRAMMAR if g not in used]); used.add(f)
        s["conds"].append((f, rng.choice(["le", "gt"]), float(Q[f][rng.choice(range(10, 91, 10))])))
    return s


def trades(D, cols, s, nrows):
    m = (cols["left"] <= s["L_hi"]) & (cols["left"] >= s["L_lo"])
    if s["scope"][0] == "series":
        m &= cols["series"] == s["scope"][1]
    elif s["scope"][0] == "family":
        m &= cols["family"] == s["scope"][1]
    if s["side"] != "both":
        m &= cols["yes"] == (1 if s["side"] == "yes" else 0)
    for f, op, th in s["conds"]:
        m &= (cols[f] <= th) if op == "le" else (cols[f] > th)
    idx = np.flatnonzero(m)
    if len(idx) == 0:
        return idx
    w = D["W"][idx]
    return idx[np.r_[True, w[1:] != w[:-1]]]


def score(D, idx, ex):
    v = D["NET"][idx, ex].astype(np.float64)
    return {"n": len(idx), "days": int(len(np.unique(D["day"][idx]))), "pf": pf(v), "mean": float(v.mean()) if len(v) else 0.0,
            "zv": float(D["ZV"][idx, ex].mean()) if len(idx) else 1.0}


def zday(D, idx, ex):
    v = D["NET"][idx, ex].astype(np.float64)
    return cluster_mean_z(list(zip(D["day"][idx].tolist(), v.tolist())))[2]


def worker(seed):
    D = G["D"]; cols = G["cols"]; Q = G["Q"]
    rng = random.Random(seed)
    n_draw = DRAWS // len(SEEDS)
    stats = np.zeros((n_draw, 5), np.float32)
    passes = []
    for i in range(n_draw):
        s = draw(rng, Q)
        idx = trades(D, cols, s, len(D["W"]))
        if len(idx) == 0:
            continue
        sc = score(D, idx, s["ex"])
        stats[i] = [sc["n"], sc["days"], min(sc["pf"], 99), sc["zv"], sc["mean"]]
        if sc["pf"] >= 1.5 and sc["n"] >= 150 and sc["days"] >= 25 and sc["zv"] <= 0.2:
            sc["z"] = zday(D, idx, s["ex"]); passes.append({"strategy": s, "dev": sc})
    return stats, passes


def search():
    D = load(DEV)
    cols = {f: np.ascontiguousarray(D["X"][:, i]) for i, f in enumerate(FEATS)}
    Q = {f: np.percentile(cols[f], list(range(101))) for f in GRAMMAR}
    G.update(D=D, cols=cols, Q=Q)
    with Pool(4) as p:
        res = p.map(worker, SEEDS)
    stats = np.concatenate([r[0] for r in res]); passes = [x for r in res for x in r[1]]
    scored = int((stats[:, 0] > 0).sum())
    np.save(DATA_DIR / "gen12_stats.npy", stats)
    N = N_SHARED + DRAWS; zb = zbar(N); zb2 = zbar(7731)
    n150 = int(((stats[:, 0] >= 150)).sum())
    lines = [f"GEN12 search: {DRAWS} strategies drawn and scored on development (cash PF basis, unrounded fee), {scored} with at least one trade, {n150} with n >= 150",
             f"N for deflation {N}, z bar {zb:.2f} (7,731 bar {zb2:.2f})",
             f"PF >= 1.0: {int((stats[:, 2] >= 1.0).sum())}; PF >= 1.3 and n >= 150: {int(((stats[:, 2] >= 1.3) & (stats[:, 0] >= 150)).sum())}; "
             f"PF >= 1.5 and n >= 150: {int(((stats[:, 2] >= 1.5) & (stats[:, 0] >= 150)).sum())}",
             f"stage 1 dev passes (PF >= 1.5, n >= 150, 25 days, zero-volume <= 20%): {len(passes)}"]
    best = sorted([(float(r[2]), int(r[0]), int(r[1])) for r in stats if r[0] >= 150], reverse=True)[:5]
    lines.append("best dev PF among n >= 150: " + "; ".join(f"PF {a:.2f} n {b} days {c}" for a, b, c in best))
    passes.sort(key=lambda r: -r["dev"]["z"])
    frozen = [r for r in passes if r["dev"]["z"] >= 3.0][:500]
    lines.append(f"dev passes with dev day-clustered z >= 3.0: {sum(1 for r in passes if r['dev']['z'] >= 3.0)}; frozen (cap 500): {len(frozen)}; best dev z {passes[0]['dev']['z']:.2f}" if passes else "no dev passes")
    FROZEN.write_text(json.dumps({"frozen_at": datetime.now(timezone.utc).isoformat(), "N": N, "zbar": zb, "draws": DRAWS, "dev_passes": len(passes), "frozen": frozen}, indent=1))
    (WK / "GEN12_search_output.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def holdout():
    fz = json.loads(FROZEN.read_text())
    flag = WK / "GEN12_holdout_output.txt"
    if flag.exists():
        print("Refusing to read held-out twice"); return
    H = load(HOLD); Dv = load(DEV)
    hc = {f: np.ascontiguousarray(H["X"][:, i]) for i, f in enumerate(FEATS)}
    dc = {f: np.ascontiguousarray(Dv["X"][:, i]) for i, f in enumerate(FEATS)}
    zb = fz["zbar"]; lines = [f"GEN12 held-out read once: {len(fz['frozen'])} frozen strategies; held-out rows {len(H['W'])}, days {len(set(H['day'].tolist()))}; z bar {zb:.2f}"]
    out = []
    for r in fz["frozen"]:
        s = r["strategy"]; s["conds"] = [tuple(c) for c in s["conds"]]; s["scope"] = tuple(s["scope"])
        hi = trades(H, hc, s, 0)
        hs = score(H, hi, s["ex"]) if len(hi) else {"n": 0, "days": 0, "pf": 0.0, "mean": 0.0, "zv": 1.0}
        s2 = hs["n"] >= 50 and hs["days"] >= 10 and hs["pf"] >= 1.5 and hs["zv"] <= 0.2
        di = trades(Dv, dc, s, 0)
        vd = Dv["NET"][di, s["ex"]].astype(np.float64); vh = H["NET"][hi, s["ex"]].astype(np.float64) if len(hi) else np.array([])
        zp = cluster_mean_z(list(zip(Dv["day"][di].tolist(), vd.tolist())) + list(zip(H["day"][hi].tolist(), vh.tolist())))[2]
        s3 = s2 and zp >= zb and vd.mean() > 0 and (len(vh) and vh.mean() > 0)
        out.append({"strategy": s, "dev": r["dev"], "held": hs, "z_pooled": zp, "stage2": bool(s2), "survivor": bool(s3), "hi": [int(x) for x in hi]})
    n2 = sum(o["stage2"] for o in out); n3 = sum(o["survivor"] for o in out)
    lines.append(f"stage 2 (held-out PF >= 1.5, n >= 50, 10 days): {n2} of {len(out)}; stage 3 (pooled z >= bar): {n3}")
    if out:
        lines.append(f"held-out PF distribution of the frozen list (cash): median {statistics.median(o['held']['pf'] for o in out):.2f}, max {max(o['held']['pf'] for o in out):.2f}; "
                     f"median dev PF {statistics.median(o['dev']['pf'] for o in out):.2f}")
    for o in sorted(out, key=lambda o: -o["held"]["pf"])[:10]:
        lines.append(f"  {'SURVIVOR' if o['survivor'] else ('stage2' if o['stage2'] else 'fail')} {o['strategy']} dev PF {o['dev']['pf']:.2f} n {o['dev']['n']} days {o['dev']['days']} | held PF {o['held']['pf']:.2f} n {o['held']['n']} days {o['held']['days']} | pooled z {o['z_pooled']:.2f}")
    (WK / "GEN12_holdout_results.json").write_text(json.dumps([{k: v for k, v in o.items() if k != "hi"} for o in out], indent=1))
    flag.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"build": build, "search": search, "holdout": holdout}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
