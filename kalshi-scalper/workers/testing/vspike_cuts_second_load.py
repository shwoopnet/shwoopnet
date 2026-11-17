#!/usr/bin/env python3
"""V3 vspike cuts reader, second build (Testing Desk, Nov 17, 2026). Offline. REFUSES unless the allow-list file carries a line containing ALLOW_MARK that names this file's sha256 AND the xz sha256 of the archive extract. Reads only market(ticker, close_ts, result, series) and candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi) of ENGINE1_archive_extract.sqlite.xz. The series wall (the 19 series with a LAST_SEARCH entry) is compared on the market row's series FIRST; a market is read further only if its close_ts is an integer below 1791043200 AND its UTC close date is on or before its series' LAST_SEARCH date (the VALIDATE half is counted and never read) AND its result is yes or no; candles of a read market with end_ts after close_ts are dropped. Counts only are printed."""
import collections, hashlib, lzma, os, shutil, sqlite3, sys, tempfile
import vspike_cuts_second as V
HERE = os.path.dirname(os.path.abspath(__file__))
XZ = "ENGINE1_archive_extract.sqlite.xz"; XZ_SHA = "9e4bece477ee5c5caec5b024b1cb86c1b6538061a2bb2092faa1e091bef06820"
CUT = 1791043200
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the Testing Desk's vspike cuts second reader"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()

def refuse_unless_allowed(allow_file=None, xz_sha=None):
    try: text = open(allow_file or ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow-list file cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    if not line or "vspike_cuts_second_load.py" not in line[0] or self_sha() not in line[0]: raise SystemExit("REFUSED: no allow-list line naming vspike_cuts_second_load.py with sha256 %s" % self_sha())
    if (xz_sha or XZ_SHA) not in line[0]: raise SystemExit("REFUSED: the allow-list line does not name the xz sha256")

def load(directory, allow_file=None, xz_sha=None):
    """-> (markets [(ticker, close_ts, series)], candles {ticker: {end_ts: row}}, counts)"""
    sha = xz_sha or XZ_SHA; refuse_unless_allowed(allow_file, sha); c = collections.Counter(); tmp = tempfile.mkdtemp()
    try:
        raw = open(os.path.join(directory, XZ), "rb").read()
        if hashlib.sha256(raw).hexdigest() != sha: raise SystemExit("REFUSED: the extract does not match the allowed xz sha256")
        path = os.path.join(tmp, "x.sqlite"); open(path, "wb").write(lzma.decompress(raw)); db = sqlite3.connect(path); db.text_factory = str
        markets = []
        for tk, close_ts, result, series in db.execute("select ticker, close_ts, result, series from market"):
            if V.short(series) not in V.LAST_SEARCH: c["market outside the series wall (not read further)"] += 1; continue
            if not isinstance(close_ts, int) or close_ts >= CUT: c["market with a non-integer close_ts or at or after the cut (dropped)"] += 1; continue
            if not V.is_search(series, close_ts): c["market in the VALIDATE half (not read further)"] += 1; continue
            if result not in ("yes", "no"): c["SEARCH market without a yes or no result (dropped)"] += 1; continue
            markets.append((tk, close_ts, series))
        want = {tk: cl for tk, cl, _s in markets}; candles = {tk: {} for tk in want}
        for row in db.execute("select ticker, end_ts, yes_bid, yes_ask, last, volume, oi from candle"):
            if row[0] not in want: c["candle row of a market not read (not parsed)"] += 1; continue
            if row[1] is None or row[1] > want[row[0]]: c["candle after the close (dropped)"] += 1; continue
            candles[row[0]][row[1]] = (row[1], row[2], row[3], row[4], row[5], row[6])
        db.close()
    finally: shutil.rmtree(tmp, ignore_errors=True)
    c["markets read"] = len(markets); return markets, candles, dict(c)
