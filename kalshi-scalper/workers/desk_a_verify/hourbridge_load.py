"""HOURBRIDGE1 loader (Desk A, Nov 16 2026), written to Auditor B's wall. Offline; reads recorder files from a checkout of quote-data: <base>/quotes/<date>/<HHMM>/{ladder,quotes,results}.csv.gz.
REFUSES unless HELDOUT_PULL_RUNS.md carries a line with the mark, "hourbridge_load.py" and this file's own sha256 (no flag, no env var).
Wall: (i) only date directories 2026-10-27 to 2026-11-01 are opened (a directory dated 2026-11-02 or later is never listed into); (ii) every file's close_time column is read FIRST and a close before 2026-10-28T00:00Z or at or after 2026-11-02T00:00Z (epoch 1793577600) is dropped and counted before any other column; (iii) ticker wall KXBTCD and KXBTC15M; (iv) `result` read only for kept rows; (v) the 15 minute quotes (no close_time column) only for tickers whose close_time came from results.csv inside the window.
  python3 -I hourbridge_load.py <quote-data checkout>   prints counts."""
import os, sys, csv, gzip, io, hashlib, calendar, time, collections, json
HERE = os.path.dirname(os.path.abspath(__file__))
START = 1793145600      # 2026-10-28T00:00Z
CUT = 1793577600        # 2026-11-02T00:00Z
DIRS = ("2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30", "2026-10-31", "2026-11-01")
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md"); ALLOW_MARK = "readable ONLY by Desk A's HOURBRIDGE1 loader"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def refuse_unless_allowed():
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "hourbridge_load.py" in line and self_sha() in line: return
    raise SystemExit("REFUSED: no allow-list line names hourbridge_load.py with this file's sha256 %s" % self_sha())
def iso(s):
    try: return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception: return None
def opened(path):
    return csv.DictReader(io.TextIOWrapper(gzip.open(path), encoding="utf-8", newline=""))
def in_window(close_s):
    t = iso(close_s) if isinstance(close_s, str) else None
    return t if t is not None and START <= t < CUT else None
def ladder_rows(rows, cnt):
    """rows with close_time FIRST: -> [(close, ticker, strike, t_recv_ms, bid, ask)] for KXBTCD rows inside the window."""
    out = []
    for r in rows:
        c = in_window(r["close_time"])
        if c is None: cnt["ladder row outside the window (dropped)"] += 1; continue
        if not r["ticker"].startswith("KXBTCD-"): cnt["ladder ticker outside the wall (dropped)"] += 1; continue
        if r["status"] != "active": cnt["ladder row not active (dropped)"] += 1; continue
        try: out.append((c, r["ticker"], float(r["strike"]), int(r["t_recv_ms"]), float(r["yes_bid"]), float(r["yes_ask"])))
        except (ValueError, KeyError): cnt["ladder row unreadable (dropped)"] += 1
    return out
def result_rows(rows, cnt):
    """results.csv: close_time first; ticker wall KXBTC15M; result only for kept rows -> {ticker: (close, result)}."""
    out = {}
    for r in rows:
        c = in_window(r["close_time"])
        if c is None: cnt["result row outside the window (dropped)"] += 1; continue
        if not r["ticker"].startswith("KXBTC15M-"): cnt["result ticker outside the wall (dropped)"] += 1; continue
        out[r["ticker"]] = (c, r["result"])
    return out
def quote_rows(rows, keep, cnt):
    out = []
    for r in rows:
        if r["ticker"] not in keep: cnt["15m quote ticker not kept (dropped)"] += 1; continue
        try: out.append((r["ticker"], float(r["strike"]), int(r["t_recv_ms"]), float(r["yes_bid"]), float(r["yes_ask"])))
        except (ValueError, KeyError): cnt["15m quote row unreadable (dropped)"] += 1
    return out
def load(base):
    refuse_unless_allowed()
    cnt = collections.Counter(); lad = []; res = {}; quotes = []; dirs = []
    for d in DIRS:
        dp = os.path.join(base, "quotes", d)
        if not os.path.isdir(dp): cnt["missing date directory"] += 1; continue
        for run in sorted(os.listdir(dp)): dirs.append(os.path.join(dp, run))
    for rp in dirs:
        f = os.path.join(rp, "results.csv.gz")
        if os.path.exists(f): res.update(result_rows(opened(f), cnt))
    for rp in dirs:
        f = os.path.join(rp, "ladder.csv.gz")
        if os.path.exists(f): lad += ladder_rows(opened(f), cnt)
        f = os.path.join(rp, "quotes.csv.gz")
        if os.path.exists(f): quotes += quote_rows(opened(f), res, cnt)
    # events: every hourly close H (minute 00) with a ladder and a 15 minute market closing at H
    by_h = collections.defaultdict(lambda: collections.defaultdict(list))
    for c, tk, k, t, b, a in lad:
        if c % 3600 == 0: by_h[c][k].append((t, b, a))
    q15 = {tk: [] for tk in res}; strike15 = {}
    for tk, k, t, b, a in quotes: q15[tk].append((t, b, a)); strike15[tk] = k
    by_close = {c: tk for tk, (c, _) in res.items()}
    events = []
    for h in sorted(by_h):
        tk = by_close.get(h)
        if tk is None or tk not in strike15: cnt["hour without a 15m market or quotes"] += 1; continue
        r = res[tk][1]; events.append({"H": h, "ladder": dict(by_h[h]), "q15": {"strike": strike15[tk], "rows": q15[tk]}, "result": r if r in ("yes", "no") else "void"})
    cnt["events built"] = len(events)
    return events, dict(cnt)
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    ev, c = load(sys.argv[1]); print(json.dumps({"counts": c, "loader_sha256": self_sha()}, indent=1))
