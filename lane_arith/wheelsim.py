# Arithmetic only, no market data. [design]  A wheel of 30 shadows and 5 live seats over 180 days.
import numpy as np, math, sys
rng=np.random.default_rng(20261115)
C=3
def fee(p): return math.ceil(0.07*C*p*(1-p)*100-1e-9)/100.0
def pf(a):
    a=np.asarray(a); g=a[a>0].sum(); l=-a[a<0].sum(); return np.inf if l==0 else g/l
def qfor(p,t):
    f=fee(p); a=C*(1-p)-f; b=C*p+f; return t*b/(a+t*b)
def run(n_rules,frac_real,confirm,seats,days=180,sig_per_day=4,fill=0.7):
    P=rng.choice([0.2,0.35,0.5,0.65],n_rules); real=rng.random(n_rules)<frac_real
    Q=np.array([qfor(p,1.3) if r else p for p,r in zip(P,real)])
    st=['S']*n_rules; blk=[[] for _ in range(n_rules)]; cf=[[] for _ in range(n_rules)]; live=[[] for _ in range(n_rules)]
    cool=[0]*n_rules; qual_day=[0]*n_rules; pnl_total=0.0; fills=0; fills_real=0; entries=0; entries_real=0; seat_days=0
    for d in range(days):
        occupied=sum(s=='L' for s in st); seat_days+=occupied
        for i in rng.permutation(n_rules):
            if st[i]=='C0':
                if d>=cool[i]: st[i]='S'; blk[i]=[]
                continue
            k=rng.binomial(rng.poisson(sig_per_day),fill)
            for _ in range(k):
                w=rng.random()<Q[i]; f=fee(P[i]); x=C*(1-P[i])-f if w else -C*P[i]-f
                if st[i]=='S':
                    blk[i].append(x)
                    if len(blk[i])==60:
                        b=np.array(blk[i]); wins=(b>0).sum(); rare=wins if P[i]<=0.5 else 60-wins
                        if pf(b)>=1.3 and pf(b[:30])>=1.0 and pf(b[30:])>=1.0 and rare>=10:
                            st[i]='K' if confirm else 'Q'; cf[i]=[]; qual_day[i]=d
                        else: blk[i]=[]
                elif st[i]=='K':
                    cf[i].append(x)
                    if len(cf[i])==30:
                        if pf(cf[i])>=1.0: st[i]='Q'; qual_day[i]=d
                        else: st[i]='S'; blk[i]=[]
                elif st[i]=='Q':
                    if sum(s=='L' for s in st)<seats:
                        st[i]='L'; live[i]=[]; entries+=1; entries_real+=real[i]
                    elif d-qual_day[i]>14: st[i]='S'; blk[i]=[]
                if st[i]=='L' and (len(live[i])>0 or True):
                    if st[i]=='L' and not (len(live[i])==0 and False):
                        pass
                if st[i]=='L':
                    live[i].append(x); pnl_total+=x; fills+=1; fills_real+=real[i]
                    c=np.cumsum(live[i]); n=len(c); peak=max(0,c.max())
                    out = (peak-c[-1]>=10) or (n==50 and c[-1] < -0.01*C*n) or (n>=60 and n%60==0 and pf(live[i][-60:])<1.0)
                    if out: st[i]='C0'; cool[i]=d+14
    m=days/30
    return pnl_total/m, fills/m, (fills_real/fills if fills else 0), entries/m, (entries_real/entries if entries else 0), seat_days/days
def avg(n_rules,fr,confirm,seats,reps):
    r=np.array([run(n_rules,fr,confirm,seats) for _ in range(reps)]); return r.mean(0), np.percentile(r[:,0],5)
print("30 shadows, 5 seats, 3 contracts, 4 signals a day a rule, 70% fillable; per month: lane cash, live fills, share of fills from real rules, entries, share of entries real, seats filled")
for fr in (0.0,0.1,0.2):
    for confirm in (False,True):
        a,p5=avg(30,fr,confirm,5,int(sys.argv[1]) if len(sys.argv)>1 else 40)
        print(f"real share {fr:.1f} confirm={confirm!s:5s}: lane ${a[0]:+.2f}/month (5th pct ${p5:+.2f}), fills {a[1]:.0f}, real fills {a[2]:.2f}, entries {a[3]:.1f}/month, real entries {a[4]:.2f}, seats {a[5]:.1f}")
