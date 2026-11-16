#!/usr/bin/env python3
"""PERPSLANE4 real-data extract for the SECOND build (Forensics desk, Nov 16, 2026; the Head's order: both builds on identical files). Reads EXACTLY the 160 files of LANE4_FILES_MANIFEST.txt (sha256 1b46f85d4b1b92d20447240c284236107e64d754e1a6f340c072ad7d2846e369) from a directory holding the perp-data files, checks every file's sha256 against the manifest (any difference refuses) and reads candles from bid_close and ask_close, funding from funding_time and funding_rate of the per-day files (never funding/all-history.csv.gz).
TICKER WALL first: each row is read as a plain list and its first field compared with the wall BEFORE any other field is parsed: KXGOLDPERP, KXUS500PERP, KXUSTECH100PERP from 2026-09-10T00:00Z (1788998400), the 94 stock perps of the wall list from 2026-11-05T18:39:00Z (1793903940); nothing with end_ts or funding_time at or after 2026-11-17T00:00Z (1794873600); funding rows from 3 days before the name's start; duplicate candles and prints: the first (manifest order) kept, counted.
Schema as the other extracts: candle(ticker, end_ts, yes_bid, yes_ask) (empty bid or ask = NULL, counted), funding(ticker, ts, rate). usage: python3 -I lane4_extract_b2.py <manifest> <perp-data dir> <wall94.json> <out dir>   (self test: python3 -I lane4_extract_b2.py --selftest)"""
import sys, os, csv, gzip, json, hashlib, sqlite3, collections, tempfile
CUT = 1794873600; START_IDX = 1788998400; START_STK = 1793903940; IDX = ("KXGOLDPERP", "KXUS500PERP", "KXUSTECH100PERP")
def sha_of(p): 
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()
def flt(x):
    try: return float(x) if x != "" else None
    except ValueError: return None
def build(manifest, base, wall, out, expect_manifest_sha="1b46f85d4b1b92d20447240c284236107e64d754e1a6f340c072ad7d2846e369"):
    if expect_manifest_sha and sha_of(manifest) != expect_manifest_sha: raise SystemExit("REFUSED: the manifest does not hash to the agreed value")
    files = []
    for line in open(manifest):
        p = line.split()
        if len(p) == 2: files.append((p[0], p[1]))
    start = {t: START_IDX for t in IDX}; start.update({t: START_STK for t in wall}); W = set(start)
    os.makedirs(out, exist_ok=True); c = collections.Counter(); cd = {}; fd = {}
    for sha, rel in files:
        path = os.path.join(base, *rel.split("/"))
        if sha_of(path) != sha: raise SystemExit("REFUSED: %s does not hash to its manifest value" % rel)
        if "all-history" in rel: c["all-history refused"] += 1; continue
        with gzip.open(path, "rt", newline="") as fh:
            rd = csv.reader(fh); hdr = next(rd)
            if rel.startswith("kalshi1m/"):
                ie, ib, ia = hdr.index("end_period_ts"), hdr.index("bid_close"), hdr.index("ask_close")
                for row in rd:
                    t = row[0]
                    if t not in W: c["candle rows of other tickers (dropped)"] += 1; continue
                    e = int(float(row[ie]))
                    if e < start[t]: c["candle before the name's start"] += 1; continue
                    if e >= CUT: c["candle at or after the cut"] += 1; continue
                    if (t, e) in cd: c["duplicate candle (first kept)"] += 1; continue
                    b, a = flt(row[ib]), flt(row[ia])
                    if b is None or a is None: c["candle with a missing bid or ask (NULL)"] += 1
                    cd[(t, e)] = (b, a)
            elif rel.startswith("funding/"):
                it, ir = hdr.index("funding_time"), hdr.index("funding_rate")
                for row in rd:
                    t = row[0]
                    if t not in W: c["funding rows of other tickers (dropped)"] += 1; continue
                    ts = int(float(row[it]))
                    if ts < start[t] - 3 * 86400: c["funding before 3 days ahead of the start"] += 1; continue
                    if ts >= CUT: c["funding at or after the cut"] += 1; continue
                    if (t, ts) in fd: c["duplicate print (first kept)"] += 1; continue
                    fd[(t, ts)] = flt(row[ir])
            else: raise SystemExit("REFUSED: %s is neither a candle nor a funding file" % rel)
    dst = os.path.join(out, "LANE4_real_extract.sqlite")
    if os.path.exists(dst): os.remove(dst)
    db = sqlite3.connect(dst); db.execute("create table candle(ticker, end_ts, yes_bid, yes_ask)"); db.execute("create table funding(ticker, ts, rate)")
    db.executemany("insert into candle values(?,?,?,?)", [(t, e, v[0], v[1]) for (t, e), v in sorted(cd.items())]); db.executemany("insert into funding values(?,?,?)", [(t, ts, r) for (t, ts), r in sorted(fd.items()) if r is not None]); db.commit(); db.close()
    by = collections.Counter(t for (t, e) in cd)
    L = {"extract": "PERPSLANE4 real data", "manifest_sha256": sha_of(manifest), "files": len(files), "candles": len(cd), "prints": len(fd), "tickers_with_candles": len(by), "counts": dict(c), "extract_sha256": sha_of(dst), "extractor_sha256": sha_of(os.path.abspath(__file__))}
    json.dump(L, open(os.path.join(out, "LANE4_real_extract_cutlog.json"), "w"), indent=1, sort_keys=True); return L
