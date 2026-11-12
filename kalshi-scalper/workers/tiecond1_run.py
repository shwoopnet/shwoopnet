import sqlite3,collections,math,json,datetime,statistics
CUT=1791158400
F=["alts2","alts3","alts4","rep","fxusd/candles","l1b","book","five","hist15/KXGOLD15M"]
GRP={}
for s in "EURUSD GBPUSD USDJPY AUDUSD USDCAD".split(): GRP["KX"+s+"15M"]="FX"
for s in "SILVER COPPER PLATINUM PALLADIUM GOLD".split(): GRP["KX"+s+"15M"]="metals"
for s in "WTI NATGAS BRENT".split(): GRP["KX"+s+"15M"]="energy"
CRYPTO={"KXBTC15M","KXETH15M","KXSOL15M","KXXRP15M","KXDOGE15M","KXBNB15M","KXHYPE15M","KXNEAR15M","KXZEC15M"}
seen=set(); rows=collections.defaultdict(list); allseries=set(); exist=[]
for f in F:
    c=sqlite3.connect(f"file:data/{f}.sqlite?mode=ro",uri=True)
    for t,s,o,cl,r,k in c.execute("select ticker,series,open_ts,close_ts,result,strike from market"):
        if s in CRYPTO: continue
        if s not in GRP: allseries.add(s); continue
        if t in seen: continue
        seen.add(t)
        exist.append((GRP[s],o,cl))  # existence only
        if cl<CUT and r in("yes","no") and k is not None: rows[s].append((cl,o,r,k))
print("unmapped non-crypto series:",allseries)
def wil(x,n):
    z=1.96;p=x/n;d=1+z*z/n;c=p+z*z/(2*n);h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return (c-h)/d,(c+h)/d
out={"stage0":{},"cells":{}}
pairs={}
for s,L in rows.items():
    L.sort(); g=GRP[s]
    # pair index i: window i with window i+1 contiguous
    P=[]; ag=0; n=0; tiebad=0
    for i in range(len(L)-1):
        a,b=L[i],L[i+1]
        if b[0]-a[0]==900 and b[1]==a[0]:
            d=round(b[3]-a[3],6); n+=1
            ok=(a[2]=="yes")==(d>=0); ag+=ok
            if d==0 and a[2]=="no": tiebad+=1
            P.append((i,d))
    out["stage0"][s]=dict(group=g,windows=len(L),pairs=n,agree=ag/n if n else None,ties_settling_no=tiebad)
    print(s,out["stage0"][s])
    pairs[s]=(L,dict(P))
keep={s for s,v in out["stage0"].items() if v["pairs"] and v["agree"]>=0.995}
bad={s for s,v in out["stage0"].items() if v["ties_settling_no"]}
if bad: print("STOP ties settle NO:",bad)
print("dropped",set(out["stage0"])-keep)
cell=collections.defaultdict(lambda:[0,0]); q8rows=[]
for s in keep:
    L,D=pairs[s]; g=GRP[s]
    ds=[abs(D[i]) for i in sorted(D)]
    pos=[abs(D[i]) for i in sorted(D) if i<500 and D[i]!=0]
    tick=min(pos) if pos else None
    # contiguity: window i's d defined; predictors need D[i-1..i-8] all defined (D[j] defined means j,j+1 contiguous), and window i itself in D
    feats=[]
    for i in sorted(D):
        if all((i-j) in D for j in range(1,9)):
            q8=statistics.median(abs(D[i-j])/tick for j in range(1,9))
            t4=sum(D[i-j]==0 for j in range(1,5))
            feats.append((i,q8,t4,D[i]==0,L[i][0]))
    if not feats: continue
    third=L[len(L)//3][0]  # first third of this series' dates
    ref=sorted(f[1] for f in feats if f[4]<=third)
    if len(ref)<3: continue
    c1,c2=ref[len(ref)//3],ref[2*len(ref)//3]
    for i,q8,t4,tie,ct in feats:
        ter=0 if q8<=c1 else (1 if q8<=c2 else 2)
        for key in ((g,"q8",ter),(g,"ties4",min(t4,2))):
            cell[key][0]+=tie; cell[key][1]+=1
    print(s,"tick",tick,"cuts",c1,c2,"feat windows",len(feats),"ties",sum(f[3] for f in feats))
res=[]
for k,(x,n) in sorted(cell.items()):
    lo,hi=wil(x,n); res.append(dict(group=k[0],pred=k[1],bin=k[2],n=n,ties=x,rate=x/n,lo=lo,hi=hi))
    print(k,n,x,round(x/n,4),round(lo,4),round(hi,4))
big=[r for r in res if r["n"]>=300]
best=max(res,key=lambda r:r["lo"]) if res else None
print("cells n>=300:",len(big),"passing lo>=6%:",[r for r in big if r["lo"]>=0.06])
print("best",best)
print("KILL GATE:", "CLOSED" if not any(r["lo"]>=0.06 for r in big) else "SURVIVES")
# existence counts (no outcome columns)
def dt(t): return datetime.datetime.fromtimestamp(t,datetime.timezone.utc)
ex=collections.defaultdict(lambda:collections.Counter())
for g,o,cl in exist:
    d=dt(o); ex[g]["all"]+=1
    if d.hour==21: ex[g]["break_21utc"]+=1
    if d.weekday()>=5: ex[g]["weekend"]+=1
    if (d.month,d.day)==(9,7): ex[g]["labor_day_sep7"]+=1
    if (d.month,d.day)==(10,12): ex[g]["columbus_oct12"]+=1
print({g:dict(v) for g,v in ex.items()})
json.dump(dict(stage0=out["stage0"],cells=res,exist={g:dict(v) for g,v in ex.items()}),open("data/tiecond1_result.json","w"),indent=1)
