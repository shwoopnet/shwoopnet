"""MMMAP1 (protocol P8), NC15 part: realized-spread map on the 11 non-crypto 15 minute series (recorder NC15, branch nc-data, folder nc15/<date>/<HHMM>/).

Desk A, Nov 12 2026, written BEFORE any NC15 row was opened; zero API calls; NO settlement outcome is loaded (the coverage `result` column is not read), so it scores no rule and spends 0 tries.
It measures where a quote would have filled: effective half spread of each public trade against the last book mid, the mid's move 30, 60 and 180 seconds later (markout), the realized spread (effective minus the 60 s markout), by series, time left, 4 hour block, whole versus fractional trades and quoted spread.
Differences from the R6 script (mmmap1_r6.py), all fixed now: SERIES is the 11 NC15 series; the book poll is 5 s (not 2 s), so the coverage filter is max_gap_ms <= 30000 and a trade's mid0 may come from at most 10 s before it (two polls); trades in the last 60 s are dropped and a markout may not run into the last 5 s, as before.
usage: python3 -I mmmap1_nc15.py <data_root = the folder holding nc15/ dates> <out_json> [<pickle>]    (dates: the constant DATES below, 2026-11-11 to 2026-11-13; excluded windows: mmmap1_nc15_excluded_tickers.txt, printed as a count)
"""
import sys, os, glob, json
import numpy as np
import pandas as pd

ROOT, OUT = sys.argv[1], sys.argv[2]
DATES = ("2026-11-11", "2026-11-12", "2026-11-13")   # FIXED read set (the Head, Nov 14): the read set cannot grow by itself; read on Nov 15 or later. No env override. DATES_EXTRA is for the synthetic dry run only (env MM_DRYRUN_DATE, ignored unless it is set by the dry run's own path).
if os.environ.get("MM_DRYRUN_DATE"): DATES = DATES + (os.environ["MM_DRYRUN_DATE"],)
# Rule 1 of the Nov 14 exposure section (HELDOUT_REGISTRY.md): windows whose result the VA looked at are dropped here too, even though this script reads no result.
EXCL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mmmap1_nc15_excluded_tickers.txt")
EXCL = {l.strip() for l in open(EXCL_FILE) if l.strip()}
DROPPED = set()
SERIES = ["KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M", "KXAUDUSD15M", "KXUSDCAD15M", "KXNATGAS15M"]
HS = (30, 60, 180)
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
rng = np.random.default_rng(20261112)

rows, snaps = [], []
for d in sorted(glob.glob(os.path.join(ROOT, "*", "*"))):
    if os.path.basename(os.path.dirname(d)) not in DATES:
        continue
    c = pd.read_csv(os.path.join(d, "coverage.csv.gz"), usecols=["close_time", "series", "ticker", "max_gap_ms"], dtype={"ticker": str})
    c = c[c["ticker"].notna() & (c["max_gap_ms"] <= 30000)]
    DROPPED.update(c.loc[c["ticker"].isin(EXCL), "ticker"]); c = c[~c["ticker"].isin(EXCL)]
    T = dict(zip(c["ticker"], ((pd.to_datetime(c["close_time"], utc=True) - EPOCH) / pd.Timedelta(milliseconds=1)).astype("int64")))
    b = pd.read_csv(os.path.join(d, "book.csv.gz"), usecols=["t_recv_ms", "ticker", "series", "yes_bid_px_1", "yes_bid_sz_1", "no_bid_px_1", "no_bid_sz_1"])
    b = b[b["ticker"].isin(T)].dropna(subset=["yes_bid_px_1", "no_bid_px_1"])
    b["mid"] = (b["yes_bid_px_1"] + 1 - b["no_bid_px_1"]) / 2
    b["hs"] = (1 - b["no_bid_px_1"] - b["yes_bid_px_1"]) / 2
    b = b[b["hs"] >= 0]
    b["touch"] = (b["yes_bid_sz_1"] + b["no_bid_sz_1"]) / 2
    b = b.sort_values("t_recv_ms")
    b["left"] = (b["ticker"].map(T) - b["t_recv_ms"]) / 1000.0
    snaps.append(b[(b["left"] > 60) & (b["left"] <= 900)][["series", "ticker", "hs", "touch"]])
    t = pd.read_csv(os.path.join(d, "trades.csv.gz"))
    t = t[t["ticker"].isin(T)]
    ts = pd.to_datetime(t["created_time"], utc=True, format="ISO8601")
    t["ms"] = ((ts - EPOCH) / pd.Timedelta(milliseconds=1)).astype("int64")
    t["hour"] = ts.dt.hour
    t["left"] = (t["ticker"].map(T) - t["ms"]) / 1000.0
    t = t[(t["left"] > 60) & (t["left"] <= 900)].sort_values("ms")
    t["s"] = np.where(t["taker_outcome_side"] == "yes", 1.0, -1.0)
    bb = b[["t_recv_ms", "ticker", "mid", "hs", "touch"]]
    # mid0: last snapshot received at least 250 ms before the trade and at most 10 s before it
    t["key"] = t["ms"] - 250
    m = pd.merge_asof(t, bb.rename(columns={"t_recv_ms": "t0", "mid": "mid0", "hs": "hs0", "touch": "touch0"}),
                      left_on="key", right_on="t0", by="ticker", direction="backward", tolerance=10000)
    for h in HS:
        m["k%d" % h] = m["ms"] + h * 1000
        m = m.sort_values("k%d" % h)
        m = pd.merge_asof(m, bb[["t_recv_ms", "ticker", "mid"]].rename(columns={"t_recv_ms": "t%d" % h, "mid": "mid%d" % h}),
                          left_on="k%d" % h, right_on="t%d" % h, by="ticker", direction="forward", tolerance=10000)
        # a markout may not run into the last 5 seconds before the close
        m.loc[m["left"] - h < 5, "mid%d" % h] = np.nan
    m = m.dropna(subset=["mid0"])
    m["series"] = m["ticker"].str.split("-").str[0]
    m["e"] = m["s"] * (m["yes_price_dollars"] - m["mid0"])
    for h in HS:
        m["m%d" % h] = m["s"] * (m["mid%d" % h] - m["mid0"])
    c_ = m["count_fp"].to_numpy(float)
    m["frac"] = (np.abs(c_ - np.rint(c_)) > 0.001)
    rows.append(m[["series", "ticker", "hour", "left", "count_fp", "frac", "e", "hs0", "touch0", "m30", "m60", "m180", "yes_price_dollars", "s", "mid0"]])
    print("done", d, len(m), flush=True)

