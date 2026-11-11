"""LEADLAG1 (workers/LEADLAG1_PROTOCOL.md). Development; held out read once for survivors."""
import sqlite3, math, collections, itertools, datetime
def fee(p): return 0.07 * p * (1 - p)
S = lambda x: "KX" + x + "15M"
FILES = ["data/alts2.sqlite","data/alts3.sqlite","data/alts4.sqlite","data/fresh.sqlite","data/rep.sqlite","data/l1b.sqlite","data/book.sqlite","data/five.sqlite","data/hist15/KXGOLD15M.sqlite","data/hist15/KXBTC15M.sqlite","data/hist15/KXETH15M.sqlite"]
FOL = ["XRP","SOL","HYPE","BNB","NEAR","ZEC"]
PAIRS = [(l, f) for l in ("BTC","ETH") for f in FOL] + [("GOLD","SILVER"),("SILVER","PLATINUM"),("PLATINUM","PALLADIUM"),("GOLD","COPPER"),("WTI","NATGAS"),("EURUSD","GBPUSD"),("GBPUSD","EURUSD")]
PAIRS = [(S(a), S(b)) for a, b in PAIRS]
NEED = {x for p in PAIRS for x in p}
mk = {}; cand = {}
for db in FILES:
    c = sqlite3.connect(db); new = {}
    for t, s_, ct, r in c.execute("select ticker,series,close_ts,result from market where result in ('yes','no')"):
        if s_ in NEED and t not in mk: new[t] = (s_, ct)
    if not new: continue
    for t, ts, b, a in c.execute("select ticker,end_ts,bid_c,ask_c from candle"):
        if t in new and b is not None and a is not None: cand.setdefault(t, {})[ts] = (b, a)
    for t, m in new.items():
        if t in cand: mk[t] = m
bys = collections.defaultdict(dict)
for t, (s, ct) in mk.items(): bys[s][ct] = t
cuts = {s: sorted(d)[2 * len(d) // 3] for s, d in bys.items()}
def get(t, ts):
    c = cand.get(t)
    if not c: return None
    for d in (0, -1, 1, -2, 2, 3, -3):
        if ts + d in c: return c[ts + d]
    return None
GRID = list(itertools.product((0.03,0.06,0.10),(2,3),(10,8,6),(2,3,4)))
res = {}  # (pair,grid) -> {'dev':[], 'ho':[]}
for lead, fol in PAIRS:
    for ct, ft in bys[fol].items():
        lt = bys[lead].get(ct)
        if not lt: continue
        part = "ho" if ct >= cuts[fol] else "dev"
        for (m, L, E, k) in GRID:
            td = ct - E * 60
            l1 = get(lt, td); l0 = get(lt, td - L * 60)
            f1 = get(ft, td); f0 = get(ft, td - L * 60); fx = get(ft, td + k * 60)
            if not (l1 and l0 and f1 and f0 and fx): continue
            mv = (l1[0] + l1[1]) / 2 - (l0[0] + l0[1]) / 2
            if abs(mv) < m: continue
            sg = 1 if mv > 0 else -1
            fm = ((f1[0] + f1[1]) / 2 - (f0[0] + f0[1]) / 2) * sg
            if fm >= m / 2: continue
            b, a = f1
            if a <= b or a - b > 0.05 or b <= 0 or a >= 1: continue
            if sg > 0: e = a; sale = fx[0]
            else: e = 1 - b; sale = 1 - fx[1]
            if not 0.20 <= e <= 0.80: continue
            net = sale - e - fee(e) - fee(sale)
            res.setdefault(((lead, fol), (m, L, E, k)), {"dev": [], "ho": []})[part].append((ct, net))
def stats(v):
    n = len(v)
    if n < 2: return n, 0, 0, 0, 0
    x = [y for _, y in v]; mu = sum(x) / n
    sd = math.sqrt(sum((y - mu) ** 2 for y in x) / (n - 1))
    g = sum(y for y in x if y > 0); l = -sum(y for y in x if y < 0)
    pf = g / l if l > 0 else 99
    days = len({datetime.datetime.utcfromtimestamp(c).date() for c, _ in v})
    return n, mu, pf, (mu / (sd / math.sqrt(n)) if sd > 0 else 0), days
N = len(PAIRS) * len(GRID)
print("markets", len(mk), "pairs", len(PAIRS), "cells N", N)
rows = []
for key in ((p, g) for p in PAIRS for g in GRID):
    d = res.get(key, {"dev": [], "ho": []})
    rows.append((key, stats(d["dev"])))
n150 = [r for r in rows if r[1][0] >= 150]
pf15 = [r for r in n150 if r[1][2] >= 1.5]
z439 = [r for r in pf15 if r[1][3] > 4.39]
z534 = [r for r in pf15 if r[1][3] > 5.34]
print("cells with any trade", sum(1 for r in rows if r[1][0] > 0), "| n>=150", len(n150), "| +PF>=1.5", len(pf15), "| +z>4.39", len(z439), "| +z>5.34", len(z534), "| NOT_ENOUGH_DATA", N - len(n150))
print("positive mean cells (n>=150):", sum(1 for r in n150 if r[1][1] > 0), "of", len(n150))
print("TOP by dev z (n>=150):")
for key, st in sorted(n150, key=lambda r: -r[1][3])[:10]:
    (l, f), g = key
    print(l[2:-3], "->", f[2:-3], g, "n=%d mean=%.4f PF=%.2f z=%.2f days=%d" % st)
print("TOP by dev PF (n>=150):")
for key, st in sorted(n150, key=lambda r: -r[1][2])[:5]:
    (l, f), g = key
    print(l[2:-3], "->", f[2:-3], g, "n=%d mean=%.4f PF=%.2f z=%.2f days=%d" % st)
print("HELD-OUT (read once) for dev survivors at bar 4.39:")
for key, st in z439:
    h = stats(res[key]["ho"]); (l, f), g = key
    print(l[2:-3], "->", f[2:-3], g, "dev n=%d PF=%.2f z=%.2f | HO n=%d mean=%.4f PF=%.2f z=%.2f days=%d" % (st[0], st[2], st[3], *h))
print("per pair best dev z:")
for p in PAIRS:
    c = [r for r in rows if r[0][0] == p and r[1][0] >= 150]
    if c:
        r = max(c, key=lambda r: r[1][3]); print(p[0][2:-3], "->", p[1][2:-3], r[0][1], "n=%d mean=%.4f PF=%.2f z=%.2f days=%d" % r[1], "| cells n>=150:", len(c))
    else: print(p[0][2:-3], "->", p[1][2:-3], "no cell n>=150 (max n %d)" % max([r[1][0] for r in rows if r[0][0] == p] or [0]))
