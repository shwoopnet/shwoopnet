"""GEN1 (README, Pre-registration: GEN1): a generator of at least 5,000 distinct full scalp strategies on KXBTC15M, KXETH15M, KXGOLD15M.
Research only; nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
    python -m scalper.gen1 build      (entry rows and every exit, discovery and validation days only)
    python -m scalper.gen1 search     (generate, dedupe, score discovery and validation; freezes the survivor list)
    python -m scalper.gen1 holdout    (once, on or after 2026-11-08, after fresh_update; reads the frozen list only)
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from multiprocessing import Pool

import numpy as np

from . import auto3
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalp12 import CUR, side_quotes, sigma1

NPZ = DATA_DIR / "gen1_rows.npz"
HOLD_NPZ = DATA_DIR / "gen1_hold_rows.npz"
FROZEN = DATA_DIR / "gen1_survivors.json"
RESULT = DATA_DIR / "gen1_result.txt"
HOLD_RESULT = DATA_DIR / "gen1_holdout_result.txt"
SERIES = ("KXBTC15M", "KXETH15M", "KXGOLD15M")
ASSET = {s: i for i, s in enumerate(SERIES)}
OTHERS = {"KXBTC15M": ("KXETH15M", "KXGOLD15M"), "KXETH15M": ("KXBTC15M", "KXGOLD15M"), "KXGOLD15M": ("KXBTC15M", "KXETH15M")}
LEFTS = list(range(840, 179, -60))
HOLD_FROM = int(datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp())
DISC_DAYS = 55
TP = (0.03, 0.05, 0.08, 0.12, 0.20, None)
ST = (None, 0.05, 0.10, 0.20)
TE = (60, 120, 240)
BK = ("none", "spread3", "cross50")
COMBOS = [(a, b, c, d) for a in TP for b in ST for c in TE for d in BK]
FEATS = ["asset", "yes", "left", "ask", "bid", "spread", "d1", "d2", "d3", "d5", "rng5", "vol", "doi", "hour",
         "xa_d2", "xa_mid", "xb_d2", "xb_mid", "z", "r3", "tb1", "tb5"]
GRAMMAR_FEATS = [f for f in FEATS if f not in ("asset", "yes", "left")]
N_PRIOR = 199_018
TARGET_DISTINCT, MIN_DISC_TRADES = 5000, 30


def fee(p, c, m=1.0):
    return math.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def load_markets(holdout: bool):
    M = {}
    for name in ("book", "l1b", "fresh"):
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        for tk, series, strike, close_ts in db.execute("select ticker, series, strike, close_ts from market where series in (?,?,?)", SERIES):
            if tk in M or (close_ts >= HOLD_FROM) != holdout:
                continue
            cs = {r[0]: (r[1], r[2], r[3] or 0.0, r[4] or 0.0) for r in db.execute(
                "select end_ts, bid_c, ask_c, volume, oi from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if cs:
                M[tk] = (series, strike, close_ts, cs)
    return M


def spot_load():
    db = sqlite3.connect(DATA_DIR / "search5k.sqlite")
    return {(cur, ts // 1000): c for cur, ts, c in db.execute("select cur, ts, c from bar")}


G = {}


def exits(bids, spreads, mids, ks, e, yes, close_ts, entry_mid):
    """Exit bid and zero-volume flag index for every combo, vectorised over the 216 combos."""
    n = len(bids)
    tp = np.array([np.inf if a is None else a for a, _, _, _ in COMBOS])[:, None]
    st = np.array([np.inf if b is None else b for _, b, _, _ in COMBOS])[:, None]
    te = np.array([c for _, _, c, _ in COMBOS])[:, None]
    bk = np.array([BK.index(d) for _, _, _, d in COMBOS])[:, None]
    B, S, Mi, K = bids[None, :], spreads[None, :], mids[None, :], ks[None, :]
    against = (Mi < 0.5) if (yes and entry_mid >= 0.5) else ((Mi > 0.5) if ((not yes) and entry_mid <= 0.5) else np.zeros_like(Mi, bool))
    hit = (B >= e + tp - 1e-9) | (B <= e - st + 1e-9) | (K >= close_ts - te) | ((bk == 1) & (S >= 0.03 - 1e-9)) | ((bk == 2) & against)
    hit[:, -1] = True
    idx = hit.argmax(axis=1)
    return idx


def build_chunk(items):
    spot, M = G["spot"], G["M"]
    byclose = G["byclose"]
    rows, n10, n1, ns, zv = [], [], [], [], []
    for wid, tk in items:
        series, strike, close_ts, cs = M[tk]
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        keys = sorted(k for k in cs if k <= close_ts - 60)
        oth = [byclose.get((o, close_ts)) for o in OTHERS[series]]
        for L in LEFTS:
            t = close_ts - L
            q = cs.get(t)
            if q is None:
                continue
            later = [k for k in keys if k > t]
            if not later:
                continue
            z0 = r30 = 0.0
            if series in CUR:
                cur = CUR[series]; s = spot.get((cur, t - 60)); sg = sigma1(spot, cur, t); s3 = spot.get((cur, t - 240))
                if s and sg and strike and s3:
                    z0 = math.log(s / strike) / (sg * math.sqrt(L / 60)); r30 = math.log(s / s3)
            xs = []
            for o in oth:
                if o is None:
                    xs += [0.0, 0.5]; continue
                a, b = o.get(t), o.get(t - 120)
                ma = (a[0] + a[1]) / 2 if a else 0.5; mb = (b[0] + b[1]) / 2 if b else ma
                xs += [ma - mb, ma]
            prev = cs.get(t - 60)
            vol = q[2]; doi = (q[3] - cs[t - 180][3]) if (t - 180) in cs else 0.0
            ent_mid = (q[0] + q[1]) / 2
            kb = np.array(later)
            yb = np.array([cs[k][0] for k in later]); ya = np.array([cs[k][1] for k in later])
            vz = np.array([cs[k][2] <= 0 for k in later])
            for yes in (1, 0):
                side = "yes" if yes else "no"
                bid, ask = side_quotes(q[:2], side)
                if not 0.03 <= ask <= 0.85:
                    continue
                ds = []
                for lag in (60, 120, 180, 300):
                    p = cs.get(t - lag); ds.append(bid - side_quotes(p[:2], side)[0] if p else 0.0)
                path = [side_quotes(cs[t - 60 * j][:2], side)[0] for j in range(6) if (t - 60 * j) in cs]
                rng5 = max(path) - min(path) if path else 0.0
                sgn = 1 if yes else -1
                fl = auto3.flow(CUR[series], t, sgn) if series in CUR else (0.0,) * 5
                bids = yb if yes else 1 - ya
                spreads = ya - yb
                mids = (ya + yb) / 2
                idx = exits(bids, spreads, mids, kb, ask, yes, close_ts, ent_mid)
                xb = bids[idx]
                rows.append((wid, day, ASSET[series], yes, L, ask, bid, ask - bid, ds[0], ds[1], ds[2], ds[3], rng5, vol, doi,
                             datetime.fromtimestamp(t, timezone.utc).hour, sgn * xs[0], xs[1], sgn * xs[2], xs[3], sgn * z0, sgn * r30, fl[0], fl[1]))
                n10.append([b - ask - fee(ask, 10) - fee(b, 10) for b in xb])
                n1.append([b - ask - fee(ask, 1) - fee(b, 1) for b in xb])
                ns.append([b - ask - fee(ask, 10, 1.2) - fee(b, 10, 1.2) for b in xb])
                zv.append(list(vz[idx] | (vol <= 0)))
    return rows, n10, n1, ns, zv


def build(holdout=False):
    M = load_markets(holdout)
    spot = spot_load()
    auto3.FUT = auto3.fut_load()
    byclose = {}
    for tk, (series, strike, close_ts, cs) in M.items():
        byclose[(series, close_ts)] = cs
    G.update(spot=spot, M=M, byclose=byclose)
    items = list(enumerate(sorted(M)))
    chunks = [items[i::64] for i in range(64)]
    with Pool(4) as p:
        res = p.map(build_chunk, chunks)
    rows = [r for a in res for r in a[0]]
    days = sorted({r[1] for r in rows}); didx = {d: i for i, d in enumerate(days)}
    X = np.array([list(r[2:]) for r in rows], dtype=np.float32)
    wid = np.array([r[0] for r in rows]); day = np.array([didx[r[1]] for r in rows])
    N10 = np.array([x for a in res for x in a[1]], dtype=np.float32)
    N1 = np.array([x for a in res for x in a[2]], dtype=np.float16)
    NS = np.array([x for a in res for x in a[3]], dtype=np.float16)
    ZV = np.array([x for a in res for x in a[4]], dtype=np.bool_)
    order = np.lexsort((-X[:, 1], -X[:, 2], wid))
    np.savez(HOLD_NPZ if holdout else NPZ, X=X[order], N10=N10[order], N1=N1[order], NS=NS[order], ZV=ZV[order], wid=wid[order], day=day[order], days=np.array(days))
    print("rows", len(rows), "days", len(days), "windows", len(M), flush=True)


def load(path=NPZ):
    z = np.load(path)
    return {k: z[k] for k in z.files}


def pf(v):
    w = float(v[v > 0].sum()); l = float(-v[v < 0].sum())
    return w / l if l > 0 else (99.0 if w > 0 else 0.0)


def trades(D, s, split):
    X = D["X"]
    m = split & (X[:, 2] <= s["L_hi"]) & (X[:, 2] >= s["L_lo"])
    if s["side"] != "both":
        m &= X[:, 1] == (1 if s["side"] == "yes" else 0)
    if s["asset"] is not None:
        m &= X[:, 0] == s["asset"]
    for f, op, th in s["conds"]:
        col = X[:, FEATS.index(f)]
        m &= (col <= th) if op == "le" else (col > th)
    idx = np.flatnonzero(m)
    if len(idx) == 0:
        return idx
    w = D["wid"][idx]
    return idx[np.r_[True, w[1:] != w[:-1]]]


def score(D, idx, c):
    v = D["N10"][idx, c].astype(np.float64)
    days = D["day"][idx]
    return {"n": len(idx), "days": len(set(days.tolist())), "pf": pf(v), "pf1": pf(D["N1"][idx, c].astype(np.float64)),
            "pfs": pf(D["NS"][idx, c].astype(np.float64)), "zv": float(D["ZV"][idx, c].mean()) if len(idx) else 1.0,
            "mean": float(v.mean()) if len(v) else 0.0}


def draw(rng, Q):
    width = rng.choice(range(60, 601, 60))
    L_hi = rng.choice([L for L in LEFTS if L - width >= 180])
    s = {"L_hi": L_hi, "L_lo": L_hi - width, "side": rng.choice(["yes", "no", "both"]), "asset": rng.choice([None, 0, 1, 2]), "conds": [], "c": rng.randrange(len(COMBOS))}
    used = set()
    for _ in range(rng.randint(1, 4)):
        f = rng.choice([g for g in GRAMMAR_FEATS if g not in used]); used.add(f)
        qv = rng.choice(range(10, 91, 10))
        s["conds"].append((f, rng.choice(["le", "gt"]), float(Q[f][qv])))
    return s


def exit_near(c1, c2):
    a, b = COMBOS[c1], COMBOS[c2]
    return all(abs(seq.index(x) - seq.index(y)) <= 1 for seq, x, y in ((TP, a[0], b[0]), (ST, a[1], b[1]), (TE, a[2], b[2]))) and a[3] == b[3]


def boot_pf5(v, days, reps=2000, seed=7):
    rng = np.random.default_rng(seed)
    ud = np.unique(days); byd = {d: v[days == d] for d in ud}
    out = []
    for _ in range(reps):
        pick = rng.choice(ud, size=len(ud), replace=True)
        out.append(pf(np.concatenate([byd[d] for d in pick])))
    return float(np.percentile(out, 5))


def search():
    D = load()
    nd = len(D["days"])
    disc = D["day"] < DISC_DAYS
    val = D["day"] >= DISC_DAYS
    X = D["X"]
    Q = {f: np.percentile(X[disc][:, FEATS.index(f)], list(range(0, 101))) for f in GRAMMAR_FEATS}
    rng = random.Random(20261029)
    distinct = []  # (strategy, discovery window set, score)
    generated = 0
    buckets = defaultdict(list)
    while len(distinct) < TARGET_DISTINCT and generated < 400_000:
        s = draw(rng, Q); generated += 1
        idx = trades(D, s, disc)
        if len(idx) < MIN_DISC_TRADES:
            continue
        ws = set(D["wid"][idx].tolist())
        key = COMBOS[s["c"]][3]
        dup = False
        for j in buckets[key]:
            s2, ws2, _ = distinct[j]
            if exit_near(s["c"], s2["c"]) and len(ws & ws2) / len(ws | ws2) > 0.5:
                dup = True; break
        if dup:
            continue
        buckets[key].append(len(distinct))
        distinct.append((s, ws, score(D, idx, s["c"])))
        if len(distinct) % 500 == 0:
            print("distinct", len(distinct), "generated", generated, flush=True)
    N_total = N_PRIOR + generated
    zbar = float(abs(np.round(_norm_ppf(1 - 0.05 / N_total), 2)))
    d_pass = [(s, sc) for s, ws, sc in distinct if sc["pf"] >= 1.5 and sc["n"] >= 150 and sc["days"] >= 25 and sc["zv"] <= 0.2]
    v_rows = []
    for s, sc in d_pass:
        idx = trades(D, s, val)
        vs = score(D, idx, s["c"])
        ok = vs["n"] >= 60 and vs["days"] >= 15 and vs["pf"] >= 1.5 and vs["pfs"] >= 1.2 and vs["zv"] <= 0.2
        b5 = z = 0.0
        if ok:
            v = D["N10"][idx, s["c"]].astype(np.float64)
            b5 = boot_pf5(v, D["day"][idx])
            _, _, z = cluster_mean_z(list(zip(D["day"][idx].tolist(), v.tolist())))
        v_rows.append((s, sc, vs, ok, b5, z, ok and b5 > 1.0, ok and b5 > 1.0 and z >= zbar))
    lines = [f"GEN1: generated {generated}, distinct (Jaccard <= 0.5 or exits apart, >= {MIN_DISC_TRADES} discovery trades) {len(distinct)}; "
             f"rows {len(X)}; days discovery {len(set(D['day'][disc].tolist()))}, validation {len(set(D['day'][val].tolist()))}; N tried for deflation {N_total}, Bonferroni z bar {zbar:.2f}"]
    lines.append(f"passed discovery (PF >= 1.5 at 10 contracts, n >= 150, 25 days, zero-volume share <= 20%): {len(d_pass)}")
    vpass = [r for r in v_rows if r[3]]; bpass = [r for r in v_rows if r[6]]; dpass = [r for r in v_rows if r[7]]
    lines.append(f"passed validation gates (PF >= 1.5, n >= 60, 15 days, stressed PF >= 1.2): {len(vpass)}; and bootstrap 5th pct PF > 1: {len(bpass)}; and deflation (z >= bar): {len(dpass)}")
    for s, sc, vs, ok, b5, z, bok, dok in sorted(v_rows, key=lambda r: -r[2]["pf"])[:15]:
        lines.append(f"  {'DEFLATED-PASS' if dok else ('pass' if ok else 'fail')} {desc(s)} | disc PF {sc['pf']:.2f} n={sc['n']} | valid PF {vs['pf']:.2f} (1c rounding {vs['pf1']:.2f}, stress {vs['pfs']:.2f}) n={vs['n']} days {vs['days']} | boot5 {b5:.2f} z {z:+.2f}")
    frozen = [{"strategy": s, "disc": sc, "valid": vs, "z": z, "boot5": b5} for s, sc, vs, ok, b5, z, bok, dok in v_rows if dok]
    FROZEN.write_text(json.dumps({"frozen_at": datetime.now(timezone.utc).isoformat(), "N_total": N_total, "zbar": zbar, "survivors": frozen}, indent=1))
    verdict = "NO_WINNER before the holdout (FALSIFIED)" if not frozen else f"{len(frozen)} frozen for the holdout"
    lines.insert(0, f"GEN1 VERDICT so far: {verdict}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


def _norm_ppf(p):
    lo, hi = -10.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if 0.5 * (1 + math.erf(mid / math.sqrt(2))) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def desc(s):
    a = {None: "all", 0: "BTC", 1: "ETH", 2: "GOLD"}[s["asset"]]
    tp, st, te, bk = COMBOS[s["c"]]
    cond = " & ".join(f"{f}{'<=' if op == 'le' else '>'}{th:.3g}" for f, op, th in s["conds"])
    return f"[{a} {s['side']} {s['L_hi']}..{s['L_lo']}s left | {cond} | TP {'none' if tp is None else int(tp * 100)} stop {'none' if st is None else int(st * 100)} time {te}s book {bk}]"


def holdout():
    if HOLD_RESULT.exists():
        print("Refusing to run again"); return
    fz = json.loads(FROZEN.read_text())
    if not fz["survivors"]:
        HOLD_RESULT.write_text("GEN1 holdout: nothing frozen, nothing to read (NO_WINNER)\n"); print("nothing frozen"); return
    build(holdout=True)
    D = load(HOLD_NPZ)
    alls = np.ones(len(D["X"]), bool)
    lines = [f"GEN1 holdout: {len(D['days'])} days, {len(set(D['wid'].tolist()))} windows"]
    for r in fz["survivors"]:
        s = r["strategy"]; s["conds"] = [tuple(c) for c in s["conds"]]
        hs = score(D, trades(D, s, alls), s["c"])
        ok = hs["n"] >= 40 and hs["days"] >= 8 and hs["pf"] >= 1.5 and hs["pfs"] >= 1.2 and hs["zv"] <= 0.2
        lines.append(f"  {'HOLDOUT-PASS' if ok else 'holdout-fail'} {desc(s)}: PF {hs['pf']:.2f} stress {hs['pfs']:.2f} n={hs['n']} days {hs['days']}")
    HOLD_RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"build": build, "search": search, "holdout": holdout}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
