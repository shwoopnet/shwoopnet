import sys,json,math
# S-LIM1-LIVE review: tag OICORE orders filled ABOVE the price first seen; report net of the tagged ones. Input: report JSON (hours=2160&orders=1) on stdin.
d=json.load(sys.stdin)
def feeo(c,p): return math.ceil(7*c*p*(1-p)-1e-9)/100   # Kalshi fee for the whole order, rounded up to the cent
rows=[]
for o in sorted([o for o in d['slotOrders'] if o.get('strategy')=='OICORE'],key=lambda o:o['ts']):
    if o['status']!='filled' or o['settledPnl'] is None or not o['count']: continue
    sa=o['seenAsk'] if o['side']=='yes' else 1-o['seenBid']
    c=o['count']
    if o['avgFill'] is not None: p=o['avgFill'] if o['side']=='yes' else 1-o['avgFill']   # NO avgFill is in YES terms (W-LIM1CHECK, Nov 8)
    else:
        pnl=o['settledPnl']
        # a win pays c*(1-p) minus fee; a loss costs c*p plus fee. The market result decides which.
        win=(o['result']==o['side'])
        p=0.1
        for _ in range(8): p=(1-(pnl+feeo(c,p))/c) if win else ((-pnl-feeo(c,p))/c)
    rows.append((o['ts'],o['side'],round(sa,3),round(p,3),round(p-sa,3),o['settledPnl'],o['count']))
tag=[r for r in rows if r[4]>=0.0095]
print('filled+settled',len(rows),'tagged (fill >= 1c above first-seen ask)',len(tag))
for r in tag: print(r)
n=sum(r[5] for r in tag);print('tagged net $%.2f'%n,'n',len(tag),'(review at 20; revert if net below zero)')
print('untagged net $%.2f'%sum(r[5] for r in rows if r[4]<0.0095))
