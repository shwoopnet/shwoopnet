#!/usr/bin/env python3
"""KXINX15M reader for the Testing Desk's second engine build (Nov 16, 2026). Offline; reads ONLY the three SPXOI1 runs named below, only through the order below, and REFUSES unless the
allow-list file carries a line for this reader naming this file's own sha256 (no flag, no env var). Opens no other run.
Order: (1) lists: ticker and close_time ONLY; rows at or after the cut 2026-12-01T00:00:00Z (1796083200) are dropped and counted before any other key is touched; (2) lists: `result` only for kept rows;
(3) candles: market_ticker first; a market not kept is never parsed further; for kept ones end_period_ts, yes_bid and yes_ask close_dollars, volume (volume_fp first) and open_interest (open_interest_fp first) only.
Disclosure carried in the allow line: SPXSCALP and ESLEAD1 already read KXINX15M prices on these days under other rules (print shas in SPX_ES_RUN_PRINTOUT_SHAS.txt), so every family read here is a further look at the same days.
  python3 -I inx15_second_load.py <dir holding the pull run folders> [out.sqlite]   prints the drop counts; the optional sqlite (market and candle tables, the OIREL-X extract's schema) goes to scratch."""
import calendar, collections, gzip, hashlib, json, os, sqlite3, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
CUT = 1796083200          # 2026-12-01T00:00:00Z
SERIES = "KXINX15M"
LISTS = ("SPXOI1_LISTS/2026-11-14T0101Z_43537940232",)
CANDLES = ("SPXOI1_CANDLES/2026-11-14T0107Z_43538584524", "SPXOI1_CANDLES_PATCH/2026-11-14T0124Z_43540387136")
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the Testing Desk's INX15M second-build reader"


def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


def refuse_unless_allowed(allow_file=None):
    try: text = open(allow_file or ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow-list file cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    if not line or "inx15_second_load.py" not in line[0] or self_sha() not in line[0]: raise SystemExit("REFUSED: no allow-list line naming inx15_second_load.py with this file's sha256 %s" % self_sha())
    for r in LISTS + CANDLES:
        if r not in line[0]: raise SystemExit("REFUSED: the allow-list line does not name run %s" % r)


def run_bodies(base, run):
    folder = os.path.join(base, *run.split("/"))
    try: man = json.load(open(os.path.join(folder, "manifest.json")))
    except Exception as e: raise SystemExit("REFUSED: %s has no readable manifest.json (%s)" % (run, e))
    if man.get("status") != "complete" or not isinstance(man.get("rows"), list) or not man["rows"]: raise SystemExit("REFUSED: %s is not a complete run" % run)
    ids = collections.defaultdict(list)
    for r in man["rows"]: ids[r.get("id")].append(r)
    for rid, rs in ids.items():
        if not any(r.get("status") == 200 for r in rs) or any(r.get("status") not in (200, 429) for r in rs): raise SystemExit("REFUSED: request %r of %s was not answered 200" % (rid, run))
    for r in man["rows"]:
        if r.get("status") == 200 and "file" in r: yield json.load(gzip.open(os.path.join(folder, r["file"]), "rt"))


def iso(s):
    try: return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception: return None


def num(c, fp, plain):
    v = c.get(fp)
    if v not in (None, ""):
        try: return float(v)
        except (TypeError, ValueError): return None
    v = c.get(plain)
    try: return None if v is None or isinstance(v, bool) else float(v)
    except (TypeError, ValueError): return None


def load(base, allow_file=None):
    refuse_unless_allowed(allow_file)
    c = collections.Counter(); kept = {}
    for run in LISTS:                                                                       # (1) ticker and close_time ONLY; the cut first
        for b in run_bodies(base, run):
            for m in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk, ct = m.get("ticker"), m.get("close_time")
                cl = iso(ct) if isinstance(ct, str) else None
                if not isinstance(tk, str) or cl is None: c["unreadable ticker or close"] += 1; continue
                if cl >= CUT: c["dropped by the cut"] += 1; continue
                if tk.split("-")[0] != SERIES: c["other series (dropped)"] += 1; continue
                kept[tk] = [cl, m]
    res = {}
    for tk, (cl, m) in kept.items():                                                       # (2) result for kept rows only
        r = m["result"] if "result" in m else None
        if r in ("yes", "no"): res[tk] = r
        else: c["no result (dropped)"] += 1
    cand = collections.defaultdict(dict)
    for run in CANDLES:                                                                    # (3) candles for kept markets only
        for b in run_bodies(base, run):
            for mk in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk = mk.get("market_ticker")
                if tk not in res: c["candle market not kept (not parsed)"] += 1; continue
                cl = kept[tk][0]
                for k in mk.get("candlesticks", []):
                    try: e = int(k["end_period_ts"]); bid = float(k["yes_bid"]["close_dollars"]); ask = float(k["yes_ask"]["close_dollars"])
                    except (KeyError, TypeError, ValueError): c["candle unreadable"] += 1; continue
                    if e > cl: c["candle after close (dropped)"] += 1; continue
                    row = (bid, ask, num(k, "volume_fp", "volume"), num(k, "open_interest_fp", "open_interest"))
                    if e in cand[tk] and cand[tk][e] != row: c["duplicate candle differs (first kept)"] += 1
                    cand[tk].setdefault(e, row)
    wins = [{"ticker": tk, "close": kept[tk][0], "result": res[tk], "candles": sorted((e,) + r for e, r in cand[tk].items())} for tk in sorted(res, key=lambda t: (kept[t][0], t))]
    return wins, dict(c)


def to_sqlite(wins, path):
    db = sqlite3.connect(path); db.execute("create table market(ticker,series,open_ts,close_ts,result,strike,src)"); db.execute("create table candle(ticker,end_ts,bid_c,ask_c,volume,oi)")
    for w in wins:
        db.execute("insert into market values(?,?,?,?,?,?,?)", (w["ticker"], SERIES, w["close"] - 900, w["close"], w["result"], None, "spxoi1")); db.executemany("insert into candle values(?,?,?,?,?,?)", [(w["ticker"],) + c for c in w["candles"]])
    db.commit(); db.close()


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3): sys.exit(__doc__)
    w, c = load(sys.argv[1])
    if len(sys.argv) == 3: to_sqlite(w, sys.argv[2])
    print(json.dumps({"dropped": c, "windows": len(w), "loader_sha256": self_sha()}, indent=1))
