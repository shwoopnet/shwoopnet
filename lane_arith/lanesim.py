# Arithmetic only: no market data. How often does a rule with a given true win rate clear the lane's entry bar by luck,
# and what does it cost live before the kill lines stop it. [design]
import numpy as np, math
rng=np.random.default_rng(20261112)
C=3
def fee(p): return math.ceil(0.07*C*p*(1-p)*100-1e-9)/100.0
def pnl(p,wins):  # wins: bool array; cash result per order of C contracts
    f=fee(p); return np.where(wins, C*(1-p)-f, -C*p-f)
def pf(x):
    g=x[x>0].sum(); l=-x[x<0].sum(); return np.inf if l==0 else g/l
def passes(x,wins,p,guard):
    if pf(x)<1.3: return False
    if guard:
        h=len(x)//2
        if pf(x[:h])<1.0 or pf(x[h:])<1.0: return False
        rare = wins.sum() if p<=0.5 else (~wins).sum()
        if rare<10: return False
    return True
def entry(p,q,N,guard,trials=20000,horizon=300,step=20):
    single=0; ever=0
    for _ in range(trials):
        w=rng.random(horizon)<q; x=pnl(p,w)
        if passes(x[:N],w[:N],p,guard): single+=1
        ok=False
        for e in range(N,horizon+1,step):
            if passes(x[e-N:e],w[e-N:e],p,guard): ok=True;break
        ever+=ok
    return single/trials, ever/trials
def live(p,q,trials=20000,maxfills=200,dd_orders=3):
    # kill: drawdown from own cash peak >= dd_orders full-size worst losses; or PF<0.8 at 30 fills; or PF<1.0 at 60; fade: rolling-60 PF<1.0 checked every 20 after 60
    worst=C*p+fee(p); out=[];life=[]
    for _ in range(trials):
        w=rng.random(maxfills)<q; x=pnl(p,w); c=np.cumsum(x); peak=np.maximum.accumulate(np.maximum(c,0))
        stop=maxfills
        for i in range(maxfills):
            n=i+1
            if peak[i]-c[i]>=dd_orders*worst: stop=n;break
            if n==30 and pf(x[:30])<0.8: stop=n;break
            if n>=60 and n%20==0 and pf(x[n-60:n])<1.0: stop=n;break
        out.append(c[stop-1]); life.append(stop)
    out=np.array(out); life=np.array(life)
    return out.mean(), np.percentile(out,5), np.median(life), (life<maxfills).mean()
print("ENTRY: P(clear PF>=1.3 on 60) single block | ever within 300 signals (checkpoint every 20)")
for p in (0.2,0.5,0.9):
    for label,q in (("no edge",p),("true cash PF about 1.3",None)):
        if q is None:
            # win rate giving expected PF 1.3: q*(C(1-p)-f) = 1.3*(1-q)*(C p+f)
            f=fee(p); a=C*(1-p)-f; b=C*p+f; q=1.3*b/(a+1.3*b)
        for guard in (False,True):
            s,e=entry(p,q,60,guard)
            print(f"price {p:.2f} {label:24s} winrate {q:.3f} guard={guard!s:5s} single {s:.3f} ever {e:.3f}")
print("LIVE at 3 contracts, 200 fills max: mean cash result, 5th pct, median fills alive, share stopped")
for p in (0.2,0.5,0.9):
    f=fee(p); a=C*(1-p)-f; b=C*p+f
    for label,q in (("no edge",p),("true PF 1.3",1.3*b/(a+1.3*b)),("true PF 0.8",0.8*b/(a+0.8*b))):
        for dd in (3,6) if p<0.9 else (2,3):
            m,p5,med,st=live(p,q,dd_orders=dd)
            print(f"price {p:.2f} {label:12s} dd={dd} worst-order ${C*p+f:.2f}: mean ${m:+.2f} p5 ${p5:+.2f} median life {med:.0f} stopped {st:.2f}")
