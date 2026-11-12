"""Re-score of V2's RECORD1 on R6 order books, covered part only. Method: RESCORE_GEN4_RECORD1_NOTE.md (committed before this ran).

The same test: V2's own module (scalper.record1: index_by_second, trade_for, judge, fee) is imported unmodified from a checkout of
claude/epic-ptolemy-0amjd9; only the rows fed to it change. No rule changed, no new try. No network, no account data.

usage: python3 -I record1_rescore.py <v2_kalshi_scalper_dir> <r6_root> <quotes_root> <out_json>
"""
import sys, os, glob, json, gzip, csv
from collections import defaultdict
import numpy as np
import pandas as pd

V2, R6, QROOT, OUT = sys.argv[1:5]
sys.path.insert(0, os.path.join(V2, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scalper import record1 as R1          # V2's scorer, unmodified
import r6load as R

SERIES = ("KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M")
T_FROM, T_TO = pd.Timestamp("2026-10-29T22:15:00Z"), pd.Timestamp("2026-11-03T21:00:00Z")      # the registered read ran 2026-11-03 21:10 UTC
assert T_TO < pd.Timestamp("2026-11-05T00:00:00Z")
EPS = 1e-9


def rows_gz(f):
    with gzip.open(f, "rt") as fh:
        return list(csv.DictReader(fh))


parts = []
for d in R.run_dirs(R6):
    f = os.path.join(d, "coverage.csv.gz")
    if os.path.exists(f):
        c = pd.read_csv(f, dtype={"ticker": str, "result": str})
        parts.append(c[c["ticker"].notna() & c["series"].isin(SERIES)])
cov = pd.concat(parts, ignore_index=True)
cov = cov[cov["result"].isin(["yes", "no"])].drop_duplicates("ticker").set_index("ticker")
cov["ct"] = pd.to_datetime(cov["close_time"], utc=True)
cov = cov[(cov["ct"] >= T_FROM) & (cov["ct"] <= T_TO)]
close_ms = (((cov["ct"] - R.EPOCH) / pd.Timedelta(milliseconds=1)).astype("int64")).to_dict()
result = cov["result"].to_dict()

# quote recorder: polls per ticker and the spot index of the same run folder, as V2's trades_for_run builds them
qpolls, qidx, clock_ok = {}, {}, {}
for f in sorted(glob.glob(os.path.join(QROOT, "quotes", "*", "*", "quotes.csv.gz"))):
    folder = os.path.dirname(f)
    by_t = defaultdict(list)
    for r in rows_gz(f):
        if r["ticker"] in close_ms and r["ticker"] not in qpolls and r["status"] == "active" and r["yes_bid"] and r["yes_ask"]:
            by_t[r["ticker"]].append({"t": int(r["t_recv_ms"]), "bid": float(r["yes_bid"]), "ask": float(r["yes_ask"]), "bid_size": float(r["bid_size"] or 0),
                                      "ask_size": float(r["ask_size"] or 0), "strike": float(r["strike"])})
    if not by_t:
        continue
    spot = rows_gz(os.path.join(folder, "spot.csv.gz")) if os.path.exists(os.path.join(folder, "spot.csv.gz")) else []
    idx = {a: R1.index_by_second(spot, a) for a in set(R1.ASSET.values())}
    for tk, ps in by_t.items():
        qpolls[tk] = sorted(ps, key=lambda q: q["t"]); qidx[tk] = idx[R1.ASSET[tk.split("-")[0]]]

# R6 polls in the same shape (last 62 s)
bparts = []
for d in R.run_dirs(R6):
    f = os.path.join(d, "book.csv.gz")
    if os.path.exists(f):
        b = pd.read_csv(f, usecols=["t_recv_ms", "ticker", "yes_bid_px_1", "no_bid_px_1", "yes_bid_sz_1", "no_bid_sz_1"])
        b = b[b["ticker"].isin(qpolls)]
        if len(b):
            left = (b["ticker"].map(close_ms) - b["t_recv_ms"]) / 1000.0
            bparts.append(b[(left <= 62) & (left > 0)])
B = pd.concat(bparts, ignore_index=True).drop_duplicates(["ticker", "t_recv_ms"]).sort_values(["ticker", "t_recv_ms"])
bpolls = {}
for tk, g in B.groupby("ticker", sort=False):
    yb = g["yes_bid_px_1"].to_numpy(float); nb = g["no_bid_px_1"].to_numpy(float)
    bs = np.nan_to_num(g["yes_bid_sz_1"].to_numpy(float)); as_ = np.nan_to_num(g["no_bid_sz_1"].to_numpy(float))
    bpolls[tk] = [{"t": int(t), "bid": float(a) if a == a else 0.0, "ask": float(1 - n) if n == n else 1.0, "bid_size": float(x), "ask_size": float(y), "strike": qpolls[tk][0]["strike"]}
                  for t, a, n, x, y in zip(g["t_recv_ms"].to_numpy(), yb, nb, bs, as_)]
common = sorted(set(qpolls) & set(bpolls))


def book_fill(tk, t_sig, side, limit, delay_ms):
    for q in bpolls[tk]:
        if q["t"] >= t_sig + delay_ms:
            if q["t"] >= close_ms[tk] or q["t"] - (t_sig + delay_ms) > 10000:
                return None
            p, sz = (q["ask"], q["ask_size"]) if side == "yes" else (1 - q["bid"], q["bid_size"])
            return p if (0 < p < 1 and sz >= 1 and (limit is None or p <= limit + EPS)) else None
    return None


def net(side, price, res):
    f = R1.fee(price)
    return (1 - price - f) if side == res else -(price + f)


L = defaultdict(list)
for tk in common:
    asset = R1.ASSET[tk.split("-")[0]]; res = result[tk]; cm = close_ms[tk]; strike = qpolls[tk][0]["strike"]; date = cov.loc[tk, "close_time"][:10]
    base = {"date": date, "asset": asset, "ticker": tk, "clock_ok": True}
    tq = R1.trade_for(qpolls[tk], qidx[tk], cm, res, strike)
    tb = R1.trade_for(bpolls[tk], qidx[tk], cm, res, strike)
    for nm, tr, polls in (("L1_quotes_common", tq, qpolls[tk]), ("L2_book_same_poll", tb, bpolls[tk])):
        if tr:
            t2 = R1.trade_for(polls, qidx[tk], cm, res, strike, R1.STRESS)
            L[nm].append({**tr, **base, "stress": t2["net"] if t2 else tr["net"]})
    if tb:
        t_sig = next(q["t"] for q in bpolls[tk] if q["t"] >= cm - tb["s"] * 1000)
        for nm, dl in (("L3_book_2s_limit", 2000), ("L3_book_6s_limit", 6000)):
            L[nm + "_signals"].append(1)
            p = book_fill(tk, t_sig, tb["side"], tb["price"], dl)
            if p is not None:
                L[nm].append({**tb, **base, "price": p, "net": net(tb["side"], p, res), "stress": net(tb["side"], p, res)})
    if tq:
        t_sig = next(q["t"] for q in qpolls[tk] if q["t"] >= cm - tq["s"] * 1000)
        for nm, lim in (("L4_quote_signal_book_price", None), ("L4_quote_signal_book_price_limit", tq["price"])):
            L[nm + "_signals"].append(1)
            p = book_fill(tk, t_sig, tq["side"], lim, 0)
            if p is not None:
                L[nm].append({**tq, **base, "price": p, "net": net(tq["side"], p, res), "stress": net(tq["side"], p, res), "paid_minus_quote": p - tq["price"]})


def line(tr, signals=None):
    if not tr:
        return {"n": 0}
    j = R1.judge(tr) if len(tr) >= 2 else {"n": len(tr)}
    v = np.array([t["net"] for t in tr]); g, l = v[v > 0].sum(), -v[v < 0].sum()
    o = {"n": len(tr), "dates": j.get("dates"), "mean_c": round(j["mean_c"], 2) if "mean_c" in j else None, "z_by_date": round(j["z"], 2) if "z" in j else None,
         "pf": round(float(g / l), 3) if l > 0 else None, "wins": int((v > 0).sum()), "mean_price": round(float(np.mean([t["price"] for t in tr])), 4),
         "mean_model_gap_c": round(float(np.mean([t["gap"] for t in tr])) * 100, 2), "by_asset_n_mean_c": {a: [n_, round(m_, 2)] for a, (n_, m_) in j.get("assets", {}).items()},
         "by_decision_second": {str(s): int(sum(1 for t in tr if t["s"] == s)) for s in R1.SECONDS}, "verdict_by_v2_judge": j.get("verdict")}
    if signals is not None:
        o["signals"] = signals; o["fill_share"] = round(len(tr) / signals, 3) if signals else None
    if tr and "paid_minus_quote" in tr[0]:
        o["paid_minus_quote_ask_c_mean"] = round(float(np.mean([t["paid_minus_quote"] for t in tr])) * 100, 2)
    return o


out = {"test": "RECORD1 re-scored on R6 books, covered part (same test, no new try)", "closes_from": str(T_FROM), "closes_to": str(T_TO), "series": SERIES,
       "windows_common": len(common), "windows_by_series": {s: int(sum(1 for t in common if t.startswith(s + "-"))) for s in SERIES},
       "L0_registered_read_2026-11-03": {"n": 300, "dates": 13, "mean_c": 3.81, "z": 1.60, "note": "all five series, Oct 22 to Nov 3, from V2's README"},
       "L1_quotes_common": line(L["L1_quotes_common"]), "L2_book_same_poll": line(L["L2_book_same_poll"]),
       "L3_book_2s_limit": line(L["L3_book_2s_limit"], len(L["L3_book_2s_limit_signals"])), "L3_book_6s_limit": line(L["L3_book_6s_limit"], len(L["L3_book_6s_limit_signals"])),
       "L4_quote_signal_book_price": line(L["L4_quote_signal_book_price"], len(L["L4_quote_signal_book_price_signals"])),
       "L4_quote_signal_book_price_limit": line(L["L4_quote_signal_book_price_limit"], len(L["L4_quote_signal_book_price_limit_signals"]))}
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
