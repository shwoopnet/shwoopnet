"""TAPECLOCK1: the R6 trade tape as a third clock for the quote recorder and the R6 order book. Bitcoin 15 minute market.

Registration: TAPECLOCK1_REGISTRATION.md (committed before anything was computed).
A measurement: no rule scored, no settlement result loaded, zero tries. No network, no account data.

usage: python3 -I tapeclock1.py <r6_root> <quotes_root> <out_json>
"""
import sys, os, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import r6load as R

R6, QROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SERIES = "KXBTC15M"
FROM, BEFORE = pd.Timestamp("2026-10-29T22:15:00Z"), pd.Timestamp("2026-11-05T00:00:00Z")
SPANS = {"150_to_120s": (120.0, 150.0), "120_to_30s": (30.0, 120.0)}
BAND = (0.05, 0.30)
TOL_MS = 4000
SHIFTS = range(-12, 13)
EPS = 1e-9
rng = np.random.default_rng(20261112)

parts = []
for d in R.run_dirs(R6):
    f = os.path.join(d, "coverage.csv.gz")
    if os.path.exists(f):
        c = pd.read_csv(f, dtype={"ticker": str}, usecols=["close_time", "series", "ticker"])
        parts.append(c[c["ticker"].notna() & (c["series"] == SERIES)])
cov = pd.concat(parts, ignore_index=True).drop_duplicates("ticker").set_index("ticker")
cov["close_ts"] = pd.to_datetime(cov["close_time"], utc=True)
cov = cov[(cov["close_ts"] >= FROM) & (cov["close_ts"] < BEFORE)]
close_ms = (((cov["close_ts"] - R.EPOCH) / pd.Timedelta(milliseconds=1)).astype("int64")).to_dict()

# quote recorder rows (market list)
qparts = []
for d in sorted(glob.glob(os.path.join(QROOT, "quotes", "*", "*"))):
    f = os.path.join(d, "quotes.csv.gz")
    if os.path.exists(f):
        q = pd.read_csv(f, dtype={"ticker": str, "status": str})
        qparts.append(q[q["ticker"].isin(close_ms)])
Q = pd.concat(qparts, ignore_index=True).drop_duplicates(["ticker", "t_recv_ms"])
Q = Q[Q["status"].str.lower().isin(["active", "open"]) & Q["yes_bid"].notna() & Q["yes_ask"].notna()]
Q = Q.assign(t=Q["t_recv_ms"], ask_yes=Q["yes_ask"], ask_no=1 - Q["yes_bid"])[["t", "ticker", "ask_yes", "ask_no"]].sort_values("t")
both = set(Q["ticker"])

# R6 book (with touch sizes for the size line) and tape
bparts, tparts = [], []
for d in R.run_dirs(R6):
    if os.path.basename(os.path.dirname(d)) > "2026-11-05":
        continue
    f = os.path.join(d, "book.csv.gz")
    if os.path.exists(f):
        b = pd.read_csv(f, usecols=["t_recv_ms", "ticker", "yes_bid_px_1", "no_bid_px_1", "yes_bid_sz_1", "no_bid_sz_1"])
        b = b[b["ticker"].isin(both)]
        if len(b):
            left = (b["ticker"].map(close_ms) - b["t_recv_ms"]) / 1000.0
            bparts.append(b[(left >= 10) & (left <= 170)])
    f = os.path.join(d, "trades.csv.gz")
    if os.path.exists(f):
        t = pd.read_csv(f, dtype={"ticker": str, "taker_outcome_side": str})
        t = t[t["ticker"].isin(both)]
        if len(t):
            t["ms"] = R.to_ms(t["created_time"])
            left = (t["ticker"].map(close_ms) - t["ms"]) / 1000.0
            tparts.append(t[(left >= 30) & (left <= 150)][["ticker", "ms", "yes_price_dollars", "count_fp", "taker_outcome_side"]])
B = pd.concat(bparts, ignore_index=True).drop_duplicates(["ticker", "t_recv_ms"]).dropna(subset=["yes_bid_px_1", "no_bid_px_1"])
B = B[B["yes_bid_px_1"] < 1 - B["no_bid_px_1"] - EPS]
B = B.assign(t=B["t_recv_ms"], ask_yes=1 - B["no_bid_px_1"], ask_no=1 - B["yes_bid_px_1"], sz_ask_yes=B["no_bid_sz_1"], sz_ask_no=B["yes_bid_sz_1"])
B = B[["t", "ticker", "ask_yes", "ask_no", "sz_ask_yes", "sz_ask_no"]].sort_values("t")
T = pd.concat(tparts, ignore_index=True).drop_duplicates()
T["yes"] = T["taker_outcome_side"] == "yes"
T["px"] = np.where(T["yes"], T["yes_price_dollars"], 1 - T["yes_price_dollars"])
T = T[(T["px"] >= BAND[0] - EPS) & (T["px"] <= BAND[1] + EPS) & T["ticker"].isin(set(B["ticker"]))].copy()
T["left"] = (T["ticker"].map(close_ms) - T["ms"]) / 1000.0
T = T.sort_values("ms").reset_index(drop=True)


