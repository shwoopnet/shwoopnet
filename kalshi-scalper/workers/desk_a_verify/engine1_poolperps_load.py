"""ENGPERPS_POOL1 loader (Desk A, Nov 16 2026): opens ONLY the two Forensics stock-perp extracts named below (candles and funding, tag 20261116), through a ticker wall already applied by Forensics (94 Equities-class perps; 36 have no quotes).
REFUSES unless HELDOUT_PULL_RUNS.md carries a line with the mark "readable ONLY by Desk A's pooled stock perps loader", "engine1_poolperps_load.py", this file's own sha256 and the sha256 of BOTH extracts (no flag, no env var). Extract hashes are checked before opening.
Reads candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi) -> {ticker: {end_ts: (bid, ask)}} (only bid and ask closes, as the pooled engine uses nothing else) and funding(ticker, ts, rate) -> {ticker: {ts: rate}}. A name enters the pool only with at least MIN_DAYS ET trading days of at least MIN_RTH candles between 09:31 and 16:00 ET and at least 2 funding prints; the others are listed and counted.
  python3 -I engine1_poolperps_load.py <dir holding the two .sqlite.xz extracts>"""
import os, sys, json, lzma, hashlib, sqlite3, tempfile, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import engine1_poolperps as W
CANDLES = ("ENGINE1_stockperps_20261116_extract.sqlite.xz", "b4073e4e0464246218ad3bca4e970d5bec95f5bbfd5380a154f9da630a8b2e15")
FUNDING = ("ENGINE1_stockperps_funding_20261116_extract.sqlite.xz", "e98273017794fcb017e4738f7b1df5627ee1b5c03becf59d23218c800f423e98")
MIN_DAYS, MIN_RTH = 5, 60
START_TS, END_TS = 1793903940, 1794873600     # 2026-11-05T18:39:00Z and 2026-11-17T00:00:00Z (date -u checked): rows outside are dropped and counted BEFORE any dict is built
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md"); ALLOW_MARK = "readable ONLY by Desk A's pooled stock perps loader"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def refuse_unless_allowed():
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "engine1_poolperps_load.py" in line and self_sha() in line and CANDLES[1] in line and FUNDING[1] in line: return
    raise SystemExit("REFUSED: no allow-list line names engine1_poolperps_load.py with this file's sha256 %s and both extract sha256 values (the Head's written acceptance, merged by Main)" % self_sha())
def open_extract(base, spec):
    name, want = spec; raw = open(os.path.join(base, name), "rb").read()
    if hashlib.sha256(raw).hexdigest() != want: raise SystemExit("REFUSED: %s does not have the sha256 named in this loader" % name)
    d = tempfile.mkdtemp(); db = os.path.join(d, "x.sqlite"); open(db, "wb").write(lzma.decompress(raw))
    return sqlite3.connect("file:%s?mode=ro" % db, uri=True)
def load(base, check_allow=True):
    if check_allow: refuse_unless_allowed()
    c = collections.Counter(); cand = collections.defaultdict(dict)
    con = open_extract(base, CANDLES)
    for tk, end, bid, ask in con.execute("SELECT ticker, end_ts, yes_bid, yes_ask FROM candle ORDER BY ticker, end_ts"):
        if not isinstance(end, int) or end < START_TS or end >= END_TS: c["candle outside the window (dropped)"] += 1; continue
        if bid is None or ask is None: c["candle without bid or ask"] += 1; continue
        cand[tk][int(end)] = (float(bid), float(ask))
    fund = collections.defaultdict(dict); con2 = open_extract(base, FUNDING)
    for tk, ts, rate in con2.execute("SELECT ticker, ts, rate FROM funding ORDER BY ticker, ts"):
        if not isinstance(ts, int) or ts < START_TS or ts >= END_TS: c["print outside the window (dropped)"] += 1; continue
        if rate is None: c["print without a rate"] += 1; continue
        fund[tk][int(ts)] = float(rate)
    keep, drop = {}, {}
    for tk, by in cand.items():
        days = collections.Counter(W.et_date(t) for t in by if 9 * 3600 + 31 * 60 <= W.sod(t) <= 16 * 3600 and W.usable(by[t]))
        nd = sum(1 for v in days.values() if v >= MIN_RTH)
        if nd < MIN_DAYS: drop[tk] = "fewer than %d trading days (%d)" % (MIN_DAYS, nd)
        elif len(fund.get(tk, {})) < 2: drop[tk] = "fewer than 2 funding prints"
        else: keep[tk] = by
    c["names kept"] = len(keep); c["names dropped"] = len(drop)
    return keep, {tk: fund.get(tk, {}) for tk in keep}, dict(c), drop
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    k, f, c, d = load(sys.argv[1]); print(json.dumps({"counts": c, "dropped": d, "loader_sha256": self_sha()}, indent=1))
