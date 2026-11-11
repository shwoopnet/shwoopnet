"""ANGLES1 (workers/ANGLES1_PROTOCOL.md). Research only, local sqlite, no network.
    python -I src/scalper/angles1.py dev        (development only; writes workers/ANGLES1_dev.json)
    python -I src/scalper/angles1.py held       (once; reads only the dev survivors' cells)
"""
import sqlite3, sys, json, math, collections, datetime, bisect
from statistics import NormalDist
sys.path.insert(0, "src")
from scalper.calibration import cluster_mean_z
def fee(p): return 0.07 * p * (1 - p)
def rfee(p, C): return math.ceil(0.07 * C * p * (1 - p) * 100 - 1e-9) / 100 / C
SER = ["KXSILVER15M","KXWTI15M","KXCOPPER15M","KXNATGAS15M","KXPLATINUM15M","KXPALLADIUM15M","KXEURUSD15M","KXGBPUSD15M","KXUSDJPY15M","KXAUDUSD15M","KXUSDCAD15M","KXNEAR15M","KXZEC15M","KXHYPE15M","KXBNB15M","KXXRP15M","KXSOL15M"]
FILES = ["alts2","alts3","alts4","e3b","fresh","rep","l1b","book","five"]
mk = {}; cand = {}
for f in FILES:
    c = sqlite3.connect("data/%s.sqlite" % f)
    new = {}
    for t, s, ct, r in c.execute("select ticker,series,close_ts,result from market where result in ('yes','no')"):
        if s in SER and t not in mk: new[t] = (s, ct, r)
    if not new: continue
    for t, ts, b, a, v in c.execute("select ticker,end_ts,bid_c,ask_c,volume from candle"):
        if t in new and b is not None and a is not None: cand.setdefault(t, []).append((ts, b, a, v or 0.0))
    for t, m in new.items():
        if t in cand: mk[t] = m
for t in cand: cand[t].sort()
bys = collections.defaultdict(dict)
for t, (s, ct, r) in mk.items(): bys[s][ct] = t
cuts = {}
for s in bys:
    cts = sorted(bys[s]); cuts[s] = cts[2 * len(cts) // 3]
def day(ct): return datetime.datetime.fromtimestamp(ct, datetime.timezone.utc).strftime("%Y-%m-%d")
def pick_range(v, ct, lo, hi):
    p = None
    for x in v:
        if lo <= ct - x[0] <= hi: p = x
    return p
def pick_near(v, ct, L):
    for x in v:
        if abs(ct - x[0] - L) <= 8: return x
    return None
def exit_net(v, ts, side, e, res, k):
    won = res == side
    hold = (1.0 if won else 0.0) - e - fee(e)
    if k is None: return hold
    for x in v:
        if abs(x[0] - (ts + 60 * k)) <= 8:
            bid = x[1] if side == "yes" else 1 - x[2]
            if bid <= 0 or bid >= 1: return hold
            return bid - e - fee(e) - fee(bid)
    return hold
def cumvol(v, ct, left):
    return sum(x[3] for x in v if x[0] <= ct - left)
def quant(xs, q):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(q * len(xs)))]
LEADS = {"10m": (570, 640), "6m": (330, 400)}
TIMES = (2, 3, 4)
mode = sys.argv[1]
want = None
if mode == "held":
    want = set(map(tuple, json.load(open("workers/ANGLES1_survivors_cells.json"))))
