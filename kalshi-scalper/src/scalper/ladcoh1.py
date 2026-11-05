"""LADCOH1: ladder coherence locks (riskless sets). Reads recorder files only; research only.
Usage: python -I ladcoh1.py daily <dir> | book <dir>   (dir holds daily/ or book/ extracted from quote-data)"""
import csv, glob, gzip, math, sys, collections

def fee(p, c=10, mult=1.0):
    return math.ceil(round(0.07 * c * p * (1 - p) * mult * 100, 6)) / 100.0

def set_net(a, b, c=10, mult=1.0):
    """buy leg at price a and leg at price b (each per contract), payout >= 1; net per set in dollars."""
    return 1.0 - a - b - (fee(a, c, mult) + fee(b, c, mult)) / c

def f(x):
    try: return float(x)
    except: return None

def good(bid, ask):
    return bid is not None and ask is not None and bid >= 0.01 and ask <= 0.99 and ask > bid

def daily(d):
    snaps = collections.defaultdict(list)
    for fn in sorted(glob.glob(d + '/daily/quotes/*/*.csv.gz')):
        for r in csv.DictReader(gzip.open(fn, 'rt')):
            snaps[fn].append(r)
    out = {'m1': [], 'b1': [], 'events': 0, 'part_ok': 0, 'part_bad': 0, 'pairs': 0}
    for fn, rows in snaps.items():
        ev = collections.defaultdict(list)
        for r in rows: ev[r['event_ticker']].append(r)
        for e, ms in ev.items():
            out['events'] += 1
            # M1 nested
            sub = []
            for r in ms:
                st = r['strike_type']
                if st in ('greater', 'greater_or_equal'):
                    k = f(r['floor_strike']); dirn = 'up'
                elif st == 'less':
                    k = f(r['cap_strike']) if r['cap_strike'] else f(r['floor_strike']); dirn = 'dn'
                else: continue
                b, a = f(r['yes_bid']), f(r['yes_ask'])
                if k is None or not good(b, a): continue
                sub.append((dirn, k, b, a, r))
            best = None
            for x in sub:
                for y in sub:
                    if x[0] != y[0] or x[1] >= y[1]: continue
                    # up: YES(y) subset of YES(x); dn: YES(x) subset of YES(y)
                    S, T = (y, x) if x[0] == 'up' else (x, y)
                    out['pairs'] += 1
                    a_leg = T[3]; b_leg = 1 - S[2]
                    n = set_net(a_leg, b_leg)
                    if best is None or n > best[0]: best = (n, S, T)
            if best and best[0] > -0.01:
                n, S, T = best
                out['m1'].append((fn[-20:], e, n, set_net(T[3], 1 - S[2], mult=1.2), S[4]['volume'], S[4]['open_interest'], T[4]['volume'], T[4]['open_interest'], S[2], T[3]))
            # B1 partition
            ty = {r['strike_type'] for r in ms}
            if 'between' in ty and ty <= {'between', 'less', 'greater'}:
                segs = sorted([(f(r['floor_strike']) if r['floor_strike'] else -1e18, f(r['cap_strike']) if r['cap_strike'] else 1e18, r) for r in ms])
                tails_ok = any(r['strike_type'] == 'less' for r in ms) and any(r['strike_type'] == 'greater' for r in ms)
                if tails_ok and len(ms) >= 3:
                    out['part_ok'] += 1
                    legs = [(f(r['yes_bid']), f(r['yes_ask'])) for _, _, r in segs]
                    if all(good(b, a) for b, a in legs):
                        sa = sum(a for b, a in legs); sb = sum(b for b, a in legs)
                        fy = sum(fee(a) for b, a in legs) / 10
                        fn_ = sum(fee(1 - b) for b, a in legs) / 10
                        out['b1'].append((fn[-20:], e, len(legs), round(sa, 3), round(sb, 3), round(1 - sa - fy, 4), round(sb - 1 - sum(1 - b for b, a in legs) + len(legs) - 1 - 0, 4) if False else round((len(legs) - 1) - sum(1 - b for b, a in legs) - fn_, 4)))
                    else:
                        out['b1'].append((fn[-20:], e, len(legs), 'illiquid', None, None, None))
                else:
                    out['part_bad'] += 1
    return out

if __name__ == '__main__':
    mode, d = sys.argv[1], sys.argv[2]
    if mode == 'daily':
        o = daily(d)
        print('event-snapshots', o['events'], 'nested pairs scanned', o['pairs'], 'partitions ok', o['part_ok'], 'not partitions', o['part_bad'])
        print('M1 near-locks (net > -1c at C=10), best pair per event-snapshot:', len(o['m1']))
        for x in sorted(o['m1'], key=lambda x: -x[2])[:15]: print(x)
        print('M1 locks >= +1c:', sum(1 for x in o['m1'] if x[2] >= 0.01), ' at fees x1.2:', sum(1 for x in o['m1'] if x[3] >= 0.01))
        liquid = [x for x in o['b1'] if x[3] != 'illiquid']
        print('B1 partitions', len(o['b1']), 'fully quoted', len(liquid))
        for x in o['b1']: print(x)

def book(d):
    files = sorted(glob.glob(d + '/book/*/*/book.csv.gz'))
    cyc_count = pairs = skew = pers = 0
    sizes = []; prev = set(); locks_all = []
    per_file = []
    for fn in files:
        rows = list(csv.DictReader(gzip.open(fn, 'rt')))
        # cycle = rows of consecutive polls; new cycle when ticker repeats
        cycles = []; cur = {}
        for r in rows:
            if r['ticker'] in cur: cycles.append(cur); cur = {}
            cur[r['ticker']] = r
        if cur: cycles.append(cur)
        prev = {}
        for cy in cycles:
            cyc_count += 1
            by_ev = collections.defaultdict(list)
            for t, r in cy.items():
                bid = f(r['yes_bid_px_1']); nb = f(r['no_bid_px_1'])
                if bid is None or nb is None: continue
                ask = 1 - nb
                if not good(bid, ask): continue
                by_ev[r['close_time']].append((f(r['strike']), bid, ask, f(r['yes_bid_sz_1']) or 0, f(r['no_bid_sz_1']) or 0, t))
            cur_locks = {}
            for ev, L in by_ev.items():
                for x in L:
                    for y in L:
                        if x[0] >= y[0]: continue
                        pairs += 1
                        # S = y (higher strike) subset of x: buy YES(x) at x.ask, NO(y) at 1-y.bid
                        n = set_net(x[2], 1 - y[1]); n12 = set_net(x[2], 1 - y[1], mult=1.2)
                        if n >= 0.01:
                            skew += 1
                            key = (x[5], y[5]); cur_locks[key] = (n, n12, min(x[4], y[3]) , x[1], x[2], y[1], y[2])
            for k, v in cur_locks.items():
                if k in prev:
                    pers += 1; sizes.append(v[2]); locks_all.append((fn[-30:], k, v))
            prev = cur_locks
    return dict(files=len(files), cycles=cyc_count, pairs=pairs, crossings=skew, persistent=pers, sizes=sizes, locks=locks_all)

if __name__ == '__main__' and sys.argv[1] == 'book':
    o = book(sys.argv[2])
    print({k: v for k, v in o.items() if k not in ('sizes', 'locks')})
    print('persistent sizes', sorted(o['sizes'])[:5], '...', sorted(o['sizes'])[-5:] if o['sizes'] else None)
    for x in o['locks'][:20]: print(x)
