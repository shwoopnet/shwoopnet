#!/usr/bin/env python3
"""Builds SIBHIT_CANDLES.json from the stage A list (time fields only). One batched request per game (two if over 60 open rungs), window T - 180 s to T.
Usage: python3 -I build_sibhit_candles.py <root holding pull/KXNBAPTS_LISTS_A> <out.json>"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sibhit_lib as L

PER = 60
root, outp = sys.argv[1], sys.argv[2]
g = L.games(L.list_rows(root))
reqs, allow = [], []
for e in sorted(g):
    op = g[e]["open"]
    for k in range(0, len(op), PER):
        chunk = op[k:k + PER]
        allow += chunk
        reqs.append({"id": "%s_%d" % (e.replace("KXNBAPTS-", "g"), k // PER), "path": "/markets/candlesticks",
                     "params": {"market_tickers": ",".join(chunk), "start_ts": g[e]["T"] - L.LOOKBACK_S, "end_ts": g[e]["T"], "period_interval": 1}})
job = {"job_id": "SIBHIT_CANDLES", "owner": "MAIN", "registration": "kalshi-scalper/workers/idea_desk_c/allkalshi/sibhit/SIBHIT_CARD.md",
       "purpose": "SIBHIT quick first read (Idea Desk C): 1 minute candles of the KXNBAPTS rungs still open at T = occurrence - 60 min, development games only, a 3 minute window per game.",
       "heldout": "none read: development games only, closes 2026-10-21 to before 2026-11-06. Never requested: PROPUNDER's reserve (closes 2026-11-06 to before 2026-11-13) and SIBHIT's held-out (closes 2026-11-13 to before 2026-12-04, read once on the Head of R&D's go).",
       "allowed_endpoints": [{"name": "markets_candlesticks_batch", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
       "series_allowlist": ["KXNBAPTS"], "ticker_allowlist": sorted(set(allow)), "max_requests": len(reqs),
       "notes": "Built by build_sibhit_candles.py from KXNBAPTS_LISTS_A (time fields only). %d games, %d requests, %d tickers, window 3 minutes each (at most 180 ticker-minutes a request, far under 10,000)." % (len(g), len(reqs), len(set(allow))),
       "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
       "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
       "requests": reqs}
open(outp, "w").write(json.dumps(job, indent=1) + "\n")
print(len(g), "games", len(reqs), "requests", len(set(allow)), "tickers", {a: sum(1 for x in g.values() if x["arm"] == a) for a in ("HIGH", "LOW")})
