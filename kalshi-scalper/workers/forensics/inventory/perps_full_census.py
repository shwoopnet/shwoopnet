#!/usr/bin/env python3
"""Full perps census (Forensics desk, Nov 16, 2026; the Head's order): every perp on perp-data's latest snapshot, all tabs. Counts and metadata only, no return or P&L.
Columns: ticker, class, status at the latest snapshot, two-sided at the latest snapshot, bid, ask, spread in bps of the mid, bid and ask size, 24h volume, open interest, notional open interest, funding_cap, funding_deadband, last funding print (time and rate) and the number of prints, first two-sided snapshot time, candle rows and first and last candle end, candle dates.
Max leverage is NOT in the data we hold (no column in the perps list rows we record): left blank. usage: python3 -I perps_full_census.py <perp-data dir> <out tsv>"""
import sys, os, csv, gzip, glob, collections, calendar, time
def f(x):
    try: return float(x)
    except Exception: return None
def iso(s): return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
def fmt(t): return time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(t))
def opn(p): return gzip.open(p, "rt", newline="") if p.endswith(".gz") else open(p, newline="")
def main(a):
    root, out = a; snaps = sorted(glob.glob(os.path.join(root, "perps", "perps-*.csv"))); last = {}; first2 = {}; lastts = ""
    for p in snaps + sorted(glob.glob(os.path.join(root, "perps30", "*", "*.csv*"))):
        for r in csv.DictReader(opn(p)):
            t = r["ticker"]; b, k = f(r["bid"]), f(r["ask"]); ts = r["ts_utc"]
            if b and k and b > 0 and k > 0 and b < k:
                x = iso(ts)
                if t not in first2 or x < first2[t]: first2[t] = x
            if "perps-" in os.path.basename(p) and ts >= lastts: lastts = ts
    for p in snaps[-2:]:
        for r in csv.DictReader(opn(p)):
            if r["ts_utc"] == lastts: last[r["ticker"]] = r
    fund = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(root, "funding", "*.csv.gz"))):
        for r in csv.DictReader(opn(p)): fund[r["ticker"]].append((r["funding_time"], f(r["funding_rate"])))
    cn = collections.defaultdict(set)
    for p in sorted(glob.glob(os.path.join(root, "kalshi1m", "*.csv.gz"))):
        h = csv.reader(opn(p)); hd = next(h); ie = hd.index("end_period_ts")
        for row in h: cn[row[0]].add(int(row[ie]))
    cols = ["ticker", "class", "status", "two_sided_now", "bid", "ask", "spread_bps", "bid_size", "ask_size", "volume_24h", "open_interest", "notional_oi_usd", "funding_cap", "funding_deadband", "max_leverage", "funding_last_time", "funding_last_rate", "funding_prints",
            "first_two_sided_snapshot", "candle_rows", "candle_first_end", "candle_last_end", "candle_dates"]
    W = open(out, "w"); W.write("\t".join(cols) + "\n"); n = collections.Counter()
    for t in sorted(last, key=lambda t: (last[t]["asset_class"], t)):
        r = last[t]; b, k = f(r["bid"]), f(r["ask"]); two = bool(b and k and b > 0 and k > 0 and b < k); fs = sorted(fund[t]); c = sorted(cn[t])
        row = [t, r["asset_class"], r["status"], str(two).lower(), r["bid"], r["ask"], "%.1f" % (10000 * (k - b) / ((k + b) / 2)) if two else "", r["bid_size"], r["ask_size"], r["volume_24h"], r["open_interest"], r["notional_oi_usd"], r["funding_cap"], r["funding_deadband"], "",
               fs[-1][0] if fs else "", "%.6f" % fs[-1][1] if fs and fs[-1][1] is not None else "", len(fs), fmt(first2[t]) if t in first2 else "", len(c), fmt(c[0]) if c else "", fmt(c[-1]) if c else "", len({time.strftime("%Y-%m-%d", time.gmtime(x)) for x in c})]
        W.write("\t".join(str(x) for x in row) + "\n"); n[(r["asset_class"], r["status"], two)] += 1
    W.close(); print("snapshot", lastts, "perps", len(last)); [print(k, v) for k, v in sorted(n.items())]
if __name__ == "__main__": main(sys.argv[1:])
