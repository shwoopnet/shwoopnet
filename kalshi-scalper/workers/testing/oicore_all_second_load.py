#!/usr/bin/env python3
"""Reader of Forensics' ENGINE1 archive extract for the Testing Desk's OICORE-every-market second build (Nov 17, 2026). Refuses to read unless the allow-list line in HELDOUT_PULL_RUNS.md names this file's own sha256,
oicore_all_second.py's sha256 AND the archive xz sha256 (no flag, no env var). The wall is the 19 series of Desk A's split constants: each market's series is compared with the wall before any other column is used.
Reads market(ticker, close_ts, result, series) and candle(ticker, end_ts, yes_bid, yes_ask, oi) only. Cuts (Desk A's loader text): closes at or after 2026-10-03T16:00Z (epoch computed in the file) are dropped; candles ending after their market's close are dropped; markets without a yes or no result are dropped; all counted.
Prints counts and the screen's lines (per series and pooled). Run ONCE.   python3 -I oicore_all_second_load.py <archive xz>"""
import collections, datetime, hashlib, lzma, os, sqlite3, sys, tempfile
import oicore_all_second as O

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_SHA = "9e4bece477ee5c5caec5b024b1cb86c1b6538061a2bb2092faa1e091bef06820"      # ENGINE1_archive_extract.sqlite.xz on claude/forensics-desk
CUT_TS = int(datetime.datetime(2026, 10, 3, 16, 0, tzinfo=datetime.timezone.utc).timestamp())
SPLITS = {"BNB": "2026-09-03", "BTC": "2026-09-03", "COPPER": "2026-09-13", "DOGE": "2026-09-03", "ETH": "2026-09-03", "EURUSD": "2026-09-27", "GBPUSD": "2026-09-27", "GOLD": "2026-09-03", "HYPE": "2026-09-03", "NATGAS": "2026-09-14",
          "NEAR": "2026-09-03", "PALLADIUM": "2026-09-24", "PLATINUM": "2026-09-24", "SILVER": "2026-09-03", "SOL": "2026-09-07", "USDJPY": "2026-09-27", "WTI": "2026-09-04", "XRP": "2026-09-03", "ZEC": "2026-09-03"}   # Desk A, Nov 17 18:37Z
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the Testing Desk's OICORE every-market second-build reader"

def sha_of(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()

def refuse_unless_allowed(allow_file=None, arch_sha=ARCHIVE_SHA):
    try: text = open(allow_file or ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow-list file cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    me, scr = sha_of(os.path.abspath(__file__)), sha_of(os.path.join(HERE, "oicore_all_second.py"))
    if not line or "oicore_all_second_load.py" not in line[0] or me not in line[0]: raise SystemExit("REFUSED: no allow-list line naming oicore_all_second_load.py with this file's sha256 %s" % me)
    for what, v in (("oicore_all_second.py sha256", scr), ("the archive xz sha256", arch_sha)):
        if v not in line[0]: raise SystemExit("REFUSED: the allow-list line does not name %s %s" % (what, v))

def series_of(ticker, series):
    s = series if series else ticker
    if s.startswith("KX"): s = s[2:]
    return s[:-3] if s.endswith("15M") else s

def load(xz_path, allow_file=None, arch_sha=ARCHIVE_SHA, splits=SPLITS):
    refuse_unless_allowed(allow_file, arch_sha)
    raw = open(xz_path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != arch_sha: raise SystemExit("REFUSED: the archive does not match the allowed xz sha256")
    tmp = tempfile.mkdtemp(); db = os.path.join(tmp, "a.sqlite"); open(db, "wb").write(lzma.decompress(raw))
    c = sqlite3.connect(db); cnt = collections.Counter(); markets = []; keep = {}
    for tk, close, result, series in c.execute("select ticker, close_ts, result, series from market"):
        s = series_of(tk, series)
        if s not in splits: cnt["outside_wall"] += 1; continue
        if close is None or close >= CUT_TS: cnt["cut_close"] += 1; continue
        if result not in ("yes", "no"): cnt["no_result"] += 1; continue
        markets.append((tk, int(close), result, s)); keep[tk] = int(close)
    candles = {}
    for tk, end, bid, ask, oi in c.execute("select ticker, end_ts, yes_bid, yes_ask, oi from candle"):
        if tk not in keep: continue
        if end > keep[tk]: cnt["candle_after_close"] += 1; continue
        candles[(tk, int(end))] = (bid, ask, oi)
    return markets, candles, {k: datetime.date.fromisoformat(v) for k, v in splits.items()}, cnt

if __name__ == "__main__":
    markets, candles, sp, cnt = load(sys.argv[1])
    print("markets", len(markets), "candles", len(candles), dict(sorted(cnt.items())))
    for l in O.lines(O.run(markets, candles, sp)): print(l)
