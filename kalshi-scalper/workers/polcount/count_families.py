"""Politics lane count by family, from the politics recorder's files. No result and no price level is read or printed:
only tickers, events, close times, and whether a quote is two-sided and how wide.
Usage: python3 -I count_families.py <folder holding polrec/...>"""
import gzip, csv, glob, sys, collections, datetime
S = sys.argv[1]
FAMILY = {
    'approval': ['KXTRUMPAPPROVE', 'KXAPRPOTUS', 'KXAPRPOTUSD', 'KXTRUMPVH', 'KXVOTEHUBTRUMPUPDOWN'],
    'generic ballot': ['KXVHGCB', 'KXGENERICBALLOTVOTEHUB'],
    'activity counts (orders, posts, acts, endorsements, nominations)': ['KXEOWEEK', 'KXTRUTHSOCIAL', 'KXTRUMPACT', 'KXTRUMPENDORSEMENTS', 'KXTRUMPNOMNUM', 'KXTRUMPPHOTO', 'KXTRUMPNUMSTATES', 'KXTRUMPMEET', 'KXBILLSCOUNT', 'KXTRUMPTIME', 'KXCABLEAVE', 'KXACTBLUETOP', 'KXLAGODAYS', 'KXWHVISIT'],
    'shipping and straits counts (foreign)': ['KXBABELMANDEBWEEKLY', 'KXSUEZWEEKLY', 'KXPANAMAWEEKLY', 'KXHORMUZWEEKLY', 'KXHORMUZPEAK', 'KXHORMUZMAX'],
    'scheduled-event politics (votes, bills, deadlines, confirmations)': ['KXMAMDANIEO', 'KXNEWTARIFFS', 'KXEPSTEIN', 'KXZACHARIAOUT', 'KXGOVTSHUTDOWN', 'KXGOVTSHUTLENGTH', 'KXSAVEACT', 'KXNEXTPRESSECPERM', 'KXCRYPTOSTRUCTURE', 'KXMJSCHEDULE', 'KXELECTIONBILL', 'KXGAMBLINGREPEAL', 'KXACAEXT', 'KXFISAEXTEND', 'KX250DOLLARBILL'],
    'post-midterm (recounts)': ['KXSENATEREC', 'KXRECNCH', 'KXRECNCBILL'],
}
FAM = {s: f for f, ss in FAMILY.items() for s in ss}
def ts(x):
    try: return datetime.datetime.fromisoformat(x.replace('Z', '+00:00')).timestamp()
    except Exception: return None
def num(x):
    try: return float(x)
    except Exception: return None
latest = {}
for f in sorted(glob.glob(S + '/polrec/*/*/quotes.csv.gz')):
    for r in csv.DictReader(gzip.open(f, 'rt')):
        latest[r['ticker']] = r
now = max(num(r['t_recv_ms']) for r in latest.values()) / 1000
print('recorder files end', datetime.datetime.fromtimestamp(now, datetime.timezone.utc).strftime('%Y-%m-%d %H:%MZ'), '| open markets inside the 30 day cap:', len(latest))
agg = collections.defaultdict(lambda: collections.defaultdict(set)); cnt = collections.defaultdict(collections.Counter)
for r in latest.values():
    fam = FAM.get(r['series'], 'unmapped: ' + r['series'])
    c = ts(r['close_time']); d = (c - now) / 86400 if c else 999
    b, a = num(r['yes_bid']), num(r['yes_ask'])
    if b is not None and a is not None and (b > 1 or a > 1): b, a = b / 100, a / 100
    two = b is not None and a is not None and 0 < b < a < 1
    tight = two and a - b <= 0.04 + 1e-9
    agg[fam]['series'].add(r['series']); agg[fam]['events'].add(r['event_ticker'])
    cnt[fam]['markets'] += 1
    for lim, key in ((7, '7'), (14, '14'), (30, '30')):
        if d <= lim:
            agg[fam]['ev' + key].add(r['event_ticker']); cnt[fam]['m' + key] += 1
            cnt[fam]['two' + key] += two; cnt[fam]['tight' + key] += tight
            if tight: agg[fam]['tev' + key].add(r['event_ticker'])
print('family | series with an open market | open markets | events | closing in 7 days: markets, EVENTS | two-sided in 14 d | in 30 d | spread 4c or less in 14 d | in 30 d | events with a tight market in 30 d | weeks to 60 EVENT signals at 10/25/50%')
for fam in sorted(cnt, key=lambda f: -cnt[f]['markets']):
    a, c = agg[fam], cnt[fam]
    ew = len(a['ev7'])
    wk = '/'.join(('%.0f' % (60 / (ew * p))) if ew else 'never' for p in (0.10, 0.25, 0.50))
    print(f"{fam} | {len(a['series'])} | {c['markets']} | {len(a['events'])} | {c['m7']}, {ew} | {c['two14']} | {c['two30']} | {c['tight14']} | {c['tight30']} | {len(a['tev30'])} | {wk}")
allev = set().union(*[agg[f]['ev7'] for f in agg])
print('ALL recorded families pooled: events closing in 7 days', len(allev), '| weeks to 60 event signals at 10/25/50%:', '/'.join('%.0f' % (60 / (len(allev) * p)) for p in (0.10, 0.25, 0.50)))
listed = sum(len(v) for v in FAMILY.values()); print('series in the family map', listed, '| with an open market inside the cap', len({r['series'] for r in latest.values()}))
