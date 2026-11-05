import sys,json,datetime,os,time; sys.path.insert(0,'.')
from g import get
ties=json.load(open('cache/ties.json'))
os.makedirs('cache/c',exist_ok=True)
for t in ties:
    k=int(datetime.datetime.fromisoformat(t['kick2'].replace('Z','+00:00')).timestamp())
    for tk in t['teams']:
        p=f"cache/c/{tk}.json"
        if os.path.exists(p): continue
        r=get(f"/historical/markets/{tk}/candlesticks?start_ts={k-4*3600}&end_ts={k-300}&period_interval=1",tries=8)
        json.dump(r if r is not None else {'error':1},open(p,'w')); time.sleep(0.7)
print('candles done',flush=True)
