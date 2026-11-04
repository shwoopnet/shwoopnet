import json,os,re,sys,time,statistics,collections,urllib.request
sys.path.insert(0,'/home/user/shwoopnet/kalshi-scalper/src')
from scalper import earnpr1 as e
D='/home/user/.cache/earnpr1/'
UA="EarnPr1ResearchBot research-notes (descriptive; no contact)"
def get(u):
    for i in range(5):
        try:
            rq=urllib.request.Request(u,headers={'User-Agent':UA,'Accept-Encoding':'identity'})
            with urllib.request.urlopen(rq,timeout=30) as r: b=r.read()
            time.sleep(0.25); return b
        except Exception as ex:
            time.sleep(2*(i+1))
    return None
ev={}
for f in ('events.json','events2.json'):
    if os.path.exists(D+f): ev.update(json.load(open(D+f)))
cik=json.load(open(D+'cikmap.json')); fil=json.load(open(D+'filings.json'))
txtp=D+'texts.json'; texts=json.load(open(txtp)) if os.path.exists(txtp) else {}
rows=[]
for en,mk in sorted(ev.items()):
    if not mk: rows.append(dict(ev=en,why='no_listing')); continue
    ser=en.rsplit('-',1)[0]; occs=[m['occ'] for m in mk if m['occ']]
    mc=min(e.ts(m['close']) for m in mk); occ0=e.ts(max(set(occs),key=occs.count)) if occs else None; occ,kind=e.call_time(occ0,mc)
    r=dict(ev=en,ser=ser,occ=occ,kind=kind,n=len(mk),close=min(m['close'] for m in mk))
    c=cik.get(ser)
    if not c: r['why']='no_cik'; rows.append(r); continue
    f=fil.get(str(c),{}).get('f',[])
    m=e.match_filing(occ,[(a,t) for a,t,_ in f])
    if not m: r['why']='no_8k'; rows.append(r); continue
    r['acc']=m[0]; r['acc_ts']=m[1]; r['lead_min']=(occ-m[1])/60; r['cik']=c
    r['doc']=[x[2] for x in f if x[0]==m[0]][0]
    rows.append(r)
# Ex-99.1 text
need=[r for r in rows if 'acc' in r and r['acc'] not in texts]
print('texts to fetch',len(need),flush=True)
for r in need:
    nd=r['acc'].replace('-','')
    idx=get(f"https://www.sec.gov/Archives/edgar/data/{r['cik']}/{nd}/{r['acc']}-index.htm")
    name=None
    if idx:
        h=idx.decode('utf8','ignore')
        for row in re.findall(r'(?is)<tr.*?</tr>',h):
            if re.search(r'EX-99\.1\b',row) :
                mm=re.search(r'href="([^"]+)"',row)
                if mm: name=mm.group(1); break
    if name:
        if not name.startswith('/'): name=f"/Archives/edgar/data/{r['cik']}/{nd}/"+name
        name=re.sub(r'^/ix\?doc=','',name)
        b=get('https://www.sec.gov'+name)
        texts[r['acc']]=e.clean_text(b.decode('utf8','ignore')) if b else None
    else: texts[r['acc']]=None
    if len(texts)%20==0: json.dump(texts,open(txtp,'w'))
json.dump(texts,open(txtp,'w'))
for r in rows:
    if 'acc' in r: r['has_text']=bool(texts.get(r['acc']))
json.dump(rows,open(D+'census_rows.json','w'))
n=len(rows); mt=[r for r in rows if 'acc' in r]
print('events',n,'by why',collections.Counter(r.get('why','matched') for r in rows))
ld=[r['lead_min'] for r in mt]
print('lead median min',statistics.median(ld),'p25',statistics.quantiles(ld,n=4)[0],'p75',statistics.quantiles(ld,n=4)[2],'n',len(ld))
print('lead<20m share',sum(1 for x in ld if x<20)/len(ld),' <10m',sum(1 for x in ld if x<10)/len(ld),' >=60m',sum(1 for x in ld if x>=60)/len(ld), 'negative', sum(1 for x in ld if x<0)/len(ld))
print('has Ex-99.1 text',sum(r['has_text'] for r in mt),'of',len(mt))
json.dump(rows,open(D+'census_rows.json','w'))
