#!/usr/bin/env python3
"""Reader of Forensics' stock perps extract (tag 20261116, 94 listed names) for the Testing Desk's POOL1 second build (Nov 16, 2026). Offline. REFUSES unless the allow-list file carries a line for this reader naming
this file's own sha256 AND the two extracts' xz sha256 (no flag, no env var). The wall is exactly the names below (Forensics' cutlog wall): each row's ticker is compared with the wall before any other column is used.
Reads only candle(ticker, end_ts, yes_bid, yes_ask) and funding(ticker, ts, rate); the market table and the columns last, volume and oi are never touched. Nothing before 2026-11-06T00:00Z and nothing at or after
2026-11-17T00:00Z (epoch 1794873600, the spec's window cut) is read; both are counted. Prints counts only.
  python3 -I pool1_second_load.py <dir with the two .xz extracts>"""
import collections, hashlib, lzma, os, shutil, sqlite3, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WALL = (
        "KXAAPLPERP",
        "KXABBVPERP",
        "KXABTPERP",
        "KXACNPERP",
        "KXADBEPERP",
        "KXADIPERP",
        "KXAMATPERP",
        "KXAMDPERP",
        "KXAMGNPERP",
        "KXAMZNPERP",
        "KXANETPERP",
        "KXAPHPERP",
        "KXARMPERP",
        "KXASMLPERP",
        "KXAVGOPERP",
        "KXAXPPERP",
        "KXBABAPERP",
        "KXBACPERP",
        "KXBAPERP",
        "KXBKNGPERP",
        "KXBLKPERP",
        "KXBRKBPERP",
        "KXCATPERP",
        "KXCOPPERP",
        "KXCOSTPERP",
        "KXCPERP",
        "KXCRMPERP",
        "KXCRWDPERP",
        "KXCSCOPERP",
        "KXCVXPERP",
        "KXDELLPERP",
        "KXDEPERP",
        "KXDHRPERP",
        "KXDISPERP",
        "KXGEPERP",
        "KXGEVPERP",
        "KXGILDPERP",
        "KXGOOGLPERP",
        "KXGSPERP",
        "KXHDPERP",
        "KXIBMPERP",
        "KXINTCPERP",
        "KXISRGPERP",
        "KXJNJPERP",
        "KXJPMPERP",
        "KXKLACPERP",
        "KXKOPERP",
        "KXLINPERP",
        "KXLLYPERP",
        "KXLMTPERP",
        "KXLRCXPERP",
        "KXMAPERP",
        "KXMCDPERP",
        "KXMETAPERP",
        "KXMRKPERP",
        "KXMSFTPERP",
        "KXMSPERP",
        "KXMUPERP",
        "KXNEEPERP",
        "KXNEMPERP",
        "KXNFLXPERP",
        "KXNVDAPERP",
        "KXORCLPERP",
        "KXPANWPERP",
        "KXPEPPERP",
        "KXPFEPERP",
        "KXPGPERP",
        "KXPLDPERP",
        "KXPLTRPERP",
        "KXPMPERP",
        "KXQCOMPERP",
        "KXQQQPERP",
        "KXRTXPERP",
        "KXSBUXPERP",
        "KXSCHWPERP",
        "KXSHOPPERP",
        "KXSKHYPERP",
        "KXSNDKPERP",
        "KXSPCXPERP",
        "KXSPYPERP",
        "KXTJXPERP",
        "KXTMOPERP",
        "KXTMUSPERP",
        "KXTSLAPERP",
        "KXTSMPERP",
        "KXTXNPERP",
        "KXUNHPERP",
        "KXUNPPERP",
        "KXVPERP",
        "KXVZPERP",
        "KXWELLPERP",
        "KXWFCPERP",
        "KXWMTPERP",
        "KXXOMPERP")
FIRST_TS, CUTOFF = 1793923200, 1794873600          # 2026-11-06T00:00Z, 2026-11-17T00:00Z
CANDLE_XZ, FUNDING_XZ = "ENGINE1_stockperps_20261116_extract.sqlite.xz", "ENGINE1_stockperps_funding_20261116_extract.sqlite.xz"
XZ_SHA = {CANDLE_XZ: "b4073e4e0464246218ad3bca4e970d5bec95f5bbfd5380a154f9da630a8b2e15", FUNDING_XZ: "e98273017794fcb017e4738f7b1df5627ee1b5c03becf59d23218c800f423e98"}
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the Testing Desk's POOL1 second-build reader"


def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


def refuse_unless_allowed(allow_file=None, xz_sha=None):
    try: text = open(allow_file or ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow-list file cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    if not line or "pool1_second_load.py" not in line[0] or self_sha() not in line[0]: raise SystemExit("REFUSED: no allow-list line naming pool1_second_load.py with this file's sha256 %s" % self_sha())
    for f, h in (xz_sha or XZ_SHA).items():
        if h not in line[0]: raise SystemExit("REFUSED: the allow-list line does not name the xz sha256 of %s" % f)


def unxz(path, expect, tmp):
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != expect: raise SystemExit("REFUSED: %s does not match the allowed xz sha256" % os.path.basename(path))
    out = os.path.join(tmp, os.path.basename(path)[:-3]); open(out, "wb").write(lzma.decompress(raw)); return out


def load(directory, allow_file=None, xz_sha=None, wall=WALL):
    """-> (data {name: {end_ts: (bid, ask)}}, funding {name: {ts: rate}}, counts)"""
    sha = xz_sha or XZ_SHA; refuse_unless_allowed(allow_file, sha)
    tmp = tempfile.mkdtemp(); c = collections.Counter(); ws = set(wall); data = {n: {} for n in wall}; funding = {n: {} for n in wall}
    try:
        cdb = sqlite3.connect(unxz(os.path.join(directory, CANDLE_XZ), sha[CANDLE_XZ], tmp)); cdb.text_factory = str
        for row in cdb.execute("select ticker, end_ts, yes_bid, yes_ask from candle"):
            tk = row[0]
            if tk not in ws: c["candle row outside the wall (not parsed)"] += 1; continue
            e = row[1]
            if e is None or e < FIRST_TS: c["candle before 2026-11-06 (dropped)"] += 1; continue
            if e >= CUTOFF: c["candle at or after 2026-11-17 (dropped)"] += 1; continue
            if int(e) in data[tk] and data[tk][int(e)] != (row[2], row[3]): c["duplicate candle differs (first kept)"] += 1
            data[tk].setdefault(int(e), (row[2], row[3]))
        cdb.close()
        fdb = sqlite3.connect(unxz(os.path.join(directory, FUNDING_XZ), sha[FUNDING_XZ], tmp))
        for row in fdb.execute("select ticker, ts, rate from funding"):
            tk = row[0]
            if tk not in ws: c["funding row outside the wall (not parsed)"] += 1; continue
            if row[1] is None or row[1] < FIRST_TS or row[2] is None: c["funding row before the start or without a rate (dropped)"] += 1; continue
            if row[1] >= CUTOFF: c["funding row at or after 2026-11-17 (dropped)"] += 1; continue
            funding[tk][int(row[1])] = float(row[2])          # booked from the extract's own print timestamps, whatever the hour
        fdb.close()
    finally: shutil.rmtree(tmp, ignore_errors=True)
    return data, funding, dict(c)


if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    d, f, c = load(sys.argv[1])
    print({"counts": c, "names_with_candles": sum(1 for v in d.values() if v), "candles": sum(len(v) for v in d.values()), "names_with_prints": sum(1 for v in f.values() if v), "prints": sum(len(v) for v in f.values()), "loader_sha256": self_sha()})
