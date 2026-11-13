#!/usr/bin/env python3
"""W92 S-FLOWL1 forward tracker. Public Kalshi only. Cache flowl1_cache.jsonl.
Gold KXGOLD15M closing after REG. In-band side: ask 0.88..0.97 on candle ending close-360 (skip none/both).
Flow = (taker bought - sold on bought side)/total, trades close-540<=t<close-360, >=5 trades. Flagged <= -0.151.
Early sell: bought side bid <= 0.25 after entry before close (candle lows if present else bid closes); loss = early sell or settled against.
Net: buy at ask, hold; early sell exits at 0.25; settle 1/0; fee ceil(7*10*p*(1-p))/1000 per contract each traded leg.
Read at 20 early sells; kill if flagged loss rate not > 1.3x unflagged."""
import json, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
REG = "2026-11-04T04:43:00Z"
src = open(HERE + '/flow_forward.py').read().replace('\nmain()\n', '\n')
ns = {'__file__': HERE + '/flow_forward.py', '__name__': 'ff'}
exec(compile(src, 'ff', 'exec'), ns)
get = ns['get']; B = ns['B']; epoch = ns['epoch']; tt = ns['trade_tuple']; pf = ns['pf']
CAP = int(os.environ.get('W125_CAP', '40'))  # W125
SER = "KXGOLD15M"; THR = -0.151; CACHE = HERE + '/flowl1_cache.jsonl'

def list_markets(since):
    mk = []; cur = None
    while True:
        u = B + "/markets?series_ticker=%s&status=settled&limit=1000&min_close_ts=%d" % (SER, since)
        if cur: u += "&cursor=" + cur
        d = get(u)
        if not d: break
        for m in d.get('markets', []):
            if m.get('result') in ('yes', 'no'): mk.append({'t': m['ticker'], 'c': epoch(m['close_time']), 'r': m['result']})
        cur = d.get('cursor')
        if not cur or not d.get('markets'): break
    return mk

def f(x, *p):
    try:
        for q in p: x = x[q]
        return float(x)
    except Exception: return None

def candles(tk, c):
    d = get(B + "/series/%s/markets/%s/candlesticks?start_ts=%d&end_ts=%d&period_interval=1" % (SER, tk, c - 660, c + 60))
    if not d: return None
    k = {}
    for x in d.get('candlesticks', []):
        try:
            k[str(int(x['end_period_ts']))] = dict(ac=f(x,'yes_ask','close_dollars'), bc=f(x,'yes_bid','close_dollars'),
                ah=f(x,'yes_ask','high_dollars'), bl=f(x,'yes_bid','low_dollars'))
        except Exception: pass
    return k

def pull(tk, c):
    out = []; cur = None
    while True:
        u = B + "/markets/trades?ticker=%s&limit=1000&min_ts=%d&max_ts=%d" % (tk, c - 540, c - 360)
        if cur: u += "&cursor=" + cur
        d = get(u)
        if d is None: return None
        out += [tt(x) for x in d.get('trades', [])]
        cur = d.get('cursor')
        if not cur or not d.get('trades'): break
    return out

def fee(p): return math.ceil(7 * 10 * p * (1 - p) - 1e-9) / 1000

def analyse(r):
    c = r['c']; k = r['k']; e = k.get(str(c - 360))
    if not e or e['ac'] is None or e['bc'] is None: return None
    ya = e['ac']; na = 1 - e['bc']
    ins = [s for s, a in (('yes', ya), ('no', na)) if 0.88 - 1e-9 <= a <= 0.97 + 1e-9]
    if len(ins) != 1: return None
    sd = ins[0]; p = ya if sd == 'yes' else na
    sel = [x for x in r['trades'] if c - 540 <= x[0] < c - 360]
    if len(sel) < 5: return 'thin'
    b = sum(x[2] for x in sel if x[3] == sd); s = sum(x[2] for x in sel if x[3] != sd)
    if b + s == 0: return 'thin'
    flow = (b - s) / (b + s)
    early = False
    for ts, v in k.items():
        ts = int(ts)
        if not (c - 360 < ts <= c): continue
        if sd == 'yes': bid = v['bl'] if v['bl'] is not None else v['bc']
        else:
            bid = (1 - v['ah']) if v['ah'] is not None else (1 - v['ac'] if v['ac'] is not None else None)
        if bid is not None and bid <= 0.25 + 1e-9: early = True; break
    won = r['r'] == sd
    if early: net = 0.25 - p - fee(p) - fee(0.25)
    elif won: net = 1 - p - fee(p)
    else: net = -p - fee(p)
    return dict(t=r['t'], c=c, flow=flow, flag=flow <= THR, early=early, loss=early or not won, net=net)

def block(name, W):
    if not W: print('%s: windows 0' % name); return
    n = [w['net'] for w in W]
    print('%s: windows %d, losses %d, early sells %d, net %+.2fc/ct, PF %.2f' % (name, len(W), sum(w['loss'] for w in W),
          sum(w['early'] for w in W), 100 * sum(n) / len(n), pf(n)))

def main():
    since = epoch(REG); cache = {}
    if os.path.exists(CACHE):
        for l in open(CACHE):
            try: r = json.loads(l); cache[r['t']] = r
            except Exception: pass
    mk = sorted([m for m in list_markets(since) if m['c'] > since], key=lambda m: m['c'])
    print('gold settled windows after %s: %d (cached %d)' % (REG, len(mk), sum(m['t'] in cache for m in mk)))
    fh = open(CACHE, 'a')
    newn = 0; pend = 0
    for m in mk:
        if m['t'] in cache: continue
        if newn >= CAP: pend += 1; continue
        newn += 1
        k = candles(m['t'], m['c']); tr = pull(m['t'], m['c'])
        if k is None or tr is None: print('skip', m['t']); continue
        r = dict(t=m['t'], c=m['c'], r=m['r'], trades=tr, k=k); fh.write(json.dumps(r) + "\n"); fh.flush(); cache[m['t']] = r
    if pend: print('W125 CAP: fetched %d new windows this run, %d still uncached (re-run to catch up); figures below use cached windows only' % (newn, pend))
    W = []; thin = 0
    for m in mk:
        r = cache.get(m['t'])
        a = analyse(r) if r else None
        if a == 'thin': thin += 1
        elif a: W.append(a)
    print('in-band windows with >=5 flow trades: %d (dropped thin %d)' % (len(W), thin))
    h = len(W) // 2
    block('first half ', W[:h]); block('second half', W[h:]); block('all', W)
    fl = [w for w in W if w['flag']]; un = [w for w in W if not w['flag']]
    block('flagged  ', fl); block('unflagged', un)
    es = sum(w['early'] for w in W)
    print('early sells %d of 20 needed' % es)
    if es >= 20 and fl and un:
        lf = sum(w['loss'] for w in fl) / len(fl); lu = sum(w['loss'] for w in un) / len(un)
        print('READ: flagged loss rate %.3f vs unflagged %.3f; %s' % (lf, lu, 'KILL' if not lf > 1.3 * lu else 'survives'))
    else: print('not yet readable')
main()
