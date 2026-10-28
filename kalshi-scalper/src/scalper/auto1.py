"""AUTO1 (README, Pre-registration: AUTO1). Research only; nothing here means trade.
Usage: python -m scalper.auto1 build | search | final   (final reads the holdout once)
"""
from __future__ import annotations
import math, sys, pickle, random
from datetime import datetime, timezone
from multiprocessing import Pool
import numpy as np
from .scalp12 import load, side_quotes, fee, sigma1, phi, CUR, FLAT
from .paths import DATA_DIR

NPZ = DATA_DIR / "auto1_rows.npz"
CAND = DATA_DIR / "auto1_cands.pkl"
RESULT = DATA_DIR / "auto1_result.txt"
LEFTS = list(range(840, 299, -60))
TARGETS = (0.05, 0.08, 0.10, 0.15, 0.20, 0.30)
STOPS = (None, 0.08, 0.12, 0.16, 0.20, 0.30)
COMBOS = [(t, s) for t in TARGETS for s in STOPS]
FEATS = ["asset", "yes", "left", "ask", "bid", "spread", "d1", "d2", "d3", "hour", "z", "r3"]
ASSET = {"KXBTC15M": 0, "KXETH15M": 1, "KXGOLD15M": 2}
M_GLOBAL = None


def exit_all(bids, e, m):
    out = []
    for tg, st in COMBOS:
        b = bids[-1]
        for x in bids:
            if x >= e + tg - 1e-9 or (st is not None and x <= e - st + 1e-9):
                b = x; break
        out.append(b - e - fee(e, m) - fee(b, m))
    return out


def build_chunk(args):
    items, spot = args
    rows, nets, nets_s = [], [], []
    for wid, tk, (series, strike, close_ts, cs) in items:
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        keys = sorted(k for k in cs if k <= close_ts - FLAT)
        for L in LEFTS:
            t = close_ts - L; q = cs.get(t)
            if q is None: continue
            later = [k for k in keys if k > t]
            if not later: continue
            z0 = r30 = 0.0
            if series in CUR:
                cur = CUR[series]; s = spot.get((cur, t - 60)); sg = sigma1(spot, cur, t); s3 = spot.get((cur, t - 240))
                if s and sg and strike and s3:
                    z0 = math.log(s / strike) / (sg * math.sqrt(L / 60)); r30 = math.log(s / s3)
            for yes in (1, 0):
                side = "yes" if yes else "no"
                bid, ask = side_quotes(q, side)
                ds = []
                for lag in (60, 120, 180):
                    p = cs.get(t - lag); ds.append(bid - side_quotes(p, side)[0] if p else 0.0)
                bids = [side_quotes(cs[k], side)[0] for k in later]
                sgn = 1 if yes else -1
                rows.append((wid, day, ASSET[series], yes, L, ask, bid, ask - bid, ds[0], ds[1], ds[2], datetime.fromtimestamp(t, timezone.utc).hour, sgn * z0, sgn * r30))
                nets.append(exit_all(bids, ask, 1.0)); nets_s.append(exit_all(bids, ask, 1.2))
    return rows, nets, nets_s


def build():
    M, spot = load()
    items = [(i, tk, v) for i, (tk, v) in enumerate(sorted(M.items()))]
    chunks = [(items[i::40], spot) for i in range(40)]
    with Pool(4) as p:
        res = p.map(build_chunk, chunks)
    rows = [r for a, _, _ in res for r in a]; N = np.array([r for _, b, _ in res for r in b], dtype=np.float32); NS = np.array([r for _, _, c in res for r in c], dtype=np.float32)
    days = sorted({r[1] for r in rows}); didx = {d: i for i, d in enumerate(days)}
    X = np.array([[r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13]] for r in rows], dtype=np.float32)
    wid = np.array([r[0] for r in rows]); day = np.array([didx[r[1]] for r in rows])
    order = np.lexsort((-X[:, 1], -X[:, 2], wid))
    np.savez(NPZ, X=X[order], N=N[order], NS=NS[order], wid=wid[order], day=day[order], ndays=len(days))
    print("rows", len(rows), "days", len(days))


