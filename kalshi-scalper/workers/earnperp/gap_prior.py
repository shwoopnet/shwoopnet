import json,urllib.request,time,datetime as dt,statistics as st,collections
from zoneinfo import ZoneInfo
NY=ZoneInfo('America/New_York')
ev=json.load(open('e202.json')); ms=json.load(open('m.json'))['markets']
eq=sorted({m['title'] for m in ms if m['asset_class']=='Equities'}-{'QQQ','SPY','BABA','SPCX'})
G=collections.defaultdict(list); fails=[]
for t in eq:
    y=t.replace('.','-')
    try:
        j=json.load(urllib.request.urlopen(urllib.request.Request('https://query1.finance.yahoo.com/v8/finance/chart/%s?range=2y&interval=1d'%y,headers={"User-Agent":"Mozilla/5.0"}),timeout=40))['chart']['result'][0]
    except Exception as e:
        fails.append((t,str(e)[:40]))
        if '429' in str(e): break
        continue
    ts=j['timestamp'];q=j['indicators']['quote'][0]
    days=[(dt.datetime.fromtimestamp(a,dt.timezone.utc).astimezone(NY).date(),o,c) for a,o,c in zip(ts,q['open'],q['close']) if o and c]
    idx={d:i for i,(d,_,_) in enumerate(days)}
    seen=set()
    for tt,a,_ in ev:
        if tt!=t or a<'2025-09-01': continue
        d=dt.datetime.fromisoformat(a.replace('Z','+00:00')).astimezone(NY); h=d.hour+d.minute/60
        if 9.5<=h<16: continue
        dd=d.date()
        if h>=16: # post: gap next session
            nxt=[k for k in idx if k>dd]; 
            if not nxt: continue
            k=min(nxt)
        else:
            if dd not in idx: continue
            k=dd
        i=idx[k]
        if i==0 or k in seen: continue
        seen.add(k)
        G[t].append((str(k),'post' if h>=16 else 'pre',(days[i][1]/days[i-1][2]-1)*1e4))
    time.sleep(0.6)
allg=[abs(x[2]) for v in G.values() for x in v]
print('names',len(G),'events',len(allg),'fails',fails[:3])
if allg:
    print('median |G| bps',st.median(allg),'mean',st.mean(allg),'share>=150',sum(a>=150 for a in allg)/len(allg),'>=300',sum(a>=300 for a in allg)/len(allg))
    for s in('pre','post'):
        a=[abs(x[2]) for v in G.values() for x in v if x[1]==s];print(s,len(a),st.median(a))
