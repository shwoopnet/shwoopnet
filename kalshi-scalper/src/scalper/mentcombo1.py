"""MENTCOMBO1 (workers/MENTCOMBO1_PROTOCOL.md). Simulation from singles. Local data only."""
import json, glob, hashlib, itertools, math, collections, datetime, sys
from statistics import NormalDist
m = json.load(open("data/ment1/markets.json")); c = {}
for f in glob.glob("data/ment1/candles_*.json"): c.update(json.load(open(f)))
ts = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
ev = collections.defaultdict(list); first = {}
for t, d in m.items():
    cl = ts(d["close"]); first[d["ev"]] = min(first.get(d["ev"], 9e18), cl)
    q = [x for x in c.get(t, []) if x[0] <= cl - 14400 and x[1] is not None and x[2] is not None and 0 < x[1] < x[2] < 1]
    if not q: continue
    a = max(q)[2]
    if 0.10 <= a <= 0.90: ev[d["ev"]].append((t, a, d["res"] == "yes"))
evs = sorted((e for e in ev if len(ev[e]) >= 2), key=lambda e: first[e]); cut = 2 * len(evs) // 3
dev, held = evs[:cut], evs[cut:]
print("events >=2 eligible legs", len(evs), "dev", len(dev), "held", len(held))
def combos(e, k):
    L = sorted(ev[e]); cs = list(itertools.combinations(L, k))
    if len(cs) > 200: cs = sorted(cs, key=lambda cb: hashlib.md5(("MC1" + e + "".join(x[0] for x in cb)).encode()).hexdigest())[:200]
    return cs
def run(E, k, h):
    rows = []  # (event, net, stake, joint, prod)
    for e in E:
        for cb in combos(e, k):
            pr = math.prod(x[1] for x in cb); P = pr * (1 - h); w = all(x[2] for x in cb)
            rows.append((e, (1.0 if w else 0.0) - P - 0.07 * P * (1 - P), P, w, pr))
    return rows
def stats(rows):
    if not rows: return None
    by = collections.defaultdict(lambda: [0.0, 0.0])
    for e, n, P, w, pr in rows: by[e][0] += n; by[e][1] += P
    N = sum(r[1] for r in rows); S = sum(r[2] for r in rows); r = N / S
    se = math.sqrt(sum((v[0] - r * v[1]) ** 2 for v in by.values())) / S
    top = max(v[0] for v in by.values()) / N if N > 0 else float("nan")
    return dict(n=len(rows), ev=len(by), joint=sum(x[3] for x in rows) / len(rows), prod=sum(x[4] for x in rows) / len(rows),
                cpd=r, z=r / se if se else 0, top=top)
def table(E, name):
    print("\n##", name); print("| legs | haircut | n combos | n events | joint rate | mean product | gap | cash/$ | event z | top event share of net |\n|---|---|---|---|---|---|---|---|---|---|")
    res = {}
    for k in (2, 3):
        for h in (0, .1, .2):
            s = stats(run(E, k, h)); res[(k, h)] = s
            if s: print("| %d | %d%% | %d | %d | %.4f | %.4f | %+.4f | %+.3f | %.2f | %.2f |" % (k, h * 100, s["n"], s["ev"], s["joint"], s["prod"], s["joint"] - s["prod"], s["cpd"], s["z"], s["top"]))
    return res
r = table(dev, "development (first two thirds of events)")
h1, h2 = dev[:len(dev) // 2], dev[len(dev) // 2:]
passed = []
for (k, h), s in r.items():
    if not s: continue
    a, b = stats(run(h1, k, h)), stats(run(h2, k, h))
    ok = s["cpd"] >= .10 and a and b and a["cpd"] >= .10 and b["cpd"] >= .10 and s["n"] >= 100 and s["top"] <= .30
    print("halves k=%d h=%d%%: %s %s -> %s" % (k, h * 100, "%+.3f" % a["cpd"] if a else None, "%+.3f" % b["cpd"] if b else None, "PASS" if ok else "fail"))
    if ok: passed.append((k, h))
print("passed:", passed)
if passed: table(held, "held-out (read once)")
else: print("held-out not read (no development pass)")
