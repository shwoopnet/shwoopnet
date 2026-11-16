#!/usr/bin/env python3
"""PERPSCALP2 loader, second build (Testing Desk, Nov 16, 2026). REFUSES unless the allow-list file carries a line containing ALLOW_MARK that names this file's sha256. Reads only <root>/kalshi1m/*.csv.gz and <root>/funding/*.csv.gz; the 14-name wall is applied on the ticker FIRST (other rows are counted, not parsed); candles end through DEV_END (1794787199, 2026-11-15T23:59:59Z) inclusive, later rows counted and dropped. Columns read: ticker, end_period_ts, bid_close, ask_close, volume (candles); ticker, funding_time, funding_rate (funding). A missing column raises. Duplicate key: first file in sorted path order kept, counted. manifest_sha256 = sha256 of repr(sorted([(relpath, file sha256 hex)])) over every file read, relpath like 'kalshi1m/2026-11-10.csv.gz' (Desk C's serialization). Only names matching ^YYYY-MM-DD(.only).csv.gz are read; others are counted as skipped. Rows not usable (0 < bid <= ask) are dropped BEFORE the first-kept duplicate rule."""
import calendar, collections, csv, glob, gzip, hashlib, os, re, sys, time
import perpscalp2_second as P
HERE = os.path.dirname(os.path.abspath(__file__))
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the Testing Desk's PERPSCALP2 second reader"
DEV_END = 1794787199
WALL = frozenset(P.LMAX)
NAME_OK = re.compile(r"^\d{4}-\d\d-\d\d(\.only)?\.csv\.gz$")


def sha_of(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()
def self_sha(): return sha_of(os.path.abspath(__file__))
def iso(t):
    t = t.strip()
    if "." in t: t = t.split(".")[0] + "Z"
    return calendar.timegm(time.strptime(t, "%Y-%m-%dT%H:%M:%SZ"))


def refuse_unless_allowed(allow_file=None):
    try: text = open(allow_file or ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow-list file cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    if not line or "perpscalp2_second_load.py" not in line[0] or self_sha() not in line[0]: raise SystemExit("REFUSED: no allow-list line naming perpscalp2_second_load.py with sha256 %s" % self_sha())


def load(root, allow_file=None):
    """-> (data {name: {end: (bid, ask, vol)}}, funding {name: {ts: rate}}, counts)"""
    refuse_unless_allowed(allow_file); c = collections.Counter(); data = {n: {} for n in WALL}; funding = {n: {} for n in WALL}; man = []
    for sub in ("kalshi1m", "funding"):
        for path in sorted(glob.glob(os.path.join(root, sub, "*"))):
            if not NAME_OK.match(os.path.basename(path)): c["skipped file name " + sub + "/" + os.path.basename(path)] += 1; continue
            rel = os.path.relpath(path, root); man.append((rel, sha_of(path))); c["files_read " + sub] += 1
            with gzip.open(path, "rt", newline="") as fh:
                r = csv.reader(fh); h = next(r, None)
                if h is None: c["empty file"] += 1; continue
                c["headers_seen " + sub + " " + ",".join(h)] += 1
                if sub == "kalshi1m":
                    ti, ei, bi, ai, vi = (h.index(k) for k in ("ticker", "end_period_ts", "bid_close", "ask_close", "volume"))
                    for row in r:
                        tk = row[ti]
                        if tk not in WALL: c["candle row outside the wall (not parsed)"] += 1; continue
                        e = int(row[ei])
                        if e > DEV_END: c["candle after the development end (dropped)"] += 1; continue
                        if row[bi] == "" or row[ai] == "": c["candle without bid or ask (dropped)"] += 1; continue
                        q = (float(row[bi]), float(row[ai]), float(row[vi]) if row[vi] != "" else 0.0)
                        if not P.usable(q): c["candle crossed or non-positive (dropped before the first-kept rule)"] += 1; continue
                        if e in data[tk]:
                            c["candle_duplicate_differs" if data[tk][e] != q else "candle_duplicate_first_kept"] += 1; continue
                        data[tk][e] = q
                else:
                    ti, fi, ri = (h.index(k) for k in ("ticker", "funding_time", "funding_rate"))
                    for row in r:
                        tk = row[ti]
                        if tk not in WALL: c["funding row outside the wall (not parsed)"] += 1; continue
                        c["funding rows read"] += 1
                        if row[ri] == "": c["funding row without a rate (dropped)"] += 1; continue
                        t = iso(row[fi])
                        if t > DEV_END: c["funding row after the development end (dropped)"] += 1; continue
                        if t in funding[tk]:
                            c["print_duplicate_differs" if funding[tk][t] != float(row[ri]) else "print_duplicate_first_kept"] += 1; continue
                        funding[tk][t] = float(row[ri])
    c["manifest_sha256 " + hashlib.sha256(repr(sorted(man)).encode()).hexdigest()] += 1
    return data, funding, dict(c)
