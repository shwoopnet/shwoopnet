"""Turns the V2READS pull answers into V2's data/fresh.sqlite (the file its forward-read scripts read), plus empty-schema files for the history sources they open.
  python3 -I v2reads_loader.py <lists run folder> <candle run folder> [<candle run folder> ...] <out dir>      (writes <out dir>/fresh.sqlite)
  python3 -I v2reads_loader.py selftest
Schema = V2's backfill.py: market(ticker, series, open_ts, close_ts, result, strike, n_candles) and candle(ticker, series, end_ts, bid_o..bid_c, ask_o..ask_c, price_c, volume, oi);
a candle is parsed as backfill.parse_candle does (yes_bid / yes_ask / price with *_dollars, volume_fp, open_interest_fp). A market with no candles is NOT stored (skip_empty, as in fresh_update).
The history sources hs1.load() opens (alts2, alts3, alts4, book, l1b, e3b) are created EMPTY so P6F and P6R, which read history plus fresh, run on the pulled days alone."""
import gzip, json, os, sys, sqlite3, calendar, time, re, tempfile
SCHEMA = """CREATE TABLE IF NOT EXISTS market(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike REAL, n_candles INTEGER);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, series TEXT, end_ts INTEGER, bid_o REAL, bid_h REAL, bid_l REAL, bid_c REAL, ask_o REAL, ask_h REAL, ask_l REAL, ask_c REAL, price_c REAL, volume REAL, oi REAL, PRIMARY KEY (ticker, end_ts));"""
HIST = ["alts2", "alts3", "alts4", "book", "l1b", "e3b"]
def iso_ts(s):
    try: return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None
def f(x):
    try: return float(x) if x not in (None, "") else None
    except Exception: return None
def d(obj, k): return f((obj or {}).get(k))
def bodies(folder):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import heldout_guard_v2 as heldout_guard; heldout_guard.refuse_heldout(folder, "v2reads_loader.bodies")      # standing rule (h)
    man = json.load(open(os.path.join(folder, "manifest.json")))
    for row in man["rows"]:
        if row.get("status") == 200 and "file" in row: yield json.load(gzip.open(os.path.join(folder, row["file"])))
def convert(lists, candle_folders, outdir):
    mk = {}
    for b in bodies(lists):
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            o, c = iso_ts(m.get("open_time") or ""), iso_ts(m.get("close_time") or "")
            if m.get("ticker") and o and c and m.get("result") in ("yes", "no"): mk[m["ticker"]] = (m["ticker"].split("-")[0], o, c, m["result"], f(m.get("floor_strike")))
    rows = {}
    for cf in candle_folders:
        for b in bodies(cf):
            for m in (b.get("markets", []) if isinstance(b, dict) else []):
                tk = m.get("market_ticker") or m.get("ticker")
                if tk not in mk: continue
                for c in m.get("candlesticks", []):
                    if c.get("end_period_ts") is None: continue
                    by, ay, p = c.get("yes_bid"), c.get("yes_ask"), c.get("price")
                    rows[(tk, int(c["end_period_ts"]))] = (tk, mk[tk][0], int(c["end_period_ts"]), d(by, "open_dollars"), d(by, "high_dollars"), d(by, "low_dollars"), d(by, "close_dollars"),
                                                           d(ay, "open_dollars"), d(ay, "high_dollars"), d(ay, "low_dollars"), d(ay, "close_dollars"), d(p, "close_dollars"), f(c.get("volume_fp")), f(c.get("open_interest_fp")))
    os.makedirs(outdir, exist_ok=True); path = os.path.join(outdir, "fresh.sqlite")
    if os.path.exists(path): os.remove(path)
    db = sqlite3.connect(path); db.executescript(SCHEMA)
    n = collections_count = 0; per = {}
    for (tk, _), r in rows.items(): per[tk] = per.get(tk, 0) + 1
    for tk, (s, o, c, res, strike) in mk.items():
        if tk in per:
            db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)", (tk, s, o, c, res, strike, per[tk])); n += 1
    db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", list(rows.values())); db.commit(); db.close()
    for h in HIST:
        hd = sqlite3.connect(os.path.join(outdir, h + ".sqlite")); hd.executescript(SCHEMA); hd.commit(); hd.close()
    return n, len(mk), len(rows)
def selftest():
    T = tempfile.mkdtemp(); L, C, O = T + "/lists", T + "/candles", T + "/out"; os.makedirs(L); os.makedirs(C)
    t0 = calendar.timegm(time.strptime("2026-10-20", "%Y-%m-%d")); ms = []
    for q in range(6):
        c = t0 + 900 * (q + 1); ms.append({"ticker": "KXGOLD15M-T%d" % q, "open_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(c - 900)), "close_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(c)), "result": "yes" if q % 2 else "no", "floor_strike": 100.0 + q})
    ms.append({"ticker": "KXGOLD15M-OPEN", "open_time": "2026-10-20T00:00:00Z", "close_time": "2026-10-20T02:00:00Z", "result": ""})
    json.dump({"markets": ms}, gzip.open(L + "/0001.json.gz", "wt")); json.dump({"rows": [{"status": 200, "file": "0001.json.gz"}]}, open(L + "/manifest.json", "w"))
    cand = lambda tk, c: {"market_ticker": tk, "candlesticks": [{"end_period_ts": c - 60 * k, "yes_bid": {"open_dollars": "0.90", "close_dollars": "0.91"}, "yes_ask": {"open_dollars": "0.92", "close_dollars": "0.93"},
                                                               "price": {"close_dollars": "0.92"}, "volume_fp": "5.00", "open_interest_fp": "100.00"} for k in range(5)]}
    json.dump({"markets": [cand("KXGOLD15M-T%d" % q, t0 + 900 * (q + 1)) for q in range(5)]}, gzip.open(C + "/0001.json.gz", "wt")); json.dump({"rows": [{"status": 200, "file": "0001.json.gz"}]}, open(C + "/manifest.json", "w"))
    n, nm, nc = convert(L, [C], O)
    assert (n, nm, nc) == (5, 6, 25), (n, nm, nc)      # T5 has no candles: not stored; the unsettled market is not listed
    sys.path.insert(0, os.environ.get("V2SRC", "")) if os.environ.get("V2SRC") else None
    db = sqlite3.connect(O + "/fresh.sqlite"); assert db.execute("SELECT COUNT(*) FROM market").fetchone()[0] == 5
    r = db.execute("SELECT bid_c, ask_c, price_c, volume, oi FROM candle LIMIT 1").fetchone(); assert r == (0.91, 0.93, 0.92, 5.0, 100.0), r
    assert all(os.path.exists(O + "/%s.sqlite" % h) for h in HIST)
    try:
        from scalper.fwd_reads import load_fresh
        m = load_fresh(O + "/fresh.sqlite", series=["KXGOLD15M"], start_ts=0); assert len(m) == 5 and len(m[0][2]) == 5, (len(m), len(m[0][2])); print("V2 load_fresh reads it:", len(m), "markets")
    except ImportError: print("(V2 load_fresh not importable here; set V2SRC to its src folder to check)")
    print("SELFTEST OK (lists + candles -> fresh.sqlite, empty history sources)")
if __name__ == "__main__":
    if sys.argv[1] == "selftest": selftest()
    else: print("markets stored %d of %d listed, candles %d" % convert(sys.argv[1], sys.argv[2:-1], sys.argv[-1]))
