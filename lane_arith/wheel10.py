# Arithmetic only, no market data. [design]  30 shadows, no seat cap, 10 contracts, per-strategy kill $60, confirmation on.
import numpy as np, math
rng=np.random.default_rng(20261117)
C=10; DD=60
def fee(p): return math.ceil(0.07*C*p*(1-p)*100-1e-9)/100.0
def pf(a):
    a=np.asarray(a); g=a[a>0].sum(); l=-a[a<0].sum(); return np.inf if l==0 else g/l
def qfor(p,t):
    f=fee(p); a=C*(1-p)-f; b=C*p+f; return t*b/(a+t*b)
def run(n_rules,frac_real,days=180,sig=4,fill=0.7):
    P=rng.choice([0.2,0.35,0.5,0.65],n_rules); real=rng.random(n_rules)<frac_real
    Q=np.array([qfor(p,1.3) if r else p for p,r in zip(P,real)])
    st=['S']*n_rules; blk=[[] for _ in range(n_rules)]; cf=[[] for _ in range(n_rules)]; live=[[] for _ in range(n_rules)]
    cool=[0]*n_rules; exits=[0]*n_rules; daily=np.zeros(days); fills=0; fr=0; entries=0; seat_days=0; maxseats=0; kills=0
    for d in range(days):
        occ=sum(s=='L' for s in st); seat_days+=occ; maxseats=max(maxseats,occ)
        for i in range(n_rules):
            if st[i]=='X': continue
            if st[i]=='C0':
                if d>=cool[i]: st[i]='S'; blk[i]=[]
                continue
            for _ in range(rng.binomial(rng.poisson(sig),fill)):
                w=rng.random()<Q[i]; f=fee(P[i]); x=C*(1-P[i])-f if w else -C*P[i]-f
                if st[i]=='S':
                    blk[i].append(x)
                    if len(blk[i])==60:
                        b=np.array(blk[i]); wins=(b>0).sum(); rare=wins if P[i]<=0.5 else 60-wins
                        if pf(b)>=1.3 and pf(b[:30])>=1.0 and pf(b[30:])>=1.0 and rare>=10: st[i]='K'; cf[i]=[]
                        else: blk[i]=[]
                elif st[i]=='K':
                    cf[i].append(x)
                    if len(cf[i])==30:
                        if pf(cf[i])>=1.0: st[i]='L'; live[i]=[]; entries+=1
                        else: st[i]='S'; blk[i]=[]
                elif st[i]=='L':
                    live[i].append(x); daily[d]+=x; fills+=1; fr+=real[i]
                    c=np.cumsum(live[i]); n=len(c); peak=max(0,c.max())
                    kill=(peak-c[-1]>=DD); perf=(n==50 and c[-1] < -0.01*C*n) or (n>=60 and n%60==0 and pf(live[i][-60:])<1.0)
                    if kill or perf:
                        exits[i]+=1; kills+=kill
                        if kill or exits[i]>=3: st[i]='X'   # needs the owner's popup; not modelled as returning
                        else: st[i]='C0'; cool[i]=d+14
                        break
    m=days/30; wk=np.convolve(daily,np.ones(7),'valid')
    return daily.sum()/m, fills/m, (fr/fills if fills else 0), entries/m, seat_days/days, maxseats, daily.min(), wk.min(), kills
for frac in (0.0,0.1,0.2,0.4):
    r=np.array([run(30,frac) for _ in range(40)])
    a=r.mean(0)
    print(f"real share {frac:.1f}: ${a[0]:+.0f}/month (5th pct ${np.percentile(r[:,0],5):+.0f}), fills {a[1]:.0f}/month, real fills {a[2]:.2f}, entries {a[3]:.1f}/month, seats avg {a[4]:.1f} max {r[:,5].max():.0f}, worst day avg ${a[6]:.0f} (worst seen ${r[:,6].min():.0f}), worst week avg ${a[7]:.0f} (worst seen ${r[:,7].min():.0f})")
