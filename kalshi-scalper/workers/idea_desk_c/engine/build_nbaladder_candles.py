#!/usr/bin/env python3
"""Builds NBALADDER_CANDLES_P1.json and _P2.json from the landed KXNBAPTS_LISTS_A (time fields only): one batched live request per game
(two when a game has more than 60 rungs), window [O - 9180 s, O - 600 s] for rungs still open at the earliest decision (close after O - 7200 s).
Split in two files by game order (by scheduled end), each under 150 MB. Usage: python3 -I build_nbaladder_candles.py <root> <out prefix>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import nbaladder as N

PER = 60
root, pre = sys.argv[1], sys.argv[2]
if KL.truncated(root, N.LIST_JOB, N.LIST_ID, N.WIN[0]):
    sys.exit("list truncated: not built")
g, drops, listed = N.games(root)
order = sorted(g, key=lambda e: (g[e]["O"], e))
half = (len(order) + 1) // 2
parts = [order[:half], order[half:]]
total = 0
for k, evs in enumerate(parts, 1):
    reqs, allow = [], []
    for e in evs:
        O = g[e]["O"]
        tks = [r["ticker"] for r in g[e]["rungs"] if r["close_time"] > O - N.DS[0]]
        for i in range(0, len(tks), PER):
            ch = tks[i:i + PER]
            allow += ch
            reqs.append({"id": "g_%s_%d" % (e.replace("KXNBAPTS-", ""), i // PER), "path": "/markets/candlesticks",
                         "params": {"market_tickers": ",".join(ch), "start_ts": O - N.DS[0] - N.MOVE_S - N.LOOKBACK_S, "end_ts": O - N.MARK_S, "period_interval": 1}})
    job = {"job_id": "NBALADDER_CANDLES_P%d" % k, "owner": "MAIN", "registration": "kalshi-scalper/workers/idea_desk_c/allkalshi/nbaladder/NBALADDER_CARD.md",
           "purpose": "NBALADDER search (Idea Desk C, engine spec): 1 minute candles with volume of KXNBAPTS rungs, development games only, window ending 10 minutes before the scheduled end; part %d of 2." % k,
           "heldout": "none read: development games only, KXNBAPTS closes 2026-10-21 to before 2026-11-06 from the landed live list. Never requested: PROPUNDER's reserve (closes 2026-11-06 to before 2026-11-13) and the joint validate window (closes 2026-11-13 to before 2026-12-04, one read with SIBHIT-R after Dec 4, on the Head of R&D's go). Each window ends 600 s before the scheduled end.",
           "allowed_endpoints": [{"name": "markets_candlesticks_batch", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": ["KXNBAPTS"], "ticker_allowlist": sorted(set(allow)), "max_requests": len(reqs),
           "notes": "Built by build_nbaladder_candles.py from KXNBAPTS_LISTS_A/2026-11-15T1457Z_43727127463 (time fields only): %d games in this file, %d requests, %d tickers; window 9180 s to 600 s before the scheduled end (143 minutes), at most 60 tickers a request (8,580 ticker-minutes, under 10,000). %d games dropped by the clock check are not requested." % (len(evs), len(reqs), len(set(allow)), len(drops)),
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
           "requests": reqs}
    open("%s_P%d.json" % (pre, k), "w").write(json.dumps(job, indent=1) + "\n")
    total += len(reqs)
    print("P%d" % k, len(evs), "games", len(reqs), "requests", len(set(allow)), "tickers")
print(len(g), "games kept", len(drops), "clock drops", total, "requests")
