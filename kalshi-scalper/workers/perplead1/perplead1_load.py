"""PERPLEAD1 loader (Desk B, Nov 16 2026; DRAFT, unrun, unsigned). Offline. Reads a checkout of quote-data (quotes/<date>/<HHMM>/ladder.csv.gz, KXETHD only) and the landed perp candle runs PERPETH1M_W8 and PERPETH1M_W11 (KXETHPERP 1 minute candles).
REFUSES unless HELDOUT_PULL_RUNS.md carries, for EACH run, a line with the mark, "perplead1_load.py", this file's own sha256 and the run stamp (no flag, no env var). Wall: a ladder row's ticker is read FIRST (KXETHD- only), then close_time inside [START, CUT), then status active.
A perp request row is accepted only if its path names KXETHPERP (read first) and its start_ts lies inside the window; a manifest row with status other than 200, truncated or without a file voids the run.
Output: events [{close, day, strikes: {look: [(strike, mid)]}, perp: {look: (bid, ask)}}] with look in m120, m60, m0 (the minute candles ending 120 s, 60 s and 0 s before the hourly close). Expected figures: EXPECTED_perplead1_load_nov16.md."""
import os, sys, csv, gzip, io, json, hashlib, calendar, time, collections
HERE = os.path.dirname(os.path.abspath(__file__))
START = 1793145600; CUT = 1794787200         # 2026-10-28T00:00Z, 2026-11-16T00:00Z
DIRS = tuple("2026-10-%02d" % d for d in (27, 28, 29, 30, 31)) + tuple("2026-11-%02d" % d for d in range(1, 16))
RUNS = ("PERPETH1M_W8", "PERPETH1M_W11"); LOOKS = (("m120", 120), ("m60", 60), ("m0", 0))
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md"); ALLOW_MARK = "readable ONLY by Desk B's PERPLEAD1 loader"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def check_run_name(run):
    p = os.path.abspath(run); par = os.path.basename(os.path.dirname(p))
    if par not in RUNS: raise SystemExit("REFUSED: %s is not a run folder of %s" % (run, " or ".join(RUNS)))
    return os.path.basename(p)
def refuse_unless_allowed(run_name):
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "perplead1_load.py" in line and self_sha() in line and run_name in line: return
    raise SystemExit("REFUSED: no allow-list line names perplead1_load.py with this file's sha256 %s and the run %s" % (self_sha(), run_name))
def iso(s):
    try: return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception: return None
def in_window(close_s):
    t = iso(close_s) if isinstance(close_s, str) else None
    return t if t is not None and START <= t < CUT else None
def opened(path): return csv.DictReader(io.TextIOWrapper(gzip.open(path), encoding="utf-8", newline=""))
def ladder_rows(rows, cnt):
    """ticker FIRST -> {(close, ticker): (strike, [(t_recv_s, mid)])}."""
    out = {}
    for r in rows:
        if not r["ticker"].startswith("KXETHD-"): cnt["ticker outside the wall (dropped)"] += 1; continue
        c = in_window(r["close_time"])
        if c is None: cnt["ladder row dropped by the cut or no close"] += 1; continue
        if r["status"] != "active": cnt["ladder row not active (dropped)"] += 1; continue
        try: t = int(r["t_recv_ms"]) / 1000.0; mid = (float(r["yes_bid"]) + float(r["yes_ask"])) / 2; k = float(r["strike"])
        except (ValueError, KeyError): cnt["ladder row unreadable (dropped)"] += 1; continue
        if not (0 < float(r["yes_bid"]) < float(r["yes_ask"]) < 1): cnt["ladder row not two sided (dropped)"] += 1; continue
        out.setdefault((c, r["ticker"]), (k, []))[1].append((t, mid))
    return out
def perp_candles(body, row, cnt):
    """{end_ts: (bid_close, ask_close)} of one answer; the request row's path is read first."""
    if "/KXETHPERP/" not in str(row.get("path", "")): cnt["perp request outside the wall (dropped)"] += 1; return {}
    p = row.get("params") or {}
    if not (START <= int(p.get("start_ts", -1)) < CUT): cnt["perp request outside the window (dropped)"] += 1; return {}
    out = {}
    for c in body.get("candlesticks") or []:
        try: e = int(c["end_period_ts"]); b = float(c["bid"]["close"]); a = float(c["ask"]["close"])
        except (KeyError, TypeError, ValueError): cnt["perp candle unreadable (dropped)"] += 1; continue
        if not (START <= e <= CUT) : cnt["perp candle outside the window (dropped)"] += 1; continue
        if not (0 < b < a): cnt["perp candle not two sided (dropped)"] += 1; continue
        out[e] = (b, a)
    return out
def assemble(lad, perp, cnt):
    """per event (close): for each look the last row of the minute ending at close - sec of every strike; perp candle ending at the same minute."""
    by_close = collections.defaultdict(dict)
    for (c, tk), (k, rows) in lad.items(): by_close[c][tk] = (k, rows)
    out = []
    for c in sorted(by_close):
        strikes = {}; pp = {}
        for name, sec in LOOKS:
            end = c - sec; mids = []
            for tk, (k, rows) in by_close[c].items():
                m = [(t, v) for t, v in rows if (int(t) // 60 + 1) * 60 == end]
                if m: mids.append((k, sorted(m)[-1][1]))
            strikes[name] = mids
            if end in perp: pp[name] = perp[end]
        out.append({"close": c, "day": time.strftime("%Y-%m-%d", time.gmtime(c)), "strikes": strikes, "perp": pp})
    return out
def load(base, runs):
    for run in runs: refuse_unless_allowed(check_run_name(run))
    cnt = collections.Counter(); lad = {}
    for d in DIRS:
        dp = os.path.join(base, "quotes", d)
        if not os.path.isdir(dp): cnt["missing date directory"] += 1; continue
        for runname in sorted(os.listdir(dp)):
            p = os.path.join(dp, runname, "ladder.csv.gz")
            if not os.path.exists(p): continue
            for key, (k, rows) in ladder_rows(opened(p), cnt).items(): lad.setdefault(key, (k, []))[1].extend(rows)
    perp = {}
    for run in runs:
        man = json.load(open(os.path.join(run, "manifest.json")))
        for m in man.get("rows", []):
            if m.get("status") != 200 or m.get("truncated") or not m.get("file"): cnt["manifest row truncated or not 200 (dropped)"] += 1; continue
            fp = os.path.join(run, os.path.basename(m["file"]))
            body = json.load((gzip.open if fp.endswith(".gz") else open)(fp, "rt"))
            perp.update(perp_candles(body, m, cnt))
    if cnt["manifest row truncated or not 200 (dropped)"]: raise SystemExit("RUN VOID: %d manifest rows missing, so perp candles are missing" % cnt["manifest row truncated or not 200 (dropped)"])
    return assemble(lad, perp, cnt), dict(cnt)
if __name__ == "__main__":
    ev, cnt = load(sys.argv[1], sys.argv[2:])
    print("PERPLEAD1 loader: events %d, with m120 perp %d; drops %s" % (len(ev), sum(1 for e in ev if "m120" in e["perp"]), dict(cnt)))
