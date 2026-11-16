#!/usr/bin/env python3
"""LABELLED CRYPTO FUNDING FILE (Forensics desk, Nov 16, 2026; the Head's order for the History Miner's crypto funding and basis lane). Reads ONLY the per-day funding files already on the perp-data branch (funding/<date>.csv.gz and funding/<date>.only.csv.gz, in sorted path order; funding/all-history.csv.gz is NOT read, its tickers are blank), keeps the 19 crypto perps of the census (ticker wall first: the row is a plain list and its first field is compared before anything else is parsed), nothing at or after 2026-11-17T00:00:00Z.
Every output row: ticker, funding_time_utc (ISO as in the file), funding_time_epoch, funding_rate (as the file holds it, a fraction of notional per print, no sign change), mark_price (as the file holds it), sign_convention ('positive rate = longs pay shorts'), source_file, source_sha256 (sha256 of that source file). Duplicates (same ticker and time) keep the first in sorted path order; a second row that DIFFERS is counted. A funding_time that is not ISO UTC ending in Z refuses.
usage: python3 -I funding_labelled.py <perp-data dir> <out dir>    (self test: --selftest)"""
import sys, os, re, csv, gzip, glob, json, hashlib, calendar, collections, tempfile
CRYPTO = ["KXAAVEPERP", "KXADAPERP", "KXBCHPERP", "KXBNBPERP", "KXBTCPERP", "KXDOGEPERP", "KXETHPERP", "KXHYPEPERP", "KXKSHIBPERP", "KXLINKPERP", "KXLTCPERP", "KXNEARPERP", "KXSOLPERP", "KXSUIPERP", "KXUNIPERP", "KXVVVPERP", "KXWLDPERP", "KXXRPPERP", "KXZECPERP"]
CUT = 1794873600; SIGN = "positive rate = longs pay shorts (help.kalshi.com articles 15357613 and 14679970)"
def sha_of(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def iso(x):
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?Z", x)
    if not m: raise SystemExit("REFUSED: funding_time %r is not an ISO UTC time ending in Z" % x)
    return calendar.timegm(tuple(int(g) for g in m.groups()))
def build(base, out):
    W = set(CRYPTO); files = sorted(glob.glob(os.path.join(base, "funding", "*.csv.gz"))); files = [f for f in files if not f.endswith("all-history.csv.gz")]
    c = collections.Counter(); rows = {}; os.makedirs(out, exist_ok=True)
    for f in files:
        rel = "funding/" + os.path.basename(f); sh = sha_of(f); c["files read"] += 1
        with gzip.open(f, "rt", newline="") as fh:
            rd = csv.reader(fh); hdr = next(rd); it, ir, im = hdr.index("funding_time"), hdr.index("funding_rate"), hdr.index("mark_price") if "mark_price" in hdr else None
            for row in rd:
                t = row[0]
                if t not in W: c["rows of other tickers (dropped)"] += 1; continue
                ts = iso(row[it])
                if ts >= CUT: c["at or after the cut"] += 1; continue
                key = (t, ts); rate = row[ir]; mark = row[im] if im is not None else ""
                if key in rows:
                    c["duplicate (first kept)"] += 1
                    if rows[key][3] != rate: c["duplicate differs"] += 1
                    continue
                rows[key] = (t, row[it], ts, rate, mark, SIGN, rel, sh)
    dst = os.path.join(out, "crypto_funding_labelled.csv")
    with open(dst, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["ticker", "funding_time_utc", "funding_time_epoch", "funding_rate", "mark_price", "sign_convention", "source_file", "source_sha256"])
        for k in sorted(rows): w.writerow(rows[k])
    gz = dst + ".gz"
    with open(dst, "rb") as a, gzip.GzipFile(gz, "wb", mtime=0) as b: b.write(a.read())
    os.remove(dst)
    by = collections.defaultdict(list)
    for (t, ts) in sorted(rows): by[t].append(ts)
    gaps = {t: sorted(collections.Counter(b - a for a, b in zip(v, v[1:])).items(), key=lambda x: -x[1])[:3] for t, v in by.items()}
    L = {"rows": len(rows), "tickers_with_prints": len(by), "first": min(r[2] for r in rows.values()) if rows else None, "last": max(r[2] for r in rows.values()) if rows else None, "counts": dict(c), "prints_per_ticker": {t: len(v) for t, v in sorted(by.items())}, "most_common_gaps_seconds": gaps, "file_sha256": sha_of(gz), "source_files": [os.path.basename(f) for f in files]}
    json.dump(L, open(os.path.join(out, "crypto_funding_labelled_cutlog.json"), "w"), indent=1, sort_keys=True); return L
def selftest():
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "funding"))
    def put(n, rows):
        with gzip.open(os.path.join(d, "funding", n), "wt", newline="") as fh: w = csv.writer(fh); w.writerow(["ticker", "funding_time", "funding_rate", "mark_price"]); w.writerows(rows)
    put("2026-11-01.csv.gz", [["KXBTCPERP", "2026-11-01T00:00:00Z", "0.0001", "100"], ["KXXRPPERP", "2026-11-01T08:00:00.000Z", "-0.0002", "1"], ["KXAAPLPERP", "2026-11-01T00:00:00Z", "0.1", "1"]])
    put("2026-11-01.only.csv.gz", [["KXBTCPERP", "2026-11-01T00:00:00Z", "0.0009", "100"], ["KXBTCPERP", "2026-11-17T00:00:00Z", "0.1", "1"]])
    put("all-history.csv.gz", [["", "2026-11-01T00:00:00Z", "5", "1"]])
    L = build(d, os.path.join(d, "o")); c = L["counts"]
    assert L["rows"] == 2 and c["rows of other tickers (dropped)"] == 1 and c["duplicate (first kept)"] == 1 and c["duplicate differs"] == 1 and c["at or after the cut"] == 1 and c["files read"] == 2
    put("2026-11-02.csv.gz", [["KXBTCPERP", "1793000000", "0", "1"]])
    try: build(d, os.path.join(d, "o2")); raise AssertionError("a non ISO funding_time must refuse")
    except SystemExit: pass
    print("funding_labelled selftest ok")
if __name__ == "__main__":
    if sys.argv[1] == "--selftest": selftest()
    else: print(json.dumps(build(sys.argv[1], sys.argv[2]), indent=1, sort_keys=True))
