#!/usr/bin/env python3
"""ENGINE1 funding extract (Forensics desk, Nov 16, 2026; Desk A's request): funding prints of KXSPYPERP, KXQQQPERP, KXUS500PERP, KXUSTECH100PERP from 2026-11-06T00:00Z, from funding/<date>.csv.gz on perp-data.
Schema: funding(ticker, ts, rate): ts = the print's funding_time as epoch seconds (UTC), rate = funding_rate exactly as the file holds it (a fraction of notional per print; no sign change). Duplicates (same ticker and ts) are kept once (first file wins) and counted.
usage: python3 -I engine1_funding.py <perp-data dir> <out dir>"""
import sys, os, csv, gzip, glob, sqlite3, json, hashlib, collections, calendar, time
T = ["KXSPYPERP", "KXQQQPERP", "KXUS500PERP", "KXUSTECH100PERP"]; START = 1793923200
def ts(s): return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
def main(a):
    root, out = a[0], a[1]; os.makedirs(out, exist_ok=True); dst = os.path.join(out, "ENGINE1_funding_extract.sqlite")
    if os.path.exists(dst): os.remove(dst)
    o = sqlite3.connect(dst); o.execute("create table funding(ticker, ts, rate)"); seen = set(); cnt = collections.Counter(); files = []
    for p in sorted(glob.glob(os.path.join(root, "funding", "*.csv.gz"))):
        files.append(os.path.basename(p))
        for r in csv.DictReader(gzip.open(p, "rt", newline="")):
            if r["ticker"] not in T: continue
            t = ts(r["funding_time"])
            if t < START: cnt["before 2026-11-06T00:00Z"] += 1; continue
            if (r["ticker"], t) in seen: cnt["duplicate"] += 1; continue
            seen.add((r["ticker"], t)); rate = float(r["funding_rate"]) if r["funding_rate"] not in ("", None) else None
            if rate is None: cnt["missing rate (NULL)"] += 1
            o.execute("insert into funding values(?,?,?)", (r["ticker"], t, rate)); cnt["prints"] += 1
    o.commit(); o.execute("vacuum"); o.close(); sha = hashlib.sha256(open(dst, "rb").read()).hexdigest(); c = sqlite3.connect(dst)
    d = lambda t: time.strftime("%Y-%m-%d", time.gmtime(t)); by = {}
    for t in T:
        r = [x for (x,) in c.execute("select ts from funding where ticker=? order by ts", (t,))]; by[t] = {"prints": len(r), "dates": sorted({d(x) for x in r}), "first": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r[0])) if r else None, "last": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r[-1])) if r else None,
                                                             "hours_utc": sorted({time.strftime("%H:%M", time.gmtime(x)) for x in r})}
    L = {"files": files, "counts": dict(cnt), "by_ticker": by, "extract_sha256": sha}; json.dump(L, open(os.path.join(out, "ENGINE1_funding_cutlog.json"), "w"), indent=1); print(json.dumps({"counts": dict(cnt), "by_ticker": by, "sha": sha}, indent=1))
if __name__ == "__main__": main(sys.argv[1:])
