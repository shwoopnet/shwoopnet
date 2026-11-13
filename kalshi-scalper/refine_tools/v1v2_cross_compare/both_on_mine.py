import sys, os, gzip, tempfile, json, csv, math, shutil
sys.path.insert(0,'/home/user/shwoopnet/kalshi-scalper/refine_tools')
import v1_resting_score as S
which=sys.argv[1]   # mine|theirs
base=sys.argv[2]; src=sys.argv[3]   # inv dir, 'mine' or 'theirs' set
HM='/tmp/cmp_hm/kalshi-scalper/workers/history_miner/resting2'
def agg(ver,sig):
    sig=sorted(sig,key=lambda s:s['ct']); n=len(sig)
    f=[s for s in sig if s['filled']]; u=[s for s in sig if not s['filled']]
    def v(frac): return [S.net(s['p_bid'],s['win'],0.0,frac) for s in f]
    p=lambda slip,ss=sig:[S.net(s['p_ask'],s['win'],slip) for s in ss]
    P=lambda x:S.pf(x) if x else None
    half=n//2
    def part(ss):
        ff=[s for s in ss if s['filled']]
        return S.pf([S.net(s['p_bid'],s['win'],0.0,0.25) for s in ff]) if ff else None, S.pf(p(0.01,ss)) if ss else None
    return dict(signals=n,fills=len(f),version_pf_25=P(v(.25)),version_pf_0=P(v(0)),version_pf_100=P(v(1)),parent_pf_p1=P(p(.01)),parent_pf_p0=P(p(0)),
        parent_pf_p1_on_missed=P(p(.01,u)),version_net_sum_25=sum(v(.25)),parent_net_sum_p1=sum(p(.01)),parent_net_sum_p0=sum(p(0)),
        h1=part(sig[:half]),h2=part(sig[half:]))
if which=='mine':
    d=tempfile.mkdtemp(prefix='cm')
    ver=sys.argv[4]
    r=os.path.join(d,'r','2026-11-03','1200'); os.makedirs(r)
    sp=os.path.join(base,ver.lower()+src); 
    for n in ('book','trades','coverage'):
        with open(os.path.join(sp,n+'.csv'),'rb') as a, gzip.open(os.path.join(r,n+'.csv.gz'),'wb') as g: g.write(a.read())
    S.MARKER_DIR=os.path.join(d,'markers'); m=os.path.join(d,'D.txt'); open(m,'w').write('DEPTH1 READ MADE: t\n'); S.DEPTH1_RECORD=m
    sigf=sp+'_signals.csv'
    rc=S.main(['--version',ver,'--block','dev','--book-root',os.path.join(d,'r'),'--signals',sigf,'--out',os.path.join(d,'o')],now='2026-12-06T00:00:00Z')
    book,trades,cover=S.load_run_folders(os.path.join(d,'r')); lo,hi=(S.epoch(x) for x in S.BLOCKS[(ver,'dev')]); sigs=[]
    for row in csv.DictReader(open(sigf)):
        ct=int(row['close_ts'])
        if not lo<=ct<=hi: print(row['ticker'],'outside_block'); continue
        w=S.one_window(ver,row['ticker'],ct,book,trades,cover)
        print(row['ticker'],{k:v for k,v in w.items() if k!='ct'})
        if w['status']=='signal': sigs.append(w)
    print('AGG',json.dumps(agg(ver,sigs),default=str,sort_keys=True))
else:
    sys.path.insert(0,HM); sys.path.insert(0,os.path.dirname(HM))
    import resting2 as R
    ver=sys.argv[4]; d=tempfile.mkdtemp(prefix='ct')
    sp=os.path.join(base,ver.lower()+src); m=os.path.join(d,'D.txt'); open(m,'w').write('DEPTH1 READ MADE: t\n')
    nc=os.path.join('/home/user/shwoopnet/kalshi-scalper/refine_tools','NC15DEPTH1_SCORER_HASH.txt')
    os.makedirs(os.path.join(d,'mk'))
    out=os.path.join(d,'out.json')
    rc=R.run(ver,'dev',sp+'_signals.csv',[sp],depth1_marker=m,marker_dir=os.path.join(d,'mk'),now=1796515200.0,nc15_record=nc,out_path=out)
    print(json.dumps(rc,sort_keys=True,indent=1))