def source_ask(S, k):
    """Ask of the bought side in the last row of S at or before trade time + k seconds (NaN if older than TOL_MS)."""
    x = T[["ticker", "ms", "yes"]].assign(key=T["ms"] + k * 1000).sort_values("key")
    m = pd.merge_asof(x, S, left_on="key", right_on="t", by="ticker", direction="backward", tolerance=TOL_MS)
    a = np.where(m["yes"], m["ask_yes"], m["ask_no"])
    return pd.Series(a, index=m.index).reindex(T.index).to_numpy(float), m


def cl(v, w):
    ok = v == v
    v, w = v[ok], w[ok]
    if len(v) == 0:
        return None
    u, inv = np.unique(w, return_inverse=True)
    num = np.bincount(inv, v); den = np.bincount(inv)
    pick = rng.integers(0, len(u), (1000, len(u)))
    bs = num[pick].sum(1) / den[pick].sum(1)
    return [round(float(v.mean()), 5), round(float(np.percentile(bs, 2.5)), 5), round(float(np.percentile(bs, 97.5)), 5)]


out = {"test": "TAPECLOCK1", "series": SERIES, "closes_from": str(FROM), "closes_before": str(BEFORE), "band_trade_price": BAND,
       "note": "gap = trade price minus the source's ask for the bought side, dollars; positive shift = the source is read AFTER the trade",
       "counts": {"trades": int(len(T)), "windows": int(T["ticker"].nunique())}}
px = T["px"].to_numpy(float); wk = T["ticker"].to_numpy(); left = T["left"].to_numpy()
asks = {name: {k: source_ask(S, k)[0] for k in SHIFTS} for name, S in (("book", B[["t", "ticker", "ask_yes", "ask_no"]]), ("quote", Q))}
# judge both sources on the same trades: those with a row from each at shift 0
common = (asks["book"][0] == asks["book"][0]) & (asks["quote"][0] == asks["quote"][0])
out["counts"]["trades_with_both_sources_at_zero"] = int(common.sum())
for span, (lo, hi) in SPANS.items():
    sel = common & (left >= lo) & (left <= hi)
    o = {"trades": int(sel.sum()), "windows": int(len(np.unique(wk[sel])))}
    for name in ("book", "quote"):
        curve = {}
        for k in SHIFTS:
            g = px[sel] - asks[name][k][sel]
            ok = g == g
            curve[str(k)] = {"n": int(ok.sum()), "within_1c": round(float((np.abs(g[ok]) <= 0.01 + 1e-6).mean()), 4), "mean_abs": round(float(np.abs(g[ok]).mean()), 5),
                             "mean_signed": round(float(g[ok].mean()), 5)}
        g0 = px[sel] - asks[name][0][sel]
        best_w = max(curve, key=lambda k: curve[k]["within_1c"]); best_a = min(curve, key=lambda k: curve[k]["mean_abs"])
        o[name] = {"at_zero": {"within_1c": cl((np.abs(g0) <= 0.01 + 1e-6).astype(float), wk[sel]), "mean_abs": cl(np.abs(g0), wk[sel]), "mean_signed": cl(g0, wk[sel])},
                   "best_shift_by_within_1c": best_w, "best_shift_by_mean_abs": best_a, "at_best": curve[best_a], "curve": curve}
    out[span] = o

# size line: trades within 0.5 s after a book poll, at exactly that poll's ask for the bought side
x = T[["ticker", "ms", "yes", "px", "count_fp"]].sort_values("ms")
m = pd.merge_asof(x, B, left_on="ms", right_on="t", by="ticker", direction="backward", tolerance=500)
m = m.dropna(subset=["t"])
a = np.where(m["yes"], m["ask_yes"], m["ask_no"]); s = np.where(m["yes"], m["sz_ask_yes"], m["sz_ask_no"])
at = np.abs(m["px"].to_numpy(float) - a) < 1e-6
ratio = m["count_fp"].to_numpy(float)[at] / np.maximum(s[at], 1e-9)
out["sizes"] = {"trades_within_500ms_after_a_poll": int(len(m)), "of_them_at_the_polls_ask": int(at.sum()),
                "share_trade_size_at_or_under_displayed": round(float((ratio <= 1 + 1e-9).mean()), 4) if at.any() else None,
                "ratio_trade_to_displayed_p50_p90_p99": [round(float(v), 4) for v in np.percentile(ratio, [50, 90, 99])] if at.any() else None,
                "share_of_trades_in_500ms_not_at_the_polls_ask": round(float(1 - at.mean()), 4) if len(m) else None}
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps(out["counts"]))
