import math, itertools, json
def vnet(b,win): f=0.25*0.07*b*(1-b); return (1-b-f) if win else -(b+f)
def pnet(a,win,slip=0.01): c=a+slip; f=0.07*c*(1-c); return (1-c-f) if win else -(c+f)
def pf(xs):
    g=sum(x for x in xs if x>0); l=-sum(x for x in xs if x<0)
    return float("nan") if (g==0 and l==0) else (math.inf if l==0 else g/l)
names=["U0W","U0L","A1","B1","B2","C4","D5","E6"]
order={"U0W":0,"U0L":1,"A1":2,"B1":3,"B2":3,"C4":4,"D5":5,"E6":6}
bid={"U0W":.10,"U0L":.10,"A1":.10,"B1":.30,"B2":.10,"C4":.30,"D5":.20,"E6":.20}
ask0={"U0W":.12,"U0L":.12,"A1":.12,"B1":.32,"B2":.12,"C4":.32,"D5":.22,"E6":.22}
filled={t:(t not in("U0W","U0L")) for t in names}
def mk(win,ask): return [(t,bid[t],ask[t],filled[t],win[t]) for t in names]
def met(w):
    v=[vnet(b,wn) for t,b,a,f,wn in w if f]; pa=[pnet(a,wn) for t,b,a,f,wn in w]; pu=[pnet(a,wn) for t,b,a,f,wn in w if not f]
    return pf(v),pf(pa),pf(pu)
def tune(win):
    ask=dict(ask0)
    v=met(mk(win,ask))[0]
    def bis(fn,lo,hi):
        flo=fn(lo)
        if flo==0 or fn(hi)*flo>0: return None
        for _ in range(200):
            m=(lo+hi)/2
            if (fn(m)>0)==(flo>0): lo=m
            else: hi=m
        return lo,hi
    r=bis(lambda nb: met(mk(win,{**ask,"U0W":1-nb}))[2]-v-0.10,0.55,0.94)
    if not r: return None
    nbU=None
    for x in r:
        pass
    # nudge below the line
    best=None
    c=r[0]
    for k in range(-3000,3000):
        cc=c
        for _ in range(abs(k)): cc=math.nextafter(cc,2 if k>0 else 0)
        d=met(mk(win,{**ask,"U0W":1-cc}))[2]-v
        if d<0.10 and (best is None or d>best[0]): best=(d,cc)
    if not best: return None
    ask["U0W"]=1-best[1]; nbU=best[1]
    g2=lambda nb: (lambda m:m[0]-m[1])(met(mk(win,{**ask,"E6":1-nb})))-0.10
    r=bis(g2,0.5,0.95)
    if not r: return None
    cand=[x for x in r if g2(x)<0]
    if not cand: return None
    nbE=max(cand,key=g2); ask["E6"]=1-nbE
    return ask,nbU,nbE
def halves(win,ask,ordr):
    w=mk(win,ask); w=sorted(w,key=lambda r:ordr.index(r[0])); h=len(w)//2; res=[]
    for part in (w[:h],w[h:]):
        v=[vnet(b,wn) for t,b,a,f,wn in part if f]; pa=[pnet(a,wn) for t,b,a,f,wn in part]
        res.append((pf(v),pf(pa)))
    (v1,p1),(v2,p2)=res; return v1,p1,v2,p2
def bar3(v1,p1,v2,p2):
    d1,d2=v1-p1,v2-p2
    fin=lambda x: x==x and abs(x)!=math.inf
    if any(x!=x for x in (v1,v2)): return False
    if fin(d1) and fin(d2): return d2>=d1-1e-9
    # second half alone
    if v2==math.inf and p2==math.inf: return None
    if v2==math.inf: return True
    if p2==math.inf: return False
    return v2-p2>=-1e-9
sorted_o=sorted(names,key=lambda t:(order[t],t)); unsorted_o=sorted(["U0W","U0L","A1","B2","B1","C4","D5","E6"],key=lambda t:order[t])
for combo in itertools.product([True,False],repeat=6):
    win={"U0W":True,"U0L":False}; win.update(dict(zip(["A1","B1","B2","C4","D5","E6"],combo)))
    if win["E6"]: continue
    t=tune(win)
    if not t: continue
    ask,nbU,nbE=t
    a=bar3(*halves(win,ask,sorted_o)); b=bar3(*halves(win,ask,unsorted_o))
    if a is not None and b is not None and a!=b:
        print(combo,a,b,nbU,nbE)
