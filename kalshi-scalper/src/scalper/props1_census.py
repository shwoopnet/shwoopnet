"""PROPS1 census: listings and close times only. No candles, no outcomes read into any statistic.
Writes a per-series, per-month count of settled markets/events before the frozen cut."""
from __future__ import annotations
import json, sys, time, collections, urllib.request, urllib.parse
BASE = "https://api.elections.kalshi.com/trade-api/v2"
CUT = "2026-10-03T16:00:00Z"
SERIES = ["KXNBAPTS","KXNBAREB","KXNBAAST","KXNBA3PT","KXNBASTL","KXNBABLK","KXWNBAPTS","KXWNBAREB","KXWNBAAST","KXWNBA3PT",
 "KXNFLPASSYDS","KXNFLRECYDS","KXNFLRSHYDS","KXNFLREC","KXNFLANYTD","KXNFLPASSTDS","KXNFLPASSCOMP","KXNFLPASSATT","KXNFLRRYDS","KXNFL2TD","KXNFLSACK",
 "KXMLBKS","KXMLBHR","KXMLBTB","KXMLBHRR","KXNHLGOAL","KXNHLAST","KXNHLPTS","KXNHLSAVES","KXNHLANYGOAL",
 "KXNBATEAMTOTAL","KXNFLTEAMTOTAL","KXMLBTEAMTOTAL","KXNCAAFTEAMTOTAL","KXWNBATEAMTOTAL","KXNCAAMBTEAMTOTAL","KXNHLTEAMTOTAL"]
def get(path, **q):
    url = BASE + path + "?" + urllib.parse.urlencode(q)
    for a in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "shwoopnet-research-props1/1.0 (listings census)"})
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as e:
            time.sleep(2 ** a)
    return None
HIST = len(sys.argv) > 2 and sys.argv[2] == "hist"
def main(out):
    res = {}
    for s in SERIES:
        n = collections.Counter(); ev = collections.defaultdict(set); first = last = None; cursor = None; tot = 0; stat = collections.Counter()
        while True:
            q = dict(series_ticker=s, limit=1000) if HIST else dict(series_ticker=s, limit=1000, status="settled")
            if cursor: q["cursor"] = cursor
            d = get("/historical/markets" if HIST else "/markets", **q); time.sleep(0.6)
            if not d: break
            for m in d.get("markets", []):
                ct = m.get("close_time") or ""
                tot += 1
                if ct < CUT:
                    n[ct[:7]] += 1; ev[ct[:7]].add(m["event_ticker"])
            cursor = d.get("cursor")
            if not cursor: break
        res[s] = dict(total_settled=tot, markets_by_month=dict(sorted(n.items())), events_by_month={k: len(v) for k, v in sorted(ev.items())})
        print(s, tot, sum(n.values()), sum(len(v) for v in ev.values()), flush=True)
    json.dump(res, open(out, "w"), indent=1)
if __name__ == "__main__": main(sys.argv[1])