def inpart(s, ct): return ct < cuts[s] if mode == "dev" else ct >= cuts[s]
# ACTIVITY1 ratio and frozen terciles (development r only)
def ratio(s, ct, v, ts):
    left = ct - ts
    base = []
    for j in range(1, 97):
        pt = bys[s].get(ct - 900 * j)
        if pt and pt in cand: base.append(cumvol(cand[pt], ct - 900 * j, left))
    if len(base) < 48: return None
    base.sort(); M = base[len(base) // 2] if len(base) % 2 else (base[len(base)//2 - 1] + base[len(base)//2]) / 2
    if M <= 0: return None
    return cumvol(v, ct, left) / M
tert = {}
for lead, (lo, hi) in LEADS.items():
    rs = []
    for t, (s, ct, res) in mk.items():
        if ct >= cuts[s]: continue
        p = pick_range(cand[t], ct, lo, hi)
        if p:
            r = ratio(s, ct, cand[t], p[0])
            if r is not None: rs.append(r)
    tert[lead] = (quant(rs, 1 / 3), quant(rs, 2 / 3)) if rs else None
print("terciles (dev)", tert)
cells = collections.defaultdict(list)   # key -> [(day, net, series)]
def add(key, ct, s, net):
    if want is not None and key not in want: return
    cells[key].append((day(ct), net, s))
def sides_ok(b, a):
    return b > 0 and a < 1 and a > b and a - b <= 0.03
def cheap(b, a):
    if 0.04 <= a <= 0.30: return "yes", a
    if 0.04 <= 1 - b <= 0.30: return "no", 1 - b
    return None
def mid_under(b, a):
    m = (b + a) / 2
    if m < 0.5 and 0.30 < a <= 0.88: return "yes", a
    if m > 0.5 and 0.30 < 1 - b <= 0.88: return "no", 1 - b
    return None
def favourite(b, a):
    m = (b + a) / 2
    if m > 0.5 and 0.30 < a <= 0.88: return "yes", a
    if m < 0.5 and 0.30 < 1 - b <= 0.88: return "no", 1 - b
    return None
def underdog_any(b, a):
    m = (b + a) / 2
    if m < 0.5 and 0.04 <= a <= 0.88: return "yes", a
    if m > 0.5 and 0.04 <= 1 - b <= 0.88: return "no", 1 - b
    return None
def dbin(d):
    return 0 if d < 0.1 else 1 if d < 0.2 else 2 if d < 0.3 else 3
for t, (s, ct, res) in mk.items():
    if not inpart(s, ct): continue
    v = cand[t]
    # OPENQ1
    for L in (840, 780, 720, 660, 600):
        p = pick_near(v, ct, L)
        if not p: continue
        ts, b, a, vol = p
        if not sides_ok(b, a) or abs((b + a) / 2 - 0.5) < 1e-9: continue
        bn = dbin(abs((b + a) / 2 - 0.5))
        r = favourite(b, a)
        if r:
            for k in TIMES: add(("OPENQ1", "FOLLOW", bn, L, "T%d" % k), ct, s, exit_net(v, ts, r[0], r[1], res, k))
        r = underdog_any(b, a)
        if r:
            for k in (None,) + TIMES: add(("OPENQ1", "FADE", bn, L, "HOLD" if k is None else "T%d" % k), ct, s, exit_net(v, ts, r[0], r[1], res, k))
    for lead, (lo, hi) in LEADS.items():
        p = pick_range(v, ct, lo, hi)
        if not p: continue
        ts, b, a, vol = p
        # TAIL1 (no spread or bid filter)
        for sd, e in (("yes", a if a < 1 else None), ("no", 1 - b if b > 0 else None)):
            if e is None: continue
            pc = round(e * 100)
            if 1 <= pc <= 3 and abs(e * 100 - pc) < 1e-6:
                pay = 1.0 if res == sd else 0.0
                add(("TAIL1", pc, lead, "unrounded"), ct, s, pay - e - fee(e))
                for C in (10, 100): add(("TAIL1", pc, lead, "round%d" % C), ct, s, pay - e - rfee(e, C))
        if not sides_ok(b, a): continue
        ch = cheap(b, a); md = mid_under(b, a)
        # WINPOS1
        pos = (ct // 60) % 60
        if pos in (0, 15, 30, 45):
            for band, r in (("CHEAP", ch), ("MID", md)):
                if r: add(("WINPOS1", pos, band, lead), ct, s, exit_net(v, ts, r[0], r[1], res, None))
        # ACTIVITY1
        if tert[lead]:
            rr = ratio(s, ct, v, ts)
            if rr is not None:
                tb = 0 if rr < tert[lead][0] else 1 if rr < tert[lead][1] else 2
                for band, r in (("CHEAP", ch), ("MID", md)):
                    if r:
                        for k in (None, 3): add(("ACTIVITY1", tb, band, lead, "HOLD" if k is None else "T3"), ct, s, exit_net(v, ts, r[0], r[1], res, k))
        # PRICECLUSTER1: ask exactly L for either side, and neighbours
        for sd, e in (("yes", a), ("no", 1 - b)):
            c100 = round(e * 100)
            if abs(e * 100 - c100) > 1e-6: continue
            for Lv in (10, 25, 50, 75):
                if c100 == Lv or abs(c100 - Lv) == 1:
                    kind = "CL" if c100 == Lv else "NB"
                    if Lv == 75 and not (0.04 <= e <= 0.88): continue
                    k = 3 if Lv == 75 else None
                    add(("PC1", Lv, lead, kind), ct, s, exit_net(v, ts, sd, e, res, k))
# ------------------------------------------------------------- scoring
NB = 1100000 + 214; Z1 = NormalDist().inv_cdf(1 - 0.05 / NB); Z2 = NormalDist().inv_cdf(1 - 0.05 / 9009)
def stat(L):
    obs = [(d, x) for d, x, _ in L]
    n = len(obs); mean, se, z = cluster_mean_z(obs) if n >= 2 else (0, 0, 0)
    gw = sum(x for _, x in obs if x > 0); gl = -sum(x for _, x in obs if x < 0)
    return n, (gw / gl if gl else 9.0), mean, z, len({d for d, _ in obs})
rows = []
for k, L in cells.items():
    if k[0] == "PC1" and k[3] == "NB": continue
    rows.append((k,) + stat(L))
# PC1 contrast
for Lv in (10, 25, 50, 75):
    for lead in LEADS:
        A = cells.get(("PC1", Lv, lead, "CL"), []); B = cells.get(("PC1", Lv, lead, "NB"), [])
        if len(A) > 1 and len(B) > 1:
            ma = sum(x for _, x, _ in A) / len(A)
            mb = sum(x for _, x, _ in B) / len(B)
            def cl(L, m):
                by = collections.defaultdict(float)
                for d, x, _ in L: by[d] += x - m
                return sum(v * v for v in by.values()) / len(L) ** 2
            se = math.sqrt(cl(A, ma) + cl(B, mb))
            rows.append((("PC1", Lv, lead, "CONTRAST"), len(A), len(B) / 1.0, ma - mb, (ma - mb) / se if se else 0, 0))
print(mode, "markets", len(mk), "cells with rows", len(rows), "bars z %.2f (N %d) %.2f (N 9009)" % (Z1, NB, Z2))
print("tests that exist (counted 214 regardless):", len(rows))
out = {"rows": [list(r) for r in rows]}
json.dump(out, open("workers/ANGLES1_%s.json" % mode, "w"), default=str)
def isstat(r): return r[0][-1] != "CONTRAST" and not (r[0][0] == "PC1" and r[0][-1] == "CONTRAST")
sr = [r for r in rows if r[0][-1] != "CONTRAST"]
print("cells n>=100:", sum(1 for r in sr if r[1] >= 100), "PF>=1.0:", sum(1 for r in sr if r[2] >= 1.0), "PF>=1.5&n>=100:", sum(1 for r in sr if r[1] >= 100 and r[2] >= 1.5))
print("top 12 by z (n>=30):")
for r in sorted([r for r in sr if r[1] >= 30], key=lambda r: -r[4])[:12]:
    print(r[0], "n %d PF %.2f mean %+.4f z %+.2f days %d" % (r[1], r[2], r[3], r[4], r[5]))
print("contrasts:")
for r in rows:
    if r[0][-1] == "CONTRAST": print(r[0], "nA %d nB %d diff %+.4f z %+.2f" % (r[1], r[2], r[3], r[4]))
if mode == "dev":
    sv = [r for r in sr if r[1] >= 100 and r[2] >= 1.5 and r[4] >= Z2]
    print("dev survivors (z>=%.2f):" % Z2, len(sv), "strict (z>=%.2f):" % Z1, sum(1 for r in sv if r[4] >= Z1))
    for r in sv: print(r[0], "n %d PF %.2f z %+.2f" % (r[1], r[2], r[4]))
    json.dump([list(r[0]) for r in sv], open("workers/ANGLES1_survivors_cells.json", "w"))
    # per-series descriptive for the three biggest groups
    print("per-series descriptive: TAIL1 unrounded 10m all prices, WINPOS1 none")
    for s in SER:
        L = [(d, x, ss) for k, LL in cells.items() if k[0] == "TAIL1" and k[2] == "10m" and k[3] == "unrounded" for d, x, ss in LL if ss == s]
        if len(L) > 5:
            n, pf, mean, z, dd = stat(L); print(s, "TAIL1 10m n %d PF %.2f mean %+.4f" % (n, pf, mean))
