"""Independent re-derivation of RETAILFRAC1 stage A (P3) and CRONCLUSTER1 stage A (P4).

Desk A, Nov 12 2026. Held data only (quote-data:book15r6 copied to the scratchpad),
zero API calls. NO outcome is loaded: the coverage `result` column is used only as
a presence flag and dropped. Cutoff is a date constant: run folders dated on or
before 2026-11-08 (tape), books for 2026-11-04..06 only.

usage: python3 -I verify_p3p4.py <data_root> <out_json>
"""
import sys, os, glob, json
import numpy as np
import pandas as pd

ROOT, OUT = sys.argv[1], sys.argv[2]
LAST_DATE = "2026-11-08"
SERIES = ["KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXGOLD15M"]
rng = np.random.default_rng(20261112)

folders = sorted(d for d in glob.glob(os.path.join(ROOT, "*", "*")) if os.path.basename(os.path.dirname(d)) <= LAST_DATE)

# ---------- coverage: the window filter ----------
cov = []
for d in folders:
    p = os.path.join(d, "coverage.csv.gz")
    if os.path.exists(p):
        c = pd.read_csv(p, dtype={"result": str, "ticker": str, "note": str})
        c["folder"] = d
        cov.append(c)
cov = pd.concat(cov, ignore_index=True)
cov = cov[cov["ticker"].notna() & (cov["ticker"] != "")]
cov["has_result"] = cov["result"].notna() & (cov["result"] != "")
cov = cov.drop(columns=["result"])  # presence flag only
cov = cov.sort_values("tape_trades", ascending=False).drop_duplicates("ticker")
tot = cov.groupby("series").size()
ok = cov[cov["has_result"] & (cov["max_gap_ms"] < 10000) &
         ((cov["tape_sum_count"] - cov["volume_fp"]).abs() <= 0.01 * cov["volume_fp"].clip(lower=1e-9))]
kept = ok.groupby("series").size()
close_ms = dict(zip(ok["ticker"], ((pd.to_datetime(ok["close_time"], utc=True) - pd.Timestamp("1970-01-01", tz="UTC")) / pd.Timedelta(milliseconds=1)).astype("int64")))
ser_of = dict(zip(ok["ticker"], ok["series"]))

# ---------- tape pass ----------
sizes = {s: {0: [], 1: []} for s in SERIES}           # class 0 whole, 1 frac
agg = {s: {k: np.zeros(2) for k in ("n", "ct", "yes_ct", "paid_sum", "paid_ct_sum")} for s in SERIES}
frac_by_min = {s: np.zeros((15, 2)) for s in SERIES}  # [minute bucket, class] contracts
frac_by_blk = {s: np.zeros((6, 2)) for s in SERIES}
nets = {}                                             # ticker -> [F, W] over (T-600, T-360]
sec_all, sec_67, sec_23 = {}, {}, {}                   # ticker -> 60-vector of contracts

