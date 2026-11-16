#!/usr/bin/env python3
"""Builds NBAREB_CANDLES_P1.json and _P2.json from the landed KXNBAREB_LISTS_A (time fields only). Same rules as build_nbaladder_candles.py, series and ids differ.
Usage: python3 -I build_nbareb_candles.py <root> <out prefix>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import nbaladder_reb as R

N = R.N
PER = 60
root, pre = sys.argv[1], sys.argv[2]
if KL.truncated(root, N.LIST_JOB, N.LIST_ID, N.WIN[0]):
    sys.exit("list truncated: not built")
g, drops, listed = N.games(root)
order = sorted(g, key=lambda e: (g[e]["O"], e))
half = (len(order) + 1) // 2
total = 0
for k, evs in enumerate((order[:half], order[half:]), 1):
    reqs, allow = [], []
    for e in evs:
        O = g[e]["O"]
        tks = [r["ticker"] for r in g[e]["rungs"] if r["close_time"] > O - N.DS[0]]
        for i in range(0, len(tks), PER):
            ch = tks[i:i + PER]
            allow += ch
            reqs.append({"id": "g_%s_%d" % (e.replace("KXNBAREB-", ""), i // PER), "path": "/markets/candlesticks",
                         "params": {"market_tickers": ",".join(ch), "start_ts": O - N.DS[0] - N.MOVE_S - N.LOOKBACK_S, "end_ts": O - N.MARK_S, "period_interval": 1}})
    job = {"job_id": "NBAREB_CANDLES_P%d" % k, "owner": "MAIN", "registration": "kalshi-scalper/workers/idea_desk_c/allkalshi/nbareb/NBAREB_CARD.md",
           "purpose": "NBAREB search (Idea Desk C, engine spec): 1 minute candles with volume of KXNBAREB rungs, development games only, window ending 10 minutes before the scheduled end; part %d of 2." % k,
           "heldout": "none read: development games only, KXNBAREB closes 2026-10-21 to before 2026-11-06 from the landed live list. Never requested: closes 2026-11-06 to before 2026-11-13 and the validate window (closes 2026-11-13 to before 2026-12-04, one joint read after Dec 4 on the Head of R&D's go). Each window ends 600 s before the scheduled end.",
           "allowed_endpoints": [{"name": "markets_candlesticks_batch", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": ["KXNBAREB"], "ticker_allowlist": sorted(set(allow)), "max_requests": len(reqs),
           "notes": "Built by build_nbareb_candles.py from KXNBAREB_LISTS_A (time fields only): %d games in this file, %d requests, %d tickers; window 9180 s to 600 s before the scheduled end, at most 60 tickers a request. %d games dropped by the clock check." % (len(evs), len(reqs), len(set(allow)), len(drops)),
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
           "requests": reqs}
    open("%s_P%d.json" % (pre, k), "w").write(json.dumps(job, indent=1) + "\n")
    total += len(reqs)
    print("P%d" % k, len(evs), "games", len(reqs), "requests")
print(len(g), "games", len(drops), "clock drops", total, "requests")
