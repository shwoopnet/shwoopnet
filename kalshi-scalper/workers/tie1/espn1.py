import json,re,datetime,os,time,urllib.request
evs=json.load(open('cache/events.json'))
days=set()
for e in evs:
    m=re.search(r'-(\d\d)([A-Z]{3})(\d\d)',e['event_ticker'])
    d=datetime.datetime.strptime(m.group(1)+m.group(2)+m.group(3),'%y%b%d').date()
    for k in range(-22,2): days.add(d+datetime.timedelta(days=k))
days=sorted(days);print(len(days),flush=True)
os.makedirs('cache/espn',exist_ok=True)
for d in days:
    for slug in ('uefa.europa.conf_qual','uefa.europa.conf'):
        p=f"cache/espn/{slug}_{d:%Y%m%d}.json"
        if os.path.exists(p): continue
        for i in range(4):
            try:
                t=urllib.request.urlopen(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={d:%Y%m%d}",timeout=25).read()
                open(p,'wb').write(t);break
            except Exception as ex: time.sleep(2)
print('espn done',flush=True)
