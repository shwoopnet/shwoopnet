"""QUOTEVSBOOK1: the quote recorder's ask (market object) against the R6 order book's ask, Bitcoin 15 minute market.

Registration: QUOTEVSBOOK1_REGISTRATION.md (committed before any quote file was fetched).
A measurement: no rule scored, no settlement result loaded, zero tries. No network, no account data.

usage: python3 -I quotevsbook1.py <r6_root> <quotes_root> <out_json> [signals_csv]
signals_csv (optional, from Desk A): t0_utc, ticker, side, ask_seen, edge [, quote_ms]; no outcome column.
"""
import sys, os, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import r6load as R

R6, QROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SIG = sys.argv[4] if len(sys.argv) > 4 else None
SERIES = "KXBTC15M"
FROM, BEFORE = pd.Timestamp("2026-10-29T22:15:00Z"), pd.Timestamp("2026-11-05T00:00:00Z")
SPANS = {"primary_150_120": (120.0, 150.0), "secondary_120_30": (30.0, 120.0)}
BAND = (0.05, 0.30)
TOL_MS = 4000
EPS = 1e-9
rng = np.random.default_rng(20261112)

# R6 coverage (no result column) for close times
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

# R6 books (last 200 s) with the server Date header for the clock check
bparts, hdr = [], []
for d in R.run_dirs(R6):
    f = os.path.join(d, "book.csv.gz")
    if not os.path.exists(f) or os.path.basename(os.path.dirname(d)) > "2026-11-05":
        continue
    b = pd.read_csv(f, usecols=["t_recv_ms", "server_date_header", "ticker", "yes_bid_px_1", "no_bid_px_1"])
    b = b[b["ticker"].isin(close_ms)]
    if b.empty:
        continue
    left = (b["ticker"].map(close_ms) - b["t_recv_ms"]) / 1000.0
    b = b[(left >= 0) & (left <= 200)]
    h = pd.to_datetime(b["server_date_header"], format="%a, %d %b %Y %H:%M:%S GMT", utc=True, errors="coerce")
    hm = ((h - R.EPOCH) / pd.Timedelta(milliseconds=1))
    hdr.append((hm + 500 - b["t_recv_ms"]).dropna().to_numpy())
    bparts.append(b[["t_recv_ms", "ticker", "yes_bid_px_1", "no_bid_px_1"]])
B = pd.concat(bparts, ignore_index=True).drop_duplicates(["ticker", "t_recv_ms"]).sort_values(["ticker", "t_recv_ms"])
books = {}
for tk, g in B.groupby("ticker", sort=False):
    t = g["t_recv_ms"].to_numpy(); yb = g["yes_bid_px_1"].to_numpy(float); nb = g["no_bid_px_1"].to_numpy(float)
    ok = (yb == yb) & (nb == nb) & (yb < 1 - nb - EPS)
    books[tk] = (t[ok], 1 - nb[ok], 1 - yb[ok])          # times, YES ask, NO ask
hdr = np.concatenate(hdr) if hdr else np.array([])

# quote recorder rows and its SNTP clock
qparts, clk = [], []
for d in sorted(glob.glob(os.path.join(QROOT, "quotes", "*", "*"))):
    f = os.path.join(d, "quotes.csv.gz")
    if os.path.exists(f):
        q = pd.read_csv(f, dtype={"ticker": str, "status": str})
        qparts.append(q[q["ticker"].isin(close_ms)])
    f = os.path.join(d, "clock.csv.gz")
    if os.path.exists(f):
        try:
            clk.append(pd.read_csv(f)["offset_ms"].to_numpy(float))
        except Exception:
            pass
