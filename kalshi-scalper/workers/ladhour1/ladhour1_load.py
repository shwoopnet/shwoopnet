"""LADHOUR1 loader (Desk B, Nov 16 2026; DRAFT, unrun, unsigned). Offline. Reads a checkout of quote-data (quotes/<date>/<HHMM>/ladder.csv.gz) and ONE landed settled-list run folder PER series.
REFUSES unless HELDOUT_PULL_RUNS.md carries a line with the mark, "ladhour1_load.py", this file's own sha256 and the run stamp (no flag, no env var), and unless the window constants below are set.
Wall: each row's ticker is read FIRST (KXINXU-, KXNASDAQ100U-, KXWTIH-, KXGOLDH- only; anything else dropped and counted, nothing else of the row parsed), then close_time (outside [START, CUT) dropped and counted), then status active.
Output: {series: [{series, ticker, close, result, candles: [(end_ts, yes_bid, yes_ask, last, volume, oi)]}]}. Expected figures: EXPECTED_ladhour1_nov16.md."""
import os, sys, csv, gzip, io, json, hashlib, calendar, time, collections
HERE = os.path.dirname(os.path.abspath(__file__))
START = None            # unix seconds of start_utc: Main writes it (the close of the first ladder row of the first recorder file after the merge)
CUT = None              # unix seconds of the read date (exclusive)
SERIES = ("KXINXU", "KXNASDAQ100U", "KXWTIH", "KXGOLDH")
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md"); ALLOW_MARK = "readable ONLY by Desk B's LADHOUR1 loader"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def check_window():
    if START is None or CUT is None or CUT <= START: raise SystemExit("REFUSED: window not set (START and CUT are written by Main before any read)")
def dirs():
    check_window(); out = []; t = START - START % 86400
    while t <= CUT: out.append(time.strftime("%Y-%m-%d", time.gmtime(t))); t += 86400
    return out
def check_run_name(run, series):
    """the run folder must be <...>/LADHOUR1_RESULTS_<SERIES>/<stamp>; returns the stamp."""
    p = os.path.abspath(run)
    if os.path.basename(os.path.dirname(p)) != "LADHOUR1_RESULTS_" + series: raise SystemExit("REFUSED: %s is not a run folder of LADHOUR1_RESULTS_%s" % (run, series))
    return os.path.basename(p)
def refuse_unless_allowed(run_name):
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "ladhour1_load.py" in line and self_sha() in line and run_name in line: return
    raise SystemExit("REFUSED: no allow-list line names ladhour1_load.py with this file's sha256 %s and the run %s" % (self_sha(), run_name))
def iso(s):
    try: return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception: return None
def in_window(close_s):
    t = iso(close_s) if isinstance(close_s, str) else None
    return t if t is not None and START <= t < CUT else None
def series_of(ticker):
    for s in SERIES:
        if ticker.startswith(s + "-"): return s
    return None
def opened(path): return csv.DictReader(io.TextIOWrapper(gzip.open(path), encoding="utf-8", newline=""))
def ladder_rows(rows, cnt):
    """ticker FIRST, then close_time -> {ticker: (series, close, [(t_recv_s, bid, ask)])}."""
    out = {}
    for r in rows:
        s = series_of(r["ticker"])
        if s is None: cnt["ticker outside the wall (dropped)"] += 1; continue      # no other column of a wrong-series row is parsed
        c = in_window(r["close_time"])
        if c is None: cnt["ladder row dropped by the cut or no close"] += 1; continue
        if r["status"] != "active": cnt["ladder row not active (dropped)"] += 1; continue
        try: t = int(r["t_recv_ms"]) / 1000.0; b = float(r["yes_bid"]); a = float(r["yes_ask"])
        except (ValueError, KeyError): cnt["ladder row unreadable (dropped)"] += 1; continue
        out.setdefault(r["ticker"], (s, c, []))[2].append((t, b, a))
    return out
def candles_of(close, rows, cnt):
    last = {}
    for t, b, a in sorted(rows):
        end = (int(t) // 60 + 1) * 60
        last[end] = (end, b, a, None, 0, 0)
    out = []
    for end in sorted(last):
        if end > close: cnt["candle after close (dropped)"] += 1; continue
        out.append(last[end])
    return out
def result_rows(rows, series, cnt):
    """results of ONE series' run: ticker FIRST against that series' prefix only, then close_time, then result (yes, no, void)."""
    out = {}
    for r in rows:
        if not r["ticker"].startswith(series + "-"): cnt["result ticker outside the wall (dropped)"] += 1; continue
        c = in_window(r["close_time"])
        if c is None: cnt["result row outside the window (dropped)"] += 1; continue
        if r["result"] not in ("yes", "no", "void"): cnt["result not yes, no or void (dropped)"] += 1; continue
        out[r["ticker"]] = r["result"]
    return out
def assemble(lad, res_by_series, cnt):
    out = {s: [] for s in SERIES}
    for tk in sorted(lad):
        s, close, rows = lad[tk]
        if tk not in res_by_series.get(s, {}): cnt["no result (dropped)"] += 1; continue
        out[s].append({"series": s, "ticker": tk, "close": close, "result": res_by_series[s][tk], "candles": candles_of(close, rows, cnt)})
    return out
def load(base, runs):
    """runs: {series: run folder}; every series that has ladder rows needs its run."""
    check_window()
    for s, run in runs.items(): refuse_unless_allowed(check_run_name(run, s))
    cnt = collections.Counter(); lad = {}
    for d in dirs():
        dp = os.path.join(base, "quotes", d)
        if not os.path.isdir(dp): cnt["missing date directory"] += 1; continue
        for runname in sorted(os.listdir(dp)):
            p = os.path.join(dp, runname, "ladder.csv.gz")
            if not os.path.exists(p): continue
            for tk, (s, c, rows) in ladder_rows(opened(p), cnt).items(): lad.setdefault(tk, (s, c, []))[2].extend(rows)
    res = {}
    for s, run in runs.items():
        man = json.load(open(os.path.join(run, "manifest.json"))); res[s] = {}
        for m in man.get("rows", []):
            if m.get("status") != 200 or m.get("truncated") or not m.get("file"): cnt["manifest row truncated or not 200 (dropped)"] += 1; continue
            fp = os.path.join(run, os.path.basename(m["file"]))
            body = json.load((gzip.open if fp.endswith(".gz") else open)(fp, "rt"))
            res[s].update(result_rows(body.get("markets") or [], s, cnt))
    if cnt["manifest row truncated or not 200 (dropped)"]: raise SystemExit("RUN VOID: %d manifest rows missing, so results are missing" % cnt["manifest row truncated or not 200 (dropped)"])
    missing = sorted({s for s, _, _ in lad.values()} - set(runs))
    if missing: raise SystemExit("REFUSED: ladder rows of %s have no results run" % ", ".join(missing))
    return assemble(lad, res, cnt), dict(cnt)
if __name__ == "__main__":
    data, cnt = load(sys.argv[1], dict(a.split("=", 1) for a in sys.argv[2:]))
    print("LADHOUR1 loader: tickers %s, candles %d; drops %s" % ({s: len(v) for s, v in data.items()}, sum(len(m["candles"]) for v in data.values() for m in v), dict(cnt)))
