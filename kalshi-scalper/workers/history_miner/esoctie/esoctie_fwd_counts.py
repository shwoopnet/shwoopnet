"""ESOCTIE forward place: counts from the wheel book recorder's files only (no result, no base rate, no gap). Eligible = Tie opened 10 to 240 min before S, all three two-sided at the
latest poll at or before D_k = S - 60k (k = 1..10, first k that works), the poll at D being within 10 s before D. Fill-checked = eligible and the Tie's YES side (its NO bids, ask = 1 - price)
offers 10 contracts at or under the Tie ask + 0.01 at the D poll and at the next fast poll at most 4 s later."""
import csv, gzip, os, sys, bisect, importlib.util
from datetime import datetime, timezone
run = sys.argv[1]
spec = importlib.util.spec_from_file_location("rwb", sys.argv[2]); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
rd = lambda f: list(csv.DictReader(gzip.open(os.path.join(run, f), "rt")))
iso = lambda s: datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
cov = [r for r in rd("coverage.csv.gz") if r["series"] == "KXESOCCERGAME"]
rows = {}
for f in ("book_fast.csv.gz", "book_slow.csv.gz"):
    for r in rd(f):
        if r["ticker"].startswith("KXESOCCERGAME"): rows.setdefault(r["ticker"], []).append(r)
for t in rows: rows[t].sort(key=lambda r: int(r["t_recv_ms"]))
fast = sorted(int(p["t_recv_ms"]) / 1000.0 for p in rd("polls.csv.gz") if p["tier"] == "fast")
run0, run1 = fast[0], fast[-1]
F = lambda x: float(x) if x not in ("", None) else None
def book_at(t, ts):
    rs = rows.get(t) or []
    i = bisect.bisect_right([int(r["t_recv_ms"]) / 1000.0 for r in rs], ts) - 1
    return rs[i] if i >= 0 else None
def two(b):
    if b is None: return False
    yb, nb = F(b["yes_bid_px_1"]), F(b["no_bid_px_1"])
    return yb is not None and nb is not None and 0 < yb < 1 - nb < 1
def offers(b, limit, n=10):
    tot = 0.0
    for i in range(1, 6):
        p, q = F(b["no_bid_px_%d" % i]), F(b["no_bid_sz_%d" % i])
        if p is None or q is None: break
        if 1 - p <= limit + 1e-9: tot += q
    return tot >= n
ev = {}
for c in cov: ev.setdefault(c["event_ticker"], []).append(c)
cnt = {"events_with_D_in_run": 0, "not_three_markets": 0, "open_guard_fail": 0, "no_poll_at_D": 0, "not_two_sided": 0, "eligible": 0, "fill_checked": 0, "no_second_poll_4s": 0}
for e, cs in ev.items():
    S = R.start_epoch(e + "-X")
    if S is None: continue
    D = S - 60
    if not (run0 + 600 <= D <= run1 - 5): continue
    cnt["events_with_D_in_run"] += 1
    tie = [c for c in cs if c["ticker"].endswith("-TIE")]
    if len(cs) != 3 or len(tie) != 1: cnt["not_three_markets"] += 1; continue
    o = iso(tie[0]["open_time"]) if tie[0]["open_time"] else None
    if o is None or not (S - 240 * 60 <= o <= S - 600): cnt["open_guard_fail"] += 1; continue
    i = bisect.bisect_right(fast, D) - 1
    if i < 0 or fast[i] < D - 10: cnt["no_poll_at_D"] += 1; continue
    ok = None
    for k in range(1, 11):
        Dk = S - 60 * k
        bs = [book_at(c["ticker"], Dk) for c in cs]
        if all(two(b) for b in bs): ok = Dk; break
    if ok is None: cnt["not_two_sided"] += 1; continue
    cnt["eligible"] += 1
    tb = book_at(tie[0]["ticker"], ok); ask = round(1 - F(tb["no_bid_px_1"]), 4); limit = round(ask + 0.01, 4)
    if i + 1 >= len(fast) or fast[i + 1] - fast[i] > 4: cnt["no_second_poll_4s"] += 1; continue
    b1, b2 = book_at(tie[0]["ticker"], fast[i]), book_at(tie[0]["ticker"], fast[i + 1])
    if b1 is not None and b2 is not None and offers(b1, limit) and offers(b2, limit): cnt["fill_checked"] += 1
hrs = (run1 - run0 - 600) / 3600.0
print(cnt, "hours with D countable %.2f" % hrs, "eligible per 21 days %.0f" % (cnt["eligible"] / hrs * 24 * 21), "fill-checked per 21 days %.0f" % (cnt["fill_checked"] / hrs * 24 * 21))
