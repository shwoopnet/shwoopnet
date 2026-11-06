"""EVM1 to EVM3 scorer (development only). Run once after registration."""
import sqlite3, json, math, random, datetime as dt, collections, sys
CUT = dt.datetime(2026, 9, 21, tzinfo=dt.timezone.utc).timestamp()  # closes at or after this are never read
START = dt.datetime(2026, 8, 24, tzinfo=dt.timezone.utc).timestamp()
K = 10000.0
perp = {}
with open('/tmp/claude-0/cache/KXBTCPERP_1m.jsonl') as f:
    for l in f:
        d = json.loads(l); s = d['end_period_ts']
        if s < START - 7200 or s > CUT: continue
        b = float(d['bid']['close'] or 0); a = float(d['ask']['close'] or 0)
        perp[s] = (b, a)
def pm(s):
    for k in range(0, 4):
        v = perp.get(s - 60 * k)
        if v and v[0] > 0 and v[1] > 0:
            m = (v[0] + v[1]) / 2
            if (v[1] - v[0]) <= 0.005 * m: return m, v[1] - v[0]
    return None
c = sqlite3.connect('data/conf2_lad.sqlite')
closes = [r for r in c.execute("select distinct close_ts from market where series='KXBTCD' and n_candles>0 and close_ts<? order by close_ts", (CUT,))]
closes = [r[0] for r in closes]
def day(ts): return dt.datetime.fromtimestamp(ts, dt.timezone.utc).date()
days = sorted({day(x) for x in closes}); half = days[len(days)//2]
print('dev closes', len(closes), 'dates', len(days), days[0], days[-1], 'D2 starts', half)
LAD = collections.defaultdict(list)
for strike, close_ts, end_ts, bid, ask, res in c.execute("select m.strike,m.close_ts,k.end_ts,k.bid_c,k.ask_c,m.result from market m join candle k on k.ticker=m.ticker where m.series='KXBTCD' and m.close_ts<? order by m.strike", (CUT,)):
    LAD[(close_ts, end_ts)].append((strike, bid, ask, res))
def ladder(C, s):
    return LAD.get((C, s), [])
def implied(rows):
    pts = [(r[0], (r[1] + r[2]) / 2) for r in rows if r[1] is not None and r[2] is not None and r[2] > 0 and r[1] >= 0 and r[2] <= 1]
    for (k1, p1), (k2, p2) in zip(pts, pts[1:]):
        if p1 >= .5 >= p2 and p1 > p2 and k2 - k1 <= 200: return k1 + (k2 - k1) * (p1 - .5) / (p1 - p2)
    return None
def cluster(vals_by_day):
    xs = [sum(v) / len(v) for v in vals_by_day.values() if v]; n = len(xs)
    if n < 3: return None, None
    m = sum(xs) / n; sd = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** .5
    return m, (m / (sd / n ** .5) if sd > 0 else None)
# scale check
rat = []; 
for C in closes:
    t = C - 1500; p = pm(t); im = implied(ladder(C, t))
    if p and im: rat.append(im / (K * p[0]))
rat.sort(); print('scale median', rat[len(rat)//2] if rat else None, len(rat))
# EVM1
def corr(x, y):
    n = len(x)
    if n < 5: return None
    mx = sum(x)/n; my = sum(y)/n; sx = sum((a-mx)**2 for a in x); sy = sum((b-my)**2 for b in y)
    if sx == 0 or sy == 0: return None
    return sum((a-mx)*(b-my) for a, b in zip(x, y)) / (sx*sy) ** .5
byday = collections.defaultdict(lambda: ([], [], [], []))  # lead x,y ; lag x,y
npairs = 0
for C in closes:
    P = {}; I = {}
    for s in range(C - 55*60, C - 60, 60):
        p = pm(s); 
        if p: P[s] = p[0]
        im = implied(ladder(C, s))
        if im: I[s] = im
    dp = {s: math.log(P[s]/P[s-60]) for s in P if s-60 in P}
    di = {s: math.log(I[s]/I[s-60]) for s in I if s-60 in I}
    for s in dp:
        if s+60 in di:
            byday[day(C)][0].append(dp[s]); byday[day(C)][1].append(di[s+60]); npairs += 1
        if s in di and s+60 in dp:
            byday[day(C)][2].append(di[s]); byday[day(C)][3].append(dp[s+60])
def lead(sel):
    A = []; B = []
    for d, v in byday.items():
        if not sel(d): continue
        a = corr(v[0], v[1]); b = corr(v[2], v[3])
        if a is not None and b is not None: A.append(a); B.append(b)
    return A, B
out = {}
for name, sel in (('all', lambda d: True), ('D1', lambda d: d < half), ('D2', lambda d: d >= half)):
    A, B = lead(sel); n = len(A)
    if n < 3: print('EVM1', name, 'n', n); continue
    diff = [a-b for a, b in zip(A, B)]; m = sum(diff)/n; sd = (sum((x-m)**2 for x in diff)/(n-1))**.5
    print('EVM1', name, 'dates', n, 'L_pi %.4f L_ip %.4f diff %.4f z %.2f' % (sum(A)/n, sum(B)/n, m, m/(sd/n**.5) if sd else 0))
print('EVM1 usable minute pairs', npairs)
# EVM2 and EVM3
def fee(P): return math.ceil(0.07*P*(1-P)*100 - 1e-9)/100
def pf(x):
    w = sum(v for v in x if v > 0); l = -sum(v for v in x if v < 0); return w/l if l else float('inf')
trig = []; ctl = []; t3 = []; c3 = []
for C in closes:
    t = C - 1500; p = pm(t); pe = pm(C)
    rows = ladder(C, t)
    if not p: continue
    im = implied(rows)
    if im and pe:
        B = (im - K*p[0]) / (K*p[0]) * 1e4
        if B != 0:
            sgn = 1 if B > 0 else -1
            gross = sgn * (pe[0]-p[0]) / p[0] * 1e4
            cost = (p[1]/p[0]/2 + pe[1]/pe[0]/2) * 1e4
            row = dict(day=day(C), gross=gross, cost=cost)
            (trig if abs(B) >= 20 else ctl).append(row)
    # EVM3
    P = K*p[0]; best = {'t': None, 'c': None}
    for k, bid, ask, res in rows:
        if bid is None or ask is None or not (0 < ask < 1) or bid <= 0: continue
        for side in ('yes', 'no'):
            price = ask if side == 'yes' else 1 - bid
            if not (0.03 <= price <= 0.30): continue
            win = (res == 'yes') if side == 'yes' else (res == 'no')
            thr = (side == 'yes' and P >= k*1.003) or (side == 'no' and P <= k*0.997)
            ctr = (side == 'yes' and P <= k*0.997) or (side == 'no' and P >= k*1.003)
            for key, ok in (('t', thr), ('c', ctr)):
                if ok and (best[key] is None or price > best[key][0]): best[key] = (price, win)
    for key, lst in (('t', t3), ('c', c3)):
        if best[key]:
            pr, win = best[key]; lst.append(dict(day=day(C), x=(100*(1 if win else 0) - 100*pr - 100*fee(pr)), x12=(100*(1 if win else 0) - 100*pr - 120*fee(pr) - 1)))
def rep2(lst, name, h):
    for mult, lab in ((1.0, ''), (1.2, 'x1.2')):
        nets = [r['gross'] - mult*(r['cost'] + 24 + 1) for r in lst if h(r['day'])]
        if nets: print(name, lab, 'n', len(nets), 'gross %.2f bp cost %.2f bp net %.2f PF %.2f' % (sum(r['gross'] for r in lst if h(r['day']))/len(nets), sum(mult*(r['cost']+25) for r in lst if h(r['day']))/len(nets), sum(nets)/len(nets), pf(nets)))
        else: print(name, lab, 'n 0')
for nm, h in (('all', lambda d: True), ('D1', lambda d: d < half), ('D2', lambda d: d >= half)):
    rep2(trig, 'EVM2 trig ' + nm, h); rep2(ctl, 'EVM2 ctrl ' + nm, h)
d = collections.defaultdict(list)
for r in trig: d[r['day']].append(r['gross'] - (r['cost'] + 25))
print('EVM2 day cluster mean,z', cluster(d))
for nm, h in (('all', lambda d: True), ('D1', lambda d: d < half), ('D2', lambda d: d >= half)):
    for lab, lst in (('trig', t3), ('ctrl', c3)):
        x = [r['x'] for r in lst if h(r['day'])]; x12 = [r['x12'] for r in lst if h(r['day'])]
        print('EVM3', lab, nm, 'n', len(x), 'net %.2fc' % (sum(x)/len(x) if x else 0), 'PF %.2f' % pf(x) if x else '', 'PF x1.2 %.2f' % pf(x12) if x else '')
# descriptive only (disclosed, not a new try): distribution of |B| in bp at the decision minute
import statistics
bs = []
for C in closes:
    t = C - 1500; p = pm(t)
    if not p: continue
    im = implied(ladder(C, t))
    if im: bs.append(abs(im - K*p[0]) / (K*p[0]) * 1e4)
bs.sort(); print('|B| bp n', len(bs), 'median %.2f p90 %.2f p99 %.2f max %.2f' % (bs[len(bs)//2], bs[int(.9*len(bs))], bs[int(.99*len(bs))], bs[-1]))
