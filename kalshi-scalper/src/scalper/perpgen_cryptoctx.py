#!/usr/bin/env python3
"""PERPGEN CRYPTOCTX worker: CRYPTO group, rules with at least one CONTEXT atom (funding, time, cross-asset leaders).
Research only; no order, no key. Follows workers/PERPGEN_PROTOCOL.md exactly (see workers/PERPGEN_CRYPTOCTX_AMENDMENT.md for the one
counting defect found). Vectorised numpy; the audit (audit_*) is a separate plain-loop implementation.

    python3 -I src/scalper/perpgen_cryptoctx.py discover <first_run> <last_run>   # ledger first, then score discovery, freeze survivors
    python3 -I src/scalper/perpgen_cryptoctx.py validate <run> [<run> ...]        # only after PERPGEN_FROZEN_CRYPTOCTX_RUN<nn>.json is committed

Conventions (all from the protocol, restated where it left a detail open; every such choice is recorded here before any result):
 * bar ts = candle END time; a decision at quarter hour t reads bars with ts <= t; entry fill = close quote of bar ts == t+60
   (long at ask, short at bid); exit = opposite side close quote of the first usable bar with ts in [t+60+h, t+60+h+300].
 * region of a trade = region of the bar START (ts-60) of its entry bar and of its exit bar; both must lie in the stage's region.
 * a signal at decision time t is ignored if t < the exit ts of the ticker's open position (a 15 minute hold therefore blocks the
   next quarter hour: it exits 960 s after t).
 * fill-quote defect: spread above min(100 bps, 10 x the ticker's discovery median) at the entry OR the exit fill drops the trade.
 * window coverage: a window of w minutes needs >= ceil(0.9 w) present minutes; returns need both endpoints present.
 * vlr uses +1 dollar smoothing: log((S + 1) / (A * w + 1)) with S the window sum and A the trailing 1,440 minute mean per minute.
 * funding features read the last rows with funding_time ts <= t (fr_avg3 needs 3 rows); mtf uses the 04/12/20 UTC calendar
   (all dev dates precede the 2026-11-01 clock change).
"""
import sys, os, json, gzip, math, hashlib, random, time, itertools
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import perpdata as pd_  # noqa: E402

ROOT = pd_.ROOT
LEDGER = os.path.join(ROOT, "workers", "perpgen_ledger")
GROUP = "CRYPTOCTX"
CRYPTO = pd_.universe_frozen()["CRYPTO"]
FEE12, FEE24 = 0.0012, 0.0024
HORIZONS = [15, 30, 60, 120, 240, 480, 1440]
LEVELS = [0.10, 0.25, 0.50, 0.75, 0.90]
NUM = ["r5", "r15", "r60", "r240", "r1440", "vol60", "vol240", "volratio", "rng60", "rng240", "sp", "spr",
       "vlr15", "vlr60", "doi60", "doi240", "tvm", "fr_last", "fr_chg", "fr_avg3",
       "dhi240", "dlo240", "dhi1440", "dlo1440", "pir1440",
       "xbtc15", "xbtc60", "xbtc240", "xeth60", "xeth240", "xgold60", "xus500_60", "rel_btc60", "rel_btc240"]
CAT = {"hod4": list(range(6)), "dow": list(range(7)), "wkend": [0, 1], "mtf": list(range(4))}
FEATS = NUM + list(CAT)
CONTEXT = {"fr_last", "fr_chg", "fr_avg3", "xbtc15", "xbtc60", "xbtc240", "xeth60", "xeth240", "xgold60", "xus500_60", "rel_btc60", "rel_btc240",
           "hod4", "dow", "wkend", "mtf"}
LEADERS = {"KXBTCPERP": "btc", "KXETHPERP": "eth", "KXGOLDPERP": "gold", "KXUS500PERP": "us500"}


