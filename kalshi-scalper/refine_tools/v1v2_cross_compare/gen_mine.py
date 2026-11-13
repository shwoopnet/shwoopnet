"""My invented rows for the V1/V2 cross-comparison. Plain csv in the recorders' columns; values are never changed when mapped."""
import csv, os, sys, calendar
BOOK=["t_send_ms","t_recv_ms","server_date_header","ticker","series","close_time"]+["yes_bid_px_%d"%i for i in range(1,6)]+["yes_bid_sz_%d"%i for i in range(1,6)]+["no_bid_px_%d"%i for i in range(1,6)]+["no_bid_sz_%d"%i for i in range(1,6)]
COV=["close_time","series","ticker","polls","ok_polls","n429","batch_fallback","max_gap_ms","first_recv_ms","last_recv_ms","book_rows","tape_pages","tape_trades","dupes_dropped","tape_sum_count","volume_fp","result","note"]
TR=["ticker","created_time","yes_price_dollars","count_fp","taker_outcome_side"]
def T(y,mo,d,h,mi): return calendar.timegm((y,mo,d,h,mi,0))
def brow(tk,ser,ct,ms,yb,nb):
    r={c:"" for c in BOOK}; r.update(t_send_ms=ms,t_recv_ms=ms,server_date_header="x",ticker=tk,series=ser,close_time=ct,yes_bid_px_1=yb,yes_bid_sz_1=10 if yb!="" else "",no_bid_px_1=nb,no_bid_sz_1=10 if nb!="" else ""); return r
