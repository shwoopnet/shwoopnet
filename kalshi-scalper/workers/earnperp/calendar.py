#!/usr/bin/env python3
"""EARNPERP calendar builder: Nasdaq earnings calendar JSON (keyless) + SEC EDGAR submissions (8-K Item 2.02 acceptance times).
Research only, public keyless GETs. EDGAR User-Agent is descriptive and carries no personal contact."""
import json,csv,sys,time,datetime as dt,collections,re,urllib.request,urllib.parse
from zoneinfo import ZoneInfo
NY=ZoneInfo('America/New_York'); EDGAR={"User-Agent":"Claude Code research (anthropic.com)"}
def get(u,h):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=40))
def bucket(acc):
    d=dt.datetime.fromisoformat(acc.replace('Z','+00:00')).astimezone(NY); h=d.hour+d.minute/60
    return 'pre' if h<9.5 else ('intraday' if h<16 else 'post'),d
def main(outdir,asof):
    ms=get('https://external-api.kalshi.com/trade-api/v2/margin/markets',EDGAR)['markets']
    eq={m['title']:m for m in ms if m['asset_class']=='Equities' and m['status']=='active'}
    U="AAPL XOM QQQ SPY GOOGL MU NFLX NVDA TSLA KO MSFT COST AMZN VZ CVX PG PLTR META SPCX".split()  # + US500, US Tech 100 (no earnings)
    cik={k:int(v[0]) for k,v in json.load(open(outdir+'/cik.json')).items()}
    cik.update({'COST':909832,'MA':1141391,'V':1403161,'BRK.B':1067983})
    nq=json.load(open(outdir+'/nasdaq_cal.json'))
    nqmap=collections.defaultdict(list)
    for d,rows in nq.items():
        for r in rows or []:
            nqmap[r['symbol'].replace('/','.')].append((d,r['time'].replace('time-','')))
    e202=collections.defaultdict(list)
    for t,a,_ in json.load(open(outdir+'/e202.json')): e202[t].append(a)
    out=[]
    for t in sorted(eq):
        hist=sorted(e202.get(t,[]))
        recent=[a for a in hist if a>='2025-09-01']
        bs=[bucket(a)[0] for a in recent]
        mode=collections.Counter(bs).most_common(1)[0][0] if bs else ''
        last=bucket(hist[-1])[1].strftime('%Y-%m-%d %H:%M ET') if hist else ''
        yago=[bucket(a)[1] for a in hist if '2025-10-25'<=a[:10]<='2026-03-01']
        nxt=[(d,s) for d,s in nqmap.get(t,[]) if d>=asof]
        out.append(dict(ticker=t,perp=eq[t]['ticker'],in_U=int(t in U),has_8K=int(t in cik),
            nasdaq_next=';'.join(d+' '+s for d,s in nxt),usual_session=mode,
            last_2_02=last,projected_from_last_year=(yago[0].strftime('%Y-%m-%d') if not nxt and yago else '')))
    with open(outdir+'/earnings_calendar.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print(len(out))
main(sys.argv[1],sys.argv[2])
