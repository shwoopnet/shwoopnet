"""EARLYCLOSE1 (workers/EARLYCLOSE1_PROTOCOL.md). Development only; held-out only for survivors."""
import json, sqlite3, collections, sys, os, statistics
def fee(p): return 0.07 * p * (1 - p)
U = os.environ.get("US2", "/tmp/claude-0/-home-user-shwoopnet/026f6e8f-6dc4-5e3b-8c3b-e0089b12fb94/scratchpad/us2/")
res = {}
for l in open(U + "census_results.jsonl"): res.update(json.loads(l)["r"])
rows = {}; cat = {}
for l in open(U + "census.jsonl"):
    d = json.loads(l)
    for m in d["markets"]:
        if m[0] in res: rows[m[0]] = (d["ticker"], m[2], m[3])   # series, close, expected exp
        cat[d["ticker"]] = d.get("cat")
early = lambda cl, ex: cl % 60 != 0 and cl < ex - 60
sh = collections.defaultdict(lambda: [0, 0])
for t, (s, cl, ex) in rows.items():
    sh[s][1] += 1; sh[s][0] += early(cl, ex)
ES = {s: a / b for s, (a, b) in sh.items() if b >= 20}
grp = {s: ("ECS" if v >= 0.8 else "CONTROL" if v <= 0.1 else None) for s, v in ES.items()}
print("series", len(ES), collections.Counter(grp.values()))
# descriptive lag
lag = collections.defaultdict(list)
for t, (s, cl, ex) in rows.items():
    if early(cl, ex): lag[cat.get(s)].append((ex - cl) / 3600)
for c, v in lag.items():
    v.sort(); print("lag_h", c, len(v), "median %.2f p10 %.2f p90 %.2f" % (statistics.median(v), v[len(v)//10], v[9*len(v)//10]))
# candles
cand = collections.defaultdict(list)
def load(db, tb, cols):
    c = sqlite3.connect(db)
    for t, ts, b, a in c.execute(f"select ticker,end_ts,{cols} from {tb}"):
        if t in rows and b is not None and a is not None and t not in done: cand[t].append((ts, b, a))
done = set()
for db, tb, cols in [("data/sports.sqlite","candle","bid_c,ask_c"),("data/sports1.sqlite","candle","bid_c,ask_c"),("data/flb1.sqlite","candle","bid_c,ask_c"),("data/theta1.sqlite","candle","bid_c,ask_c"),("data/newlist1.sqlite","cd","bid,ask")]:
    load(db, tb, cols); done |= set(cand)
for t in cand: cand[t].sort()
byser = collections.defaultdict(list)
for t in cand:
    s = rows[t][0]
    if grp.get(s): byser[s].append(rows[t][1])
cut = {s: sorted(v)[2 * len(v) // 3] for s, v in byser.items()}
print("markets with candles", sum(len(v) for v in byser.values()), collections.Counter(grp[s] for s in byser for _ in byser[s]))
def entry(t, H, band):
    s, cl, ex = rows[t]; target = ex - H * 3600
    best = None
    for ts, b, a in cand[t]:
        if abs(ts - target) <= 1800 and ts <= cl - 600 and (best is None or abs(ts - target) < abs(best[0] - target)): best = (ts, b, a)
    if not best: return None
    ts, b, a = best
    if b <= 0 or a >= 1 or a < b or a - b > 0.05: return None
    lo, hi = (0.04, 0.30) if band == "CHEAP" else (0.30, 0.88)
    if lo <= a <= hi: side, e = "yes", a
    elif lo <= 1 - b <= hi: side, e = "no", 1 - b
    else: return None
    return (1.0 if res[t] == side else 0.0) - e - fee(e), e, side, (a + b) / 2
def stats(xs):
    n = len(xs)
    if not n: return None
    w = sum(x for _, x in xs if x > 0); l = -sum(x for _, x in xs if x < 0)
    cl = collections.defaultdict(float)
    for d, x in xs: cl[d] += x
    k = len(cl); m = sum(cl.values()) / k
    sd = (sum((v - m) ** 2 for v in cl.values()) / (k - 1)) ** 0.5 if k > 1 else float("nan")
    z = m / (sd / k ** 0.5) if k > 1 and sd > 0 else float("nan")
    return dict(n=n, pf=round(w / l, 3) if l else None, mean_c=round(100 * sum(x for _, x in xs) / n, 2), z=round(z, 2), days=k)
held = "--held" in sys.argv
for g in ("ECS", "CONTROL"):
    for H in (6, 2):
        for band in ("CHEAP", "MID"):
            xs = []
            for s in byser:
                if grp[s] != g: continue
                for t in cand:
                    if rows[t][0] != s or (rows[t][1] >= cut[s]) != held: continue
                    r = entry(t, H, band)
                    if r: xs.append((rows[t][1] // 86400, r[0]))
            print(g, H, band, stats(xs))
# calibration ECS dev: cheaper side mid by 0.05 bin (H=6 entry, both bands merged)
bins = collections.defaultdict(list)
for s in byser:
    if grp[s] != "ECS": continue
    for t in cand:
        if rows[t][0] != s or (rows[t][1] >= cut[s]) != held: continue
        for band in ("CHEAP", "MID"):
            r = entry(t, 6, band)
            if r and r[3] is not None:
                m = r[3] if r[2] == "yes" else 1 - r[3]  # mid of the side bought
                if m <= 0.5 and band == "CHEAP":
                    bins[min(int(m / 0.05), 9)].append(1.0 if (r[0] + r[1] + fee(r[1])) > 0.5 else 0.0)
for b in sorted(bins):
    v = bins[b]; print("cal bin %.2f-%.2f n %d win %.3f mid %.3f" % (b * .05, b * .05 + .05, len(v), sum(v)/len(v), b * .05 + .025))
