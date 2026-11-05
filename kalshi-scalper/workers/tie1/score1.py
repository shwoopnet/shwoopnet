import json,datetime,math,statistics,os
ties=json.load(open('cache/ties.json'))
def f(x):
    try: return float(x)
    except: return None
def fee(p,c=10): return math.ceil(round(0.07*c*p*(1-p)*100,9)/1)/100  # total fee for C contracts, dollars
def look(tk,k):
    p=f"cache/c/{tk}.json"
    if not os.path.exists(p): return None
    d=json.load(open(p))
    best=None
    for c in d.get('candlesticks',[]):
        t=c['end_period_ts']
        if t>k-300: continue
        b=f((c.get('yes_bid') or {}).get('close'));a=f((c.get('yes_ask') or {}).get('close'))
        if b is None or a is None or b<=0 or a<=b or a-b>0.10+1e-9: continue
        best=(t,b,a)
    return best
rows=[];dropped=dict(noquote=0,noside=0)
for t in ties:
    k=int(datetime.datetime.fromisoformat(t['kick2'].replace('Z','+00:00')).timestamp())
    qs={}
    for tk in t['teams']:
        q=look(tk,k)
        if q: qs[tk]=q
    if len(qs)<2: dropped['noquote']+=1;continue
    tk=min(qs,key=lambda x:qs[x][2]); ask=qs[tk][2]
    if not(0.03<=ask<=0.30+1e-9): dropped['noside']+=1;continue
    tm=t['teams'][tk]; deficit=tm['leg1_against']-tm['leg1_for']
    win=t['result'][tk]=='yes'
    c=10; cost=ask*c+fee(ask,c); pay=c if win else 0
    rows.append(dict(event=t['event'],date=t['kick2'][:10],ask=ask,deficit=deficit,home2=tm['home2'],win=win,net=(pay-cost)/c,net12=(pay-ask*c-1.2*fee(ask,c))/c))
rows.sort(key=lambda r:r['date'])
def summ(rs,lab):
    n=len(rs)
    if n==0: print(lab,'n 0');return
    m=sum(r['net'] for r in rs)/n
    gp=sum(max(0,r['net']) for r in rs);gl=sum(max(0,-r['net']) for r in rs)
    pf=gp/gl if gl else float('inf')
    sd=statistics.pstdev([r['net'] for r in rs]) if n>1 else 0
    z=m/(sd/math.sqrt(n)) if sd else float('nan')
    pf12=sum(max(0,r['net12']) for r in rs)/max(1e-9,sum(max(0,-r['net12']) for r in rs))
    print(f"{lab}: n {n} win {sum(r['win'] for r in rs)/n:.3f} mean ask {sum(r['ask'] for r in rs)/n:.3f} mean net {m*100:+.2f}c PF {pf:.2f} z {z:.2f} PFx1.2 {pf12:.2f}")
print('ties',len(ties),'dropped',dropped,'candidates',len(rows))
mid=rows[len(rows)//2]['date'] if rows else ''
tr=[r for r in rows if r['deficit']<=1]
summ(rows,'CONTROL all candidates');summ(tr,'TREATED deficit<=1')
summ([r for r in tr if r['date']<mid],'  treated D1');summ([r for r in tr if r['date']>=mid],'  treated D2')
summ([r for r in rows if r['deficit']>=2],'info deficit>=2')
summ([r for r in tr if r['home2']],'info treated home leg2');summ([r for r in tr if not r['home2']],'info treated away leg2')
print('split date',mid)