Q = pd.concat(qparts, ignore_index=True).drop_duplicates(["ticker", "t_recv_ms"])
# Added after Part 1 was read (descriptive, flagged in the result): how long the quote endpoint returns the SAME state.
_q = Q.sort_values(["ticker", "t_recv_ms"])
_key = _q["yes_bid"].astype(str) + "|" + _q["yes_ask"].astype(str) + "|" + _q["bid_size"].astype(str) + "|" + _q["ask_size"].astype(str)
_chg = (_key != _key.groupby(_q["ticker"]).shift())
_gap = (_q[_chg.values].groupby("ticker")["t_recv_ms"].diff().dropna() / 1000.0).to_numpy()
_poll = (_q.groupby("ticker")["t_recv_ms"].diff().dropna() / 1000.0).to_numpy()
PERSIST = {"polls": int(len(_q)), "distinct_states": int(_chg.sum()), "polls_per_state": round(float(len(_q) / max(_chg.sum(), 1)), 2),
           "seconds_between_polls_median": round(float(np.median(_poll)), 2),
           "seconds_between_state_changes_p10_p25_p50_p75_p90": [round(float(x), 2) for x in np.percentile(_gap, [10, 25, 50, 75, 90])],
           "share_of_changes_10_to_12_s_apart": round(float(((_gap >= 10) & (_gap <= 12)).mean()), 4),
           "request_time_ms_median": float((_q["t_recv_ms"] - _q["t_send_ms"]).median())}
Q = Q[Q["status"].str.lower().isin(["active", "open"]) & Q["yes_bid"].notna() & Q["yes_ask"].notna()]
Q["left"] = (Q["ticker"].map(close_ms) - Q["t_recv_ms"]) / 1000.0
Q["ask_yes"] = Q["yes_ask"]; Q["ask_no"] = 1 - Q["yes_bid"]
Q = Q[(Q["ask_yes"] - Q["ask_no"]).abs() > EPS]
Q["side_yes"] = Q["ask_yes"] < Q["ask_no"]
Q["q"] = np.where(Q["side_yes"], Q["ask_yes"], Q["ask_no"])
Q = Q[(Q["q"] >= BAND[0] - EPS) & (Q["q"] <= BAND[1] + EPS) & (Q["left"] >= 30) & (Q["left"] <= 150)].reset_index(drop=True)


def book_at(tk, tms, side_yes):
    """(ask at the last poll at or before tms, its age ms, ask at the first poll after, its lead ms); NaN if none within TOL_MS."""
    bk = books.get(tk)
    if bk is None:
        return (np.nan, np.nan, np.nan, np.nan)
    t, ay, an = bk
    a = ay if side_yes else an
    k = np.searchsorted(t, tms, side="right")
    b1 = (a[k - 1], tms - t[k - 1]) if k > 0 and tms - t[k - 1] <= TOL_MS else (np.nan, np.nan)
    b2 = (a[k], t[k] - tms) if k < len(t) and t[k] - tms <= TOL_MS else (np.nan, np.nan)
    return (b1[0], b1[1], b2[0], b2[1])


def compare(tk, tms, side_yes, q, shift_ms=0):
    b1, age, b2, lead = book_at(tk, tms + shift_ms, side_yes)
    d1, d2 = q - b1, q - b2
    if b1 == b1 and b2 == b2:
        lo, hi = min(b1, b2), max(b1, b2)
        br = q - lo if q < lo else (q - hi if q > hi else 0.0)
        near = d1 if age <= lead else d2
    else:
        br = np.nan
        near = d1 if b1 == b1 else d2
    return d1, d2, br, near, age, lead


def cl(v, w, f=np.mean):
    v = np.asarray(v, float); w = np.asarray(w); ok = v == v
    v, w = v[ok], w[ok]
    if len(v) == 0:
        return None
    u, inv = np.unique(w, return_inverse=True)
    if f is np.mean:
        num = np.bincount(inv, v); den = np.bincount(inv)
        pick = rng.integers(0, len(u), (2000, len(u)))
        bs = num[pick].sum(1) / den[pick].sum(1)
        est = v.mean()
    return [round(float(est), 5), round(float(np.percentile(bs, 2.5)), 5), round(float(np.percentile(bs, 97.5)), 5)]