def load_rows():
    z = np.load(NPZ); X, N, NS, wid, day = z["X"], z["N"], z["NS"], z["wid"], z["day"]; nd = int(z["ndays"])
    a, b = nd // 2, nd // 2 + nd // 4
    sp = {"train": day < a, "valid": (day >= a) & (day < b), "hold": day >= b}
    return X, N, NS, wid, day, sp


def pf(v):
    w = float(v[v > 0].sum()); l = float(-v[v < 0].sum()); return (w / l) if l > 0 else (99.0 if w > 0 else 0.0)


def mask_of(X, rule):
    m = np.ones(len(X), bool)
    for f, op, th in rule:
        m &= (X[:, f] <= th) if op == "le" else (X[:, f] > th)
    return m


def evaluate(X, N, wid, day, split, rule, c, NS=None):
    m = mask_of(X, rule) & split
    idx = np.flatnonzero(m)
    if len(idx) == 0: return None
    w = wid[idx]; first = np.r_[True, w[1:] != w[:-1]]; idx = idx[first]
    v = N[idx, c]
    out = {"n": len(idx), "pf": pf(v), "days": len(set(day[idx].tolist())), "loss": float((v < 0).mean()), "idx": idx}
    if NS is not None: out["pfs"] = pf(NS[idx, c])
    return out


def tree_rules(tree, leaf_ok):
    t = tree.tree_; out = {}
    def go(n, conds):
        if t.children_left[n] == -1:
            out[n] = list(conds); return
        go(t.children_left[n], conds + [(int(t.feature[n]), "le", float(t.threshold[n]))])
        go(t.children_right[n], conds + [(int(t.feature[n]), "gt", float(t.threshold[n]))])
    go(0, []); return out