def iso(ms): 
    import time; return time.strftime("%Y-%m-%dT%H:%M:%S",time.gmtime(ms//1000))+(".%03dZ"%(ms%1000) if ms%1000 else "Z")
def build(version, outdir, cases):
    ser="KXBTC15M" if version=="V1" else "KXSILVER15M"
    lead=178 if version=="V1" else 180
    book,cov,tr,sig=[],[],[],[]
    for k,c in enumerate(cases):
        tk="%s-X%d"%(ser,k+1); close=c["close"]; cts=iso(close*1000)
        t0=(close-lead)*1000+c.get("t0late",500)
        if not c.get("no_t0"): book.append(brow(tk,ser,cts,t0,c["yb"],c["nb"]))
        for (off,yb,nb) in c.get("later",[]): book.append(brow(tk,ser,cts,t0+off,yb,nb))
        book.append(brow(tk,ser,cts,c.get("cancel_ms",(close-120)*1000+100),c.get("cyb",c["yb"]),c.get("cnb",c["nb"])))
        for (ms,p,side) in c.get("trades",[]): tr.append({"ticker":tk,"created_time":iso(ms) if isinstance(ms,int) else ms,"yes_price_dollars":p,"count_fp":"1.00","taker_outcome_side":side})
        for res in c.get("results",[c.get("result","yes")]):
            cov.append({"close_time":cts,"series":ser,"ticker":tk,"result":res})
        sig.append((tk,close))
    os.makedirs(outdir,exist_ok=True)
    def w(n,cols,rows):
        with open(os.path.join(outdir,n+".csv"),"w",newline="") as f:
            d=csv.DictWriter(f,fieldnames=cols); d.writeheader(); [d.writerow(r) for r in rows]
    w("book",BOOK,book); w("trades",TR,tr); w("coverage",COV,cov)
    with open(outdir+"_signals.csv","w",newline="") as f:
        f.write("ticker,close_ts\n"); [f.write("%s,%d\n"%s) for s in sig]
B=T(2026,11,3,12,0)
def v1cases():
    t=lambda close,off: (close-178)*1000+500+off
    C=[]
    def add(i,**k): k.setdefault("close",B+900*i); C.append(k)
    add(1,yb=0.10,nb=0.85,trades=[(t(B+900*1,3000),0.09,"no")],result="no")            # fill by trade, loss
    add(2,yb=0.10,nb=0.85,result="yes")                                                  # no trade, unfilled winner
    add(3,yb=0.10,nb=0.85,trades=[(t(B+900*3,3000),0.10,"no")],result="yes")            # touch only
    add(4,yb=0.10,nb=0.85,later=[(4000,0.05,0.90)],result="yes")                         # fill by book ask <= bid
    add(5,yb=0.70,nb=0.20,trades=[(t(B+900*5,3000),0.81,"yes")],result="no")            # NO side fill by trade, win
    add(6,yb=0.50,nb=0.50,trades=[(t(B+900*6,3000),0.49,"no")],result="yes")            # tie of asks takes YES, band edge .50
    add(7,yb=0.02,nb=0.95,result="yes")                                                  # ask exactly .05
    add(8,yb=0.02,nb=0.96,result="yes")                                                  # ask .04 below band
    add(9,yb=0.40,nb=0.49,result="yes")                                                  # YES ask .51 above band, NO .60
    add(10,yb="",nb=0.85,result="no")                                                    # no bid
    add(11,yb=0.10,nb=0.85,t0late=12000,result="yes")                                    # t0 row 12 s late
    add(12,yb=0.10,nb=0.85,result="")                                                    # no result
    add(13,yb=0.10,nb=0.85,trades=[("%s.500Z"%iso((B+900*13-120)*1000)[:19],0.05,"no")],result="yes")   # fraction: after the cancel row
    add(14,yb=0.10,nb=0.85,cancel_ms=(B+900*14-120)*1000,trades=[("%s.000Z"%iso((B+900*14-120)*1000)[:19],0.05,"no")],result="yes")  # trade exactly at cancel row
    add(15,yb=0.10,nb=0.85,close=T(2026,11,14,0,15),result="yes")                         # outside the block
    add(16,yb=0.10,nb=0.85,results=["yes",""],result="yes")                               # coverage: yes row then empty row
    add(17,yb=0.10,nb=0.85,trades=[(t(B+900*17,3000),0.05,"yes")],result="yes")           # wrong taker side
    add(18,yb=0.30,nb=0.65,trades=[(t(B+900*18,3000),0.29,"no")],result="yes")           # YES ask .35 bid .30 fill, win
    add(19,yb=0.30,nb=0.65,trades=[(t(B+900*19,3000),0.20,"no")],result="no")            # fill, loss
    add(20,yb=0.10,nb=0.0,result="yes")                                                    # NO bid 0.00: no YES ask; NO ask .90 out of band
    add(21,yb=0.0,nb=0.85,result="no")                                                     # YES bid 0.00: no YES bid, YES ask .15, no order
    add(22,yb=0.10,nb=0.85,close=B+900*22,trades=[(t(B+900*22,3000),0.09,"no")],result="no")   # two windows with the SAME close: ticker order decides the half split
    add(23,yb=0.10,nb=0.85,close=B+900*22,result="yes")
    add(24,yb=0.10,nb=0.85,close=B+900*22,trades=[(t(B+900*22,3000),0.05,"no")],result="yes")
    return C
def v2cases():
    t=lambda close,off: (close-180)*1000+500+off
    C=[]; b=T(2026,11,13,12,0)
    def add(i,**k): k.setdefault("close",b+900*i); C.append(k)
    add(1,yb=0.20,nb=0.78,trades=[(t(b+900*1,3000),0.19,"no")],result="yes")           # spread .02 fill, win
    add(2,yb=0.30,nb=0.60,result="no")                                                   # spread exactly .10, unfilled
    add(3,yb=0.30,nb=0.59,result="no")                                                   # spread .11 fails
    add(4,yb="",nb=0.80,result="no")                                                     # no YES bid
    add(5,yb=0.70,nb=0.25,trades=[(t(b+900*5,3000),0.76,"yes")],result="yes")           # NO cheaper, fill, loss
    add(6,yb=0.20,nb=0.78,t0late=0,later=[(2000,0.10,0.88)],result="yes")                # t0 at exactly the target; fill by book
    add(7,yb=0.20,nb=0.78,close=T(2026,12,8,12,0),result="yes")                           # outside the block
    add(8,yb=0.20,nb=0.78,trades=[(t(b+900*8,3000),0.19,"no")],result="no")              # fill, loss
    return C
if __name__=="__main__":
    base=sys.argv[1]
    build("V1",os.path.join(base,"v1mine"),v1cases()); build("V2",os.path.join(base,"v2mine"),v2cases())
