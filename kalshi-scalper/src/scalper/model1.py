"""MODEL1 (README "MODEL1"; workers/MODEL1_REGISTRATION.md): can a pooled, price-matched model on observable quote features find ANY region of
CHEAP-side entries (ask 3c to 30c) with positive expected net after fees, out of sample? Reuses the LIQ1/CALIB1 development table; no Kalshi fetch.
Cheap side only (owner rule): no entry above 0.30 is ever built, counted, scored or printed. Frozen third never read.

Usage: python3 -I -m scalper.model1 census   rows, missing rates, split sizes (NO outcome read)
       python3 -I -m scalper.model1 fit      train outcomes only; picks hyperparameters on the inner split; prints selected TEST counts (test outcomes NOT loaded)
       python3 -I -m scalper.model1 score    ONE run on the test third -> workers/MODEL1_RESULT.json (refuses a second run)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKERS = ROOT / "workers"
LIQ1_DIR = Path(os.environ.get("MODEL1_LIQ1", "/tmp/liq1"))
OVR_SWEEP = os.environ.get("MODEL1_SWEEP", "/tmp/usweep1_cache")
OUT = Path(os.environ.get("MODEL1_OUT", "/tmp/model1"))
os.environ.setdefault("OVR1_SWEEP", OVR_SWEEP)

from scalper import calib1 as C  # noqa: E402

SEED = 20261104
BOOT = 2000
MARGINS = (0.02, 0.04)
MAX_PER_EVENT = 2
MIN_TRADES = 150
PF_BAR = 1.5
PERM_P = 0.01
N_PERM = {"logit": 500, "gbt": 200}
MIN_PERM_TRADES = 20
LOGIT_LAMBDAS = (0.1, 1.0, 10.0, 100.0)
GBT_GRID = [{"depth": d, "trees": t} for d in (2, 3) for t in (50, 150)]
GBT_FIXED = {"lr": 0.1, "min_leaf": 100, "l2": 10.0, "bins": 32}
MIN_CAT, MIN_SERIES = 100, 200      # a category / series is its own column only with this many TRAIN rows
FRAC_TRAIN, FRAC_INNER = 2 / 3, 3 / 4
FROZEN_FROM = 1791043200            # 2026-10-03T16:00Z: rows whose market closes at or after this are dropped (the research session's frozen third)


# ---------------------------------------------------------------- data (no outcome)
def md5key(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def look_minutes(tag: str):
    """Minutes before the close at the look, or None when the look is an age after listing (A1h, A3h, A6h)."""
    if tag.startswith("T"):
        return float(tag[1:])
    if tag == "late":
        return 180.0
    return None


def load_rows():
    rows = [json.loads(x) for x in open(LIQ1_DIR / "features.jsonl") if x.strip()]
    assert all(r["ask"] <= C.ASK_HI + 1e-9 for r in rows), "a favourite-side entry slipped in"
    return [r for r in rows if r["t"] < FROZEN_FROM]


def attach_overround(rows):
    """Weather ladder overround of the event-look where OVERROUND1's registered structure exists; otherwise missing. Structure only, no outcome."""
    from scalper import overround1 as O
    ov = {}
    for r in O.build(False):
        ov[(r["event"], r["look"])] = r["ov"]
    for r in rows:
        r["ov"] = ov.get((r["event"], r["look"]))
    return rows


def split_events(rows):
    """Event sets: train (first 2/3 by earliest close, ties by event id), test (last third), inner fit / inner val inside train."""
    g = C.event_groups(rows, key="ask")
    order = sorted(g, key=lambda e: (g[e][2], e))
    k = int(len(order) * FRAC_TRAIN)
    tr, te = order[:k], order[k:]
    ki = int(len(tr) * FRAC_INNER)
    return set(tr), set(te), set(tr[:ki]), set(tr[ki:]), te


# ---------------------------------------------------------------- features
def logit(p):
    return math.log(p / (1 - p))


