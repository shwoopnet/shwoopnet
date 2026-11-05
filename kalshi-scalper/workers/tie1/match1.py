import json,glob,re,unicodedata,datetime,os
evs=json.load(open('cache/events.json'))
def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return set(t for t in re.findall(r'[a-z]+',s) if len(t)>=3 and t not in('fc','sk','ac','fk','the','club','afc','cfc'))
games=[]
for f in glob.glob('cache/espn/*.json'):
    try: d=json.load(open(f))
    except: continue
    for e in d.get('events',[]):
        c=e['competitions'][0]
        if e['status']['type']['name'] not in('STATUS_FULL_TIME','STATUS_FINAL_AET','STATUS_FINAL_PEN'): continue
        h=[x for x in c['competitors'] if x['homeAway']=='home'][0];a=[x for x in c['competitors'] if x['homeAway']=='away'][0]
        games.append(dict(id=e['id'],t=e['date'],h=h['team']['displayName'],a=a['team']['displayName'],hs=int(h['score']),as_=int(a['score']),st=e['status']['type']['name'],dd=c.get('details')))
seen={};
for g in games: seen[g['id']]=g
games=list(seen.values());print(len(games))
def tm(a,b): return bool(a&b) and len(a&b)/min(len(a),len(b))>=0.5
out=[];drop={}
for e in evs:
    et=e['event_ticker']
    p=f"cache/m_{et}.json"
    if not os.path.exists(p): drop['nomarket']=drop.get('nomarket',0)+1;continue
    ms=json.load(open(p)).get('markets',[])
    if len(ms)!=2: drop['markets!=2']=drop.get('markets!=2',0)+1;continue
    teams=[(m['ticker'],m['yes_sub_title'].replace(' advances','')) for m in ms]
    occ=ms[0].get('occurrence_datetime') or ms[0].get('expected_expiration_time') or ms[0]['close_time']
    od=datetime.datetime.fromisoformat(occ.replace('Z','+00:00'))
    n0,n1=norm(teams[0][1]),norm(teams[1][1])
    cand=[]
    for g in games:
        gt=datetime.datetime.fromisoformat(g['t'].replace('Z','+00:00'))
        if not(od-datetime.timedelta(days=21)<=gt<=od+datetime.timedelta(hours=12)): continue
        gh,ga=norm(g['h']),norm(g['a'])
        if (tm(n0,gh) and tm(n1,ga)) or (tm(n0,ga) and tm(n1,gh)): cand.append((gt,g))
    cand.sort(key=lambda x:x[0])
    if len(cand)!=2: drop[f'legs={len(cand)}']=drop.get(f'legs={len(cand)}',0)+1;continue
    (t1,g1),(t2,g2)=cand
    if t2-t1<datetime.timedelta(days=2): drop['legs too close']=drop.get('legs too close',0)+1;continue
    # goals per team in leg 1
    def goals(g,n):
        return g['hs'] if tm(n,norm(g['h'])) else g['as_']
    res={}
    for tk,nm in teams: res[tk]=dict(name=nm,leg1_for=goals(g1,norm(nm)),leg1_against=goals(g1,norm([x for x in teams if x[0]!=tk][0][1])),home2=tm(norm(nm),norm(g2['h'])))
    out.append(dict(event=et,kick2=g2['t'],kick1=g1['t'],status2=g2['st'],teams=res,result={m['ticker']:m['result'] for m in ms},occ=occ))
print(len(out),drop)
json.dump(out,open('cache/ties.json','w'))
