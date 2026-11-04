import json,time,os,re,urllib.request
UA="EarnPr1ResearchBot research-notes (descriptive; no contact)"
D='/home/user/.cache/earnpr1/'
def get(u):
    for i in range(5):
        try:
            rq=urllib.request.Request(u,headers={'User-Agent':UA,'Accept-Encoding':'identity'})
            with urllib.request.urlopen(rq,timeout=30) as r: b=r.read()
            time.sleep(0.25); return b
        except Exception as e:
            time.sleep(2*(i+1))
    return None
s=json.load(open('/tmp/claude-0/-home-user-shwoopnet/026f6e8f-6dc4-5e3b-8c3b-e0089b12fb94/scratchpad/series.json'))
t=json.load(open('/tmp/s.json'))
bt={}
for v in t.values(): bt.setdefault(v['ticker'].upper(),v)
manual={'ADOBE':796343,'DEER':315189,'EA':712515,'DOLLARGENERAL':29534,'VSCO':1856437,'COINBASE':1679788,'DOCUSIGN':1261333,'LUCID':1811210,'SYUM':1041061}
bad={'ACA'}
cik={}
for x in s:
    suf=x['ticker'][len('KXEARNINGSMENTION'):]
    if suf in bad: continue
    if suf in manual: cik[x['ticker']]=manual[suf]
    elif suf in bt: cik[x['ticker']]=bt[suf]['cik_str']
json.dump(cik,open(D+'cikmap.json','w'))
out=json.load(open(D+'filings.json')) if os.path.exists(D+'filings.json') else {}
CUT='2026-10-03T16:00:00'
for sr,c in sorted(cik.items()):
    if str(c) in out: continue
    b=get('https://data.sec.gov/submissions/CIK%010d.json'%c)
    if not b: continue
    d=json.loads(b); rows=[]
    def take(r):
        for i in range(len(r['form'])):
            if r['form'][i]=='8-K' and '2.02' in (r['items'][i] or '') and r['acceptanceDateTime'][i]<CUT:
                rows.append((r['accessionNumber'][i],r['acceptanceDateTime'][i],r['primaryDocument'][i]))
    take(d['filings']['recent'])
    for f in d['filings'].get('files',[]):
        if f.get('filingTo','9999')>='2025-01-01':
            bb=get('https://data.sec.gov/submissions/'+f['name'])
            if bb: take(json.loads(bb))
    out[str(c)]={'name':d['name'],'f':rows}
    json.dump(out,open(D+'filings.json','w'))
print('done',len(out))
