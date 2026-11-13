"""MAPBREAK lists: counts from tickers, strikes and close times only. No price and no result is read."""
import json, gzip, os, sys, collections, datetime
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
from deskb_guard import refuse_all as _refuse_all
_refuse_all()   # standing rule (h): refuse any HELDOUT_ folder before the first open or glob
S = sys.argv[1]
m = json.load(open(S + '/manifest.json'))
live = collections.defaultdict(lambda: collections.defaultdict(dict)); hist = collections.defaultdict(dict); pages = collections.Counter()
def ts(x): return datetime.datetime.fromisoformat(x.replace('Z', '+00:00')).timestamp() if x else None
for r in m['rows']:
    if r.get('status') != 200 or not str(r.get('id', '')).startswith(('live_', 'hist_')): continue
    kind, series = r['id'].split('_', 1)
    pages[r['id']] += 1
    body = json.load(gzip.open(os.path.join(S, r['file']), 'rt'))
    for mk in body.get('markets', []) if isinstance(body, dict) else []:
        tk, ev = mk.get('ticker', ''), mk.get('event_ticker', '')
        key = ev.split('-', 1)[1] if '-' in ev else ''
        rec = {'tk': tk, 'close': ts(mk.get('close_time')), 'strike': mk.get('floor_strike'), 'ev': ev}
        if kind == 'live': live[series][ev][tk] = rec
        else: hist[series][tk] = rec
f = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime('%Y-%m-%d')
CUT = datetime.datetime(2026, 9, 12, tzinfo=datetime.timezone.utc).timestamp()
print('sample tickers:', [next(iter(next(iter(live[s].values())))) for s in ('KXCS2GAME', 'KXCS2MAP', 'KXCS2TOTALMAPS')])
print('sample total-maps strikes:', collections.Counter(str(r['strike']) for e in live['KXCS2TOTALMAPS'].values() for r in e.values()).most_common(6))
tot_live_bo3 = 0
for title in ('CS2', 'DOTA2', 'VALORANT', 'LOL'):
    g, mp, tm = live['KX%sGAME' % title], live['KX%sMAP' % title], live['KX%sTOTALMAPS' % title]
    keys = {ev.split('-', 1)[1] for ev in g}
    # map events may be keyed <key>-<n>; collect map numbers per match key
    mapnums = collections.defaultdict(set)
    for ev, mk in mp.items():
        for tk in mk:
            rest = tk.split('-', 1)[1]
            for k in keys:
                if rest.startswith(k + '-'):
                    seg = rest[len(k) + 1:].split('-')[0]
                    if seg.isdigit(): mapnums[k].add(int(seg))
    strikes = collections.defaultdict(set)
    for ev, mk in tm.items():
        k = ev.split('-', 1)[1]
        for r in mk.values():
            try: strikes[k].add(float(r['strike']))
            except (TypeError, ValueError): strikes[k].add(str(r['tk'].rsplit('-', 1)[1]))
    bo3 = [k for k in keys if strikes.get(k) and max((s for s in strikes[k] if isinstance(s, float)), default=0) == 2.5 and {1, 2} <= mapnums.get(k, set())]
    tot_live_bo3 += len(bo3)
    share = len(bo3) / max(1, len(keys))
    h = hist['KX%sGAME' % title]
    hev = collections.defaultdict(list)
    for r in h.values(): hev[r['ev']].append(r['close'] or 0)
    hc = [max(v) for v in hev.values()]
    before = [c for c in hc if c and c < CUT]
    print(f"{title}: LIVE window match events {len(keys)} | with a total-maps event {len([k for k in keys if k in strikes])} | best-of-three by the registered test {len(bo3)} ({100 * share:.0f}%) | "
          f"HISTORY match events {len(hev)} (list pages {pages['hist_KX%sGAME' % title]}{', page cap reached, more exist' if pages['hist_KX%sGAME' % title] >= 10 else ''}) closes {f(min(hc)) if hc else '-'} to {f(max(hc)) if hc else '-'} | before 2026-09-12: {len(before)} | "
          f"if the live best-of-three share held: about {round(len(before) * share)}")
print('LIVE best-of-three total', tot_live_bo3)
