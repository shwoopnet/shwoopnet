import sys, os, gzip, shutil, tempfile, json
sys.path.insert(0,'/home/user/shwoopnet/kalshi-scalper/refine_tools')
import v1_resting_score as S
HM='/tmp/cmp_hm/kalshi-scalper/workers/history_miner/resting2/inv'
def gz_copy(src,dst):
    os.makedirs(dst,exist_ok=True)
    for n in ('book','trades','coverage'):
        with open(os.path.join(src,n+'.csv'),'rb') as f, gzip.open(os.path.join(dst,n+'.csv.gz'),'wb') as g: g.write(f.read())
def run(ver):
    d=tempfile.mkdtemp(prefix='cmpx')
    gz_copy(os.path.join(HM,ver.lower()+'run'), os.path.join(d,'r','2026-11-01','1200'))
    S.MARKER_DIR=os.path.join(d,'markers')
    m=os.path.join(d,'D.txt'); open(m,'w').write('DEPTH1 READ MADE: test\n'); S.DEPTH1_RECORD=m
    sig=os.path.join(HM,ver.lower()+'run_signals.csv')
    rc=S.main(['--version',ver,'--block','dev','--book-root',os.path.join(d,'r'),'--signals',sig,'--out',os.path.join(d,'out')], now='2026-12-06T00:00:00Z')
    print('exit',rc)
    # per window unrounded
    book,trades,cover=S.load_run_folders(os.path.join(d,'r'))
    import csv
    for r in csv.DictReader(open(sig)):
        w=S.one_window(ver,r['ticker'],int(r['close_ts']),book,trades,cover)
        if w['status']=='signal':
            ask,bid=w['p_ask'],w['p_bid']
            print(r['ticker'],{k:(round(v,9) if isinstance(v,float) else v) for k,v in w.items() if k!='ct'}, 'p1=%.9f p0=%.9f'%(S.net(ask,w['win'],0.01),S.net(ask,w['win'],0.0)), ('v25=%.9f'%S.net(bid,w['win'],0.0,0.25) if w['filled'] else ''))
        else: print(r['ticker'],w['status'])
print('=== V1'); run('V1'); print('=== V2'); run('V2')
