import sys,json,time,os,collections;sys.path.insert(0,'/home/user/shwoopnet/kalshi-scalper/src')
from scalper import api
C='/home/user/.cache/earnpr1/events.json'
ms=json.load(open('/home/user/shwoopnet/kalshi-scalper/data/ment1/markets.json'))
ev=collections.defaultdict(list)
for m in ms.values(): ev[m['ev']].append(m)
cut='2026-10-03T16:00:00Z'
pre=sorted(e for e,v in ev.items() if min(x['close'] for x in v)<cut)
have=json.load(open(C)) if os.path.exists(C) else {}
for i,e in enumerate(pre):
    if e in have: continue
    out=None
    for path in ('/historical/markets','/markets'):
        try:
            r=api._get(path,{'event_ticker':e,'limit':1000})
        except Exception as x:
            continue
        mk=r.get('markets',[])
        if mk:
            out=[{'t':m['ticker'],'word':(m.get('custom_strike') or {}).get('Word'),'occ':m.get('occurrence_datetime'),'close':m.get('close_time'),'title':m.get('title')} for m in mk]; break
    have[e]=out or []
    if i%20==0: json.dump(have,open(C,'w')); print(i,len(pre),flush=True)
    time.sleep(0.25)
json.dump(have,open(C,'w')); print('done',len(have),flush=True)
