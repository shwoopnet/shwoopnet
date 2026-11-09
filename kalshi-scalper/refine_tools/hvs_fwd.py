import sys,json,random,urllib.request,datetime as D,collections
P=sys.argv[1];START=sys.argv[2] if len(sys.argv)>2 else '2026-11-07T20:24:00Z'
d=json.load(open(P))
B='https://api.elections.kalshi.com/trade-api/v2/markets/'
def res(t):
    try:
        r=json.load(urllib.request.urlopen(urllib.request.Request(B+t,headers={'User-Agent':'hvs'}),timeout=20))['market'].get('result')
        return r if r in('yes','no') else None
    except Exception: return None
rows=[o for o in d['orders'] if o['ts']>START and o['result']=='exit' and o['ticker'][:6] in('KXGOLD','KXDOGE') and o['count'] and o['count']>0 and o.get('settledPnl') is not None and o.get('avgFill') is not None and o.get('limit') is not None]
out=[]
for o in rows:
    y=o['side']=='yes';c=o['count']
    paid=o['avgFill'] if y else 1-o['avgFill'];lim=o['limit'] if y else 1-o['limit']
    act=o['settledPnl']+c*(lim-paid)
    ex=o['result']=='exit'
    r=res(o['ticker']) if ex else o['result']
    if r not in('yes','no'): continue
    win=r==o['side'];fee=(o['avgFee'] or 0)*c
    hold=(c*(1-paid)-fee) if win else (-c*paid-fee)
    ct=(datetime:=D.datetime.fromisoformat(o['ts'].replace('Z','+00:00')))
    day=(ct-D.timedelta(hours=5 if ct.month<11 or (ct.month==11 and ct.day<1) else 6)).date().isoformat()
    out.append(dict(m=o['ticker'][:6],ex=ex,c=c,paid=paid,act=act,hold=hold,win=win,day=day,ts=o['ts'],exitAvg=o.get('exitAvg')))
E=[x for x in out if x['ex']]
n=len(E)
print('since',START,'new early sells',n,'(rows read %d)'%len(out))
if n:
    D_=[x['hold']-x['act'] for x in E];ct=sum(x['c'] for x in E)
    random.seed(1);bs=sorted(sum(random.choice(D_) for _ in D_) for _ in range(10000))
    lo,hi=bs[500]/ct,bs[9500]/ct
    print('actual %.2f hold %.2f hold minus actual %.2f ($) %.4f per contract (%d contracts)'%(sum(x['act'] for x in E),sum(x['hold'] for x in E),sum(D_),sum(D_)/ct,ct))
    print('paired bootstrap 90%% CI $[%.2f, %.2f] per contract [%.4f, %.4f]'%(bs[500],bs[9500],lo,hi))
    print('hold better %d/%d, would have won %d/%d'%(sum(1 for z in D_ if z>0),n,sum(x['win'] for x in E),n))
    pc=sum(D_)/ct
if n<30: print('NOT AT READ POINT n/30: %d/30'%n)
else:
    if pc<0: v='CLOSE: point estimate negative, keep the 25c exit'
    elif lo>0: v='PROMOTION PACKET IDEA to main: per contract diff above 0 with 90%% CI above 0 (note the exit watch protects the tail: worst day -36.32 with exit vs -27.46 held on history)'
    else: v='EXTEND by 30 new sells: interval includes 0'
    print('READ POINT n/30 reached (%d): %s'%(n,v))
