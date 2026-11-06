#!/usr/bin/env python3
"""PERPGEN generator, slice CRYPTOPRICE (Strategy Research V2 worker). Research only: no order, no key, no live code.

Registered protocol: workers/PERPGEN_PROTOCOL.md (bars, grammar, cuts, split, fill rule, audit A1-A10 are NOT changed here).
Slice: the 10 CRYPTO universe tickers; atoms ONLY from the price families of the protocol's fixed feature list:
  returns r5 r15 r60 r240 r1440 | range/volatility vol60 vol240 volratio rng60 rng240 | flow vlr15 vlr60 doi60 doi240 tvm |
  distance from extremes dhi240 dlo240 dhi1440 dlo1440 pir1440         (20 numeric features, 200 numeric atoms)
Not used (other workers or not in this slice): funding, time categoricals, cross-asset leaders, spread atoms (sp, spr).
The protocol's feature list has no "candle shape" feature; none is invented here (amendment file would be needed).

    python3 -I src/scalper/perpgen_cryptoprice.py discover <nn> [--rules 5000]   ledger first, score on DISCOVERY, freeze survivors
    python3 -I src/scalper/perpgen_cryptoprice.py validate <nn>                    after the frozen list is committed and pushed
    python3 -I src/scalper/perpgen_cryptoprice.py audit <nn>                       A1-A10 on validation survivors
Vectorised numpy for features and masks; the one-position-per-ticker selection runs in a tiny C routine (ctypes).
"""
import ctypes, glob, gzip, hashlib, itertools, json, math, os, random, subprocess, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import perpdata as pd_                                   # the guarded loader

ROOT = pd_.ROOT
WORK = os.path.join(ROOT, "workers")
LEDGER_DIR = os.path.join(WORK, "perpgen_ledger")
CACHE = os.path.join(pd_.DATA, "cryptoprice")
GROUP = "CRYPTOPRICE"
TICKERS = pd_.universe_frozen()["CRYPTO"]
FEATS = ["r5", "r15", "r60", "r240", "r1440", "vol60", "vol240", "volratio", "rng60", "rng240",
         "vlr15", "vlr60", "doi60", "doi240", "tvm", "dhi240", "dlo240", "dhi1440", "dlo1440", "pir1440"]
FIDX = {f: i for i, f in enumerate(FEATS)}
QS = (0.10, 0.25, 0.50, 0.75, 0.90)
HORIZONS = (900, 1800, 3600, 7200, 14400, 28800, 86400)
FEE12, FEE24, FEE5 = 0.0012, 0.0024, 0.0005
Q15 = 900


# ------------------------------------------------------------------ C greedy (one position per ticker)
_C = r"""
#include <stdint.h>
int64_t select_trades(const uint8_t* mask, const int64_t* qh, const uint8_t* occ, int64_t n, int64_t k, int32_t* out, int64_t* st){
  int64_t nxt = -((int64_t)1<<62), m = 0, ign = 0, drop = 0;
  for (int64_t i = 0; i < n; i++){
    if (!mask[i]) continue;
    if (qh[i] < nxt){ ign++; continue; }
    if (!occ[i]){ drop++; continue; }
    out[m++] = (int32_t)i; nxt = qh[i] + k;
  }
  st[0] = ign; st[1] = drop; return m;
}
"""


def _lib():
    os.makedirs(CACHE, exist_ok=True)
    src, so = os.path.join(CACHE, "sel.c"), os.path.join(CACHE, "sel.so")
    if not os.path.exists(so) or open(src).read() != _C:
        open(src, "w").write(_C)
        subprocess.check_call(["gcc", "-O2", "-shared", "-fPIC", "-o", so, src])
    lib = ctypes.CDLL(so)
    lib.select_trades.restype = ctypes.c_int64
    return lib


