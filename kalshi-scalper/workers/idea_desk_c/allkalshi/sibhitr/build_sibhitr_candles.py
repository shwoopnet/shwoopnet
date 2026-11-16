#!/usr/bin/env python3
"""Builds SIBHITR_CANDLES.json from the SIBHITR_LISTS_A list (time fields only): one historical single-market candle read per open rung,
window [T - 180 s, T]. (2025-26 markets are before the historical cutoff, so the batched live endpoint is not used.)
Usage: python3 -I build_sibhitr_candles.py <root> <out prefix>   writes <prefix>_P1.json ... in files of at most 460 requests."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sibhitr_lib as L

root, pre = sys.argv[1], sys.argv[2]
if L.truncated(root):
    sys.exit("list truncated: not built")
g = L.games(L.list_rows(root))
reqs = []
for e in sorted(g):
    for t in g[e]["open"]:
        reqs.append({"id": "h_" + t, "path": "/historical/markets/%s/candlesticks" % t,
                     "params": {"start_ts": g[e]["T"] - L.LOOKBACK_S, "end_ts": g[e]["T"], "period_interval": 1}})
PER = 460
files = [reqs[i:i + PER] for i in range(0, len(reqs), PER)]
for k, chunk in enumerate(files, 1):
    tick = sorted(r["id"][2:] for r in chunk)
    job = {"job_id": "SIBHITR_CANDLES_P%d" % k, "owner": "MAIN", "registration": "kalshi-scalper/workers/idea_desk_c/allkalshi/sibhitr/SIBHITR_CARD.md",
           "purpose": "SIBHIT-R one read (Idea Desk C): 1 minute candles of 2025-26 KXNBAPTS rungs open at T = occurrence - 60 min, closes 2026-03-01 to before 2026-04-14, part %d of %d." % (k, len(files)),
           "heldout": "The released window only (PROPS1 CLOSED Nov 16 by the Head of R&D; Amendments 1 and 2): closes 2026-03-01 to before 2026-04-14. Nothing else is requested; each window ends at T, so no candle after the decision is fetched.",
           "allowed_endpoints": [{"name": "hist_market_candlesticks", "method": "GET", "path_pattern": "/historical/markets/(?P<ticker>[A-Z0-9][A-Z0-9._-]{0,63})/candlesticks",
                                  "params_allowed": ["start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": ["KXNBAPTS"], "ticker_allowlist": tick, "max_requests": len(chunk),
           "notes": "Built by build_sibhitr_candles.py from SIBHITR_LISTS_A (time fields only): %d games, %d requests in all, %d files; this file %d requests." % (len(g), len(reqs), len(files), len(chunk)),
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
           "requests": chunk}
    open("%s_P%d.json" % (pre, k), "w").write(json.dumps(job, indent=1) + "\n")
print(len(g), "games", len(reqs), "requests", len(files), "files", "clock drops", len(L.B.CLOCK_DROPS))
