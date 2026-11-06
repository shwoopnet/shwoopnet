#!/usr/bin/env python3
"""PERPGEN generator, NONCRYPTO slice (gold, silver, copper, US 500, Tech 100, WTI). Research only: no order, no key, no live code.
Registered protocol: workers/PERPGEN_PROTOCOL.md (bars, grammar, features, cuts are NOT changed here; interpretations and the one
miscount are disclosed in workers/PERPGEN_NONCRYPTO_AMENDMENT.md).

    python3 -I src/scalper/perpgen_noncrypto.py run <nn> [--n 5000]     one RUN: ledger first, discovery, freeze, (validation + audit for survivors)
    python3 -I src/scalper/perpgen_noncrypto.py selfcheck                 data build + feature sanity, no scoring

Vectorised numpy; the independent plain-loop recompute used by audit A1 is in perpgen_noncrypto_audit.py (shares no code).
"""
import gzip, hashlib, json, math, os, random, sys, time, glob, warnings
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from scalper import perpdata as pdt  # noqa: E402

ROOT = pdt.ROOT
LEDGER_DIR = os.path.join(ROOT, "workers", "perpgen_ledger")
GROUP = "NONCRYPTO"
TARGETS = pdt.universe_frozen()[GROUP]
LEADERS = {"btc": "KXBTCPERP", "eth": "KXETHPERP", "gold": "KXGOLDPERP", "us500": "KXUS500PERP"}
CUTS = pdt.cuts()
HORIZONS = [15, 30, 60, 120, 240, 480, 1440]                      # minutes
NUM = ["r5", "r15", "r60", "r240", "r1440", "vol60", "vol240", "volratio", "rng60", "rng240", "sp", "spr", "vlr15", "vlr60", "doi60", "doi240",
       "tvm", "fr_last", "fr_chg", "fr_avg3", "dhi240", "dlo240", "dhi1440", "dlo1440", "pir1440",
       "xbtc15", "xbtc60", "xbtc240", "xeth60", "xeth240", "xgold60", "xus500_60", "rel_btc60", "rel_btc240"]
CAT = {"hod4": 6, "dow": 7, "wkend": 2, "mtf": 4}
LEVELS = [0.10, 0.25, 0.50, 0.75, 0.90]
ATOMS = [(f, "n", op, q) for f in NUM for op in (0, 1) for q in LEVELS] + [(f, "c", 2, v) for f, k in CAT.items() for v in range(k)]
FEE12, FEE24, FEE5 = 0.0012, 0.0024, 0.0005
MINDATA = 0.9


def atom_name(a):
    f, k, op, v = a
    return "%s%sq%02d" % (f, ">=" if op == 0 else "<=", int(round(v * 100))) if k == "n" else "%s==%d" % (f, v)


def rule_name(atoms, d, h):
    return "&".join(sorted((atom_name(ATOMS[i]) for i in atoms), key=lambda s: (s.split(">=")[0].split("<=")[0].split("==")[0], s))) + "|%s|%d" % ("long" if d == 0 else "short", HORIZONS[h])


