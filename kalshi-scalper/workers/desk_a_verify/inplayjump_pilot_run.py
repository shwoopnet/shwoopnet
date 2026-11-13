import sys, json
sys.path.insert(0, "/home/user/shwoopnet/kalshi-scalper/workers/desk_a_verify"); sys.path.insert(0, sys.argv[1] + "/sk")
import inplayjump as J, scorekit
S = json.load(open(sys.argv[1] + "/SERIES.json")); K = S["constants"]
mk = scorekit.markets([sys.argv[1] + "/INPLAYJUMP_LISTS"]); cd = scorekit.candles([sys.argv[1] + "/pilot_min"])
print("markets in lists", len(mk), "tickers with pilot candles", len(cd))
for fam in S["families_ranked_by_events"]:
    b = (scorekit.iso(fam["development"]["closes_from"]), scorekit.iso(fam["development"]["closes_before"]))
    sub = {t: m for t, m in mk.items() if t in cd or any(t.rsplit("-",1)[0] == x.rsplit("-",1)[0] for x in cd)}
    sub = {t: m for t, m in sub.items() if m["series"] in fam["series"]}
    if not sub: print(fam["family"], "no pilot tickers"); continue
    for L in J.pilot(fam, K, sub, {t: v for t, v in cd.items() if t in sub}, b): print(L)
