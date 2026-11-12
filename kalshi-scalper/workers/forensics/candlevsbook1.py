"""CANDLEVSBOOK1: is the 1 minute candle's ask close the R6 order book's ask at the minute's end? Bitcoin 15 minute market.

Registration: CANDLEVSBOOK1_REGISTRATION.md (committed before any candle was obtained).
A measurement: no rule scored, no settlement result loaded, zero tries. No network, no account data.

usage: python3 -I candlevsbook1.py <r6_root> <candles_csv> <out_json>
candles_csv: ticker, end_period_ts (unix seconds or ISO time), yes_bid_close, yes_ask_close (dollars or cents). A file with a result column is refused.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import r6load as R

R6, CAND, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SERIES = "KXBTC15M"
FROM, BEFORE = pd.Timestamp("2026-10-29T22:15:00Z"), pd.Timestamp("2026-11-12T00:00:00Z")
BANDS = {"3c_to_30c": (0.03, 0.30), "5c_to_30c": (0.05, 0.30)}
TOL_MS = 4000
EPS = 1e-9
rng = np.random.default_rng(20261112)

C = pd.read_csv(CAND)
assert not any(c.lower() in ("result", "outcome", "win", "won", "pnl", "settlement_value") for c in C.columns), "an outcome column is present"
ren = {}
for want, opts in (("end", ("end_period_ts", "end_ts", "end_time", "t_end")), ("bid", ("yes_bid_close", "bid_close", "yes_bid.close_dollars", "yes_bid_c")),
                   ("ask", ("yes_ask_close", "ask_close", "yes_ask.close_dollars", "yes_ask_c"))):
    hit = next((c for c in C.columns if c in opts), None)
    assert hit, "no column for " + want + " among " + str(list(C.columns))
    ren[hit] = want
C = C.rename(columns=ren)[["ticker", "end", "bid", "ask"]].dropna()
C["end_ms"] = (C["end"].astype("int64") * 1000) if np.issubdtype(C["end"].dtype, np.number) else R.to_ms(C["end"])
for c in ("bid", "ask"):
    C[c] = C[c].astype(float)
    if C[c].max() > 1.5:
        C[c] = C[c] / 100.0          # cents to dollars

# R6 close times (no result column) and books
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
C = C[C["ticker"].isin(close_ms)].copy()
C["left"] = (C["ticker"].map(close_ms) - C["end_ms"]) / 1000.0
C = C[(C["left"] >= 60 - 1) & (C["left"] <= 840 + 1) & (C["ask"] > C["bid"])]
bparts = []
for d in R.run_dirs(R6):
    f = os.path.join(d, "book.csv.gz")
    if os.path.exists(f):
        b = pd.read_csv(f, usecols=["t_recv_ms", "ticker", "yes_bid_px_1", "no_bid_px_1"])
        bparts.append(b[b["ticker"].isin(set(C["ticker"]))])
B = pd.concat(bparts, ignore_index=True).drop_duplicates(["ticker", "t_recv_ms"]).sort_values(["ticker", "t_recv_ms"])
books = {}
for tk, g in B.groupby("ticker", sort=False):
    t = g["t_recv_ms"].to_numpy(); yb = g["yes_bid_px_1"].to_numpy(float); nb = g["no_bid_px_1"].to_numpy(float)
    ok = (yb == yb) & (nb == nb) & (yb < 1 - nb - EPS)
    books[tk] = (t[ok], 1 - nb[ok], 1 - yb[ok])

C["ask_yes"] = C["ask"]; C["ask_no"] = 1 - C["bid"]
C = C[(C["ask_yes"] - C["ask_no"]).abs() > EPS]
C["side_yes"] = C["ask_yes"] < C["ask_no"]
C["c"] = np.where(C["side_yes"], C["ask_yes"], C["ask_no"])


def compare(tk, tms, side_yes, q, shift_ms=0):
    bk = books.get(tk)
    if bk is None:
        return (np.nan,) * 4
    t, ay, an = bk
    a = ay if side_yes else an
    x = tms + shift_ms
    k = np.searchsorted(t, x, side="right")
    b1, age = (a[k - 1], x - t[k - 1]) if k > 0 and x - t[k - 1] <= TOL_MS else (np.nan, np.nan)
    b2, lead = (a[k], t[k] - x) if k < len(t) and t[k] - x <= TOL_MS else (np.nan, np.nan)
    if b1 == b1 and b2 == b2:
        lo, hi = min(b1, b2), max(b1, b2)
        br = q - lo if q < lo else (q - hi if q > hi else 0.0)
        near = (q - b1) if age <= lead else (q - b2)
    else:
        br = np.nan; near = (q - b1) if b1 == b1 else (q - b2)
    return q - b1, q - b2, br, near


def cl(v, w):
    v = np.asarray(v, float); w = np.asarray(w); ok = v == v
    v, w = v[ok], w[ok]
    if len(v) == 0:
        return None
    u, inv = np.unique(w, return_inverse=True)
    num = np.bincount(inv, v); den = np.bincount(inv)
    pick = rng.integers(0, len(u), (2000, len(u)))
    bs = num[pick].sum(1) / den[pick].sum(1)
    return [round(float(v.mean()), 5), round(float(np.percentile(bs, 2.5)), 5), round(float(np.percentile(bs, 97.5)), 5)]


def dist(d, w):
    d = np.asarray(d, float); w = np.asarray(w); ok = d == d
    d, w = d[ok], w[ok]
    if len(d) == 0:
        return {"rows": 0}
    o = {"rows": int(len(d)), "windows": int(len(np.unique(w))), "mean": cl(d, w), "median": round(float(np.median(d)), 5),
         "mean_abs": cl(np.abs(d), w), "within_1c": cl((np.abs(d) <= 0.01 + 1e-6).astype(float), w)}
    for c in (0.02, 0.04, 0.10):
        o["candle_lower_by_%dc_or_more" % round(c * 100)] = cl((d <= -c + 1e-6).astype(float), w)
        o["candle_higher_by_%dc_or_more" % round(c * 100)] = cl((d >= c - 1e-6).astype(float), w)
    return o


def block(G):
    if len(G) == 0:
        return {"rows": 0}
    r = [compare(tk, tms, sy, q) for tk, tms, sy, q in zip(G["ticker"], G["end_ms"], G["side_yes"], G["c"])]
    D = pd.DataFrame(r, columns=["before", "after", "bracket", "near"], index=G.index)
    o = {"rows": int(len(G)), "windows": int(G["ticker"].nunique()), "with_a_book_poll": int((D["before"].notna() | D["after"].notna()).sum()),
         "against_poll_before": dist(D["before"], G["ticker"]), "against_poll_after": dist(D["after"], G["ticker"]),
         "bracket": dist(D["bracket"], G["ticker"]), "nearest_poll": dist(D["near"], G["ticker"])}
    curve = {}
    for k in range(-20, 21):
        rr = [compare(tk, tms, sy, q, k * 1000) for tk, tms, sy, q in zip(G["ticker"], G["end_ms"], G["side_yes"], G["c"])]
        near = np.array([x[3] for x in rr], float); br = np.array([x[2] for x in rr], float)
        ok = near == near
        if ok.any():
            curve[str(k)] = {"rows": int(ok.sum()), "mean_abs_nearest": round(float(np.abs(near[ok]).mean()), 5), "mean_signed_nearest": round(float(near[ok].mean()), 5),
                             "within_1c_bracket": round(float((np.abs(br[br == br]) <= 0.01 + 1e-6).mean()), 4) if (br == br).any() else None}
    o["shift_curve_seconds"] = curve
    if curve:
        o["best_shift_s"] = min(curve, key=lambda k: curve[k]["mean_abs_nearest"])
    return o


out = {"test": "CANDLEVSBOOK1", "series": SERIES, "closes_from": str(FROM), "closes_before": str(BEFORE),
       "note": "d = candle ask close minus book ask, dollars; negative = the candle shows a cheaper ask than the book; [value, 2.5%, 97.5%] by resampling windows",
       "counts": {"candles_in_range": int(len(C)), "windows": int(C["ticker"].nunique()), "r6_windows": int(len(close_ms))}}
for name, (lo, hi) in BANDS.items():
    G = C[(C["c"] >= lo - EPS) & (C["c"] <= hi + EPS)]
    out[name] = {"primary_candle_ending_120s_before_close": block(G[(G["left"] - 120).abs() <= 1]),
                 "all_minutes_14_to_1": block(G),
                 "by_minutes_left_bracket_within_1c": {str(int(m)): (lambda X: dist([compare(tk, tms, sy, q)[2] for tk, tms, sy, q in zip(X["ticker"], X["end_ms"], X["side_yes"], X["c"])], X["ticker"]).get("within_1c"))(G[(G["left"] / 60.0).round() == m])
                                                      for m in range(1, 15)}}
out["all_prices_all_minutes"] = block(C)
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps(out["counts"]))
