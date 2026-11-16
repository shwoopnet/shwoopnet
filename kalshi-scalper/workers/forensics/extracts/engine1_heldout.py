#!/usr/bin/env python3
"""ENGINE1 HELD-OUT read extractor (Forensics desk, Nov 16, 2026; the Head's order of 17:20Z). WRITTEN WITHOUT OPENING ANY PULL RUN. The run names below are filled in AFTER the pull lands (which changes this file's sha256: one allow line after landing).
REFUSES unless HELDOUT_PULL_RUNS.md carries a line containing this file's name, its own sha256 and EVERY run name of LISTS and CANDLES (an empty list refuses). Opens no other run.
Windows (market close_time, epoch, from inclusive to exclusive; each epoch checked with calendar.timegm): FROM = 1791043200 (2026-10-03T16:00Z, HOLDS H01 ENGINE1 global freeze: this card's own read). TO per series: the 8 clean series (BTC, ETH, XRP, GOLD, HYPE, NEAR, SOL, BNB; the SHADOW_LIST_V1 markets) and DOGE: 1793145600 (2026-10-28T00:00Z, HOLDS H20 for BTC, ETH, XRP, DOGE, GOLD, and the card's own end for the others);
SILVER, COPPER, WTI, EURUSD, GBPUSD, USDJPY: 1793836800 (2026-11-05T00:00Z, H21); NATGAS: 1795046400 (2026-11-19T00:00Z, H22); ZEC, PALLADIUM, PLATINUM: no HOLDS row beyond H01, so no end other than the pull's own.
Order as the NC15 and ECONHIST extractors: (1) lists: ticker and close_time ONLY; a series not among the 19, an unreadable close, a close before FROM or at or after the series' TO is dropped and counted (separately for before and after) before any other key of the market is touched; (2) result for kept rows only (not yes or no: dropped and counted);
(3) candle runs: market_ticker first, non-kept markets counted and not parsed; per candle: end_period_ts, yes_bid.close_dollars, yes_ask.close_dollars (else unreadable, skipped), plus last = price.close_dollars, volume = volume_fp, oi = open_interest_fp (NULL and counted when missing); a candle ending after the market's close is dropped and counted; duplicates keep the first and are counted.
Schema as the other ENGINE1 extracts: market(ticker, series, close_ts, result, src) and candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi). usage: python3 -I engine1_heldout.py <dir holding the pull run folders> <out dir>"""
import os, sys, json, gzip, hashlib, collections, calendar, time, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__))
FROM = calendar.timegm((2026, 10, 3, 16, 0, 0))
OCT28, NOV5, NOV19 = calendar.timegm((2026, 10, 28, 0, 0, 0)), calendar.timegm((2026, 11, 5, 0, 0, 0)), calendar.timegm((2026, 11, 19, 0, 0, 0))
TO = {"KXBTC15M": OCT28, "KXETH15M": OCT28, "KXXRP15M": OCT28, "KXGOLD15M": OCT28, "KXHYPE15M": OCT28, "KXNEAR15M": OCT28, "KXSOL15M": OCT28, "KXBNB15M": OCT28, "KXDOGE15M": OCT28,
      "KXSILVER15M": NOV5, "KXCOPPER15M": NOV5, "KXWTI15M": NOV5, "KXEURUSD15M": NOV5, "KXGBPUSD15M": NOV5, "KXUSDJPY15M": NOV5, "KXNATGAS15M": NOV19, "KXZEC15M": None, "KXPALLADIUM15M": None, "KXPLATINUM15M": None}
