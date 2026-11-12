# Arithmetic only, no market data. [design]
import numpy as np, math
rng=np.random.default_rng(20261113)
def fee(p,C): return math.ceil(0.07*C*p*(1-p)*100-1e-9)/100.0
def pnl(p,w,C):
    f=fee(p,C); return np.where(w, C*(1-p)-f, -C*p-f)
def pf(x):
    g=x[x>0].sum(); l=-x[x<0].sum(); return np.inf if l==0 else g/l
def qfor(p,target,C=3):
    f=fee(p,C); a=C*(1-p)-f; b=C*p+f; return target*b/(a+target*b)
def block_ok(x,w,p):
    if pf(x)<1.3: return False
    h=len(x)//2
    if pf(x[:h])<1.0 or pf(x[h:])<1.0: return False
    return True
def entry_nonoverlap(p,q,confirm,trials=20000,blocks=5,N=60,K=30):
    # non-overlapping blocks of N fresh signals; optional confirmation: next K signals PF>=1.0
    ever=0; first=0
    for _ in range(trials):
        ok=False
        for b in range(blocks):
            w=rng.random(N+K)<q; x=pnl(p,w,3)
            good=block_ok(x[:N],w[:N],p) and (not confirm or pf(x[N:])>=1.0)
            if b==0 and good: first+=1
            if good: ok=True;break
        ever+=ok
    return first/trials, ever/trials
def live(p,q,probation,trials=20000,maxfills=200,dd_orders=6,fade=0.7):
    out=[];life=[]
    for _ in range(trials):
        w=rng.random(maxfills)<q
        size=np.where(np.arange(maxfills)<30,1,3) if probation else np.full(maxfills,3)
        x=np.array([pnl(p,np.array([w[i]]),int(size[i]))[0] for i in range(maxfills)])
        c=np.cumsum(x); peak=np.maximum.accumulate(np.maximum(c,0)); worst=3*p+fee(p,3)
        stop=maxfills
        for i in range(maxfills):
            n=i+1
            if peak[i]-c[i]>=dd_orders*worst: stop=n;break
            if n==30 and pf(x[:30])<0.8: stop=n;break
            if n>=60 and n%20==0 and pf(x[n-60:n])<fade: stop=n;break
        out.append(c[stop-1]); life.append(stop)
    out=np.array(out); life=np.array(life)
    return out.mean(), np.percentile(out,5), np.median(life), (life<maxfills).mean()
print("ENTRY on NON-OVERLAPPING 60-signal blocks (both halves >= 1.0): first block | ever in 5 blocks (300 signals)")
for p in (0.2,0.35,0.5):
    for label,t in (("no edge",None),("true PF 1.3",1.3),("true PF 1.5",1.5)):
        q=p if t is None else qfor(p,t)
        for confirm in (False,True):
            f,e=entry_nonoverlap(p,q,confirm)
            print(f"price {p:.2f} {label:11s} confirm30={confirm!s:5s} first {f:.3f} ever {e:.3f}")
print("LIVE, drawdown stop 6 worst full-size orders, PF<0.8 at 30, rolling-60 fade line 0.7: mean, p5, median life, stopped by 200")
for p in (0.2,0.5):
    for label,t in (("no edge",None),("true PF 0.8",0.8),("true PF 1.3",1.3)):
        q=p if t is None else qfor(p,t)
        for prob in (False,True):
            m,p5,med,st=live(p,q,prob,trials=4000)
            print(f"price {p:.2f} {label:11s} probation={prob!s:5s} mean ${m:+.2f} p5 ${p5:+.2f} median life {med:.0f} stopped {st:.2f}")
