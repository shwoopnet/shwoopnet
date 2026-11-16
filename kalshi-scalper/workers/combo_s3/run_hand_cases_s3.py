#!/usr/bin/env python3
"""Runs the hand cases of EXPECTED_hand_s3_nov15.md on made-up trees (no Kalshi data). Prints PASS or FAIL per case."""
import contextlib, datetime, importlib.util, io, os, random, re, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
spec = importlib.util.spec_from_file_location("s3", os.path.join(here, "s3_score.py")); s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
from make_s3_fixture import make_tree, make_lg_tree
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
o = run(d["T120"], "2026-12-20T12:00:00Z")
ok.append(("2", "paper fills 120 | due 120 | settled 100 | unresolved 20" in o and "wins 90 | cash PF 2.09 | net per dollar +0.109" in o and "LABEL: NOT_ENOUGH_DATA, description only" in o and "paper edge shown" not in o and "bar not met" not in o and "KILLED" not in o.split("== NO WEATHER")[0]))
o = run(d["K"], "2026-12-20T12:00:00Z").split("== NO WEATHER")[0]
o0 = run(d["K0"], "2026-12-20T12:00:00Z").split("== NO WEATHER")[0]
ok.append(("3", "would read KILLED (description only): running paper net fell under $-40 at settled fill 21" in o and "KILLED: running" not in o.replace("would read KILLED", "") and "LABEL: KILLED" not in o0 and "KILLED: running paper net fell under $-40 at settled fill 21" in o0 and "(description only)" not in o0))
# 4 bootstrap pin, tree B (all resolved, 12 losses), independent implementation
ob = run(d["B"], "2026-12-20T12:00:00Z").split("== NO WEATHER")[0]
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
ok.append(("5", "MONITOR, counts only, not the registered verdict; the Dec 12 read is the verdict" in om and "monitor: paper fills 120 | due 40 | settled 36 | unresolved 4" in om and not any(w in om for w in ("wins", "PF", "net per dollar", "LABEL", "KILLED", "bootstrap"))))
# 6 the registered read is still refused early
ok.append(("6", "REFUSED" in run(d["T120"], "2026-11-17T00:00:00Z")))
# 7 cut leg lists (Auditor B, line 9)
ok.append(("7a", s3.leg_series("KXA-1:yes|KXB-2:no") == (["KXA", "KXB"], "complete") and s3.leg_series("KXA-1:yes|KXB-2:no|...") == (["KXA", "KXB"], "incomplete") and s3.leg_series("") == ([], "unknown")))
s3.LEGS.clear(); lg = tempfile.mkdtemp(); make_lg_tree(lg); ol = run(lg, "2026-12-20T12:00:00Z")
nw = ol.split("== NO WEATHER")[1]
ok.append(("7b", "paper fills 4 | due 4 | settled 4" in ol and "paper fills with leg tickers stored 4 | leg unknown 0 | legs incomplete 2 | with a weather leg 1" in ol
           and "..." not in ol.split("== ALL")[0].split("leg series seen")[1] and "settled 2" in nw.splitlines()[0] and "== ALL COMBOS (the registered line): settled 4" in ol))
# 8 window extended to Dec 5
def rowat(iso):
    t = int(datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)
    return {"t_recv_ms": str(t), "ticker": "X", "event_ticker": "E", "yes_bid_size": "5", "volume": "3", "legs": "3", "close_time": "2026-12-10T10:00:00Z", "no_ask": "0.79"}
def inw(iso):
    f = s3.qualifies(rowat(iso)); return bool(f) and s3.ts(s3.START_UTC) <= f["t"] < s3.ts(s3.DEV_END_UTC)
ok.append(("8a", inw("2026-12-05T23:59:59Z") and not inw("2026-12-06T00:00:00Z")))
ok.append(("8b", "REFUSED" in run(d["T120"], "2026-12-11T23:59:59Z") and "REFUSED" not in run(d["T120"], "2026-12-12T00:00:00Z") and "REFUSED" in run(d["T120"], "2026-12-20T12:00:00Z", "heldout")))
for k, v in ok: print(k, "PASS" if v else "FAIL")
sys.exit(0 if all(v for _, v in ok) else 1)
