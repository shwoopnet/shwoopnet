#!/usr/bin/env python3
"""PERPSLANE4 loader (Testing Desk, Nov 16, 2026). Offline. REFUSES unless the allow-list file carries a line for this reader naming this file's sha256 AND the sha256 of LANE4_FILES_MANIFEST.txt (the list of the exact files, each with its own sha256, which Forensics reads too). Every file's sha256 is checked
against the manifest before it is opened. The wall is compared with each row's ticker before any other column is used: KXGOLDPERP, KXUS500PERP, KXUSTECH100PERP from 2026-09-10T00:00Z and the 94 stock perps of Forensics' wall from 2026-11-05T18:39:00Z; nothing at or after the cut (default 2026-11-17T00:00:00Z) is read.
Reads candles (ticker, end_period_ts, bid_close, ask_close) and funding (ticker, funding_time, funding_rate); the mark_price and every open, high and low column are never used. Prints counts only (no price, no rate).
  python3 -I lane4_load.py <dir holding kalshi1m/ and funding/> [allow file]"""
import calendar, collections, csv, gzip, hashlib, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
STOCKS = (
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
INDEX3 = ("KXGOLDPERP", "KXUS500PERP", "KXUSTECH100PERP")
START3, START_STOCK, CUT = 1788998400, 1793903940, 1794873600          # 2026-09-10T00:00Z, 2026-11-05T18:39:00Z, 2026-11-17T00:00:00Z
MANIFEST = os.path.join(HERE, "LANE4_FILES_MANIFEST.txt")
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the Testing Desk's PERPSLANE4 reader"


def sha_of(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()
def self_sha(): return sha_of(os.path.abspath(__file__))


def refuse_unless_allowed(allow_file=None, manifest=None):
    try: text = open(allow_file or ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow-list file cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    if not line or "lane4_load.py" not in line[0] or self_sha() not in line[0]: raise SystemExit("REFUSED: no allow-list line naming lane4_load.py with this file's sha256 %s" % self_sha())
    if sha_of(manifest or MANIFEST) not in line[0]: raise SystemExit("REFUSED: the allow-list line does not name the sha256 of the files manifest")


def read_manifest(path):
    out = {}
    for l in open(path, encoding="utf-8").read().splitlines():
        if l.strip(): h, rel = l.split(None, 1); out[rel.strip()] = h
    return out


def iso(t): return calendar.timegm(time.strptime(t, "%Y-%m-%dT%H:%M:%SZ"))


def load(directory, allow_file=None, manifest=None, cut=CUT):
    """-> (data {name: {end_ts: (bid, ask)}}, funding {name: {ts: rate}}, counts, weekday_counts)"""
    mp = manifest or MANIFEST; refuse_unless_allowed(allow_file, mp); man = read_manifest(mp)
    wall3, wallS = set(INDEX3), set(STOCKS); c = collections.Counter(); data = {n: {} for n in INDEX3 + STOCKS}; funding = {n: {} for n in INDEX3 + STOCKS}; wk = collections.Counter()
    def start(tk): return START3 if tk in wall3 else START_STOCK
    for rel in sorted(man):
        path = os.path.join(directory, rel)
        if not os.path.exists(path): c["manifest file missing"] += 1; continue
        if sha_of(path) != man[rel]: raise SystemExit("REFUSED: %s does not match the manifest sha256" % rel)
        with gzip.open(path, "rt", newline="") as fh:
            r = csv.reader(fh); h = next(r, None)
            if h is None: c["empty file"] += 1; continue
            if rel.startswith("kalshi1m/"):
                ti, ei, bi, ai = h.index("ticker"), h.index("end_period_ts"), h.index("bid_close"), h.index("ask_close")
                for row in r:
                    tk = row[ti]
                    if tk not in wall3 and tk not in wallS: c["candle row outside the wall (not parsed)"] += 1; continue
                    if row[bi] == "" or row[ai] == "": c["candle without a bid or ask (dropped)"] += 1; continue
                    e = int(row[ei])
                    if e < start(tk): c["candle before the name's start (dropped)"] += 1; continue
                    if e >= cut: c["candle at or after the cut (dropped)"] += 1; continue
                    q = (float(row[bi]), float(row[ai]))
                    if e in data[tk] and data[tk][e] != q: c["duplicate candle differs (first kept)"] += 1
                    data[tk].setdefault(e, q)
            else:
                ti, fi, ri = h.index("ticker"), h.index("funding_time"), h.index("funding_rate")
                for row in r:
                    tk = row[ti]
                    if tk not in wall3 and tk not in wallS: c["funding row outside the wall (not parsed)"] += 1; continue
                    if row[ri] == "": c["funding row without a rate (dropped)"] += 1; continue
                    t = iso(row[fi])
                    if t < start(tk) - 3 * 86400: c["funding row more than 3 days before the start (dropped)"] += 1; continue
                    if t >= cut: c["funding row at or after the cut (dropped)"] += 1; continue
                    funding[tk][t] = float(row[ri])
    for n in funding:
        for t in funding[n]: wk[time.gmtime(t).tm_wday] += 1
    return data, funding, dict(c), dict(wk)


if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    d, f, c, wk = load(sys.argv[1], *(sys.argv[2:3]))
    print({"counts": c, "names_with_candles": sum(1 for v in d.values() if v), "candles": sum(len(v) for v in d.values()), "names_with_prints": sum(1 for v in f.values() if v), "prints": sum(len(v) for v in f.values()), "prints_by_UTC_weekday_Mon0": dict(sorted(wk.items())), "loader_sha256": self_sha(), "manifest_sha256": sha_of(MANIFEST)})
