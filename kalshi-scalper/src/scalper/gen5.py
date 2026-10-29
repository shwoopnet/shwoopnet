"""GEN5 (workers/GEN5_REGISTRATION.md): a 1 minute strategy generator on KXGOLD15M and KXBTC15M with OUTSIDE reference prices
(Yahoo GC=F, DX-Y.NYB, ^TNX for gold; Coinbase BTC-USD for Bitcoin). GEN1's grammar, exits and dedupe. Research only; places nothing.
    python -m scalper.gen5_fetch                (outside bars, public)
    python -m scalper.gen5 build gold|btc       (entry rows and every exit, discovery and validation days)
    python -m scalper.gen5 discover gold|btc    (generate, dedupe, score discovery; freezes survivors with sha256)
    python -m scalper.gen5 validate gold|btc    (once; frozen survivors only)
    python -m scalper.gen5 forward <candidate.json>   (forward read via evaluate(); needs fresh_update and gen5_fetch first)
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
from multiprocessing import Pool

import numpy as np

from .calibration import cluster_mean_z
from .gen1 import BK, COMBOS, LEFTS, ST, TE, TP, exit_near, exits, pf, vfee, _norm_ppf
from .paths import DATA_DIR
from .scalp12 import side_quotes

OUT = DATA_DIR / "gen5"
SERIES = {"gold": "KXGOLD15M", "btc": "KXBTC15M"}
OUTSIDE = {"gold": {"o": "GCF", "dx": "DX-Y.NYB", "tnx": "TNX"}, "btc": {"o": "CB_BTCUSD"}}
GUARD = {"GCF": ("log", 0.005), "DX-Y.NYB": ("log", 0.005), "TNX": ("lvl", 0.05), "CB_BTCUSD": ("log", 0.03)}
FWD_FROM = int(datetime(2026, 10, 30, tzinfo=timezone.utc).timestamp())
SPLIT = {"gold": (("2026-10-01", "2026-10-18"), ("2026-10-19", "2026-10-29")),
         "btc": (("2026-08-06", "2026-09-30"), ("2026-10-01", "2026-10-29"))}
SCREEN = {"gold": (60, 8), "btc": (100, 10)}
KAL = ["ask", "spread", "d1", "d3", "rng5", "hour"]
OFEAT = ["o_r1", "o_r3", "o_r5", "o_r15", "o_vol", "o_volr", "o_dz", "o_fv"]
MFEAT = {"gold": ["dx_r5", "dx_r15", "tnx_r5", "tnx_r15"], "btc": []}
N_PRIOR = 439_000
TARGET, MAX_DRAWS, MIN_DISC = 5000, 300_000, 30


def feats(mk):
    return ["yes", "left"] + KAL + OFEAT + MFEAT[mk]


def grammar(mk):
    return KAL + OFEAT + MFEAT[mk]


def outside_feats(mk):
    return OFEAT + MFEAT[mk]


class Px:
    """Minute price series keyed by bar START, forward-filled at most 5 minutes; tracks which minutes had a real bar."""

    def __init__(self, name):
        bars = {int(k): v for k, v in json.loads((OUT / f"{name}.json").read_text())["bars"].items() if int(k) % 60 == 0}  # a non-minute stamp is the live, unfinished bar
        self.t0 = min(bars) // 60 * 60
        n = (max(bars) - self.t0) // 60 + 1
        p = np.full(n, np.nan); real = np.zeros(n, bool)
        for k, v in bars.items():
            i = (k - self.t0) // 60
            if v > 0:
                p[i] = v; real[i] = True
        last, age = np.nan, 99
        for i in range(n):
            if real[i]:
                last, age = p[i], 0
            else:
                age += 1; p[i] = last if age <= 5 else np.nan
        self.p, self.real, self.n = p, real, n
        kind, lim = GUARD[name]
        self.lg = np.log(p) if kind == "log" else p
        ch = np.abs(np.diff(self.lg, prepend=np.nan))
        self.bad = np.nan_to_num(ch, nan=0.0) > lim

    def i(self, ts):
        k = (ts - self.t0) // 60
        return int(k) if 0 <= k < self.n else None

    def at(self, ts):
        k = self.i(ts)
        return self.lg[k] if k is not None else np.nan

    def ok(self, ts, minutes):
        k = self.i(ts)
        if k is None or k - minutes < 0:
            return False
        return not self.bad[k - minutes + 1:k + 1].any()

    def vol(self, ts, m):
        k = self.i(ts)
        if k is None or k - m < 0:
            return np.nan
        seg = self.lg[k - m:k + 1]
        if self.real[k - m + 1:k + 1].sum() < 0.75 * m or np.isnan(seg).any():
            return np.nan
        return float(np.std(np.diff(seg)))


def load_markets(mk, lo_ts, hi_ts):
    series = SERIES[mk]
    M = {}
    for name in ("five", "fresh", "book", "l1b"):
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        last = db.execute("select max(end_ts) from candle where series=?", (series,)).fetchone()[0] or 0
        for tk, close_ts in db.execute("select ticker, close_ts from market where series=? and close_ts>=? and close_ts<?", (series, lo_ts, hi_ts)).fetchall():
            if tk in M or close_ts > last:
                continue
            cs = {r[0]: (r[1], r[2], r[3] or 0.0) for r in db.execute(
                "select end_ts, bid_c, ask_c, volume from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if cs:
                M[tk] = (close_ts, cs)
    return M


G = {}


def outside_row(mk, t, close_ts, sgn, ask):
    """Outside features at decision candle end t. Only bars with START <= t - 120 (ended before the signal candle began)."""
    P = G["px"]
    s = t - 120
    o = P["o"]
    f = {}
    if o.ok(s, 61):
        x = o.at(s)
        for k in (1, 3, 5, 15):
            f[f"o_r{k}"] = sgn * (x - o.at(s - 60 * k)) * 1e4
        v60 = o.vol(s, 60); v15 = o.vol(s, 15)
        f["o_vol"] = v60 * 1e4 if v60 == v60 else np.nan
        f["o_volr"] = v15 / v60 if (v60 == v60 and v15 == v15 and v60 > 0) else np.nan
        x0 = o.at(close_ts - 900 - 60)
        tau = (close_ts - s) / 60
        if v60 == v60 and v60 > 0 and x0 == x0 and o.ok(s, (s - (close_ts - 960)) // 60 + 1):
            dz = sgn * (x - x0) / (v60 * math.sqrt(tau))
            f["o_dz"] = dz
            f["o_fv"] = 0.5 * (1 + math.erf(dz / math.sqrt(2))) - ask
    for pre in ("dx", "tnx"):
        if pre in P:
            q = P[pre]
            if q.ok(s, 16):
                for k in (5, 15):
                    f[f"{pre}_r{k}"] = sgn * (q.at(s) - q.at(s - 60 * k)) * (1e4 if pre == "dx" else 100)
    return f


def side_arrays(cs, later, yes):
    yb = np.array([cs[k][0] for k in later]); ya = np.array([cs[k][1] for k in later])
    bids = yb if yes else 1 - ya
    return bids, ya - yb, (ya + yb) / 2


def build_chunk(items):
    mk, M = G["mk"], G["M"]
    F = feats(mk)
    X, wids, days, N10n, N1n, NSn, ZVn, N10s, N1s, ZVs, FILLN = [], [], [], [], [], [], [], [], [], [], []
    nanrow = np.full(len(COMBOS), np.nan, np.float32)
    for wid, tk in items:
        close_ts, cs = M[tk]
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        keys = sorted(k for k in cs if k <= close_ts - 60)
        for L in LEFTS:
            t = close_ts - L
            q = cs.get(t)
            if q is None:
                continue
            later_s = [k for k in keys if k > t]
            if not later_s:
                continue
            nq = cs.get(t + 60)
            later_n = [k for k in keys if k > t + 60]
            ent_mid = (q[0] + q[1]) / 2
            for yes in (1, 0):
                side = "yes" if yes else "no"
                bid, ask = side_quotes(q[:2], side)
                if not 0.03 <= ask <= 0.85:
                    continue
                sgn = 1 if yes else -1
                ds = []
                for lag in (60, 180):
                    p = cs.get(t - lag); ds.append(bid - side_quotes(p[:2], side)[0] if p else np.nan)
                path = [side_quotes(cs[t - 60 * j][:2], side)[0] for j in range(6) if (t - 60 * j) in cs]
                f = outside_row(mk, t, close_ts, sgn, ask)
                f.update(yes=yes, left=L, ask=ask, spread=ask - bid, d1=ds[0], d3=ds[1], rng5=(max(path) - min(path)) if path else np.nan,
                         hour=datetime.fromtimestamp(t, timezone.utc).hour)
                X.append([f.get(k, np.nan) for k in F]); wids.append(wid); days.append(day)
                kb = np.array(later_s); b, sp, mi = side_arrays(cs, later_s, yes)
                idx = exits(b, sp, mi, kb, ask, yes, close_ts, ent_mid); xb = b[idx]
                vz = np.array([cs[k][2] <= 0 for k in later_s])
                N10s.append((xb - ask - vfee(ask, 10) - vfee(xb, 10)).astype(np.float32))
                N1s.append((xb - ask - vfee(ask, 1) - vfee(xb, 1)).astype(np.float32))
                ZVs.append(vz[idx] | (q[2] <= 0))
                if nq is not None and later_n:
                    e = side_quotes(nq[:2], side)[1]
                    kb = np.array(later_n); b, sp, mi = side_arrays(cs, later_n, yes)
                    idx = exits(b, sp, mi, kb, e, yes, close_ts, ent_mid); xb = b[idx]
                    vz = np.array([cs[k][2] <= 0 for k in later_n])
                    N10n.append((xb - e - vfee(e, 10) - vfee(xb, 10)).astype(np.float32))
                    N1n.append((xb - e - vfee(e, 1) - vfee(xb, 1)).astype(np.float32))
                    NSn.append((xb - e - vfee(e, 10, 1.2) - vfee(xb, 10, 1.2)).astype(np.float32))
                    ZVn.append(vz[idx] | (nq[2] <= 0)); FILLN.append(True)
                else:
                    N10n.append(nanrow); N1n.append(nanrow); NSn.append(nanrow); ZVn.append(np.ones(len(COMBOS), bool)); FILLN.append(False)
    nc = len(COMBOS)
    return dict(X=np.array(X, np.float32).reshape(-1, len(F)), wid=np.array(wids, np.int64), day=np.array(days),
                N10n=np.array(N10n, np.float32).reshape(-1, nc), N1n=np.array(N1n, np.float16).reshape(-1, nc), NSn=np.array(NSn, np.float16).reshape(-1, nc),
                ZVn=np.array(ZVn, bool).reshape(-1, nc), N10s=np.array(N10s, np.float32).reshape(-1, nc), N1s=np.array(N1s, np.float16).reshape(-1, nc),
                ZVs=np.array(ZVs, bool).reshape(-1, nc), filln=np.array(FILLN, bool))


def _init(mk, M):
    G.update(mk=mk, M=M, px={k: Px(v) for k, v in OUTSIDE[mk].items()})


def build_rows(mk, lo_ts, hi_ts, path):
    M = load_markets(mk, lo_ts, hi_ts)
    items = list(enumerate(sorted(M)))
    chunks = [items[i::32] for i in range(32)]
    with Pool(4, initializer=_init, initargs=(mk, M)) as p:
        parts = p.map(build_chunk, chunks)
    D = {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}
    order = np.lexsort((-D["X"][:, 0], -D["X"][:, 1], D["wid"]))
    D = {k: v[order] for k, v in D.items()}
    np.savez(path, **D)
    print(mk, "rows", len(D["X"]), "windows", len(M), "days", len(set(D["day"].tolist())), "next-candle fill available", float(D["filln"].mean()), flush=True)


def npz(mk):
    return DATA_DIR / f"gen5_{mk}_rows.npz"


def build(mk):
    (a, _), (_, b) = SPLIT[mk]
    lo = int(datetime.fromisoformat(a).replace(tzinfo=timezone.utc).timestamp())
    hi = int(datetime.fromisoformat(b).replace(tzinfo=timezone.utc).timestamp()) + 86400
    build_rows(mk, lo, min(hi, FWD_FROM), npz(mk))


def load(path):
    z = np.load(path)
    return {k: z[k] for k in z.files}


def trades(D, s, mask, mk):
    F = feats(mk)
    X = D["X"]
    m = mask & (X[:, 1] <= s["L_hi"]) & (X[:, 1] >= s["L_lo"])
    if s["side"] != "both":
        m &= X[:, 0] == (1 if s["side"] == "yes" else 0)
    for f, op, th in s["conds"]:
        col = X[:, F.index(f)]
        m &= (col <= th) if op == "le" else (col > th)
    idx = np.flatnonzero(m)
    if len(idx) == 0:
        return idx
    w = D["wid"][idx]
    return idx[np.r_[True, w[1:] != w[:-1]]]


def score(D, idx, c, fill="n"):
    if fill == "n":
        idx = idx[D["filln"][idx]]
    v = D[f"N10{fill}"][idx, c].astype(np.float64)
    out = {"n": int(len(idx)), "days": len(set(D["day"][idx].tolist())), "pf": pf(v), "pf1": pf(D[f"N1{fill}"][idx, c].astype(np.float64)),
           "zv": float(D[f"ZV{fill}"][idx, c].mean()) if len(idx) else 1.0, "mean_c": float(v.mean() * 100) if len(v) else 0.0}
    if fill == "n":
        out["pfs"] = pf(D["NSn"][idx, c].astype(np.float64))
        _, _, z = cluster_mean_z(list(zip(D["day"][idx].tolist(), v.tolist()))) if len(v) > 1 else (0, 0, 0.0)
        out["z"] = float(z)
    return out


def draw(rng, Q, mk):
    width = rng.choice(range(60, 601, 60))
    L_hi = rng.choice([L for L in LEFTS if L - width >= 180])
    s = {"market": mk, "L_hi": L_hi, "L_lo": L_hi - width, "side": rng.choice(["yes", "no", "both"]), "conds": [], "c": rng.randrange(len(COMBOS))}
    k = rng.randint(1, 4)
    pool_o, pool = outside_feats(mk), grammar(mk)
    used = {rng.choice(pool_o)}
    while len(used) < k:
        used.add(rng.choice(pool))
    for f in sorted(used):
        qv = rng.choice(range(10, 91, 10))
        s["conds"].append((f, rng.choice(["le", "gt"]), float(Q[f][qv])))
    return s


def desc(s):
    tp, st, te, bk = COMBOS[s["c"]]
    cond = " & ".join(f"{f}{'<=' if op == 'le' else '>'}{th:.4g}" for f, op, th in s["conds"])
    return (f"[{s['market']} {s['side']} {s['L_hi']}..{s['L_lo']}s left | {cond} | TP {'none' if tp is None else int(round(tp * 100))} "
            f"stop {'none' if st is None else int(round(st * 100))} time {te}s book {bk}]")


def masks(D, mk):
    (a, b), (c, d) = SPLIT[mk]
    day = D["day"]
    return (day >= a) & (day <= b), (day >= c) & (day <= d)


def frozen_path(mk):
    return DATA_DIR / f"gen5_{mk}_frozen.json"


def discover(mk):
    D = load(npz(mk)); disc, val = masks(D, mk)
    F = feats(mk)
    Q = {f: np.nanpercentile(D["X"][disc][:, F.index(f)], list(range(101))) for f in grammar(mk)}
    rng = random.Random(20261030 + (1 if mk == "btc" else 0))
    distinct, buckets, generated = [], defaultdict(list), 0
    while len(distinct) < TARGET and generated < MAX_DRAWS:
        s = draw(rng, Q, mk); generated += 1
        idx = trades(D, s, disc, mk)
        idx = idx[D["filln"][idx]]
        if len(idx) < MIN_DISC:
            continue
        ws = set(D["wid"][idx].tolist())
        dup = False
        for j in buckets[COMBOS[s["c"]][3]]:
            s2, ws2, _ = distinct[j]
            if exit_near(s["c"], s2["c"]) and len(ws & ws2) / len(ws | ws2) > 0.5:
                dup = True; break
        if dup:
            continue
        buckets[COMBOS[s["c"]][3]].append(len(distinct))
        distinct.append((s, ws, score(D, idx, s["c"])))
        if len(distinct) % 1000 == 0:
            print(mk, "distinct", len(distinct), "generated", generated, flush=True)
    mn, md = SCREEN[mk]
    surv = [(s, sc) for s, _, sc in distinct if sc["pf"] >= 1.5 and sc["n"] >= mn and sc["days"] >= md and sc["zv"] <= 0.2]
    pfs = np.array([sc["pf"] for _, _, sc in distinct]); big = np.array([sc["pf"] for _, _, sc in distinct if sc["n"] >= mn and sc["days"] >= md])
    body = {"market": mk, "frozen_at": datetime.now(timezone.utc).isoformat(), "generated": generated, "distinct": len(distinct),
            "disc_pf_median": float(np.median(pfs)), "disc_pf_p95": float(np.percentile(pfs, 95)),
            "disc_pf_max_screened_size": float(big.max()) if len(big) else None, "n_screened_size": int(len(big)),
            "survivors": [{"strategy": s, "disc": sc, "disc_signal_fill": score(D, trades(D, s, disc, mk), s["c"], "s")} for s, sc in surv]}
    top = sorted([(s, sc) for s, _, sc in distinct if sc["n"] >= mn and sc["days"] >= md], key=lambda r: -r[1]["pf"])[:10]
    body["top10_info"] = [{"strategy": s, "disc": sc} for s, sc in top]
    txt = json.dumps(body, indent=1, default=float)
    frozen_path(mk).write_text(txt)
    print(mk, "generated", generated, "distinct", len(distinct), "survivors", len(surv), "sha256", hashlib.sha256(txt.encode()).hexdigest(), flush=True)


def validate(mk):
    out = DATA_DIR / f"gen5_{mk}_validation.json"
    if out.exists():
        print("Refusing to run again"); return
    txt = frozen_path(mk).read_text()
    fz = json.loads(txt)
    D = load(npz(mk)); disc, val = masks(D, mk)
    rows = []
    for r in fz["survivors"] + [dict(t, info=True) for t in fz["top10_info"]]:
        s = r["strategy"]; s["conds"] = [tuple(c) for c in s["conds"]]
        idx = trades(D, s, val, mk)
        vs = score(D, idx, s["c"]); vss = score(D, idx, s["c"], "s")
        ok = (not r.get("info")) and vs["pf"] >= 1.3 and vs["n"] >= 40 and vs["pfs"] > 1.0 and vs["zv"] <= 0.2
        rows.append({"strategy": s, "disc": r["disc"], "valid": vs, "valid_signal_fill": vss, "pass": ok, "info_only": bool(r.get("info"))})
    out.write_text(json.dumps({"frozen_sha256": hashlib.sha256(txt.encode()).hexdigest(), "read_at": datetime.now(timezone.utc).isoformat(), "rows": rows}, indent=1, default=float))
    print(mk, "survivors", len(fz["survivors"]), "validation passes", sum(r["pass"] for r in rows))


def evaluate(strategy, since_ts=FWD_FROM, until_ts=None):
    """Forward evaluator for a GEN5 candidate: rebuilds rows for windows closing in [since_ts, until_ts) and scores the frozen strategy
    at the next candle's ask (primary) and the signal candle's ask. Needs `python -m scalper.fresh_update` and `python -m scalper.gen5_fetch` first."""
    mk = strategy["market"]; s = dict(strategy, conds=[tuple(c) for c in strategy["conds"]])
    path = DATA_DIR / f"gen5_{mk}_fwd_rows.npz"
    build_rows(mk, since_ts, until_ts or 2**31, path)
    D = load(path); allm = np.ones(len(D["X"]), bool)
    idx = trades(D, s, allm, mk)
    return {"next_fill": score(D, idx, s["c"]), "signal_fill": score(D, idx, s["c"], "s"), "days_on_file": len(set(D["day"].tolist()))}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "forward":
        c = json.loads(open(sys.argv[2]).read())
        print(json.dumps(evaluate(c["strategy"]), indent=1, default=float))
    elif cmd in ("build", "discover", "validate"):
        {"build": build, "discover": discover, "validate": validate}[cmd](sys.argv[2])
    else:
        print(__doc__)
