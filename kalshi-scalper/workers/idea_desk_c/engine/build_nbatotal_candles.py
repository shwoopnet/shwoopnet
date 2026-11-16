#!/usr/bin/env python3
"""Builds NBATOTAL_CANDLES_P1.json and _P2.json from the landed KXNBATOTAL_LISTS_A (time fields only). Per game: one batched request per decision window
[D - 3780 s, D] for D of 9 h, 5 h and 4 h before the scheduled end (rungs open at D), and one for the 3.5 h mark [O - 12660 s, O - 12600 s]; at most 60 tickers
a request. Split in two files by game order, each at most 470 requests. Usage: python3 -I build_nbatotal_candles.py <root> <out prefix>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import nbatotal as N

PER = 60
root, pre = sys.argv[1], sys.argv[2]
if KL.truncated(root, N.LIST_JOB, N.LIST_ID, N.WIN[0]):
    sys.exit("list truncated: not built")
g, drops, listed = N.games(root)
order = sorted(g, key=lambda e: (g[e]["O"], e))
half = (len(order) + 1) // 2
files = []
for evs in (order[:half], order[half:]):
    reqs, allow = [], []
    for e in evs:
        O = g[e]["O"]
        wins = [("D%d" % (d // 3600), O - d - N.MOVE_S - N.LOOKBACK_S, O - d, O - d) for d in N.DS] + [("M", O - N.MARK_S - 60, O - N.MARK_S, O - N.MARK_S)]
        for tag, a, b, dd in wins:
            tks = [r["ticker"] for r in g[e]["rungs"] if r["close_time"] > dd]
            for i in range(0, len(tks), PER):
                ch = tks[i:i + PER]
                allow += ch
                reqs.append({"id": "g_%s_%s_%d" % (e.replace("KXNBATOTAL-", ""), tag, i // PER), "path": "/markets/candlesticks",
                             "params": {"market_tickers": ",".join(ch), "start_ts": a, "end_ts": b, "period_interval": 1}})
    files.append((evs, reqs, allow))
for k, (evs, reqs, allow) in enumerate(files, 1):
    assert len(reqs) <= 470
    job = {"job_id": "NBATOTAL_CANDLES_P%d" % k, "owner": "MAIN", "registration": "kalshi-scalper/workers/idea_desk_c/allkalshi/nbatotal/NBATOTAL_CARD.md",
           "purpose": "NBATOTAL search (Idea Desk C, engine spec): 1 minute candles with volume of pre-game KXNBATOTAL rungs, development games only, one window per decision time (9 h, 5 h, 4 h before the scheduled end) and the 3.5 h mark; part %d of 2." % k,
           "heldout": "none read: development games only, KXNBATOTAL closes 2026-10-21 to before 2026-11-06 from the landed live list. Never requested: closes 2026-11-06 to before 2026-11-13 and the joint validate window (closes 2026-11-13 to before 2026-12-04, after Dec 4, joint print, clause S2). Every window ends at least 3.5 hours before the scheduled end.",
           "allowed_endpoints": [{"name": "markets_candlesticks_batch", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": ["KXNBATOTAL"], "ticker_allowlist": sorted(set(allow)), "max_requests": len(reqs) + 12,
           "notes": "Built by build_nbatotal_candles.py from KXNBATOTAL_LISTS_A (time fields only): %d games in this file, %d requests (cap = requests + 12 for 429 re-asks), %d tickers; decision windows 63 minutes, mark window 1 minute, at most 60 tickers a request. %d games dropped by the clock check." % (len(evs), len(reqs), len(set(allow)), len(drops)),
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
           "requests": reqs}
    open("%s_P%d.json" % (pre, k), "w").write(json.dumps(job, indent=1) + "\n")
    print("P%d" % k, len(evs), "games", len(reqs), "requests", len(set(allow)), "tickers")
print(len(g), "games", len(drops), "clock drops")
