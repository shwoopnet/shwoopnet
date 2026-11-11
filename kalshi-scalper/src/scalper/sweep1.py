"""SWEEP1 (workers/SWEEP1_PROTOCOL.md). Development only."""
import sqlite3, math, sys, collections, datetime
sys.path.insert(0, "src/scalper")
import leg1
from statistics import NormalDist
def fee(p): return 0.07 * p * (1 - p)
SRC = [("data/hist15/KXBTC15M.sqlite", None), ("data/hist15/KXETH15M.sqlite", None)] + [("data/alts2.sqlite", s) for s in ("KXXRP15M", "KXDOGE15M", "KXHYPE15M", "KXBNB15M")]
mk = {}; cand = {}; serof = {}
for db, ser in SRC:
    c = sqlite3.connect(db)
    q = "select ticker,series,close_ts,result from market where result in ('yes','no') and n_candles>0" + (" and series='%s'" % ser if ser else "")
    for t, s, ct, r in c.execute(q): mk[t] = (s, ct, r)
    cq = "select ticker,end_ts,bid_c,ask_c,bid_h,ask_l,volume from candle" + (" where series='%s'" % ser if ser else "")
    for t, ts, b, a, bh, al, v in c.execute(cq):
        if t in mk and b is not None and a is not None: cand.setdefault(t, []).append((ts, b, a, bh, al, v or 0))
for t in cand: cand[t].sort()
bys = collections.defaultdict(dict)  # series -> close_ts -> ticker
for t, (s, ct, r) in mk.items(): bys[s][ct] = t
cuts = {}
for s in bys:
    cts = sorted(bys[s]); cuts[s] = cts[2 * len(cts) // 3]
def mid_at(t, ts, tol=8):
    for x in cand.get(t, []):
        if abs(x[0] - ts) <= tol: return (x[1] + x[2]) / 2
    return None
def bino(x, edges): 
    for i, e in enumerate(edges):
        if x < e: return i
    return len(edges)
tests = collections.defaultdict(list)  # (feature,bin,lead,exit) -> [(event, net)]
for t, (s, ct, res) in mk.items():
    if ct >= cuts[s]: continue
    v = cand.get(t)
    if not v: continue
    for lead, (lo, hi) in (("10m", (570, 640)), ("6m", (330, 400))):
        pick = None
        for x in v:
            if lo <= ct - x[0] <= hi: pick = x
        if not pick: continue
        ts, b, a, bh, al, vol = pick
        if b <= 0 or a >= 1 or a <= b or a - b > 0.03: continue
        if 0.04 <= a <= 0.30: side = "yes"; e = a
        elif 0.04 <= 1 - b <= 0.30: side = "no"; e = 1 - b
        else: continue
        sgn = 1 if side == "yes" else -1
        sidemid = lambda m: m if side == "yes" else 1 - m
        won = res == side
        # exits
        hold = (1.0 if won else 0.0) - e - fee(e)
        tp = None
        for x in v:
            if x[0] <= ts: continue
            hi_sell = x[3] if side == "yes" else (1 - x[4] if x[4] is not None else None)
            if hi_sell is not None and hi_sell >= e + 0.15: tp = 0.15 - fee(e) - fee(e + 0.15) if e + 0.15 < 1 else None; break
        nets = {"HOLD": hold, "TP": tp if tp is not None else hold}
        feats = {}
        m_now = sidemid((b + a) / 2); m3 = mid_at(t, ts - 180)
        if m3 is not None: feats["F1"] = bino(m_now - sidemid(m3), [-0.02, 0.0201])
        earlier = [x for x in v if x[0] <= ts]
        sm = [sidemid((x[1] + x[2]) / 2) for x in earlier]
        if len(sm) >= 3: feats["F2"] = bino(max(sm) - min(sm), [0.04, 0.1201])
        feats["F3"] = min(2, int(round((a - b) * 100)) - 1) if round((a - b) * 100) >= 1 else 0
        l3 = sum(x[5] for x in earlier[-3:]); pr = sum(x[5] for x in earlier[:-3])
        if pr > 0 and len(earlier) > 3: feats["F4"] = bino(l3 / pr, [0.5, 2.0001])
        prev = bys[s].get(ct - 900)
        if prev and mk[prev][2] in ("yes", "no"): feats["F5"] = 0 if mk[prev][2] == side else 1
        hr = ((ct - 6 * 3600) % 86400) // 3600; feats["F6"] = int(hr // 6)
        wd = datetime.datetime.fromtimestamp(ct - 6 * 3600, datetime.timezone.utc).weekday(); feats["F7"] = 1 if wd >= 5 else 0
        if len(sm) >= 3: feats["F8"] = bino(sm[-1] - sm[0], [-0.10, 0.1001])
        ref = "KXETH15M" if s == "KXBTC15M" else "KXBTC15M"
        rt = bys[ref].get(ct)
        if rt:
            r1 = mid_at(rt, ts); r0 = mid_at(rt, ts - 180)
            if r1 is not None and r0 is not None and r1 != r0: feats["F9"] = 0 if (r1 - r0) * sgn > 0 else 1
        feats["F10"] = bino(e, [0.10, 0.20])
        for f, bn in feats.items():
            for ex, nv in nets.items():
                tests[(f, bn, lead, ex)].append((t, nv))
Z = NormalDist().inv_cdf(1 - 0.05 / 5319)
print("tests", len(tests), "z bar %.2f" % Z)
rs = []
for k, L in sorted(tests.items()):
    n, ne, mean, z = leg1.clustered(L)
    gw = sum(x for _, x in L if x > 0); gl = -sum(x for _, x in L if x < 0)
    rs.append((k, n, gw / gl if gl else 9, mean, z))
for k, n, pf, mean, z in sorted(rs, key=lambda r: -r[4])[:12]: print(k, "n %d PF %.2f mean %+.4f z %+.2f" % (n, pf, mean, z))
surv = [r for r in rs if r[1] >= 100 and r[2] >= 1.3 and r[4] >= Z]
print("cells with n>=100:", sum(1 for r in rs if r[1] >= 100), "PF>=1.3 & n>=100:", sum(1 for r in rs if r[1] >= 100 and r[2] >= 1.3), "survivors:", len(surv))
print("PF>=1.0 count", sum(1 for r in rs if r[2] >= 1.0), "of", len(rs))
