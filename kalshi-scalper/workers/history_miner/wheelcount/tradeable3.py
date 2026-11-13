"""Tradeable-series re-count on one wheelbook run folder from the FIXED recorder. Per series and tier: markets, market-minutes before the
market's own close (coverage close_time, which the fixed recorder takes from the market read), share of minutes whose latest book row is
two-sided at the top (yes bid > 0, no bid > 0, yes bid < 1 - no bid; a 0.00 bid is no side), median and p90 spread. A row older than
60 s at the minute end is counted stale (not two-sided) in the strict column. Counts and spreads only; no result is read."""
import csv, gzip, os, sys, bisect, statistics, importlib.util
from datetime import datetime, timezone
run = sys.argv[1]
spec = importlib.util.spec_from_file_location("rwb", sys.argv[2]); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
rd = lambda f: list(csv.DictReader(gzip.open(os.path.join(run, f), "rt")))
iso = lambda s: datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp() if s else None
cov = rd("coverage.csv.gz")
rows = {}
for f in ("book_fast.csv.gz", "book_slow.csv.gz"):
    for r in rd(f): rows.setdefault(r["ticker"], []).append(r)
for t in rows: rows[t].sort(key=lambda r: int(r["t_recv_ms"]))
run_end = max(int(p["t_recv_ms"]) for p in rd("polls.csv.gz")) / 1000.0
def f_(x):
    try: return float(x)
    except: return None
out = {}
no_rows = {}
for c in cov:
    s, t = c["series"], c["ticker"]
    rs = rows.get(t)
    if not rs:
        no_rows[s] = no_rows.get(s, 0) + 1; continue
    times = [int(r["t_recv_ms"]) / 1000.0 for r in rs]
    o = iso(c["open_time"]); cl = iso(c["close_time"])
    lo = max(int(c["first_seen_ms"]) / 1000.0, times[0])
    hi = min(run_end, cl if cl is not None else run_end)
    m = int(-(-lo // 60) * 60)
    while m + 60 <= hi:
        tier = R.tier_for(s, t, o, m + 60)
        if tier:
            st = out.setdefault((s, tier), {"mm": 0, "two": 0, "strict": 0, "sp": [], "mk": set()})
            j = bisect.bisect_right(times, m + 60) - 1
            b = rs[j]; yb, nb = f_(b["yes_bid_px_1"]), f_(b["no_bid_px_1"])
            st["mm"] += 1; st["mk"].add(t)
            if yb is not None and nb is not None and yb > 0 and nb > 0 and yb < 1 - nb - 1e-9:
                st["two"] += 1; st["sp"].append(round(1 - nb - yb, 4))
                if m + 60 - times[j] <= 60: st["strict"] += 1
        m += 60
print("run", run, "coverage rows", len(cov), "markets with no book row by series", no_rows)
for (s, tier), st in sorted(out.items()):
    sp = sorted(st["sp"])
    print("%-18s %-5s markets %3d  market-minutes %5d  two-sided %5.1f%%  strict(<=60s) %5.1f%%  median spread %s  p90 %s  spread<=4c %5.1f%%" % (s, tier, len(st["mk"]), st["mm"], 100.0*st["two"]/st["mm"], 100.0*st["strict"]/st["mm"], statistics.median(sp) if sp else None, sp[int(.9*len(sp))] if sp else None, 100.0*sum(1 for x in sp if x<=0.04+1e-9)/st["mm"]))
