"""PERPEQ cost map: spreads and touch sizes of active equity/ETF/index perps. Information only, no returns.
Reads origin/perp-data samples (given as CSVs) and one live margin/markets JSON. Prints a table and writes a CSV."""
import csv, json, sys, statistics as st, collections
files, live, out = sys.argv[1].split(','), sys.argv[2], sys.argv[3]
obs = collections.defaultdict(list)   # ticker -> [(label, spread_bp, touch_usd_bid, touch_usd_ask)]
def add(label, tk, bid, ask, bs, as_, px):
    if bid <= 0 or ask <= 0 or ask > 1e9: return
    mid = (bid + ask) / 2
    obs[tk].append((label, (ask - bid) / mid * 1e4, bs * bid, as_ * ask))
for f in files:
    for r in csv.DictReader(open(f)):
        if r['asset_class'] not in ('Equities', 'Indices') or r['status'] != 'active': continue
        add(r['ts_utc'][:16] + 'Z', r['ticker'], float(r['bid']), float(r['ask']), float(r['bid_size']), float(r['ask_size']), float(r['price']))
for m in json.load(open(live))['markets']:
    if m['asset_class'] in ('Equities', 'Indices') and m['status'] == 'active':
        add('live', m['ticker'], float(m['bid']), float(m['ask']), float(m['bid_size_fp']), float(m['ask_size_fp']), 0)
labels = sorted({o[0] for v in obs.values() for o in v})
w = csv.writer(open(out, 'w'))
w.writerow(['ticker', 'n_obs', 'median_spread_bp', 'max_spread_bp', 'median_touch_usd_min_side'] + ['sp_' + l for l in labels])
rows = []
for tk, v in obs.items():
    sp = [o[1] for o in v]; touch = [min(o[2], o[3]) for o in v]
    d = {o[0]: o[1] for o in v}
    rows.append([tk, len(v), round(st.median(sp), 2), round(max(sp), 2), round(st.median(touch))] + [round(d[l], 1) if l in d else '' for l in labels])
rows.sort(key=lambda r: r[2])
for r in rows: w.writerow(r)
print('labels', labels)
for r in rows: print(r)