R = pd.concat(rows, ignore_index=True)
S = pd.concat(snaps, ignore_index=True)
R["r60"] = R["e"] - R["m60"]
R["tk"] = pd.factorize(R["ticker"])[0]
if len(sys.argv) > 3:
    R.drop(columns=["ticker"]).to_pickle(sys.argv[3]); S.to_pickle(sys.argv[3] + ".snaps")
    sys.exit(0)

def boot(g, col, wcol=None):
    g = g.dropna(subset=[col])
    if len(g) < 200:
        return None
    u, inv = np.unique(g["tk"].to_numpy(), return_inverse=True)
    w = g[wcol].to_numpy(float) if wcol else np.ones(len(g))
    num = np.bincount(inv, g[col].to_numpy(float) * w); den = np.bincount(inv, w)
    bs = []
    for _ in range(300):
        i = rng.integers(0, len(u), len(u))
        bs.append(num[i].sum() / den[i].sum())
    return [round(100 * num.sum() / den.sum(), 3), round(100 * float(np.percentile(bs, 2.5)), 3), round(100 * float(np.percentile(bs, 97.5)), 3)]

def line(g, sn=None):
    o = {"trades": int(len(g)), "contracts": float(g["count_fp"].sum()), "windows": int(g["ticker"].nunique()),
         "e_c": boot(g, "e"), "m30_c": boot(g, "m30"), "m60_c": boot(g, "m60"), "m180_c": boot(g, "m180"),
         "r60_c_per_trade": boot(g, "r60"), "r60_c_per_contract": boot(g, "r60", "count_fp"),
         "frac_share_contracts": float(g.loc[g["frac"], "count_fp"].sum() / max(g["count_fp"].sum(), 1e-9))}
    if sn is not None:
        o["quoted_half_spread_c"] = round(100 * float(sn["hs"].mean()), 3)
        o["median_touch"] = float(sn["touch"].median())
        o["contracts_per_hour"] = float(g["count_fp"].sum() / (g["ticker"].nunique() * 14 / 60))
    return o

res = {"dates": DATES, "excluded_windows_in_list": len(EXCL), "excluded_windows_dropped_here": len(DROPPED), "note": "cents; [mean, 2.5%, 97.5%] by resampling whole windows; trades in the last 60 s dropped"}
for s in SERIES:
    g = R[R["series"] == s]
    if g.empty:
        continue
    o = line(g, S[S["series"] == s])
    o["by_left"] = {k: line(g[(g["left"] > lo) & (g["left"] <= hi)]) for k, (lo, hi) in {"15-10": (600, 900), "10-5": (300, 600), "5-1": (60, 300)}.items()}
    o["by_blk_r60_trade"] = {str(b * 4): boot(g[g["hour"] // 4 == b], "r60") for b in range(6)}
    o["by_class_r60_trade"] = {"whole": boot(g[~g["frac"]], "r60"), "frac": boot(g[g["frac"]], "r60")}
    # trades that hit a 1 cent wide book or a wider one
    o["by_spread_r60_trade"] = {"hs<=0.5c": boot(g[g["hs0"] <= 0.0051], "r60"), "hs 1c": boot(g[(g["hs0"] > 0.0051) & (g["hs0"] <= 0.0101)], "r60"), "hs>1c": boot(g[g["hs0"] > 0.0101], "r60")}
    res[s] = o
print("EXCLUDED WINDOWS DROPPED: %d (list holds %d)" % (len(DROPPED), len(EXCL)))
json.dump(res, open(OUT, "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
