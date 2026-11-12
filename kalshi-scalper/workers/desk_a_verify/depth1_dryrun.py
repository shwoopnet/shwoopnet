"""DEPTH1 end-to-end DRY RUN on a SYNTHETIC R6 fixture (Desk A, Nov 12 2026). No recorded row is read, no network, nothing written outside a temp dir.
It drives V2's real `scalper.depth1.run()` (the one read) with patched file access, to show the one-command read works end to end on the day and refuses a second time.
  python3 -I depth1_dryrun.py <path to kalshi-scalper dir of V2's branch, containing src/scalper/depth1.py>
Prints the verdict line and the first lines of the result. Random labels: the synthetic outcome has NO edge, so the expected verdict is FALSIFIED (or NOT_ENOUGH_DATA if fewer than 300 windows)."""
import sys, os, io, csv, gzip, random, tempfile, contextlib, time, json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root / "src"))
from scalper import depth1 as D, r6tests as R6
rng = random.Random(7)
def iso(ts): return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
files, cov = {}, []
N_PER = int(os.environ.get("N_PER", "330"))
day0 = datetime(2026, 10, 30, 15, tzinfo=timezone.utc).timestamp()
for ser in D.UNIVERSE:
    for i in range(N_PER):
        close = int(day0 + (i // 22) * 86400 + (i % 22) * 900 + (0 if ser == D.GOLD else 450)); dt = datetime.fromtimestamp(close, timezone.utc)
        run = f"book15r6/{dt:%Y-%m-%d}/0000"; res = rng.choice(["yes", "no"]); tk = f"{ser}-{i}"
        rows = files.setdefault(run, {"book": [], "trades": []})
        mid = rng.uniform(0.3, 0.7)
        for k in range(0, 440):
            t = close - 900 + 2 * k; recv = t * 1000 - 500; bid = round(mid + rng.uniform(-0.01, 0.01), 2)
            r = dict(t_send_ms=recv - 100, t_recv_ms=recv, server_date_header=format_datetime(datetime.fromtimestamp(t, timezone.utc), usegmt=True), ticker=tk, series=ser, close_time=iso(close))
            for L in range(1, 6):
                r[f"yes_bid_px_{L}"] = round(bid - 0.01 * (L - 1), 2); r[f"yes_bid_sz_{L}"] = rng.randint(5, 100)
                r[f"no_bid_px_{L}"] = round(1 - bid - 0.02 - 0.01 * (L - 1), 2); r[f"no_bid_sz_{L}"] = rng.randint(5, 100)
            rows["book"].append({c: r[c] for c in R6.BOOK_COLS})       # column order must equal the recorder schema
        for k in range(8):
            rows["trades"].append(dict(ticker=tk, created_time=iso(close - 300 - 30 * k), yes_price_dollars=round(mid, 2), count_fp=rng.randint(1, 20), taker_outcome_side=rng.choice(["yes", "no"])))
        cov.append((run, dict(ticker=tk, series=ser, close_time=iso(close), polls=440, ok_polls=440, max_gap_ms=2000, tape_pages=1, note="", first_recv_ms=(close - 900) * 1000, last_recv_ms=close * 1000, result=res)))
def blob(path):
    run, name = path.rsplit("/", 1)
    return files.get(run, {}).get("book" if name.startswith("book") else "trades", [])
with tempfile.TemporaryDirectory() as d:
    D.RESULT_TXT, D.RESULT_MD, D.MARKER = Path(d) / "r.txt", Path(d) / "r.md", Path(d) / "started"
    D._blob = blob; D._oicore_held = lambda tk: {t: False for t in tk}
    def history(): raise RuntimeError("history check skipped in the dry run")
    D.history_check = history
    D._coverage = lambda: {(int(R6._ts(r["close_time"])), r["series"]): (run, r) for run, r in cov}
    for h in (D.R6,): pass
    out = io.StringIO()
    with contextlib.redirect_stdout(out): v = D.run(now=D.READ_NOT_BEFORE + 7200)
    print("verdict:", v); print("\n".join(out.getvalue().splitlines()[:6])[:1500])
    out2 = io.StringIO()
    with contextlib.redirect_stdout(out2): v2 = D.run(now=D.READ_NOT_BEFORE + 7300)
    assert v2 is None and "Refusing to run again" in out2.getvalue(); print("second run refused: OK")
    assert D.MARKER.exists() and D.RESULT_TXT.exists()