def selftest():
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "kalshi1m")); os.makedirs(os.path.join(d, "funding"))
    def put(rel, hdr, rows):
        p = os.path.join(d, *rel.split("/")); 
        with gzip.open(p, "wt", newline="") as fh: w = csv.writer(fh); w.writerow(hdr); w.writerows(rows)
        return sha_of(p)
    h1 = ["ticker", "end_period_ts", "bid_open", "bid_close", "ask_close"]; hf = ["ticker", "funding_time", "funding_rate", "mark_price"]
    s1 = put("kalshi1m/a.csv.gz", h1, [["KXGOLDPERP", 1788998400, 1, 99.0, 99.1], ["KXGOLDPERP", 1788998399, 1, 1, 2], ["KXGOLDPERP", 1788998400, 1, 5, 6], ["KXOTHERPERP", 1788998460, 1, 5, 6], ["KXGOLDPERP", CUT, 1, 5, 6], ["KXAAPLPERP", 1793903940, 1, "", 7], ["KXAAPLPERP", 1793903939, 1, 1, 2]])
    s2 = put("funding/a.csv.gz", hf, [["KXAAPLPERP", 1793903940 - 3 * 86400, 0.0001, 1], ["KXAAPLPERP", 1793903940 - 3 * 86400 - 1, 0.0002, 1], ["KXAAPLPERP", CUT, 0.0003, 1], ["KXGOLDPERP", 1789000000, 0.0004, 1], ["KXZZZPERP", 1789000000, 0.1, 1]])
    s3 = put("funding/all-history.csv.gz", hf, [["KXGOLDPERP", 1789000001, 0.5, 1]])
    man = os.path.join(d, "M.txt"); open(man, "w").write("%s  kalshi1m/a.csv.gz\n%s  funding/a.csv.gz\n%s  funding/all-history.csv.gz\n" % (s1, s2, s3))
    L = build(man, d, ["KXAAPLPERP"], os.path.join(d, "out"), expect_manifest_sha=None); c = L["counts"]
    assert L["candles"] == 2 and L["prints"] == 2 and c["duplicate candle (first kept)"] == 1 and c["candle at or after the cut"] == 1 and c["candle before the name's start"] == 2 and c["candle rows of other tickers (dropped)"] == 1 and c["candle with a missing bid or ask (NULL)"] == 1, L
    assert c["funding before 3 days ahead of the start"] == 1 and c["funding at or after the cut"] == 1 and c["funding rows of other tickers (dropped)"] == 1 and c["all-history refused"] == 1, L
    open(os.path.join(d, "kalshi1m", "a.csv.gz"), "ab").write(b"x")
    try: build(man, d, ["KXAAPLPERP"], os.path.join(d, "out2"), expect_manifest_sha=None); raise AssertionError("a changed file must refuse")
    except SystemExit: pass
    print("lane4 extract selftest ok", c)
def main(a):
    if a[0] == "--selftest": return selftest()
    print(json.dumps(build(a[0], a[1], json.load(open(a[2])), a[3]), indent=1, sort_keys=True))
if __name__ == "__main__": main(sys.argv[1:])