# ------------------------------------------------------------------ features (vectorised)
class Grid:
    """One ticker's 1 minute rows on a dense minute grid (NaN = missing; no forward fill anywhere)."""
    def __init__(self, rows):
        self.ts0 = int(rows[0]["ts"])
        L = int((rows[-1]["ts"] - self.ts0) // 60) + 1
        self.L = L
        def col(k):
            a = np.full(L, np.nan)
            for r in rows:
                v = r[k]
                if v is not None:
                    a[int((r["ts"] - self.ts0) // 60)] = v
            return a
        self.present = np.zeros(L, bool)
        for r in rows:
            self.present[int((r["ts"] - self.ts0) // 60)] = True
        self.bid, self.ask, self.px, self.vol, self.oi = col("bid_c"), col("ask_c"), col("px_c"), col("vol_usd"), col("oi")
        ok = np.zeros(L, bool)
        for r in rows:
            if r["ok"] == 1.0:
                ok[int((r["ts"] - self.ts0) // 60)] = True
        self.ok = ok & ~np.isnan(self.bid) & ~np.isnan(self.ask)
        self.mid = np.where(self.ok, (self.bid + self.ask) / 2, np.nan)
        self.sp = np.where(self.ok, (self.ask - self.bid) / self.mid * 1e4, np.nan)
        # next usable bar at or after g (for the exit)
        nxt = np.full(L + 1, 10 ** 9, dtype=np.int64)
        for g in range(L - 1, -1, -1):
            nxt[g] = g if self.ok[g] else nxt[g + 1]
        self.nxt = nxt
        self.t_of = lambda g: self.ts0 + 60 * g


def _cs(a):
    return np.concatenate([[0.0], np.cumsum(a)])


def compute_features(G, gs):
    """Feature matrix (n, 20) at decision grid indices gs (the bar ENDING at each decision time). Every window uses only bars at or before g."""
    n = len(gs); F = np.full((n, len(FEATS)), np.nan)
    mid, ok = G.mid, G.ok
    cok = _cs(ok.astype(float)); cpr = _cs(G.present.astype(float))
    r1 = np.full(G.L, np.nan); r1[1:] = np.log(mid[1:] / mid[:-1])
    v1 = np.isfinite(r1)
    C1 = _cs(v1.astype(float)); S1 = _cs(np.where(v1, r1, 0)); S2 = _cs(np.where(v1, r1 * r1, 0))
    V = np.where(np.isnan(G.vol), 0.0, G.vol); cV = _cs(np.where(G.present, V, 0.0))
    def okw(w):                                     # bars g-w+1..g, at least 90 percent usable
        lo = gs + 1 - w
        return (lo >= 0) & ((cok[gs + 1] - cok[np.maximum(lo, 0)]) >= 0.9 * w)
    def prw(w):
        lo = gs + 1 - w
        return (lo >= 0) & ((cpr[gs + 1] - cpr[np.maximum(lo, 0)]) >= 0.9 * w)
    for name, w in (("r5", 5), ("r15", 15), ("r60", 60), ("r240", 240), ("r1440", 1440)):
        g0 = gs - w
        good = okw(w) & (g0 >= 0)
        good &= ok[np.maximum(g0, 0)]
        F[good, FIDX[name]] = 1e4 * np.log(mid[gs[good]] / mid[g0[good]])
    def vol(w):
        lo = gs + 1 - w
        c = C1[gs + 1] - C1[np.maximum(lo, 0)]
        good = (lo >= 1) & (c >= 0.9 * w) & (c > 2)
        s1 = S1[gs + 1] - S1[np.maximum(lo, 0)]; s2 = S2[gs + 1] - S2[np.maximum(lo, 0)]
        with np.errstate(all="ignore"):
            var = (s2 - s1 * s1 / c) / (c - 1)
        return np.where(good & (var >= 0), np.sqrt(np.maximum(var, 0)) * 1e4, np.nan)
    v60, v240, v1440 = vol(60), vol(240), vol(1440)
    F[:, FIDX["vol60"]] = v60; F[:, FIDX["vol240"]] = v240
    with np.errstate(all="ignore"):
        rt = v60 / v1440
    F[:, FIDX["volratio"]] = np.where(np.isfinite(rt), rt, np.nan)
    ext = {}
    for w in (60, 240, 1440):
        mx = np.full(n, np.nan); mn = np.full(n, np.nan)
        good = okw(w)
        for a in range(0, n, 800):
            sl = slice(a, min(n, a + 800)); gi = gs[sl]
            idx = np.maximum(gi[:, None] - np.arange(w)[None, :], 0)
            blk = mid[idx]
            with np.errstate(all="ignore"):
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    mx[sl] = np.nanmax(blk, axis=1); mn[sl] = np.nanmin(blk, axis=1)
        mx[~good] = np.nan; mn[~good] = np.nan
        ext[w] = (mx, mn)
    m_t = mid[gs]
    for w in (60, 240):
        F[:, FIDX["rng%d" % w]] = (ext[w][0] - ext[w][1]) / m_t * 1e4
    for w in (240, 1440):
        F[:, FIDX["dhi%d" % w]] = (m_t / ext[w][0] - 1) * 1e4
        F[:, FIDX["dlo%d" % w]] = (m_t / ext[w][1] - 1) * 1e4
    with np.errstate(all="ignore"):
        pir = (m_t - ext[1440][1]) / (ext[1440][0] - ext[1440][1])
    F[:, FIDX["pir1440"]] = np.where(np.isfinite(pir), pir, np.nan)
    ok1440 = prw(1440)
    for name, w in (("vlr15", 15), ("vlr60", 60)):
        lo = gs + 1 - w
        sw = cV[gs + 1] - cV[np.maximum(lo, 0)]
        s14 = cV[gs + 1] - cV[np.maximum(gs + 1 - 1440, 0)]
        c14 = cpr[gs + 1] - cpr[np.maximum(gs + 1 - 1440, 0)]
        with np.errstate(all="ignore"):
            avg = s14 / c14
            x = np.log(sw / (avg * w))
        good = prw(w) & ok1440 & (sw > 0) & (avg > 0) & np.isfinite(x)
        F[good, FIDX[name]] = x[good]
    for name, w in (("doi60", 60), ("doi240", 240)):
        g0 = gs - w
        a, b = G.oi[gs], G.oi[np.maximum(g0, 0)]
        good = prw(w) & (g0 >= 0) & np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
        with np.errstate(all="ignore"):
            x = np.log(a / b)
        F[good, FIDX[name]] = x[good]
    last = np.full(n, np.nan)
    for k in range(4, -1, -1):                       # latest non-missing trade price among the 5 bars ending at g
        v = G.px[np.maximum(gs - k, 0)]
        v = np.where(gs - k >= 0, v, np.nan)
        last = np.where(np.isfinite(v), v, last)
    F[:, FIDX["tvm"]] = (last / m_t - 1) * 1e4
    return F


def trade_arrays(G, gs, fund, lo_ts, hi_ts, lat, med_sp):
    """Per horizon: occ, valid, ret_long, ret_short, fund_sum, for every decision. Fill at the bar ending decision+lat; exit at the
    first usable bar within 5 minutes at or after fill+horizon. Defect: fill quote spread above 10x discovery median or above 100 bps."""
    cap = min(10 * med_sp, 100.0)
    ge = gs + lat // 60
    inb = ge < G.L
    ge_c = np.minimum(ge, G.L - 1)
    ent_ok = inb & G.ok[ge_c] & (G.sp[ge_c] <= cap)
    ent_start = G.ts0 + 60 * ge_c - 60
    ent_region = (ent_start >= lo_ts) & (ent_start < hi_ts)
    fts = np.array([r["ts"] for r in fund]); frate = np.array([r["funding_rate"] for r in fund])
    cf = np.concatenate([[0.0], np.cumsum(frate)]) if len(fund) else np.zeros(1)
    out = {}
    for H in HORIZONS:
        gx0 = ge_c + H // 60
        inx = gx0 < G.L
        gx = np.where(inx, G.nxt[np.minimum(gx0, G.L)], 10 ** 9)
        found = inx & (gx - gx0 <= 5) & (gx < G.L)
        gxc = np.minimum(gx, G.L - 1)
        x_start = G.ts0 + 60 * np.where(inx, gx0, G.L - 1) - 60
        region = ent_region & (x_start < hi_ts)
        occ = ent_ok & region
        sp_x = G.sp[gxc]
        valid = occ & found & (sp_x <= cap)
        bid_e, ask_e, bid_x, ask_x = G.bid[ge_c], G.ask[ge_c], G.bid[gxc], G.ask[gxc]
        with np.errstate(all="ignore"):
            rl = bid_x / ask_e - 1
            rs = -(ask_x / bid_e - 1)
        t_ent = G.ts0 + 60 * ge_c; t_x = G.ts0 + 60 * gxc
        if len(fund):
            F = cf[np.searchsorted(fts, t_x, "right")] - cf[np.searchsorted(fts, t_ent, "right")]
        else:
            F = np.zeros(len(gs))
        out[H] = dict(occ=occ.astype(np.uint8), valid=valid, rl=np.where(valid, rl, 0), rs=np.where(valid, rs, 0), F=np.where(valid, F, 0.0),
                      gx=gxc, stale=(gx - gx0 > 0) | ~G.present[np.maximum(gxc - 1, 0)] | ~G.present[np.maximum(ge_c - 1, 0)])
    return out, ge_c


# ------------------------------------------------------------------ stage object
class Stage:
    def __init__(self, name, tk_list, per, F_all):
        self.name = name; self.tk = tk_list; self.per = per
        self.F = F_all                                               # (N, 20)


def build_stage(stage, frozen_id=None, lat=60):
    """Decision-level arrays of the CRYPTO group for 'discovery' or 'validation' (the loader enforces the freeze for validation)."""
    cu = pd_.cuts()
    parts = []
    for ti, tk in enumerate(TICKERS):
        disc = pd_.load_stage(tk, "discovery")
        rows = disc if stage == "discovery" else disc + pd_.load_stage(tk, "validation", frozen_id=frozen_id)
        G = Grid(rows)
        lo = 0 if stage == "discovery" else cu[tk]["validation_ts"]
        hi = cu[tk]["validation_ts"] if stage == "discovery" else cu[tk]["holdout_ts"]
        t_all = G.ts0 + 60 * np.arange(G.L)
        gs = np.nonzero((t_all % Q15 == 0) & G.ok & (t_all - 60 >= lo) & (t_all - 60 < hi))[0]
        F = compute_features(G, gs)
        med = float(np.median([(r["ask_c"] - r["bid_c"]) / ((r["ask_c"] + r["bid_c"]) / 2) * 1e4 for r in disc if r["ok"] == 1.0]))
        fund = pd_.load_stage(tk, "discovery", "funding") + (pd_.load_stage(tk, "validation", "funding", frozen_id=frozen_id) if stage == "validation" else [])
        ta, ge = trade_arrays(G, gs, fund, lo, hi, lat, med)
        parts.append(dict(tk=ti, gs=gs, t=t_all[gs], F=F, ta=ta, ge=ge, G=G, med=med, lo=lo, hi=hi))
    return parts


def pool(parts):
    S = {}
    S["tk"] = np.concatenate([np.full(len(p["gs"]), p["tk"]) for p in parts])
    S["t"] = np.concatenate([p["t"] for p in parts]).astype(np.int64)
    S["F"] = np.concatenate([p["F"] for p in parts])
    S["qh"] = (S["t"] // Q15 + S["tk"].astype(np.int64) * 10 ** 7).astype(np.int64)
    S["day"] = ((S["t"] + 60) // 86400).astype(np.int64)
    S["ta"] = {H: {k: np.concatenate([p["ta"][H][k] for p in parts]) for k in ("occ", "valid", "rl", "rs", "F", "stale")} for H in HORIZONS}
    S["n"] = len(S["t"])
    return S


# ------------------------------------------------------------------ cuts (discovery decision-time values only)
def make_cuts(parts):
    cuts = {}
    for p in parts:
        tk = TICKERS[p["tk"]]
        cuts[tk] = {f: [float(np.quantile(p["F"][:, i][np.isfinite(p["F"][:, i])], q)) for q in QS] for f, i in FIDX.items()}
    blob = json.dumps(cuts, sort_keys=True, separators=(",", ":"))
    return cuts, hashlib.sha256(blob.encode()).hexdigest()


def atom_masks(S, cuts):
    """uint8 (200, N): atom a = (feature, op, q) with op 0 'ge' and 1 'le'; NaN features make every atom false."""
    N = S["n"]
    M = np.zeros((len(FEATS) * 2 * len(QS), N), np.uint8)
    cutarr = np.array([[cuts[tk][f] for f in FEATS] for tk in TICKERS])            # (tk, feat, q)
    for fi in range(len(FEATS)):
        x = S["F"][:, fi]
        c = cutarr[S["tk"], fi, :]                                                   # (N, q)
        with np.errstate(invalid="ignore"):
            for qi in range(len(QS)):
                M[(fi * 2 + 0) * len(QS) + qi] = (x >= c[:, qi])
                M[(fi * 2 + 1) * len(QS) + qi] = (x <= c[:, qi])
    return M


def atom_name(a):
    fi, rest = divmod(a, 2 * len(QS)); op, qi = divmod(rest, len(QS))
    return "%s:%s:%.2f" % (FEATS[fi], "ge" if op == 0 else "le", QS[qi])


NAME2ATOM = {atom_name(a): a for a in range(len(FEATS) * 2 * len(QS))}


def canon(atoms, direction, H):
    return "&".join(sorted((atom_name(a) for a in atoms), key=lambda s: s.split(":")[0])) + "|" + direction + "|" + str(H)


def parse(s):
    a, d, h = s.split("|")
    return [NAME2ATOM[x] for x in a.split("&")], d, int(h)


# ------------------------------------------------------------------ scoring
def pf(x):
    p = x[x > 0].sum(); n = -x[x < 0].sum()
    return float("inf") if n == 0 and p > 0 else (p / n if n > 0 else 0.0)


def trade_nets(S, idx, d, H, fee):
    ta = S["ta"][H]
    r = ta["rl"][idx] if d == "L" else ta["rs"][idx]
    fs = -1.0 if d == "L" else 1.0
    return r + fs * ta["F"][idx] - 2 * fee


class Scorer:
    def __init__(self, S, M):
        self.S, self.M, self.lib = S, M, _lib()
        self.qh = np.ascontiguousarray(S["qh"]); self.out = np.zeros(S["n"], np.int32); self.st = np.zeros(2, np.int64)
        self.mask = np.zeros(S["n"], np.uint8)
        self.ones = np.ones(S["n"], np.uint8)

    def select(self, atoms, H, valid_only=True, ones=False):
        if ones or not atoms:
            mask = self.ones
        else:
            mask = self.mask
            np.copyto(mask, self.M[atoms[0]])
            for a in atoms[1:]:
                np.bitwise_and(mask, self.M[a], out=mask)
        occ = self.S["ta"][H]["occ"]
        k = int(math.ceil((H + 60) / Q15))
        m = self.lib.select_trades(mask.ctypes.data_as(ctypes.c_void_p), self.qh.ctypes.data_as(ctypes.c_void_p), occ.ctypes.data_as(ctypes.c_void_p),
                                   ctypes.c_int64(self.S["n"]), ctypes.c_int64(k), self.out.ctypes.data_as(ctypes.c_void_p), self.st.ctypes.data_as(ctypes.c_void_p))
        idx = self.out[:m].copy()
        if valid_only:
            idx = idx[self.S["ta"][H]["valid"][idx]]
        return idx, int(self.st[0]), int(self.st[1])


def metrics(S, idx, d, H):
    """12 bps figures for the trade set idx (indices into the stage arrays)."""
    n = len(idx)
    if n == 0:
        return None
    day = S["day"][idx]
    net = trade_nets(S, idx, d, H, FEE12)
    ud = np.unique(day)
    med = np.median(day)
    h1 = day <= med; h2 = ~h1
    tot = net.sum()
    ds = np.array([net[day == u].sum() for u in ud]) if len(ud) < 400 else np.bincount(np.searchsorted(ud, day), weights=net)
    out = dict(n=n, dates=len(ud), pf=pf(net), mean=float(net.mean()), pf1=pf(net[h1]), pf2=pf(net[h2]),
               m1=float(net[h1].mean()) if h1.any() else 0.0, m2=float(net[h2].mean()) if h2.any() else 0.0,
               mean24=float((net + 2 * (FEE12 - FEE24)).mean()) if False else float(trade_nets(S, idx, d, H, FEE24).mean()),
               pf24=pf(trade_nets(S, idx, d, H, FEE24)), top=float(ds.max() / tot) if tot > 0 else 9.0)
    return out


def disc_pass(m):
    return (m is not None and m["n"] >= 200 and m["dates"] >= 20 and m["pf"] >= 1.3 and m["mean24"] > 0 and m["pf1"] > 1.0 and m["pf2"] > 1.0 and m["top"] <= 0.25)


def val_pass(m, ctrl, core):
    return (m is not None and m["n"] >= 100 and m["dates"] >= 10 and m["pf"] >= 1.3 and m["pf1"] > 1.0 and m["pf2"] > 1.0 and m["m1"] > 0 and m["m2"] > 0
            and m["pf24"] >= 1.0 and ctrl["pf"] < 1.0 and ctrl["mean"] < m["mean"] and core["mean"] < m["mean"])


# ------------------------------------------------------------------ ledger
def ledger_files():
    return sorted(glob.glob(os.path.join(LEDGER_DIR, "*_CRYPTO*.ids.gz")))


def read_lines(f):
    """All lines of a ledger; another worker may be appending (a half-written gzip member): retry, never guess."""
    for attempt in range(20):
        try:
            with gzip.open(f, "rt") as fh:
                return [l.strip() for l in fh if l.strip()]
        except (EOFError, OSError):
            time.sleep(1.5)
    raise RuntimeError("ledger unreadable: " + f)


def ledger_seen():
    seen = set()
    for f in ledger_files():
        seen.update(read_lines(f))
    return seen


def ledger_total():
    return sum(len(read_lines(f)) for f in glob.glob(os.path.join(LEDGER_DIR, "*.ids.gz")))


def ledger_append(path, lines):
    blob = gzip.compress(("\n".join(lines) + "\n").encode())
    with open(path, "ab") as f:
        f.write(blob); f.flush(); os.fsync(f.fileno())


def gen_rules(seed, n, seen):
    rng = random.Random(seed)
    out, mine = [], set()
    na = len(FEATS) * 2 * len(QS)
    tries = 0
    while len(out) < n:
        tries += 1
        if tries > n * 400:
            break
        k = rng.choices((1, 2, 3), (0.2, 0.4, 0.4))[0]
        fs = rng.sample(range(len(FEATS)), k)
        atoms = [f * 2 * len(QS) + rng.randrange(2) * len(QS) + rng.randrange(len(QS)) for f in fs]
        s = canon(atoms, rng.choice("LS"), rng.choice(HORIZONS))
        if s in seen or s in mine:
            continue
        mine.add(s); out.append(s)
    return out


def stage_cache(name, frozen_id=None):
    import pickle
    path = os.path.join(CACHE, "stage_%s.pkl" % name)
    if os.path.exists(path):
        return pickle.load(open(path, "rb"))
    parts = build_stage(name, frozen_id)
    obj = dict(parts=[{k: v for k, v in p.items() if k != "G"} for p in parts])
    pickle.dump(obj, open(path, "wb"))
    return obj


def get_discovery():
    import pickle
    os.makedirs(CACHE, exist_ok=True)
    pth = os.path.join(CACHE, "disc.pkl")
    if os.path.exists(pth):
        return pickle.load(open(pth, "rb"))
    parts = build_stage("discovery")
    cuts, sha = make_cuts(parts)
    S = pool(parts)
    obj = dict(S=S, cuts=cuts, cuts_sha=sha, med={TICKERS[p["tk"]]: p["med"] for p in parts})
    pickle.dump(obj, open(pth, "wb"), protocol=4)
    json.dump(dict(sha256=sha, cuts=cuts), open(os.path.join(WORK, "perpgen_cryptoprice_cuts.json"), "w"), sort_keys=True, indent=1)
    return obj


def jaccard(a, b):
    i = len(np.intersect1d(a, b)); u = len(a) + len(b) - i
    return i / u if u else 0.0


def cluster(items, thr, key=lambda x: x):
    """items sorted best first; keeps one per cluster (same dir and horizon; entry-set Jaccard >= thr)."""
    kept = []
    for it in items:
        if not any(k["d"] == it["d"] and k["H"] == it["H"] and jaccard(k["idx"], it["idx"]) >= thr for k in kept):
            kept.append(it)
    return kept


def cmd_discover(nn, nrules):
    seed = 1000 + nn
    D = get_discovery(); S = D["S"]
    t0 = time.time()
    M = atom_masks(S, D["cuts"])
    sc = Scorer(S, M)
    seen = ledger_seen()
    rules = gen_rules(seed, nrules, seen)
    path = os.path.join(LEDGER_DIR, "RUN%02d_%s.ids.gz" % (nn, GROUP))
    os.makedirs(LEDGER_DIR, exist_ok=True)
    assert not os.path.exists(path), "ledger already exists: runs are append-only and never rerun"
    surv, npass0, ntrades0 = [], 0, 0
    best = None; stats = dict(rules=len(rules), ge200=0)
    for b in range(0, len(rules), 500):
        batch = rules[b:b + 500]
        ledger_append(path, batch)                                  # BEFORE scoring the batch
        for s in batch:
            atoms, d, H = parse(s)
            idx, ign, drop = sc.select(atoms, H)
            m = metrics(S, idx, d, H)
            if m is None:
                continue
            if m["n"] >= 200:
                stats["ge200"] += 1
                if best is None or m["pf"] > best[0]["pf"]:
                    best = (m, s)
            if disc_pass(m):
                surv.append(dict(rule=s, d=d, H=H, idx=idx, m=m))
    surv.sort(key=lambda x: -x["m"]["pf"])
    kept = cluster(surv, 0.9)
    fz = dict(frozen_id="CRYPTOPRICE_R%02d" % nn, group="CRYPTO", slice=GROUP, seed=seed, cuts_sha256=D["cuts_sha"], n_rules=len(rules),
              discovery_survivors=len(surv), clusters=len(kept),
              survivors=[dict(rule=k["rule"], disc={a: (round(b, 6) if isinstance(b, float) else b) for a, b in k["m"].items()}) for k in kept])
    fpath = os.path.join(WORK, "PERPGEN_FROZEN_CRYPTOPRICE_R%02d.json" % nn)
    blob = json.dumps(fz, sort_keys=True, indent=1)
    open(fpath, "w").write(blob)
    print("RUN%02d discover: rules %d, scored n>=200: %d, disc survivors %d, clusters %d, best disc PF %s, frozen sha256 %s, %.0fs" % (
        nn, len(rules), stats["ge200"], len(surv), len(kept), ("%.3f (n %d) %s" % (best[0]["pf"], best[0]["n"], best[1])) if best else "none",
        hashlib.sha256(blob.encode()).hexdigest(), time.time() - t0))
    return fz


def cmd_rescore(nn):
    """Re-score an existing ledger's rules (deterministic, writes nothing) to report per-stage counts for the results file."""
    D = get_discovery(); S = D["S"]; sc = Scorer(S, atom_masks(S, D["cuts"]))
    rules = read_lines(os.path.join(LEDGER_DIR, "RUN%02d_%s.ids.gz" % (nn, GROUP)))
    c = dict(rules=len(rules), n200=0, pf13=0, halves=0, conc=0, mean24=0, surv=0); best = None
    for s in rules:
        atoms, d, H = parse(s)
        idx, _, _ = sc.select(atoms, H); m = metrics(S, idx, d, H)
        if m is None or m["n"] < 200:
            continue
        c["n200"] += 1
        if m["dates"] >= 20 and m["pf"] >= 1.3:
            c["pf13"] += 1
            if m["pf1"] > 1 and m["pf2"] > 1:
                c["halves"] += 1
                if m["mean24"] > 0:
                    c["mean24"] += 1
                    if m["top"] <= 0.25:
                        c["surv"] += 1
        if best is None or m["pf"] > best[0]:
            best = (m["pf"], m["n"])
    print("RUN%02d rules %d | n>=200 %d | +dates>=20,PF>=1.3 %d | +both halves>1 %d | +mean24>0 %d | +top date<=25%% (survivors) %d | best disc PF %.3f (n %d)" % (
        nn, c["rules"], c["n200"], c["pf13"], c["halves"], c["mean24"], c["surv"], best[0], best[1]))


if __name__ == "__main__":
    cmd = sys.argv[1]
    nn = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    nr = int(sys.argv[sys.argv.index("--rules") + 1]) if "--rules" in sys.argv else 5000
    if cmd == "discover":
        cmd_discover(nn, nr)
    if cmd == "rescore":
        cmd_rescore(nn)
