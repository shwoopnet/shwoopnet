#!/usr/bin/env python3
"""1e-9 compare of the PERPSCALP2 first build (engine/perpscalp2.py) against the Testing Desk's second build on THEIR invented fixture (Nov 16, 2026).
Usage: python3 -I compare_second_build.py <fixture.json.gz> <their_lines.txt> <engine dir>
The fixture {data, funding, ticks} is written in the perp-data layout (kalshi1m and funding per-day files); the first build runs unchanged with NAMES and LMAX patched
to the fixture's three invented names (ticks come from the plugin's own rule and are printed beside the fixture's)."""
import csv, gzip, json, math, os, sys, tempfile, time
fx, theirs, eng = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, eng)
import perpscalp2 as P

d = json.load(gzip.open(fx, "rt"))
root = tempfile.mkdtemp()
os.makedirs(os.path.join(root, "kalshi1m")); os.makedirs(os.path.join(root, "funding"))
rows = []
for n, c in d["data"].items():
    for t, (b, a, v) in c.items():
        rows.append([n, int(t), repr(b), repr(a), repr(v)])
rows.sort(key=lambda r: (r[1], r[0]))
with gzip.open(os.path.join(root, "kalshi1m", "2026-11-10.csv.gz"), "wt", newline="") as f:
    w = csv.writer(f); w.writerow(["ticker", "end_period_ts", "bid_close", "ask_close", "volume"]); w.writerows(rows)
with gzip.open(os.path.join(root, "funding", "2026-11-10.csv.gz"), "wt", newline="") as f:
    w = csv.writer(f); w.writerow(["ticker", "funding_time", "funding_rate", "mark_price"])
    for n, fu in d["funding"].items():
        for t, r in fu.items():
            w.writerow([n, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t))), repr(r), "1"])
P.NAMES = tuple(d["data"])
# the fixture's candles run past the development end (1794787199) and carry their own tick sizes: the compare isolates the rules, so the end epoch is lifted to the
# fixture's last candle and the fixture's ticks are used (the loader's cutoff and the plugin's own tick rule are tested in test_perpscalp2.py)
P.END_EPOCH = max(int(t) for c in d["data"].values() for t in c)
_ticks = dict(d["ticks"])
P.tick_of = lambda c, _t=_ticks: _t[next(n for n, cc in DATA.items() if cc is c)]
DATA = {}
P.LMAX = {n: 5.0 for n in d["data"]}
_load = P.load
def _wrapped(*a, **k):
    c, fu = _load(*a, **k)
    DATA.update(c)
    return c, fu
P.load = _wrapped
out = P.run(root, 6290660)
print("my counts:", {k: v for k, v in out["counts"].items() if k not in ("load", "manifest_sha256")})
print("my ticks:", out["counts"]["ticks"], " their ticks:", d["ticks"])
mine = {}
for r in out["cells"]:
    cell = tuple(r["cell"])
    for col, m in (("TT", r["TT"]), ("TS", r["TS"])) + tuple((k, v) for k, v in r["maker"].items()):
        mine[(cell, col)] = m
diffs, checked, nonempty = [], 0, 0
for l in open(theirs).read().split("\n"):
    if not l.strip():
        continue
    t = json.loads(l)
    key = (tuple(t["cell"]), t["col"])
    m = mine.get(key)
    if m is None:
        diffs.append((key, "missing in first build")); continue
    checked += 1
    nonempty += 1 if t["n"] else 0
    for f in ("n", "days", "pf", "h1", "h2", "z", "mean_bps", "spanning_funding"):
        a, b = t[f], m[f]
        if a is None or b is None or isinstance(a, str) or isinstance(b, str):
            if not (a is None and b is None):
                diffs.append((key, f, a, b))
        elif isinstance(a, int) and isinstance(b, int):
            if a != b: diffs.append((key, f, a, b))
        elif math.isinf(a) or math.isinf(b):
            if a != b: diffs.append((key, f, a, b))
        elif not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9):
            diffs.append((key, f, a, b))
print("lines compared:", checked, "with trades:", nonempty, "of which cells x columns in first build:", len(mine))
print("differences:", len(diffs))
for x in diffs[:int(os.environ.get("SHOW", "40"))]:
    print(" ", x)
