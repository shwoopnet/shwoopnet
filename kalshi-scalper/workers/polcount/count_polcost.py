"""Politics lane count from the Testing Desk's POLCOST snapshot (open markets of 79 daily, weekly or monthly
Politics series, pull/TESTING_LISTS_BUNDLE, requests with id prefix pc_). No request. Open markets only, so no
result exists; of each market only the ticker, event, close time and whether its quote is two-sided and how wide
are read. No price level is printed.
Usage: python3 -I count_polcost.py <run folder of pull/TESTING_LISTS_BUNDLE> [series_partial.json]"""
import gzip, json, sys, collections, datetime, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from deskb_guard import refuse_all
refuse_all()
D = sys.argv[1]
titles = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
m = json.load(open(os.path.join(D, 'manifest.json')))
def ts(x):
    try: return datetime.datetime.fromisoformat(x.replace('Z', '+00:00')).timestamp()
    except Exception: return None
def num(x):
    try: return float(x)
    except Exception: return None
now = None; per = collections.OrderedDict(); asked = 0
for r in m['rows']:
    if not r['id'].startswith('pc_'): continue
    s = r['params']['series_ticker']; asked += (r.get('page', 1) == 1)
    now = max(now or 0, r['t_recv_ms'] / 1000)
    try: body = json.load(gzip.open(os.path.join(D, r['file'])))
    except Exception: body = {}
    per.setdefault(s, []).extend(body.get('markets', []) if isinstance(body, dict) else [])
print('snapshot', datetime.datetime.fromtimestamp(now, datetime.timezone.utc).strftime('%Y-%m-%d %H:%MZ'), '| series asked', asked, '| with an open market', sum(1 for v in per.values() if v), '| open markets', sum(len(v) for v in per.values()))
print('series | title | open markets | events | closing in 7 d: markets, events | in 14 d: markets, two-sided, spread 4c or less | in 30 d: markets, two-sided, spread 4c or less | beyond 30 d')
tot = collections.Counter(); ev7 = set(); ev30 = set()
for s, ms in sorted(per.items(), key=lambda kv: -len(kv[1])):
    if not ms: continue
    c = collections.Counter(); e7 = set(); ev = set()
    for x in ms:
        ct = ts(x.get('close_time') or ''); d = (ct - now) / 86400 if ct else 9999
        b = num(x.get('yes_bid_dollars', x.get('yes_bid'))); a = num(x.get('yes_ask_dollars', x.get('yes_ask')))
        if b is not None and a is not None and (b > 1 or a > 1): b, a = b / 100, a / 100
        two = b is not None and a is not None and 0 < b < a < 1; tight = two and a - b <= 0.04 + 1e-9
        ev.add(x.get('event_ticker'))
        for lim in (7, 14, 30):
            if d <= lim: c['m%d' % lim] += 1; c['two%d' % lim] += two; c['t%d' % lim] += tight
        if d <= 7: e7.add(x.get('event_ticker')); ev7.add(x.get('event_ticker'))
        if d <= 30: ev30.add(x.get('event_ticker'))
        if d > 30: c['later'] += 1
    tot.update(c); tot['mk'] += len(ms)
    t = (titles.get(s) or {}).get('title') or ''; f = (titles.get(s) or {}).get('frequency') or ''
    print(f"{s} | {t[:48]} ({f}) | {len(ms)} | {len(ev)} | {c['m7']}, {len(e7)} | {c['m14']}, {c['two14']}, {c['t14']} | {c['m30']}, {c['two30']}, {c['t30']} | {c['later']}")
print(f"ALL | | {tot['mk']} | | {tot['m7']}, {len(ev7)} | {tot['m14']}, {tot['two14']}, {tot['t14']} | {tot['m30']}, {tot['two30']}, {tot['t30']} | {tot['later']}")
print('events closing in 7 days', len(ev7), '| events closing in 30 days', len(ev30))
FAMILY = {
 'approval and favourability': ['KXTRUMPAPPROVE','KXAPRPOTUS','KXTRUMPVH','KXTRUMPFAV','538APPROVE','APRPOTUS','KX538APPROVE','KXVOTEHUBTRUMPUPDOWN'],
 'generic ballot': ['KXVHGCB','KXGENERICBALLOTVOTEHUB'],
 'shipping and straits counts': ['KXBABELMANDEBWEEKLY','KXHORMUZWEEKLY','KXPANAMAWEEKLY','KXSUEZWEEKLY','KXHORMUZPEAK','KXHORMUZMAX','KXMAXSHIPSHORMUZ'],
 'single questions and scheduled events': ['KXEPSTEIN','KXLEAVECONGRESS','KXMAMDANIEO','KXNEWDEAL','KXNEWTARIFFS','KXUKPOLLFIRST','KXFRPROTEST','KXLVL4WARNING','KXUSUNSCVETO','KXTORYMPJOINREFORM','KXLEADERCOMBOOUT','KXTRUMPVISITGREENLAND','KXUSCANADATARIFFDOWN','KXUSCANADATARIFFUP'],
}
FAM = {x: f for f, ss in FAMILY.items() for x in ss}
fam = collections.defaultdict(collections.Counter); fev = collections.defaultdict(lambda: collections.defaultdict(set)); fser = collections.defaultdict(set)
for s, ms in per.items():
    f = FAM.get(s, 'activity counts (orders, posts, acts, visits, judges, pardons, bills)')
    fam[f]['asked'] += 1
    if ms: fser[f].add(s)
    for x in ms:
        ct = ts(x.get('close_time') or ''); d = (ct - now) / 86400 if ct else 9999
        b = num(x.get('yes_bid_dollars', x.get('yes_bid'))); a = num(x.get('yes_ask_dollars', x.get('yes_ask')))
        if b is not None and a is not None and (b > 1 or a > 1): b, a = b / 100, a / 100
        two = b is not None and a is not None and 0 < b < a < 1; tight = two and a - b <= 0.04 + 1e-9
        fam[f]['mk'] += 1
        for lim in (7, 14, 30):
            if d <= lim:
                fam[f]['m%d' % lim] += 1; fam[f]['two%d' % lim] += two; fam[f]['t%d' % lim] += tight; fev[f]['e%d' % lim].add(x.get('event_ticker'))
                if tight: fev[f]['te%d' % lim].add(x.get('event_ticker'))
print()
print('family | series asked | with an open market | open markets | closing in 7 d: markets, events | in 14 d: markets, two-sided, spread 4c or less | in 30 d: markets, two-sided, spread 4c or less | events in 30 d | events with a tight market in 30 d')
for f in sorted(fam, key=lambda f: -fam[f]['mk']):
    c = fam[f]; e = fev[f]
    print(f"{f} | {c['asked']} | {len(fser[f])} | {c['mk']} | {c['m7']}, {len(e['e7'])} | {c['m14']}, {c['two14']}, {c['t14']} | {c['m30']}, {c['two30']}, {c['t30']} | {len(e['e30'])} | {len(e['te30'])}")
print('series asked with no open market:', ' '.join(s for s, v in per.items() if not v))
