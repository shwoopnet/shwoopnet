"""MADE-UP bets to test POLGAPH's pooling block. Not real markets. Usage: make_pool_fixture.py <out> <case>"""
import gzip, json, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo
out, case = sys.argv[1], sys.argv[2]
SPEC = {  # family: (series, wins, losses)
 'pooled_fails_dominant_family': {'activity counts': ('KXTRUTHSOCIAL', 130, 70), 'shipping counts': ('KXHORMUZWEEKLY', 100, 100), 'single questions': ('KXMAMDANIEO', 98, 102)},
 'two_families_exceed_half': {'activity counts': ('KXTRUTHSOCIAL', 160, 40), 'shipping counts': ('KXHORMUZWEEKLY', 160, 40), 'single questions': ('KXMAMDANIEO', 25, 35)},
 'no_family_over_half': {'activity counts': ('KXTRUTHSOCIAL', 110, 40), 'shipping counts': ('KXHORMUZWEEKLY', 110, 40), 'single questions': ('KXMAMDANIEO', 110, 40)},
}[case]
ET = ZoneInfo('America/New_York'); os.makedirs(os.path.join(out, 'lists'), exist_ok=True); os.makedirs(os.path.join(out, 'minute'), exist_ok=True)
looks = [int(datetime(2026, 10, 1, 7, tzinfo=ET).timestamp()), int(datetime(2026, 10, 20, 7, tzinfo=ET).timestamp())]
dec, rows, mrows, k = [], [], [], 0
for fam, (ser, w, l) in SPEC.items():
    mk = []
    for i in range(w + l):
        res = 'yes' if i < w else 'no'
        # spread wins and losses evenly over the two halves: pair index parity decides the half
        half = (i if i < w else i - w) % 2
        look = looks[half]; tk = '%s-E%04d-T1' % (ser, i); ev = '%s-E%04d' % (ser, i)
        mk.append({'ticker': tk, 'event_ticker': ev, 'open_time': '2026-09-20T00:00:00Z', 'close_time': '2026-10-25T00:00:00Z', 'result': res})
        dec.append({'ticker': tk, 'event': ev, 'series': ser, 'family': fam, 'morning': '2026-10-01' if half == 0 else '2026-10-20', 'look': look, 'side': 'yes', 'ask': 0.49, 'bid': 0.47, 'gap': 0.06, 'close': 1793145600})
    k += 1; fn = '%04d.json.gz' % k; json.dump({'markets': mk}, gzip.open(os.path.join(out, 'lists', fn), 'wt'))
    rows.append({'id': 'set_' + ser, 'status': 200, 'file': fn, 'params': {'series_ticker': ser}})
json.dump({'rows': rows}, open(os.path.join(out, 'lists', 'manifest.json'), 'w'))
dec.sort(key=lambda r: (r['look'], r['ticker']))
json.dump({'counts': {'made_up': 1}, 'cost_rows': [{'family': r['family'], 'ask': 0.49, 'mid': 0.48} for r in dec], 'decisions': dec, 'baseline': []}, open(os.path.join(out, 'decisions.json'), 'w'))
for j, look in enumerate(looks):
    tks = [r['ticker'] for r in dec if r['look'] == look]
    for c in range(0, len(tks), 100):
        fn = '%04d.json.gz' % (len(mrows) + 1); json.dump({'markets': []}, gzip.open(os.path.join(out, 'minute', fn), 'wt'))
        mrows.append({'id': 'm%d_%d' % (look, c), 'status': 200, 'file': fn, 'params': {'market_tickers': ','.join(tks[c:c + 100]), 'start_ts': look, 'end_ts': look + 60, 'period_interval': 1}})
json.dump({'rows': mrows}, open(os.path.join(out, 'minute', 'manifest.json'), 'w'))
