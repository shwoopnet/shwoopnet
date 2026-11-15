#!/usr/bin/env python3
"""Single-stock and index perp census (Forensics desk, Nov 15, 2026; the Head's order). Counts and metadata only: quote, size, open interest, volume, funding and candle COVERAGE; no return, result or P&L is computed.
usage: python3 -I perps_census.py <perp-data checkout dir> <out dir>
Universe: asset_class Equities (stocks, SPY, QQQ) and Indices (US 500, US Tech 100, US 2000) in perps/*.csv. Two-sided quote: bid > 0, ask > 0, bid < ask. Spread in basis points of the mid."""
import sys, os, csv, gzip, glob, statistics as st, collections
from datetime import datetime, timezone

def op(p): return gzip.open(p, "rt", newline="") if p.endswith(".gz") else open(p, newline="")
def f(x):
    try: return float(x)
    except Exception: return None
def q(xs, p):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(p * (len(xs) - 1) + 0.5))] if xs else None
def iso(s): return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
def fmt(t): return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

def main(a):
    root, out = a[0], a[1]; os.makedirs(out, exist_ok=True)
    rows = collections.defaultdict(list); cls = {}
    for p in sorted(glob.glob(os.path.join(root, "perps", "*.csv"))) + sorted(glob.glob(os.path.join(root, "perps30", "*", "*.csv.gz"))):
        for r in csv.DictReader(op(p)):
            if r["asset_class"] in ("Equities", "Indices"):
                cls[r["ticker"]] = r["asset_class"]; rows[r["ticker"]].append((iso(r["ts_utc"]), r, "30s" if "perps30" in p else "1h"))
    fund = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(root, "funding", "*.csv.gz"))):
        for r in csv.DictReader(op(p)):
            if r["ticker"] in cls: fund[r["ticker"]].append((r["funding_time"], f(r["funding_rate"])))
    cn = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(root, "kalshi1m", "*.csv.gz"))):
        for r in csv.DictReader(op(p)):
            if r["ticker"] in cls: cn[r["ticker"]].append(int(r["end_period_ts"]))
    T = sorted(cls); hdr = ["ticker", "class", "underlying_from_name", "snapshot_rows", "two_sided_rows", "first_two_sided", "spread_bps_median", "spread_bps_p90", "tob_size_median_min", "volume_24h_median", "oi_median", "notional_oi_usd_median",
                            "fund_prints", "fund_first", "fund_last", "fund_median", "fund_min", "fund_max", "c1m_rows", "c1m_first", "c1m_last", "c1m_gaps_over_5m", "c1m_gaps_over_60m", "c1m_longest_gap_h"]
    W = open(os.path.join(out, "PERPS_CENSUS_NOV15_TICKERS.tsv"), "w"); W.write("\t".join(hdr) + "\n")
    summ = []
    for t in T:
        rs = sorted(rows[t], key=lambda x: x[0]); two = []; sp = []; sz = []
        for ts, r, k in rs:
            b, a_, bs, as_ = f(r["bid"]), f(r["ask"]), f(r["bid_size"]), f(r["ask_size"])
            if b and a_ and b > 0 and a_ > 0 and b < a_:
                two.append(ts); sp.append(10000 * (a_ - b) / ((a_ + b) / 2))
                if bs is not None and as_ is not None: sz.append(min(bs, as_))
        vol = [f(r["volume_24h"]) for _, r, _ in rs if f(r["volume_24h"])]; oi = [f(r["open_interest"]) for _, r, _ in rs if f(r["open_interest"])]; no = [f(r["notional_oi_usd"]) for _, r, _ in rs if f(r["notional_oi_usd"])]
        fr = [x for _, x in fund[t] if x is not None]; fs = sorted(fund[t]); c = sorted(set(cn[t])); gaps = [b - a_ for a_, b in zip(c, c[1:])]
        row = [t, cls[t], t[2:-4], len(rs), len(two), fmt(min(two)) if two else "", "%.1f" % st.median(sp) if sp else "", "%.1f" % q(sp, .9) if sp else "", "%.0f" % st.median(sz) if sz else "",
               "%.0f" % st.median(vol) if vol else "", "%.0f" % st.median(oi) if oi else "", "%.0f" % st.median(no) if no else "",
               len(fs), fs[0][0] if fs else "", fs[-1][0] if fs else "", "%.6f" % st.median(fr) if fr else "", "%.6f" % min(fr) if fr else "", "%.6f" % max(fr) if fr else "",
               len(c), fmt(c[0]) if c else "", fmt(c[-1]) if c else "", sum(1 for g in gaps if g > 300), sum(1 for g in gaps if g > 3600), "%.1f" % (max(gaps) / 3600) if gaps else ""]
        W.write("\t".join(str(x) for x in row) + "\n"); summ.append(row)
    W.close()
    print("tickers", len(T), "Equities", sum(1 for t in T if cls[t] == "Equities"), "Indices", sum(1 for t in T if cls[t] == "Indices"))
    for lab, i in (("spread_bps_median", 6), ("volume_24h_median", 9), ("oi_median", 10), ("notional_oi_usd_median", 11), ("fund_prints", 12), ("c1m_rows", 18)):
        v = [float(r[i]) for r in summ if r[i] != ""]; print(lab, "n", len(v), "min %.1f median %.1f max %.1f" % (min(v), st.median(v), max(v)))
    for r in summ:
        if r[18] == 0 or r[12] == 0 or r[4] == 0: print("EMPTY", r[0], "two_sided", r[4], "funding", r[12], "candles", r[18])
    print("first_two_sided range", min(r[5] for r in summ if r[5]), max(r[5] for r in summ if r[5]))
    print("candle range", min(r[19] for r in summ if r[19]), max(r[20] for r in summ if r[20]))
    print("funding range", min(r[13] for r in summ if r[13]), max(r[14] for r in summ if r[14]))

if __name__ == "__main__": main(sys.argv[1:])
