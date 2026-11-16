"""ETHLATE1 loader (Desk B, Nov 16 2026). Offline. Reads a checkout of quote-data (quotes/<date>/<HHMM>/ladder.csv.gz) and ONE landed ETHD_RESULTS2 run folder.
REFUSES unless HELDOUT_PULL_RUNS.md carries a line with the mark, "ethlate1_load.py" and this file's own sha256 (no flag, no env var).
Wall: only date directories 2026-10-27 to 2026-11-15 are listed; each row's ticker is read FIRST (KXETHD- only; any other series dropped and counted, nothing else of the row parsed), then close_time (outside [2026-10-28T00:00Z, 2026-11-16T00:00Z) dropped and counted), then status; results from the run only for kept rows: yes, no or void.
Output: {"KXETHD": [{series, ticker, close, result, candles: [(end_ts, yes_bid, yes_ask, last, volume, oi)]}]} (the last ladder row of each clock minute; last None, volume 0, oi 0).
Expected figures: EXPECTED_ethlate1_load_nov16.md."""
import os, sys, csv, gzip, io, json, hashlib, calendar, time, collections
HERE = os.path.dirname(os.path.abspath(__file__))
START = 1793145600      # 2026-10-28T00:00Z
CUT = 1794787200        # 2026-11-16T00:00Z
DIRS = tuple("2026-10-%02d" % d for d in (27, 28, 29, 30, 31)) + tuple("2026-11-%02d" % d for d in range(1, 16))
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md"); ALLOW_MARK = "readable ONLY by Desk B's ETHLATE1 loader"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def check_run_name(run):
    """the run folder must be <...>/ETHD_RESULTS2/<stamp>; returns the stamp."""
    p = os.path.abspath(run)
    if os.path.basename(os.path.dirname(p)) != "ETHD_RESULTS2": raise SystemExit("REFUSED: %s is not a run folder of ETHD_RESULTS2" % run)
    return os.path.basename(p)
def refuse_unless_allowed(run_name):
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "ethlate1_load.py" in line and self_sha() in line and run_name in line: return
    raise SystemExit("REFUSED: no allow-list line names ethlate1_load.py with this file's sha256 %s and the run %s" % (self_sha(), run_name))
def iso(s):
    try: return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception: return None
def in_window(close_s):
    t = iso(close_s) if isinstance(close_s, str) else None
    return t if t is not None and START <= t < CUT else None
def opened(path): return csv.DictReader(io.TextIOWrapper(gzip.open(path), encoding="utf-8", newline=""))
def ladder_rows(rows, cnt):
    """close_time FIRST -> {ticker: (close, [(t_recv_s, bid, ask)])} for KXETHD rows inside the window."""
    out = {}
    for r in rows:
        if not r["ticker"].startswith("KXETHD-"): cnt["ticker outside the wall (dropped)"] += 1; continue      # ticker FIRST: no other column of a wrong-series row is parsed
        c = in_window(r["close_time"])
        if c is None: cnt["ladder row dropped by the cut or no close"] += 1; continue
        if r["status"] != "active": cnt["ladder row not active (dropped)"] += 1; continue
        try: t = int(r["t_recv_ms"]) / 1000.0; b = float(r["yes_bid"]); a = float(r["yes_ask"])
        except (ValueError, KeyError): cnt["ladder row unreadable (dropped)"] += 1; continue
        out.setdefault(r["ticker"], (c, []))[1].append((t, b, a))
    return out
def candles_of(close, rows, cnt):
    """the last row of each clock minute; end_ts = the minute's end; a candle ending after the close is dropped and counted."""
    last = {}
    for t, b, a in sorted(rows):
        end = (int(t) // 60 + 1) * 60
        last[end] = (end, b, a, None, 0, 0)
    out = []
    for end in sorted(last):
        if end > close: cnt["candle after close (dropped)"] += 1; continue
        out.append(last[end])
    return out
def result_rows(rows, cnt):
    """results from the ETHD_RESULTS answers: close_time first, ticker wall, then result (yes or no only)."""
    out = {}
    for r in rows:
        if not r["ticker"].startswith("KXETHD-"): cnt["result ticker outside the wall (dropped)"] += 1; continue   # ticker FIRST: a KXBTCD outcome is never read
        c = in_window(r["close_time"])
        if c is None: cnt["result row outside the window (dropped)"] += 1; continue
        if r["result"] not in ("yes", "no", "void"): cnt["result not yes, no or void (dropped)"] += 1; continue
        out[r["ticker"]] = r["result"]
    return out
def assemble(lad, res, cnt):
    out = []
    for tk in sorted(lad):
        close, rows = lad[tk]
        if tk not in res: cnt["no result (dropped)"] += 1; continue
        out.append({"series": "KXETHD", "ticker": tk, "close": close, "result": res[tk], "candles": candles_of(close, rows, cnt)})
    return {"KXETHD": out}
def load(base, run):
    refuse_unless_allowed(check_run_name(run))
    cnt = collections.Counter(); lad = {}
    for d in DIRS:
        dp = os.path.join(base, "quotes", d)
        if not os.path.isdir(dp): cnt["missing date directory"] += 1; continue
        for runname in sorted(os.listdir(dp)):
            p = os.path.join(dp, runname, "ladder.csv.gz")
            if not os.path.exists(p): continue
            for tk, (c, rows) in ladder_rows(opened(p), cnt).items(): lad.setdefault(tk, (c, []))[1].extend(rows)
    res = {}
    man = json.load(open(os.path.join(run, "manifest.json")))
    for m in man.get("rows", []):
        if m.get("status") != 200 or m.get("truncated") or not m.get("file"): cnt["manifest row truncated or not 200 (dropped)"] += 1; continue
        fp = os.path.join(run, os.path.basename(m["file"]))
        body = json.load((gzip.open if fp.endswith(".gz") else open)(fp, "rt"))
        res.update(result_rows(body.get("markets") or [], cnt))
    if cnt["manifest row truncated or not 200 (dropped)"]: raise SystemExit("RUN VOID: %d manifest rows missing, so KXETHD results are missing" % cnt["manifest row truncated or not 200 (dropped)"])
    return assemble(lad, res, cnt), dict(cnt)
if __name__ == "__main__":
    data, cnt = load(sys.argv[1], sys.argv[2])
    print("ETHLATE1 loader: tickers %d, candles %d; drops %s" % (len(data["KXETHD"]), sum(len(m["candles"]) for m in data["KXETHD"]), dict(cnt)))
