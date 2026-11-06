"""STOCKPERP data fetch (keyless GETs, 1.2 s spacing, stops on 429/403). Writes raw JSON/CSV into the directory given as argv[1].
Candles: close bid/ask only are later used. Funding: per ticker history. Markets and schedules: snapshots."""
import sys, os, json, time, csv, gzip, urllib.request, urllib.error
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
from scalper import perpdata as pd
OUT = sys.argv[1]; END = int(time.time())
pd.SLEEP = 1.2
def get(path, params=None):
    time.sleep(1.2)
    return pd._get(path, params)       # raises Blocked on repeated 429 / 401 / 403: we stop, never work around
m = json.load(open(os.path.join(OUT, "markets.json")))["markets"]
eq = sorted(x["ticker"] for x in m if x["asset_class"] in ("Equities", "Indices") and x["status"] == "active")
print(len(eq), "tickers")
fr = {}
for tk in eq:
    fr[tk] = get("/margin/funding_rates/historical", {"ticker": tk, "limit": 200})["funding_rates"]
json.dump(fr, open(os.path.join(OUT, "funding.json"), "w"))
for kind, per, start, step in (("1m", 1, 1793800000, 22 * 3600), ("1h", 60, 1793000000, 20 * 86400)):
    rows = []
    for tk in eq:
        s = start
        while s < END:
            e = min(s + step, END)
            d = get("/margin/markets/%s/candlesticks" % tk, {"period_interval": per, "start_ts": s, "end_ts": e})
            for c in d.get("candlesticks", []):
                r = pd.row_from(c, e); rows.append((tk, r["ts"], r["bid_c"], r["ask_c"], r["ok"]))
            s = e
    with gzip.open(os.path.join(OUT, "candles_%s.csv.gz" % kind), "wt") as f:
        w = csv.writer(f); w.writerow(["ticker", "ts", "bid_c", "ask_c", "ok"]); w.writerows(rows)
    print(kind, len(rows))
