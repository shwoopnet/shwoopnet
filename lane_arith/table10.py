# Arithmetic only, no market data. [design]  The entry-bar table at 3 and at 10 contracts, and under two meanings of "no edge".
import numpy as np, math
rng=np.random.default_rng(20261119)
def fee(p,C): return math.ceil(0.07*C*p*(1-p)*100-1e-9)/100.0
def pf(x):
    g=x[x>0].sum(); l=-x[x<0].sum(); return np.inf if l==0 else g/l
def q_breakeven(p,C):
    f=fee(p,C); a=C*(1-p)-f; b=C*p+f; return b/(a+b)
def bare(x): return pf(x)>=1.3
def guarded(x,w,p):
    if pf(x)<1.3 or pf(x[:30])<1.0 or pf(x[30:])<1.0: return False
    return (w.sum() if p<=0.5 else (~w).sum())>=10
def row(p,q,C,T=12000):
    f=fee(p,C); single=roll=nonov=nonov_c=first_c=0
    for _ in range(T):
        w=rng.random(450)<q; x=np.where(w,C*(1-p)-f,-C*p-f)
        single+=bare(x[:60])
        roll+=any(bare(x[e-60:e]) for e in range(60,301,20))
        ok=False; okc=False
        for b in range(5):
            s=b*90; blk=slice(s,s+60); g=guarded(x[blk],w[blk],p)
            if b==0: first_c+= g and pf(x[s+60:s+90])>=1.0
            if g and not ok: ok=True
            if g and pf(x[s+60:s+90])>=1.0: okc=True
        nonov+=ok; nonov_c+=okc
    return [round(100*v/T,1) for v in (single,roll,nonov,nonov_c,first_c)]
print("columns: one block bare | ever in 300 rolling | ever in 5 blocks, guarded | same with confirmation | first block with confirmation")
for C in (3,10):
    for p in (0.2,0.5):
        print(f"C={C} price {p:.2f} fair market (win rate = price): {row(p,p,C)}")
        print(f"C={C} price {p:.2f} break-even after the fee:      {row(p,q_breakeven(p,C),C)}")
    f=fee(0.9,C); T=12000; s=0
    for _ in range(T):
        w=rng.random(60)<0.9; x=np.where(w,C*0.1-f,-C*0.9-f); s+=bare(x)
    print(f"C={C} price 0.90 fair market, one block bare: {round(100*s/T,1)}")
