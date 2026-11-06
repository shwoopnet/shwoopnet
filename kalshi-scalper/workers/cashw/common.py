import json,glob,gzip,csv,io,subprocess,math,datetime as dt
from zoneinfo import ZoneInfo
ET=ZoneInfo("America/New_York"); UTC=dt.timezone.utc
import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..",".."))
PERPS={"KXUS500PERP":"SPY","KXUSTECH100PERP":"QQQ"}
FUT={"KXUS500PERP":"ES=F","KXUSTECH100PERP":"NQ=F"}
IDX={"KXUS500PERP":"^GSPC","KXUSTECH100PERP":"^NDX"}
def f(x):
    try:
        v=float(x); return v if 0<v<1e9 else None
    except: return None
def perp(tk,max_et_date):
    """quotes keyed by candle END ts; only candles whose ET date <= max_et_date are returned (rows later are never kept)."""
    out={}
    for fn in sorted(glob.glob(f"{ROOT}/data/perpgen/raw/{tk}/m1_*.json")):
        for c in json.load(open(fn)):
            t=c["end_period_ts"]
            if dt.datetime.fromtimestamp(t,ET).date()>max_et_date: continue
            b=f((c.get("bid") or {}).get("close")); a=f((c.get("ask") or {}).get("close"))
            if b and a and a>=b and a<=2*b: out[t]=(b,a)
    return out
def cash(max_et_date):
    d=subprocess.run(["git","-C",ROOT,"show","origin/perp-data:cash1m/2026-11-06.csv.gz"],capture_output=True).stdout
    out={}
    for r in csv.DictReader(io.StringIO(gzip.decompress(d).decode())):
        s=int(r["ts_unix"])
        if dt.datetime.fromtimestamp(s,ET).date()>max_et_date: continue
        out.setdefault(r["symbol"],{})[s]=tuple(float(r[k]) if r[k] else None for k in("open","high","low","close"))
    return out
def ets(date,h,m): return int(dt.datetime(date.year,date.month,date.day,h,m,tzinfo=ET).timestamp())