class Spec:
    """Column layout fitted on TRAIN rows only (categories, series, standardisation)."""
    def __init__(self, train):
        n = len(train)
        cats = {}
        ser = {}
        for r in train:
            cats[r["cat"]] = cats.get(r["cat"], 0) + 1
            ser[r["series"]] = ser.get(r["series"], 0) + 1
        self.cats = sorted(c for c, k in cats.items() if k >= MIN_CAT)
        self.series = sorted(s for s, k in ser.items() if k >= MIN_SERIES)
        self.looks = sorted({r["look"] for r in train})
        self.names = (["ask", "logit_ask", "spread_c", "log_vol", "vol_zero", "log_ttc", "ttc_missing", "ov", "ov_missing", "side_yes"]
                      + [f"cat={c}" for c in self.cats] + ["cat=other"] + [f"life={x}" for x in ("D", "W", "H")]
                      + [f"look={x}" for x in self.looks] + [f"ser={s}" for s in self.series] + ["ser=other"])
        self.cont = list(range(0, 10))      # the first ten are standardised (binary ones too, harmless)
        X = self._raw(train)
        self.mu = X.mean(axis=0)
        self.sd = X.std(axis=0)
        self.sd[self.sd < 1e-9] = 1.0
        self.n_train = n

    def _raw(self, rows):
        X = np.zeros((len(rows), len(self.names)))
        ci = {c: 10 + i for i, c in enumerate(self.cats)}
        o_cat = 10 + len(self.cats)
        li = {x: o_cat + 1 + i for i, x in enumerate(("D", "W", "H"))}
        lk = {x: o_cat + 4 + i for i, x in enumerate(self.looks)}
        o_ser = o_cat + 4 + len(self.looks)
        si = {s: o_ser + i for i, s in enumerate(self.series)}
        for i, r in enumerate(rows):
            a = r["ask"]
            tt = look_minutes(r["look"])
            X[i, 0], X[i, 1], X[i, 2] = a, logit(a), r["spread_c"]
            X[i, 3], X[i, 4] = math.log1p(r["vol"]), 1.0 if r["vol"] <= 0 else 0.0
            X[i, 5], X[i, 6] = (math.log1p(tt), 0.0) if tt is not None else (0.0, 1.0)
            ov = r.get("ov")
            X[i, 7], X[i, 8] = (ov, 0.0) if ov is not None else (0.0, 1.0)
            X[i, 9] = 1.0 if r["side"] == "yes" else 0.0
            X[i, ci.get(r["cat"], o_cat)] = 1.0
            if r["life"] in li:
                X[i, li[r["life"]]] = 1.0
            if r["look"] in lk:
                X[i, lk[r["look"]]] = 1.0
            X[i, si.get(r["series"], len(self.names) - 1)] = 1.0
        return X

    def matrix(self, rows):
        X = self._raw(rows)
        Z = X.copy()
        Z[:, self.cont] = (X[:, self.cont] - self.mu[self.cont]) / self.sd[self.cont]
        return X, Z


# ---------------------------------------------------------------- model 1: L2 logistic (Newton)
def fit_logit(Z, y, lam, iters=40):
    n, d = Z.shape
    A = np.hstack([np.ones((n, 1)), Z])
    w = np.zeros(d + 1)
    w[0] = math.log(max(y.mean(), 1e-6) / max(1 - y.mean(), 1e-6))
    pen = np.full(d + 1, lam)
    pen[0] = 0.0
    for _ in range(iters):
        z = np.clip(A @ w, -30, 30)
        p = 1 / (1 + np.exp(-z))
        g = A.T @ (p - y) + pen * w
        H = (A * (p * (1 - p))[:, None]).T @ A + np.diag(pen) + 1e-9 * np.eye(d + 1)
        step = np.linalg.solve(H, g)
        w -= step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w


def predict_logit(w, Z):
    z = np.clip(w[0] + Z @ w[1:], -30, 30)
    return 1 / (1 + np.exp(-z))


