#!/usr/bin/env python3
"""ENGINE1 extract (b): the NC15 runs in ONE schema (Forensics desk, Nov 15, 2026; the Head's written ruling of 22:45Z and Auditor B's request). WRITTEN WITHOUT OPENING ANY NC15 RUN; the only run of it on the real runs happens after the allow line is merged.
REFUSES unless HELDOUT_PULL_RUNS.md carries a line containing this file's name and its own sha256 and every run name below (no flag, no env var). Opens no other run.
Order, as the allow line: (1) lists: `ticker` and `close_time` ONLY; rows with close_time at or after CUT (2026-10-03T16:00Z, epoch 1791043200), or of a series not in SERIES, or with no readable close, are dropped and COUNTED before any other key of the market is touched.
(2) lists: `result` only for kept rows (not yes or no: dropped and counted). (3) candle runs: `market_ticker` first; a market not kept is counted and nothing else of it is parsed; for a kept market, per candle: end_period_ts, yes_bid.close_dollars, yes_ask.close_dollars (a candle without both is counted unreadable and skipped),
plus last (price.close_dollars), volume (volume_fp, else volume) and open interest (open_interest_fp, else open_interest) when present: a missing one is NULL and counted. A candle ending after the market's close is DROPPED and counted. A duplicate (ticker, end_ts) keeps the first and is counted (and counted again if it differs).
Schema (as the archive extract): market(ticker, series, close_ts, result, src) and candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi). Prints the counts and the sha256 of the sqlite. usage: python3 -I engine1_nc15.py <dir holding the pull run folders> <out dir>"""
import os, sys, json, gzip, hashlib, collections, calendar, time, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__))
CUT = 1791043200
SERIES = ("KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M", "KXAUDUSD15M", "KXUSDCAD15M", "KXNATGAS15M")
LISTS = ("NC15_LISTS_A/2026-11-14T0639Z_43567362760", "NC15_LISTS_B/2026-11-14T0710Z_43569819335")
CANDLES = ("NC15_CANDLES_A1/2026-11-14T0742Z_43572344399", "NC15_CANDLES_A2/2026-11-14T0822Z_43575507647", "NC15_CANDLES_A3/2026-11-14T0902Z_43578620866",
           "NC15_CANDLES_B1/2026-11-14T0940Z_43581645588", "NC15_CANDLES_B2/2026-11-14T1020Z_43584771195", "NC15_CANDLES_B3/2026-11-14T1101Z_43588018609", "NC15_CANDLES_B4/2026-11-14T1141Z_43591230490")
ALLOW_FILE = os.path.join(HERE, "..", "..", "HELDOUT_PULL_RUNS.md")
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def refuse_unless_allowed(allow_file=ALLOW_FILE):
    try: text = open(allow_file, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    lines = [l for l in text.splitlines() if "engine1_nc15.py" in l and self_sha() in l]
    if not lines: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md has no allow-list line naming engine1_nc15.py with this file's sha256 %s" % self_sha())
    for r in LISTS + CANDLES:
        if r not in lines[0]: raise SystemExit("REFUSED: the allow-list line does not name run %s" % r)
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
        if r.get("status") == 200 and "file" in r: yield json.load(gzip.open(os.path.join(folder, r["file"])))
def iso(s):
    try: return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception: return None
def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None
def pick(c, path):
    for p in path:
        v = c
        for k in p:
            v = v.get(k) if isinstance(v, dict) else None
        if v is not None and num(v) is not None: return num(v)
    return None
def build(base, out, allow_file=ALLOW_FILE):
    refuse_unless_allowed(allow_file); os.makedirs(out, exist_ok=True)
    c = collections.Counter(); kept = {}
    for run in LISTS:                                                       # (1) ticker and close_time only
        for b in run_bodies(base, run):
            for m in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk, ct = m["ticker"], m["close_time"]
                s = tk.split("-")[0] if isinstance(tk, str) else None; cl = iso(ct) if isinstance(ct, str) else None
                if s not in SERIES or cl is None: c["unknown series or no close"] += 1; continue
                if cl >= CUT: c["dropped by the cut"] += 1; continue
                if tk in kept: c["duplicate market in the lists (first kept)"] += 1; continue
                kept[tk] = [s, cl, m]
    res = {}
    for tk, v in kept.items():                                              # (2) result for kept rows only
        r = v[2].get("result")
        if r in ("yes", "no"): res[tk] = r
        else: c["no result (dropped)"] += 1
    dst = os.path.join(out, "ENGINE1_nc15_extract.sqlite")
    if os.path.exists(dst): os.remove(dst)
    o = sqlite3.connect(dst); o.execute("create table market(ticker, series, close_ts, result, src)"); o.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    seen = {}
    for run in CANDLES:                                                     # (3) candles for kept markets only
        for b in run_bodies(base, run):
            for mk in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk = mk["market_ticker"]
                if tk not in res: c["candle market not kept (not parsed)"] += 1; continue
                cl = kept[tk][1]
                for k in mk["candlesticks"]:
                    try: e = int(k["end_period_ts"]); bid = float(k["yes_bid"]["close_dollars"]); ask = float(k["yes_ask"]["close_dollars"])
                    except (KeyError, TypeError, ValueError): c["candle unreadable (no end, bid or ask)"] += 1; continue
                    if e > cl: c["candle after close (dropped)"] += 1; continue
                    last = pick(k, [("price", "close_dollars")]); vol = pick(k, [("volume_fp",), ("volume",)]); oi = pick(k, [("open_interest_fp",), ("open_interest",)])
                    for nm, v in (("last", last), ("volume", vol), ("oi", oi)):
                        if v is None: c["candle without " + nm + " (NULL)"] += 1
                    key = (tk, e); row = (bid, ask, last, vol, oi)
                    if key in seen:
                        c["duplicate candle (first kept)"] += 1
                        if seen[key] != row: c["duplicate candle differs"] += 1
                        continue
                    seen[key] = row; o.execute("insert into candle values(?,?,?,?,?,?,?)", (tk, e, bid, ask, last, vol, oi)); c["candles kept"] += 1
    for tk, r in res.items(): o.execute("insert into market values(?,?,?,?,?)", (tk, kept[tk][0], kept[tk][1], r, "nc15"))
    o.commit(); o.execute("create index ix on candle(ticker)"); o.commit(); o.execute("vacuum"); o.close()
    sha = hashlib.sha256(open(dst, "rb").read()).hexdigest(); db = sqlite3.connect(dst)
    by = db.execute("select series,count(*),min(close_ts),max(close_ts) from market group by series order by series").fetchall()
    L = {"extract": "ENGINE1 nc15", "cut": CUT, "series": SERIES, "runs": list(LISTS + CANDLES), "counts": dict(c), "markets_by_series": by, "markets": len(res), "extract_sha256": sha, "extractor_sha256": self_sha()}
    json.dump(L, open(os.path.join(out, "ENGINE1_nc15_cutlog.json"), "w"), indent=1); return L
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    L = build(sys.argv[1], sys.argv[2]); print(json.dumps({k: L[k] for k in ("counts", "markets", "extract_sha256", "extractor_sha256")}, indent=1))
