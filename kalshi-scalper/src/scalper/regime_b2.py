"""Batch 2 shadow rules by regime on history (cash basis, unrounded fee 0.07*p*(1-p) per contract, no slip). Research only."""
import sqlite3, collections, datetime, sys
RULES = [  # id, db, series, lo, hi, left_hi, left_lo, maxspread
 ("XRPFAV6","data/alts2.sqlite","KXXRP15M",0.88,0.92,400,330,0.02),
 ("XRPFAV10","data/alts2.sqlite","KXXRP15M",0.88,0.92,640,570,None),
 ("GOLDHI6S","data/hist15/KXGOLD15M.sqlite","KXGOLD15M",0.92,0.97,400,330,0.02),
 ("BTCHI10","data/hist15/KXBTC15M.sqlite","KXBTC15M",0.92,0.97,640,570,None),
]
def fee(p): return 0.07*p*(1-p)
def pf(xs):
    w=sum(x for x in xs if x>0); l=-sum(x for x in xs if x<0)
    return (w/l if l>0 else 99.0)
def et(ts):  # Eastern, fixed UTC-5 as in earlier registrations
    return datetime.datetime.utcfromtimestamp(ts-5*3600)
for rid,db,ser,lo,hi,l_hi,l_lo,msp in RULES:
    c=sqlite3.connect(db)
    mk={t:(ct,r) for t,ct,r in c.execute("select ticker,close_ts,result from market where series=? and result in ('yes','no') and n_candles>0",(ser,))}
    by=collections.defaultdict(dict)
    for tk,ts,b,a in c.execute("select ticker,end_ts,bid_c,ask_c from candle where series=?",(ser,)):
        if tk in mk and b is not None and a is not None: by[tk][ts]=(b,a)
    rows=[]
    for tk,cs in by.items():
        ct,res=mk[tk]
        pick=None
        for ts in sorted(cs):
            left=ct-ts
            if l_lo<=left<=l_hi: pick=ts
        if pick is None: continue
        b,a=cs[pick]
        if b<=0 or a>=1 or a<=b: continue
        if msp is not None and a-b>msp: continue
        ysp,nsp=a,1-b
        side,p=("yes",ysp) if ysp>=nsp else ("no",nsp)
        if not (lo<=p<=hi): continue
        net=(1.0 if res==side else 0.0)-p-fee(p)
        prev=cs.get(pick-180)
        mid=lambda q:(q[0]+q[1])/2
        rise=None
        if prev: rise=(mid(cs[pick])-mid(prev))*(1 if side=="yes" else -1)
        d=et(pick)
        rows.append(dict(t=ct,net=net,spr=a-b,clock=7<=d.hour<17,wk=d.weekday()<5,rise=rise))
    rows.sort(key=lambda r:r["t"]); n=len(rows)
    days=len({r["t"]//86400 for r in rows})
    def line(name,sel):
        s=[r for r in rows if sel(r)]
        if len(s)<20: return "  %-18s n %4d (too few)"%(name,len(s))
        h=len(s)//2
        x=[r["net"] for r in s]
        return "  %-18s n %4d PF %.2f net %+.2f$/contract-sum | halves %.2f / %.2f"%(name,len(s),pf(x),sum(x),pf(x[:h]),pf(x[h:]))
    print("\n%s %s: %d trades over %d days"%(rid,ser,n,days))
    if n==0: continue
    print(line("ALL",lambda r:True))
    print(line("R1 spread<=0.01",lambda r:r["spr"]<=0.01)); print(line("R1 spread>0.01",lambda r:r["spr"]>0.01))
    print(line("R2 US day 7-17E",lambda r:r["clock"])); print(line("R2 other hours",lambda r:not r["clock"]))
    print(line("R3 weekday",lambda r:r["wk"])); print(line("R3 weekend",lambda r:not r["wk"]))
    print(line("R4 moving>=0.05",lambda r:r["rise"] is not None and abs(r["rise"])>=0.05)); print(line("R4 still<0.05",lambda r:r["rise"] is not None and abs(r["rise"])<0.05))
