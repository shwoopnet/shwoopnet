#!/usr/bin/env python3
"""W23 FLOW1-TRACKER. Read only. No network: reads the report JSON and flow_cache.jsonl
(refresh the cache first with: python3 flow_forward.py). Usage: forward_flow1.py <report.json>
FLOW1 orders are slotOrders with strategy == 'FLOW1'. Shadow = low half pool (imb <= -0.036,
>= 5 trades in [close-360, close-180)), the same rule as flow_forward.py."""
import sys, json, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
THR = -0.036
def fee(p): return 0.07 * p * (1 - p)
def feeo(c, p): return math.ceil(7 * c * p * (1 - p) - 1e-9) / 100
def pf(ns):
    g = sum(x for x in ns if x > 0); l = -sum(x for x in ns if x < 0)
    return g / l if l else float('inf')

def cheap_side(k, c):
    try: ya, yb = k[c - 180]; fa, fb = k[c - 120]
    except KeyError: return None
    for s, a in (('yes', ya), ('no', 1 - yb)):
        if 0.05 - 1e-9 <= a <= 0.5 + 1e-9:
            p = fa if s == 'yes' else 1 - fb
            return (s, p) if 0 < p < 1 else None
    return None
def imbalance(tr, c, sd):
    sel = [x for x in tr if c - 360 <= x[0] < c - 180]
    buy = sum(x[2] for x in sel if x[3] == sd); sell = sum(x[2] for x in sel if x[3] != sd)
    return len(sel), ((buy - sell) / (buy + sell) if buy + sell else None)

def live_fill(o):
    if o.get('avgFill') is not None: return o['avgFill']
    c = o['count']; pnl = o['settledPnl']; win = (o['result'] == o['side']); p = 0.1
    for _ in range(8): p = (1 - (pnl + feeo(c, p)) / c) if win else ((-pnl - feeo(c, p)) / c)
    return p

def flag(cond, text): print('  ' + ('** FLAG ** ' if cond else 'ok   ') + text)

def main():
    d = json.load(open(sys.argv[1]))
    fo = sorted([o for o in d.get('slotOrders', []) if o.get('strategy') == 'FLOW1'], key=lambda o: o['ts'])
    if not fo: print('no FLOW1 orders yet'); return
    cache = {}
    p = os.path.join(HERE, 'flow_cache.jsonl')
    if os.path.exists(p):
        for l in open(p):
            try: r = json.loads(l); cache[r['t']] = r
            except Exception: pass
    # shadow pool windows
    S = {}
    for t, r in cache.items():
        k = {int(a): tuple(v) for a, v in r['k'].items()}
        cs = cheap_side(k, r['c'])
        if not cs: continue
        sd, ask = cs; n, imb = imbalance(r['trades'], r['c'], sd)
        if n < 5 or imb is None: continue
        win = r['r'] == sd
        S[t] = dict(c=r['c'], imb=imb, ask=ask, side=sd, win=win, net=(1 - ask - fee(ask)) if win else (-ask - fee(ask)))
    first = fo[0]
    c0 = cache[first['ticker']]['c'] if first['ticker'] in cache else None
    if c0 is None:
        import datetime
        c0 = datetime.datetime.fromisoformat(first['ts'].replace('Z', '+00:00')).timestamp()
        print('note: first FLOW1 market not in cache, using order time as the start')
    low = {t: s for t, s in S.items() if s['imb'] <= THR and s['c'] >= c0 - 1}
    newest = max((r['c'] for r in cache.values()), default=0)
    filled = [o for o in fo if o['status'] == 'filled' and o.get('count')]
    done = [o for o in filled if o.get('settledPnl') is not None]
    print('FLOW1 orders %d, filled %d, settled %d | shadow low-half windows since first order: %d (cache covers markets to %s UTC)' % (
        len(fo), len(filled), len(done), len(low),
        __import__('datetime').datetime.utcfromtimestamp(newest).strftime('%m-%d %H:%M') if newest else 'n/a'))
    if low:
        ns = [s['net'] for s in low.values()]
        print('shadow low half: n %d win %.1f%% PF %.2f net %+.2fc/ct' % (len(ns), 100 * sum(s['win'] for s in low.values()) / len(ns), pf(ns), 100 * sum(ns) / len(ns)))
    print('(a) fill rate')
    if len(low) < 20: print('  n too small: %d shadow low windows (need 20); fill rate now %d/%d' % (len(low), len(filled), len(low)))
    else:
        r = len(filled) / len(low); flag(r < 0.5, 'FLOW1 filled %d of %d shadow low windows = %.0f%% (flag under 50%%)' % (len(filled), len(low), 100 * r))
    print('(b) fill price vs shadow -120 s ask')
    pairs = [(live_fill(o), S[o['ticker']]['ask']) for o in done if o['ticker'] in S]
    if pairs:
        lv = sum(a for a, b in pairs) / len(pairs); sh = sum(b for a, b in pairs) / len(pairs)
        txt = 'live avg fill %.4f vs shadow ask %.4f, diff %+.2fc over %d matched fills' % (lv, sh, 100 * (lv - sh), len(pairs))
        if len(pairs) < 10: print('  n too small: ' + txt + ' (need 10)')
        else: flag(lv - sh > 0.015, txt + ' (flag over +1.5c)')
    else: print('  n too small: no settled FLOW1 fill matched to a cached window')
    print('(c) live result')
    if done:
        w = sum(1 for o in done if o['result'] == o['side']); net = sum(o['settledPnl'] for o in done)
        print('  live settled %d, won %d (%.1f%%), net $%.2f' % (len(done), w, 100 * w / len(done), net))
        if len(done) < 20: print('  win rate: n too small (need 20)')
        else: flag(w / len(done) < 0.20, 'win rate %.1f%% (flag under 20%%)' % (100 * w / len(done)))
        if len(done) < 30 or len(low) < 30: print('  net vs shadow PF: n too small (need 30 fills and a readable shadow)')
        else:
            spf = pf([s['net'] for s in low.values()])
            flag(net < 0 and spf > 1.5, 'live net $%.2f, shadow low half PF %.2f (flag if net < 0 and PF > 1.5)' % (net, spf))
    else: print('  n too small: no settled FLOW1 fills')
    print('(d) recorded flow vs shadow imbalance')
    fk = next((k for k in ('flow', 'flowImb', 'imbalance', 'imb') if any(o.get(k) is not None for o in fo)), None)
    if not fk: print('  no recorded flow field on FLOW1 orders (looked for flow, flowImb, imbalance, imb)')
    else:
        pr = [(o[fk], S[o['ticker']]['imb']) for o in fo if o.get(fk) is not None and o['ticker'] in cache and o['ticker'] in S]
        if not pr: print('  n too small: field %s present but no matched shadow window' % fk)
        else:
            bad = sum(1 for a, b in pr if abs(a - b) > 0.05)
            txt = '%d of %d orders differ by more than 0.05 (%.0f%%) using field %s' % (bad, len(pr), 100 * bad / len(pr), fk)
            if len(pr) < 10: print('  n too small: ' + txt + ' (need 10)')
            else: flag(bad / len(pr) > 0.20, txt + ' (flag over 20%)')
main()
