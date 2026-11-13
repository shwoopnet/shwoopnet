#!/usr/bin/env python3
"""R6 final rerun. Usage (from anywhere): python3 r6_final.py [--live]
Default = dry: no network, only the files already local.
--live  = git fetch origin quote-data (read only), copy new book/trades files,
          and pull missing candles (public Kalshi endpoint, 1 request per 0.5 s).
Rules of cap.py, w10.py, w12.py are NOT changed: they are executed as they are.
The gold depth-sum is rebuilt here (no script of it was kept) with the same
definition as the first run: in-band gold windows at close-360 (ask or 1-bid in
0.88..0.97 from the candle), nearest book poll within 6 s, buy walks the 5 levels
of the opposite bids (price = 1 - bid), extra cents = average walk price minus touch."""
import os,sys,subprocess,json,gzip,csv,glob,time,datetime as D,statistics,io,contextlib
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
LIVE='--live' in sys.argv
RETRY='--retry-only' in sys.argv  # W97: only re-pull rows stored ok:false
REPO='/home/user/shwoopnet'
def sh(*a): return subprocess.run(a,capture_output=True,text=True)
os.makedirs('r6',exist_ok=True); os.makedirs('r6t',exist_ok=True)

# ---- (1) sync files ----
if LIVE and not RETRY:
    MIR=os.path.join(HERE,'mirror.git')   # scratchpad-only repo; the project's .git is never written
    if not os.path.exists(MIR):
        sh('git','init','--bare','-q',MIR)
        open(MIR+'/objects/info/alternates','w').write(REPO+'/.git/objects\n')  # read-only reuse
    r=sh('git','--git-dir',MIR,'fetch','-q','https://github.com/shwoopnet/shwoopnet','+quote-data:refs/heads/quote-data'); print('fetch rc',r.returncode,r.stderr[-200:])
    ls=sh('git','--git-dir',MIR,'ls-tree','-r','--name-only','quote-data').stdout.split('\n')
    new=0
    for p in ls:
        if not p.startswith('book15r6/'): continue
        if p.endswith('/book.csv.gz'): dst='r6/'+p.replace('/','_')
        elif p.endswith('/trades.csv.gz'):
            d,t=p.split('/')[1:3]; dst='r6t/%s_%s_.gz'%(d,t)
        else: continue
        if os.path.exists(dst): continue
        b=subprocess.run(['git','--git-dir',MIR,'show','quote-data:'+p],capture_output=True).stdout
        if b: open(dst,'wb').write(b); new+=1
    print('new files copied',new)
else:
    print('DRY mode: no fetch, no candle pull (use --live)')
nb=len(glob.glob('r6/*book.csv.gz')); nt=len(glob.glob('r6t/*.gz'))
print('local book files',nb,'trade files',nt)

# ---- candle top-up ----
B="https://api.elections.kalshi.com/trade-api/v2"
def get(u):
    wait=2
    for _ in range(6):
        r=subprocess.run(['curl','-sS','-m','40','-w','\n%{http_code}',u],capture_output=True,text=True)
        if '\n' in r.stdout:
            b,c=r.stdout.rsplit('\n',1);c=int(c) if c.isdigit() else 0
            if c==200:
                try: return json.loads(b)
                except: pass
            if not(c==429 or c==0 or c>=500): return None
        time.sleep(wait);wait=min(wait*2,60)
    return None
FILES={'KXBTC15M':'oi/btc.jsonl','KXGOLD15M':'oi/gold.jsonl','KXDOGE15M':'oi/doge.jsonl'}
def book_markets():
    m={}
    for f in sorted(glob.glob('r6/*book.csv.gz')):
        for r in csv.DictReader(gzip.open(f,'rt')):
            if r['series'] in FILES: m[r['ticker']]=(r['series'],r['close_time'])
    return m
def have(fn):
    s=set()
    if os.path.exists(fn):
        for l in open(fn):
            try:
                j=json.loads(l)
                if j.get('ok') is False: continue   # W97: failed pull is NOT done
                s.add(j['t'])
            except: pass
    return s
