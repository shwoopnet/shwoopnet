"""PERPSLIST1: is the recorded perps LIST a delayed copy, measured against Kalshi's 1 minute perp candles?

Registration: PERPSLIST1_REGISTRATION.md (committed before any candle file was opened).
A measurement: no rule scored, nothing settles, zero tries. No network, no account data.

usage: python3 -I perpslist1.py <candles_dir> <hourly_dir> <perps30_dir> <out_json>
"""
import sys, os, glob, json
import numpy as np
import pandas as pd

CDIR, HDIR, FDIR, OUT = sys.argv[1:5]
rng = np.random.default_rng(20261112)

C = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(CDIR, "*.csv.gz")))], ignore_index=True)
for c in ("bid_close", "ask_close"):
    C[c] = pd.to_numeric(C[c], errors="coerce")
C = C.dropna(subset=["bid_close", "ask_close"])
C = C[(C["bid_close"] > 0) & (C["ask_close"] > C["bid_close"])].drop_duplicates(["ticker", "end_period_ts"]).sort_values(["ticker", "end_period_ts"])
C["mid"] = (C["bid_close"] + C["ask_close"]) / 2
cand = {tk: (g["end_period_ts"].to_numpy("int64"), g["mid"].to_numpy(float)) for tk, g in C.groupby("ticker", sort=False)}
c_dates = sorted({os.path.basename(f)[:10] for f in glob.glob(os.path.join(CDIR, "*.csv.gz"))})


def load_list(files, src):
    parts = []
    for f in files:
        d = pd.read_csv(f, dtype={"ticker": str, "status": str, "asset_class": str})
        d["src"] = src
        parts.append(d)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


Lh = load_list([f for f in sorted(glob.glob(os.path.join(HDIR, "perps-*.csv"))) if os.path.basename(f)[6:16] in c_dates], "hourly")
Lf = load_list(sorted(glob.glob(os.path.join(FDIR, "*", "*.csv.gz"))), "30s")
L = pd.concat([Lh, Lf], ignore_index=True)
for c in ("bid", "ask"):
    L[c] = pd.to_numeric(L[c], errors="coerce")
L = L[(L["status"] == "active") & (L["bid"] > 0) & (L["ask"] > L["bid"]) & L["ticker"].isin(cand)].copy()
L["t"] = (pd.to_datetime(L["ts_utc"], utc=True) - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)
L["mid"] = (L["bid"] + L["ask"]) / 2

rows = []
for tk, t, mid, bid, ask, src, cls in zip(L["ticker"], L["t"].to_numpy("int64"), L["mid"].to_numpy(float), L["bid"].to_numpy(float), L["ask"].to_numpy(float), L["src"], L["asset_class"]):
    ts, cm = cand[tk]
    e_next = ((t + 59) // 60) * 60            # the boundary at or after t
    for e in ({e_next - 60, e_next} if e_next != t else {t - 60, t, t + 60}):
        k = np.searchsorted(ts, e)
        if k >= len(ts) or ts[k] != e:
            continue
        lo, hi = np.searchsorted(ts, e - 600), np.searchsorted(ts, e + 600, side="right")
        seg_t, seg_m = ts[lo:hi], cm[lo:hi]
        step = np.abs(np.diff(seg_m))[np.diff(seg_t) == 60]
        if len(step) < 10:
            continue
        s = float(np.median(step))
        if s <= 0:
            continue
        d = int(t - e)
        if -60 <= d <= 60:
            rows.append((tk, cls, src, int(t), d, abs(mid - cm[k]) / s, abs(mid - cm[k]) / mid * 1e4, float(bid - 2e-4 * mid <= cm[k] <= ask + 2e-4 * mid)))
P = pd.DataFrame(rows, columns=["ticker", "cls", "src", "t", "d", "r", "bps", "inside"])


def A_stat(G):
    after, before = G[(G["d"] > 0) & (G["d"] <= 12)], G[(G["d"] >= -12) & (G["d"] < 0)]
    o = {"rows_after": int(len(after)), "rows_before": int(len(before)), "timestamps_after": int(after["t"].nunique()), "timestamps_before": int(before["t"].nunique()),
         "median_r_after": round(float(after["r"].median()), 4) if len(after) else None, "median_r_before": round(float(before["r"].median()), 4) if len(before) else None,
         "mean_d_after": round(float(after["d"].mean()), 2) if len(after) else None, "mean_d_before": round(float(before["d"].mean()), 2) if len(before) else None}
    if len(after) and len(before) and before["r"].median() > 0:
        o["A"] = round(float(after["r"].median() / before["r"].median()), 4)
        ta, tb = after.groupby("t")["r"].apply(np.array), before.groupby("t")["r"].apply(np.array)
        bs = []
        for _ in range(2000):
            a = np.concatenate(ta.iloc[rng.integers(0, len(ta), len(ta))].to_list()); b = np.concatenate(tb.iloc[rng.integers(0, len(tb), len(tb))].to_list())
            if np.median(b) > 0:
                bs.append(np.median(a) / np.median(b))
        o["A_interval"] = [round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)]
    return o


out = {"test": "PERPSLIST1", "candle_dates": c_dates, "candle_rows_two_sided": int(len(C)), "candle_tickers": int(len(cand)),
       "list_rows_usable": int(len(L)), "list_rows_by_source": L["src"].value_counts().to_dict(), "list_timestamps_by_source": L.groupby("src")["t"].nunique().to_dict(),
       "pairs": int(len(P)), "pairs_by_source": P["src"].value_counts().to_dict() if len(P) else {}, "pair_timestamps_by_source": P.groupby("src")["t"].nunique().to_dict() if len(P) else {},
       "note": "d = list time minus candle end time, seconds; r = |list mid - candle mid close| / the ticker's local median 1 minute move; A = median r for d in (0,12] over median r for d in [-12,0)"}
if len(P):
    out["primary_all"] = A_stat(P)
    out["by_source"] = {k: A_stat(G) for k, G in P.groupby("src")}
    out["by_class"] = {k: A_stat(G) for k, G in P.groupby("cls")}
    P["bin"] = (np.floor(P["d"] / 10.0) * 10).astype(int).clip(-60, 50)
    out["curve_10s_bins"] = {("%d_to_%d" % (b, b + 10)): {"rows": int(len(G)), "timestamps": int(G["t"].nunique()), "median_r": round(float(G["r"].median()), 4), "median_bps": round(float(G["bps"].median()), 3)}
                             for b, G in P.groupby("bin")}
    out["curve_by_source"] = {s: {("%d_to_%d" % (b, b + 10)): {"rows": int(len(G)), "timestamps": int(G["t"].nunique()), "median_r": round(float(G["r"].median()), 4)} for b, G in H.groupby("bin")} for s, H in P.groupby("src")}
    near = P[P["d"].abs() <= 5]
    out["within_5s_of_a_boundary"] = {"rows": int(len(near)), "timestamps": int(near["t"].nunique()), "share_candle_mid_inside_list_bid_ask_plus_2bps": round(float(near["inside"].mean()), 4) if len(near) else None,
                                      "mean_abs_diff_bps": round(float(near["bps"].mean()), 3) if len(near) else None, "d_values": sorted(near["d"].unique().tolist())}
    out["d_values_by_source"] = {s: {str(int(k)): int(v) for k, v in G.groupby("d")["t"].nunique().items()} for s, G in P.groupby("src")}
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
