"""REMATCH: counts from a market listing. Times and tickers only: no price and no result is read or printed.
Usage: python3 -I count_listing.py <folder with NNNN.json.gz list answers>"""
import sys, gzip, json, glob, re, collections, datetime
from zoneinfo import ZoneInfo
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
from deskb_guard import refuse_all as _refuse_all
_refuse_all()   # standing rule (h): refuse any HELDOUT_ folder before the first open or glob
ET = ZoneInfo('America/New_York')
MON = {m: i + 1 for i, m in enumerate('JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split())}
SERIES = ('KXESOCCERGAME', 'KXEBASKETBALLGAME')
GAP_MIN, GAP_MAX, SETTLED_BEFORE = 20, 60, 12   # minutes; the registered constants

def ts(x):
    return datetime.datetime.fromisoformat(x.replace('Z', '+00:00')).timestamp() if x else None

ev = collections.defaultdict(dict)
for f in sorted(glob.glob(sys.argv[1] + '/0*.json.gz')):
    try:
        j = json.load(gzip.open(f))
    except Exception:
        continue
    for m in (j.get('markets', []) if isinstance(j, dict) else []):
        t = m.get('event_ticker') or ''
        s = t.split('-')[0]
        if s not in SERIES:
            continue
        e = ev[s].setdefault(t, {})
        e[m['ticker'].rsplit('-', 1)[1]] = (ts(m.get('settlement_ts')), ts(m.get('open_time')))
for s in SERIES:
    recs = []
    for t, e in ev[s].items():
        m = re.match(r'(\d{2})([A-Z]{3})(\d{2})(\d{2})(\d{2})', t.split('-', 1)[1])
        sufs = tuple(sorted(x for x in e if x != 'TIE'))
        if not m or len(sufs) != 2:
            continue
        yy, mon, dd, hh, mi = m.groups()
        S = datetime.datetime(2000 + int(yy), MON[mon], int(dd), int(hh), int(mi), tzinfo=ET).timestamp()
        sett = max((v[0] or 0) for v in e.values())
        opn = min((v[1] or 9e18) for v in e.values())
        recs.append((sufs, S, sett, opn))
    by = collections.defaultdict(list)
    for r in recs:
        by[r[0]].append(r)
    nxt = in_gap = settled = open_ok = 0
    days = collections.Counter()
    for rs in by.values():
        rs.sort(key=lambda r: r[1])
        for a, b in zip(rs, rs[1:]):
            nxt += 1
            g = (b[1] - a[1]) / 60
            if not (GAP_MIN <= g <= GAP_MAX):
                continue
            in_gap += 1
            if not (a[2] and a[2] <= b[1] - SETTLED_BEFORE * 60):
                continue
            settled += 1
            if b[3] <= a[1] - 3 * 60:
                open_ok += 1
    print('%s: matches %d, pairs %d, next meetings of the same pair %d, of those %d to %d minutes after the earlier start %d, earlier one settled %d+ minutes before the later start %d, later market already open 3 minutes before the earlier start %d'
          % (s, len(recs), len(by), nxt, GAP_MIN, GAP_MAX, in_gap, SETTLED_BEFORE, settled, open_ok))
