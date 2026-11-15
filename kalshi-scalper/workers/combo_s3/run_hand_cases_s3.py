#!/usr/bin/env python3
"""Runs the hand cases of EXPECTED_hand_s3_nov15.md on made-up trees (no Kalshi data). Prints PASS or FAIL per case."""
import contextlib, datetime, importlib.util, io, os, random, re, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
spec = importlib.util.spec_from_file_location("s3", os.path.join(here, "s3_score.py")); s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
from make_s3_fixture import make_tree
def run(root, read, mode="dev"):
    buf = io.StringIO(); old = sys.argv; sys.argv = ["s3_score.py", root, read, mode]
    try:
        with contextlib.redirect_stdout(buf): s3.main()
    finally: sys.argv = old
    return buf.getvalue()
ok = []
# 1 band tolerance (unit)
t = 1000000000000 / 1000; close = datetime.datetime.fromtimestamp(t + 86400, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
base = {"t_recv_ms": "1000000000000", "ticker": "X", "event_ticker": "E", "yes_bid_size": "5", "volume": "3", "legs": "3", "close_time": close}
q = lambda na: bool(s3.qualifies(dict(base, no_ask=na)))
cents = all(q("%.2f" % (c / 100)) == (59 <= c <= 89) for c in range(1, 99))
ok.append(("1", cents and q("0.8900000001") and not q("0.89000001") and q("0.5899999999") and not q("0.5899")))
d = {}
for kind in ("T120", "K", "K0", "B"): d[kind] = tempfile.mkdtemp(); make_tree(d[kind], kind)
o = run(d["T120"], "2026-11-30T12:00:00Z")
ok.append(("2", "paper fills 120 | due 120 | settled 100 | unresolved 20" in o and "wins 90 | cash PF 2.09 | net per dollar +0.109" in o and "LABEL: NOT_ENOUGH_DATA, description only" in o and "paper edge shown" not in o and "bar not met" not in o and "KILLED" not in o.split("== NO WEATHER")[0]))
o = run(d["K"], "2026-11-30T12:00:00Z").split("== NO WEATHER")[0]
o0 = run(d["K0"], "2026-11-30T12:00:00Z").split("== NO WEATHER")[0]
ok.append(("3", "would read KILLED (description only): running paper net fell under $-40 at settled fill 21" in o and "KILLED: running" not in o.replace("would read KILLED", "") and "LABEL: KILLED" not in o0 and "KILLED: running paper net fell under $-40 at settled fill 21" in o0 and "(description only)" not in o0))
# 4 bootstrap pin, tree B (all resolved, 12 losses), independent implementation
ob = run(d["B"], "2026-11-30T12:00:00Z").split("== NO WEATHER")[0]
cost = 0.80 + 0.07 * 0.80 * 0.20; win, loss = 1 - cost, -cost
fills = []   # (close date, net) in ticker order, losses at ranks 9, 18 ... 108
for i in range(1, 121): fills.append(("2026-11-14" if i <= 40 else "2026-11-16", loss if i % 9 == 0 else win))
dates = sorted({x[0] for x in fills}); rng = random.Random(20261112)
def ppd(rows): return sum(n for _, n in rows) / (len(rows) * cost)
boots = sorted(ppd([f for dt in [rng.choice(dates) for _ in dates] for f in fills if f[0] == dt]) for _ in range(2000))
want = boots[100]; m = re.search(r"bootstrap 5th percentile by close date ([+-]?[0-9.]+)", ob)
ok.append(("4", bool(m) and abs(float(m.group(1)) - want) < 5e-4))
# 5 monitor, tree T120, read 2026-11-17T00:00Z
om = run(d["T120"], "2026-11-17T00:00:00Z", "monitor")
ok.append(("5", "MONITOR, not the registered verdict; the Nov 26 read is the verdict" in om and "due 40 | settled 36 | unresolved 4 | wins 32 | cash PF 1.86 | net per dollar +0.096" in om and "LABEL" not in om and "KILLED" not in om and "bootstrap" not in om))
# 6 the registered read is still refused early
ok.append(("6", "REFUSED" in run(d["T120"], "2026-11-17T00:00:00Z")))
for k, v in ok: print(k, "PASS" if v else "FAIL")
sys.exit(0 if all(v for _, v in ok) else 1)
