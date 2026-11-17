#!/usr/bin/env python3
"""Reader of Forensics' stock perps extract (tag 20261116) for the Testing Desk's lanes 1 and 6 second build (Nov 17, 2026): the 13 basket names only (wall applied on the ticker before any other column), same extracts, window and cut as POOL1; plus page_max(path), which accepts only the pinned table (sha256 in PAGE_MAX_SHA) and returns {ticker: page max} for the wall names whose page_max parses as a number (unknown or blank = absent, no default). Offline. REFUSES unless the allow-list file carries a line for this reader naming
this file's own sha256 AND the two extracts' xz sha256 (no flag, no env var). The wall is exactly the names below (Forensics' cutlog wall): each row's ticker is compared with the wall before any other column is used.
Reads only candle(ticker, end_ts, yes_bid, yes_ask) and funding(ticker, ts, rate); the market table and the columns last, volume and oi are never touched. Nothing before 2026-11-05T18:39:00Z (epoch 1793903940, spec v3.5) and nothing at or after
2026-11-17T00:00Z (epoch 1794873600, the spec's window cut) is read; both are counted. Prints counts only.
  python3 -I lanes16_second_load.py <dir with the two .xz extracts>"""
import collections, hashlib, lzma, os, shutil, sqlite3, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WALL = ("KXAAPLPERP", "KXAMATPERP", "KXAMDPERP", "KXAMZNPERP", "KXAVGOPERP", "KXCOPPERP", "KXCVXPERP", "KXGOOGLPERP", "KXMETAPERP", "KXMSFTPERP", "KXMUPERP", "KXNVDAPERP", "KXXOMPERP")     # the 13 basket names of ENGPERPS_LANES_1_6_SPEC (semis, mega-cap tech, energy); every other ticker is counted, never parsed
PAGE_MAX_SHA = "5be707ecce0cab05f7c5e1103af1ec2915d2b340b27f969853fb22d85888de36"      # PERPS_PAGE_MAX_20261116.tsv at a67ac7f92 on claude/forensics-desk (Forensics v4)
FIRST_TS, CUTOFF = 1793903940, 1794873600          # 2026-11-05T18:39:00Z (spec v3.5 loader wall), 2026-11-17T00:00:00Z
CANDLE_XZ, FUNDING_XZ = "ENGINE1_stockperps_20261116_extract.sqlite.xz", "ENGINE1_stockperps_funding_20261116_extract.sqlite.xz"
XZ_SHA = {CANDLE_XZ: "b4073e4e0464246218ad3bca4e970d5bec95f5bbfd5380a154f9da630a8b2e15", FUNDING_XZ: "e98273017794fcb017e4738f7b1df5627ee1b5c03becf59d23218c800f423e98"}
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the Testing Desk's lanes 1 and 6 second-build reader"


def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


def refuse_unless_allowed(allow_file=None, xz_sha=None):
    try: text = open(allow_file or ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow-list file cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    if not line or "lanes16_second_load.py" not in line[0] or self_sha() not in line[0]: raise SystemExit("REFUSED: no allow-list line naming lanes16_second_load.py with this file's sha256 %s" % self_sha())
    for f, h in (xz_sha or XZ_SHA).items():
        if h not in line[0]: raise SystemExit("REFUSED: the allow-list line does not name the xz sha256 of %s" % f)


def page_max(path):
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != PAGE_MAX_SHA: raise SystemExit("REFUSED: the page max table does not match the pinned sha256")
    out = {}
    for i, l in enumerate(raw.decode("utf-8").splitlines()):
        f = l.split("\t")
        if i == 0 or len(f) < 3 or f[0] not in WALL: continue
        try: v = float(f[2])
        except ValueError: continue
        if v > 0: out[f[0]] = v
    return out


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
            if e is None: c["candle without end_ts (dropped)"] += 1; continue
            if e < FIRST_TS: c["candle before 2026-11-05T18:39Z (dropped)"] += 1; continue
            if e >= CUTOFF: c["candle at or after 2026-11-17 (dropped)"] += 1; continue
            if int(e) in data[tk] and data[tk][int(e)] != (row[2], row[3]): c["duplicate candle differs (first kept)"] += 1
            data[tk].setdefault(int(e), (row[2], row[3]))
        cdb.close()
        fdb = sqlite3.connect(unxz(os.path.join(directory, FUNDING_XZ), sha[FUNDING_XZ], tmp))
        for row in fdb.execute("select ticker, ts, rate from funding"):
            tk = row[0]
            if tk not in ws: c["funding row outside the wall (not parsed)"] += 1; continue
            if row[1] is None or row[1] < FIRST_TS or row[2] is None: c["funding row before 2026-11-05T18:39Z or without a ts or rate (dropped)"] += 1; continue
            if row[1] >= CUTOFF: c["funding row at or after 2026-11-17 (dropped)"] += 1; continue
            funding[tk][int(row[1])] = float(row[2])          # booked from the extract's own print timestamps, whatever the hour
        fdb.close()
    finally: shutil.rmtree(tmp, ignore_errors=True)
    return data, funding, dict(c)


if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    d, f, c = load(sys.argv[1])
    print({"counts": c, "names_with_candles": sum(1 for v in d.values() if v), "candles": sum(len(v) for v in d.values()), "names_with_prints": sum(1 for v in f.values() if v), "prints": sum(len(v) for v in f.values()), "loader_sha256": self_sha()})
