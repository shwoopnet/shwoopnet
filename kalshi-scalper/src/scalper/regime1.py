"""REGIME1 (workers/REGIME1_PROTOCOL.md). Development scored for all cells; held-out printed ONLY for cells that survive."""
import sqlite3, sys, collections, datetime, math
sys.path.insert(0, "src/scalper")
import leg1
from statistics import NormalDist
def fee(p): return 0.07 * p * (1 - p)
GROUPS = {"CRYP": ["KXBTC15M","KXETH15M","KXXRP15M","KXDOGE15M"], "ALT": ["KXHYPE15M","KXBNB15M","KXNEAR15M","KXZEC15M"],
          "MET": ["KXSILVER15M","KXPLATINUM15M","KXPALLADIUM15M","KXCOPPER15M"], "ENE": ["KXWTI15M","KXNATGAS15M"],
          "FX": ["KXEURUSD15M","KXGBPUSD15M","KXUSDJPY15M","KXAUDUSD15M","KXUSDCAD15M"]}
SER = {s for g in GROUPS.values() for s in g}
GOF = {s: g for g, l in GROUPS.items() for s in l}
FILES = ["data/hist15/KXBTC15M.sqlite","data/hist15/KXETH15M.sqlite","data/alts2.sqlite","data/alts3.sqlite","data/alts4.sqlite","data/fresh.sqlite","data/rep.sqlite","data/l1b.sqlite","data/book.sqlite","data/five.sqlite"]
mk = {}; cand = {}
for db in FILES:
    c = sqlite3.connect(db); new = {}
    for t, s_, ct, r in c.execute("select ticker,series,close_ts,result from market where result in ('yes','no')"):
        if s_ in SER and t not in mk: new[t] = (s_, ct, r)
    if not new: continue
    for t, ts, b, a, bh, al, v in c.execute("select ticker,end_ts,bid_c,ask_c,bid_h,ask_l,volume from candle"):
        if t in new and b is not None and a is not None: cand.setdefault(t, []).append((ts, b, a, bh, al, v or 0))
    for t, m in new.items():
        if t in cand: mk[t] = m
