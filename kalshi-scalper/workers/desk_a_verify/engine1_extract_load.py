"""ENGINE1 extract loader (Desk A, Nov 15 2026), written to Auditor B's Line B. Offline; opens ONLY the two Forensics extracts named by sha256 below.
REFUSES unless HELDOUT_PULL_RUNS.md carries a line with the mark, "engine1_extract_load.py", this file's own sha256 and the sha256 of every extract it opens (archive and perps; NC15 too in the NC15 pass) (no flag, no env var). A file whose sha256 differs from the constant is refused.
Archive: market rows read as ticker and close_ts first; rows at or after CUT dropped and counted before any other column; then result only for kept rows; then candles of kept tickers only, candles ending after the market's close dropped and counted.
Perps: ticker first; every ticker not in PERPS dropped and counted before any other column; candles from PERP_FROM only (UTC 2026-11-06). No close_ts or result is read for a perp.
  python3 -I engine1_extract_load.py <dir holding the two .sqlite.xz files>   prints the drop counts and per-series counts."""
import os, sys, json, lzma, hashlib, sqlite3, tempfile, collections
HERE = os.path.dirname(os.path.abspath(__file__))
CUT = 1791043200                                   # 2026-10-03T16:00Z (the archive extract itself stops at 2026-10-03T00:00Z)
PERP_FROM = 1793923200                             # 2026-11-06T00:00Z (date -u -d checked)
PERPS = ("KXSPYPERP", "KXQQQPERP", "KXNVDAPERP", "KXAAPLPERP")
PERPS_EXT = ("KXUS500PERP", "KXUSTECH100PERP")                  # EVM4 closed and released by the owner 2026-11-16; gold has no 1 minute candles, KXWTIFUTURE is not requested
FUNDING_TICKERS = PERPS_EXT + ("KXSPYPERP", "KXQQQPERP")
ARCHIVE = ("ENGINE1_archive_extract.sqlite.xz", "9e4bece477ee5c5caec5b024b1cb86c1b6538061a2bb2092faa1e091bef06820")
PERPFILE = ("ENGINE1_perps_extract.sqlite.xz", "730fa9385bc04e4225cba35c197bff200d49b0ecd6a2830c92978f653c03c398")
PERPEXT = ("ENGINE1_perps_ext_extract.sqlite.xz", "97d72ea6edc50af22fdf5497fcaa96992596b06c7950738043706957c243293a")        # Forensics db8f7451
FUNDING = ("ENGINE1_funding_extract.sqlite.xz", "bb07226f85745223053e3eb0686bd10185ff54f945ad66d900580e1849524a9b")         # Forensics 264cb785: funding(ticker, ts, rate)
NC15FILE = ("ENGINE1_nc15_extract.sqlite.xz", "ada858e596bf8d373fe2ac227cb1450cd6b31ca46a1f5f8804f1d4ba782552f8")   # Forensics' NC15 extract, commit 49bc3031 (Auditor B hashed the committed file); an empty value refuses the NC15 pass
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by Desk A's ENGINE1 extract loader"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def refuse_unless_allowed(with_nc15=False, pass2=False):
    """ANY line carrying the mark, the file name, this file's own sha256 and the sha256 of every extract that pass opens is enough (Auditor B: the first-pass line B1 and the later NC15 line B2 may both be present)."""
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    need = ([PERPFILE[1], PERPEXT[1], FUNDING[1]] if pass2 else [ARCHIVE[1], PERPFILE[1]]) + ([NC15FILE[1]] if with_nc15 else [])
    for line in text.splitlines():
        if ALLOW_MARK in line and "engine1_extract_load.py" in line and self_sha() in line and all(x and x in line for x in need): return
    raise SystemExit("REFUSED: no allow-list line names engine1_extract_load.py with this file's sha256 %s and the sha256 of every extract this pass opens (the Head's written acceptance, merged by Main)" % self_sha())
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
def load_perps(base, spec=None, tickers=None):
    con = open_extract(base, spec or PERPFILE); c = collections.Counter(); out = {}; tickers = tickers or PERPS
    for (tk,) in con.execute("SELECT ticker FROM market"):                         # ticker first
        if tk not in tickers: c["other ticker dropped"] += 1; continue
        out[tk] = []
    for tk in out:
        for row in con.execute("SELECT end_ts, yes_bid, yes_ask, last, volume, oi FROM candle WHERE ticker = ? ORDER BY end_ts", (tk,)):
            if row[0] < PERP_FROM: c["perp candle before 2026-11-06 (dropped)"] += 1; continue
            out[tk].append(tuple(row))
    return out, dict(c)
def load_funding(base):
    """funding(ticker, ts, rate): ticker first, every ticker outside FUNDING_TICKERS dropped and counted before any other column; prints before 2026-11-06T00:00Z dropped and counted. -> ({ticker: {ts: rate}}, counts). The sign convention is NOT in the file (Kalshi's help article for single stock perps says a positive rate is paid by longs: index perps assumed alike, unconfirmed)."""
    con = open_extract(base, FUNDING); c = collections.Counter(); out = {}
    for (tk,) in con.execute("SELECT DISTINCT ticker FROM funding"):
        if tk not in FUNDING_TICKERS: c["other ticker dropped"] += 1; continue
        out[tk] = {}
    for tk in out:
        for ts, rate in con.execute("SELECT ts, rate FROM funding WHERE ticker = ?", (tk,)):
            if ts < PERP_FROM: c["print before 2026-11-06 (dropped)"] += 1; continue
            if rate is None: c["print without a rate (dropped)"] += 1; continue
            out[tk][int(ts)] = float(rate)
    return out, dict(c)
def load_pass2(base):
    """Perps pass 2 (the Head, Nov 16): SPY and QQQ from the first perps extract, US 500 and US Tech 100 from the extension extract, funding for all four; the archive extract is NOT opened. -> (perps {ticker: candles}, drops, funding {ticker: {ts: rate}}, funding drops)."""
    refuse_unless_allowed(pass2=True)
    p, cp = load_perps(base, PERPFILE, ("KXSPYPERP", "KXQQQPERP")); e, ce = load_perps(base, PERPEXT, PERPS_EXT); f, cf = load_funding(base)
    p.update(e); return p, {"perps": cp, "ext": ce}, f, cf
def load(base, with_nc15=False):
    """First pass: archive and perps only (the Head, Nov 16). The NC15 pass is a second call with with_nc15=True, needs the NC15 sha filled in and named in the allow line."""
    refuse_unless_allowed(with_nc15)
    a, ca = load_archive(base); p, cp = load_perps(base); n, cn = ({}, {})
    if with_nc15: n, cn = load_archive(base, NC15FILE)
    return a, ca, p, cp, n, cn
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    a, ca, p, cp, n, cn = load(sys.argv[1], with_nc15=False)
    print(json.dumps({"nc15_dropped": cn, "nc15_windows": {k: len(v) for k, v in n.items()}, "archive_dropped": ca, "archive_windows": {s: len(v) for s, v in a.items()}, "perps_dropped": cp, "perp_candles": {k: len(v) for k, v in p.items()}, "loader_sha256": self_sha()}, indent=1))
