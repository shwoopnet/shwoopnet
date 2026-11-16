#!/usr/bin/env python3
"""Builds LATEWORD_CANDLES.json: one historical single-market candle request per late word, window [D - 180 s, D], 1 minute.
Usage: python3 -I build_lateword_candles.py <root> <out.json>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lateword_lib as L

root, outp = sys.argv[1], sys.argv[2]
if L.truncated(root):
    sys.exit("list truncated: %s" % L.truncated(root))
w = L.late_words(L.list_rows(root))
reqs = [{"id": "h_" + t, "path": "/historical/markets/%s/candlesticks" % t,
         "params": {"start_ts": w[t]["D"] - L.LOOKBACK_S, "end_ts": w[t]["D"], "period_interval": 1}} for t in sorted(w)]
job = {"job_id": "LATEWORD_CANDLES", "owner": "MAIN", "registration": "kalshi-scalper/workers/idea_desk_c/allkalshi/lateword/LATEWORD_CARD.md",
       "purpose": "LATEWORD quick first read (Idea Desk C): 1 minute candles of late-listed Trump mention words at D = occurrence - 60 min, development events only, a 3 minute window each.",
       "heldout": "none read: development events only (own occurrence 2026-04-17 to before 2026-08-06). Never requested: TRUMPTOPIC1's spent held-out (occurrence 2026-08-06 to before 2026-10-03), LATEWORD's held-out (occurrence 2026-10-03 to before 2026-11-05, read once on the Head of R&D's go) and TRUMPTOPIC1's forward window (from 2026-11-05).",
       "allowed_endpoints": [{"name": "hist_market_candlesticks", "method": "GET", "path_pattern": "/historical/markets/(?P<ticker>[A-Z0-9][A-Z0-9._-]{0,63})/candlesticks",
                              "params_allowed": ["start_ts", "end_ts", "period_interval"]}],
       "series_allowlist": list(L.SERIES), "ticker_allowlist": sorted(w), "max_requests": len(reqs),
       "notes": "Built by build_lateword_candles.py from MENTDRIFT_LISTS_A (time fields and word title only). %d late words in %d events, one request each, window end_ts = D so no candle after the decision is fetched." % (len(w), len({x['event'] for x in w.values()})),
       "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
       "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
       "requests": reqs}
open(outp, "w").write(json.dumps(job, indent=1) + "\n")
print(len(w), "late words", len({x['event'] for x in w.values()}), "events", len(reqs), "requests")
