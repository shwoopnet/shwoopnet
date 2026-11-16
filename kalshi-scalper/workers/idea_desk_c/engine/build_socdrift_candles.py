#!/usr/bin/env python3
"""Builds SOCDRIFT_CANDLES_P1.json and _P2.json from the landed SOCDERIV_LISTS (time fields and tickers only). Per game: ONE batched request of the game's winner markets (3 tickers),
hourly candles (period_interval 60), window [K - 33 h, K] with K = occurrence - 3 h (the 24 h decision needs its 6 h anchor and volume windows; the live guard reads the hour before K).
Split in two files by game order, each at most 400 requests. Usage: python3 -I build_socdrift_candles.py <root> <out prefix>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import socdrift as N

PER = 60
root, pre = sys.argv[1], sys.argv[2]
bad = [i for i in N.LIST_IDS if any(True for _ in KL.bodies(root, N.LIST_JOB, i)) and KL.truncated(root, N.LIST_JOB, i, N.WIN[0])]
if bad:
    sys.exit("list truncated: not built %s" % bad)
g, drops, listed = N.games(root)
order = sorted(g, key=lambda e: (g[e]["O"], e))
half = (len(order) + 1) // 2
files = []
for evs in (order[:half], order[half:]):
    reqs, allow = [], []
    for e in evs:
        Kt = g[e]["K"]
        tks = [r["ticker"] for r in g[e]["rungs"]]
        allow += tks
        reqs.append({"id": "g_%s" % e.split("-", 1)[1] + "_" + e.split("-")[0], "path": "/markets/candlesticks",
                     "params": {"market_tickers": ",".join(tks), "start_ts": Kt - 33 * 3600, "end_ts": Kt, "period_interval": 60}})
    files.append((evs, reqs, allow))
for k, (evs, reqs, allow) in enumerate(files, 1):
    assert len(reqs) <= 400
    job = {"job_id": "SOCDRIFT_CANDLES_P%d" % k, "owner": "MAIN", "registration": "kalshi-scalper/workers/idea_desk_c/allkalshi/socdrift/SOCDRIFT_CARD.md",
           "purpose": "SOCDRIFT search (Idea Desk C, engine spec): hourly candles with volume of the three winner markets of each development soccer game, window K - 33 h to K with K = occurrence - 3 h (an estimate of kickoff); part %d of 2." % k,
           "heldout": "none read: development games only, 15 GAME series, closes 2026-09-18 to before 2026-10-30T02:53:19Z (1793328799) from the landed SOCDERIV_LISTS. Never requested: closes on or after that cut (the frozen third), closes from 2026-11-13 (SOCDERIV held-out, not pulled), KXCOPADELREYGAME. Every window ends at K, the estimated kickoff, before the match.",
           "allowed_endpoints": [{"name": "markets_candlesticks_batch", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": list(N.SERIES), "ticker_allowlist": sorted(set(allow)), "max_requests": len(reqs) + 12,
           "notes": "Built by build_socdrift_candles.py from SOCDERIV_LISTS (time fields and tickers only): %d games in this file, %d requests (cap = requests + 12 for 429 re-asks), %d tickers; one request a game, 3 tickers, hourly candles, 33 hour window (at most 99 candles). %d games dropped by the clock check." % (len(evs), len(reqs), len(set(allow)), len(drops)),
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
           "requests": reqs}
    open("%s_P%d.json" % (pre, k), "w").write(json.dumps(job, indent=1) + "\n")
    print("P%d" % k, len(evs), "games", len(reqs), "requests", len(set(allow)), "tickers")
print(len(g), "games", len(drops), "clock drops")
