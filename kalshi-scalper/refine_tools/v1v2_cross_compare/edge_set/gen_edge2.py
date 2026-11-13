import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gen_mine as G
NBL=0.5595439501147242; NBE=0.620549936201214
B=G.T(2026,11,4,12,0)
# (ticker suffix, close order, yes bid, no bid, filled, win)
spec=[("U0W",0,0.10,0.70,False,True),("U0L",1,0.10,NBL,False,False),("A1",2,0.10,0.898,True,False),
      ("B2",3,0.35,0.648,True,True),("B1",3,0.30,0.698,True,False),("C4",4,0.35,0.648,True,True),
      ("D5",5,0.20,0.798,True,False),("E6",6,0.35,NBE,True,False),
      ("CRX",7,0.60,0.45,False,True),("LCK",8,0.30,0.70,False,True)]   # file order: B2 before B1; CRX crossed, LCK locked
def build(outdir):
    cases=[]
    for tk,o,yb,nb,filled,win in spec:
        close=B+900*o
        c=dict(yb=yb,nb=nb,close=close,result="yes" if win else "no")
        if filled: c["trades"]=[((close-178)*1000+500+3000, round(yb-0.01,6), "no")]
        cases.append((tk,c))
    # reuse the generator with explicit tickers
    ser="KXBTC15M"; book,cov,tr,sig=[],[],[],[]
    for tk,c in cases:
        t="%s-%s"%(ser,tk); close=c["close"]; cts=G.iso(close*1000); t0=(close-178)*1000+500
        book.append(G.brow(t,ser,cts,t0,c["yb"],c["nb"]))
        book.append(G.brow(t,ser,cts,(close-120)*1000+100,c["yb"],c["nb"]))
        for (ms,p,side) in c.get("trades",[]): tr.append({"ticker":t,"created_time":G.iso(ms),"yes_price_dollars":p,"count_fp":"1.00","taker_outcome_side":side})
        cov.append({"close_time":cts,"series":ser,"ticker":t,"result":c["result"]}); sig.append((t,close))
    os.makedirs(outdir,exist_ok=True)
    import csv
    def w(n,cols,rows):
        with open(os.path.join(outdir,n+".csv"),"w",newline="") as f:
            d=csv.DictWriter(f,fieldnames=cols); d.writeheader(); [d.writerow(r) for r in rows]
    w("book",G.BOOK,book); w("trades",G.TR,tr); w("coverage",G.COV,cov)
    with open(outdir+"_signals.csv","w",newline="") as f:
        f.write("ticker,close_ts\n"); [f.write("%s,%d\n"%s) for s in sig]
build(sys.argv[1]+"/v1edge2")
