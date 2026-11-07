"""BINPATH: rules on the UNDERLYING Binance BTC and ETH minute path, priced by a fitted QUOTE MODEL, scored by the shared harness (scan.py).
Research only: no order, no key, no network, no trading code. EVERY RESULT FROM THIS FILE IS A MODEL RESULT, NEVER A LIVE FIGURE.
Protocol (registered before any rule was scored): workers/BINPATH_PROTOCOL.md.  scan.py is imported and not edited.

    python3 -I src/scalper/scan_binance.py model                 proxy error vs Kalshi results and the quote model fit (Kalshi development windows only)
    python3 -I src/scalper/scan_binance.py unseen                counts of the held-out windows (never read)
    python3 -I src/scalper/scan_binance.py baseline --sym BTC --arm band     unconditional entries per window (ledgered)
    python3 -I src/scalper/scan_binance.py run --sym BTC --arm band --n 5000 --seed 91001     one RUN (ledger first, then score)
    python3 -I src/scalper/scan_binance.py audit --run <file>     truncation, reverse control, fee stress on the survivors of a run file

The held-out (closes from 2025-01-01) is reachable only through BinAdapter.build_holdout, which needs scan's guard file; this task never calls it."""
from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import random
import sqlite3
import sys
import time
from datetime import datetime, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scan as S            # noqa: E402  (the shared harness; same module the harness CLI uses)
import histbinance as HB    # noqa: E402

ROOT = S.ROOT
CACHE = os.path.join(S.SCAN_DATA, "binpath")
MODEL_FILE = os.path.join(S.WORKERS, "BINPATH_QUOTE_MODEL.json")

T0 = int(datetime(2019, 1, 1, tzinfo=timezone.utc).timestamp())
T_END = int(datetime(2026, 11, 7, tzinfo=timezone.utc).timestamp())
W_CUTS = (int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()), int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp()))
HOLD_LO = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())           # closes on or after this are the held-out, guarded
FIRST_CLOSE = T0 + 2 * 86400                                                   # the 1440 minute volume baseline needs two days of bars
LOOKS = (360, 600)
ARMS = {"band": (0.88, 0.97), "cheap": (0.03, 0.30)}
SYMS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}
KALSHI_SERIES = {"BTC": "KXBTC15M", "ETH": "KXETH15M"}
SIGMA_FLOOR = 1.0
FEATS = ["ask", "dist", "zd", "r1", "r3", "r5", "r9", "vol15", "vol60", "rng5", "rng15", "mrise3", "mrng5", "vlr15", "tbi5", "fmin", "fr_last", "hour"]
CATS = ["hod4", "dow"]


class Blocked(S.Blocked):
    pass


# ------------------------------------------------------------------ normal cdf (no scipy)
def erf(x):
    x = np.asarray(x, dtype=np.float64)
    s = np.sign(x); a = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * a)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-a * a)
    return s * y


def Phi(u):
    return 0.5 * (1.0 + erf(np.asarray(u, dtype=np.float64) / math.sqrt(2.0)))


def phi(u):
    u = np.asarray(u, dtype=np.float64)
    return np.exp(-0.5 * u * u) / math.sqrt(2.0 * math.pi)


# ------------------------------------------------------------------ data grid (one minute, NaN where a minute is missing)
class Grid:
    """Minute grid from `t0`: arrays o h l c v tbv (NaN = missing minute). A slice keeps the same code path for the truncation audit."""

    def __init__(self, t0, o, h, l, c, v, tbv):
        self.t0, self.o, self.h, self.l, self.c, self.v, self.tbv = t0, o, h, l, c, v, tbv
        self.lc = np.log(c)
        self._cv = None

    @property
    def cv(self):
        if self._cv is None:
            self._cv = np.r_[0.0, np.cumsum(np.where(np.isnan(self.v), 0.0, self.v))]
        return self._cv

    def slice(self, a, b):
        a = max(0, a)
        return Grid(self.t0 + 60 * a, self.o[a:b], self.h[a:b], self.l[a:b], self.c[a:b], self.v[a:b], self.tbv[a:b])


