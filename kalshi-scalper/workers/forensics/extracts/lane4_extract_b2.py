#!/usr/bin/env python3
"""PERPSLANE4 real-data extract for the SECOND build (Forensics desk, Nov 16, 2026; the Head's order: both builds on identical files). Reads EXACTLY the 160 files of LANE4_FILES_MANIFEST.txt (sha256 1b46f85d4b1b92d20447240c284236107e64d754e1a6f340c072ad7d2846e369) from a directory holding the perp-data files, checks every file's sha256 against the manifest (any difference refuses) and reads candles from bid_close and ask_close, funding from funding_time and funding_rate of the per-day files (never funding/all-history.csv.gz).
TICKER WALL first: each row is read as a plain list and its first field compared with the wall BEFORE any other field is parsed: KXGOLDPERP, KXUS500PERP, KXUSTECH100PERP from 2026-09-10T00:00Z (1788998400), the 94 stock perps of the wall list from 2026-11-05T18:39:00Z (1793903940); nothing with end_ts or funding_time at or after 2026-11-17T00:00Z (1794873600); funding rows from 3 days before the name's start; duplicate candles and prints: the first (manifest order) kept, counted.
Schema as the other extracts: candle(ticker, end_ts, yes_bid, yes_ask) (empty bid or ask = NULL, counted), funding(ticker, ts, rate). usage: python3 -I lane4_extract_b2.py <manifest> <perp-data dir> <out dir>   (self test: python3 -I lane4_extract_b2.py --selftest). REFUSES unless HELDOUT_PULL_RUNS.md carries a line naming this file, its own sha256 and the manifest sha256 ('readable ONLY by Forensics PERPSLANE4 extractor lane4_extract_b2.py'); the wall of 94 names is embedded and pinned."""
import sys, os, re, csv, gzip, json, hashlib, sqlite3, collections, tempfile, calendar
WALL94 = ["KXAAPLPERP", "KXABBVPERP", "KXABTPERP", "KXACNPERP", "KXADBEPERP", "KXADIPERP", "KXAMATPERP", "KXAMDPERP", "KXAMGNPERP", "KXAMZNPERP", "KXANETPERP", "KXAPHPERP", "KXARMPERP", "KXASMLPERP", "KXAVGOPERP", "KXAXPPERP", "KXBABAPERP", "KXBACPERP", "KXBAPERP", "KXBKNGPERP", "KXBLKPERP", "KXBRKBPERP", "KXCATPERP", "KXCOPPERP", "KXCOSTPERP", "KXCPERP", "KXCRMPERP", "KXCRWDPERP", "KXCSCOPERP", "KXCVXPERP", "KXDELLPERP", "KXDEPERP", "KXDHRPERP", "KXDISPERP", "KXGEPERP", "KXGEVPERP", "KXGILDPERP", "KXGOOGLPERP", "KXGSPERP", "KXHDPERP", "KXIBMPERP", "KXINTCPERP", "KXISRGPERP", "KXJNJPERP", "KXJPMPERP", "KXKLACPERP", "KXKOPERP", "KXLINPERP", "KXLLYPERP", "KXLMTPERP", "KXLRCXPERP", "KXMAPERP", "KXMCDPERP", "KXMETAPERP", "KXMRKPERP", "KXMSFTPERP", "KXMSPERP", "KXMUPERP", "KXNEEPERP", "KXNEMPERP", "KXNFLXPERP", "KXNVDAPERP", "KXORCLPERP", "KXPANWPERP", "KXPEPPERP", "KXPFEPERP", "KXPGPERP", "KXPLDPERP", "KXPLTRPERP", "KXPMPERP", "KXQCOMPERP", "KXQQQPERP", "KXRTXPERP", "KXSBUXPERP", "KXSCHWPERP", "KXSHOPPERP", "KXSKHYPERP", "KXSNDKPERP", "KXSPCXPERP", "KXSPYPERP", "KXTJXPERP", "KXTMOPERP", "KXTMUSPERP", "KXTSLAPERP", "KXTSMPERP", "KXTXNPERP", "KXUNHPERP", "KXUNPPERP", "KXVPERP", "KXVZPERP", "KXWELLPERP", "KXWFCPERP", "KXWMTPERP", "KXXOMPERP"]
WALL94_SHA = "3958bb6e7f7a604d83cb64c8e2268457826c9de054ac5514a31cb94893f02824"      # sha256 of json.dumps(sorted list): the wall is embedded, not an argument
MANIFEST_SHA = "1b46f85d4b1b92d20447240c284236107e64d754e1a6f340c072ad7d2846e369"
HERE = os.path.dirname(os.path.abspath(__file__)); ALLOW_FILE = os.path.join(HERE, "..", "..", "HELDOUT_PULL_RUNS.md")
CUT = 1794873600; START_IDX = 1788998400; START_STK = 1793903940; IDX = ("KXGOLDPERP", "KXUS500PERP", "KXUSTECH100PERP")
def sha_of(p): 
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()
def iso(x):
    """funding_time like 2026-11-06T16:00:00Z or 2026-11-06T16:00:00.000Z -> epoch seconds. Anything else REFUSES (never a silent skip)."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?Z", x)
    if not m: raise SystemExit("REFUSED: funding_time %r is not an ISO UTC time ending in Z" % x)
    return calendar.timegm(tuple(int(g) for g in m.groups()))
def ets(x):
    if not re.fullmatch(r"\d+", x): raise SystemExit("REFUSED: end_period_ts %r is not an integer" % x)
    return int(x)
def flt(x):
    try: return float(x) if x != "" else None
    except ValueError: return None
def refuse_unless_allowed(manifest, allow_file=None):
    allow_file = ALLOW_FILE if allow_file is None else allow_file
    try: lines = open(allow_file).read().splitlines()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    need = [os.path.basename(os.path.abspath(__file__)), sha_of(os.path.abspath(__file__)), MANIFEST_SHA]
    if not any(all(n in l for n in need) for l in lines): raise SystemExit("REFUSED: no line of HELDOUT_PULL_RUNS.md names this extractor, its sha256 and the manifest sha256")
def build(manifest, base, wall, out, expect_manifest_sha=MANIFEST_SHA, allow_file="unchecked"):
    if allow_file != "unchecked": refuse_unless_allowed(manifest, allow_file)
    if hashlib.sha256(json.dumps(sorted(wall)).encode()).hexdigest() != WALL94_SHA and expect_manifest_sha: raise SystemExit("REFUSED: the wall list does not hash to the pinned value")
    if expect_manifest_sha and sha_of(manifest) != expect_manifest_sha: raise SystemExit("REFUSED: the manifest does not hash to the agreed value")
    files = []
    for line in open(manifest):
        p = line.split()
        if len(p) == 2: files.append((p[0], p[1]))
    files.sort(key=lambda f: f[1])           # sorted path order, as the Testing Desk's loader (the first of two disagreeing files is the same row for both builds)
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
                    e = ets(row[ie])
                    if e < start[t]: c["candle before the name's start"] += 1; continue
                    if e >= CUT: c["candle at or after the cut"] += 1; continue
                    b, a = flt(row[ib]), flt(row[ia])
                    if (t, e) in cd:
                        c["duplicate candle (first kept)"] += 1
                        if cd[(t, e)] != (b, a): c["duplicate candle differs"] += 1
                        continue
                    if b is None or a is None: c["candle with a missing bid or ask (NULL)"] += 1
                    cd[(t, e)] = (b, a)
            elif rel.startswith("funding/"):
                it, ir = hdr.index("funding_time"), hdr.index("funding_rate")
                for row in rd:
                    t = row[0]
                    if t not in W: c["funding rows of other tickers (dropped)"] += 1; continue
                    ts = iso(row[it])
                    if ts < start[t] - 3 * 86400: c["funding before 3 days ahead of the start"] += 1; continue
                    if ts >= CUT: c["funding at or after the cut"] += 1; continue
                    if (t, ts) in fd:
                        c["duplicate print (first kept)"] += 1
                        if fd[(t, ts)] != flt(row[ir]): c["duplicate print differs"] += 1
                        continue
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
    Z = lambda t: __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(t))
    s2 = put("funding/a.csv.gz", hf, [["KXAAPLPERP", Z(1793903940 - 3 * 86400), 0.0001, 1], ["KXAAPLPERP", Z(1793903940 - 3 * 86400 - 1), 0.0002, 1], ["KXAAPLPERP", Z(CUT), 0.0003, 1], ["KXGOLDPERP", Z(1789000000)[:-1] + ".000Z", 0.0004, 1], ["KXZZZPERP", Z(1789000000), 0.1, 1]])
    s3 = put("funding/all-history.csv.gz", hf, [["KXGOLDPERP", 1789000001, 0.5, 1]])
    man = os.path.join(d, "M.txt"); open(man, "w").write("%s  kalshi1m/a.csv.gz\n%s  funding/a.csv.gz\n%s  funding/all-history.csv.gz\n" % (s1, s2, s3))
    L = build(man, d, ["KXAAPLPERP"], os.path.join(d, "out"), expect_manifest_sha=None); c = L["counts"]
    assert L["candles"] == 2 and L["prints"] == 2 and c["duplicate candle (first kept)"] == 1 and c["candle at or after the cut"] == 1 and c["candle before the name's start"] == 2 and c["candle rows of other tickers (dropped)"] == 1 and c["candle with a missing bid or ask (NULL)"] == 1, L
    assert c["funding before 3 days ahead of the start"] == 1 and c["funding at or after the cut"] == 1 and c["funding rows of other tickers (dropped)"] == 1 and c["all-history refused"] == 1, L
    open(os.path.join(d, "kalshi1m", "a.csv.gz"), "ab").write(b"x")
    try: build(man, d, ["KXAAPLPERP"], os.path.join(d, "out2"), expect_manifest_sha=None); raise AssertionError("a changed file must refuse")
    except SystemExit: pass
    assert iso("2026-11-06T16:00:00Z") == calendar.timegm((2026, 11, 6, 16, 0, 0)) and iso("2026-11-06T16:00:00.000Z") == calendar.timegm((2026, 11, 6, 16, 0, 0)) and ets("1794268800") == 1794268800
    for bad in ("1794268800", "2026-11-06 16:00:00", "2026-11-06T16:00:00+00:00", ""):
        try: iso(bad); raise AssertionError("a funding_time that is not ISO Z must refuse")
        except SystemExit: pass
    for bad in ("1794268800.0", "x", ""):
        try: ets(bad); raise AssertionError("a non integer end_period_ts must refuse")
        except SystemExit: pass
    open(os.path.join(d, "A.md"), "w").write("no line\n")
    try: build(man, d, ["KXAAPLPERP"], os.path.join(d, "out3"), expect_manifest_sha=None, allow_file=os.path.join(d, "A.md")); raise AssertionError("no allow line must refuse")
    except SystemExit: pass
    try: build(man, d, ["KXAAPLPERP"], os.path.join(d, "out4"), expect_manifest_sha=MANIFEST_SHA); raise AssertionError("a different wall must refuse")
    except SystemExit: pass
    assert hashlib.sha256(json.dumps(sorted(WALL94)).encode()).hexdigest() == WALL94_SHA and len(WALL94) == 94
    print("lane4 extract selftest ok", c)
def main(a):
    if a[0] == "--selftest": return selftest()
    print(json.dumps(build(a[0], a[1], WALL94, a[2], allow_file=ALLOW_FILE), indent=1, sort_keys=True))
if __name__ == "__main__": main(sys.argv[1:])
