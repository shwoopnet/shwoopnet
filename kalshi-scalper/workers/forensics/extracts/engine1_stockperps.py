#!/usr/bin/env python3
"""ENGINE1 ALL STOCK PERPS extract (Forensics desk, Nov 16, 2026; the Head's order): 1 minute candles and funding prints of EXACTLY the 94 Equities-class perps below (stocks plus SPY and QQQ; the list is the Equities class of the perps snapshot of 2026-11-16T17:00Z), from their first trade (2026-11-05T18:39Z) to before 2026-11-17T00:00Z (epoch checked with calendar.timegm), every kalshi1m and funding file on perp-data.
TICKER WALL: each row is read as a plain list and its first field (the ticker) is compared with the wall BEFORE any other field is touched; a row of any other ticker is dropped uncounted-by-field (only the number of rows dropped is counted). Only end_period_ts, bid_close, ask_close, price_close, volume and open_interest of a wall row are parsed; for funding: funding_time and funding_rate only.
Schema: market(ticker, series, close_ts NULL, result NULL, src); candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi); funding(ticker, ts, rate). Duplicates kept once (first file in name order) and counted. Nothing before 2026-11-05T18:39Z or from 2026-11-17T00:00Z on is stored.
usage: python3 -I engine1_perps15.py <dir with kalshi1m and funding folders> <out dir> <tag>"""
import sys, os, csv, gzip, glob, sqlite3, json, hashlib, collections, calendar, time
WALL = ("KXAAPLPERP", "KXABBVPERP", "KXABTPERP", "KXACNPERP", "KXADBEPERP", "KXADIPERP", "KXAMATPERP", "KXAMDPERP", "KXAMGNPERP", "KXAMZNPERP", "KXANETPERP", "KXAPHPERP", "KXARMPERP", "KXASMLPERP", "KXAVGOPERP", "KXAXPPERP", "KXBABAPERP", "KXBACPERP", "KXBAPERP", "KXBKNGPERP", "KXBLKPERP", "KXBRKBPERP", "KXCATPERP", "KXCOPPERP", "KXCOSTPERP", "KXCPERP", "KXCRMPERP", "KXCRWDPERP", "KXCSCOPERP", "KXCVXPERP", "KXDELLPERP", "KXDEPERP", "KXDHRPERP", "KXDISPERP", "KXGEPERP", "KXGEVPERP", "KXGILDPERP", "KXGOOGLPERP", "KXGSPERP", "KXHDPERP", "KXIBMPERP", "KXINTCPERP", "KXISRGPERP", "KXJNJPERP", "KXJPMPERP", "KXKLACPERP", "KXKOPERP", "KXLINPERP", "KXLLYPERP", "KXLMTPERP", "KXLRCXPERP", "KXMAPERP", "KXMCDPERP", "KXMETAPERP", "KXMRKPERP", "KXMSFTPERP", "KXMSPERP", "KXMUPERP", "KXNEEPERP", "KXNEMPERP", "KXNFLXPERP", "KXNVDAPERP", "KXORCLPERP", "KXPANWPERP", "KXPEPPERP", "KXPFEPERP", "KXPGPERP", "KXPLDPERP", "KXPLTRPERP", "KXPMPERP", "KXQCOMPERP", "KXQQQPERP", "KXRTXPERP", "KXSBUXPERP", "KXSCHWPERP", "KXSHOPPERP", "KXSKHYPERP", "KXSNDKPERP", "KXSPCXPERP", "KXSPYPERP", "KXTJXPERP", "KXTMOPERP", "KXTMUSPERP", "KXTSLAPERP", "KXTSMPERP", "KXTXNPERP", "KXUNHPERP", "KXUNPPERP", "KXVPERP", "KXVZPERP", "KXWELLPERP", "KXWFCPERP", "KXWMTPERP", "KXXOMPERP",)
END = calendar.timegm((2026, 11, 17, 0, 0, 0))
START = calendar.timegm((2026, 11, 5, 18, 39, 0))
def num(x):
    try: return float(x) if x not in ("", None) else None
    except ValueError: return None
def ts(s): return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def rows(path):
    r = csv.reader(gzip.open(path, "rt", newline="")); h = next(r, None)
    return h, r
