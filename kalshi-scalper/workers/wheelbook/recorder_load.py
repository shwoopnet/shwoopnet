"""Concurrency estimate for a book recorder, from the Nov 10 census listing. Times and tickers only."""
import gzip, json, glob, re, collections, datetime, sys
from zoneinfo import ZoneInfo
ET = ZoneInfo('America/New_York'); MON = {m: i + 1 for i, m in enumerate('JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split())}
def ts(x): return datetime.datetime.fromisoformat(x.replace('Z', '+00:00')).timestamp() if x else None
def start(ev):
    m = re.match(r'(\d{2})([A-Z]{3})(\d{2})(\d{2})(\d{2})', ev.split('-', 1)[1])
    if not m: return None
    yy, mon, dd, hh, mi = m.groups()
    return datetime.datetime(2000 + int(yy), MON[mon], int(dd), int(hh), int(mi), tzinfo=ET).timestamp()
FAST = {'KXESOCCERGAME': 600, 'KXLIGAPROMATCH': 120, 'KXEBASKETBALLGAME': 120, 'KXCS2GAME': 0, 'KXDOTA2GAME': 0}     # seconds before S that the fast tier starts
SLOW = {'KXESOCCERGAME': None, 'KXCS2GAME': 2700, 'KXDOTA2GAME': 2700}                                             # None = from the open; else seconds before S
MAPS = ('KXCS2MAP', 'KXDOTA2MAP')
fast = collections.Counter(); slow = collections.Counter(); perfam = collections.defaultdict(collections.Counter); n = collections.Counter()
for f in sorted(glob.glob(sys.argv[1] + '/0*.json.gz')):
    try: j = json.load(gzip.open(f))
    except Exception: continue
    for m in (j.get('markets', []) if isinstance(j, dict) else []):
        ev = m.get('event_ticker') or ''; s = ev.split('-')[0]
        c, o = ts(m.get('close_time')), ts(m.get('open_time'))
        if not c or not o: continue
        if s in FAST:
            S = start(ev)
            if S is None: continue
            n[s] += 1
            a = S - FAST[s]
            for t in range(int(a // 60), int(c // 60) + 1): fast[t] += 1; perfam[s][t] += 1
            sl = o if SLOW.get(s, 0) is None else (S - SLOW[s] if s in SLOW else None)
            if sl is not None:
                for t in range(int(sl // 60), int(a // 60)): slow[t] += 1
        elif s in MAPS:
            n[s] += 1
            S = start(ev)
            if S is None: continue
            for t in range(int(S // 60), int(c // 60) + 1): slow[t] += 1
day0 = int(datetime.datetime(2026, 11, 10, 6, tzinfo=datetime.timezone.utc).timestamp() // 60); day1 = day0 + 18 * 60   # the 18 hours of Nov 10 the listing covers best
fm = [fast[t] for t in range(day0, day1)]; sm = [slow[t] for t in range(day0, day1)]
print('markets counted', dict(n))
print('FAST tier tickers at once, 06:00 to 24:00 UTC Nov 10: mean %.0f, median %d, p95 %d, max %d' % (sum(fm) / len(fm), sorted(fm)[len(fm) // 2], sorted(fm)[int(len(fm) * .95)], max(fm)))
for s in FAST:
    v = [perfam[s][t] for t in range(day0, day1)]
    print('   ', s, 'mean %.1f max %d' % (sum(v) / len(v), max(v)))
print('SLOW tier tickers at once: mean %.0f, p95 %d, max %d' % (sum(sm) / len(sm), sorted(sm)[int(len(sm) * .95)], max(sm)))
print('fast ticker-polls a day at 3 s (mean x 28,800): %.2f million' % (sum(fm) / len(fm) * 28800 / 1e6), '| slow ticker-polls a day at 60 s: %.0f thousand' % (sum(sm) / len(sm) * 1440 / 1e3))
