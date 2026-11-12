# Arithmetic only, no market data. [design]  Kill lines: fixed dollar drawdown, net under -1c a contract at 50 fills, rolling-60 PF under 0.7.
import numpy as np, math
rng=np.random.default_rng(20261114)
def fee(p,C): return math.ceil(0.07*C*p*(1-p)*100-1e-9)/100.0
def pf(x):
    g=x[x>0].sum(); l=-x[x<0].sum(); return np.inf if l==0 else g/l
def qfor(p,t,C=3):
    f=fee(p,C); a=C*(1-p)-f; b=C*p+f; return t*b/(a+t*b)
def live(p,q,dd,trials=6000,maxfills=200,C=3):
    f=fee(p,C); out=[];life=[]
    for _ in range(trials):
        w=rng.random(maxfills)<q; x=np.where(w,C*(1-p)-f,-C*p-f)
        c=np.cumsum(x); peak=np.maximum.accumulate(np.maximum(c,0)); stop=maxfills
        for i in range(maxfills):
            n=i+1
            if peak[i]-c[i]>=dd: stop=n;break
            if n==50 and c[i] < -0.01*C*n: stop=n;break
            if n>=60 and n%20==0 and pf(x[n-60:n])<0.7: stop=n;break
        out.append(c[stop-1]); life.append(stop)
    out=np.array(out); life=np.array(life)
    return out.mean(), np.percentile(out,5), np.median(life), (life<maxfills).mean()
for dd in (8,10,12):
    for p in (0.2,0.5,0.8):
        for label,t in (("no edge",None),("true PF 0.8",0.8),("true PF 1.3",1.3)):
            q=p if t is None else qfor(p,t)
            m,p5,med,st=live(p,q,dd)
            print(f"dd ${dd} price {p:.2f} {label:11s} mean ${m:+.2f} p5 ${p5:+.2f} median life {med:.0f} stopped by 200: {st:.2f}")
