"""HAND-WORKED expectations, edge set v2 (invented rows; crossed-quote ruling). Plain formulas, written before either build ran on these rows.
Asks are exactly 1 - (NO bid) as both builds compute them. Parent +1c: cost p+0.01, fee 0.07*c*(1-c). Version: fill at its bid, fee 25% of 0.07*b*(1-b). PF = gains / losses. weeks = ceil(15/7) = 3."""
import math, json
NBL=0.5595439501147242; NBE=0.620549936201214
# ticker: (close order, yes bid, no bid, filled, win)
W={"U0W":(0,0.10,0.70,False,True),"U0L":(1,0.10,NBL,False,False),"A1":(2,0.10,0.898,True,False),
   "B1":(3,0.30,0.698,True,False),"B2":(3,0.35,0.648,True,True),"C4":(4,0.35,0.648,True,True),
   "D5":(5,0.20,0.798,True,False),"E6":(6,0.35,NBE,True,False)}
EXTRA={"CRX":"yes bid 0.60, no bid 0.45 (sum 1.05): crossed, no quote","LCK":"yes bid 0.30, no bid 0.70 (sum 1.00): locked, no quote"}
def vnet(b,win): f=0.25*0.07*b*(1-b); return (1-b-f) if win else -(b+f)
def pnet(a,win,slip): c=a+slip; f=0.07*c*(1-c); return (1-c-f) if win else -(c+f)
def pf(xs):
    g=sum(x for x in xs if x>0); l=-sum(x for x in xs if x<0)
    return float("nan") if (g==0 and l==0) else (math.inf if l==0 else g/l)
def rows(order): return [(t,)+W[t] for t in order]
def stats(sig):
    v=[vnet(b,w) for t,o,b,nb,f,w in sig if f]
    return v,[pnet(1-nb,w,0.01) for t,o,b,nb,f,w in sig],[pnet(1-nb,w,0.0) for t,o,b,nb,f,w in sig],[pnet(1-nb,w,0.01) for t,o,b,nb,f,w in sig if not f]
sorted_order=sorted(W,key=lambda t:(W[t][0],t))
input_order=["U0W","U0L","A1","B2","B1","C4","D5","E6"]
stable_close_only=sorted(input_order,key=lambda t:W[t][0])
v,p1,p0,unf=stats(rows(sorted_order))
out={"counts":{"signals":8,"filled":6,"not_filled":2,"crossed_quote":2},"weeks":3,
 "version_pf_25":pf(v),"parent_pf_p1":pf(p1),"parent_pf_p0":pf(p0),"parent_pf_unfilled_p1":pf(unf),
 "bar1_diff":pf(v)-pf(p1),"missed_diff":pf(unf)-pf(v),
 "version_net_week":sum(v)/3,"parent_net_week_p1":sum(p1)/3,"parent_net_week_p0":sum(p0)/3,
 "extra_windows":EXTRA,"sorted_order":sorted_order,"close_only_order":stable_close_only}
def half(order):
    s=rows(order); h=len(s)//2; res=[]
    for part in (s[:h],s[h:]):
        vv,a1,a0,u=stats(part); res.append((pf(vv),pf(a1)))
    return res
def bar3(h):
    (v1,p1_),(v2,p2_)=h; d1,d2=v1-p1_,v2-p2_
    fin=lambda x:x==x and abs(x)!=math.inf
    if fin(d1) and fin(d2): return d2>=d1-1e-9,"finite: d2 %.6f against d1 %.6f"%(d2,d1)
    if v2==math.inf and p2==math.inf: return None,"both inf"
    if v2==math.inf: return True,"second half alone, version infinite"
    if p2==math.inf: return False,"second half alone, parent infinite"
    return v2-p2>=-1e-9,"second half alone finite: %.6f against %.6f"%(v2,p2)
for name,order in (("sorted",sorted_order),("close_only",stable_close_only)):
    h=half(order); b,why=bar3(h); out["bar3_"+name]={"halves":h,"met":b,"why":why}
out["bar1_expected_under_1e-9_tolerance"]= (out["bar1_diff"]>=0.10-1e-9)
out["missed_expected_under_1e-9_tolerance"]=(out["missed_diff"]>=0.10-1e-9)
out["bar1_strict_compare"]=(out["bar1_diff"]>=0.10); out["missed_strict_compare"]=(out["missed_diff"]>=0.10)
out["bar2_met"]=(sum(v)/3>=sum(p0)/3-1e-9) and (sum(v)/3>=sum(p1)/3-1e-9)
json.dump(out,open("expected_by_hand_v2.json","w"),indent=1,default=str); print(json.dumps(out,indent=1,default=str))