def topup():
    bm=book_markets(); now=time.time(); tot=0
    for ser,fn in FILES.items():
        h=have(fn)
        miss=[(c,t) for t,(s,c) in bm.items() if s==ser and t not in h]
        miss=[(int(D.datetime.fromisoformat(c.replace('Z','+00:00')).timestamp()),t) for c,t in miss]
        miss=sorted(x for x in miss if x[0]<now-600)   # settled by now
        print(ser,'recorded markets without candles:',len(miss),'live pull' if LIVE else '(dry, not pulled)')
        if not LIVE: continue
        bad=set()
        if RETRY:
            for l in open(fn):
                try:
                    j=json.loads(l)
                    if j.get('ok') is False: bad.add(j['t'])
                except: pass
            miss=[x for x in miss if x[1] in bad]; print(ser,'retry-only:',len(miss))
            # drop stale ok:false rows so a retry never leaves a duplicate
            keep=[l for l in open(fn) if not (lambda j:j.get('ok') is False)(json.loads(l))]
            open(fn,'w').writelines(keep)
        f=open(fn,'a')
        for cs,t in miss:
            m=get(B+"/markets/"+t); time.sleep(0.5)
            res=(m or {}).get('market',{}).get('result')
            if res not in('yes','no'): continue   # not settled yet
            d=get(B+"/series/%s/markets/%s/candlesticks?start_ts=%d&end_ts=%d&period_interval=1"%(ser,t,cs-660,cs)); time.sleep(0.5)
            if d is None: print('FAILED',t); continue   # W97: never store a failed request
            cd=d.get('candlesticks',[])
            rows=[]
            for c in (cd or []):
                try: rows.append({'e':int(c['end_period_ts']),'oi':c.get('open_interest_fp'),'ac':c['yes_ask'].get('close_dollars'),'bc':c['yes_bid'].get('close_dollars')})
                except Exception: pass
            f.write(json.dumps({'t':t,'c':cs,'r':res,'k':rows,'ok':True})+"\n");f.flush();tot+=1
        f.close()
    if LIVE: print('candle rows added',tot)
topup()
if RETRY: sys.exit(0)

def run(name):
    print('\n'+'='*20,name,'='*20,flush=True)
    g={'__name__':'__main__'}
    exec(compile(open(name).read(),name,'exec'),g)

# ---- coverage summary ----
def days(fn):
    ds=set()
    for l in open(fn):
        try: ds.add(D.datetime.fromtimestamp(json.loads(l)['c'],D.UTC).strftime('%m-%d'))
        except: pass
    return (min(ds),max(ds)) if ds else None
bm=book_markets(); bd=sorted({c[:10] for s,c in bm.values()})
print('book days',bd[0] if bd else None,'to',bd[-1] if bd else None,'(%d days)'%len(bd))
for s,fn in FILES.items(): print('candle file',fn,days(fn),'rows',len(have(fn)))

# ---- (2a) gold depth-sum ----
print('\n'+'='*20,'GOLD DEPTH SUM','='*20)
cand={}
for l in open('oi/gold.jsonl'):
    try: r=json.loads(l)
    except: continue
    cand[r['t']]=r
polls={}
for f in sorted(glob.glob('r6/*book.csv.gz')):
    for r in csv.DictReader(gzip.open(f,'rt')):
        if r['series']=='KXGOLD15M': polls.setdefault(r['ticker'],[]).append((int(r['t_recv_ms'])/1000,r))
fl=lambda x:float(x) if x else None
rec=[];inband=0;nopoll=0
for t,pl in polls.items():
    r=cand.get(t)
    if not r or not r.get('ok'): continue
    c=r['c'];k={x['e']:x for x in r['k']};e=k.get(c-360)
    if not e: continue
    try: ask=float(e['ac']);bid=float(e['bc'])
    except: continue
    if .88-1e-9<=ask<=.97+1e-9: side='yes'
    elif .88-1e-9<=1-bid<=.97+1e-9: side='no'
    else: continue
    inband+=1
    tt,b=min(pl,key=lambda x:abs(x[0]-(c-360)))
    if abs(tt-(c-360))>6: nopoll+=1;continue
    opp='no' if side=='yes' else 'yes'   # buying yes lifts the asks = 1 - no bids
    lv=[(1-fl(b[f'{opp}_bid_px_{i}']),fl(b[f'{opp}_bid_sz_{i}'])) for i in range(1,6) if b[f'{opp}_bid_px_{i}']]
    if lv: rec.append(lv)
print('gold windows with book recorded and candles',len(polls),'in band at close-360',inband,'no poll within 6 s',nopoll,'WINDOWS USED',len(rec))
def walk(lv,n):
    left=n;cost=0
    for p,s in lv:
        q=min(left,s);cost+=q*p;left-=q
        if left<=0: break
    return None if left>0 else 100*(cost/n-lv[0][0])
def pc(xs,p): xs=sorted(xs);return xs[int(p*(len(xs)-1))]
print('order | n filled in 5 levels | extra cents above touch: median p90 max | windows deeper than 5 levels')
for n in(15,30,60,125,250):
    xs=[x for lv in rec if (x:=walk(lv,n)) is not None]
    if xs: print('%4d | %4d | %.2f %.2f %.2f | %d'%(n,len(xs),statistics.median(xs),pc(xs,.9),max(xs),len(rec)-len(xs)))
    else: print(n,'no windows')

# ---- (2b) cap.py, (2c) w10.py, (2d) w12.py ----
run('cap.py')
run('w10.py')
print('\nw12 overlap: windows with tape per series, with candles')
tick=set()
for f in glob.glob('r6t/*.gz'):
    for r in csv.DictReader(gzip.open(f,'rt')): tick.add(r['ticker'])
for ser,fn in(('KXGOLD15M','oi/gold.jsonl'),('KXDOGE15M','oi/doge.jsonl')):
    h=have(fn); tt={t for t in tick if t.startswith(ser)}
    print(ser,'tape tickers',len(tt),'with candles',len(tt&h),'missing',len(tt-h))
run('w12.py')
