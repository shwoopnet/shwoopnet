import json,os,sys,time,urllib.request,urllib.error
sys.path.insert(0,'.')
from g import get
S='KXUECLADVANCE'
evs=[];cur=''
while True:
    r=get(f"/events?series_ticker={S}&status=settled&limit=200"+(f"&cursor={cur}" if cur else ""))
    evs+=r['events'];cur=r.get('cursor')
    if not cur: break
json.dump(evs,open('cache/events.json','w'))
print(len(evs),flush=True)
for e in evs:
    p=f"cache/m_{e['event_ticker']}.json"
    if os.path.exists(p): continue
    r=get(f"/historical/markets?event_ticker={e['event_ticker']}")
    if not r or not r.get('markets'):
        r=get(f"/markets?event_ticker={e['event_ticker']}&status=settled")
    json.dump(r,open(p,'w')); time.sleep(0.6)
print('markets done',flush=True)