def dist(d, w):
    d = np.asarray(d, float); w = np.asarray(w); ok = d == d
    d, w = d[ok], w[ok]
    if len(d) == 0:
        return {"rows": 0}
    o = {"rows": int(len(d)), "windows": int(len(np.unique(w))), "mean": cl(d, w), "median": round(float(np.median(d)), 5),
         "mean_abs": cl(np.abs(d), w), "within_1c": cl((np.abs(d) <= 0.01 + 1e-6).astype(float), w)}
    for c in (0.02, 0.04, 0.10):
        o["quote_lower_by_%dc_or_more" % round(c * 100)] = cl((d <= -c + 1e-6).astype(float), w)
        o["quote_higher_by_%dc_or_more" % round(c * 100)] = cl((d >= c - 1e-6).astype(float), w)
    return o


rows = [compare(tk, tms, sy, q) for tk, tms, sy, q in zip(Q["ticker"], Q["t_recv_ms"], Q["side_yes"], Q["q"])]
Q[["d_before", "d_after", "bracket", "near", "age_ms", "lead_ms"]] = pd.DataFrame(rows, index=Q.index)
Q["has_book"] = Q["d_before"].notna() | Q["d_after"].notna()
out = {"test": "QUOTEVSBOOK1", "series": SERIES, "closes_from": str(FROM), "closes_before": str(BEFORE), "band": BAND,
       "note": "d = quote ask minus book ask, dollars (0.01 = 1 cent); negative = the quote shows a cheaper ask than the book; [value, 2.5%, 97.5%] by resampling windows",
       "counts": {"r6_windows_in_range": int(len(close_ms)), "quote_rows_in_band_30_150s": int(len(Q)), "with_a_book_poll": int(Q["has_book"].sum()),
                  "windows_with_quote_rows": int(Q["ticker"].nunique())},
       "quote_state_persistence": PERSIST,
       "clock": {"r6_date_header_plus_500ms_minus_recv_ms": {"n": int(len(hdr)), "median": float(np.median(hdr)) if len(hdr) else None,
                                                                "p05_p95": [float(np.percentile(hdr, 5)), float(np.percentile(hdr, 95))] if len(hdr) else None},
                 "quote_recorder_sntp_offset_ms": {"n": int(sum(len(x) for x in clk)), "median": float(np.median(np.concatenate(clk))) if clk else None,
                                                    "min_max": [float(np.concatenate(clk).min()), float(np.concatenate(clk).max())] if clk else None}}}
Qb = Q[Q["has_book"]]
for name, (lo, hi) in SPANS.items():
    G = Qb[(Qb["left"] >= lo) & (Qb["left"] <= hi)]
    o = {"rows": int(len(G)), "windows": int(G["ticker"].nunique()), "median_age_of_poll_before_ms": float(G["age_ms"].median()) if len(G) else None,
         "median_lead_of_poll_after_ms": float(G["lead_ms"].median()) if len(G) else None,
         "against_poll_before": dist(G["d_before"], G["ticker"]), "against_poll_after": dist(G["d_after"], G["ticker"]),
         "bracket": dist(G["bracket"], G["ticker"]), "nearest_poll": dist(G["near"], G["ticker"])}
    curve = {}
    # Registered range is -3 to +3 s. The minimum fell on the -3 edge, so the curve is extended to -20 s (flagged in the result as beyond the registration).
    for k in list(range(-20, -3)) + list(range(-3, 4)):
        r = [compare(tk, tms, sy, q, k * 1000) for tk, tms, sy, q in zip(G["ticker"], G["t_recv_ms"], G["side_yes"], G["q"])]
        near = np.array([x[3] for x in r], float); br = np.array([x[2] for x in r], float)
        ok = near == near
        curve[str(k)] = {"rows": int(ok.sum()), "mean_abs_nearest": round(float(np.abs(near[ok]).mean()), 5) if ok.any() else None,
                         "within_1c_bracket": round(float((np.abs(br[br == br]) <= 0.01 + 1e-6).mean()), 4) if (br == br).any() else None,
                         "quote_lower_2c_bracket": round(float((br[br == br] <= -0.02 + 1e-6).mean()), 4) if (br == br).any() else None}
    o["shift_curve_seconds"] = curve
    o["best_shift_s_registered_range"] = min((k for k in curve if -3 <= int(k) <= 3 and curve[k]["mean_abs_nearest"] is not None), key=lambda k: curve[k]["mean_abs_nearest"])
    o["best_shift_s"] = min((k for k in curve if curve[k]["mean_abs_nearest"] is not None), key=lambda k: curve[k]["mean_abs_nearest"])
    kb = int(o["best_shift_s"])
    rb = [compare(tk, tms, sy, q, kb * 1000) for tk, tms, sy, q in zip(G["ticker"], G["t_recv_ms"], G["side_yes"], G["q"])]
    o["at_best_shift"] = {"bracket": dist([x[2] for x in rb], G["ticker"]), "nearest_poll": dist([x[3] for x in rb], G["ticker"])}
    # by price bucket, bracket measure
    o["bracket_by_bucket"] = {nm: dist(G[(G["q"] >= a - EPS) & (G["q"] < b)]["bracket"], G[(G["q"] >= a - EPS) & (G["q"] < b)]["ticker"])
                              for nm, a, b in (("05-10c", 0.05, 0.10), ("10-20c", 0.10, 0.20), ("20-30c", 0.20, 0.30 + 1e-6))}
    out[name] = o