# ---------------------------------------------------------------- model 2: gradient-boosted shallow trees (log loss, Newton leaves, binned)
def make_bins(X, nb):
    edges = []
    for j in range(X.shape[1]):
        u = np.unique(X[:, j])
        if len(u) <= nb:
            edges.append((u[:-1] + u[1:]) / 2 if len(u) > 1 else np.array([]))
        else:
            qs = np.unique(np.quantile(X[:, j], np.linspace(0, 1, nb + 1)[1:-1]))
            edges.append(qs)
    return edges


def apply_bins(X, edges):
    B = np.zeros(X.shape, dtype=np.int16)
    for j, e in enumerate(edges):
        B[:, j] = np.searchsorted(e, X[:, j], side="right") if len(e) else 0
    return B


def _build_tree(B, g, h, idx, depth, max_depth, min_leaf, l2, nbins):
    """Returns nested dict: leaf {'v': value} or split {'f','b','l','r'} (go left when bin <= b)."""
    G, H = g[idx].sum(), h[idx].sum()
    leaf = {"v": -G / (H + l2)}
    if depth >= max_depth or len(idx) < 2 * min_leaf:
        return leaf
    best = (1e-12, None, None)
    base = G * G / (H + l2)
    for f in range(B.shape[1]):
        col = B[idx, f]
        gh = np.bincount(col, weights=g[idx], minlength=nbins)
        hh = np.bincount(col, weights=h[idx], minlength=nbins)
        cn = np.bincount(col, minlength=nbins)
        cg, ch, cc = np.cumsum(gh), np.cumsum(hh), np.cumsum(cn)
        for b in range(nbins - 1):
            if cc[b] < min_leaf or len(idx) - cc[b] < min_leaf:
                continue
            gain = cg[b] ** 2 / (ch[b] + l2) + (G - cg[b]) ** 2 / (H - ch[b] + l2) - base
            if gain > best[0]:
                best = (gain, f, b)
    if best[1] is None:
        return leaf
    f, b = best[1], best[2]
    m = B[idx, f] <= b
    return {"f": f, "b": b, "l": _build_tree(B, g, h, idx[m], depth + 1, max_depth, min_leaf, l2, nbins),
            "r": _build_tree(B, g, h, idx[~m], depth + 1, max_depth, min_leaf, l2, nbins)}


def _tree_pred(t, B):
    out = np.zeros(len(B))
    stack = [(t, np.arange(len(B)))]
    while stack:
        node, ix = stack.pop()
        if "v" in node:
            out[ix] = node["v"]
        else:
            m = B[ix, node["f"]] <= node["b"]
            stack.append((node["l"], ix[m]))
            stack.append((node["r"], ix[~m]))
    return out


class GBT:
    def __init__(self, depth, trees, lr=0.1, min_leaf=100, l2=10.0, bins=32):
        self.depth, self.trees, self.lr, self.min_leaf, self.l2, self.nb = depth, trees, lr, min_leaf, l2, bins

    def fit(self, X, y):
        self.edges = make_bins(X, self.nb)
        B = apply_bins(X, self.edges)
        nbins = int(B.max()) + 1
        p0 = min(max(y.mean(), 1e-6), 1 - 1e-6)
        self.f0 = math.log(p0 / (1 - p0))
        F = np.full(len(y), self.f0)
        self.ts = []
        for _ in range(self.trees):
            p = 1 / (1 + np.exp(-np.clip(F, -30, 30)))
            g, h = p - y, np.maximum(p * (1 - p), 1e-6)
            t = _build_tree(B, g, h, np.arange(len(y)), 0, self.depth, self.min_leaf, self.l2, nbins)
            self.ts.append(t)
            F += self.lr * _tree_pred(t, B)
        return self

    def predict(self, X):
        B = apply_bins(X, self.edges)
        F = np.full(len(X), self.f0)
        for t in self.ts:
            F += self.lr * _tree_pred(t, B)
        return 1 / (1 + np.exp(-np.clip(F, -30, 30)))


