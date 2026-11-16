"""ENGINE1 held-out loader (Desk A, Nov 16 2026), for the one read of the 190 validate-bar rules on closes the archive never held (plan ENGINE1_HELDOUT_READ_PLAN_NOV16.md, Auditor B's windows). Offline; reads only the pull runs NAMED ON THE ALLOW LINE, only through the order below.
REFUSES unless HELDOUT_PULL_RUNS.md carries a line with the mark, "engine1_heldout_load.py" and this file's own sha256 (no flag, no env var); the runs it opens are the ones that line names (ENGINE1_HELD_LISTS_*/<stamp> and ENGINE1_HELD_CANDLES_NN/<stamp>), nothing else.
Order: (1) lists: ticker and close_time ONLY; a close outside its series' window (WINDOWS) is dropped and counted before any other key is touched, and WTI and Silver closes within 5 minutes of 13:30Z on ANY date are dropped and counted (EVENT830's windows); (2) `result` only for kept markets (a result that is not yes or no is kept as 'void', never dropped: no conditioning on the outcome); (3) candles: market_ticker first, a market not kept is never parsed further; for kept ones every candle ending at or before the close (bid, ask, last, volume, open interest); candles ending after the close are dropped and counted.
  python3 -I engine1_heldout_load.py <dir holding the pull run folders>   prints the drop counts and the per-series market counts."""
import os, sys, json, gzip, hashlib, collections, calendar, time
HERE = os.path.dirname(os.path.abspath(__file__))
HELD_FROM = 1791043200                                   # 2026-10-03T16:00:00Z (date -u checked)
A_TO, B_TO = 1793145600, 1793721600                      # 2026-10-28T00:00:00Z and 2026-11-03T16:00:00Z (date -u checked)
WINDOWS = {"KXBTC15M": (HELD_FROM, A_TO), "KXETH15M": (HELD_FROM, A_TO), "KXXRP15M": (HELD_FROM, A_TO), "KXDOGE15M": (HELD_FROM, A_TO), "KXGOLD15M": (HELD_FROM, A_TO),
           "KXHYPE15M": (HELD_FROM, B_TO), "KXSOL15M": (HELD_FROM, B_TO), "KXNEAR15M": (HELD_FROM, B_TO), "KXBNB15M": (HELD_FROM, B_TO), "KXZEC15M": (HELD_FROM, B_TO), "KXWTI15M": (HELD_FROM, B_TO), "KXSILVER15M": (HELD_FROM, B_TO)}
EVENT830_CUT = ("KXWTI15M", "KXSILVER15M"); EVENT830_SOD = 13 * 3600 + 30 * 60; EVENT830_BAND = 300
N_FLOOR = {s: (74 if w[1] == A_TO else 90) for s, w in WINDOWS.items()}      # 3 a day x the window days, Auditor B's constants (the five R6 series about 74, the rest 90)
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by Desk A's ENGINE1 held-out loader"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def allowed_runs():
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "engine1_heldout_load.py" in line and self_sha() in line:
            toks = [t.strip(" ,;()") for t in line.replace("\\", "/").split()]
            lists = sorted({t for t in toks if t.startswith("ENGINE1_HELD_LISTS_") and "/" in t}); cands = sorted({t for t in toks if t.startswith("ENGINE1_HELD_CANDLES_") and "/" in t})
            if not lists or not cands: raise SystemExit("REFUSED: the allow-list line names no ENGINE1_HELD_LISTS run or no ENGINE1_HELD_CANDLES run")
            return lists, cands
    raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md has no allow-list line naming engine1_heldout_load.py with this file's sha256 %s (the Head's written acceptance, merged by Main)" % self_sha())
