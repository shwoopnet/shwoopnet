"""MECHOI1 (workers/MECHOI1_REGISTRATION.md): WHY does the Bitcoin open interest core (REF_GEN6_OICORE) work?
A pre-registered mechanism decomposition of OICORE's own windows. No new trade rule; research only, nothing here
places an order, reads a key or decides anything live.
    PYTHONPATH=src python -m scalper.mechoi1 counts    (distinct dates and the thirds; reads no outcome)
    PYTHONPATH=src python -m scalper.mechoi1 fetch     (OKX BTC-USDT 1 minute closes for the first two thirds only)
    PYTHONPATH=src python -m scalper.mechoi1 parity    (OICORE's published discovery 222 / 2.28 reproduced by this loader)
    PYTHONPATH=src python -m scalper.mechoi1 score     (ONCE; refuses a second run)
Fill, fee and the 180 s row are gen6.window_rows / gen6.vfee / gen6.pf (not re-implemented).
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from datetime import datetime, timezone

import numpy as np

from . import gen6, oicorex1
from .paths import DATA_DIR

SERIES = "KXBTC15M"
FIXED = 86299.56000000001
C = 10
B_REPS = 2000
SEED = 7
TRAIL_S = 86400                  # trailing window for the relative threshold
TRAIL_GAP_S = 900                # only windows closed at least 900 s before this close (their doi is known)
TRAIL_MIN = 40                   # windows needed in the trailing day
PCT = 90
SIG_MIN_RETURNS = 50             # of the 60 one minute returns before the look
LUMPY = 0.60                     # share of the 3 minute open interest change that fell in one minute
UNCH = 0.01 + 1e-9               # ask unchanged: |ask(-180) - ask(-360)| <= 1c
FAR_Q, NEAR_Q = 1 / 3, 2 / 3
DROP_MIN_N = 60
OUT = DATA_DIR / "mechoi1"
KLINES = OUT / "klines.json"
SCORE = DATA_DIR / "mechoi1_score.json"
RESULT_MD = DATA_DIR.parent / "workers" / "MECHOI1_RESULT.md"

# decision thresholds, fixed in the registration before any outcome
TH = {
    "M1_ratio": 1.20, "M1_lean_abs": 0.10, "M1_dir_exc": 0.03, "M1_far_near": 0.03,
    "M2_lean_sig": 0.15, "M2_lean_post": 0.10, "M2_split": 0.05, "M2_exc": 0.03,
    "M3_split": 0.04, "M3_exc": 0.03, "M3_spread": 0.005,
    "M4_split": 0.04, "M4_exc": 0.03,
}


def _ts(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


def day_of(ct):
    return datetime.fromtimestamp(ct, timezone.utc).strftime("%Y-%m-%d")


# ----------------------------------------------------------------- windows

def strikes():
    out = {}
    for name in oicorex1.BTC_FILES:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        for tk, k in db.execute("select ticker, strike from market where series=?", (SERIES,)):
            if tk not in out and k is not None:
                out[tk] = float(k)
    return out


def all_windows():
    """Settled Bitcoin windows with a usable open interest pair at -360 and -180, in close order (no row filter yet)."""
    return oicorex1.window_list(SERIES, gen6.DISC[0], _ts(2026, 11, 8))


def split_dates(dates):
    k = len(dates) // 3
    return dates[:k], dates[k:2 * k], dates[2 * k:]


def build_record(tk, ct, res, cs, strike):
    """One OICORE-style record: the 180 s row (YES first), plus the context the mechanisms need. None if no cheaper side."""
    rows, _ = gen6.window_rows("KXBTC15M", ct, cs, {})
    r = [x for x in rows if x["L"] == 180]
    if not r:
        return None
    r = r[0]
    q180, q360 = cs[ct - 180], cs[ct - 360]
    yes = int(r["yes"])
    s180 = gen6._sq(q180, yes)
    s360 = gen6._sq(q360, yes)
    oi = [cs.get(ct - s) for s in (360, 300, 240, 180)]
    oiv = [None if o is None else o[3] for o in oi]
    d3 = None
    if all(v is not None for v in oiv):
        d3 = [oiv[1] - oiv[0], oiv[2] - oiv[1], oiv[3] - oiv[2]]
    return {"tk": tk, "ct": ct, "day": day_of(ct), "res": res, "yes": yes, "d": 1 if yes else -1, "fill": r["fill"], "sig": r["sig_ask"],
            "win": 1.0 if (res == "yes") == bool(yes) else 0.0, "doi": q180[3] - q360[3], "level": q360[3], "d3": d3,
            "ask180": s180[1], "ask360": s360[1], "spr180": q180[1] - q180[0], "spr360": q360[1] - q360[0],
            "strike": strike, "zv": bool(r["zv_entry"])}


def build_records(dates_keep):
    K = strikes()
    keep = set(dates_keep)
    recs, nwin = [], 0
    for tk, ct, res, cs in all_windows():
        if day_of(ct) not in keep:
            continue
        nwin += 1
        rec = build_record(tk, ct, res, cs, K.get(tk))
        if rec is not None:
            recs.append(rec)
    return recs, nwin


def trailing_thr(recs):
    """Per record: the 90th percentile of doi over records closing in [ct - 24h, ct - 900 s]; None if fewer than TRAIL_MIN.
    Also the 10th percentile (used only for the registered drop fallback)."""
    cts = np.array([r["ct"] for r in recs])
    dois = np.array([r["doi"] for r in recs])
    hi, lo10 = [], []
    for r in recs:
        m = (cts >= r["ct"] - TRAIL_S) & (cts <= r["ct"] - TRAIL_GAP_S)
        if m.sum() < TRAIL_MIN:
            hi.append(np.nan); lo10.append(np.nan)
        else:
            hi.append(float(np.percentile(dois[m], PCT))); lo10.append(float(np.percentile(dois[m], 100 - PCT)))
    return np.array(hi), np.array(lo10)


# ----------------------------------------------------------------- spot

def load_klines():
    d = json.loads(KLINES.read_text())
    return {int(k): v for k, v in d.items()}


def spot_at(K, t):
    """Close of the one minute kline that ends at t (opens at t - 60)."""
    return K.get(t - 60)


def sigma_min(K, t):
    """Std of the 60 one minute log returns ending at t; nan if fewer than SIG_MIN_RETURNS exist."""
    px = [K.get(t - 60 * i) for i in range(0, 61)]
    r = [math.log(px[i] / px[i + 1]) for i in range(60) if px[i] and px[i + 1]]
    if len(r) < SIG_MIN_RETURNS:
        return float("nan")
    return float(np.std(r, ddof=1))


def add_spot(recs, K):
    for r in recs:
        ct = r["ct"]
        s360, s180, s0 = spot_at(K, ct - 360), spot_at(K, ct - 180), spot_at(K, ct)
        r["spot_ok"] = bool(s360 and s180 and s0 and r["strike"])
        sg = sigma_min(K, ct - 180) * math.sqrt(3) if r["spot_ok"] else float("nan")
        r["sigw"] = sg
        if r["spot_ok"]:
            r["post"] = math.log(s0 / s180)
            r["sigmv"] = math.log(s180 / s360)
            r["gap"] = r["d"] * math.log(s180 / r["strike"])
            r["proxy_ok"] = ((s0 >= r["strike"]) == (r["res"] == "yes"))
        else:
            r["post"] = r["sigmv"] = r["gap"] = float("nan")
            r["proxy_ok"] = None


# ----------------------------------------------------------------- arrays and statistics

def arrays(recs, K=None):
    g = lambda k: np.array([r[k] for r in recs], dtype=np.float64)
    days = sorted({r["day"] for r in recs})
    A = {k: g(k) for k in ("ct", "d", "fill", "win", "doi", "ask180", "ask360", "spr180", "spr360")}
    A["day"] = np.array([days.index(r["day"]) for r in recs])
    A["days"] = days
    A["exc"] = A["win"] - A["fill"]
    A["net"] = A["win"] - A["fill"] - gen6.vfee(A["fill"], C)
    A["post"], A["sigmv"], A["gap"], A["sigw"] = (g(k) for k in ("post", "sigmv", "gap", "sigw"))
    A["ok"] = np.array([bool(r.get("spot_ok")) for r in recs])
    with np.errstate(invalid="ignore", divide="ignore"):
        A["okz"] = A["ok"] & np.isfinite(A["sigw"]) & (A["sigw"] > 0)
        A["apost"] = np.abs(A["post"])
        A["asig"] = np.abs(A["sigmv"])
        A["apost_sd"] = A["apost"] / A["sigw"]
        A["dpost_sd"] = A["d"] * A["post"] / A["sigw"]
        A["dsig_sd"] = A["d"] * A["sigmv"] / A["sigw"]
        A["zg"] = A["gap"] / A["sigw"]
    A["unch"] = np.abs(A["ask180"] - A["ask360"]) <= UNCH
    sh = np.full(len(recs), np.nan)
    for i, r in enumerate(recs):
        if r["d3"] is not None:
            a = np.abs(r["d3"]); s = a.sum()
            sh[i] = a.max() / s if s > 0 else np.nan
    A["share"] = sh
    A["lumpy"] = sh >= LUMPY
    return A


def dm(x, m):
    v = x[m]
    v = v[np.isfinite(v)]
    return float(v.mean()) if len(v) else float("nan")


def day_base(A, Bm, key):
    """Per record: the mean of `key` over baseline records of the same date with spot (nan if none)."""
    out = np.full(len(A["ct"]), np.nan)
    for d in np.unique(A["day"]):
        m = (A["day"] == d) & Bm & A["ok"]
        if m.any():
            out[A["day"] == d] = A[key][m].mean()
    return out


def make_ctx(A, T, Bm):
    z = A["zg"][Bm & A["okz"]]
    ctx = {"A": A, "T": T, "B": Bm, "q_far": float(np.quantile(z, FAR_Q)), "q_near": float(np.quantile(z, NEAR_Q)),
           "dbp": day_base(A, Bm, "apost"), "dbs": day_base(A, Bm, "asig")}
    return ctx


def stat_vector(idx, ctx):
    A, T0, B0 = ctx["A"], ctx["T"], ctx["B"]
    t, b = T0[idx], B0[idx]
    g = lambda k: A[k][idx]
    exc, net, fill, win = g("exc"), g("net"), g("fill"), g("win")
    ok, okz, d = g("ok"), g("okz"), g("d")
    o = {}
    o["n_t"] = float(t.sum())
    o["win_t"], o["fill_t"] = dm(win, t), dm(fill, t)
    o["exc_t"], o["exc_b"] = dm(exc, t), dm(exc, b)
    o["exc_diff"] = o["exc_t"] - o["exc_b"]
    o["net_t"], o["net_b"] = dm(net, t), dm(net, b)
    nt = net[t]
    w, l = nt[nt > 0].sum(), -nt[nt < 0].sum()
    o["pf_t"] = float(w / l) if l > 0 else float("nan")
    nb = net[b]
    w, l = nb[nb > 0].sum(), -nb[nb < 0].sum()
    o["pf_b"] = float(w / l) if l > 0 else float("nan")
    # M1
    tm = t & ok
    den = ctx["dbp"][idx][tm]
    den = den[np.isfinite(den)]
    num = g("apost")[tm][np.isfinite(ctx["dbp"][idx][tm])]
    o["R_post"] = float(num.sum() / den.sum()) if len(den) and den.sum() > 0 else float("nan")
    den = ctx["dbs"][idx][tm]
    den = den[np.isfinite(den)]
    num = g("asig")[tm][np.isfinite(ctx["dbs"][idx][tm])]
    o["R_sig"] = float(num.sum() / den.sum()) if len(den) and den.sum() > 0 else float("nan")
    a, bb = dm(g("apost_sd"), t & okz), dm(g("apost_sd"), b & okz)
    o["R_post_sd"] = a / bb if bb and bb > 0 else float("nan")
    o["lean_post"] = dm(g("dpost_sd"), t & okz) - dm(g("dpost_sd"), b & okz)
    o["lean_sig"] = dm(g("dsig_sd"), t & okz) - dm(g("dsig_sd"), b & okz)
    o["exc_yes_t"], o["exc_no_t"] = dm(exc, t & (d > 0)), dm(exc, t & (d < 0))
    zg = g("zg")
    far, near = okz & (zg <= ctx["q_far"]), okz & (zg >= ctx["q_near"])
    o["exc_far_t"], o["exc_near_t"] = dm(exc, t & far), dm(exc, t & near)
    o["far_near_t"] = o["exc_far_t"] - o["exc_near_t"]
    o["far_near_b"] = dm(exc, b & far) - dm(exc, b & near)
    # M2
    ds = g("dsig_sd")
    pos, neg = okz & (ds > 0), okz & (ds <= 0)
    o["exc_dpos_t"], o["exc_dneg_t"] = dm(exc, t & pos), dm(exc, t & neg)
    o["dsplit_t"] = o["exc_dpos_t"] - o["exc_dneg_t"]
    o["share_dpos_t"], o["share_dpos_b"] = dm(pos.astype(float), t & okz), dm(pos.astype(float), b & okz)
    # M3
    u = g("unch")
    o["share_unch_t"], o["share_unch_b"] = dm(u.astype(float), t), dm(u.astype(float), b)
    o["exc_unch_t"], o["exc_mov_t"] = dm(exc, t & u), dm(exc, t & ~u)
    o["unch_split_t"] = o["exc_unch_t"] - o["exc_mov_t"]
    s = g("spr180")
    o["spread_t"] = float(np.median(s[t])) if t.any() else float("nan")
    o["spread_b"] = float(np.median(s[b])) if b.any() else float("nan")
    o["spread_diff"] = o["spread_t"] - o["spread_b"]
    # M4
    sh = g("share")
    lk, ev = np.isfinite(sh) & (sh >= LUMPY), np.isfinite(sh) & (sh < LUMPY)
    o["share_lumpy_t"], o["share_lumpy_b"] = dm(lk.astype(float), t & np.isfinite(sh)), dm(lk.astype(float), b & np.isfinite(sh))
    o["exc_lumpy_t"], o["exc_even_t"] = dm(exc, t & lk), dm(exc, t & ev)
    o["lumpy_split_t"] = o["exc_lumpy_t"] - o["exc_even_t"]
    o["n_lumpy_t"], o["n_even_t"] = float((t & lk).sum()), float((t & ev).sum())
    return o


def boot(A, ctx, reps=B_REPS, seed=SEED):
    """Point values plus day-clustered bootstrap (dates resampled with replacement) 2.5 and 97.5 percentiles."""
    n = len(A["ct"])
    point = stat_vector(np.arange(n), ctx)
    by_day = [np.flatnonzero(A["day"] == d) for d in range(len(A["days"]))]
    rng = np.random.default_rng(seed)
    keys = list(point)
    M = np.full((reps, len(keys)), np.nan)
    for i in range(reps):
        pick = rng.integers(0, len(by_day), len(by_day))
        idx = np.concatenate([by_day[j] for j in pick])
        v = stat_vector(idx, ctx)
        M[i] = [v[k] for k in keys]
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lo = np.nanpercentile(M, 2.5, axis=0)
            hi = np.nanpercentile(M, 97.5, axis=0)
    return {k: (point[k], float(lo[j]), float(hi[j])) for j, k in enumerate(keys)}


# ----------------------------------------------------------------- decision

def _p(S, k):
    return S[k][0]


def _lo(S, k):
    return S[k][1]


def _ok(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def decide(S):
    """Mechanism labels from the stat dict (point, lo, hi) of the PRIMARY version. SUPPORTED needs every line;
    LEANING means the headline points pass and a confidence interval crosses its line; otherwise NOT SUPPORTED."""
    ge = lambda x, th: _ok(x) and x >= th
    out = {}
    # M1 volatility event
    a_pt, a_ci = ge(_p(S, "R_post"), TH["M1_ratio"]), _lo(S, "R_post") > 1.0
    b_pt = _ok(_p(S, "lean_post")) and abs(_p(S, "lean_post")) <= TH["M1_lean_abs"]
    c_pt = ge(_p(S, "exc_yes_t"), TH["M1_dir_exc"]) and ge(_p(S, "exc_no_t"), TH["M1_dir_exc"])
    d_pt = ge(_p(S, "far_near_t"), TH["M1_far_near"])
    out["M1"] = "SUPPORTED" if (a_pt and a_ci and b_pt and c_pt and d_pt) else ("LEANING" if (a_pt and c_pt) else "NOT SUPPORTED")
    out["M1_lines"] = {"ratio": (a_pt, a_ci), "no_lean": b_pt, "both_directions": c_pt, "far_gt_near": d_pt}
    # M2 informed direction
    a_pt, a_ci = ge(_p(S, "lean_sig"), TH["M2_lean_sig"]), _lo(S, "lean_sig") > 0
    b_pt, b_ci = ge(_p(S, "lean_post"), TH["M2_lean_post"]), _lo(S, "lean_post") > 0
    c_pt = ge(_p(S, "dsplit_t"), TH["M2_split"]) and ge(_p(S, "exc_dpos_t"), TH["M2_exc"])
    out["M2"] = "SUPPORTED" if (a_pt and a_ci and b_pt and b_ci and c_pt) else ("LEANING" if (b_pt and (a_pt or c_pt)) else "NOT SUPPORTED")
    out["M2_lines"] = {"sig_lean": (a_pt, a_ci), "post_lean": (b_pt, b_ci), "concentrated": c_pt}
    # M3 stale maker
    s_pt, s_ci = ge(_p(S, "unch_split_t"), TH["M3_split"]), _lo(S, "unch_split_t") > 0
    e_pt = ge(_p(S, "exc_unch_t"), TH["M3_exc"])
    w_pt = _ok(_p(S, "spread_diff")) and _p(S, "spread_diff") <= TH["M3_spread"]
    out["M3"] = "SUPPORTED" if (s_pt and s_ci and e_pt and w_pt) else ("LEANING" if s_pt else "NOT SUPPORTED")
    out["M3_lines"] = {"split": (s_pt, s_ci), "unchanged_pays": e_pt, "spread_not_wider": w_pt}
    # M4 lumpy
    s_pt, s_ci = ge(_p(S, "lumpy_split_t"), TH["M4_split"]), _lo(S, "lumpy_split_t") > 0
    e_pt = ge(_p(S, "exc_lumpy_t"), TH["M4_exc"])
    out["M4"] = "SUPPORTED" if (s_pt and s_ci and e_pt) else ("LEANING" if s_pt else "NOT SUPPORTED")
    out["M4_lines"] = {"split": (s_pt, s_ci), "lumpy_pays": e_pt}
    return out


# ----------------------------------------------------------------- run

def masks(A, recs, version):
    """(rise, drop, baseline, drop_fallback) boolean masks for 'fixed' or 'rel'."""
    doi = A["doi"]
    if version == "fixed":
        elig = np.ones(len(doi), bool)
        rise, drop = doi > FIXED, doi < -FIXED
        drop2 = np.zeros(len(doi), bool)
        base = ~rise & ~drop
    else:
        hi, lo10 = trailing_thr(recs)
        elig = np.isfinite(hi)
        with np.errstate(invalid="ignore"):
            rise = elig & (doi > hi)
            drop = elig & (doi < -hi)
            drop2 = elig & np.isfinite(lo10) & (lo10 < 0) & (doi < lo10)
            base = elig & ~rise & ~drop & ~drop2
    return rise & elig, drop & elig, base, drop2


def fmt(v, nd=3):
    return "nan" if not _ok(v) else f"{v:.{nd}f}"


def line(S, k, nd=3, scale=1.0):
    p, lo, hi = S[k]
    return f"{fmt(p * scale, nd)} [{fmt(lo * scale, nd)}, {fmt(hi * scale, nd)}]"


def run_all(recs, K_ok=True):
    A = arrays(recs)
    res = {}
    for version in ("fixed", "rel"):
        rise, drop, base, drop2 = masks(A, recs, version)
        specs = {"rise": rise, "drop": drop}
        if version == "rel":
            specs["drop_p10"] = drop2
        for name, T in specs.items():
            if T.sum() < 5:
                res[f"{version}_{name}"] = {"n": int(T.sum()), "stats": None}
                continue
            ctx = make_ctx(A, T, base)
            res[f"{version}_{name}"] = {"n": int(T.sum()), "n_base": int(base.sum()), "stats": boot(A, ctx),
                                        "q_far": ctx["q_far"], "q_near": ctx["q_near"]}
    return A, res


def score():
    if SCORE.exists():
        print("refusing: MECHOI1 was already scored once (", SCORE, ")"); return
    w1, w2, w3 = split_dates(dates_all())
    keep = set(w1) | set(w2)
    recs, nwin = build_records(keep)          # the holdout dates are never turned into records
    K = load_klines()
    add_spot(recs, K)
    A, res = run_all(recs)
    # data check: how often the OKX close side matches the Kalshi result
    pr = [r["proxy_ok"] for r in recs if r["proxy_ok"] is not None]
    meta = {"records": len(recs), "windows": nwin, "dates_used": len(keep), "w1": [w1[0], w1[-1]], "w2": [w2[0], w2[-1]],
            "holdout_untouched": [w3[0], w3[-1]], "spot_ok": int(A["ok"].sum()), "proxy_agree": float(np.mean(pr)) if pr else None}
    # halves
    halves = {}
    for name, ds in (("W1", set(w1)), ("W2", set(w2))):
        sub = [r for r in recs if r["day"] in ds]
        Ah = arrays(sub)
        rise, _, base, _ = masks(Ah, sub, "fixed")
        if rise.sum() >= 5:
            halves[name] = {"n": int(rise.sum()), "stats": stat_vector(np.arange(len(sub)), make_ctx(Ah, rise, base))}
    labels = {v: decide(res[f"{v}_rise"]["stats"]) for v in ("fixed", "rel") if res[f"{v}_rise"]["stats"]}
    payload = {"meta": meta, "res": {k: ({"n": v["n"], "stats": v["stats"]} if v["stats"] else v) for k, v in res.items()},
               "labels": labels, "halves": halves, "th": TH}
    SCORE.write_text(json.dumps(payload, indent=1, default=lambda o: None if (isinstance(o, float) and math.isnan(o)) else o))
    write_md(payload)
    print(RESULT_MD.read_text())


def dates_all():
    return sorted({day_of(ct) for _, ct, _, _ in all_windows()})


def write_md(P):
    L = []
    m = P["meta"]
    L.append("# MECHOI1 result (auto-generated by `scalper.mechoi1 score`; interpretation is in README.md)\n")
    L.append(f"Windows with a cheaper side in the first two thirds: {m['records']} of {m['windows']} with a usable open interest pair; "
             f"dates {m['w1'][0]} to {m['w2'][1]} ({m['dates_used']} dates). Holdout {m['holdout_untouched'][0]} to {m['holdout_untouched'][1]} not read. "
             f"Spot available: {m['spot_ok']}. OKX close on the right side of the strike as Kalshi settled: {fmt(m['proxy_agree'])}.\n")
    for key, R in P["res"].items():
        S = R["stats"]
        L.append(f"\n## {key}: n {R['n']}")
        if not S:
            L.append("NOT_ENOUGH_DATA (fewer than 5 windows)"); continue
        L.append("| statistic | point [95% day-clustered CI] |\n|---|---|")
        for k, (p, lo, hi) in S.items():
            sc = 100.0 if k in ("exc_t", "exc_b", "exc_diff", "net_t", "net_b", "exc_yes_t", "exc_no_t", "exc_far_t", "exc_near_t", "far_near_t", "far_near_b",
                                "exc_dpos_t", "exc_dneg_t", "dsplit_t", "exc_unch_t", "exc_mov_t", "unch_split_t", "exc_lumpy_t", "exc_even_t", "lumpy_split_t", "spread_diff", "spread_t", "spread_b") else 1.0
            nd = 1 if sc == 100.0 else 3
            L.append(f"| {k}{' (cents)' if sc == 100.0 else ''} | {fmt(p * sc, nd)} [{fmt(lo * sc, nd)}, {fmt(hi * sc, nd)}] |")
    L.append("\n## Labels (primary: fixed 86,299.56 rise; second version: relative trailing 24h p90 rise)")
    for v, lab in P["labels"].items():
        L.append(f"- {v}: M1 {lab['M1']}, M2 {lab['M2']}, M3 {lab['M3']}, M4 {lab['M4']}")
        for mk in ("M1", "M2", "M3", "M4"):
            L.append(f"  - {mk} lines: {lab[mk + '_lines']}")
    L.append("\n## Halves (fixed rise, point values)")
    for h, R in P["halves"].items():
        S = R["stats"]
        L.append(f"- {h}: n {R['n']}, exc {fmt(S['exc_t'] * 100, 1)}c, R_post {fmt(S['R_post'])}, lean_post {fmt(S['lean_post'])}, "
                 f"unch_split {fmt(S['unch_split_t'] * 100, 1)}c, lumpy_split {fmt(S['lumpy_split_t'] * 100, 1)}c, PF {fmt(S['pf_t'], 2)}")
    RESULT_MD.write_text("\n".join(L) + "\n")


# ----------------------------------------------------------------- cli

def counts():
    ds = dates_all()
    w1, w2, w3 = split_dates(ds)
    print(f"dates {len(ds)}: W1 {w1[0]}..{w1[-1]} ({len(w1)}), W2 {w2[0]}..{w2[-1]} ({len(w2)}), W3 (frozen) {w3[0]}..{w3[-1]} ({len(w3)})")
    print("settled windows with usable OI pair:", len(all_windows()))


def fetch():
    from . import lag15
    ds = dates_all()
    w1, w2, _ = split_dates(ds)
    lo = int(datetime.strptime(w1[0], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()) - 4500
    hi = int(datetime.strptime(w2[-1], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()) + 86400 + 900
    OUT.mkdir(parents=True, exist_ok=True)
    k = lag15.okx_klines("BTC-USDT", lo, hi)
    KLINES.write_text(json.dumps({str(a): b for a, b in sorted(k.items())}))
    print("klines", len(k), min(k), max(k))


def parity():
    """OICORE's published discovery figures (n 222, PF 2.28) must come out of this loader. Discovery lies wholly in the first two thirds."""
    w1, w2, _ = split_dates(dates_all())
    recs, _ = build_records(set(w1) | set(w2))
    disc = [r for r in recs if gen6.DISC[0] <= r["ct"] < gen6.DISC[1]]
    A = arrays(disc)
    m = A["doi"] > FIXED
    v = A["net"][m]
    print("discovery fixed rise n", int(m.sum()), "PF", round(gen6.pf(v), 2), "(published 222, 2.28)")


if __name__ == "__main__":
    {"counts": counts, "fetch": fetch, "parity": parity, "score": score}[sys.argv[1]]()
