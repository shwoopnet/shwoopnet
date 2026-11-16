#!/usr/bin/env python3
"""Builds MENTBREADTH_CANDLES_P1.json: one historical single-market read per sampled wide word, window [D - 180 s, D].
Usage: python3 -I build_mentbreadth_candles.py <root> <out.json>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import mentbreadth as P

root, outp = sys.argv[1], sys.argv[2]
if KL.truncated(root, "MENTDRIFT_LISTS_A", "hist_KXTRUMPMENTION", P.DEV[0]) or KL.truncated(root, "MENTDRIFT_LISTS_A", "hist_KXTRUMPMENTIONB", P.DEV[0]):
    sys.exit("list truncated")
ws, nwide = P.build(root)
reqs = [{"id": "h_" + r["ticker"], "path": "/historical/markets/%s/candlesticks" % r["ticker"], "params": {"start_ts": D - P.LOOKBACK_S, "end_ts": D, "period_interval": 1}}
        for D, r in sorted(ws, key=lambda x: x[1]["ticker"])]
job = {"job_id": "MENTBREADTH_CANDLES_P1", "owner": "MAIN", "registration": "kalshi-scalper/workers/idea_desk_c/allkalshi/mentbreadth/MENTBREADTH_CARD.md",
       "purpose": "MENTBREADTH quick first read (Idea Desk C, engine spec): 1 minute candles of a fixed md5 sample of wide-event Trump mention words at D = open + 30 min, development only.",
       "heldout": "none read: development events only (own occurrence 2026-04-17 to before 2026-08-06). Never requested: TRUMPTOPIC1's spent held-out (2026-08-06 to before 2026-10-03), the Trump-word families' joint held-out (2026-10-03 to before 2026-11-05, read once on the Head of R&D's go) and TRUMPTOPIC1's forward window (from 2026-11-05).",
       "allowed_endpoints": [{"name": "hist_market_candlesticks", "method": "GET", "path_pattern": "/historical/markets/(?P<ticker>[A-Z0-9][A-Z0-9._-]{0,63})/candlesticks", "params_allowed": ["start_ts", "end_ts", "period_interval"]}],
       "series_allowlist": list(P.SERIES), "ticker_allowlist": sorted(r["id"][2:] for r in reqs), "max_requests": len(reqs),
       "notes": "Built by build_mentbreadth_candles.py from MENTDRIFT_LISTS_A (time fields and word titles only): %d wide words, the first %d by md5 read; each window ends at D." % (nwide, len(reqs)),
       "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
       "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
       "requests": reqs}
open(outp, "w").write(json.dumps(job, indent=1) + "\n")
print(nwide, "wide words", len(reqs), "requests")
