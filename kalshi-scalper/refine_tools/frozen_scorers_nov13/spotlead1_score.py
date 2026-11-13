import json,math,bisect,calendar,time,statistics as st,sys
cov=json.load(open('cov.json')); cb=json.load(open('cb.json'))
def ep(i): return calendar.timegm(time.strptime(i,'%Y-%m-%dT%H:%M:%SZ'))
books=json.load(open('books.json'))
tick={}
for l in open('ticks.jsonl'):
    d=json.loads(l); tick[(d['c'],d['s'])]=d['t']
prod={'KXBTC15M':'BTC-USD','KXETH15M':'ETH-USD'}
Phi=lambda x:0.5*(1+math.erf(x/math.sqrt(2)))
cand={}
for p,rows in cb.items(): cand[p]={int(k):v for k,v in rows.items()}  # t -> low high open close vol
MODE='cb'
W=[]
for r in cov:
    if r['series'] in prod and r['result'] in('yes','no') and int(r['ok_polls'])>=100:
        c=ep(r['close_time'])
        if True: W.append((c,r['series'],r['ticker'],r['result']))
W.sort()
def feat(c,s,tk,L):
    cd=cand[prod[s]]
    o=cd.get(c-900)
    if not o: return None
    K=o[2]
    if MODE=='tick':
        ts=[t for t in tick.get((c,s),[]) if t[0]<=L]
        if not ts: return None
        S=ts[-1][1]
        if L-ts[-1][0]>60: return None
    else:
        v=cd.get((int(L)//60)*60-60)
        if v is None: return None
        S=v[3]
    # closes of candles whose end <= L
    last=(int(L)//60)*60-60  # candle start t, ends t+60 <= L
    cl=[]
    for t in range(last-60*60,last+1,60):
        v=cd.get(t)
        if v is None: return None
        cl.append(v[3])
    rets=[math.log(cl[i+1]/cl[i]) for i in range(len(cl)-1)]
    sg=st.pstdev(rets)
    return K,S,sg
def run(edge=0.10,look=180,delay=2,sdm=1.0,slip=0.0,assets=('KXBTC15M','KXETH15M'),lo=0.50,hi=0.87,detail=False):
    T=[]
    for c,s,tk,res in W:
        if s not in assets: continue
        L=c-look
        f=feat(c,s,tk,L)
        if not f: continue
        K,S,sg=f
        sd=sg*sdm*math.sqrt(look/60)
        if sd<=0: continue
        py=Phi(math.log(S/K)/sd)
        bk=books.get(tk,[])
        row=None
        for b in bk:
            if b[0]<=L+delay: row=b
        if row is None or L+delay-row[0]>10: continue
        _,yb,_,nb,_=row
        if yb is None or nb is None: continue
        ay=1-nb; an=1-yb
        best=None
        for side,p,a in(('yes',py,ay),('no',1-py,an)):
            if lo<=a<=hi and p-a>=edge and (best is None or p-a>best[0]): best=(p-a,side,a)
        if not best: continue
        _,side,a=best
        paid=a+slip
        win=(side==res)
        pnl=(1-paid if win else -paid)-0.07*paid*(1-paid)
        T.append((c,s,pnl,paid,win))
    return T
def pf(T):
    g=sum(x[2] for x in T if x[2]>0); l=-sum(x[2] for x in T if x[2]<0)
    return g/l if l>0 else float('inf')
def summ(T):
    if not T: return 'n0'
    h=len(T)//2; Ts=sorted(T)
    return 'n%d PF %.2f net %.2fc/c win %.0f%% h1 %.2f h2 %.2f'%(len(T),pf(T),100*sum(x[2] for x in T)/len(T),100*sum(x[4] for x in T)/len(T),pf(Ts[:h]) if h else 0,pf(Ts[h:]) if h else 0)
if __name__=='__main__':
    print('windows with ticks',len(W))
    for slip in(0,0.01):
        for d in(2,10):
            print('main slip',slip,'delay',d,summ(run(slip=slip,delay=d)))
