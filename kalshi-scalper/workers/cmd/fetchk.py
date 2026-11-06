import sys,json,time,gzip,csv
sys.path.insert(0,'/home/user/shwoopnet/kalshi-scalper/src/scalper')
import perpdata as P
CUT=P.to_ts("2026-11-04T00:00:00Z"); START=P.to_ts("2026-10-29T00:00:00Z")
out={}
for tk in ["KXGOLDPERP","KXSILVERPERP","KXCOPPERPERP","KXWTIFUTURE","KXUS500PERP","KXUSTECH100PERP"]:
    rows={}
    g=START
    while g<CUT:
        c=P._get("/margin/markets/%s/candlesticks"%tk,{"period_interval":1,"start_ts":g,"end_ts":min(g+3*86400,CUT)})["candlesticks"]
        for x in c:
            if x["end_period_ts"]>CUT: continue
            r=P.row_from(x,CUT); r.pop("_crossed",None); rows[r["ts"]]=r
        g+=3*86400; time.sleep(0.5)
    P.write_csv(sys.argv[1]+"/%s_1m.csv.gz"%tk,[rows[k] for k in sorted(rows)],P.FIELDS)
    print(tk,len(rows),min(rows),max(rows))
