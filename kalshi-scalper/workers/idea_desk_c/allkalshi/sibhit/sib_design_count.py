# Design count run Nov 15 ~21:40Z on the landed KXNBAPTS_LISTS_A, time fields only. Printed: events 120, share median 0.0818 (exact 0.08179993308798929), q25 0.054, q75 0.12, open at T 5339.
# TIME FIELDS ONLY: ticker, event_ticker, close_time, occurrence_datetime. Sets SIBHIT's threshold (median share) and the request plan.
import gzip,json,os,sys,calendar,time,statistics as st,collections
def iso(s):
    s=(s or '').split('.')[0].rstrip('Z')
    try: return calendar.timegm(time.strptime(s,'%Y-%m-%dT%H:%M:%S'))
    except: return None
d=sys.argv[1]; ms=[]
for f in sorted(x for x in os.listdir(d) if x.endswith('.json.gz')):
    b=json.load(gzip.open(os.path.join(d,f),'rt'))
    for m in b.get('markets') or []:
        if m['ticker'].split('-')[0]=='KXNBAPTS': ms.append((m['ticker'],m['event_ticker'],iso(m['close_time']),iso(m['occurrence_datetime'])))
ev=collections.defaultdict(list)
for t,e,c,o in ms: ev[e].append((t,c,o))
rows=[]
for e,L in sorted(ev.items()):
    occ=min(o for _,_,o in L if o)
    A,T=occ-180*60,occ-60*60
    base=[x for x in L if x[1]>A]
    hits=[x for x in base if A<x[1]<=T]
    openT=[x for x in base if x[1]>T]
    if len(base)<10: continue
    rows.append((e,len(base),len(hits),len(hits)/len(base),len(openT)))
sh=[r[3] for r in rows]
print('events',len(rows),'share median',round(st.median(sh),4),'q25/q75',[round(x,3) for x in st.quantiles(sh,n=4)])
print('open at T: total',sum(r[4] for r in rows),'median',st.median([r[4] for r in rows]),'max',max(r[4] for r in rows))
print('pre-A closes (before occ-180):',sum(1 for t,e,c,o in ms if c<=min(oo for _,_,oo in ev[e] if oo)-180*60))
