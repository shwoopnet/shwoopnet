import sys,json,math,datetime as D
rep=sys.argv[1];START=sys.argv[2] if len(sys.argv)>2 else '2026-11-08T12:44:00Z'
d=json.load(open(rep))
CUT={'price':{'KXGOLD':0.911,'KXDOGE':0.903},'rise3':{'KXGOLD':0.05,'KXDOGE':0.04}}
rows=[]
for x in d['orders']:
    t=x['ticker'][:6]
    if t not in('KXGOLD','KXDOGE') or x['ts']<=START or not (x.get('count') or 0)>0: continue
    if x.get('result') not in('exit','yes','no') or x.get('avgFill') is None: continue
    c=x['count'];f=x['avgFill'] if x['side']=='yes' else 1-x['avgFill'];fee=(x.get('avgFee') or 0)*c
    if x['result']=='exit':
        ea=x.get('exitAvg');ea=None if ea is None else (ea if x['side']=='yes' else 1-ea)
        pnl=c*((ea if ea is not None else f)-f)-fee
    else: pnl=(c*(1-f) if x['side']==x['result'] else -c*f)-fee
    rows.append(dict(mk=t,y=int(x['result']=='exit'),price=f,rise3=x.get('rise3'),pnl=pnl))
N=len(rows);E=sum(r['y'] for r in rows)
print('S-ESFEAT1 since %s (order ts after): fills %d (gold %d, Dogecoin %d), early sells %d'%(START,N,sum(r['mk']=='KXGOLD' for r in rows),sum(r['mk']=='KXDOGE' for r in rows),E))
def cdf(k,n,p): return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k+1))
def cp(k,n,a=0.05):
    if n==0: return (float('nan'),)*2
    def bis(f):
        lo,hi=0.,1.
        for _ in range(60):
            m=(lo+hi)/2
            if f(m): hi=m
            else: lo=m
        return lo
    return (0 if k==0 else bis(lambda p:1-cdf(k-1,n,p)>=a/2), 1 if k==n else bis(lambda p:cdf(k,n,p)<=a/2))
def fisher1(a,n1,b,n2):
    K=a+b;T=n1+n2
    if n1==0 or n2==0: return float('nan')
    return sum(math.comb(K,i)*math.comb(T-K,n1-i) for i in range(a,min(K,n1)+1))/math.comb(T,n1)
BAR=0.05/20
for lead in('price','rise3'):
    s=[r for r in rows if r[lead] is not None]
    H=[r for r in s if r[lead]<=CUT[lead][r['mk']]];Rt=[r for r in s if r[lead]>CUT[lead][r['mk']]]
    a,n1,b,n2=sum(r['y'] for r in H),len(H),sum(r['y'] for r in Rt),len(Rt)
    print('\nlead %s: T1 cutoffs gold <= %s, Dogecoin <= %s; rows used %d of %d'%(lead,CUT[lead]['KXGOLD'],CUT[lead]['KXDOGE'],len(s),N))
    if n1==0 or n2==0:
        print('  H %d/%d, rest %d/%d: no rates yet'%(a,n1,b,n2));continue
    l1=cp(a,n1);l2=cp(b,n2);diff=100*(a/n1-b/n2);p=fisher1(a,n1,b,n2)
    print('  H   %d/%d = %.1f%% [%.1f, %.1f]'%(a,n1,100*a/n1,100*l1[0],100*l1[1]))
    print('  rest %d/%d = %.1f%% [%.1f, %.1f]'%(b,n2,100*b/n2,100*l2[0],100*l2[1]))
    print('  diff %+.1f points, one-sided exact Fisher p=%.4f (20-test bar %.4f)'%(diff,p,BAR))
    print('  early-sell $ (fill-booked, entry fee only): H %.2f, rest %.2f'%(sum(r['pnl'] for r in H if r['y']),sum(r['pnl'] for r in Rt if r['y'])))
if E>=20 or N>=300:
    print('\nREAD POINT reached (early sells %d/20, fills %d/300): see leads above; pass needs diff >= 4 points AND p < 0.05 AND direction as registered; a failing lead is CLOSED, not re-run. Information only, owner decides any change.'%(E,N))
else:
    print('\nNOT AT READ POINT: early sells %d/20, fills %d/300'%(E,N))
