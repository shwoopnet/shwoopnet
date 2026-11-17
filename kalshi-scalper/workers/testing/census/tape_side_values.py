#!/usr/bin/env python3
"""Counts-only census of the taker_side column of the perps trade tape (Auditor B, Nov 17, 2026; the Head's condition on amendment 6). NOT a builder: no price, count, time-of-trade or bar is read.
  python3 -I tape_side_values.py <root with tape/YYYY-MM-DD.csv.gz> <ticker list file> <from> <to> <allow file> <holds file> <holds sha256>
Reads, per row, ONLY the ticker column (first; a row of another ticker is counted and nothing else of it is read) and the taker_side column of the wall tickers. Prints: the row counts of the exact words "bid" and "ask", and for every OTHER value only the number of distinct values, their total rows and at most 12 of them cut to 16 characters (truncated flag), per ticker and in all, the number of files and rows read, and the manifest sha256.
REFUSES unless: the range lies wholly in DEVELOPMENT (2026-09-18 to 2026-10-27); the holds file matches the pinned sha256 (a wall ticker-day inside an OPEN or FROZEN hold, or at or after forward_default_deny_from, is counted and not read); and ONE allow line carries the mark "readable ONLY by Auditor B's taker_side census", this file's sha256, the manifest sha256 (repr of the sorted (relpath, sha256) tuples of the in-range files, hashed BEFORE any file is opened for reading values), the holds sha256, the sha256 of the ticker list file and the range."""
import collections, csv, fnmatch, glob, gzip, hashlib, json, os, re, sys, time, calendar
DEV = ("2026-09-18", "2026-10-27"); MARK = "readable ONLY by Auditor B's taker_side census"
def sha(b): return hashlib.sha256(b).hexdigest()
def load_holds(path, pinned):
    raw = open(path, "rb").read()
    if sha(raw) != pinned: raise SystemExit("REFUSED: the holds file does not match the pinned sha256")
    d = json.loads(raw); deny = d["forward_default_deny_from"]; rows = [r for r in d["rows"] if r["status"] in ("OPEN", "FROZEN") and "scope" not in r and r.get("kind") != "clearance"]
    def held(tk, t):
        return t >= deny or any(r["from"] <= t and (r["to"] is None or t < r["to"]) and any(fnmatch.fnmatchcase(tk, p) for p in r["tickers"]) for r in rows)
    return held
def day_ts(d): return calendar.timegm(time.strptime(d, "%Y-%m-%d"))
def run(root, tickers_file, d_from, d_to, allow, holds_path, holds_sha):
    for x in (d_from, d_to):
        if not re.fullmatch(r"\d{4}-\d\d-\d\d", x): raise SystemExit("REFUSED: bad date %r" % x)
    if not (DEV[0] <= d_from <= d_to <= DEV[1]): raise SystemExit("REFUSED: the range is not wholly inside development %s to %s" % DEV)
    traw = open(tickers_file, "rb").read(); tsha = sha(traw); wall = {l.strip() for l in traw.decode().splitlines() if l.strip()}; held = load_holds(holds_path, holds_sha)
    paths = sorted(p for p in glob.glob(os.path.join(root, "tape", "*.csv.gz")) if re.fullmatch(r"\d{4}-\d\d-\d\d\.csv\.gz", os.path.basename(p)) and d_from <= os.path.basename(p)[:10] <= d_to)
    man = sorted((os.path.relpath(p, root), sha(open(p, "rb").read())) for p in paths); msha = sha(repr(man).encode()); me = sha(open(os.path.abspath(__file__), "rb").read())
    line = [l for l in open(allow, encoding="utf-8").read().splitlines() if MARK in l]
    if not line or "tape_side_values.py" not in line[0]: raise SystemExit("REFUSED: no allow line for tape_side_values.py")
    for what, v in (("this file's sha256", me), ("the manifest sha256", msha), ("the holds sha256", holds_sha), ("the ticker list sha256", tsha), ("the range start", d_from), ("the range end", d_to)):
        if v not in line[0]: raise SystemExit("REFUSED: the allow line does not name %s %s" % (what, v))
    per = collections.defaultdict(collections.Counter); other = 0; held_n = 0; rows = 0
    for p in paths:
        fday = os.path.basename(p)[:10]
        with gzip.open(p, "rt", newline="") as fh:
            r = csv.reader(fh); h = next(r); it, isd = h.index("ticker"), h.index("taker_side")
            for row in r:
                tk = row[it]
                if tk not in wall: other += 1; continue
                if held(tk, day_ts(fday)): held_n += 1; continue
                per[tk][row[isd]] += 1; rows += 1
    allc = collections.Counter()
    for c in per.values(): allc.update(c)
    def show(c):
        oth = sorted((k, v) for k, v in c.items() if k not in ("bid", "ask"))
        return {"bid": c.get("bid", 0), "ask": c.get("ask", 0), "other_distinct": len(oth), "other_rows": sum(v for _, v in oth),
                "other_first_12_cut_16": [[repr(k[:16]), v] for k, v in oth[:12]], "other_truncated": len(oth) > 12 or any(len(k) > 16 for k, _ in oth)}
    out = {"files": len(paths), "manifest_sha256": msha, "ticker_list_sha256": tsha, "wall_rows_read": rows, "rows_other_tickers_not_read": other, "rows_held_not_read": held_n, "all": show(allc), "per_ticker": {tk: show(c) for tk, c in sorted(per.items())}, "only_bid_and_ask": set(allc) <= {"bid", "ask"}}
    return json.dumps(out, sort_keys=True)
if __name__ == "__main__":
    if len(sys.argv) != 8: sys.exit(__doc__)
    text = run(*sys.argv[1:]); print(text); sys.stderr.write("print sha256 %s\n" % sha(text.encode()))
