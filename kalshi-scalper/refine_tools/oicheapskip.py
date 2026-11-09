#!/usr/bin/env python3 -I
"""S-OICHEAPSKIP1. Read only: public GETs, no key. See REGISTRATION.md.
Usage: python3 -I oicheapskip.py report.json [deploy_ts_iso]   (default deploy ts: DEPLOY_TS file beside this script)"""
import json,sys,os,math,time,datetime,urllib.request
B='https://api.elections.kalshi.com/trade-api/v2/'
NEED=(40,80)
def get(u):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(B+u,headers={'User-Agent':'oicheapskip'}),timeout=20))
    except Exception: return None
def res(t):
    r=get('markets/'+t); r=(r or {}).get('market',{}).get('result')
    return r if r in('yes','no') else None
def num(x):
    try: return float(x)
    except Exception: return None
def side_from_candles(t,atms):
    s=t.split('-')[0]; e=int(atms/1000); 
    r=get('series/%s/markets/%s/candlesticks?start_ts=%d&end_ts=%d&period_interval=1'%(s,t,e-180,e+60))
    for c in reversed((r or {}).get('candlesticks',[])):
        vals=[]
        for k in('yes_bid','yes_ask'):
            v=c.get(k) or {}
            x=num(v.get('close_dollars'))
            if x is None:
                x=num(v.get('close'))
                if x is not None and x>1: x/=100
            vals.append(x)
        if None not in vals: return 'yes' if (vals[0]+vals[1])/2<0.5 else 'no'
    return None
def fee(c,p): return math.ceil(round(7*c*p*(1-p),6))/100
def book(r,p,c):
    return c*(1-p)-fee(c,p) if r else -(c*p+fee(c,p))
here=os.path.dirname(os.path.abspath(sys.argv[0]))
rp=sys.argv[1] if len(sys.argv)>1 else 'dash_report.json'
ts=sys.argv[2] if len(sys.argv)>2 else None
if not ts and os.path.exists(os.path.join(here,'DEPLOY_TS')): ts=open(os.path.join(here,'DEPLOY_TS')).read().strip()
if not ts: print('NOT DEPLOYED / no skip records (no deploy timestamp: DEPLOY_TS absent)'); sys.exit(0)
cut=datetime.datetime.fromisoformat(ts.replace('Z','+00:00')).timestamp()*1000
d=json.load(open(rp))
rows=[r for r in (d.get('skips') or {}).get('rows',[]) if r.get('reason')=='cheap_skipped' and r.get('atMs',0)>=cut]
if not rows: print('NOT DEPLOYED / no skip records (no cheap_skipped since %s)'%ts); sys.exit(0)
G=[];unk=0;pend=0
for r in rows:
    p=num((r.get('detail') or {}).get('price')); sd=r.get('note') or r.get('side') or side_from_candles(r['ticker'],r['atMs'])
    if sd not in('yes','no') or p is None: unk+=1; continue
    rs=res(r['ticker'])
    if rs is None: pend+=1; continue
    G.append((p,rs==sd))
n=len(G);w=sum(1 for _,x in G if x)
n5=sum(book(x,p,5) for p,x in G); n12=sum(book(x,p,12) for p,x in G)
print('CHEAPSKIP since %s (deploy date %s; OICORE streak/kill/ladder inputs change from this day)'%(ts,ts[:10]))
print(' skip records %d | settled+side known %d | unsettled %d | side unknown %d'%(len(rows),n,pend,unk))
print(' wins %d of %d | net at 5 contracts $%.2f | at 12 contracts (information) $%.2f'%(w,n,n5,n12))
if n<NEED[0]: print(' NO READ: %d of %d settled signals needed (read points 40 and 80).'%(n,NEED[0]))
else:
    if n>=NEED[1]: v='PERMANENT SKIP' if w<=3 else ('DROP THE SKIP' if w>=8 else 'no rule at 80: report')
    else: v='PERMANENT SKIP' if w<=1 else ('DROP THE SKIP' if w>=4 else 'EXTEND TO 80 (weak test)')
    print(' VERDICT:',v)