# ---------------------------------------------------------------- data
def _grid(rows):
    t0, t1 = int(rows[0]["ts"]), int(rows[-1]["ts"])
    n = (t1 - t0) // 60 + 1
    A = {k: np.full(n, np.nan) for k in ("bid", "ask", "px", "vol", "oi")}
    served = np.zeros(n, bool)
    ts = np.array([r["ts"] for r in rows], dtype=np.int64)
    ix = ((ts - t0) // 60).astype(int)
    served[ix] = True
    for k, f in (("bid", "bid_c"), ("ask", "ask_c"), ("px", "px_c"), ("oi", "oi")):
        A[k][ix] = [np.nan if r[f] is None else r[f] for r in rows]
    A["vol"][ix] = [0.0 if r["vol_usd"] is None else r["vol_usd"] for r in rows]
    ok = np.zeros(n, bool)
    ok[ix] = [bool(r["ok"]) for r in rows]
    mid = np.where(ok, (A["bid"] + A["ask"]) / 2, np.nan)
    spb = np.where(ok, (A["ask"] - A["bid"]) / mid * 1e4, np.nan)
    return dict(t0=t0, n=n, bid=A["bid"], ask=A["ask"], px=A["px"], vol=A["vol"], oi=A["oi"], served=served, ok=ok, mid=mid, sp=spb)


def _roll(s, w, f, frac=0.9):
    r = s.rolling(w, min_periods=math.ceil(frac * w))
    return getattr(r, f)()


def own_features(g):
    """Features computable from one ticker's own grid (all arrays over the grid, index i = bar ending t0 + 60 i)."""
    m = pd.Series(g["mid"]); lm = np.log(m)
    F = {}
    cnt = m.notna().astype(float)
    for w in (5, 15, 60, 240, 1440):
        full = _roll(cnt, w, "sum") >= math.ceil(0.9 * w) if w > 1 else cnt > 0
        r = (lm - lm.shift(w)) * 1e4
        F["r%d" % w] = r.where(full & (_roll(cnt, w, "sum") >= 0) & m.notna() & m.shift(w).notna())
    ret = lm - lm.shift(1)
    v60, v240, v1440 = _roll(ret, 60, "std"), _roll(ret, 240, "std"), _roll(ret, 1440, "std")
    F["vol60"], F["vol240"], F["volratio"] = v60, v240, v60 / v1440
    for w in (60, 240):
        F["rng%d" % w] = (_roll(m, w, "max") - _roll(m, w, "min")) / m
    sp = pd.Series(g["sp"])
    F["sp"] = sp
    F["spr"] = sp / _roll(sp, 1440, "median")
    vol = pd.Series(g["vol"])
    A = _roll(vol, 1440, "mean")
    for w in (15, 60):
        S = _roll(vol, w, "sum")
        F["vlr%d" % w] = np.log((S + 1) / (A * w + 1))
    oi = pd.Series(g["oi"]); srv = pd.Series(g["served"].astype(float))
    for w in (60, 240):
        cov = _roll(srv, w, "sum") >= math.ceil(0.9 * w)
        F["doi%d" % w] = np.log(oi / oi.shift(w)).where(cov)
    px = pd.Series(g["px"]).ffill(limit=4)
    F["tvm"] = (px / m - 1) * 1e4
    for w, nm in ((240, "240"), (1440, "1440")):
        hi, lo = _roll(m, w, "max"), _roll(m, w, "min")
        F["dhi" + nm] = (m / hi - 1) * 1e4
        F["dlo" + nm] = (m / lo - 1) * 1e4
        if w == 1440:
            F["pir1440"] = ((m - lo) / (hi - lo)).where(hi > lo)
    return {k: np.asarray(v, float) for k, v in F.items()}


def build(stage, frozen_id=None):
    """Dataset of decision rows for the stage (stage 'discovery' reads discovery files only; 'validation' needs the frozen file and
    reads discovery + validation so windows can look back; rows returned are those whose DECISION time is in the stage)."""
    cu = pd_.cuts(); costs = json.load(open(pd_.FROZEN))["ticker_costs"]
    stages = ["discovery"] if stage == "discovery" else ["discovery", "validation"]
    def rows_of(tk, kind="1m"):
        out = []
        for s in stages:
            out += pd_.load_stage(tk, s, kind, frozen_id=frozen_id)
        return out
    G, FT, FUND = {}, {}, {}
    need = list(CRYPTO) + [t for t in LEADERS if t not in CRYPTO]
    for tk in need:
        rows = rows_of(tk)
        G[tk] = _grid(rows)
        FT[tk] = own_features(G[tk])
        fr = rows_of(tk, "funding")
        FUND[tk] = (np.array([r["ts"] for r in fr], dtype=np.int64), np.array([r["funding_rate"] for r in fr]))
    def lead_ret(L, w):                       # leader log return in bps over w minutes on the leader's own grid (as pandas series by ts)
        g = G[L]; m = pd.Series(g["mid"]); lm = np.log(m)
        cnt = m.notna().astype(float)
        ok = (_roll(cnt, w, "sum") >= math.ceil(0.9 * w)) & m.notna() & m.shift(w).notna()
        r = ((lm - lm.shift(w)) * 1e4).where(ok)
        r.index = g["t0"] + 60 * np.arange(g["n"])
        return r
    LR = {}
    for L, nm in LEADERS.items():
        for w in (15, 60, 240):
            LR[(nm, w)] = lead_ret(L, w)
    D = dict(tk=[], t=[], vals={f: [] for f in FEATS}, tid=[], stage=[])
    ds = {}
    for ti, tk in enumerate(CRYPTO):
        g = G[tk]; c = cu[tk]
        t_first = g["t0"]; t_last = g["t0"] + 60 * (g["n"] - 1)
        ts = np.arange(((t_first + 899) // 900) * 900, t_last + 1, 900)
        i = ((ts - g["t0"]) // 60).astype(int)
        keep = g["ok"][i]                                 # usable quote at t
        # decision rows are those whose entry bar start (= t) lies in the stage
        lo = 0 if stage == "discovery" else c["validation_ts"]
        hi = c["validation_ts"] if stage == "discovery" else c["holdout_ts"]
        keep &= (ts >= lo) & (ts < hi)
        ts, i = ts[keep], i[keep]
        F = {f: FT[tk][f][i] for f in NUM if f in FT[tk]}
        # funding
        fts, fr = FUND[tk]
        k = np.searchsorted(fts, ts, side="right") - 1
        frb = fr * 1e4
        F["fr_last"] = np.where(k >= 0, frb[np.clip(k, 0, None)], np.nan) if len(fr) else np.full(len(ts), np.nan)
        F["fr_chg"] = np.where(k >= 1, frb[np.clip(k, 0, None)] - frb[np.clip(k - 1, 0, None)], np.nan) if len(fr) else np.full(len(ts), np.nan)
        F["fr_avg3"] = np.where(k >= 2, (frb[np.clip(k, 0, None)] + frb[np.clip(k - 1, 0, None)] + frb[np.clip(k - 2, 0, None)]) / 3, np.nan) if len(fr) else np.full(len(ts), np.nan)
        # leaders (a ticker does not lead itself; a leader value exists only where the leader's own loaded data covers t)
        def lead(nm, w):
            s = LR[(nm, w)]
            return s.reindex(ts).to_numpy()
        nan = np.full(len(ts), np.nan)
        F["xbtc15"] = nan if tk == "KXBTCPERP" else lead("btc", 15)
        F["xbtc60"] = nan if tk == "KXBTCPERP" else lead("btc", 60)
        F["xbtc240"] = nan if tk == "KXBTCPERP" else lead("btc", 240)
        F["xeth60"] = nan if tk == "KXETHPERP" else lead("eth", 60)
        F["xeth240"] = nan if tk == "KXETHPERP" else lead("eth", 240)
        F["xgold60"] = lead("gold", 60)
        F["xus500_60"] = lead("us500", 60)
        F["rel_btc60"] = nan if tk == "KXBTCPERP" else F["r60"] - F["xbtc60"]
        F["rel_btc240"] = nan if tk == "KXBTCPERP" else F["r240"] - F["xbtc240"]
        # time
        hh = (ts // 3600) % 24
        F["hod4"] = (hh // 4).astype(float)
        F["dow"] = (((ts // 86400) + 3) % 7).astype(float)         # 1970-01-01 was a Thursday; Monday = 0
        F["wkend"] = (F["dow"] >= 5).astype(float)
        mins = (ts % 86400) / 60
        nxt = np.min(np.stack([(h * 60 - mins) % 1440 for h in (4, 12, 20)]), axis=0)
        nxt = np.where(nxt == 0, 480, nxt)                          # a decision exactly at a funding time looks to the next one
        F["mtf"] = np.where(nxt < 30, 0, np.where(nxt < 120, 1, np.where(nxt < 240, 2, 3))).astype(float)
        # trades per horizon
        sp_lim = min(100.0, 10 * costs[tk]["median_spread_bp_discovery"])
        trades = {}
        stats = dict(rows=len(ts), void_entry=0, void_exit=0, defect=0, region=0)
        for h in HORIZONS:
            nr = len(ts)
            ei = i + 1
            e_ok = np.zeros(nr, bool); e_ok[:] = (ei < g["n"])
            e_ok &= g["ok"][np.minimum(ei, g["n"] - 1)]
            e_sp = g["sp"][np.minimum(ei, g["n"] - 1)]
            xi = np.full(nr, -1)
            for j in range(0, 6):                              # first usable bar within the next 5 minutes (ts offsets 0..5 minutes)
                cand = i + 1 + h + j
                okc = (cand < g["n"]) & (xi < 0)
                okc &= g["ok"][np.minimum(cand, g["n"] - 1)]
                xi = np.where(okc, cand, xi)
            x_ok = xi >= 0
            xs = np.maximum(xi, 0)
            ts_e = g["t0"] + 60 * ei; ts_x = g["t0"] + 60 * xs
            ent_start, ext_start = ts_e - 60, ts_x - 60
            reg_ok = (ext_start >= lo) & (ext_start < hi) & (ent_start >= lo) & (ent_start < hi)
            defect = (e_sp > sp_lim) | (g["sp"][xs] > sp_lim)
            valid = e_ok & x_ok & reg_ok & ~defect
            stats["void_entry"] += int((~e_ok).sum()); stats["void_exit"] += int((e_ok & ~x_ok).sum())
            stats["region"] += int((e_ok & x_ok & ~reg_ok).sum()); stats["defect"] += int((e_ok & x_ok & reg_ok & defect).sum())
            ask_e, bid_e = g["ask"][np.minimum(ei, g["n"] - 1)], g["bid"][np.minimum(ei, g["n"] - 1)]
            ask_x, bid_x = g["ask"][xs], g["bid"][xs]
            with np.errstate(all="ignore"):
                pl = bid_x / ask_e - 1                          # long: buy ask, sell bid
                ps = -(ask_x / bid_e - 1)                       # short: sell bid, buy ask
            # funding settlements with funding_time in (entry ts, exit ts]
            a = np.searchsorted(fts, ts_e, side="right"); b = np.searchsorted(fts, ts_x, side="right")
            cs = np.concatenate([[0.0], np.cumsum(fr)]) if len(fr) else np.zeros(1)
            fsum = cs[b] - cs[a]
            trades[h] = dict(valid=valid, pl=np.where(valid, pl, 0), ps=np.where(valid, ps, 0), fsum=np.where(valid, fsum, 0),
                             ts_e=ts_e, ts_x=ts_x)
        ds[tk] = dict(ts=ts, F=F, trades=trades, stats=stats)
    # concatenate
    d = dict(tk=[], ts=[], N=0)
    cat = lambda xs: np.concatenate(xs) if xs else np.array([])
    out = dict(ts=cat([ds[tk]["ts"] for tk in CRYPTO]), tid=cat([np.full(len(ds[tk]["ts"]), ti) for ti, tk in enumerate(CRYPTO)]).astype(int))
    out["F"] = {f: cat([ds[tk]["F"][f] for tk in CRYPTO]) for f in FEATS}
    out["tr"] = {h: {k: cat([ds[tk]["trades"][h][k] for tk in CRYPTO]) for k in ("valid", "pl", "ps", "fsum", "ts_e", "ts_x")} for h in HORIZONS}
    out["date"] = out["ts"] // 86400 - int(out["ts"].min() // 86400)
    out["stats"] = {tk: ds[tk]["stats"] for tk in CRYPTO}
    out["N"] = len(out["ts"])
    return out


# ---------------------------------------------------------------- cuts and atoms
def cuts_for(ds_disc):
    """Quantile cut per (ticker, feature, level) from DISCOVERY decision-time values only."""
    C = {}
    for ti, tk in enumerate(CRYPTO):
        m = ds_disc["tid"] == ti
        for f in NUM:
            v = ds_disc["F"][f][m]; v = v[~np.isnan(v)]
            C["%s|%s" % (tk, f)] = [float(np.quantile(v, q)) if len(v) else None for q in LEVELS]
    return C


def atoms_all():
    out = []
    for f in NUM:
        for op in (">=", "<="):
            for q in LEVELS:
                out.append("%s%sq%.2f" % (f, op, q))
    for f, vals in CAT.items():
        for v in vals:
            out.append("%s==%d" % (f, v))
    return out


def atom_arrays(ds, C):
    A = {}
    for a in atoms_all():
        if "==" in a:
            f, v = a.split("=="); A[a] = ds["F"][f] == float(v)
            continue
        op = ">=" if ">=" in a else "<="
        f, qs = a.split(op); q = float(qs[1:]); qi = LEVELS.index(q)
        cut = np.array([C["%s|%s" % (CRYPTO[t], f)][qi] if C["%s|%s" % (CRYPTO[t], f)][qi] is not None else np.nan for t in range(len(CRYPTO))])[ds["tid"]]
        x = ds["F"][f]
        with np.errstate(invalid="ignore"):
            A[a] = (x >= cut) if op == ">=" else (x <= cut)
        A[a] &= ~np.isnan(x) & ~np.isnan(cut)
    return A


# ---------------------------------------------------------------- scoring
def entries(ds, mask, h):
    """Row indices of accepted entries (one position per ticker; a signal before the open position's exit is ignored)."""
    tr = ds["tr"][h]
    idx = np.flatnonzero(mask & tr["valid"])
    if len(idx) < 2:
        return idx, 0
    same = ds["tid"][idx[1:]] == ds["tid"][idx[:-1]]
    conflict = same & (ds["ts"][idx[1:]] < tr["ts_x"][idx[:-1]])
    if not conflict.any():
        return idx, 0
    keep = []; last_x = {}; ign = 0
    ts, tid, tx = ds["ts"], ds["tid"], tr["ts_x"]
    for j in idx.tolist():
        k = tid[j]
        if ts[j] < last_x.get(k, -1):
            ign += 1; continue
        keep.append(j); last_x[k] = tx[j]
    return np.array(keep, dtype=int), ign


def trade_nets(ds, idx, h, direction, fee=FEE12, sign=1):
    tr = ds["tr"][h]
    g = tr["pl"][idx] if direction == "long" else tr["ps"][idx]
    f = -sign * tr["fsum"][idx] if direction == "long" else sign * tr["fsum"][idx]
    return g + f - 2 * fee


def pf(x):
    w = x[x > 0].sum(); l = -x[x < 0].sum()
    return math.inf if l == 0 and w > 0 else (0.0 if l == 0 else w / l)


def halves(date):
    med = np.median(date)
    return date <= med


def metrics(ds, idx, h, direction, fee=FEE12):
    net = trade_nets(ds, idx, h, direction, fee)
    d = ds["date"][idx]
    return net, d


def disc_pass(ds, idx, h, direction):
    """Returns (stage reached 0..6, pf12, n). Order: n>=200, dates>=20, PF>=1.3, mean24>0, halves, concentration."""
    n = len(idx)
    if n < 200:
        return 0, None, n
    net = trade_nets(ds, idx, h, direction); d = ds["date"][idx]
    p = pf(net)
    if len(np.unique(d)) < 20:
        return 1, p, n
    if p < 1.3:
        return 2, p, n
    if trade_nets(ds, idx, h, direction, FEE24).mean() <= 0:
        return 3, p, n
    hf = halves(d)
    if hf.all() or (~hf).all() or pf(net[hf]) <= 1.0 or pf(net[~hf]) <= 1.0:
        return 4, p, n
    tot = net.sum()
    ds_ = np.bincount(d, weights=net)
    if tot <= 0 or ds_.max() > 0.25 * tot:
        return 5, p, n
    return 6, p, n


def canon(atoms, direction, h):
    return "&".join(sorted(atoms, key=lambda a: a.replace("==", "<").replace(">=", "<").split("<")[0])) + "|%s|%d" % (direction, h)


def parse(rule):
    a, d, h = rule.split("|")
    return a.split("&"), d, int(h)


def draw(rng):
    while True:
        k = rng.choices([1, 2, 3], [0.2, 0.4, 0.4])[0]
        fs = rng.sample(FEATS, k)
        if not any(f in CONTEXT for f in fs):
            continue
        at = []
        for f in fs:
            if f in CAT:
                at.append("%s==%d" % (f, rng.choice(CAT[f])))
            else:
                at.append("%s%sq%.2f" % (f, rng.choice([">=", "<="]), rng.choice(LEVELS)))
        return canon(at, rng.choice(["long", "short"]), rng.choice(HORIZONS))


def existing_ids():
    s = set()
    if os.path.isdir(LEDGER):
        for fn in os.listdir(LEDGER):
            if fn.endswith(".ids.gz") and "CRYPTO" in fn:
                with gzip.open(os.path.join(LEDGER, fn), "rt") as f:
                    s.update(l.rstrip("\n") for l in f)
    return s


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def cuts_file(ds_disc):
    path = os.path.join(ROOT, "workers", "PERPGEN_CRYPTOCTX_CUTS.json")
    if os.path.exists(path):
        return json.load(open(path))["cuts"]
    C = cuts_for(ds_disc)
    json.dump(dict(group=GROUP, levels=LEVELS, note="quantile cuts of each ticker's own DISCOVERY decision-time feature values, computed once", cuts=C),
              open(path, "w"), indent=0, sort_keys=True)
    open(path + ".sha256", "w").write(sha(path) + "\n")
    return C


def run_discovery(run, ds, A, bar=500, target=5000):
    seed = 1000 + run
    rng = random.Random(seed)
    seen = existing_ids()
    new = []
    tries = 0
    local = set()
    while len(new) < target and tries < target * 200:
        tries += 1
        r = draw(rng)
        if r in seen or r in local:
            continue
        local.add(r); new.append(r)
    os.makedirs(LEDGER, exist_ok=True)
    lp = os.path.join(LEDGER, "RUN%02d_%s.ids.gz" % (run, GROUP))
    if os.path.exists(lp):
        raise SystemExit("ledger exists: " + lp)
    stagecount = [0] * 7; surv = []; best = (0, None); best_pass = None; nvoid = 0
    with gzip.open(lp, "wt") as lf:
        for b in range(0, len(new), bar):
            batch = new[b:b + bar]
            lf.write("\n".join(batch) + "\n"); lf.flush()          # ledger line is on disk BEFORE the batch is scored
            for r in batch:
                atoms, d, h = parse(r)
                m = A[atoms[0]]
                for a in atoms[1:]:
                    m = m & A[a]
                idx, ign = entries(ds, m, h)
                s, p, n = disc_pass(ds, idx, h, d)
                stagecount[s] += 1
                if n >= 200 and p is not None and p > best[0]:
                    best = (p, r)
                if s == 6:
                    surv.append(dict(rule=r, n=int(n), pf=p, idx=idx))
    return new, stagecount, best, surv


def jaccard(a, b):
    sa, sb = set(a.tolist()), set(b.tolist())
    return len(sa & sb) / max(1, len(sa | sb))


def cluster(surv, th):
    keep = []
    for s in sorted(surv, key=lambda s: -s["pf"]):
        _, d, h = parse(s["rule"])
        if all(not (parse(k["rule"])[1:] == (d, h) and jaccard(s["idx"], k["idx"]) >= th) for k in keep):
            keep.append(s)
    return keep


def main():
    cmd = sys.argv[1]
    if cmd == "discover":
        r0, r1 = int(sys.argv[2]), int(sys.argv[3])
        t0 = time.time()
        ds = build("discovery")
        C = cuts_file(ds)
        A = atom_arrays(ds, C)
        print("built discovery rows", ds["N"], "in %.0fs" % (time.time() - t0), flush=True)
        os.makedirs(LEDGER, exist_ok=True)
        for run in range(r0, r1 + 1):
            t1 = time.time()
            new, sc, best, surv = run_discovery(run, ds, A)
            cl = cluster(surv, 0.9)
            fid = "CRYPTOCTX_RUN%02d" % run
            fz = os.path.join(ROOT, "workers", "PERPGEN_FROZEN_%s.json" % fid)
            body = dict(id=fid, group=GROUP, run=run, seed=1000 + run, n_scored=len(new),
                        survivors=[dict(rule=s["rule"], n=s["n"], pf12=s["pf"]) for s in cl], n_before_clustering=len(surv))
            json.dump(body, open(fz, "w"), indent=1)
            open(fz + ".sha256", "w").write(sha(fz) + "\n")
            names = ["n<200", "dates<20", "PF<1.3", "mean24<=0", "half PF<=1", "date>25%", "survived"]
            print("RUN%02d N=%d  %s  best PF(n>=200)=%s %s  clusters=%d  %.0fs" % (
                run, len(new), " ".join("%s:%d" % (a, b) for a, b in zip(names, sc)),
                None if best[1] is None else "%.3f" % best[0], best[1], len(cl), time.time() - t1), flush=True)
            open(os.path.join(ROOT, "workers", "perpgen_ledger", "cryptoctx_run_summary.txt"), "a").write(
                "RUN%02d N=%d disc_survivors=%d clusters=%d best_pf=%s best_rule=%s stages=%s\n" % (run, len(new), len(surv), len(cl), None if best[1] is None else "%.3f" % best[0], best[1], sc))
    else:
        raise SystemExit("unknown command")


if __name__ == "__main__":
    main()