if SIG:
    S = pd.read_csv(SIG)
    S["t_ms"] = S["quote_ms"].astype("int64") if "quote_ms" in S.columns and S["quote_ms"].notna().all() else R.to_ms(S["t0_utc"])
    S = S[S["ticker"].isin(close_ms)].reset_index(drop=True)
    r = [compare(tk, int(tms), sd == "yes", float(q)) for tk, tms, sd, q in zip(S["ticker"], S["t_ms"], S["side"], S["ask_seen"])]
    S[["d_before", "d_after", "bracket", "near", "age_ms", "lead_ms"]] = pd.DataFrame(r, index=S.index)
    S = S[S["d_before"].notna() | S["d_after"].notna()]
    p2 = {"rows_with_book": int(len(S)), "time_used": "quote_ms" if "quote_ms" in S.columns else "t0_utc"}
    for e in (1, 0):
        G = S[S["edge"] == e]
        p2["edge_%d" % e] = {"rows": int(len(G)), "windows": int(G["ticker"].nunique()), "against_poll_before": dist(G["d_before"], G["ticker"]),
                             "against_poll_after": dist(G["d_after"], G["ticker"]), "bracket": dist(G["bracket"], G["ticker"])}
    # difference edge minus non-edge, resampling windows within each group
    def diff(col, f):
        a = S[S["edge"] == 1]; b = S[S["edge"] == 0]
        a = a[a[col].notna()]; b = b[b[col].notna()]
        if len(a) == 0 or len(b) == 0:
            return None
        ua, ub = a["ticker"].unique(), b["ticker"].unique()
        ga = {k: f(v[col].to_numpy()) for k, v in a.groupby("ticker")}; na = a.groupby("ticker").size().to_dict()
        gb = {k: f(v[col].to_numpy()) for k, v in b.groupby("ticker")}; nb_ = b.groupby("ticker").size().to_dict()
        est = f(a[col].to_numpy()).sum() / len(a) - f(b[col].to_numpy()).sum() / len(b)
        bs = []
        for _ in range(2000):
            pa = rng.choice(ua, len(ua)); pb = rng.choice(ub, len(ub))
            bs.append(sum(ga[k].sum() for k in pa) / sum(na[k] for k in pa) - sum(gb[k].sum() for k in pb) / sum(nb_[k] for k in pb))
        return [round(float(est), 5), round(float(np.percentile(bs, 2.5)), 5), round(float(np.percentile(bs, 97.5)), 5)]
    p2["edge_minus_nonedge"] = {"mean_d_bracket": diff("bracket", lambda v: v), "share_quote_lower_2c_bracket": diff("bracket", lambda v: (v <= -0.02 + 1e-6).astype(float)),
                                "mean_d_before": diff("d_before", lambda v: v), "share_quote_lower_2c_before": diff("d_before", lambda v: (v <= -0.02 + 1e-6).astype(float))}
    out["part2_model_rows"] = p2
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps(out["counts"]), json.dumps(out["clock"]))
