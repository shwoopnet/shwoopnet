"""Politics recorder count: markets, events, closes and spread level per series. No result and no price level is printed
(two-sidedness and spread only). Usage: python3 -I count_polrec.py <folder holding polrec/...>"""
import gzip, csv, glob, sys, collections, datetime, statistics
S = sys.argv[1]
def ts(x):
    try: return datetime.datetime.fromisoformat(x.replace('Z', '+00:00')).timestamp()
    except Exception: return None
def num(x):
    try: return float(x)
    except Exception: return None
latest = {}; first_seen = {}
for f in sorted(glob.glob(S + '/polrec/*/*/quotes.csv.gz')):
    for r in csv.DictReader(gzip.open(f, 'rt')):
        t = num(r['t_recv_ms'])
        latest[r['ticker']] = r
        first_seen.setdefault(r['ticker'], t)
closed = {}
for f in sorted(glob.glob(S + '/polrec/*/*/results.csv.gz')):
    for r in csv.DictReader(gzip.open(f, 'rt')):
        closed[r['ticker']] = (r['series'], r['event_ticker'], ts(r['close_time']))
now = max(num(r['t_recv_ms']) for r in latest.values()) / 1000
print('files end at', datetime.datetime.fromtimestamp(now, datetime.timezone.utc).strftime('%Y-%m-%d %H:%MZ'), '| open markets seen', len(latest), '| markets in results files', len(closed))
by = collections.defaultdict(list)
for r in latest.values(): by[r['series']].append(r)
cs = collections.defaultdict(list)
for tk, (s, ev, c) in closed.items(): cs[s].append((ev, c))
print('series | open mkts | events | two-sided | median spread c | two-sided with spread<=4c | closing <=7d | <=14d | <=30d | closed in results (mkts/events, span days)')
tot = collections.Counter()
for s in sorted(set(by) | set(cs), key=lambda s: -len(by.get(s, []))):
    rows = by.get(s, [])
    ev = {r['event_ticker'] for r in rows}
    two = []; d7 = d14 = d30 = 0
    for r in rows:
        b, a = num(r['yes_bid']), num(r['yes_ask'])
        if b is not None and a is not None:
            if b > 1 or a > 1: b, a = b / 100, a / 100
            if 0 < b < a < 1: two.append(a - b)
        c = ts(r['close_time'])
        if c:
            d = (c - now) / 86400
            d7 += d <= 7; d14 += d <= 14; d30 += d <= 30
    cl = cs.get(s, [])
    span = (max(c for _, c in cl if c) - min(c for _, c in cl if c)) / 86400 if len([1 for _, c in cl if c]) > 1 else 0
    print(f"{s} | {len(rows)} | {len(ev)} | {len(two)} | {('%.0f' % (100 * statistics.median(two))) if two else '-'} | {sum(1 for x in two if x <= 0.04 + 1e-9)} | {d7} | {d14} | {d30} | {len(cl)}/{len({e for e, _ in cl})}, {span:.1f}")
    tot['open'] += len(rows); tot['two'] += len(two); tot['tight'] += sum(1 for x in two if x <= 0.04 + 1e-9); tot['d7'] += d7; tot['d14'] += d14; tot['d30'] += d30; tot['closed'] += len(cl)
print('TOTAL', dict(tot))
