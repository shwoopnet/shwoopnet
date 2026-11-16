#!/usr/bin/env python3
"""ENGINE1 perps BACK-PULL extract (Forensics desk, Nov 16, 2026; the Head's order): KXGOLDPERP, KXUS500PERP, KXUSTECH100PERP, candles with end_ts from 2026-09-04T00:00Z to before 2026-11-01T00:00Z (Nov 1 on is EXCLUDED: US500 and US Tech 100 of Nov 6 to 14 are reserved for the forward read), plus funding prints in the same window where present.
Source: every kalshi1m/*.csv.gz and funding/*.csv.gz on perp-data (the back-pull files are <date>.only.csv.gz), files in name order, first wins. Schemas as the ENGINE1 perps extracts: market(ticker, series, close_ts NULL, result NULL, src), candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi), funding(ticker, ts, rate).
Rows outside the window are counted and not stored. usage: python3 -I engine1_perps_backpull.py <perp-data dir> <out dir> <tag>"""
import sys, os, csv, gzip, glob, sqlite3, json, hashlib, collections, calendar, time
T = ["KXGOLDPERP", "KXUS500PERP", "KXUSTECH100PERP"]
LO = calendar.timegm((2026, 9, 4, 0, 0, 0)); HI = calendar.timegm((2026, 11, 1, 0, 0, 0))
def num(x):
    try: return float(x) if x not in ("", None) else None
    except ValueError: return None
def ts(s): return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def main(a):
    root, out, tag = a; os.makedirs(out, exist_ok=True)
    cp, fp = os.path.join(out, "ENGINE1_perps_backpull_%s_extract.sqlite" % tag), os.path.join(out, "ENGINE1_perps_backpull_funding_%s_extract.sqlite" % tag)
    for p in (cp, fp):
        if os.path.exists(p): os.remove(p)
    o = sqlite3.connect(cp); o.execute("create table market(ticker, series, close_ts, result, src)"); o.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    for t in T: o.execute("insert into market values(?,?,?,?,?)", (t, t, None, None, "kalshi1m"))
    seen = set(); cc = collections.Counter(); nfiles = 0
    for p in sorted(glob.glob(os.path.join(root, "kalshi1m", "*.csv.gz"))):
        nfiles += 1
        for r in csv.DictReader(gzip.open(p, "rt", newline="")):
            if r["ticker"] not in T: continue
            e = int(r["end_period_ts"])
            if e < LO: cc["before 2026-09-04"] += 1; continue
            if e >= HI: cc["on or after 2026-11-01 (excluded)"] += 1; continue
            k = (r["ticker"], e)
            if k in seen: cc["duplicate_row"] += 1; continue
            seen.add(k); b, s = num(r["bid_close"]), num(r["ask_close"])
            if b is None or s is None: cc["missing_bid_or_ask"] += 1
            o.execute("insert into candle values(?,?,?,?,?,?,?)", (k[0], e, b, s, num(r["price_close"]), num(r["volume"]), num(r["open_interest"]))); cc["candles"] += 1
    o.commit(); o.execute("create index ix on candle(ticker)"); o.commit(); o.execute("vacuum"); o.close()
    f = sqlite3.connect(fp); f.execute("create table funding(ticker, ts, rate)"); seen = set(); cn = collections.Counter()
    for p in sorted(glob.glob(os.path.join(root, "funding", "*.csv.gz"))):
        for r in csv.DictReader(gzip.open(p, "rt", newline="")):
            if r["ticker"] not in T: continue
            t = ts(r["funding_time"])
            if t < LO or t >= HI: cn["outside window"] += 1; continue
            if (r["ticker"], t) in seen: cn["duplicate"] += 1; continue
            seen.add((r["ticker"], t)); rate = num(r["funding_rate"]); cn["prints"] += 1
            if rate is None: cn["missing rate (NULL)"] += 1
            f.execute("insert into funding values(?,?,?)", (r["ticker"], t, rate))
    f.commit(); f.execute("vacuum"); f.close()
    d = lambda t: time.strftime("%Y-%m-%d", time.gmtime(t)); c = sqlite3.connect(cp); g = sqlite3.connect(fp); by = {}
    for t in T:
        e = [x for (x,) in c.execute("select end_ts from candle where ticker=? order by end_ts", (t,))]; fr = [x for (x,) in g.execute("select ts from funding where ticker=? order by ts", (t,))]
        by[t] = {"candles": len(e), "first_end": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(e[0])) if e else None, "last_end": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(e[-1])) if e else None, "candle_dates": sorted({d(x) for x in e}),
                 "funding_prints": len(fr), "funding_first": d(fr[0]) if fr else None, "funding_last": d(fr[-1]) if fr else None, "funding_dates": sorted({d(x) for x in fr})}
    L = {"tag": tag, "window": ["2026-09-04T00:00Z", "2026-11-01T00:00Z (exclusive)"], "kalshi1m_files_read": nfiles, "candle_counts": dict(cc), "funding_counts": dict(cn), "by_ticker": by, "candle_extract_sha256": sha(cp), "funding_extract_sha256": sha(fp)}
    json.dump(L, open(os.path.join(out, "ENGINE1_perps_backpull_%s_cutlog.json" % tag), "w"), indent=1)
    print(json.dumps({k: L[k] for k in ("candle_counts", "funding_counts", "candle_extract_sha256", "funding_extract_sha256")}, indent=1))
    for t in T: print(t, by[t]["candles"], by[t]["first_end"], by[t]["last_end"], len(by[t]["candle_dates"]), "candle dates; funding", by[t]["funding_prints"], by[t]["funding_first"], by[t]["funding_last"])
if __name__ == "__main__": main(sys.argv[1:])
