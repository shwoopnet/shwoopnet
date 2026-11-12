"""Shared pieces for the stocks desk scorers. No data is read here.

Input conventions (all prices are the LISTING venue's official auction prints,
one price definition across the whole sample, never switched at the cutoff):
  daily frame columns: date (datetime64, trading day), symbol, open, close, volume
  minute frame columns: ts (naive US/Eastern bar START time), symbol, open, close
"""
import json, math, os
import numpy as np
import pandas as pd

HELDOUT_START = pd.Timestamp("2024-07-01")   # constant, pinned Nov 12 2026
W1 = (pd.Timestamp("2018-05-01"), pd.Timestamp("2021-03-31"))
W2 = (pd.Timestamp("2021-04-01"), pd.Timestamp("2024-06-30"))
W3 = (HELDOUT_START, pd.Timestamp("2026-11-11"))
Z_RESEARCH = 5.46
D_PF15 = 0.16165750674585438     # mean/sd of a normal event return giving PF 1.5

# Costs, ONE WAY, in basis points. ASSUMED, not measured (marked in every report).
COST_BP = {"index_etf": 0.5, "large_cap": 1.5, "illiquid": 15.0, "auction_extra": 0.5}
SEC_SELL_BP = 0.206            # 0.0000206 of sell value (Alpaca schedule Oct 12 2026)
BORROW_ANNUAL = 0.10           # assumed hard-to-borrow rate on shorts
SPLIT_LO, SPLIT_HI = 0.4, 2.5  # name-days with a close-to-close ratio outside are dropped

def profit_factor(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    w, l = x[x > 0].sum(), -x[x < 0].sum()
    if l == 0:
        return math.inf if w > 0 else float("nan")
    return w / l

def zstat(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 2 or x.std(ddof=1) == 0:
        return float("nan")
    return x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))

def events_needed(z=Z_RESEARCH, power_z=0.0):
    return ((z + power_z) / D_PF15) ** 2

def window_of(date):
    d = pd.Timestamp(date)
    if W1[0] <= d <= W1[1]: return "W1"
    if W2[0] <= d <= W2[1]: return "W2"
    if W3[0] <= d <= W3[1]: return "W3"
    return None

def drop_splits(daily):
    """Drop name-days whose close/prev close is outside [0.4, 2.5] (no adjustment source)."""
    d = daily.sort_values(["symbol", "date"]).copy()
    r = d.groupby("symbol")["close"].transform(lambda s: s / s.shift(1))
    bad = (r < SPLIT_LO) | (r > SPLIT_HI)
    # also drop the day after the jump for the open-based ratios
    bad = bad | bad.groupby(d["symbol"]).shift(-1, fill_value=False)
    return d[~bad]

def per_window(pnl_bp, dates, min_pf=1.5):
    """pnl_bp: per-event (or per-day) net pnl in bp. Returns dict by window, development first."""
    s = pd.Series(np.asarray(pnl_bp, float), index=pd.DatetimeIndex(dates))
    out = {}
    for name in ("W1", "W2", "W3"):
        lo, hi = {"W1": W1, "W2": W2, "W3": W3}[name]
        x = s[(s.index >= lo) & (s.index <= hi)]
        out[name] = {"n": int(len(x)), "pf": profit_factor(x.values),
                     "mean_bp": float(x.mean()) if len(x) else float("nan"),
                     "z": zstat(x.values)}
    dev = s[s.index < HELDOUT_START]
    out["DEV"] = {"n": int(len(dev)), "pf": profit_factor(dev.values),
                  "mean_bp": float(dev.mean()) if len(dev) else float("nan"), "z": zstat(dev.values)}
    return out

def label(win, judged):
    """Registered labels. judged=True for S1, S2, S7 (research bar z 5.46, PF 1.5 in each window).
    judged=False for screens (S3-S6): never a pass."""
    n_all = sum(win[w]["n"] for w in ("W1", "W2", "W3"))
    dev = win["DEV"]
    if not judged:
        if dev["n"] >= 30 and dev["pf"] >= 1.3 and win["W1"]["mean_bp"] > 0 and win["W2"]["mean_bp"] > 0:
            return f"paper-list candidate (screen, unproven), n = {n_all}"
        if dev["n"] >= 100 and dev["pf"] < 1.0:
            return f"FALSIFIED on development (screen), n = {dev['n']}"
        return f"screen only, no evidence at n = {n_all}"
    if dev["n"] >= 100 and dev["pf"] < 1.0:
        return f"FALSIFIED on development, n = {dev['n']}"
    ok = all(win[w]["n"] > 0 and win[w]["pf"] >= 1.5 for w in ("W1", "W2", "W3"))
    if ok and n_all >= events_needed():
        return f"cleared its registered bar (PF 1.5 in 3 windows, n = {n_all}); needs Verification Analyst re-check; NOT a research-bar pass until then"
    return f"no evidence at n = {n_all}" if n_all < events_needed() else f"not cleared, n = {n_all}"

MARKER = "HELDOUT_READ_MARKER.txt"
def read_heldout_once(card, marker_path=MARKER):
    """Refuse a second held-out read. The marker line must be committed to the repo."""
    lines = []
    if os.path.exists(marker_path):
        with open(marker_path) as fh: lines = fh.read().splitlines()
    if any(l.split()[0] == card for l in lines if l.strip()):
        raise RuntimeError(f"{card}: held-out already read (marker line exists)")
    with open(marker_path, "a") as f:
        f.write(f"{card} HELDOUT_START={HELDOUT_START.date()}\n")

def report(card, win, judged, extra=None):
    r = {"card": card, "assumed_costs": True, "windows": win, "label": label(win, judged)}
    if extra: r.update(extra)
    return r

def dev_corr(a, b):
    """Daily pnl correlation of two cards on DEVELOPMENT dates only (before HELDOUT_START). Amendment 3 item 4:
    computed before either held-out read."""
    x = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    x = x[x.index < HELDOUT_START]
    return float(x["a"].corr(x["b"])) if len(x) > 2 else float("nan")
