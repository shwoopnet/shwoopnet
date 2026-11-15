"""ENGINE1 extract loader (Desk A, Nov 15 2026), written to Auditor B's Line B. Offline; opens ONLY the two Forensics extracts named by sha256 below.
REFUSES unless HELDOUT_PULL_RUNS.md carries a line with the mark, "engine1_extract_load.py", this file's own sha256 and all three extract sha256 values (no flag, no env var). A file whose sha256 differs from the constant is refused.
Archive: market rows read as ticker and close_ts first; rows at or after CUT dropped and counted before any other column; then result only for kept rows; then candles of kept tickers only, candles ending after the market's close dropped and counted.
Perps: ticker first; every ticker not in PERPS dropped and counted before any other column; candles from PERP_FROM only (UTC 2026-11-06). No close_ts or result is read for a perp.
  python3 -I engine1_extract_load.py <dir holding the two .sqlite.xz files>   prints the drop counts and per-series counts."""
import os, sys, json, lzma, hashlib, sqlite3, tempfile, collections
HERE = os.path.dirname(os.path.abspath(__file__))
CUT = 1791043200                                   # 2026-10-03T16:00Z (the archive extract itself stops at 2026-10-03T00:00Z)
PERP_FROM = 1793923200                             # 2026-11-06T00:00Z (date -u -d checked)
PERPS = ("KXSPYPERP", "KXQQQPERP", "KXNVDAPERP", "KXAAPLPERP")
ARCHIVE = ("ENGINE1_archive_extract.sqlite.xz", "9e4bece477ee5c5caec5b024b1cb86c1b6538061a2bb2092faa1e091bef06820")
PERPFILE = ("ENGINE1_perps_extract.sqlite.xz", "730fa9385bc04e4225cba35c197bff200d49b0ecd6a2830c92978f653c03c398")
NC15FILE = ("ENGINE1_nc15_extract.sqlite.xz", "")   # sha256 OPEN until Forensics runs the NC15 extract once after Line A; an empty value refuses the loader. Freeze this file only after it is filled.
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by Desk A's ENGINE1 extract loader"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def refuse_unless_allowed():
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    if not line or "engine1_extract_load.py" not in line[0] or self_sha() not in line[0] or not NC15FILE[1] or ARCHIVE[1] not in line[0] or PERPFILE[1] not in line[0] or NC15FILE[1] not in line[0]:
        raise SystemExit("REFUSED: no allow-list line names engine1_extract_load.py with this file's sha256 %s and all three extract sha256 values (the Head's written acceptance, merged by Main)" % self_sha())
def open_extract(base, spec):
    name, want = spec; path = os.path.join(base, name)
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != want: raise SystemExit("REFUSED: %s does not have the sha256 named in this loader" % name)
    d = tempfile.mkdtemp(); db = os.path.join(d, "x.sqlite"); open(db, "wb").write(lzma.decompress(raw))
    return sqlite3.connect("file:%s?mode=ro" % db, uri=True)
def load_archive(base, spec=None):
    con = open_extract(base, spec or ARCHIVE); c = collections.Counter(); kept = {}
    for tk, cl in con.execute("SELECT ticker, close_ts FROM market"):              # (1) ticker and close_ts only
        if not isinstance(cl, int): c["no close_ts"] += 1; continue
        if cl >= CUT: c["dropped by the cut"] += 1; continue
        kept[tk] = cl
    res = {}
    for tk in kept:                                                                # (2) result only for kept rows
        r, s = con.execute("SELECT result, series FROM market WHERE ticker = ?", (tk,)).fetchone()
        if r in ("yes", "no"): res[tk] = (r, s)
        else: c["no result (dropped)"] += 1; c["no result (dropped): " + str(s)] += 1
    out = collections.defaultdict(list)
    for tk, (r, s) in res.items():                                                 # (3) candles of kept tickers only
        cl = kept[tk]; cands = []
        for row in con.execute("SELECT end_ts, yes_bid, yes_ask, last, volume, oi FROM candle WHERE ticker = ? ORDER BY end_ts", (tk,)):
            if row[0] > cl: c["candle after close (dropped)"] += 1; continue
            cands.append(tuple(row))
        out[s].append({"series": s, "ticker": tk, "close": cl, "result": r, "candles": cands})
    return dict(out), dict(c)
def load_perps(base):
    con = open_extract(base, PERPFILE); c = collections.Counter(); out = {}
    for (tk,) in con.execute("SELECT ticker FROM market"):                         # ticker first
        if tk not in PERPS: c["other ticker dropped"] += 1; continue
        out[tk] = []
    for tk in out:
        for row in con.execute("SELECT end_ts, yes_bid, yes_ask, last, volume, oi FROM candle WHERE ticker = ? ORDER BY end_ts", (tk,)):
            if row[0] < PERP_FROM: c["perp candle before 2026-11-06 (dropped)"] += 1; continue
            out[tk].append(tuple(row))
    return out, dict(c)
def load(base):
    refuse_unless_allowed()
    a, ca = load_archive(base); p, cp = load_perps(base); n, cn = load_archive(base, NC15FILE)
    return a, ca, p, cp, n, cn
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    a, ca, p, cp, n, cn = load(sys.argv[1])
    print(json.dumps({"nc15_dropped": cn, "nc15_windows": {k: len(v) for k, v in n.items()}, "archive_dropped": ca, "archive_windows": {s: len(v) for s, v in a.items()}, "perps_dropped": cp, "perp_candles": {k: len(v) for k, v in p.items()}, "loader_sha256": self_sha()}, indent=1))