for t in cand: cand[t].sort()
print("markets", len(mk), collections.Counter(m[0] for m in mk.values()))
bys = collections.defaultdict(dict)
for t, (s, ct, r) in mk.items(): bys[s][ct] = t
cuts = {s: sorted(bys[s])[2 * len(bys[s]) // 3] for s in bys}
# per-market vol (mean abs 1 minute yes-mid change)
mv = {}
for t, v in cand.items():
    d = [abs((v[i][1] + v[i][2]) / 2 - (v[i-1][1] + v[i-1][2]) / 2) for i in range(1, len(v)) if 52 <= v[i][0] - v[i-1][0] <= 68]
    if d: mv[t] = sum(d) / len(d)
def prior_vol(s, ct):
    xs = [mv[bys[s][ct - 900 * j]] for j in range(1, 17) if (ct - 900 * j) in bys[s] and bys[s][ct - 900 * j] in mv]
    return sum(xs) / len(xs) if len(xs) >= 8 else None
pv = {}
for t, (s, ct, r) in mk.items(): pv[t] = prior_vol(s, ct)
terc = {}
for s in bys:
    xs = sorted(pv[t] for t, (s2, ct, r) in mk.items() if s2 == s and ct < cuts[s] and pv[t] is not None)
    if len(xs) >= 30: terc[s] = (xs[len(xs) // 3], xs[2 * len(xs) // 3])
def streak(s, ct):
    k = 0; d = None
    for j in range(1, 5):
        t = bys[s].get(ct - 900 * j)
        if not t: break
        r = mk[t][2]
        if d is None: d = r
        if r != d: break
        k += 1
    return k, d
def session(ct):
    dt = datetime.datetime.fromtimestamp(ct, datetime.timezone.utc); wd = dt.weekday(); h = dt.hour + dt.minute / 60
    if (wd == 4 and h >= 22) or wd == 5 or (wd == 6 and h < 22): return "WKND"
    return "ASIA" if h < 8 else "EUR" if h < 13.5 else "US" if h < 20 else "LATE"
def event(ct):
    dt = datetime.datetime.fromtimestamp(ct, datetime.timezone.utc)
    if dt.weekday() == 4 and dt.day <= 7: return "JOBS"
    if dt.weekday() < 5 and 10 <= dt.day <= 14: return "CPI"
    return "OTHER"
ALLCELLS = set()
for sc in ["ALL"] + list(GROUPS) + sorted(SER):
    for b in ("low", "mid", "high"): ALLCELLS.add(("R1", b, sc))
    for b in ("WKND", "ASIA", "EUR", "US", "LATE"): ALLCELLS.add(("R2", b, sc))
for sc in ["ALL"] + list(GROUPS):
    for b in ("JOBS", "CPI", "OTHER"): ALLCELLS.add(("R3", b, sc))
    for k in (2, 3, 4):
        for w in ("with", "against"): ALLCELLS.add(("R4", "k%d_%s" % (k, w), sc))
    for b in ("wide", "tight"): ALLCELLS.add(("R5", b, sc))
print("cells", len(ALLCELLS), "tests", len(ALLCELLS) * 4)
D = collections.defaultdict(list); H = collections.defaultdict(list)
for t, (s, ct, res) in mk.items():
    if s not in SER: continue
    ho = ct >= cuts[s]; store = H if ho else D
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
        won = res == side
        hold = (1.0 if won else 0.0) - e - fee(e)
        tp = None
        for x in v:
            if x[0] <= ts: continue
            hs = x[3] if side == "yes" else (1 - x[4] if x[4] is not None else None)
            if hs is not None and hs >= e + 0.15: tp = 0.15 - fee(e) - fee(e + 0.15) if e + 0.15 < 1 else None; break
        nets = {"HOLD": hold, "TP": tp if tp is not None else hold}
        tags = []
        if pv[t] is not None and s in terc:
            tags.append(("R1", "low" if pv[t] < terc[s][0] else "mid" if pv[t] < terc[s][1] else "high"))
        tags.append(("R2", session(ct))); tags.append(("R3", event(ct)))
        k, d = streak(s, ct)
        for kk in (2, 3, 4):
            if k >= kk: tags.append(("R4", "k%d_%s" % (kk, "with" if d == side else "against")))
        sp = round((a - b) * 100); tags.append(("R5", "wide" if sp >= 2 else "tight"))
        for rg, bn in tags:
            scopes = ["ALL", GOF[s]] + ([s] if rg in ("R1", "R2") else [])
            for sc in scopes:
                for ex, nv in nets.items(): store[(rg, bn, sc, lead, ex)].append((t, nv))
def stats(L):
    n, ne, mean, z = leg1.clustered(L)
    gw = sum(x for _, x in L if x > 0); gl = -sum(x for _, x in L if x < 0)
    return n, (gw / gl if gl else 9.0), mean, z
Z1 = NormalDist().inv_cdf(1 - 0.05 / 8795); Z2 = NormalDist().inv_cdf(1 - 0.05 / 801844)
print("z bars %.2f (N 8,795) %.2f (N 801,844)" % (Z1, Z2))
rs = []
for k, L in D.items():
    n, pf, mean, z = stats(L); rs.append((k, n, pf, mean, z))
ntests = len(ALLCELLS) * 4
print("tests", ntests, "populated", len(rs), "empty", ntests - len(rs))
big = [r for r in rs if r[1] >= 100]
print("n>=100:", len(big), "| PF>=1.5 & n>=100:", sum(1 for r in big if r[2] >= 1.5), "| PF>=1.0:", sum(1 for r in rs if r[2] >= 1.0),
      "| z>bar1 (n>=100):", sum(1 for r in big if r[4] >= Z1), "| z>bar2:", sum(1 for r in big if r[4] >= Z2))
print("top by cash PF (n>=100):")
for k, n, pf, mean, z in sorted(big, key=lambda r: -r[2])[:5]: print(" ", k, "n %d PF %.2f mean %+.4f z %+.2f" % (n, pf, mean, z))
print("top by z (any n):")
for k, n, pf, mean, z in sorted(rs, key=lambda r: -r[4])[:5]: print(" ", k, "n %d PF %.2f mean %+.4f z %+.2f" % (n, pf, mean, z))
surv = [r for r in big if r[2] >= 1.5 and r[4] >= Z1]
print("survivors (dev, bar1):", len(surv))
for k, n, pf, mean, z in surv:
    hn, hpf, hm, hz = stats(H[k]) if H.get(k) else (0, 0, 0, 0)
    print("SURV", k, "dev n %d PF %.2f z %+.2f | held-out n %d PF %.2f mean %+.4f z %+.2f" % (n, pf, z, hn, hpf, hm, hz))
