#!/usr/bin/env python3
"""Reader of Forensics' 15-name stock perps extract for the Testing Desk's second engine build (Nov 16, 2026). Offline. REFUSES unless the allow-list file carries a line for this reader naming this
file's own sha256 AND the two extracts' xz sha256 (no flag, no env var). The wall is exactly the 15 names below: each row's ticker is compared with the wall before any other column is used.
Reads only candle(ticker, end_ts, yes_bid, yes_ask) and funding(ticker, ts, rate); the other columns (last, volume, oi) are never touched. Nothing before 2026-11-06T00:00Z is read.
Splits (the engine's rule, Desk A's engine1_split.py): per ticker the distinct UTC dates of its candle end_ts, D of them; SEARCH = the first floor(D/2) dates; B = the first candle second of the next UTC date.
  python3 -I perps15_second_load.py <dir with the two .xz extracts>     prints counts, D and the last SEARCH date per ticker."""
import calendar, collections, hashlib, lzma, math, os, shutil, sqlite3, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
WALL = ("KXSPCXPERP", "KXMUPERP", "KXTSLAPERP", "KXINTCPERP", "KXAMATPERP", "KXSNDKPERP", "KXQCOMPERP", "KXMETAPERP", "KXAMDPERP", "KXPLTRPERP", "KXAVGOPERP", "KXGOOGLPERP", "KXORCLPERP", "KXMSFTPERP", "KXAMZNPERP")
FIRST_TS = 1793923200          # 2026-11-06T00:00Z
CANDLE_XZ, FUNDING_XZ = "ENGINE1_perps15_20261116_extract.sqlite.xz", "ENGINE1_perps15_funding_20261116_extract.sqlite.xz"
XZ_SHA = {CANDLE_XZ: "8d74c14b3f921a40fb8b577d9bb18025e17a90e94035170eede4da25f1f9936f", FUNDING_XZ: "f2efbf194cf465b24c56ef157cd0fac28cfce08d7a504ac397c94f5cf52236d3"}
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the Testing Desk's perps15 second-build reader"


def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


def refuse_unless_allowed(allow_file=None, xz_sha=None):
    try: text = open(allow_file or ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow-list file cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    if not line or "perps15_second_load.py" not in line[0] or self_sha() not in line[0]: raise SystemExit("REFUSED: no allow-list line naming perps15_second_load.py with this file's sha256 %s" % self_sha())
    for f, h in (xz_sha or XZ_SHA).items():
        if h not in line[0]: raise SystemExit("REFUSED: the allow-list line does not name the xz sha256 of %s" % f)


def unxz(path, expect, tmp):
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != expect: raise SystemExit("REFUSED: %s does not match the allowed xz sha256" % os.path.basename(path))
    out = os.path.join(tmp, os.path.basename(path)[:-3]); open(out, "wb").write(lzma.decompress(raw)); return out


def day(ts): return ts // 86400


def load(directory, allow_file=None, xz_sha=None, wall=WALL):
    sha = xz_sha or XZ_SHA; refuse_unless_allowed(allow_file, sha)
    tmp = tempfile.mkdtemp(); c = collections.Counter(); series = {n: {} for n in wall}; funding = {n: {} for n in wall}
    try:
        cdb = sqlite3.connect(unxz(os.path.join(directory, CANDLE_XZ), sha[CANDLE_XZ], tmp)); cdb.text_factory = str
        for row in cdb.execute("select * from candle"):
            tk = row[0]
            if tk not in series: c["candle row outside the wall (not parsed)"] += 1; continue
            e, b, a = row[1], row[2], row[3]
            if e is None or e < FIRST_TS: c["candle before 2026-11-06 (dropped)"] += 1; continue
            if e in series[tk] and series[tk][e] != (b, a): c["duplicate candle differs (first kept)"] += 1
            series[tk].setdefault(int(e), (b, a))
        cdb.close()
        fdb = sqlite3.connect(unxz(os.path.join(directory, FUNDING_XZ), sha[FUNDING_XZ], tmp))
        for row in fdb.execute("select * from funding"):
            tk = row[0]
            if tk not in funding: c["funding row outside the wall (not parsed)"] += 1; continue
            if row[1] is None or row[1] < FIRST_TS or row[1] % 86400 != 21 * 3600: c["funding row not a 21:00Z print or before the start (dropped)"] += 1; continue
            funding[tk][day(row[1])] = float(row[2])
        fdb.close()
    finally: shutil.rmtree(tmp, ignore_errors=True)
    return series, funding, dict(c)


def splits(series):
    """per ticker: (D, last SEARCH UTC day number, B the first second of the next day) by the engine's rule"""
    out = {}
    for n, s in series.items():
        ds = sorted(set(day(e) for e in s)); D = len(ds)
        if D < 2: continue
        last = ds[D // 2 - 1]; out[n] = (D, last, (last + 1) * 86400)
    return out


def iso_day(d): return time.strftime("%Y-%m-%d", time.gmtime(d * 86400))


if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    s, f, c = load(sys.argv[1]); sp = splits(s)
    print({"counts": c, "candles": {n: len(v) for n, v in s.items()}, "funding_prints": {n: len(v) for n, v in f.items()}, "splits": {n: (D, iso_day(l)) for n, (D, l, b) in sp.items()}, "loader_sha256": self_sha()})
