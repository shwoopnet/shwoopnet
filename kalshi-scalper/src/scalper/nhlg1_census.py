"""NHLG1 census: KXNHLGOAL listings only (ticker, event, close time, strike, volume). Never reads result or any price.
python -m scalper.nhlg1_census OUT.json   (cache of raw listing fields in ~/.cache/nhlg1/listing.json)"""
from __future__ import annotations
import json, sys, time, statistics as st, collections
from pathlib import Path
from . import api
CUT = "2026-10-03T16:00:00Z"
CACHE = Path("/home/user/.cache/nhlg1") / "listing.json"
KEEP = ("ticker", "event_ticker", "yes_sub_title", "close_time", "open_time", "expected_expiration_time", "volume_fp", "floor_strike")

def listing():
    rows = {}
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cursor = None
        while True:
            q = dict(series_ticker="KXNHLGOAL", limit=1000, **extra)
            if cursor: q["cursor"] = cursor
            d = api._get(path, q); time.sleep(1.0)
            for m in d.get("markets", []):
                rows[m["ticker"]] = {k: m.get(k) for k in KEEP}
            cursor = d.get("cursor")
            print(path, len(rows), flush=True)
            if not cursor: break
    return list(rows.values())

def main(out):
    if CACHE.exists(): rows = json.load(open(CACHE))
    else:
        rows = listing(); json.dump(rows, open(CACHE, "w"))
    pre = [r for r in rows if (r["close_time"] or "") < CUT]
    ev = collections.defaultdict(list)
    for r in pre: ev[r["event_ticker"]].append(r)
    mon = collections.Counter(); evmon = collections.defaultdict(set)
    for r in pre:
        mon[r["close_time"][:7]] += 1; evmon[r["close_time"][:7]].add(r["event_ticker"])
    one = [r for r in pre if r["floor_strike"] == 0.5]
    vols = [float(r["volume_fp"] or 0) for r in pre]
    res = dict(total_listed=len(rows), pre_cut_markets=len(pre), pre_cut_events=len(ev), one_plus_markets=len(one),
               one_plus_with_volume=sum(1 for r in one if float(r["volume_fp"] or 0) > 0),
               median_volume=st.median(vols) if vols else 0,
               first=min((r["close_time"] for r in pre), default=None), last=max((r["close_time"] for r in pre), default=None),
               by_month={k: [mon[k], len(evmon[k])] for k in sorted(mon)},
               post_cut_events=len({r["event_ticker"] for r in rows if (r["close_time"] or "") >= CUT}),
               strikes=dict(collections.Counter(r["floor_strike"] for r in pre)))
    json.dump(res, open(out, "w"), indent=1); print(json.dumps(res, indent=1))
if __name__ == "__main__": main(sys.argv[1])
