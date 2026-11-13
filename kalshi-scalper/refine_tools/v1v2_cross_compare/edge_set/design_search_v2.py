import math, itertools, json
def vnet(b,win): f=0.25*0.07*b*(1-b); return (1-b-f) if win else -(b+f)
def pnet(a,win,slip=0.01): c=a+slip; f=0.07*c*(1-c); return (1-c-f) if win else -(c+f)
def pf(xs):
    g=sum(x for x in xs if x>0); l=-sum(x for x in xs if x<0)
    return float("nan") if (g==0 and l==0) else (math.inf if l==0 else g/l)
names=["U0W","U0L","A1","B1","B2","C4","D5","E6"]
order={"U0W":0,"U0L":1,"A1":2,"B1":3,"B2":3,"C4":4,"D5":5,"E6":6}
BID={"U0W":.10,"U0L":.10,"A1":.10,"B1":.30,"B2":.35,"C4":.35,"D5":.20,"E6":.35}
filled={t:(t not in("U0W","U0L")) for t in names}
def M(win,ask):
    v=[vnet(BID[t],win[t]) for t in names if filled[t]]
    pa=[pnet(ask[t],win[t]) for t in names]; pu=[pnet(ask[t],win[t]) for t in names if not filled[t]]
    return pf(v),pf(pa),pf(pu)
def root(fn,lo,hi):
    flo=fn(lo)
    if not (flo*fn(hi)<0): return None
    for _ in range(300):
        m=(lo+hi)/2
        if (fn(m)>0)==(flo>0): lo=m
        else: hi=m
    return lo,hi
def nudge(fn,x,var_nb):
    """float neighbours of x (as nb when var_nb, so ask=1-nb); return the one with fn<0 and closest to 0"""
    best=None
    for d in (-1,1):
        c=x
        for k in range(3000):
            c=math.nextafter(c,2 if d>0 else 0)
            val=fn(c)
            if val<0 and (best is None or val>best[0]): best=(val,c)
    return best
def tune(win,u0l_rng=(0.12,0.45),e6_rng=(0.36,0.5)):
    ask={t:BID[t]+0.002 for t in names}; ask["U0W"]=0.30; ask["E6"]=0.40
    def fl(nb):
        ask["U0L"]=1-nb; v,pa,pu=M(win,ask); return pu-v-0.10
    r=root(fl,1-u0l_rng[1],1-u0l_rng[0])
    if not r: return None
    b=nudge(fl,r[0],True)
    if not b: return None
    nbL=b[1]; fl(nbL)
    def fe(nb):
        ask["E6"]=1-nb; v,pa,pu=M(win,ask); return v-pa-0.10
    r=root(fe,1-e6_rng[1],1-e6_rng[0])
    if not r: return None
    b=nudge(fe,r[0],True)
    if not b: return None
    nbE=b[1]; fe(nbE); fl(nbL)   # re-evaluate missed with final E6 (E6 does not enter P_unf or v)
    v,pa,pu=M(win,ask)
    return ask,nbL,nbE,v-pa,pu-v
def halves(win,ask,ordr):
    w=sorted(names,key=lambda t:ordr.index(t)); h=len(w)//2; res=[]
    for part in (w[:h],w[h:]):
        v=[vnet(BID[t],win[t]) for t in part if filled[t]]; pa=[pnet(ask[t],win[t]) for t in part]
        res.append((pf(v),pf(pa)))
    (v1,p1),(v2,p2)=res; return v1,p1,v2,p2
def bar3(v1,p1,v2,p2):
    d1,d2=v1-p1,v2-p2; fin=lambda x:x==x and abs(x)!=math.inf
    if v1!=v1 or v2!=v2: return False
    if fin(d1) and fin(d2): return d2>=d1-1e-9
    if v2==math.inf and p2==math.inf: return None
    if v2==math.inf: return True
    if p2==math.inf: return False
    return v2-p2>=-1e-9
S_o=sorted(names,key=lambda t:(order[t],t)); U_o=sorted(["U0W","U0L","A1","B2","B1","C4","D5","E6"],key=lambda t:order[t])
out=[]
for combo in itertools.product([True,False],repeat=6):
    win={"U0W":True,"U0L":False}; win.update(dict(zip(["A1","B1","B2","C4","D5","E6"],combo)))
    if win["E6"]: continue
    t=tune(win)
    if not t: continue
    ask,nbL,nbE,d1,d2=t
    if not (d1<0.10 and d2<0.10 and d1>0.0999999 and d2>0.0999999): continue
    legal=all(BID[x]<ask[x]<=0.5 and ask[x]>=0.05 for x in names)
    a=bar3(*halves(win,ask,S_o)); b=bar3(*halves(win,ask,U_o))
    if legal and a is not None and b is not None and a!=b:
        print(combo,a,b,"nbL",repr(nbL),"nbE",repr(nbE),d1,d2)
