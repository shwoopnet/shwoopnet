"""OPEN1H score (workers/OPEN1H_PROTOCOL.md, Amendment 1). Development only; the last third by close time within each source is never scored here."""
import sys, sqlite3, collections, math
from statistics import NormalDist
sys.path.insert(0,"src/scalper")
import leg1
db=sqlite3.connect("data/open1h.sqlite")
mk=db.execute("select ticker,src,open_ts,close_ts,result from mk").fetchall()
cs=collections.defaultdict(list)
for tk,ts,b,a in db.execute("select ticker,end_ts,bid_c,ask_c from candle"): cs[tk].append((ts,b,a))
N=5148; zbar=NormalDist().inv_cdf(1-0.05/N); print("N %d z bar %.2f"%(N,zbar))
BANDS=[(0.04,0.12),(0.12,0.20),(0.20,0.30)]
usable=collections.Counter(); tot=collections.Counter()
by_src=collections.defaultdict(list)
for tk,src,o,c,res in mk:
    tot[src]+=1; by_src[src].append((c,tk,o,res))
cells=collections.defaultdict(list); heldn=collections.Counter()
for src,L in by_src.items():
    L.sort(); cut=2*len(L)//3
    for i,(c,tk,o,res) in enumerate(L):
        if i>=cut: heldn[src]+=1; continue                     # held out, unread
        q=[x for x in cs.get(tk,[]) if x[0]-o<=3600 and x[1] is not None and x[2] is not None]
        if not q: continue
        ts,b,a=max(q)
        if b<=0 or a>=1 or a<=b or a-b>0.05: continue
        usable[src]+=1
        ev=tk.rsplit("-",1)[0]
        for side,p,won in (("yes",a,res=="yes"),("no",1-b,res=="no")):
            for lo,hi in BANDS:
                if lo<=p<hi:
                    net=(1.0 if won else 0.0)-p-float(leg1.fee_per_contract(p))
                    cells[(src,side,(lo,hi))].append((ev,net))
print("markets",dict(tot),"dev with a usable first-hour quote",dict(usable),"held out",dict(heldn))
rows=[]
for k,v in cells.items():
    n,ncl,m,z=leg1.clustered(v); x=[y for _,y in v]
    w=sum(t for t in x if t>0); l=-sum(t for t in x if t<0)
    rows.append((m,k,n,ncl,z,w/l if l>0 else 99.0))
rows.sort(reverse=True)
for m,k,n,ncl,z,p in rows: print("%-16s %-3s %.2f-%.2f n %4d ev %4d PF %.2f mean %+.3f z %.2f"%(k[0],k[1],k[2][0],k[2][1],n,ncl,p,m,z))
sl=[r for r in rows if r[2]>=100 and r[3]>=30 and r[0]>=0.02 and r[4]>=zbar]
print("SHORTLIST:",len(sl))