LISTS = ()      # filled after the pull lands: "<job>/<stamp>_<runid>" folder names of the lists runs
CANDLES = ()    # filled after the pull lands: the candle runs
ALLOW_FILE = os.path.join(HERE, "..", "..", "HELDOUT_PULL_RUNS.md")
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def refuse_unless_allowed(allow_file=ALLOW_FILE, lists=None, candles=None):
    lists = LISTS if lists is None else lists; candles = CANDLES if candles is None else candles
    if not lists or not candles: raise SystemExit("REFUSED: no run names are filled in")
    try: text = open(allow_file, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    lines = [l for l in text.splitlines() if "engine1_heldout.py" in l and self_sha() in l]
    if not lines: raise SystemExit("REFUSED: no allow-list line naming engine1_heldout.py with this file's sha256 %s" % self_sha())
    for r in tuple(lists) + tuple(candles):
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
def build(base, out, allow_file=ALLOW_FILE, lists=None, candles=None):
    lists = LISTS if lists is None else lists; candles = CANDLES if candles is None else candles
    refuse_unless_allowed(allow_file, lists, candles); os.makedirs(out, exist_ok=True); c = collections.Counter(); kept = {}
    for run in lists:                                                       # (1) ticker and close_time only
        for b in run_bodies(base, run):
            for m in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk, ct = m["ticker"], m["close_time"]
                s = tk.split("-")[0] if isinstance(tk, str) else None; cl = iso(ct) if isinstance(ct, str) else None
                if s not in TO or cl is None: c["unknown series or no close"] += 1; continue
                if cl < FROM: c["dropped before 2026-10-03T16:00Z"] += 1; continue
                if TO[s] is not None and cl >= TO[s]: c["dropped at or after the series' end"] += 1; continue
                if tk in kept: c["duplicate market in the lists (first kept)"] += 1; continue
                kept[tk] = [s, cl, m]
    res = {}
    for tk, v in kept.items():                                              # (2) result for kept rows only
        r = v[2].get("result")
        if r in ("yes", "no"): res[tk] = r
        else: c["no result (dropped)"] += 1
    dst = os.path.join(out, "ENGINE1_heldout_extract.sqlite")
    if os.path.exists(dst): os.remove(dst)
    o = sqlite3.connect(dst); o.execute("create table market(ticker, series, close_ts, result, src)"); o.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)"); seen = {}
    for run in candles:                                                     # (3) candles for kept markets only
        for b in run_bodies(base, run):
            for mk in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk = mk["market_ticker"]
                if tk not in res: c["candle market not kept (not parsed)"] += 1; continue
                cl = kept[tk][1]
                for k in mk["candlesticks"]:
                    try: e = int(k["end_period_ts"]); bid = float(k["yes_bid"]["close_dollars"]); ask = float(k["yes_ask"]["close_dollars"])
                    except (KeyError, TypeError, ValueError): c["candle unreadable (no end, bid or ask)"] += 1; continue
                    if e > cl: c["candle after close (dropped)"] += 1; continue
                    pr = k.get("price"); last = num(pr.get("close_dollars")) if isinstance(pr, dict) else None; vol = num(k.get("volume_fp")); oi = num(k.get("open_interest_fp"))
                    for nm, v in (("last", last), ("volume", vol), ("oi", oi)):
                        if v is None: c["candle without " + nm + " (NULL)"] += 1
                    key = (tk, e); row = (bid, ask, last, vol, oi)
                    if key in seen:
                        c["duplicate candle (first kept)"] += 1
                        if seen[key] != row: c["duplicate candle differs"] += 1
                        continue
                    seen[key] = row; o.execute("insert into candle values(?,?,?,?,?,?,?)", (tk, e, bid, ask, last, vol, oi)); c["candles kept"] += 1
    for tk, r in res.items(): o.execute("insert into market values(?,?,?,?,?)", (tk, kept[tk][0], kept[tk][1], r, "heldout"))
    o.commit(); o.execute("create index ix on candle(ticker)"); o.commit(); o.execute("vacuum"); o.close()
    sha = hashlib.sha256(open(dst, "rb").read()).hexdigest(); db = sqlite3.connect(dst)
    by = db.execute("select series,count(*),min(close_ts),max(close_ts) from market group by series order by series").fetchall()
    L = {"extract": "ENGINE1 heldout", "from": FROM, "to": TO, "runs": list(lists) + list(candles), "counts": dict(c), "markets_by_series": by, "markets": len(res), "extract_sha256": sha, "extractor_sha256": self_sha()}
    json.dump(L, open(os.path.join(out, "ENGINE1_heldout_cutlog.json"), "w"), indent=1); return L
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    L = build(sys.argv[1], sys.argv[2]); print(json.dumps({k: L[k] for k in ("counts", "markets", "markets_by_series", "extract_sha256", "extractor_sha256")}, indent=1))