def load_grid(sym):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, "%s_spot1m.npz" % sym)
    if os.path.exists(p):
        z = np.load(p)
        return Grid(T0, z["o"], z["h"], z["l"], z["c"], z["v"], z["tbv"])
    rows = HB.load(SYMS[sym], "spot_1m")
    n = (T_END - T0) // 60
    arr = {k: np.full(n, np.nan) for k in "ohlcv"}
    arr["tbv"] = np.full(n, np.nan)
    a = np.array(rows, dtype=np.float64)
    idx = ((a[:, 0] - T0) // 60).astype(np.int64)
    ok = (idx >= 0) & (idx < n)
    idx = idx[ok]; a = a[ok]
    for k, j in (("o", 1), ("h", 2), ("l", 3), ("c", 4), ("v", 5), ("tbv", 7)):
        arr[k][idx] = a[:, j]
    np.savez(p, **arr)
    return Grid(T0, arr["o"], arr["h"], arr["l"], arr["c"], arr["v"], arr["tbv"])


def load_funding(sym):
    f = np.array(HB.load(SYMS[sym], "funding"), dtype=np.float64)
    return f[:, 0].astype(np.int64), f[:, 2] * 1e4          # settle ts, rate in bp


# ------------------------------------------------------------------ the quote model (form fixed in the protocol)
def default_model():
    return {"360": [0.0, 1.0], "600": [0.0, 1.0], "h": [0.005, 0.005, 0.005], "fitted": False}


def zone_of(mid):
    return np.where(mid < 0.30, 0, np.where(mid > 0.70, 2, 1))


def mid_from_z(model, L, z):
    c0, c1 = model[str(L)]
    return Phi(c0 + c1 * z)


def gather(a, idx, lo, hi):
    """a over [idx+lo, idx+hi] inclusive for every idx; (n, hi-lo+1)."""
    return a[idx[:, None] + np.arange(lo, hi + 1)[None, :]]


def core(G, idd, ido, L, model):
    """Distance, sigma15, z and the modelled YES mid / both asks at decision-bar indices idd (open-bar indices ido). Uses bars <= idd only
    (plus the open bar, which is <= idd). Returns dict; NaN where a needed bar is missing."""
    lc = G.lc
    d = 1e4 * (lc[idd] - np.log(G.o[ido]))
    R = np.diff(gather(lc, idd, -15, 0), axis=1)                       # the 15 one minute log returns ending at the decision bar
    sig = np.sqrt(np.mean(R * R, axis=1) - np.mean(R, axis=1) ** 2) * 1e4
    sig = np.maximum(sig, SIGMA_FLOOR)
    tau = L / 60.0
    z = d / (sig * math.sqrt(tau))
    mid = mid_from_z(model, L, z)
    h = np.array(model["h"])[zone_of(mid)]
    ask_yes = np.clip(np.round((mid + h) * 100.0) / 100.0, 0.01, 0.99)
    ask_no = np.clip(np.round(((1.0 - mid) + h) * 100.0) / 100.0, 0.01, 0.99)
    return dict(d=d, sig=sig, z=z, mid=mid, h=h, ask_yes=ask_yes, ask_no=ask_no)


def pick_side(cr, arm):
    """+1 buy YES, -1 buy NO, 0 none: the side whose rounded modelled ask is in the arm's range (at most one can be)."""
    lo, hi = ARMS[arm]
    y = (cr["ask_yes"] >= lo - 1e-9) & (cr["ask_yes"] <= hi + 1e-9)
    n = (cr["ask_no"] >= lo - 1e-9) & (cr["ask_no"] <= hi + 1e-9)
    return np.where(y, 1, np.where(n, -1, 0)).astype(np.int8)


def side_features(G, idd, ido, t, L, model, s, cr, fr_ts, fr_rate):
    """Feature matrix (len(idd), F) for rows with side sign s (+1 YES, -1 NO). Every input is a bar at or before idd, a funding settle at or before t."""
    n = len(idd)
    F = np.full((n, len(FEATS)), np.nan)
    lc = G.lc
    sf = s.astype(np.float64)
    ask = np.where(s > 0, cr["ask_yes"], cr["ask_no"])
    F[:, 0] = ask
    F[:, 1] = sf * cr["d"]
    F[:, 2] = sf * cr["z"]
    for j, m in ((3, 1), (4, 3), (5, 5), (6, 9)):
        F[:, j] = sf * 1e4 * (lc[idd] - lc[idd - m])
    F[:, 7] = cr["sig"]
    C61 = gather(lc, idd, -60, 0); R61 = np.diff(C61, axis=1)
    cnt = (~np.isnan(R61)).sum(1)
    with np.errstate(all="ignore"):
        v60 = np.nanstd(R61, axis=1) * 1e4
    F[:, 8] = np.where(cnt >= 54, v60, np.nan)
    Hh, Ll = gather(G.h, idd, -14, 0), gather(G.l, idd, -14, 0)
    with np.errstate(all="ignore"):
        F[:, 9] = (np.max(Hh[:, -5:], 1) - np.min(Ll[:, -5:], 1)) / G.c[idd] * 1e4
        F[:, 10] = (np.max(Hh, 1) - np.min(Ll, 1)) / G.c[idd] * 1e4
    # model-priced path of the side's mid at the minute marks t, t-60, ..., t-300 (the rise3 and rng5 analogues)
    R20 = np.diff(gather(lc, idd, -20, 0), axis=1)                      # returns ending at idd-19 .. idd, columns 0..19
    marks = []
    lo_ = np.log(G.o[ido])
    for j in range(6):
        dj = 1e4 * (lc[idd - j] - lo_)
        Rj = R20[:, 19 - j - 14: 19 - j + 1]
        sj = np.maximum(np.sqrt(np.mean(Rj * Rj, 1) - np.mean(Rj, 1) ** 2) * 1e4, SIGMA_FLOOR)
        my = mid_from_z(model, L, dj / (sj * math.sqrt(L / 60.0 + j)))
        marks.append(np.where(s > 0, my, 1.0 - my))
    Mk = np.stack(marks, 1)
    F[:, 11] = (Mk[:, 0] - Mk[:, 3]) * 100.0
    F[:, 12] = (np.max(Mk, 1) - np.min(Mk, 1)) * 100.0
    vsum15 = G.cv[idd + 1] - G.cv[idd - 14]
    vbase = (G.cv[idd + 1] - G.cv[idd + 1 - 1440]) / 96.0
    F[:, 13] = np.log((vsum15 + 1.0) / (vbase + 1.0))
    Vv, Tb = gather(G.v, idd, -4, 0), gather(G.tbv, idd, -4, 0)
    with np.errstate(all="ignore"):
        sv = np.sum(Vv, 1)
        F[:, 14] = sf * np.where(sv > 0, (2.0 * np.sum(Tb, 1) - sv) / sv, np.nan)
    F[:, 15] = (t % 28800) / 60.0
    k = np.searchsorted(fr_ts, t, side="right") - 1
    if len(fr_ts):
        okf = (k >= 0) & (t - fr_ts[np.maximum(k, 0)] <= 8 * 3600)
        F[:, 16] = np.where(okf, fr_rate[np.maximum(k, 0)], np.nan)
    F[:, 17] = (t % 86400) // 3600
    return F


def window_index(G, closes, L):
    """Indices of the decision bar, open bar and settle bar for window closes (unix s) at look L, and a validity mask: the open bar, the settle
    bar and the 16 closes ending at the decision bar all exist (and 20 returns for the rise marks, 1440 minutes of volume baseline are inside the grid)."""
    idd = (closes - L - 60 - G.t0) // 60
    ido = (closes - 900 - G.t0) // 60
    idc = (closes - 60 - G.t0) // 60
    ok = (ido >= 0) & (idd >= 1500) & (idc < len(G.c))
    idd_, ido_, idc_ = np.where(ok, idd, 1500), np.where(ok, ido, 0), np.where(ok, idc, 0)
    ok &= ~np.isnan(G.o[ido_]) & ~np.isnan(G.c[idc_]) & ~np.isnan(G.c[idd_])
    full = ~np.isnan(gather(G.c, idd_, -20, 0)).any(1)
    return idd, ido, idc, ok & full


# ------------------------------------------------------------------ Kalshi side: development windows, proxy error, model fit
def kalshi_dev_windows(sym):
    """KXBTC15M or KXETH15M settled windows closing before the frozen holdout cut (2026-10-28), with the candle quotes at the two looks."""
    db = sqlite3.connect("file:%s?mode=ro" % os.path.join(S.DATA, "fresh.sqlite"), uri=True)
    ser = KALSHI_SERIES[sym]
    out = []
    for tk, close_ts, res, strike in db.execute("SELECT ticker, close_ts, result, strike FROM market WHERE series = ? AND result IN ('yes','no') AND close_ts < ? ORDER BY close_ts",
                                                (ser, S.HOLD_FROM_TS)):
        q = {}
        for L in LOOKS:
            r = db.execute("SELECT bid_c, ask_c FROM candle WHERE ticker = ? AND end_ts = ?", (tk, close_ts - L)).fetchone()
            q[L] = r if r is not None and S._valid_quote(r[0], r[1]) else None
        out.append((close_ts, res, strike, q))
    db.close()
    return out


def kalshi_frame(sym, G):
    """Per Kalshi window and look: Binance core quantities and Kalshi quotes. Arrays; rows with a missing Binance bar are dropped."""
    kw = kalshi_dev_windows(sym)
    closes = np.array([k[0] for k in kw], dtype=np.int64)
    res = np.array([1 if k[1] == "yes" else 0 for k in kw])
    strike = np.array([k[2] for k in kw], dtype=np.float64)
    ud = np.unique(closes // 86400); parts = np.array_split(ud, 3)
    wmap = {int(d): w for w, p in enumerate(parts) for d in p}
    dayrank = {int(d): i for w, p in enumerate(parts) for i, d in enumerate(p)}
    win = np.array([wmap[int(c // 86400)] for c in closes]); drank = np.array([dayrank[int(c // 86400)] for c in closes])
    fr = []
    for L in LOOKS:
        idd, ido, idc, ok = window_index(G, closes, L)
        bid = np.array([k[3][L][0] if k[3][L] else np.nan for k in kw]); ask = np.array([k[3][L][1] if k[3][L] else np.nan for k in kw])
        fr.append(dict(L=L, closes=closes, idd=idd, ido=ido, idc=idc, ok=ok, bid=bid, ask=ask, res=res, strike=strike, win=win, drank=drank))
    return fr


def fit_mid(z, mid, iters=60):
    """Least squares (cents) of Phi(c0 + c1 z) on the YES mid; Levenberg-Marquardt on two parameters, numpy only."""
    c = np.array([0.0, 1.0]); lam = 1e-3
    def sse(c_):
        return float(np.sum((Phi(c_[0] + c_[1] * z) - mid) ** 2))
    cur = sse(c)
    for _ in range(iters):
        u = c[0] + c[1] * z; r = Phi(u) - mid
        J = np.stack([phi(u), phi(u) * z], 1)
        A = J.T @ J; g = J.T @ r
        step = np.linalg.solve(A + lam * np.diag(np.diag(A)), g)
        new = c - step; s2 = sse(new)
        if s2 < cur:
            c, cur, lam = new, s2, lam * 0.3
            if np.max(np.abs(step)) < 1e-9:
                break
        else:
            lam *= 10.0
    return c


def fit_model(frames, fit_mask_fn):
    """Fit c0, c1 per look on rows chosen by fit_mask_fn(frame) (pooled BTC and ETH), then the half spreads by mid zone. Returns the model dict."""
    model = default_model()
    hs = []
    for L in LOOKS:
        zs, ms, sp = [], [], []
        for fr in frames:
            f = [x for x in fr if x["L"] == L][0]
            keep = f["ok"] & ~np.isnan(f["bid"]) & fit_mask_fn(f)
            idd, ido = f["idd"][keep], f["ido"][keep]
            cr = core(f["G"], idd, ido, L, default_model())
            zs.append(cr["z"]); ms.append(0.5 * (f["bid"][keep] + f["ask"][keep])); sp.append(0.5 * (f["ask"][keep] - f["bid"][keep]))
        z, m, s_ = np.concatenate(zs), np.concatenate(ms), np.concatenate(sp)
        c = fit_mid(z, m)
        model[str(L)] = [float(c[0]), float(c[1])]
        hs.append((Phi(c[0] + c[1] * z), s_))
    mid_all = np.concatenate([a for a, _ in hs]); sp_all = np.concatenate([b for _, b in hs])
    zn = zone_of(mid_all)
    model["h"] = [float(np.median(sp_all[zn == k])) if (zn == k).sum() >= 20 else 0.005 for k in range(3)]
    model["fitted"] = True
    return model


def model_report(frames, model, mask_fn, label):
    """Out-of-sample error of the model on rows chosen by mask_fn: mid RMSE and MAE in cents, in the band zones, and band-set agreement."""
    out = {"label": label}
    for L in LOOKS:
        zs, mids, mods, asks, bids, ress, ask_y_m, ask_n_m = [], [], [], [], [], [], [], []
        for fr in frames:
            f = [x for x in fr if x["L"] == L][0]
            keep = f["ok"] & ~np.isnan(f["bid"]) & mask_fn(f)
            cr = core(f["G"], f["idd"][keep], f["ido"][keep], L, model)
            mids.append(0.5 * (f["bid"][keep] + f["ask"][keep])); mods.append(cr["mid"]); asks.append(f["ask"][keep]); bids.append(f["bid"][keep])
            ress.append(f["res"][keep]); ask_y_m.append(cr["ask_yes"]); ask_n_m.append(cr["ask_no"])
        mid, mod, ask, bid, res = (np.concatenate(x) for x in (mids, mods, asks, bids, ress))
        ay, an = np.concatenate(ask_y_m), np.concatenate(ask_n_m)
        e = (mod - mid) * 100.0
        d = dict(n=int(len(mid)), mid_rmse_c=float(np.sqrt(np.mean(e ** 2))) if len(e) else None, mid_mae_c=float(np.mean(np.abs(e))) if len(e) else None,
                 mid_bias_c=float(np.mean(e)) if len(e) else None)
        fav = (mid > 0.80) | (mid < 0.20)
        d["n_extreme_mid"] = int(fav.sum()); d["mid_mae_extreme_c"] = float(np.mean(np.abs(e[fav]))) if fav.any() else None
        # band agreement: the side priced 88c to 97c, by the model against by Kalshi's actual ask
        act_y = (ask >= 0.88) & (ask <= 0.97); act_n = ((1 - bid) >= 0.88) & ((1 - bid) <= 0.97)
        mod_y = (ay >= 0.88) & (ay <= 0.97); mod_n = (an >= 0.88) & (an <= 0.97)
        act = act_y | act_n; modb = mod_y | mod_n
        both = act & modb & ((act_y & mod_y) | (act_n & mod_n))
        d["band_actual"] = int(act.sum()); d["band_model"] = int(modb.sum()); d["band_both_same_side"] = int(both.sum())
        d["band_precision"] = float(both.sum() / modb.sum()) if modb.sum() else None
        d["band_recall"] = float(both.sum() / act.sum()) if act.sum() else None
        # PF of model priced entries against actually priced entries, on the same Kalshi windows, held to the Kalshi result
        won_y = res == 1
        def pf_net(sel_y, sel_n, ask_y, ask_n):
            n1 = np.concatenate([S.kalshi_net_cents(won_y[sel_y], ask_y[sel_y]), S.kalshi_net_cents(~won_y[sel_n], ask_n[sel_n])])
            return dict(n=int(len(n1)), pf=S.pf_of(n1) if len(n1) else None, mean_c=float(n1.mean()) if len(n1) else None, win=float(((n1 > 0).mean())) if len(n1) else None)
        d["pf_actual_priced"] = pf_net(act_y, act_n, ask, 1 - bid)
        d["pf_model_priced_model_set"] = pf_net(mod_y, mod_n, ay, an)
        out["L%d" % L] = d
    return out


def proxy_report(sym, G, frames_sym, model):
    """Binance window outcome vs Kalshi's settled result, by series: overall, by distance band, in the model's band set; open vs strike in bp."""
    fr = [x for x in frames_sym if x["L"] == 360][0]
    ok = fr["ok"] & ~np.isnan(G.c[np.where(fr["ok"], fr["idc"], 0)])
    idc, ido = fr["idc"][ok], fr["ido"][ok]
    bin_yes = (G.c[idc] > G.o[ido]).astype(int)
    k_res = fr["res"][ok]
    agree = bin_yes == k_res
    out = dict(series=KALSHI_SERIES[sym], windows=int(ok.sum()), agree=float(agree.mean()), disagree=int((~agree).sum()))
    bin_vs_strike = (G.c[idc] > fr["strike"][ok]).astype(int)
    out["agree_settle_vs_kalshi_strike"] = float((bin_vs_strike == k_res).mean())
    diff_bp = 1e4 * (np.log(G.o[ido]) - np.log(fr["strike"][ok]))
    out["open_minus_strike_bp"] = dict(mean=float(diff_bp.mean()), median=float(np.median(diff_bp)), p05=float(np.percentile(diff_bp, 5)), p95=float(np.percentile(diff_bp, 95)),
                                      mean_abs=float(np.abs(diff_bp).mean()))
    # by |distance| at the 6 minute look
    cr = core(G, fr["idd"][ok], ido, 360, model)
    ad = np.abs(cr["d"])
    bands = [(0, 1), (1, 3), (3, 6), (6, 12), (12, 1e9)]
    out["by_abs_dist_bp_at_6min"] = [dict(lo=lo, hi=hi if hi < 1e8 else None, n=int(((ad >= lo) & (ad < hi)).sum()),
                                           agree=float(agree[(ad >= lo) & (ad < hi)].mean()) if ((ad >= lo) & (ad < hi)).any() else None) for lo, hi in bands]
    side = pick_side(cr, "band")
    inb = side != 0
    out["model_band_6min"] = dict(n=int(inb.sum()), agree=float(agree[inb].mean()) if inb.any() else None, disagree=int((~agree[inb]).sum()))
    # outcome disagreement among windows where the side the model would buy lost on Kalshi but won on Binance, or the reverse
    return out


def kalshi_setup():
    grids = {s: load_grid(s) for s in SYMS}
    frames = []
    for s in SYMS:
        fr = kalshi_frame(s, grids[s])
        for f in fr:
            f["G"] = grids[s]; f["sym"] = s
        frames.append(fr)
    return grids, frames


def cmd_model(a):
    grids, frames = kalshi_setup()
    # discovery third (W1) of the 17 development dates: first 4 dates fit, last 2 dates held-out slice
    fit_a = lambda f: (f["win"] == 0) & (f["drank"] < 4)
    hold_a = lambda f: (f["win"] == 0) & (f["drank"] >= 4)
    w2 = lambda f: f["win"] == 1
    w3 = lambda f: f["win"] == 2
    m4 = fit_model(frames, fit_a)
    rep = dict(model_fit_on="first 4 UTC dates of Kalshi development W1", params_4day=m4)
    rep["heldout_slice_last2dates_W1"] = model_report(frames, m4, hold_a, "W1 dates 5-6 (held-out slice, 4 day model)")
    rep["train_slice_first4dates_W1"] = model_report(frames, m4, fit_a, "W1 dates 1-4 (in sample)")
    final = fit_model(frames, lambda f: f["win"] == 0)
    rep["params_final_W1_all_6_dates"] = final
    rep["oos_W2"] = model_report(frames, final, w2, "W2 dev dates (final model, drift check)")
    rep["oos_W3"] = model_report(frames, final, w3, "W3 dev dates (final model, drift check)")
    rep["in_sample_W1"] = model_report(frames, final, lambda f: f["win"] == 0, "W1 (in sample)")
    mae = rep["heldout_slice_last2dates_W1"]["L360"]["mid_mae_c"]
    rep["gate_mid_mae_over_8c"] = bool(mae is not None and mae > 8.0)
    rep["proxy"] = {s: proxy_report(s, grids[s], frames[i], final) for i, s in enumerate(SYMS)}
    rep["note"] = "MODEL RESULT: Binance path + fitted quote model; Kalshi development windows only (closes before 2026-10-28); never a live figure."
    json.dump(rep, open(os.path.join(S.WORKERS, "BINPATH_QUOTE_MODEL_REPORT.json"), "w"), indent=1)
    if not rep["gate_mid_mae_over_8c"]:
        json.dump(final, open(MODEL_FILE, "w"), indent=1)
    print(json.dumps(rep, indent=1))


# ------------------------------------------------------------------ the adapter
def load_model():
    if not os.path.exists(MODEL_FILE):
        raise Blocked("quote model file missing (run `model` first; it is not written if the MAE gate fails)")
    return json.load(open(MODEL_FILE))


def closes_between(lo, hi):
    a = ((max(lo, FIRST_CLOSE) + 899) // 900) * 900
    return np.arange(a, hi, 900, dtype=np.int64)


class BinAdapter(S.Adapter):
    groups = ("ALL",)

    def __init__(self, sym, arm):
        self.sym, self.arm = sym, arm
        self.name = "binpath_%s_%s" % (sym, arm)
        self.G = load_grid(sym)
        self.fr_ts, self.fr_rate = load_funding(sym)
        self.model = load_model()

    def _rows(self, lo, hi):
        """Build row arrays for closes in [lo, hi). The dev call can never pass hi above the held-out cut."""
        G = self.G
        cols, meta = [], []
        for L in LOOKS:
            closes = closes_between(lo, hi)
            idd, ido, idc, ok = window_index(G, closes, L)
            closes, idd, ido, idc = closes[ok], idd[ok], ido[ok], idc[ok]
            cr = core(G, idd, ido, L, self.model)
            side = pick_side(cr, self.arm)
            k = side != 0
            closes, idd, ido, idc, side = closes[k], idd[k], ido[k], idc[k], side[k]
            cr = {x: v[k] for x, v in cr.items()}
            t = closes - L
            F = side_features(G, idd, ido, t, L, self.model, side, cr, self.fr_ts, self.fr_rate)
            yes_won = G.c[idc] > G.o[ido]
            won = np.where(side > 0, yes_won, ~yes_won)
            ask = np.where(side > 0, cr["ask_yes"], cr["ask_no"])
            ask_opp = np.where(side > 0, cr["ask_no"], cr["ask_yes"])
            cols.append(F)
            meta.append(np.stack([closes, idd, ido, idc, np.full(len(closes), L), side, won, ask, ask_opp, t], 1).astype(np.float64))
        F = np.concatenate(cols); M = np.concatenate(meta)
        o = np.argsort(M[:, 0], kind="stable")
        return F[o], M[o]

    def _table(self, lo, hi, stage):
        F, M = self._rows(lo, hi)
        n = len(M)
        close = M[:, 0].astype(np.int64); look = M[:, 4].astype(np.int32); side = M[:, 5].astype(np.int8)
        won = M[:, 6] > 0.5; ask = M[:, 7]; ask_opp = M[:, 8]; t = M[:, 9].astype(np.int64)
        date = (close // 86400).astype(np.int32)
        win = (np.where(close < W_CUTS[0], 0, np.where(close < W_CUTS[1], 1, 2)) if stage == "dev" else np.full(n, 3)).astype(np.int8)
        net = S.kalshi_net_cents(won, ask).astype(np.float32)
        nets = S.kalshi_net_cents(won, ask, 1, 1.2).astype(np.float32)
        cats = {"hod4": ((t % 86400) // 14400).astype(np.int16), "dow": (((t // 86400) + 3) % 7).astype(np.int16)}

        def outcome(dir_, variant, group):
            rows_ = np.flatnonzero((side == (1 if dir_ == "yes" else -1)) & (look == variant))
            return rows_, net[rows_], nets[rows_]

        tab = S.Table(self.name + ("" if stage == "dev" else ":holdout"), ["ALL"], FEATS, F.T.astype(np.float32).copy(), cats, t, date, win,
                      np.zeros(n, dtype=np.int16), ["ALL"], ("yes", "no"), LOOKS, outcome, np.arange(n),
                      meta=dict(M=M, side=side, look=look, won=won, ask=ask, ask_opp=ask_opp, close=close))
        return tab

    def build_dev(self):
        return self._table(FIRST_CLOSE, HOLD_LO, "dev")          # hi is the held-out cut: no close at or after 2025-01-01 is ever built here

    def build_holdout(self, frozen_id, cuts):
        S.guard_check(frozen_id, self.name)
        S.guard_record(frozen_id, self.name)                      # recorded BEFORE the read
        return self._table(HOLD_LO, T_END, "holdout")

    def unseen(self):
        """Counts only: held-out windows (closes from 2025-01-01) with the bars a row needs. No price is read."""
        G = self.G
        closes = closes_between(HOLD_LO, T_END)
        idd, ido, idc, ok = window_index(G, closes, 360)
        return dict(adapter=self.name, holdout_from="2025-01-01", holdout_windows=int(ok.sum()), holdout_rows_est=int(2 * ok.sum()),
                    note="windows closing 2025-01-01 to 2026-11-06 with all bars present, counted from bar presence only; never scored. The quote model and "
                         "proxy check used Binance bars of 2026-10-11 to 10-27 (prices and one agreement count, no rule).")

    def truncation_test(self, tab, n=200, seed=0):
        """Delete every bar after the decision (a local slice ending at the decision bar, funding at or before the decision) and recompute the
        row: side, ask and the whole feature vector must equal the stored ones."""
        rng = random.Random(seed)
        idx = rng.sample(range(tab.n), min(n, tab.n)); bad = 0
        M = tab.meta["M"]
        for i in idx:
            close, idd, ido, L, side = int(M[i, 0]), int(M[i, 1]), int(M[i, 2]), int(M[i, 4]), int(M[i, 5])
            a = idd - 1700
            Gs = self.G.slice(a, idd + 1)                           # nothing after the decision bar exists in Gs
            t = np.array([close - L]); k = int(np.searchsorted(self.fr_ts, t[0], side="right"))
            cr = core(Gs, np.array([idd - max(a, 0)]), np.array([ido - max(a, 0)]), L, self.model)
            s2 = pick_side(cr, self.arm)
            ok = s2[0] == side
            if ok:
                F2 = side_features(Gs, np.array([idd - max(a, 0)]), np.array([ido - max(a, 0)]), t, L, self.model, s2, cr, self.fr_ts[:k], self.fr_rate[:k])
                ok = bool(np.allclose(F2[0].astype(np.float32), tab.X[:, i], rtol=1e-4, atol=1e-4, equal_nan=True))
            bad += 0 if ok else 1
        return dict(name="truncation", checked=len(idx), mismatches=bad, passed=bad == 0)


# ------------------------------------------------------------------ audits (development data only)
def audit_rules(ad, tab, ats, rules):
    """Truncation (200 random rows of the table), reverse control (the opposite side at its own modelled ask on the same windows, pooled PF under 1.0)
    and fee stress (x1.2 pooled PF at least 1.0) for each rule. Returns (global truncation result, per rule results)."""
    trunc = ad.truncation_test(tab, 200, 0)
    out = []
    for r in rules:
        rows, net, nets = S._prep(tab, "ALL", r.dir, r.variant)
        m = ats.A[list(r.atoms)][:, rows].all(axis=0)
        sel = rows[m]
        won_opp = ~tab.meta["won"][sel]
        opp = S.kalshi_net_cents(won_opp, tab.meta["ask_opp"][sel])
        st = S.exact_rule(tab, ats, "ALL", r, stress=True)
        rev_pf = S.pf_of(opp)
        out.append(dict(reverse_pf=rev_pf, reverse_ok=bool(rev_pf < 1.0), stress_pf=st["all"]["pf"], stress_ok=bool(st["all"]["pf"] >= 1.0)))
    return trunc, out


# ------------------------------------------------------------------ the run (the harness engine with per stage counts and baseline ledger)
def baseline(ad, tab, group="ALL"):
    """The unconditional entry (no atom) per direction and look and window: descriptive, and ledgered as scored tries."""
    out = {}
    for d in ("yes", "no"):
        for v in LOOKS:
            rows, net, nets = tab.outcome(d, v, group)
            st = S.stats_from_rows(tab.win[rows], tab.date[rows], net)
            sts = S.stats_from_rows(tab.win[rows], tab.date[rows], nets)
            out["%s|%d" % (d, v)] = dict(win=[dict(n=w["n"], pf=round(w["pf"], 3), mean_c=round(w["mean"], 3), wr=round(w["wr"], 4)) for w in st["win"]],
                                         all=dict(n=st["all"]["n"], pf=round(st["all"]["pf"], 3), mean_c=round(st["all"]["mean"], 3), wr=round(st["all"]["wr"], 4)),
                                         mean_ask=float(tab.meta["ask"][rows].mean()) if len(rows) else None,
                                         stress_pf=round(sts["all"]["pf"], 3))
    return out


def baseline_ledger(tab):
    path = os.path.join(S.LEDGER_DIR, "%s_ALL_BASE.ids.gz" % tab.name)
    if os.path.exists(path):
        return False
    ids = ["%s|ALL||%s|%d" % (tab.name, d, v) for d in ("yes", "no") for v in LOOKS]
    S.ledger_append(path, ids)
    return True


def run_binpath(ad, tab, n_rules, seed, batch=2000, out_dir=None, verbose=True):
    cuts = S.make_cuts(tab); csha = S.cuts_sha(cuts)
    ats = S.AtomSet(tab, cuts)
    group = "ALL"; prefix = "%s|%s|" % (tab.name, group)
    seen = S.seen_ids(prefix)
    rng = random.Random(seed)
    path = os.path.join(S.LEDGER_DIR, "%s_%s_RUN%d.ids.gz" % (tab.name, group, seed))
    if os.path.exists(path):
        raise Blocked("a run with seed %d already exists for %s; seeds are not reused" % (seed, tab.name))
    N0 = S.n_total()
    if verbose:
        print("MODEL RESULT ONLY (Binance path + fitted quote model). %s: rows %d, atoms %d, cuts sha %s" % (tab.name, tab.n, ats.n_real, csha[:16]))
        print("BAR PF >= 1.5 in each of W1, W2, W3; floors %d/window %d total; N so far %d, z bar %.3f" % (S.BAR["min_trades_window"], S.BAR["min_trades_total"], N0, S.z_bar(N0)))
    done = tried = 0
    st1 = st12 = scr = 0
    best_pf = [0.0, 0.0, 0.0]; best_min = (0.0, "")
    surv = []
    t0 = time.time()
    while done < n_rules and tried < 50 * n_rules:
        want = min(batch, n_rules - done); cand, ids = [], []
        while len(cand) < want and tried < 50 * n_rules:
            r = S.draw_rule(rng, ats, tab); tried += 1
            rid = S.rule_id(tab, ats, group, r)
            if rid in seen:
                continue
            seen.add(rid); cand.append(r); ids.append(rid)
        if not cand:
            break
        S.ledger_append(path, ids)                                   # BEFORE scoring
        res = S.score_rules(tab, ats, group, cand)
        for r, rid, s in zip(cand, ids, res):
            n_, pf_ = s["n"], s["pf"]
            ok1 = pf_[0] >= S.BAR["pf"] - S.SCREEN_SLACK and n_[0] >= S.BAR["min_trades_window"]
            ok2 = ok1 and pf_[1] >= S.BAR["pf"] - S.SCREEN_SLACK and n_[1] >= S.BAR["min_trades_window"]
            st1 += ok1; st12 += ok2; scr += bool(s["surv"])
            for w in range(3):
                if n_[w] >= S.BAR["min_trades_window"] and pf_[w] > best_pf[w]:
                    best_pf[w] = pf_[w]
            if all(x >= S.BAR["min_trades_window"] for x in n_) and min(pf_) > best_min[0]:
                best_min = (min(pf_), rid)
            if s["surv"]:
                surv.append((r, rid, s))
        done += len(cand)
    dt = time.time() - t0
    N1 = S.n_total(); zb = S.z_bar(N1)
    final = []
    for r, rid, s in surv:
        ex = S.exact_rule(tab, ats, group, r)
        if S.passes_bar(ex):
            final.append(dict(id=rid, atoms=[ats.specs[a] for a in r.atoms], dir=r.dir, variant=r.variant, batch=s,
                              exact={k: ex[k] for k in ("win", "all")}, deflated=bool(ex["all"]["z"] >= zb)))
    summary = dict(adapter=tab.name, group=group, seed=seed, rules_scored=done, seconds=round(dt, 2), N_before=N0, N_after=N1, z_bar=round(zb, 4),
                   stage_W1=int(st1), stage_W1_W2=int(st12), screen_survivors=int(scr), exact_survivors=len(final), deflated=sum(1 for f in final if f["deflated"]),
                   best_pf_by_window_floor40=[round(x, 3) for x in best_pf], best_min_window_pf=[round(best_min[0], 3), best_min[1]],
                   cuts_sha256=csha, table_sha256=tab.fingerprint(), survivors=final, cuts=cuts, rows=int(tab.n),
                   rows_by_window=[int((tab.win == w).sum()) for w in range(3)], note="MODEL RESULT, not a live figure")
    od = out_dir or os.path.join(S.SCAN_DATA, "runs"); os.makedirs(od, exist_ok=True)
    fn = os.path.join(od, "%s_ALL_RUN%d.json" % (tab.name, seed))
    json.dump(summary, open(fn, "w"), indent=1, default=str)
    summary["file"] = fn
    if verbose:
        print("RUN%d scored %d in %.1fs; N %d -> %d, z bar %.3f; W1 %d, W1+W2 %d, screen %d, exact %d, deflated %d; best PF by window %s; best min-window PF %s"
              % (seed, done, dt, N0, N1, zb, st1, st12, scr, len(final), summary["deflated"], summary["best_pf_by_window_floor40"], summary["best_min_window_pf"]))
    return summary


def cmd_run(a):
    ad = BinAdapter(a.sym, a.arm)
    tab = ad.build_dev()
    if baseline_ledger(tab):
        print("baseline ledgered (4 ids)")
    run_binpath(ad, tab, a.n, a.seed)


def cmd_baseline(a):
    ad = BinAdapter(a.sym, a.arm)
    tab = ad.build_dev()
    print("baseline ledgered" if baseline_ledger(tab) else "baseline already ledgered")
    print(json.dumps(baseline(ad, tab), indent=1))


def cmd_unseen(a):
    for s in SYMS:
        for arm in ARMS:
            print(json.dumps(BinAdapter(s, arm).unseen()))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scan_binance")
    ap.add_argument("cmd", choices=["model", "unseen", "baseline", "run"])
    ap.add_argument("--sym", default="BTC"); ap.add_argument("--arm", default="band"); ap.add_argument("--n", type=int, default=5000); ap.add_argument("--seed", type=int)
    a = ap.parse_args(argv)
    {"model": cmd_model, "unseen": cmd_unseen, "baseline": cmd_baseline, "run": cmd_run}[a.cmd](a)


if __name__ == "__main__":
    main()
