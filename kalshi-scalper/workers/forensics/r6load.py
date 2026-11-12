"""Loader for recorder R6 files (book15r6/<date>/<HHMM>/{book,trades,coverage}.csv.gz).

Forensics desk, Nov 12 2026. Public recorded market data only. No network, no account data.
Date constants are the registration's (FORENSICS_REGISTRATION_NOV12.md); a window is assigned
to a block by its close_time and anything closing on or after FROZEN_FROM is dropped unread.
"""
import os, glob
import numpy as np
import pandas as pd

D_FROM = pd.Timestamp("2026-10-29T00:00:00Z")
H_FROM = pd.Timestamp("2026-11-05T00:00:00Z")
FROZEN_FROM = pd.Timestamp("2026-11-09T00:00:00Z")
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
PX = ["yes_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_px_%d" % i for i in range(1, 6)]
SZ = ["yes_bid_sz_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]


def to_ms(s):
    return ((pd.to_datetime(s, utc=True, format="ISO8601") - EPOCH) / pd.Timedelta(milliseconds=1)).astype("int64")


def block_of(close_ts):
    """'D', 'H' or None for a close time (a pandas Timestamp, UTC)."""
    if close_ts < D_FROM or close_ts >= FROZEN_FROM:
        return None
    return "D" if close_ts < H_FROM else "H"


def run_dirs(root):
    return sorted(d for d in glob.glob(os.path.join(root, "book15r6", "*", "*")) if os.path.isdir(d))


def load_coverage(root, series):
    """One row per ticker: close_ms, block, result ('yes'/'no'/''), worst max_gap_ms over the runs that saw it."""
    parts = []
    for d in run_dirs(root):
        f = os.path.join(d, "coverage.csv.gz")
        if not os.path.exists(f):
            continue
        c = pd.read_csv(f, dtype={"ticker": str, "result": str}, usecols=["close_time", "series", "ticker", "max_gap_ms", "result"])
        parts.append(c[c["ticker"].notna() & c["series"].isin(series)])
    c = pd.concat(parts, ignore_index=True)
    c["result"] = c["result"].fillna("").str.lower()
    c["close_ts"] = pd.to_datetime(c["close_time"], utc=True)
    g = c.groupby("ticker").agg(series=("series", "first"), close_ts=("close_ts", "first"), max_gap_ms=("max_gap_ms", "max"),
                                result=("result", lambda s: next((x for x in s if x in ("yes", "no")), "")))
    g["block"] = [block_of(t) for t in g["close_ts"]]
    g = g[g["block"].notna()].copy()
    g["close_ms"] = ((g["close_ts"] - EPOCH) / pd.Timedelta(milliseconds=1)).astype("int64")
    return g


def load_books(root, tickers, min_left_s=None, max_left_s=None, close_ms=None):
    """All book rows of the given tickers, sorted by ticker then t_recv_ms. Optional filter on seconds left."""
    tickers = set(tickers)
    parts = []
    for d in run_dirs(root):
        f = os.path.join(d, "book.csv.gz")
        if not os.path.exists(f):
            continue
        b = pd.read_csv(f, usecols=["t_recv_ms", "ticker"] + PX + SZ)
        b = b[b["ticker"].isin(tickers)]
        if close_ms is not None and (min_left_s is not None or max_left_s is not None):
            left = (b["ticker"].map(close_ms) - b["t_recv_ms"]) / 1000.0
            keep = np.ones(len(b), bool)
            if min_left_s is not None:
                keep &= (left >= min_left_s).to_numpy()
            if max_left_s is not None:
                keep &= (left <= max_left_s).to_numpy()
            b = b[keep]
        parts.append(b)
    b = pd.concat(parts, ignore_index=True).drop_duplicates(subset=["ticker", "t_recv_ms"])
    return b.sort_values(["ticker", "t_recv_ms"]).reset_index(drop=True)


def load_trades(root, tickers, close_ms, min_left_s, max_left_s):
    """Tape rows of the given tickers with min_left_s <= seconds left <= max_left_s."""
    tickers = set(tickers)
    parts = []
    for d in run_dirs(root):
        f = os.path.join(d, "trades.csv.gz")
        if not os.path.exists(f):
            continue
        t = pd.read_csv(f, dtype={"ticker": str, "taker_outcome_side": str})
        t = t[t["ticker"].isin(tickers)]
        if t.empty:
            continue
        t["ms"] = to_ms(t["created_time"])
        left = (t["ticker"].map(close_ms) - t["ms"]) / 1000.0
        t = t[(left >= min_left_s) & (left <= max_left_s)]
        parts.append(t[["ticker", "ms", "yes_price_dollars", "count_fp", "taker_outcome_side"]])
    t = pd.concat(parts, ignore_index=True).drop_duplicates()
    return t.sort_values(["ticker", "ms"]).reset_index(drop=True)


def fee(p):
    """Taker fee per contract, unrounded."""
    return 0.07 * p * (1.0 - p)


def pf(x):
    x = np.asarray(x, float)
    w, l = x[x > 0].sum(), -x[x < 0].sum()
    return float("inf") if l == 0 and w > 0 else (float("nan") if l == 0 else w / l)


def boot(values, clusters, stat, n=2000, seed=20261112):
    """95% interval of stat(values) by resampling whole clusters."""
    values = np.asarray(values, float)
    if len(values) == 0:
        return [None, None]
    rng = np.random.default_rng(seed)
    u, inv = np.unique(np.asarray(clusters), return_inverse=True)
    idx = [np.flatnonzero(inv == k) for k in range(len(u))]
    out = []
    for _ in range(n):
        pick = rng.integers(0, len(u), len(u))
        v = np.concatenate([values[idx[k]] for k in pick])
        s = stat(v)
        if s == s and abs(s) != float("inf"):
            out.append(s)
    if len(out) < n // 2:
        return [None, None]
    return [round(float(np.percentile(out, 2.5)), 4), round(float(np.percentile(out, 97.5)), 4)]
