# Arithmetic only, no market data. [design]  10 contracts an order, per-strategy kill scaled to the order's risk, no lane cap, no seat cap.
import numpy as np, math, sys
rng=np.random.default_rng(20261116)
C=10
def fee(p): return math.ceil(0.07*C*p*(1-p)*100-1e-9)/100.0
def pf(a):
    a=np.asarray(a); g=a[a>0].sum(); l=-a[a<0].sum(); return np.inf if l==0 else g/l
def qfor(p,t):
    f=fee(p); a=C*(1-p)-f; b=C*p+f; return t*b/(a+t*b)
def live(p,q,dd,trials=5000,maxfills=200):
    f=fee(p); out=[];life=[]
    for _ in range(trials):
        w=rng.random(maxfills)<q; x=np.where(w,C*(1-p)-f,-C*p-f)
        c=np.cumsum(x); peak=np.maximum.accumulate(np.maximum(c,0)); stop=maxfills
        for i in range(maxfills):
            n=i+1
            if peak[i]-c[i]>=dd: stop=n;break
            if n==50 and c[i] < -0.01*C*n: stop=n;break
            if n>=60 and n%60==0 and pf(x[n-60:n])<1.0: stop=n;break
        out.append(c[stop-1]); life.append(stop)
    out=np.array(out); life=np.array(life)
    return out.mean(), np.percentile(out,5), np.median(life), (life<maxfills).mean()
print("per-order: price, fee, win, loss, EV per order at true PF 1.3")
for p in (0.2,0.35,0.5,0.65,0.8):
    f=fee(p); q=qfor(p,1.3); print(f"{p:.2f} fee ${f:.2f} win ${C*(1-p)-f:.2f} loss ${C*p+f:.2f} EV ${q*(C*(1-p)-f)-(1-q)*(C*p+f):+.2f}")
print("LIVE at 10 contracts: kill = drawdown of k x $10; plus -1c a contract at 50 fills; last 60 under 1.0 at each 60th")
for k in (4,6,8):
    for p in (0.2,0.5,0.8):
        for label,t in (("no edge",None),("true PF 0.8",0.8),("true PF 1.3",1.3)):
            q=p if t is None else qfor(p,t)
            m,p5,med,st=live(p,q,10*k)
            print(f"kill ${10*k} price {p:.2f} {label:11s} mean ${m:+.2f} p5 ${p5:+.2f} median life {med:.0f} out by 200: {st:.2f}")