# ------------------------------------------------------------------ grids
class Grid:
    def __init__(self, tk, rows, fund):
        ts = np.array([r["ts"] for r in rows]).astype(np.int64)
        self.tk, self.ts0 = tk, int(ts[0])
        n = int((ts[-1] - ts[0]) // 60 + 1)
        self.n = n
        ix = ((ts - ts[0]) // 60).astype(np.int64)
        def col(k):
            a = np.full(n, np.nan)
            a[ix] = np.array([np.nan if r[k] is None else r[k] for r in rows])
            return a
        self.have = np.zeros(n, bool); self.have[ix] = True
        self.bid, self.ask = col("bid_c"), col("ask_c")
        self.ok = np.isfinite(self.bid) & np.isfinite(self.ask) & (self.ask >= self.bid)
        self.bid[~self.ok] = np.nan; self.ask[~self.ok] = np.nan
        self.mid = (self.bid + self.ask) / 2
        self.sp = (self.ask - self.bid) / self.mid * 1e4
        self.px = col("px_c"); self.vol = col("vol_usd"); self.oi = col("oi")
        self.cok = np.r_[0, np.cumsum(self.ok)]
        self.chave = np.r_[0, np.cumsum(self.have)]
        lr = np.full(n, np.nan); lr[1:] = np.log(self.mid[1:] / self.mid[:-1])
        v = np.isfinite(lr)
        self.cv = np.r_[0, np.cumsum(v)]; self.cs = np.r_[0, np.cumsum(np.where(v, lr, 0))]; self.cs2 = np.r_[0, np.cumsum(np.where(v, lr * lr, 0))]
        self.cvol = np.r_[0, np.cumsum(np.nan_to_num(self.vol))]
        self.csp_ok = self.cok
        self.fund = fund
        self.ft = np.array([f["ts"] for f in self.fund]).astype(np.int64)
        self.fr = np.array([f["funding_rate"] for f in self.fund])
        self.fc = np.r_[0, np.cumsum(self.fr)]
        self.holdout_ts = CUTS[tk]["holdout_ts"]; self.validation_ts = CUTS[tk]["validation_ts"]

    def idx(self, ts):
        i = (np.asarray(ts) - self.ts0) // 60
        return i

    def okw(self, I, w, cum=None):
        cum = self.cok if cum is None else cum
        lo = I + 1 - w
        c = np.where(lo >= 0, cum[I + 1] - cum[np.clip(lo, 0, None)], -1)
        return c >= MINDATA * w - 1e-9


def ret(g, I, w):
    I = np.asarray(I); out = np.full(len(I), np.nan)
    inb = (I >= w) & (I < g.n)
    Ic = np.clip(I, 0, g.n - 1)
    a, b = g.mid[Ic], g.mid[np.clip(I - w, 0, None)]
    good = inb & np.isfinite(a) & np.isfinite(b) & g.okw(Ic, w)
    out[good] = 1e4 * np.log(a[good] / b[good])
    return out


def vol(g, I, w):
    out = np.full(len(I), np.nan); lo = I + 1 - w
    good = lo >= 0
    Ic, loc = I[good], lo[good]
    n = g.cv[Ic + 1] - g.cv[loc]; s = g.cs[Ic + 1] - g.cs[loc]; s2 = g.cs2[Ic + 1] - g.cs2[loc]
    with np.errstate(all="ignore"):
        var = (s2 - s * s / n) / (n - 1)
        o = np.where((n >= MINDATA * w - 1e-9) & (n > 2) & (var >= 0), 1e4 * np.sqrt(np.maximum(var, 0)), np.nan)
    out[good] = o
    return out


def roll(g, I, w, arr, fn):
    """rolling nanmax / nanmin / nanmedian of arr over the w minutes ending at I (needs 90 percent of the minutes with a quote)."""
    out = np.full(len(I), np.nan)
    good = (I >= w - 1) & g.okw(I, w)
    if good.any():
        win = np.lib.stride_tricks.sliding_window_view(arr, w)[I[good] - w + 1]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            out[good] = fn(win, axis=1)
    return out


def last_px(g, I):
    out = np.full(len(I), np.nan)
    for k in range(4, -1, -1):
        v = g.px[np.clip(I - k, 0, None)]
        out = np.where(np.isfinite(v), v, out)               # later offsets (smaller k) overwrite: ends with the most recent trade
    return out


def features(g, I, xs):
    """All 34 numeric + 4 categorical features at minute-grid indices I (decision times). xs: dict of leader Grids."""
    t = g.ts0 + 60 * I
    F = {}
    for w in (5, 15, 60, 240, 1440):
        F["r%d" % w] = ret(g, I, w)
    F["vol60"], F["vol240"] = vol(g, I, 60), vol(g, I, 240)
    v1440 = vol(g, I, 1440)
    with np.errstate(all="ignore"):
        F["volratio"] = F["vol60"] / v1440
    mid = g.mid[I]
    for w in (60, 240):
        mx, mn = roll(g, I, w, g.mid, np.nanmax), roll(g, I, w, g.mid, np.nanmin)
        F["rng%d" % w] = 1e4 * (mx - mn) / mid
    F["sp"] = g.sp[I]
    with np.errstate(all="ignore"):
        F["spr"] = g.sp[I] / roll(g, I, 1440, g.sp, np.nanmedian)
    for w in (15, 60):
        lo = I + 1 - w; good = (lo >= 0)
        Sw = np.where(good, g.cvol[I + 1] - g.cvol[np.clip(lo, 0, None)], np.nan)
        cw = np.where(good, g.chave[I + 1] - g.chave[np.clip(lo, 0, None)], np.nan)
        lo2 = I + 1 - 1440; good2 = lo2 >= 0
        S2 = np.where(good2, g.cvol[I + 1] - g.cvol[np.clip(lo2, 0, None)], np.nan)
        c2 = np.where(good2, g.chave[I + 1] - g.chave[np.clip(lo2, 0, None)], np.nan)
        with np.errstate(all="ignore"):
            r = np.log((Sw / cw) / (S2 / c2))
        r[~((cw >= MINDATA * w - 1e-9) & (c2 >= MINDATA * 1440 - 1e-9) & (Sw > 0) & (S2 > 0))] = np.nan
        F["vlr%d" % w] = r
    for w in (60, 240):
        a, b = g.oi[I], g.oi[np.clip(I - w, 0, None)]
        lo = I + 1 - w
        hv = (lo >= 0) & ((g.chave[I + 1] - g.chave[np.clip(lo, 0, None)]) >= MINDATA * w - 1e-9)
        with np.errstate(all="ignore"):
            r = np.log(a / b)
        r[~(hv & np.isfinite(a) & np.isfinite(b))] = np.nan
        F["doi%d" % w] = r
    F["tvm"] = 1e4 * (last_px(g, I) / mid - 1)
    k = np.searchsorted(g.ft, t, side="right") - 1                 # last funding row with funding_time <= t: never a later one
    fl = np.where(k >= 0, g.fr[np.clip(k, 0, None)], np.nan) * 1e4
    F["fr_last"] = fl
    F["fr_chg"] = np.where(k >= 1, fl - g.fr[np.clip(k - 1, 0, None)] * 1e4, np.nan)
    F["fr_avg3"] = np.where(k >= 2, (g.fr[np.clip(k, 0, None)] + g.fr[np.clip(k - 1, 0, None)] + g.fr[np.clip(k - 2, 0, None)]) / 3 * 1e4, np.nan)
    for w in (240, 1440):
        mx, mn = roll(g, I, w, g.mid, np.nanmax), roll(g, I, w, g.mid, np.nanmin)
        F["dhi%d" % w] = 1e4 * (mid / mx - 1); F["dlo%d" % w] = 1e4 * (mid / mn - 1)
        if w == 1440:
            with np.errstate(all="ignore"):
                p = (mid - mn) / (mx - mn)
            p[~(mx > mn)] = np.nan
            F["pir1440"] = p
    for name, lead, w in (("xbtc15", "btc", 15), ("xbtc60", "btc", 60), ("xbtc240", "btc", 240), ("xeth60", "eth", 60), ("xeth240", "eth", 240),
                          ("xgold60", "gold", 60), ("xus500_60", "us500", 60)):
        L = xs[lead]
        if L.tk == g.tk:
            F[name] = np.full(len(I), np.nan); continue
        j = L.idx(t)
        F[name] = np.where((j >= 0) & (j < L.n), ret(L, np.clip(j, 0, L.n - 1), w), np.nan)
    F["rel_btc60"] = F["r60"] - F["xbtc60"]; F["rel_btc240"] = F["r240"] - F["xbtc240"]
    hr = (t // 3600) % 24; dw = (t // 86400 + 3) % 7            # 1970-01-01 was a Thursday; Monday = 0
    F["hod4"] = (hr // 4).astype(float); F["dow"] = dw.astype(float); F["wkend"] = (dw >= 5).astype(float)
    nxt = np.where(k >= 0, g.ft[np.clip(k, 0, None)] + 86400, 0)    # daily funding: next settlement = last settlement + 24h (causal; see amendment)
    mn_ = (nxt - t) / 60.0
    F["mtf"] = np.where((k >= 0) & (mn_ > 0), np.where(mn_ < 30, 0, np.where(mn_ < 120, 1, np.where(mn_ < 240, 2, 3))), np.nan)
    return F


# ------------------------------------------------------------------ data build
def build(frozen_id=None):
    """frozen_id None: the targets' own grids hold DISCOVERY rows only (the validation guard is respected through load_stage).
    frozen_id given: discovery + validation rows (load_stage refuses until workers/PERPGEN_FROZEN_<id>.json exists).
    Leaders (BTC, ETH, gold, US 500) are read from their dev rows, as the protocol allows (a leader's discovery or validation region)."""
    t0 = time.time()
    grids = {}
    for tk in TARGETS:
        rows = pdt.load_stage(tk, "discovery", "1m"); fund = pdt.load_stage(tk, "discovery", "funding")
        if frozen_id:
            rows = rows + pdt.load_stage(tk, "validation", "1m", frozen_id); fund = fund + pdt.load_stage(tk, "validation", "funding", frozen_id)
        grids[tk] = Grid(tk, rows, fund)
    for k, tk in LEADERS.items():
        grids["L_" + tk] = Grid(tk, pdt.load(tk, "1m"), pdt.load(tk, "funding"))
    xs = {k: grids["L_" + v] for k, v in LEADERS.items()}
    D = dict(tk=[], t=[], stage=[], I=[])
    feats = {f: [] for f in NUM + list(CAT)}
    hz = {k: [] for k in ("entry_ok", "defect", "bid_e", "ask_e", "exit_ok", "exit_ts", "bid_x", "ask_x", "fsum", "inreg")}
    arr = {h: {k: [] for k in ("bid_e", "ask_e", "bid_x", "ask_x", "exit_ts", "fsum", "found", "inreg")} for h in range(len(HORIZONS))}
    med_sp = {}
    for ti, tk in enumerate(TARGETS):
        g = grids[tk]; c = CUTS[tk]
        t_all = g.ts0 + 60 * np.arange(g.n)
        lim = c["holdout_ts"] if frozen_id else c["validation_ts"]
        sel = np.flatnonzero((t_all % 900 == 0) & g.ok & (t_all < lim))
        I = sel.astype(np.int64); t = t_all[I]
        F = features(g, I, xs)
        for f in feats:
            feats[f].append(F[f])
        D["tk"].append(np.full(len(I), ti)); D["t"].append(t)
        D["stage"].append(np.where(t < c["validation_ts"], 0, 1)); D["I"].append(I)
        dsp = g.sp[(t_all < c["validation_ts"]) & g.ok]
        med_sp[tk] = float(np.median(g.sp[g.ok & (t_all - 60 < c["validation_ts"])]))
        # entry quote: the bar ending at t + 60
        ie = I + 1
        ine = ie < g.n
        iec = np.clip(ie, 0, g.n - 1)
        ent_ok = ine & g.ok[iec]
        spe = g.sp[iec]
        defect = ent_ok & ((spe > 10 * med_sp[tk]) | (spe > 100))
        for hi, h in enumerate(HORIZONS):
            x0 = I + 1 + h                                        # minute-grid index of the bar ending at t + 60 s + horizon
            found = np.zeros(len(I), bool); xi = np.zeros(len(I), np.int64)
            for off in range(0, 6):                               # first usable bar within the next 5 minutes
                j = x0 + off; jc = np.clip(j, 0, g.n - 1)
                m = (~found) & (j < g.n) & g.ok[jc]
                xi = np.where(m, jc, xi); found |= m
            exit_ts = g.ts0 + 60 * np.where(found, xi, x0)
            tx = g.ts0 + 60 * x0                                  # nominal exit time
            reg_hi = np.where(t < c["validation_ts"], c["validation_ts"], c["holdout_ts"])
            inreg = (np.where(found, exit_ts, tx) - 60 < reg_hi)  # the exit bar (actual when found) must start inside the stage's region
            a = arr[hi]
            a["bid_e"].append(np.where(ent_ok, g.bid[iec], np.nan)); a["ask_e"].append(np.where(ent_ok, g.ask[iec], np.nan))
            a["bid_x"].append(np.where(found, g.bid[np.clip(xi, 0, g.n - 1)], np.nan)); a["ask_x"].append(np.where(found, g.ask[np.clip(xi, 0, g.n - 1)], np.nan))
            a["exit_ts"].append(exit_ts)
            tE = t + 60
            a["fsum"].append(g.fc[np.searchsorted(g.ft, exit_ts, side="right")] - g.fc[np.searchsorted(g.ft, tE, side="right")])
            a["found"].append(found); a["inreg"].append(inreg)
        hz["defect"].append(defect); hz["entry_ok"].append(ent_ok)
    for k in D:
        D[k] = np.concatenate(D[k])
    for f in feats:
        feats[f] = np.concatenate(feats[f])
    for hi in arr:
        for k in arr[hi]:
            arr[hi][k] = np.concatenate(arr[hi][k])
    S = dict(D=D, F=feats, H=arr, entry_ok=np.concatenate(hz["entry_ok"]), defect=np.concatenate(hz["defect"]), med_sp=med_sp)
    S["date"] = (D["t"] + 60) // 86400
    print("built %d decision rows in %.1fs" % (len(D["t"]), time.time() - t0), flush=True)
    return S


def make_cuts(S):
    """Quantile cut points from each ticker's own DISCOVERY decision-time values; stored with a sha256."""
    D, F = S["D"], S["F"]; out = {}
    for ti, tk in enumerate(TARGETS):
        m = (D["tk"] == ti) & (D["stage"] == 0)
        out[tk] = {}
        for f in NUM:
            v = F[f][m]; v = v[np.isfinite(v)]
            out[tk][f] = [float(np.quantile(v, q)) for q in LEVELS] if len(v) >= 20 else None
    blob = json.dumps(out, sort_keys=True).encode()
    return out, hashlib.sha256(blob).hexdigest()


def atom_matrix(S, cuts):
    D, F = S["D"], S["F"]; nd = len(D["t"])
    M = np.zeros((len(ATOMS), nd), bool)
    ticker_cut = {ti: cuts[tk] for ti, tk in enumerate(TARGETS)}
    for ai, (f, k, op, v) in enumerate(ATOMS):
        if k == "c":
            x = F[f]; M[ai] = np.isfinite(x) & (x == v); continue
        qi = LEVELS.index(v); x = F[f]
        for ti in range(len(TARGETS)):
            m = D["tk"] == ti; cut = ticker_cut[ti][f]
            if cut is None:
                continue
            c = cut[qi]
            with np.errstate(invalid="ignore"):
                M[ai, m] = (x[m] >= c) if op == 0 else (x[m] <= c)
            M[ai, m] &= np.isfinite(x[m])
    return M


# ------------------------------------------------------------------ trades and metrics
def gross(S, d, h, funding="assumed"):
    """per-row gross return (before fee) of direction d (0 long, 1 short) at horizon index h. NaN where entry or exit quote is missing."""
    a = S["H"][h]
    with np.errstate(all="ignore"):
        r = a["bid_x"] / a["ask_e"] - 1 if d == 0 else -(a["ask_x"] / a["bid_e"] - 1)
    f = a["fsum"]
    sgn = 1 if d == 0 else -1
    if funding == "assumed":
        r = r - sgn * f                                           # long pays a positive rate (ASSUMED sign), short receives it
    elif funding == "flipped":
        r = r + sgn * f
    return r


def trades(S, sig, h, stage, tk_of_row=None):
    """Greedy one-position-per-ticker over the signal rows of one stage. Returns (row indices, counts dict)."""
    D = S["D"]; a = S["H"][h]
    rows = np.flatnonzero(sig & (D["stage"] == stage))
    ct = dict(sig=len(rows), ignored=0, entry_void=0, defect=0, exit_void=0, out_region=0)
    out = []
    tkv, tv = D["tk"], D["t"]; eo, df = S["entry_ok"], S["defect"]; fd, ir, xt = a["found"], a["inreg"], a["exit_ts"]
    busy = -1; ctk = -1
    hs = HORIZONS[h] * 60
    for j in rows.tolist():
        k = tkv[j]
        if k != ctk:
            ctk = k; busy = -1
        if tv[j] < busy:
            ct["ignored"] += 1; continue
        if not eo[j]:
            ct["entry_void"] += 1; continue
        if df[j]:
            ct["defect"] += 1; continue
        if not ir[j]:
            ct["out_region"] += 1; continue
        busy = xt[j] if fd[j] else tv[j] + 60 + hs
        if not fd[j]:
            ct["exit_void"] += 1; continue
        out.append(j)
    return np.array(out, np.int64), ct


def pf_of(x):
    w = x[x > 0].sum(); l = -x[x < 0].sum()
    return (w / l if l > 0 else (99.0 if w > 0 else 0.0))


def split_halves(ts, date):
    """first half = trades on or before the date of the median trade; second = after."""
    o = np.argsort(ts, kind="stable"); md = date[o[len(o) // 2]]
    return date <= md


def day_z(net, date):
    ud = np.unique(date)
    if len(ud) < 2:
        return 0.0
    mu = np.array([net[date == d].mean() for d in ud])
    sd = mu.std(ddof=1)
    return float(mu.mean() / (sd / math.sqrt(len(ud)))) if sd > 0 else 0.0


def stage1(S, sig, d, h):
    """discovery bars. returns (pass, info)."""
    rows, ct = trades(S, sig, h, 0)
    info = dict(n=len(rows), ndates=0, pf=0.0, ct=ct)
    if len(rows) == 0:
        info["fail"] = "trades"; return False, info, rows
    g = gross(S, d, h)[rows]
    net12, net24 = g - 2 * FEE12, g - 2 * FEE24
    date, ts = S["date"][rows], S["D"]["t"][rows]
    nd = len(np.unique(date)); info.update(ndates=nd, pf=pf_of(net12), mean12=float(net12.mean()), mean24=float(net24.mean()))
    if len(rows) < 200: info["fail"] = "trades"; return False, info, rows
    if nd < 20: info["fail"] = "dates"; return False, info, rows
    if info["pf"] < 1.3: info["fail"] = "pf"; return False, info, rows
    if info["mean24"] <= 0: info["fail"] = "cost24"; return False, info, rows
    h1 = split_halves(ts, date)
    if not (h1.any() and (~h1).any() and pf_of(net12[h1]) > 1.0 and pf_of(net12[~h1]) > 1.0): info["fail"] = "halves"; return False, info, rows
    ud = np.unique(date); ds = np.array([net12[date == u].sum() for u in ud])
    if ds.max() > 0.25 * net12.sum(): info["fail"] = "conc"; return False, info, rows
    info["fail"] = None; info["z"] = day_z(net12, date)
    return True, info, rows


def jaccard(a, b):
    sa, sb = set(a.tolist()), set(b.tolist()); u = len(sa | sb)
    return len(sa & sb) / u if u else 0.0


def cluster(items, thr, key=lambda it: (it["d"], it["h"])):
    """items: dicts with rows, pf, d, h; keep the best PF of every group of Jaccard >= thr (within the same key)."""
    kept = []
    for it in sorted(items, key=lambda x: -x["pf"]):
        if not any(key(it) == key(k) and jaccard(it["rows"], k["rows"]) >= thr for k in kept):
            kept.append(it)
    return kept


# ------------------------------------------------------------------ rules, ledger
def ledger_set():
    seen = set()
    for p in glob.glob(os.path.join(LEDGER_DIR, "RUN*_%s.ids.gz" % GROUP)):
        with gzip.open(p, "rt") as f:
            seen.update(l.rstrip("\n") for l in f if l.strip())
    return seen


def draw(rng, seen, n):
    out = []; cur = set()
    while len(out) < n:
        k = rng.choices((1, 2, 3), weights=(0.2, 0.4, 0.4))[0]
        atoms = []; feats = set()
        while len(atoms) < k:
            i = rng.randrange(len(ATOMS))
            if ATOMS[i][0] in feats:
                continue
            feats.add(ATOMS[i][0]); atoms.append(i)
        d = rng.randrange(2); h = rng.randrange(len(HORIZONS))
        name = rule_name(atoms, d, h)
        if name in seen or name in cur:
            continue
        cur.add(name); out.append((name, tuple(atoms), d, h))
    return out


def run(nn, n_target, S, M, cuts, cuts_sha):
    seed = 1000 + nn
    rng = random.Random(seed)
    os.makedirs(LEDGER_DIR, exist_ok=True)
    lp = os.path.join(LEDGER_DIR, "RUN%02d_%s.ids.gz" % (nn, GROUP))
    seen = ledger_set()
    done = 0; t0 = time.time()
    fails = {}; reach200 = 0; best = (0.0, None); best200 = (0.0, None); best50 = (0.0, None)
    surv = []; nsig_small = 0
    while done < n_target:
        batch = draw(rng, seen, min(500, n_target - done))
        with gzip.open(lp, "at") as f:                             # ledger first, flushed, BEFORE this batch is scored
            f.write("".join(b[0] + "\n" for b in batch)); f.flush()
        seen.update(b[0] for b in batch)
        for name, atoms, d, h in batch:
            sig = M[atoms[0]].copy()
            for a in atoms[1:]:
                sig &= M[a]
            if int((sig & (S["D"]["stage"] == 0)).sum()) < 200:    # fewer than 200 signals cannot make 200 trades: same verdict as the trade bar
                fails["trades"] = fails.get("trades", 0) + 1; nsig_small += 1; continue
            ok, info, rows = stage1(S, sig, d, h)
            if info["n"] >= 200:
                reach200 += 1
                if info["pf"] > best200[0]: best200 = (info["pf"], name)
            if info["n"] >= 50 and info["pf"] > best50[0]: best50 = (info["pf"], name)
            if ok:
                surv.append(dict(name=name, atoms=atoms, d=d, h=h, rows=rows, pf=info["pf"], info=info))
            else:
                fails[info["fail"]] = fails.get(info["fail"], 0) + 1
        done += len(batch)
        print("  run %d: %d/%d scored, %.0fs, %d survivors" % (nn, done, n_target, time.time() - t0, len(surv)), flush=True)
    return dict(N=done, surv=surv, fails=fails, reach200=reach200, best200=best200, best50=best50, nsig_small=nsig_small, secs=time.time() - t0)


SCRATCH = os.environ.get("PG_SCRATCH", "/tmp/claude-0/-home-user-shwoopnet/026f6e8f-6dc4-5e3b-8c3b-e0089b12fb94/scratchpad")


def discover(nn, n):
    S = build(); cuts, sha = make_cuts(S)
    cp = os.path.join(ROOT, "workers", "PERPGEN_NONCRYPTO_QCUTS.json")
    if os.path.exists(cp):
        old = json.load(open(cp))
        assert old["sha256"] == sha, "cut points changed between runs"
    else:
        json.dump(dict(group=GROUP, sha256=sha, note="quantile cuts from each ticker's own DISCOVERY decision-time values; sha256 of json.dumps(cuts, sort_keys=True)", cuts=cuts), open(cp, "w"), indent=1, sort_keys=True)
    M = atom_matrix(S, cuts)
    r = run(nn, n, S, M, cuts, sha)
    kept = cluster(r["surv"], 0.9)
    fz = dict(id="NC%02d" % nn, group=GROUP, seed=1000 + nn, n_discovery_survivors=len(r["surv"]), n_after_cluster=len(kept),
              cuts_sha256=sha, rules=[dict(name=k["name"], atoms=[atom_name(ATOMS[a]) for a in k["atoms"]], atom_idx=list(k["atoms"]), d=k["d"], h=HORIZONS[k["h"]],
                                           disc_n=k["info"]["n"], disc_pf=round(k["info"]["pf"], 4)) for k in kept])
    blob = json.dumps(fz, sort_keys=True).encode(); fz["sha256_of_rules"] = hashlib.sha256(json.dumps(fz["rules"], sort_keys=True).encode()).hexdigest()
    json.dump(fz, open(os.path.join(ROOT, "workers", "PERPGEN_FROZEN_NC%02d.json" % nn), "w"), indent=1)
    r2 = {k: v for k, v in r.items() if k != "surv"}; r2.update(n_surv=len(r["surv"]), n_kept=len(kept), cuts_sha=sha, frozen_sha=fz["sha256_of_rules"])
    os.makedirs(SCRATCH, exist_ok=True)
    json.dump(r2, open(os.path.join(SCRATCH, "nc%02d_disc.json" % nn), "w"), indent=1)
    print(json.dumps(r2))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "discover":
        discover(int(sys.argv[2]), int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 5000)
    if cmd == "selfcheck":
        S = build(); cuts, sha = make_cuts(S)
        print("cuts sha", sha)
        M = atom_matrix(S, cuts); print(M.shape)