def search_cfg(cfg):
    from sklearn.tree import DecisionTreeRegressor
    c, scope, depth, leaf, seed = cfg
    rng = np.random.default_rng(seed)
    sel = np.flatnonzero(SP["train"] & ((X[:, 0] == scope) if scope >= 0 else True))
    if len(sel) < 2000: return []
    sub = rng.choice(sel, size=int(len(sel) * 0.5), replace=False)
    tr = DecisionTreeRegressor(max_depth=depth, min_samples_leaf=leaf // 2, random_state=int(seed)).fit(X[sub], N[sub, c])
    rules = tree_rules(tr, None); found = []
    for node, conds in rules.items():
        if scope >= 0: conds = [(0, "gt", scope - 0.5), (0, "le", scope + 0.5)] + conds
        r = evaluate(X, N, wid, day, SP["train"], conds, c)
        if r and r["n"] >= 100 and r["pf"] >= 2.5:
            found.append((conds, c, r["pf"], r["n"]))
    return found


def init():
    global X, N, NS, wid, day, SP
    X, N, NS, wid, day, SP = load_rows()


def search():
    init()
    seeds = range(int(sys.argv[2]) if len(sys.argv) > 2 else 12)
    cfgs = [(c, sc, d, lf, 0) for c in range(len(COMBOS)) for sc in (-1, 0, 1, 2) for d in (2, 3, 4) for lf in (100, 200) for s in seeds]
    cfgs = [(a, b, cc, dd, i) for i, (a, b, cc, dd, _) in enumerate(cfgs)]
    print("trees", len(cfgs), flush=True)
    cands = {}
    with Pool(4, initializer=init) as p:
        for i, f in enumerate(p.imap_unordered(search_cfg, cfgs, chunksize=8)):
            for conds, c, pfv, n in f:
                cands[(tuple((a, b, round(t, 4)) for a, b, t in conds), c)] = (pfv, n)
            if i % 500 == 0: print(i, len(cands), flush=True)
    pickle.dump({"cands": cands, "trees": len(cfgs)}, open(CAND, "wb"))
    print("trees", len(cfgs), "train winners (PF>=2.5, n>=100)", len(cands))


def neighbours(rule, c):
    qs = {}
    out = []
    for i, (f, op, th) in enumerate(rule):
        if f in (0, 1) : continue
        col = X[SP["train"], f]; q = float((col <= th).mean())
        for dq in (-0.05, 0.05):
            nt = float(np.quantile(col, min(max(q + dq, 0.01), 0.99)))
            out.append((tuple(rule[:i]) + ((f, op, nt),) + tuple(rule[i + 1:]), c))
    ti, si = divmod(c, len(STOPS))
    for dt in (-1, 1):
        for ds in (-1, 1):
            nt, ns = ti + dt, si + ds
            if 0 <= nt < len(TARGETS) and 0 <= ns < len(STOPS): out.append((rule, nt * len(STOPS) + ns))
    for dt in (-1, 1):
        if 0 <= ti + dt < len(TARGETS): out.append((rule, (ti + dt) * len(STOPS) + si))
    for ds in (-1, 1):
        if 0 <= si + ds < len(STOPS): out.append((rule, ti * len(STOPS) + si + ds))
    return out


def final():
    init()
    d = pickle.load(open(CAND, "rb")); cands = d["cands"]
    lines = [f"AUTO1: trees {d['trees']}, train winners {len(cands)}"]
    val = []
    for (rule, c), (pft, nt) in cands.items():
        r = evaluate(X, N, wid, day, SP["valid"], list(rule), c, NS)
        if r and r["n"] >= 60 and r["days"] >= 12 and r["pf"] >= 2.5 and r["pfs"] >= 2.0:
            val.append((r["pf"], rule, c, r, pft, nt))
    lines.append(f"passed validation (PF>=2.5, n>=60, 12 days, stressed PF>=2.0): {len(val)}")
    stable = []
    for vpf, rule, c, r, pft, nt in val:
        nb = neighbours(rule, c); good = 0; tot = 0
        for nr, nc in nb:
            q = evaluate(X, N, wid, day, SP["valid"], list(nr), nc); tot += 1
            if q and q["n"] >= 30 and q["pf"] >= 1.5: good += 1
        if tot and good / tot >= 0.8: stable.append((vpf, rule, c, r, pft, nt, good, tot))
    lines.append(f"passed mutation test (80% of neighbours keep validation PF>=1.5): {len(stable)}")
    stable.sort(key=lambda x: -x[0]); chosen = []
    for s in stable:
        tr = set(np.flatnonzero(mask_of(X, s[1]) & SP["valid"]).tolist()) & set(s[3]["idx"].tolist())
        if all(len(tr & set(o[3]["idx"].tolist())) / max(len(tr), 1) < 0.5 for o in chosen): chosen.append(s)
    lines.append(f"distinct (under 50% shared trades): {len(chosen)}")
    passed = 0
    for vpf, rule, c, r, pft, nt, g, tot in chosen:
        h = evaluate(X, N, wid, day, SP["hold"], list(rule), c, NS)
        ok = bool(h and h["n"] >= 40 and h["pf"] >= 2.5)
        passed += ok
        desc = " and ".join(f"{FEATS[f]} {'<=' if op == 'le' else '>'} {th:.3f}" for f, op, th in rule)
        lines.append(f"{'HOLDOUT-PASS' if ok else 'holdout-fail'} target +{COMBOS[c][0]*100:.0f}c stop {'none' if COMBOS[c][1] is None else '-%.0fc' % (COMBOS[c][1]*100)}: {desc} | train PF {pft:.2f} n={nt} | valid PF {vpf:.2f} n={r['n']} loss {100*r['loss']:.0f}% | mutation {g}/{tot} | holdout " + (f"PF {h['pf']:.2f} n={h['n']} loss {100*h['loss']:.0f}%" if h else "no trades"))
    lines.insert(1, f"VERDICT {'NOT_YET_FALSIFIED' if passed else 'FALSIFIED'}: {passed} strategies passed the holdout")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"build": build, "search": search, "final": final}.get(sys.argv[1], lambda: print(__doc__))()
