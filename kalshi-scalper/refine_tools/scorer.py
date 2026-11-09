# Read only strategy scorer. Usage: python3 -I scorer.py <report.json>. See REGISTRATION.md (W-SCORER). No network, no token.
import sys,json,datetime as D
d=json.load(open(sys.argv[1]))
def T(s): return D.datetime.fromisoformat(s.replace('Z','+00:00'))
now=T(d['generatedAt'])
def pf(v):
    g=sum(x for x in v if x>0);l=-sum(x for x in v if x<0)
    return g/l if l else float('inf')
def trade(o):
    c=o['count'];y=o['side']=='yes'
    paid=o['avgFill'] if y else 1-o['avgFill']
    pnl=o['settledPnl'];ex=o.get('result')=='exit'
    fee0=(o.get('avgFee') or 0)*c
    # cash basis: win or loss recomputed from the fill (stored settledPnl is limit-booked before PR 741; found Nov 9)
    if o.get('result') in('yes','no'): pnl=(c*(1-paid)-fee0) if o['result']==o['side'] else (-c*paid-fee0)
    if ex and o.get('limit') is not None:
        pnl+=c*((o['limit'] if y else 1-o['limit'])-paid)
    slip=None
    sa,sb=o.get('seenAsk'),o.get('seenBid')
    if sa is not None and sb is not None: slip=(paid-(sa if y else 1-sb))*100
    return dict(ts=o['ts'],c=c,pnl=pnl,fee=(o.get('avgFee') or 0)*c,ex=ex,slip=slip)
G={}
for o in d['orders']:
    k=o['ticker'].split('-')[0]
    nm={'KXGOLD15M':'gold L1','KXXRP15M':'XRP (paused)','KXBTC15M':'Bitcoin (paused)','KXETH15M':'Ethereum (paused)','KXDOGE15M':'Dogecoin (info)','KXAUDUSD15M':'AUD/USD (paused)','KXUSDCAD15M':'USD/CAD (paused)','KXNATGAS15M':'nat gas (paused)'}.get(k,k)
    G.setdefault(nm,[]).append(o)
for o in d.get('slotOrders',[]): G.setdefault(o.get('strategy','?'),[]).append(o)
hdr='%-18s %5s %5s %8s %5s %5s %6s %5s %6s %5s %6s %6s %7s'%('group','n','PF','net$','f/wk','fill%','fee%gw','slip','exits','ex%','r60now','r60min','net c/ct')
print('generated',d['generatedAt'][:16],'rows',len(d['orders']),'slot',len(d.get('slotOrders',[])));print(hdr)
notes=[]
for nm,rows in sorted(G.items(),key=lambda kv:-len(kv[1])):
    rows=sorted(rows,key=lambda o:o['ts'])
    tr=[trade(o) for o in rows if o.get('count') and o['count']>0 and o.get('settledPnl') is not None and o.get('avgFill') is not None]
    if not tr: print('%-18s no settled fills (submitted %d)'%(nm,len(rows)));continue
    v=[t['pnl'] for t in tr];n=len(tr)
    wk=max((now-T(rows[0]['ts'])).total_seconds()/604800,1e-9)
    filled=sum(1 for o in rows if o.get('count') and o['count']>0)
    W=[t for t in tr if t['pnl']>0]
    gw=sum(t['pnl'] for t in W)+sum(t['fee'] for t in W)
    sl=[t['slip'] for t in tr if t['slip'] is not None]
    ne=sum(t['ex'] for t in tr)
    roll=[pf(v[i-60:i]) for i in range(60,n+1)]
    cts=sum(t['c'] for t in tr);cum=0;cc=0;crossed=None;first_r1=None
    for i,t in enumerate(tr,1):
        cum+=t['pnl'];cc+=t['c']
        if i>=50 and crossed is None and 100*cum/cc<-1: crossed=i
        if i>=60 and first_r1 is None and pf(v[i-60:i])<0.7: first_r1=i
    cpc=100*sum(v)/cts
    r5=cpc<-1 and n>=50
    r1=bool(roll) and min(roll)<0.7
    days=(now-T(tr[0]['ts'])).total_seconds()/86400
    need=[]
    if n<100:need.append('%d more fills'%(100-n))
    if days<14:need.append('%.0f more days'%(14-days))
    print('%-18s %5d %5.2f %8.2f %5.1f %5.0f %6.1f %5s %6d %5.1f %6s %6s %7.2f'%(nm,n,pf(v),sum(v),n/wk,100*filled/len(rows),100*sum(t['fee'] for t in tr)/gw if gw else 0,('%.2f'%(sum(sl)/len(sl))) if sl else 'na',ne,100*ne/n,('%.2f'%roll[-1]) if roll else 'na',('%.2f'%min(roll)) if roll else 'na',cpc))
    notes.append('%s: R5 %s (ever crossed after 50: %s); R1 %s (first at fill %s); stage %s'%(nm,'KILL' if r5 else 'ok',crossed or 'no','KILL' if r1 else 'ok',first_r1 or '-','eligible' if not need else 'not yet, needs '+' and '.join(need)))
    notes[-1]+='; fills since start %d'%n
print();print('\n'.join(notes))