for d in folders:
    p = os.path.join(d, "trades.csv.gz")
    if not os.path.exists(p):
        continue
    t = pd.read_csv(p)
    t = t[t["ticker"].isin(close_ms)]
    if t.empty:
        continue
    ts = pd.to_datetime(t["created_time"], utc=True, format="ISO8601")
    ms = ((ts - pd.Timestamp("1970-01-01", tz="UTC")) / pd.Timedelta(milliseconds=1)).to_numpy()
    t["ms"] = ms
    t["T"] = t["ticker"].map(close_ms)
    t["left"] = (t["T"] - t["ms"]) / 1000.0
    t = t[(t["left"] > 0) & (t["left"] <= 900)]
    c = t["count_fp"].to_numpy(float)
    t["frac"] = (np.abs(c - np.rint(c)) > 0.001).astype(int)
    t["yes"] = (t["taker_outcome_side"] == "yes").astype(int)
    t["paid"] = np.where(t["yes"] == 1, t["yes_price_dollars"], 1 - t["yes_price_dollars"])
    t["series"] = t["ticker"].map(ser_of)
    t["minb"] = np.minimum((t["left"] // 60).astype(int), 14)
    t["blk"] = ts.loc[t.index].dt.hour // 4
    t["sec"] = ts.loc[t.index].dt.second
    for s, g in t.groupby("series"):
        if s not in agg:
            continue
        for k in (0, 1):
            h = g[g["frac"] == k]
            sizes[s][k].append(h["count_fp"].to_numpy(np.float32))
            agg[s]["n"][k] += len(h)
            agg[s]["ct"][k] += h["count_fp"].sum()
            agg[s]["yes_ct"][k] += (h["count_fp"] * h["yes"]).sum()
            agg[s]["paid_sum"][k] += h["paid"].sum()
            agg[s]["paid_ct_sum"][k] += (h["paid"] * h["count_fp"]).sum()
        pv = g.pivot_table(index="minb", columns="frac", values="count_fp", aggfunc="sum", fill_value=0)
        for mb in pv.index:
            for k in pv.columns:
                frac_by_min[s][mb, k] += pv.loc[mb, k]
        pv = g.pivot_table(index="blk", columns="frac", values="count_fp", aggfunc="sum", fill_value=0)
        for b in pv.index:
            for k in pv.columns:
                frac_by_blk[s][b, k] += pv.loc[b, k]
    # per window nets over (T-600, T-360]
    w = t[(t["left"] >= 360) & (t["left"] < 600)].copy()
    w["signed"] = np.where(w["yes"] == 1, w["count_fp"], -w["count_fp"])
    nn = w.pivot_table(index="ticker", columns="frac", values="signed", aggfunc="sum", fill_value=0)
    for tk, row in nn.iterrows():
        nets[tk] = [float(row.get(1, 0.0)), float(row.get(0, 0.0))]
    # second-of-minute vectors
    for store, sub in ((sec_all, t), (sec_67, t[(t["left"] >= 360) & (t["left"] < 420)]), (sec_23, t[(t["left"] >= 120) & (t["left"] < 180)])):
        pv = sub.pivot_table(index="ticker", columns="sec", values="count_fp", aggfunc="sum", fill_value=0)
        arr = pv.reindex(columns=range(60), fill_value=0)
        for tk, row in zip(arr.index, arr.to_numpy(float)):
            store[tk] = store.get(tk, 0) + row
    print("tape", d, len(t), flush=True)

res = {"windows_total": tot.to_dict(), "windows_kept": kept.to_dict(), "p3": {}, "p4": {}}
for s in SERIES:
    a = agg[s]
    sz = {k: np.concatenate(sizes[s][k]) if sizes[s][k] else np.array([]) for k in (0, 1)}
    tks = [tk for tk in ok[ok["series"] == s]["ticker"]]
    F = np.array([nets.get(tk, [0, 0])[0] for tk in tks])
    W = np.array([nets.get(tk, [0, 0])[1] for tk in tks])
    res["p3"][s] = {
        "trades_whole": int(a["n"][0]), "trades_frac": int(a["n"][1]),
        "frac_share_trades": a["n"][1] / a["n"].sum(),
        "frac_share_contracts": a["ct"][1] / a["ct"].sum(),
        "median_whole": float(np.median(sz[0])), "median_frac": float(np.median(sz[1])),
        "p90_whole": float(np.percentile(sz[0], 90)), "p90_frac": float(np.percentile(sz[1], 90)),
        "yes_share_whole": a["yes_ct"][0] / a["ct"][0], "yes_share_frac": a["yes_ct"][1] / a["ct"][1],
        "paid_whole_per_trade": a["paid_sum"][0] / a["n"][0], "paid_frac_per_trade": a["paid_sum"][1] / a["n"][1],
        "paid_whole_per_contract": a["paid_ct_sum"][0] / a["ct"][0], "paid_frac_per_contract": a["paid_ct_sum"][1] / a["ct"][1],
        "corr_F_W": float(np.corrcoef(F, W)[0, 1]), "n_windows": len(tks),
        "frac_share_by_min": (frac_by_min[s][:, 1] / frac_by_min[s].sum(1)).round(3).tolist(),
        "frac_share_by_blk": (frac_by_blk[s][:, 1] / frac_by_blk[s].sum(1)).round(3).tolist(),
    }

    def peak(store):
        M = np.array([store[tk] for tk in tks if tk in store and np.ndim(store[tk])])
        if len(M) == 0:
            return None
        f = lambda X: X[:, :10].sum() / (X.sum() * 10 / 60)
        bs = [f(M[rng.integers(0, len(M), len(M))]) for _ in range(500)]
        sec0 = M[:, 0].sum() / (M.sum() / 60)
        return {"peak": float(f(M)), "lo": float(np.percentile(bs, 2.5)), "hi": float(np.percentile(bs, 97.5)), "sec0": float(sec0), "n": len(M)}
    res["p4"][s] = {"all": peak(sec_all), "m6_7": peak(sec_67), "m2_3": peak(sec_23)}

# ---------- book pass: touch depth before and after each minute boundary ----------
book_dates = ("2026-11-04", "2026-11-05", "2026-11-06")
pairs = []
for d in folders:
    if os.path.basename(os.path.dirname(d)) not in book_dates:
        continue
    p = os.path.join(d, "book.csv.gz")
    if not os.path.exists(p):
        continue
    b = pd.read_csv(p, usecols=["t_recv_ms", "ticker", "series", "yes_bid_px_1", "yes_bid_sz_1", "no_bid_px_1", "no_bid_sz_1"])
    b = b[b["ticker"].isin(close_ms)].dropna(subset=["yes_bid_px_1", "no_bid_px_1"])
    b["T"] = b["ticker"].map(close_ms)
    b["sec"] = (b["t_recv_ms"] // 1000) % 60
    b["minute"] = b["t_recv_ms"] // 60000
    b["depth"] = b["yes_bid_sz_1"] + b["no_bid_sz_1"]
    b["spread"] = 1 - b["yes_bid_px_1"] - b["no_bid_px_1"]
    bef = b[(b["sec"] >= 52)].sort_values("t_recv_ms").groupby(["ticker", "minute"]).tail(1)
    aft = b[(b["sec"] >= 8) & (b["sec"] <= 15)].sort_values("t_recv_ms").groupby(["ticker", "minute"]).head(1)
    bef = bef.assign(bmin=bef["minute"] + 1)[["ticker", "series", "T", "bmin", "depth", "spread"]]
    aft = aft.assign(bmin=aft["minute"])[["ticker", "bmin", "depth", "spread"]]
    m = bef.merge(aft, on=["ticker", "bmin"], suffixes=("_b", "_a"))
    m["left_min"] = (m["T"] - m["bmin"] * 60000) / 60000.0
    pairs.append(m[(m["left_min"] > 0) & (m["left_min"] < 15)])
    print("book", d, len(m), flush=True)
pairs = pd.concat(pairs, ignore_index=True)

def ratio(g):
    if len(g) < 30:
        return None
    tk = g["ticker"].to_numpy()
    u, inv = np.unique(tk, return_inverse=True)
    sb = np.bincount(inv, g["depth_b"]); sa = np.bincount(inv, g["depth_a"])
    bs = []
    for _ in range(500):
        i = rng.integers(0, len(u), len(u))
        bs.append(sa[i].sum() / sb[i].sum())
    return {"ratio": float(sa.sum() / sb.sum()), "lo": float(np.percentile(bs, 2.5)), "hi": float(np.percentile(bs, 97.5)),
            "pairs": int(len(g)), "spread_b": float(g["spread_b"].mean()), "spread_a": float(g["spread_a"].mean())}

for s in SERIES:
    g = pairs[pairs["series"] == s]
    res["p4"][s]["depth_all"] = ratio(g)
    res["p4"][s]["depth_6_7"] = ratio(g[(g["left_min"] >= 6) & (g["left_min"] <= 7)])
    res["p4"][s]["depth_2_3"] = ratio(g[(g["left_min"] >= 2) & (g["left_min"] <= 3)])

json.dump(res, open(OUT, "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
