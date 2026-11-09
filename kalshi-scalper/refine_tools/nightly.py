# Read only nightly every-trade review. Usage: python3 -I nightly.py <report.json> [YYYY-MM-DD, a US Central date; default the last full CT day]
# Cash basis as in scorer.py (win or loss recomputed from avgFill and avgFee, exits corrected to the limit). No network, no token.
import sys, json, re, datetime as D
from zoneinfo import ZoneInfo
CT = ZoneInfo('America/Chicago')
d = json.load(open(sys.argv[1]))
def T(s): return D.datetime.fromisoformat(s.replace('Z', '+00:00'))
now = T(d['generatedAt'])
day = D.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else (now.astimezone(CT) - D.timedelta(days=1)).date()
def pf(v):
    g = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return g / l if l else float('inf')
def fp(x): return 'inf' if x == float('inf') else '%.2f' % x
def cdate(o): return T(o['ts']).astimezone(CT).date()
def trade(o, grp):
    c = o['count']; y = o['side'] == 'yes'
    paid = o['avgFill'] if y else 1 - o['avgFill']
    ex = o.get('result') == 'exit'; fee = (o.get('avgFee') or 0) * c
    pnl = o['settledPnl']
    if o.get('result') in ('yes', 'no'): pnl = (c * (1 - paid) - fee) if o['result'] == o['side'] else (-c * paid - fee)
    if ex and o.get('limit') is not None: pnl += c * ((o['limit'] if y else 1 - o['limit']) - paid)
    sa = o.get('seenAsk'); slip = None
    if sa is not None: slip = (paid - (sa if y else 1 - o['seenBid'])) * 100 if o.get('seenBid') is not None else None
    return dict(o=o, grp=grp, c=c, paid=paid, pnl=pnl, ex=ex, slip=slip, ts=o['ts'], d=cdate(o))
def grp_of(o, slot):
    if slot: return o.get('strategy', '?')
    k = o['ticker'].split('-')[0]
    return {'KXGOLD15M': 'gold L1'}.get(k, k + ' L1')
allo = [(o, False) for o in d['orders']] + [(o, True) for o in d.get('slotOrders', [])]
def settled(o): return o.get('count') and o['count'] > 0 and o.get('settledPnl') is not None and o.get('avgFill') is not None
tr = sorted([trade(o, grp_of(o, s)) for o, s in allo if settled(o)], key=lambda t: t['ts'])
sub = [(o, grp_of(o, s)) for o, s in allo]
print('NIGHTLY REVIEW for CT day %s (%s) | report %s UTC | CASH basis' % (day, day.strftime('%a'), d['generatedAt'][:16]))
# ---- per strategy
def win(v, lo, hi): return [t for t in v if lo <= t['d'] <= hi]
names = ['gold L1', 'OICORE', 'EVENT830'] + sorted({t['grp'] for t in tr} - {'gold L1', 'OICORE', 'EVENT830'})
print('\n%-9s %-16s %5s %5s %9s' % ('', 'strategy', 'n', 'PF', 'net$'))
for label, lo in (('day', day), ('7 days', day - D.timedelta(days=6)), ('30 days', day - D.timedelta(days=29)), ('start, to now', D.date(2000, 1, 1))):
    hi = D.date(2999, 1, 1) if lo.year == 2000 else day
    for nm in names:
        v = [t for t in win(tr, lo, hi) if t['grp'] == nm]
        if not v and nm not in names[:3]: continue
        p = [t['pnl'] for t in v]
        print('%-14s %-16s %5d %5s %9.2f' % (label, nm, len(v), fp(pf(p)) if v else 'na', sum(p)))
# ---- every trade of the day
print('\nEVERY TRADE, CT %s (filled; time, strategy, market, side, count, paid, result, cash pnl, lead, fill vs seen ask in cents)' % day)
dayt = [t for t in tr if t['d'] == day]
for t in dayt:
    o = t['o']; tk = o['ticker']; m = re.match(r'KX([A-Z]+?)(?:15M)?-(\d\d[A-Z]{3}\d\d)(\d{4})-', tk)
    short = ('%s %s' % (m[1], m[3])) if m else tk
    print('%s  %-8s %-12s %-3s x%-3d paid %.3f  %-4s pnl %+7.2f  lead %-4s slip %s' % (
        T(o['ts']).astimezone(CT).strftime('%H:%M:%S'), t['grp'][:8], short, o['side'], t['c'], t['paid'], o.get('result'), t['pnl'], o.get('entryLead') or '-', ('%+.1f' % t['slip']) if t['slip'] is not None else 'na'))
