"""CHEAPEXIT1 (workers/CHEAPEXIT1_PROTOCOL.md). Development only: the last third of each series by close time is never scored here."""
import sqlite3, collections, math
from statistics import NormalDist
def fee(p): return 0.07*p*(1-p)
def pf(x):
    w=sum(v for v in x if v>0); l=-sum(v for v in x if v<0)
    return w/l if l>0 else 99.0
N=5156; zbar=NormalDist().inv_cdf(1-0.05/N)
print("N %d z bar %.2f"%(N,zbar))
for db,ser in (("data/hist15/KXBTC15M.sqlite","BTC"),("data/hist15/KXETH15M.sqlite","ETH")):
    c=sqlite3.connect(db)
    mk={t:(ct,r) for t,ct,r in c.execute("select ticker,close_ts,result from market where result in ('yes','no') and n_candles>0")}
    order=sorted(mk,key=lambda t:mk[t][0]); dev=set(order[:2*len(order)//3])
    by=collections.defaultdict(list)
    for tk,ts,b,a in c.execute("select ticker,end_ts,bid_c,ask_c from candle"):
        if tk in dev and b is not None and a is not None: by[tk].append((ts,b,a))
    for lo,hi in ((0.04,0.08),(0.08,0.12)):
        res={0.03:[],0.06:[],"hold":[]}; evs=[]
        for tk,v in by.items():
            v.sort(); ct,r=mk[tk]
            pick=None
            for ts,b,a in v:
                if 570<=ct-ts<=640: pick=(ts,b,a)
            if not pick: continue
            ts0,b,a=pick
            if b<=0 or a>=1 or a<=b: continue
            ya,na=a,1-b
            side,p=("yes",ya) if ya<=na else ("no",na)
            if not(lo<=p<=hi) or a-b>0.03: continue
            hold=(1.0 if r==side else 0.0)-p-fee(p)
            res["hold"].append(hold)
            for T in (0.03,0.06):
                out=None
                for ts,bb,aa in v:
                    if ts<=ts0 or ct-ts<120: continue
                    sb=bb if side=="yes" else 1-aa      # bid of the held side
                    if sb>=p+T: out=sb; break
                res[T].append(hold if out is None else out-p-fee(p)-fee(out))
        for k in (0.03,0.06,"hold"):
            x=res[k]; n=len(x)
            if n<20: print(ser,lo,hi,k,"n",n,"too few"); continue
            h=n//2
            m=sum(x)/n; sd=(sum((v-m)**2 for v in x)/(n-1))**.5; z=m/(sd/n**.5) if sd>0 else 0
            print("%s %.2f-%.2f %-5s n %4d PF %.2f halves %.2f/%.2f mean %+.2fc z %.2f"%(ser,lo,hi,k,n,pf(x),pf(x[:h]),pf(x[h:]),100*m,z))