def log_loss(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


# ---------------------------------------------------------------- decision rule and scoring
def select(rows, p, margin, k=MAX_PER_EVENT):
    """Indices of entries with model probability minus ask above the margin, at most k per event (largest margin first, ties by md5(market|look))."""
    by = {}
    for i, r in enumerate(rows):
        m = p[i] - r["ask"]
        if m > margin + 1e-12:
            by.setdefault(r["event"], []).append((-m, md5key(f"{r['market']}|{r['look']}"), i))
    out = []
    for e, v in by.items():
        out += [i for _, _, i in sorted(v)[:k]]
    return sorted(out)


def pf(nets):
    w = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return w / l if l > 0 else float("inf")


def attach_outcome(r, res):
    won = r["side"] == res[r["market"]]
    return {**r, "won": 1 if won else 0, "net": C.net_per_contract(won, r["ask"]), "fee": C.fee_per_contract(r["ask"]),
            "date": C.datetime.fromtimestamp(r["t"], C.timezone.utc).strftime("%Y-%m-%d")}


def summarize(rows, rng, B=BOOT):
    s = C.stats(rows, rng, B)
    if s["n"]:
        s["pf"] = pf([r["net"] for r in rows])
    return s


def calibration(p, y, ask, bins=10):
    """Deciles of model probability on the test rows: n, mean model p, win rate, mean ask."""
    order = np.argsort(p)
    out = []
    for ch in np.array_split(order, bins):
        if len(ch):
            out.append({"n": int(len(ch)), "p_hat": float(p[ch].mean()), "win": float(y[ch].mean()), "ask": float(ask[ch].mean())})
    return out


def perm_outcomes(y, bk, rng):
    """Shuffle outcomes within ask bucket (the CALIB1 buckets), across train and test together."""
    out = y.copy()
    for b in np.unique(bk):
        ix = np.where(bk == b)[0]
        out[ix] = y[rng.permutation(ix)]
    return out


# ---------------------------------------------------------------- stages
def prepare(with_test_outcomes):
    rows = attach_overround(load_rows())
    tr, te, inner_fit, inner_val, te_order = split_events(rows)
    res = json.load(open(LIQ1_DIR / "res.json"))
    for r in rows:
        r["_split"] = "train" if r["event"] in tr else "test"
    return rows, tr, te, inner_fit, inner_val, te_order, res


def census():
    rows, tr, te, ifit, ival, te_order, res = prepare(False)
    n = len(rows)
    miss = {"ov": sum(1 for r in rows if r.get("ov") is None) / n, "ttc (age looks)": sum(1 for r in rows if look_minutes(r["look"]) is None) / n,
            "vol zero": sum(1 for r in rows if r["vol"] <= 0) / n}
    print(f"{n} cheap entries, {len({r['event'] for r in rows})} events (COUNTS ONLY; no outcome read)")
    print("train events", len(tr), "test events", len(te), "inner fit", len(ifit), "inner val", len(ival))
    trr = [r for r in rows if r["event"] in tr]
    ter = [r for r in rows if r["event"] in te]
    print("train rows", len(trr), "test rows", len(ter), "close ts", min(r["t"] for r in ter), max(r["t"] for r in ter))
    print("missing / zero rates (share of rows):", {k: round(v, 3) for k, v in miss.items()})
    print("spread_c missing: 0 (always present); series count", len({r["series"] for r in rows}), "categories", len({r["cat"] for r in rows}))
    print("test rows per ask bucket:", {C.BUCKET_NAMES[b]: sum(1 for r in ter if r["bk"] == b) for b in range(5)})
    print("test rows by cat:", sorted(((c, sum(1 for r in ter if r["cat"] == c)) for c in {r["cat"] for r in ter}), key=lambda x: -x[1])[:8])


def fit_stage():
    rows, tr, te, ifit, ival, te_order, res = prepare(False)
    trr = [attach_outcome(r, res) for r in rows if r["event"] in tr]       # test outcomes are NOT attached
    ter = [r for r in rows if r["event"] in te]
    assert all("won" not in r for r in ter)
    spec = Spec(trr)
    Xtr, Ztr = spec.matrix(trr)
    ytr = np.array([r["won"] for r in trr], dtype=float)
    ifm = np.array([r["event"] in ifit for r in trr])
    # inner selection (time-ordered inside train): log loss on the last quarter of train events
    sel = {"logit": None, "gbt": None}
    cand = {"logit": [], "gbt": []}
    for lam in LOGIT_LAMBDAS:
        w = fit_logit(Ztr[ifm], ytr[ifm], lam)
        cand["logit"].append({"lam": lam, "val_logloss": log_loss(predict_logit(w, Ztr[~ifm]), ytr[~ifm])})
    for hp in GBT_GRID:
        m = GBT(**hp, **GBT_FIXED).fit(Xtr[ifm], ytr[ifm])
        cand["gbt"].append({**hp, "val_logloss": log_loss(m.predict(Xtr[~ifm]), ytr[~ifm])})
    for k in cand:
        sel[k] = min(cand[k], key=lambda c: c["val_logloss"])
    # refit on all of train and predict the test features
    w = fit_logit(Ztr, ytr, sel["logit"]["lam"])
    gb = GBT(sel["gbt"]["depth"], sel["gbt"]["trees"], **GBT_FIXED).fit(Xtr, ytr)
    Xte, Zte = spec.matrix(ter)
    preds = {"logit": predict_logit(w, Zte), "gbt": gb.predict(Xte)}
    base_rate = {"train_win": float(ytr.mean()), "train_price": float(np.mean([r["ask"] for r in trr]))}
    counts = {}
    for name, p in preds.items():
        for m in MARGINS:
            counts[f"{name}@{int(m*100)}c"] = len(select(ter, p, m))
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump({"selected_hp": sel, "candidates": cand, "selected_test_counts": counts, "base": base_rate, "train_n": len(trr), "test_n": len(ter)}, open(OUT / "fit.json", "w"), indent=1)
    print("inner candidates:", json.dumps(cand))
    print("selected:", sel)
    print("train base rates:", base_rate)
    print("SELECTED TEST TRADES (before any test outcome):", counts)
    return sel, counts


def score(force=False):
    path = WORKERS / "MODEL1_RESULT.json"
    if path.exists() and not force:
        raise SystemExit("already run: workers/MODEL1_RESULT.json exists (run once)")
    fit = json.load(open(OUT / "fit.json"))
    sel = fit["selected_hp"]
    rows, tr, te, ifit, ival, te_order, res = prepare(True)
    allr = [attach_outcome(r, res) for r in rows]
    trr = [r for r in allr if r["event"] in tr]
    ter = [r for r in allr if r["event"] in te]
    spec = Spec(trr)
    Xtr, Ztr = spec.matrix(trr)
    Xte, Zte = spec.matrix(ter)
    ytr = np.array([r["won"] for r in trr], dtype=float)
    yte = np.array([r["won"] for r in ter], dtype=float)
    aste = np.array([r["ask"] for r in ter])
    w = fit_logit(Ztr, ytr, sel["logit"]["lam"])
    gb = GBT(sel["gbt"]["depth"], sel["gbt"]["trees"], **GBT_FIXED).fit(Xtr, ytr)
    preds = {"logit": predict_logit(w, Zte), "gbt": gb.predict(Xte)}
    rng = np.random.default_rng(SEED)
    half = set(te_order[: len(te_order) // 2])
    netall = np.array([r["net"] for r in ter])
    out = {"train_n": len(trr), "test_n": len(ter), "test_events": len(te), "selected_hp": sel, "results": {}, "calibration": {}, "weights_logit": {}}
    out["weights_logit"] = {n: float(v) for n, v in zip(["intercept"] + spec.names, w)}
    bk_all = np.array([r["bk"] for r in allr])
    y_all = np.array([r["won"] for r in allr], dtype=float)
    ntr = len(trr)
    # allr is in file order; build train/test index maps for the permutation (outcomes shuffled in ask bucket across the whole table)
    idx_tr = [i for i, r in enumerate(allr) if r["event"] in tr]
    idx_te = [i for i, r in enumerate(allr) if r["event"] in te]
    for name, p in preds.items():
        out["calibration"][name] = calibration(p, yte, aste)
        for m in MARGINS:
            ix = select(ter, p, m)
            chosen = [ter[i] for i in ix]
            whole = summarize(chosen, rng)
            h1 = summarize([r for r in chosen if r["event"] in half], rng)
            h2 = summarize([r for r in chosen if r["event"] not in half], rng)
            key = f"{name}@{int(round(m*100))}c"
            out["results"][key] = {"all": whole, "H1": h1, "H2": h2}
            # permutation baseline: same hyperparameters, refit on shuffled outcomes, same rule, statistic = mean net of the selected test trades
            obs = whole.get("net") if whole["n"] else None
            exceed, done = 0, 0
            for _ in range(N_PERM[name]):
                yp = perm_outcomes(y_all, bk_all, rng)
                ytr_p, yte_p = yp[idx_tr], yp[idx_te]
                if name == "logit":
                    pp = predict_logit(fit_logit(Ztr, ytr_p, sel["logit"]["lam"]), Zte)
                else:
                    pp = GBT(sel["gbt"]["depth"], sel["gbt"]["trees"], **GBT_FIXED).fit(Xtr, ytr_p).predict(Xte)
                sx = select(ter, pp, m)
                done += 1
                if len(sx) >= MIN_PERM_TRADES and obs is not None:
                    nets = [yte_p[i] - ter[i]["ask"] - ter[i]["fee"] for i in sx]
                    if sum(nets) / len(nets) >= obs:
                        exceed += 1
            out["results"][key]["perm_p"] = (exceed + 1) / (done + 1)
            out["results"][key]["perm_n"] = done
            w_ = out["results"][key]
            if whole["n"] < MIN_TRADES:
                w_["verdict"] = "NOT_ENOUGH_DATA"
            elif not (whole["net"] > 0 and whole["pf"] >= PF_BAR):
                w_["verdict"] = "FALSIFIED"
            elif h1["n"] and h2["n"] and h1["net"] > 0 and h2["net"] > 0 and w_["perm_p"] < PERM_P:
                w_["verdict"] = "LEAD"
            else:
                w_["verdict"] = "FALSIFIED"
    out["control_all_test"] = summarize(ter, rng)
    path.write_text(json.dumps(out, indent=1))
    return out


def fmt(s):
    if not s.get("n"):
        return "n=0"
    return (f"n={s['n']} ev={s['events']} win={100*s['win']:.2f}% px={100*s['price']:.2f}c w-p={100*s['excess']:+.2f}c "
            f"net={100*s['net']:+.2f}c [{100*s['lo']:+.2f},{100*s['hi']:+.2f}] PF={s['pf']:.2f}")


def report(out):
    print(f"train {out['train_n']} test {out['test_n']} rows ({out['test_events']} events); control (all test rows) {fmt(out['control_all_test'])}")
    for k, v in out["results"].items():
        print(f"{k:10s} {v['verdict']}  perm_p={v['perm_p']:.4f} (B={v['perm_n']})\n   all: {fmt(v['all'])}\n   H1: {fmt(v['H1'])}\n   H2: {fmt(v['H2'])}")
    for name, cal in out["calibration"].items():
        print(f"calibration {name} (test deciles of model p): n, p_hat, win, ask")
        for c in cal:
            print(f"   {c['n']:5d} {100*c['p_hat']:6.2f}% {100*c['win']:6.2f}% {100*c['ask']:6.2f}c")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "census":
        census()
    elif cmd == "fit":
        fit_stage()
    elif cmd == "score":
        report(score())
    else:
        print(__doc__)