PARTIAL_OK = {"ENGINE1_HELD_CANDLES_A1": frozenset(("h00048",))}      # Nov 16: run 118 answered h00001 to h00047 and stopped on h00048 (HTTP 400, over the 10,000 minutes x tickers limit); ENGINE1_HELD_CANDLES_A1C (a complete run) carries that request split in two and every request never sent. Only that run and only that id may be unanswered, and only with status 400.
def run_bodies(base, run):
    folder = os.path.join(base, *run.split("/"))
    try: man = json.load(open(os.path.join(folder, "manifest.json")))
    except Exception as e: raise SystemExit("REFUSED: %s has no readable manifest.json (%s)" % (run, e))
    okfail = PARTIAL_OK.get(run.split("/")[0], frozenset())
    if not isinstance(man.get("rows"), list) or not man["rows"] or man.get("status") != ("complete" if not okfail else "stopped_failures"): raise SystemExit("REFUSED: %s is not a complete run" % run)
    ids = collections.defaultdict(list)
    for r in man["rows"]: ids[r.get("id")].append(r)
    for rid, rs in ids.items():
        if rid in okfail:
            if any(r.get("status") == 200 for r in rs) or any(r.get("status") not in (400, 429) for r in rs): raise SystemExit("REFUSED: request %r of %s is not the registered 400" % (rid, run))
            continue
        if not any(r.get("status") == 200 for r in rs) or any(r.get("status") not in (200, 429) for r in rs): raise SystemExit("REFUSED: request %r of %s was not answered 200" % (rid, run))
    for r in man["rows"]:
        if r.get("status") == 200 and "file" in r: yield json.load(gzip.open(os.path.join(folder, r["file"])))
def iso(s):
    try: return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception: return None
def in_window(series, cl):
    """-> None if kept, else the reason it is dropped. A market's series is the ticker's first part."""
    w = WINDOWS.get(series)
    if w is None: return "series not in the plan"
    if not (w[0] <= cl < w[1]): return "close outside the series window"
    if series in EVENT830_CUT and abs(cl % 86400 - EVENT830_SOD) <= EVENT830_BAND: return "EVENT830 cut (13:30Z, WTI and Silver)"
    return None
def num(x):
    try: return float(x) if x not in ("", None) else None
    except (TypeError, ValueError): return None
def load(base, runs=None):
    """-> ({series: [market]}, counts). market = {series, ticker, close, result, candles [(end, bid, ask, last, vol, oi)]}: the driver's own format. runs = (lists, candles) is for the tests only."""
    lists, cands = runs if runs is not None else allowed_runs()
    c = collections.Counter(); kept = {}
    for run in lists:                                                        # (1) ticker and close_time ONLY
        for b in run_bodies(base, run):
            for m in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk = m.get("ticker"); ct = m.get("close_time"); cl = iso(ct) if isinstance(ct, str) else None
                if not isinstance(tk, str) or cl is None: c["no ticker or close"] += 1; continue
                series = tk.split("-")[0]; why = in_window(series, cl)
                if why: c["dropped: " + why] += 1; continue
                if tk in kept: c["duplicate ticker (first kept)"] += 1; continue
                kept[tk] = [series, cl, m]                                   # the market object is held; `result` is read only in step (2)
    res = {}
    for tk, (series, cl, m) in kept.items():                                 # (2) result for kept rows only; not yes or no stays 'void'
        r = m.get("result"); res[tk] = r if r in ("yes", "no") else "void"
        if res[tk] == "void": c["result not yes or no (kept as void)"] += 1
    cand = collections.defaultdict(dict)
    for run in cands:                                                        # (3) market_ticker first; candles of kept markets only
        for b in run_bodies(base, run):
            for mk in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk = mk.get("market_ticker")
                if tk not in kept: c["candle market not kept (not parsed)"] += 1; continue
                cl = kept[tk][1]
                for k in mk.get("candlesticks", []):
                    try: e = int(k["end_period_ts"]); bid = float(k["yes_bid"]["close_dollars"]); ask = float(k["yes_ask"]["close_dollars"])
                    except (KeyError, TypeError, ValueError): c["candle unreadable"] += 1; continue
                    if e > cl: c["candle after close (dropped)"] += 1; continue
                    row = (e, bid, ask, num((k.get("price") or {}).get("close_dollars")), num(k.get("volume_fp")), num(k.get("open_interest_fp")))
                    if e in cand[tk] and cand[tk][e] != row: c["duplicate candle differs (first kept)"] += 1
                    cand[tk].setdefault(e, row)
    out = collections.defaultdict(list)
    for tk, (series, cl, _) in kept.items():
        out[series].append({"series": series, "ticker": tk, "close": cl, "result": res[tk], "candles": sorted(cand[tk].values())})
    return {s: sorted(v, key=lambda m: (m["close"], m["ticker"])) for s, v in out.items()}, dict(c)
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    w, c = load(sys.argv[1]); print(json.dumps({"dropped": c, "markets": {s: len(v) for s, v in w.items()}, "loader_sha256": self_sha()}, indent=1))
