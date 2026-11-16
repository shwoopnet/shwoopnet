#!/usr/bin/env python3
"""ENGINE1 perps WALL extract (Forensics desk, Nov 16, 2026; Testing Desk's request): 1 minute candles and daily funding prints of EXACTLY the 15 stock perps below, from 2026-11-06T00:00Z, every kalshi1m and funding file on perp-data.
TICKER WALL: each row is read as a plain list and its first field (the ticker) is compared with the wall BEFORE any other field is touched; a row of any other ticker is dropped uncounted-by-field (only the number of rows dropped is counted). Only end_period_ts, bid_close, ask_close and volume of a wall row are parsed (the other candle columns are never read); for funding: funding_time and funding_rate only.
Schema: market(ticker, series, close_ts NULL, result NULL, src); candle(ticker, end_ts, yes_bid, yes_ask, last NULL, volume, oi NULL); funding(ticker, ts, rate). Duplicates kept once (first file in name order) and counted. Nothing before 2026-11-06T00:00Z is stored.
usage: python3 -I engine1_perps15.py <dir with kalshi1m and funding folders> <out dir> <tag>"""
import sys, os, csv, gzip, glob, sqlite3, json, hashlib, collections, calendar, time
WALL = ("KXSPCXPERP", "KXMUPERP", "KXTSLAPERP", "KXINTCPERP", "KXAMATPERP", "KXSNDKPERP", "KXQCOMPERP", "KXMETAPERP", "KXAMDPERP", "KXPLTRPERP", "KXAVGOPERP", "KXGOOGLPERP", "KXORCLPERP", "KXMSFTPERP", "KXAMZNPERP")
START = calendar.timegm((2026, 11, 6, 0, 0, 0))
def num(x):
    try: return float(x) if x not in ("", None) else None
    except ValueError: return None
def ts(s): return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def rows(path):
    r = csv.reader(gzip.open(path, "rt", newline="")); h = next(r, None)
    return h, r
def main(a):
    root, out, tag = a; os.makedirs(out, exist_ok=True); cp, fp = os.path.join(out, "ENGINE1_perps15_%s_extract.sqlite" % tag), os.path.join(out, "ENGINE1_perps15_funding_%s_extract.sqlite" % tag)
    for p in (cp, fp):
        if os.path.exists(p): os.remove(p)
    o = sqlite3.connect(cp); o.execute("create table market(ticker, series, close_ts, result, src)"); o.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    for t in WALL: o.execute("insert into market values(?,?,?,?,?)", (t, t, None, None, "kalshi1m"))
    seen = set(); cc = collections.Counter(); files = []
    for p in sorted(glob.glob(os.path.join(root, "kalshi1m", "*.csv.gz"))):
        h, r = rows(p); files.append(os.path.basename(p))
        if not h or h[0] != "ticker": raise SystemExit("unexpected header in " + p)
        ie, ib, ia, iv = h.index("end_period_ts"), h.index("bid_close"), h.index("ask_close"), h.index("volume")
        for row in r:
            if row[0] not in WALL: cc["rows outside the wall (dropped)"] += 1; continue
            e = int(row[ie])
            if e < START: cc["before 2026-11-06T00:00Z"] += 1; continue
            k = (row[0], e)
            if k in seen: cc["duplicate"] += 1; continue
            seen.add(k); b, s = num(row[ib]), num(row[ia])
            if b is None or s is None: cc["missing bid or ask (NULL)"] += 1
            o.execute("insert into candle values(?,?,?,?,?,?,?)", (row[0], e, b, s, None, num(row[iv]), None)); cc["candles"] += 1
    o.commit(); o.execute("create index ix on candle(ticker)"); o.commit(); o.execute("vacuum"); o.close()
    f = sqlite3.connect(fp); f.execute("create table funding(ticker, ts, rate)"); seen = set(); cn = collections.Counter(); ff = []
    for p in sorted(glob.glob(os.path.join(root, "funding", "*.csv.gz"))):
        h, r = rows(p); ff.append(os.path.basename(p))
        if not h or h[0] != "ticker": raise SystemExit("unexpected header in " + p)
        it, ir = h.index("funding_time"), h.index("funding_rate")
        for row in r:
            if row[0] not in WALL: cn["rows outside the wall (dropped)"] += 1; continue
            t = ts(row[it])
            if t < START: cn["before 2026-11-06T00:00Z"] += 1; continue
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
    json.dump(L, open(os.path.join(out, "ENGINE1_perps15_%s_cutlog.json" % tag), "w"), indent=1)
    print(json.dumps({k: L[k] for k in ("candle_counts", "funding_counts", "candle_extract_sha256", "funding_extract_sha256")}, indent=1)); [print(t, by[t]["candles"], by[t]["funding_prints"], len(by[t]["per_day"]), "days", by[t]["first_end"], by[t]["last_end"]) for t in WALL]
if __name__ == "__main__": main(sys.argv[1:])