def main(a):
    root, out, tag = a; os.makedirs(out, exist_ok=True); cp, fp = os.path.join(out, "ENGINE1_stockperps_%s_extract.sqlite" % tag), os.path.join(out, "ENGINE1_stockperps_funding_%s_extract.sqlite" % tag)
    for p in (cp, fp):
        if os.path.exists(p): os.remove(p)
    o = sqlite3.connect(cp); o.execute("create table market(ticker, series, close_ts, result, src)"); o.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    for t in WALL: o.execute("insert into market values(?,?,?,?,?)", (t, t, None, None, "kalshi1m"))
    seen = set(); cc = collections.Counter(); files = []
    for p in sorted(glob.glob(os.path.join(root, "kalshi1m", "*.csv.gz"))):
        h, r = rows(p); files.append(os.path.basename(p))
        if not h or h[0] != "ticker": raise SystemExit("unexpected header in " + p)
        ie, ib, ia, iv, ip, io = h.index("end_period_ts"), h.index("bid_close"), h.index("ask_close"), h.index("volume"), h.index("price_close"), h.index("open_interest")
        for row in r:
            if row[0] not in WALL: cc["rows outside the wall (dropped)"] += 1; continue
            e = int(row[ie])
            if e < START: cc["before 2026-11-05T18:39Z"] += 1; continue
            if e >= END: cc["at or after 2026-11-17T00:00Z (dropped)"] += 1; continue
            k = (row[0], e)
            if k in seen: cc["duplicate"] += 1; continue
            seen.add(k); b, s = num(row[ib]), num(row[ia])
            if b is None or s is None: cc["missing bid or ask (NULL)"] += 1
            o.execute("insert into candle values(?,?,?,?,?,?,?)", (row[0], e, b, s, num(row[ip]), num(row[iv]), num(row[io]))); cc["candles"] += 1
    o.commit(); o.execute("create index ix on candle(ticker)"); o.commit(); o.execute("vacuum"); o.close()
    f = sqlite3.connect(fp); f.execute("create table funding(ticker, ts, rate)"); seen = set(); cn = collections.Counter(); ff = []
    for p in sorted(glob.glob(os.path.join(root, "funding", "*.csv.gz"))):
        h, r = rows(p); ff.append(os.path.basename(p))
        if not h or h[0] != "ticker": raise SystemExit("unexpected header in " + p)
        it, ir = h.index("funding_time"), h.index("funding_rate")
        for row in r:
            if row[0] not in WALL: cn["rows outside the wall (dropped)"] += 1; continue
            t = ts(row[it])
            if t < START: cn["before 2026-11-05T18:39Z"] += 1; continue
            if t >= END: cn["at or after 2026-11-17T00:00Z (dropped)"] += 1; continue
            if (row[0], t) in seen: cn["duplicate"] += 1; continue
            seen.add((row[0], t)); rate = num(row[ir]); cn["prints"] += 1
            if rate is None: cn["missing rate (NULL)"] += 1
            f.execute("insert into funding values(?,?,?)", (row[0], t, rate))
    f.commit(); f.execute("vacuum"); f.close()
    d = lambda t: time.strftime("%Y-%m-%d", time.gmtime(t)); c = sqlite3.connect(cp); g = sqlite3.connect(fp); by = {}
    for t in WALL:
        e = [x for (x,) in c.execute("select end_ts from candle where ticker=? order by end_ts", (t,))]; fr = [x for (x,) in g.execute("select ts from funding where ticker=? order by ts", (t,))]; per = collections.Counter(d(x) for x in e)
        by[t] = {"candles": len(e), "per_day": dict(sorted(per.items())), "funding_prints": len(fr), "first_end": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(e[0])) if e else None, "last_end": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(e[-1])) if e else None}
    L = {"tag": tag, "wall": WALL, "candle_files": files, "funding_files": ff, "candle_counts": dict(cc), "funding_counts": dict(cn), "by_ticker": by, "candle_extract_sha256": sha(cp), "funding_extract_sha256": sha(fp)}
    json.dump(L, open(os.path.join(out, "ENGINE1_stockperps_%s_cutlog.json" % tag), "w"), indent=1)
    print(json.dumps({k: L[k] for k in ("candle_counts", "funding_counts", "candle_extract_sha256", "funding_extract_sha256")}, indent=1)); [print(t, by[t]["candles"], by[t]["funding_prints"], len(by[t]["per_day"]), "days", by[t]["first_end"], by[t]["last_end"]) for t in WALL]
if __name__ == "__main__": main(sys.argv[1:])
