import sys,json,datetime as D
rep=sys.argv[1]; start=sys.argv[2] if len(sys.argv)>2 else '2026-11-09T16:22:00Z'
d=json.load(open(rep))
rows=[]
for o in d['orders']:
    if not o['ticker'].startswith('KXGOLD'): continue
    c=o.get('count') or 0
    if c<=0 or o.get('avgFill') is None or o.get('settledPnl') is None or o.get('result') not in('yes','no','exit'): continue
    y=o['side']=='yes'; paid=o['avgFill'] if y else 1-o['avgFill']; fee=(o.get('avgFee') or 0)*c
    if o['result']=='exit':
        lim=o.get('limit'); p=o['settledPnl']+(c*((lim if y else 1-lim)-paid) if lim is not None else 0)
    elif o['result']==o['side']: p=c*(1-paid)-fee
    else: p=-c*paid-fee
    rows.append((o['ts'],p))
rows.sort()
def pf(v):
    g=sum(x for x in v if x>0); l=-sum(x for x in v if x<0)
    return g/l if l else float('inf')
since=[r for r in rows if r[0]>=start.replace('Z','')]
print('gold settled trades total %d (first %s); since %s: n=%d/100'%(len(rows),rows[0][0][:16],start,len(since)))
v=[p for _,p in since]
print('since start: cumulative PF %s net $%.2f'%(('%.2f'%pf(v)) if v else 'n/a',sum(v)))
roll=[(rows[i+59][0],pf([p for _,p in rows[i:i+60]])) for i in range(len(rows)-59)]
trip=[]
if roll:
    mn=min(roll,key=lambda x:x[1])
    print('rolling-60 PF: min %.2f ending %s; latest %.2f ending %s'%(mn[1],mn[0][:16],roll[-1][1],roll[-1][0][:16]))
    print('last 10 rolling-60 PF:',' '.join('%.2f'%x[1] for x in roll[-10:]))
    below=[x for x in roll if x[1]<0.7]
    print('windows below 0.7 in history: %d of %d'%(len(below),len(roll)))
# rule (b): history before the start is informational (5 windows already below 0.7); only windows ending since the start trip
if roll and any(x[1]<0.7 for x in roll if x[0]>=start.replace('Z','')): trip.append('(b) a window ending since start is below 0.7')
if len(since)>=100 and pf([p for _,p in since[:100]])<1.0: trip.append('(a) PF of first 100 since start %.2f < 1.0'%pf([p for _,p in since[:100]]))
# whole record, 7 trading days
days=sorted({r[0][:10] for r in rows})[-7:]
w=[p for t,p in rows if t[:10]>=days[0]]
print('whole record last 7 trading days (%s..%s): n=%d PF %.2f net $%.2f'%(days[0],days[-1],len(w),pf(w),sum(w)))
print('TRIPWIRE: '+('TRIPPED '+'; '.join(trip) if trip else 'OK')+' (n since start %d/100, cum PF %s, latest r60 %s)'%(len(since),('%.2f'%pf(v)) if v else 'n/a','%.2f'%roll[-1][1] if roll else 'n/a'))
