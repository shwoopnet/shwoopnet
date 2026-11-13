#!/usr/bin/env python3
"""W126 S-OIRLOW1 forward tracker. Read only, public Kalshi endpoints, no secret.
Registered (REFINE_STATUS.md 2026-11-04 07:33 AM CT): Bitcoin KXBTC15M windows closing after 2026-11-04T14:00:00Z;
OIR = OI(candle ending close-180) - OI(candle ending close-360) in [60000, 86300); cheap side (lower ask side)
ask 0.05..0.50 at close-180; fill at that side's ask on the candle ending close-120; hold to settlement;
fee 0.07*p*(1-p) rounded up to the cent per 10 contracts; read once at 40 windows. Information only."""
import json, subprocess, sys, time, datetime, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
B = "https://api.elections.kalshi.com/trade-api/v2"; SER = "KXBTC15M"
START = "2026-11-04T14:00:00Z"; LO, HI = 60000, 86300; TARGET = 40
CAP = int(os.environ.get('W126_CAP', '40'))
CACHE = os.path.join(HERE, 'oirlow1_cache.jsonl'); LOCK = os.path.join(HERE, 'oirlow1_cache.lock')
def epoch(s): return int(datetime.datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp())
def fee(p): return math.ceil(round(0.07 * 10 * p * (1 - p) * 100, 9)) / 100 / 10  # per contract, rounded up per 10
_last = [0.0]
def get(u, tries=8):
    wait = 2
    for _ in range(tries):
        dt = time.time() - _last[0]
        if dt < 0.5: time.sleep(0.5 - dt)
        _last[0] = time.time()
        r = subprocess.run(['curl', '-sS', '-m', '40', '-w', '\n%{http_code}', u], capture_output=True, text=True)
        if '\n' not in r.stdout: time.sleep(wait); continue
        b, c = r.stdout.rsplit('\n', 1); c = int(c) if c.isdigit() else 0
        if c == 200:
            try: return json.loads(b)
            except Exception: pass
        if c in (429, 0) or c >= 500: time.sleep(wait); wait = min(wait * 2, 60); continue
        return None
    return None
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
def candles(tk, c):
    d = get(B + "/series/%s/markets/%s/candlesticks?start_ts=%d&end_ts=%d&period_interval=1" % (SER, tk, c - 660, c))
    if not d: return None
    k = {}
    for x in d.get('candlesticks', []):
        try: k[str(int(x['end_period_ts']))] = [float(x['yes_ask']['close_dollars']), float(x['yes_bid']['close_dollars']), float(x.get('open_interest_fp') or 0)]
        except Exception: pass
    return k
def trigger(k, c):
    try:
        a = k[c - 180]; b = k[c - 360]; f = k[c - 120]
    except KeyError: return None
    if a[2] <= 0 or b[2] <= 0: return None
    oir = a[2] - b[2]
    if not (LO <= oir < HI): return None
    for s, ask in (('yes', a[0]), ('no', 1 - a[1])):
        if 0.05 - 1e-9 <= ask <= 0.5 + 1e-9:
            p = f[0] if s == 'yes' else 1 - f[1]
            return (s, p, oir) if 0 < p < 1 else None
    return None
def pf(ns):
    g = sum(x for x in ns if x > 0); l = -sum(x for x in ns if x < 0)
    return g / l if l else float('inf')
def main():
    since = epoch(START)
    if os.path.exists(LOCK) and time.time() - os.path.getmtime(LOCK) < 900:
        print('W126: another run holds the lock; reading cache only'); locked = False
    else:
        open(LOCK, 'w').write(str(os.getpid())); locked = True
    cache = {}
    if os.path.exists(CACHE):
        for l in open(CACHE):
            try: r = json.loads(l); cache[r['t']] = r
            except Exception: pass
    try:
        if locked:
            mk = sorted([m for m in list_markets(since) if m['c'] > since and 'EST' not in m['t']], key=lambda m: m['c'])
            print('settled KXBTC15M markets closing after %s: %d (cached %d)' % (START, len(mk), sum(m['t'] in cache for m in mk)))
            f = open(CACHE, 'a'); newn = 0; pend = 0
            for m in mk:
                if m['t'] in cache: continue
                if newn >= CAP: pend += 1; continue
                newn += 1; k = candles(m['t'], m['c'])
                if k is None: print('skip (fetch failed)', m['t']); continue
                r = {'t': m['t'], 'c': m['c'], 'r': m['r'], 'k': k}
                f.write(json.dumps(r) + "\n"); f.flush(); cache[m['t']] = r
            if pend: print('W126 CAP: fetched %d new windows, %d still uncached (re-run to catch up)' % (newn, pend))
    finally:
        if locked and os.path.exists(LOCK): os.remove(LOCK)
    T = []
    for r in sorted(cache.values(), key=lambda r: r['c']):
        if r['c'] <= since: continue
        k = {int(a): v for a, v in r['k'].items()}
        tg = trigger(k, r['c'])
        if not tg: continue
        s, p, oir = tg; win = r['r'] == s
        T.append(dict(t=r['t'], win=win, net=(1 - p - fee(p)) if win else (-p - fee(p))))
    n = len(T); w = sum(t['win'] for t in T); ns = [t['net'] for t in T]
    print('S-OIRLOW1 windows %d wins %d PF %s net %s c/ct   %d of %d' % (n, w, ('%.2f' % pf(ns)) if ns else 'n/a', ('%+.2f' % (100 * sum(ns) / n)) if n else 'n/a', n, TARGET))
    if n >= TARGET:
        print('READ-READY: S-OIRLOW1 at %d windows (registered read at 40): net %+.2f c/ct, PF %.2f. Positive net and PF>=1.5 = smooth effect; zero or negative = warning for Nov 13, not a kill.' % (n, 100 * sum(ns) / n, pf(ns)))
main()
