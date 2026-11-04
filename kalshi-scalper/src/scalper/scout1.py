"""SCOUT1: census (listings and close times only; no candle, no result field read) and, once a rule is registered, the scorer.
Usage: python -m scalper.scout1 census OUT.json SERIES...   (counts markets/events/close dates settled before the frozen cut, per month, plus median volume)
The census never reads `result`, `settlement_value`, prices or any outcome."""
from __future__ import annotations
import collections, json, statistics as st, sys, time, urllib.parse, urllib.request

BASE = "https://api.elections.kalshi.com/trade-api/v2"
CUT = "2026-10-03T16:00:00Z"
UA = "shwoopnet-research-scout1/1.0 (listings census; polite)"
import os
MAX_PAGES = int(os.environ.get("SCOUT1_MAXP", "6"))


def get(path, **q):
    url = BASE + path + "?" + urllib.parse.urlencode(q)
    for a in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as e:
            time.sleep(min(60, 2 ** a * (3 if "429" in str(e) else 1)))
    return None


def census_series(s):
    mon = collections.Counter(); ev = collections.defaultdict(set); days = set(); vols = []
    tot = 0; capped = False; first = last = None
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cursor = None; pages = 0
        while True:
            q = dict(series_ticker=s, limit=1000, **extra)
            if cursor: q["cursor"] = cursor
            d = get(path, **q); time.sleep(0.5)
            if not d: break
            pages += 1
            for m in d.get("markets", []):
                ct = m.get("close_time") or ""
                tot += 1
                if ct and ct < CUT:
                    mon[ct[:7]] += 1; ev[ct[:7]].add(m.get("event_ticker")); days.add(ct[:10])
                    try: vols.append(float(m.get("volume_fp") or m.get("volume") or 0))
                    except Exception: pass
                    first = ct if first is None or ct < first else first
                    last = ct if last is None or ct > last else last
            cursor = d.get("cursor")
            if not cursor: break
            if pages >= MAX_PAGES: capped = True; break
    nm = sum(mon.values()); ne = sum(len(v) for v in ev.values())
    return dict(markets=nm, events=ne, close_days=len(days), first=first, last=last, capped=capped,
                median_volume=(st.median(vols) if vols else 0), by_month={k: [mon[k], len(ev[k])] for k in sorted(mon)})


def main():
    out, series = sys.argv[2], sys.argv[3:]
    res = {}
    for s in series:
        res[s] = census_series(s)
        r = res[s]
        print(s, r["markets"], r["events"], r["close_days"], r["first"], r["last"], "CAPPED" if r["capped"] else "", flush=True)
        json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__" and sys.argv[1] == "census":
    main()