if not dayt: print('(no settled fills)')
# ---- flags
print('\nFLAGS')
LOCK = {'gold L1': 50, 'OICORE': 12, 'EVENT830': 1, 'KXDOGE15M L1': 50, 'KXXRP15M L1': 1, 'KXBTC15M L1': 1, 'KXETH15M L1': 1}
ex = [t for t in dayt if t['ex']]
print('early sells: %d' % len(ex) + ''.join('\n   %s %s x%d pnl %+.2f' % (T(t['ts']).astimezone(CT).strftime('%H:%M'), t['o']['ticker'], t['c'], t['pnl']) for t in ex))
big = [t for t in dayt if t['pnl'] < -5]
print('losses over $5: %d' % len(big) + ''.join('\n   %s %s x%d pnl %+.2f' % (T(t['ts']).astimezone(CT).strftime('%H:%M'), t['o']['ticker'], t['c'], t['pnl']) for t in big))
ov = [t for t in dayt if t['c'] > LOCK.get(t['grp'], 50)]
print('orders above the size lock (assumed locks: OICORE 12 since Nov 7, EVENT830 1; edit LOCK; see the server oversize line below): %d' % len(ov) + ''.join('\n   %s x%d' % (t['o']['ticker'], t['c']) for t in ov))
nf = [(o, g) for o, g in sub if cdate(o) == day and not (o.get('count') and o['count'] > 0)]
from collections import Counter
print('no-fill orders: %d %s' % (len(nf), dict(Counter(g for _, g in nf))))
ovd = [x for x in (d.get('oversize') or {}).get('orders', []) if T(x['ts']).astimezone(CT).date() == day]
print('server oversize rows that day: %d (all time %s)' % (len(ovd), (d.get('oversize') or {}).get('count')))
sk = (d.get('skips') or {}).get('rows')
if sk is None: print('cheap_skipped: skip rows not in this report')
else:
    sd = [r for r in sk if T(r['at']).astimezone(CT).date() == day]
    cs = [r for r in sd if r['reason'] == 'cheap_skipped']
    print('skip rows that day %d (window of report: last %s days); cheap_skipped: %d %s' % (len(sd), d['skips'].get('days'), len(cs), dict(Counter(r['reason'] for r in sd))))
    for r in cs: print('   %s %s left %ss %s' % (T(r['at']).astimezone(CT).strftime('%H:%M'), r['ticker'], r.get('secondsLeft'), json.dumps(r.get('detail'))))
# ---- gold tripwire (as goldtrip.py)
START = '2026-11-09T16:22:00'
g = [(t['ts'], t['pnl']) for t in tr if t['grp'] == 'gold L1' and t['o'].get('result') in ('yes', 'no', 'exit')]
gs = [p for ts, p in g if ts >= START]
roll = [pf([p for _, p in g[i:i + 60]]) for i in range(len(g) - 59)]
below = [r for r in roll[max(0, len(roll) - len([1 for ts, _ in g if ts >= START])):] if r < 0.7] if roll else []
print('\nGOLD TRIPWIRE: n since %sZ %d of 100, cumulative cash PF %s net $%.2f, latest rolling-60 PF %s, windows below 0.7 since start %d' % (START[:16], len(gs), fp(pf(gs)) if gs else 'na', sum(gs), fp(roll[-1]) if roll else 'na', len(below)))
# ---- OICORE headroom (booked settledPnl, as the code books it)
o = sorted([x for x in d.get('slotOrders', []) if x.get('strategy') == 'OICORE' and x.get('status') == 'filled' and x.get('settledPnl') is not None], key=lambda x: x['ts'])
BASE = 979.25
cts = o[-1]['count'] if o else 10
stop = min(5 * cts, 0.12 * BASE, 150)
cum = pk = streak = ms = 0.0; mdd = 0.0; killn = None
for i, x in enumerate(o, 1):
    cum += x['settledPnl']; pk = max(pk, cum); mdd = max(mdd, pk - cum)
    streak = streak + 1 if x['settledPnl'] < 0 else 0; ms = max(ms, streak)
dd = pk - cum
print('OICORE HEADROOM (booked settledPnl, %d fills):' % len(o))
print('  drawdown from peak %.2f (peak %.2f, net %.2f, worst so far %.2f) vs stop min(5 x %d, 12%% x %.2f = %.2f, 150) = %.2f -> room %.2f' % (dd, pk, cum, mdd, cts, BASE, 0.12 * BASE, stop, stop - dd))
print('  net kill: net %.2f after %d fills; kill if under -6.00 once 40 fills -> %s' % (cum, len(o), ('room %.2f' % (cum + 6)) if len(o) >= 40 else 'armed, room %.2f' % (cum + 6)))
print('  losing streak now %d (worst %d) vs kill at 24 -> room %d' % (streak, ms, 24 - streak))
# ---- open positions
op = [(x, g) for x, g in sub if x.get('status') == 'filled' and (x.get('count') or 0) > 0 and (x.get('result') is None or x.get('settledPnl') is None)]
print('\nOPEN POSITIONS: %d' % len(op))
for x, g in op: print('  %s %s %s x%d paid %s' % (T(x['ts']).astimezone(CT).strftime('%m-%d %H:%M'), g, x['ticker'], x['count'], x.get('avgFill')))
