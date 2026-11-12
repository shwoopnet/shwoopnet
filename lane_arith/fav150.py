# Arithmetic only, no market data. [design]  Favourite at 88c or above: block of at least 150 signals that runs on until it holds 10 losses; then 1.3, halves 1.0; confirmation 30 at 1.0.
import numpy as np, math
rng=np.random.default_rng(20261118); C=10
def fee(p): return math.ceil(0.07*C*p*(1-p)*100-1e-9)/100.0
def pf(x):
    g=x[x>0].sum(); l=-x[x<0].sum(); return np.inf if l==0 else g/l
def qfor(p,t):
    f=fee(p); a=C*(1-p)-f; b=C*p+f; return t*b/(a+t*b)
def one(p,q,confirm):
    f=fee(p); w=rng.random(2000)<q; x=np.where(w,C*(1-p)-f,-C*p-f)
    losses=np.cumsum(~w); n=max(150,int(np.argmax(losses>=10))+1)
    b=x[:n]; h=n//2
    ok=pf(b)>=1.3 and pf(b[:h])>=1.0 and pf(b[h:])>=1.0
    if ok and confirm: ok=pf(x[n:n+30])>=1.0
    return ok,n
for p in (0.88,0.92,0.95):
    for label,q in (("no edge",p),("true PF 1.3",qfor(p,1.3))):
        for confirm in (False,True):
            r=[one(p,q,confirm) for _ in range(20000)]
            print(f"price {p:.2f} {label:11s} confirm={confirm!s:5s} clears {np.mean([a for a,_ in r]):.3f} median block {int(np.median([n for _,n in r]))}")
