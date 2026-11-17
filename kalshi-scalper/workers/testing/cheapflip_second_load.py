#!/usr/bin/env python3
"""CHEAPFLIP loader, second build (Testing Desk, Nov 17, 2026). REFUSES unless the allow-list file carries a line containing ALLOW_MARK that names this file's sha256. Reads only <base>/<date>/<HHMM>/book.csv.gz and coverage.csv.gz (every folder of the checkout); the series wall (KXHYPE15M, KXBNB15M, KXNATGAS15M) is applied on the `series` column of a book row (and on the ticker prefix of a coverage row) BEFORE any other column is used; rows of other series are counted and never parsed. Markets whose close_time is after 1794787199 are dropped (counted). Columns by name; a missing column raises. close_time: epoch seconds or ISO 8601 (Z).
manifest = sha256 of repr(sorted([(relpath, sha256 hex)])) of every book.csv.gz and coverage.csv.gz found, relpath from the base; its file count is printed."""
import calendar, collections, csv, glob, gzip, hashlib, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the Testing Desk's CHEAPFLIP second reader"
WALL = ("KXHYPE15M", "KXBNB15M", "KXNATGAS15M")
CUT = 1794787199
PX = ["yes_bid_px_%d" % i for i in range(1, 6)]; SZ = ["yes_bid_sz_%d" % i for i in range(1, 6)]; NPX = ["no_bid_px_%d" % i for i in range(1, 6)]; NSZ = ["no_bid_sz_%d" % i for i in range(1, 6)]


def sha_of(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()
def self_sha(): return sha_of(os.path.abspath(__file__))


def refuse_unless_allowed(allow_file=None):
    try: text = open(allow_file or ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow-list file cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    if not line or "cheapflip_second_load.py" not in line[0] or self_sha() not in line[0]: raise SystemExit("REFUSED: no allow-list line naming cheapflip_second_load.py with sha256 %s" % self_sha())


def parse_close(s):
    s = s.strip()
    try: return float(s)
    except ValueError: pass
    s = s.replace("+00:00", "Z")
    if "." in s: s = s.split(".")[0] + "Z"
    return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))


def num(x): return None if x is None or x.strip() == "" else float(x)


def levels(row, idx, p, s): return [(num(row[idx[a]]), num(row[idx[b]])) for a, b in zip(p, s)]


def load(base, allow_file=None):
    """-> (markets {ticker: (series, close, polls)}, results {ticker: str}, counts, manifest dict)"""
    refuse_unless_allowed(allow_file); c = collections.Counter(); man = []; polls = {}; closes = {}; seen = set(); results = {}
    books = sorted(glob.glob(os.path.join(base, "*", "*", "book.csv.gz"))); covs = sorted(glob.glob(os.path.join(base, "*", "*", "coverage.csv.gz")))
    for path in books + covs: man.append((os.path.relpath(path, base), sha_of(path)))
    for path in books:
        with gzip.open(path, "rt", newline="") as fh:
            r = csv.reader(fh); h = next(r, None)
            if h is None: c["empty book file"] += 1; continue
            idx = {n: i for i, n in enumerate(h)}
            for need in ["t_recv_ms", "ticker", "series", "close_time"] + PX + SZ + NPX + NSZ:
                if need not in idx: raise SystemExit("REFUSED: book.csv.gz lacks column %s" % need)
            for row in r:
                if row[idx["series"]] not in WALL: c["book row outside the series wall (not parsed)"] += 1; continue
                tk = row[idx["ticker"]]; cl = parse_close(row[idx["close_time"]])
                if cl > CUT: c["book row of a market closing after the cut (dropped)"] += 1; continue
                key = (tk, row[idx["t_recv_ms"]])
                if key in seen: c["duplicate poll (first kept)"] += 1; continue
                seen.add(key); closes[tk] = (row[idx["series"]], cl)
                polls.setdefault(tk, []).append((int(float(row[idx["t_recv_ms"]])), tk, cl, levels(row, idx, PX, SZ), levels(row, idx, NPX, NSZ)))
    for path in covs:
        with gzip.open(path, "rt", newline="") as fh:
            r = csv.reader(fh); h = next(r, None)
            if h is None: c["empty coverage file"] += 1; continue
            idx = {n: i for i, n in enumerate(h)}
            for need in ("ticker", "close_time", "result"):
                if need not in idx: raise SystemExit("REFUSED: coverage.csv.gz lacks column %s" % need)
            for row in r:
                tk = row[idx["ticker"]]
                if not any(tk.startswith(s + "-") for s in WALL): c["coverage row outside the series wall (not parsed)"] += 1; continue
                if tk in results and results[tk] != row[idx["result"]]: c["conflicting result (first kept)"] += 1; continue
                results.setdefault(tk, row[idx["result"]])
    markets = {tk: (closes[tk][0], closes[tk][1], sorted(ps, key=lambda p: p[0])) for tk, ps in polls.items()}
    c["book files"] = len(books); c["coverage files"] = len(covs)
    return markets, {k: v for k, v in results.items() if k in markets}, dict(c), {"files": len(man), "manifest_sha256": hashlib.sha256(repr(sorted(man)).encode()).hexdigest()}
