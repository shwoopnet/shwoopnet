import json,sys,collections,statistics,glob
sys.path.insert(0,'/home/user/shwoopnet/kalshi-scalper/src')
from scalper import earnpr1 as e
D='/home/user/.cache/earnpr1/'
rows=json.load(open(D+'census_rows.json')); texts=json.load(open(D+'texts.json'))
ev=json.load(open(D+'events.json'))
cd={}
for f in sorted(glob.glob('/home/user/shwoopnet/kalshi-scalper/data/ment1/candles_*.json')): cd.update(json.load(open(f)))
n=len(rows); mt=[r for r in rows if 'acc' in r]
print('events',n,collections.Counter(r.get('why','matched') for r in rows),collections.Counter(r['kind'] for r in rows if 'kind' in r))
for kind in ('sched','proxy',None):
    ld=[r['lead_min'] for r in mt if kind is None or r['kind']==kind]
    if ld: print(kind,'n',len(ld),'lead median',round(statistics.median(ld),1),'p25/p75',[round(x,1) for x in statistics.quantiles(ld,n=4)[::2]],'<20m',round(sum(x<20 for x in ld)/len(ld),3),'<10m',round(sum(x<10 for x in ld)/len(ld),3))
ok=[r for r in mt if r['has_text']]
print('matched',len(mt),'with Ex-99.1 text',len(ok))
# quote coverage by hourly grid, existence only
loose=strict=0
for r in ok:
    L=S=False
    for m in ev[r['ev']]:
        for c in cd.get(m['t'],[]) or []:
            if c[1] is not None and c[2] is not None and 0<c[1]<c[2]<1:
                if r['acc_ts']-3600<=c[0]<=r['occ']: L=True
                if r['acc_ts']+600<=c[0]<=r['occ']-600: S=True
    loose+=L; strict+=S
print('quote coverage (events with text): loose hourly',loose,round(loose/len(ok),3),'strict hourly',strict,round(strict/len(ok),3))
# word-in-release rate by stem, no outcomes
cnt=collections.defaultdict(lambda:[0,0]); tot=[0,0]
for r in ok:
    t=texts[r['acc']]
    for m in ev[r['ev']]:
        if not m['word']: continue
        h=e.in_release(m['word'],t); s=e.stem_of(m['word'])
        cnt[s][0]+=1; cnt[s][1]+=h; tot[0]+=1; tot[1]+=h
print('markets in matched events',tot[0],'word in release share',round(tot[1]/tot[0],3),'stems',len(cnt))
top=sorted(cnt.items(),key=lambda x:-x[1][0])[:15]
print([(k,v[0],round(v[1]/v[0],2)) for k,v in top])
# events by pre-cut time thirds
ok.sort(key=lambda r:r['occ']); k=len(ok)*2//3
import datetime as dt
f=lambda t:dt.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d')
print('FIT events',k,f(ok[0]['occ']),f(ok[k-1]['occ']),'TEST',len(ok)-k,f(ok[k]['occ']),f(ok[-1]['occ']))
print('markets FIT',sum(len(ev[r['ev']]) for r in ok[:k]),'TEST',sum(len(ev[r['ev']]) for r in ok[k:]))
