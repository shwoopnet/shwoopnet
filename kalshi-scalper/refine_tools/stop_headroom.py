#!/usr/bin/env python3
# Replays the shared 12% loss stop (botRisk in functions/kalshiLiveLib.js) from dash_report.json. Read only.
# usage: python3 -I stop_headroom.py dash_report.json [base ...]   (default bases 466 518)
import json, sys, math, re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
CT, ET = ZoneInfo('America/Chicago'), ZoneInfo('America/New_York')
FRAC = 0.12
d = json.load(open(sys.argv[1]))
bases = [float(x) for x in sys.argv[2:]] or [466.0, 518.0]
now = datetime.fromisoformat(d['generatedAt'].replace('Z', '+00:00'))
MON = {m: i + 1 for i, m in enumerate('JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split())}
def close_of(tk):  # ticker time part is the close in US Eastern: YYMONDDHHMM
    m = re.search(r'-(\d\d)([A-Z]{3})(\d\d)(\d\d)(\d\d)-', tk)
    y, mo, dd, hh, mm = 2000 + int(m[1]), MON[m[2]], int(m[3]), int(m[4]), int(m[5])
    return datetime(y, mo, dd, hh, mm, tzinfo=ET).astimezone(timezone.utc)
def fee(c, p): return math.ceil(0.07 * c * p * (1 - p) * 100 - 1e-9) / 100
rows = []
for src, lst in (('L1', d['orders']), ('SLOT', d['slotOrders'])):
    for x in lst:
        if x['status'] != 'filled' or not x['count'] or x['result'] is None or x['settledPnl'] is None: continue
        c = x['count']; s = x['side']; res = x['result']
        ts = datetime.fromisoformat(x['ts'].replace('Z', '+00:00')); pnl = x['settledPnl']
        lp = (x['limit'] if s == 'yes' else 1 - x['limit']) if x.get('limit') is not None else None
        # maxCost (limit price + fee, what the stop books). Exact when derivable from a non-exit settledPnl, else estimated from the limit.
        if res == 'exit': mc = c * lp + fee(c, lp) if lp is not None else -pnl
        elif res == s: mc = c - pnl
        else: mc = -pnl
        add = x.get('addon') or 0
        ac = mc * add / c if src == 'L1' else 0.0
        loss = (res != s) if res != 'exit' else pnl < 0
        arisk = (ac if res != 'exit' else (-pnl * ac / mc if pnl < 0 and mc > 0 else 0)) if loss else 0.0
        if res != 'exit' and res != s: arisk = ac
        rows.append(dict(src=src, ts=ts, close=max(close_of(x['ticker']), ts), pnl=pnl, mc=mc, ac=ac, arisk=arisk, tk=x['ticker']))
rows.sort(key=lambda r: r['ts'])
def state(t, pre=False):
    """net, openCost, addonAtRisk of orders with ts in (t-24h, t]; unresolved (close>t) counted at full cost as lost."""
    net = oc = ar = 0.0
    for r in rows:
        if r['ts'] < t - timedelta(hours=24) or r['ts'] > t or (pre and r['ts'] == t): continue
        if r['close'] > t: oc += r['mc']; ar += r['ac']
        else: net += r['pnl']; ar += r['arisk']
    return net, oc, ar
def head(t, base, pre=False):
    n, o, a = state(t, pre); return FRAC * base + a + (n - o)
pts = set()
for r in rows:
    pts.update([r['ts'], r['close'], r['ts'] + timedelta(hours=24)])
pts = sorted(p for p in pts if p <= now)
last7 = sorted({p.astimezone(CT).date() for p in pts})[-7:]
print('generated', now.astimezone(CT).strftime('%a %m-%d %H:%M CT'), '| filled orders used', len(rows), '(L1 %d, slot %d)' % (sum(r['src']=='L1' for r in rows), sum(r['src']=='SLOT' for r in rows)))
for b in bases:
    print('\nbase %g  stop = %.2f + addon at risk' % (b, FRAC * b))
    for day in last7:
        best = None
        for p in pts:
            if p.astimezone(CT).date() != day: continue
            for pre in (False, True):
                h = head(p, b, pre)
                if best is None or h < best[0]: best = (h, p, pre)
        h, p, pre = best
        print('  %s min headroom %6.2f at %s CT%s' % (day, h, p.astimezone(CT).strftime('%H:%M'), ' (just before an order)' if pre else ''))
    n, o, a = state(now); print('  now: net %.2f open %.2f addonAtRisk %.2f -> headroom %.2f' % (n, o, a, FRAC * b + a + n - o))
print('\nNext 24h, losses leaving the 24h window (no new orders assumed), CT:')
fut = sorted({r['ts'] + timedelta(hours=24) for r in rows if now < r['ts'] + timedelta(hours=24) <= now + timedelta(hours=24)})
for p in fut:
    gone = [r for r in rows if r['ts'] + timedelta(hours=24) == p]
    out = sum(-r['pnl'] for r in gone)
    if out > 0.5 or len(fut) < 12 or out < -0.5:
        print('  %s  pnl of orders leaving %+.2f | headroom after: %s' % (p.astimezone(CT).strftime('%a %H:%M'), -out, ', '.join('%g: %.2f' % (b, head(p, b)) for b in bases)))
