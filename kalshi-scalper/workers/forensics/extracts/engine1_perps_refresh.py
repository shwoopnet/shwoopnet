#!/usr/bin/env python3
"""ENGINE1 perps REFRESH (Forensics desk, Nov 16, 2026): candles and funding of KXSPYPERP, KXQQQPERP, KXNVDAPERP, KXAAPLPERP, KXUS500PERP, KXUSTECH100PERP from kalshi1m and funding on perp-data (2026-11-06 on), every file on the branch at the time of the run, as ONE candle extract and ONE funding extract named with the run date.
Schemas as before: market(ticker, series, close_ts NULL, result NULL, src), candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi) and funding(ticker, ts, rate). Duplicates (same ticker and end_ts, or ticker and ts) are kept once (first file wins, files in name order) and counted; a missing bid or ask is kept as NULL and counted.
Earlier extracts keep their own hashes. usage: python3 -I engine1_perps_refresh.py <perp-data dir> <out dir> <tag, e.g. 20261116>"""
import sys, os, csv, gzip, glob, sqlite3, json, hashlib, collections, calendar, time
T = ["KXSPYPERP", "KXQQQPERP", "KXNVDAPERP", "KXAAPLPERP", "KXUS500PERP", "KXUSTECH100PERP"]; START = 1793923200
def num(x):
    try: return float(x) if x not in ("", None) else None
    except ValueError: return None
def ts(s): return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def main(a):
    root, out, tag = a; os.makedirs(out, exist_ok=True)
    cp, fp = (os.path.join(out, "ENGINE1_perps6_%s_extract.sqlite" % tag), os.path.join(out, "ENGINE1_funding6_%s_extract.sqlite" % tag))
    for p in (cp, fp):
        if os.path.exists(p): os.remove(p)
    o = sqlite3.connect(cp); o.execute("create table market(ticker, series, close_ts, result, src)"); o.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    for t in T: o.execute("insert into market values(?,?,?,?,?)", (t, t, None, None, "kalshi1m"))
    seen = set(); cc = collections.Counter(); cf = []
    for p in sorted(glob.glob(os.path.join(root, "kalshi1m", "*.csv.gz"))):
        cf.append(os.path.basename(p))
        for r in csv.DictReader(gzip.open(p, "rt", newline="")):
            if r["ticker"] not in T: continue
            k = (r["ticker"], int(r["end_period_ts"]))
            if k in seen: cc["duplicate_row"] += 1; continue
            seen.add(k); b, s = num(r["bid_close"]), num(r["ask_close"])
            if b is None or s is None: cc["missing_bid_or_ask"] += 1
            o.execute("insert into candle values(?,?,?,?,?,?,?)", (k[0], k[1], b, s, num(r["price_close"]), num(r["volume"]), num(r["open_interest"]))); cc["candles"] += 1
    o.commit(); o.execute("create index ix on candle(ticker)"); o.commit(); o.execute("vacuum"); o.close()
    f = sqlite3.connect(fp); f.execute("create table funding(ticker, ts, rate)"); seen = set(); cn = collections.Counter(); ff = []
    for p in sorted(glob.glob(os.path.join(root, "funding", "*.csv.gz"))):
        ff.append(os.path.basename(p))
        for r in csv.DictReader(gzip.open(p, "rt", newline="")):
            if r["ticker"] not in T: continue
            t = ts(r["funding_time"])
            if t < START: cn["before start"] += 1; continue
            if (r["ticker"], t) in seen: cn["duplicate"] += 1; continue
            seen.add((r["ticker"], t)); rate = num(r["funding_rate"]); cn["prints"] += 1
            if rate is None: cn["missing rate (NULL)"] += 1
            f.execute("insert into funding values(?,?,?)", (r["ticker"], t, rate))
    f.commit(); f.execute("vacuum"); f.close()
    d = lambda t: time.strftime("%Y-%m-%d", time.gmtime(t)); c = sqlite3.connect(cp); g = sqlite3.connect(fp); by = {}
    for t in T:
        e = [x for (x,) in c.execute("select end_ts from candle where ticker=? order by end_ts", (t,))]; fr = [x for (x,) in g.execute("select ts from funding where ticker=? order by ts", (t,))]
        by[t] = {"candles": len(e), "first_end": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(e[0])) if e else None, "last_end": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(e[-1])) if e else None, "candle_dates": sorted({d(x) for x in e}), "funding_prints": len(fr), "funding_dates": sorted({d(x) for x in fr})}
    L = {"tag": tag, "candle_files": cf, "funding_files": ff, "candle_counts": dict(cc), "funding_counts": dict(cn), "by_ticker": by, "candle_extract_sha256": sha(cp), "funding_extract_sha256": sha(fp)}
    json.dump(L, open(os.path.join(out, "ENGINE1_perps6_%s_cutlog.json" % tag), "w"), indent=1)
    print(json.dumps({k: L[k] for k in ("candle_counts", "funding_counts", "candle_extract_sha256", "funding_extract_sha256")}, indent=1))
    for t in T: print(t, by[t]["candles"], by[t]["first_end"], by[t]["last_end"], len(by[t]["candle_dates"]), "dates; funding", by[t]["funding_prints"])
if __name__ == "__main__": main(sys.argv[1:])
