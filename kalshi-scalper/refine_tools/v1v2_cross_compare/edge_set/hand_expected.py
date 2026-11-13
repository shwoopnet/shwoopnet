"""HAND-WORKED expectations for the edge set (invented rows). Plain formulas, written before either build ran on the finished rows.
Parent +1c: cost p+0.01, fee 0.07*c*(1-c) at the paid price. Version: fill at its bid, fee 25% of 0.07*b*(1-b). PF = gains / losses.
Net per contract-week uses weeks = ceil(15 / 7) = 3 for the V1 dev block (2026-10-29T22:15Z to 2026-11-13T23:59:59Z)."""
import math, json
NB_U0W=0.5834525848860371; NB_E6=0.8998608543712031
# ticker: (close order, yes bid = our limit, no bid, filled, win)
W={"U0W":(0,0.10,NB_U0W,False,True),"U0L":(1,0.10,0.88,False,False),"A1":(2,0.10,0.88,True,True),
   "B1":(3,0.30,0.68,True,True),"B2":(3,0.10,0.88,True,False),"C4":(4,0.30,0.68,True,False),
   "D5":(5,0.20,0.78,True,True),"E6":(6,0.20,NB_E6,True,False)}
def vnet(b,win): f=0.25*0.07*b*(1-b); return (1-b-f) if win else -(b+f)
def pnet(a,win,slip): c=a+slip; f=0.07*c*(1-c); return (1-c-f) if win else -(c+f)
def pf(xs):
    g=sum(x for x in xs if x>0); l=-sum(x for x in xs if x<0)
    return float("nan") if (g==0 and l==0) else (math.inf if l==0 else g/l)
def rows(order):
    return [(t,)+W[t] for t in order]
def stats(sig):
    v=[vnet(b,w) for t,o,b,nb,f,w in sig if f]
    pall1=[pnet(1-nb,w,0.01) for t,o,b,nb,f,w in sig]; pall0=[pnet(1-nb,w,0.0) for t,o,b,nb,f,w in sig]
    unf=[pnet(1-nb,w,0.01) for t,o,b,nb,f,w in sig if not f]
    return v,pall1,pall0,unf
sorted_order=sorted(W,key=lambda t:(W[t][0],t))                 # (close, ticker)
input_order=["U0W","U0L","A1","B2","B1","C4","D5","E6"]       # the signals file order (B2 before B1), stable sort by close only
v,p1,p0,unf=stats(rows(sorted_order))
out={"signals":8,"fills":6,"weeks":3,"sorted_order":sorted_order,"input_order_stable_by_close":sorted(input_order,key=lambda t:W[t][0]),
 "version_pf_25":pf(v),"parent_pf_p1":pf(p1),"parent_pf_p0":pf(p0),"parent_pf_unfilled_p1":pf(unf),
 "bar1_diff":pf(v)-pf(p1),"missed_diff":pf(unf)-pf(v),
 "version_net_week":sum(v)/3,"parent_net_week_p1":sum(p1)/3,"parent_net_week_p0":sum(p0)/3}
def half(order):
    s=rows(order); h=len(s)//2
    res=[]
    for part in (s[:h],s[h:]):
        vv,a1,a0,u=stats(part); res.append((pf(vv),pf(a1),sum(vv),sum(a0)))
    return res
for name,order in (("sorted",sorted_order),("unsorted",out["input_order_stable_by_close"])):
    (v1,p1_,vn1,pn1),(v2,p2_,vn2,pn2)=half(order)
    d1,d2=v1-p1_,v2-p2_
    out["halves_"+name]={"first":[v1,p1_],"second":[v2,p2_],"d1":d1,"d2":d2,"bar3_finite_met":d2>=d1-1e-9}
json.dump(out,open("expected_by_hand.json","w"),indent=1,default=str)
print(json.dumps(out,indent=1,default=str))
