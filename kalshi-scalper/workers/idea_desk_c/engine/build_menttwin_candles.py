#!/usr/bin/env python3
"""Builds MENTTWIN_CANDLES_P*.json: one historical single-market candle read per twin market, window [D - 180 s, D]; files of at most 460.
Usage: python3 -I build_menttwin_candles.py <root> <out prefix>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import menttwin as P

root, pre = sys.argv[1], sys.argv[2]
if KL.truncated(root, "MENTDRIFT_LISTS_A", "hist_KXTRUMPMENTION", P.DEV[0]) or KL.truncated(root, "MENTDRIFT_LISTS_A", "hist_KXTRUMPMENTIONB", P.DEV[0]):
    sys.exit("list truncated")
mk, ps = P.build(root)
want = {}
for D, a, b in ps:
    want[a["ticker"]] = D
    want[b["ticker"]] = D
reqs = [{"id": "h_" + t, "path": "/historical/markets/%s/candlesticks" % t, "params": {"start_ts": D - P.LOOKBACK_S, "end_ts": D, "period_interval": 1}}
        for t, D in sorted(want.items())]
files = [reqs[i:i + 460] for i in range(0, len(reqs), 460)]
for k, ch in enumerate(files, 1):
    job = {"job_id": "MENTTWIN_CANDLES_P%d" % k, "owner": "MAIN", "registration": "kalshi-scalper/workers/idea_desk_c/allkalshi/menttwin/MENTTWIN_CARD.md",
           "purpose": "MENTTWIN quick first read (Idea Desk C, engine spec): 1 minute candles of twin Trump mention words at D = later open + 30 min, development only, part %d of %d." % (k, len(files)),
           "heldout": "none read: development events only (own occurrence 2026-04-17 to before 2026-08-06). Never requested: TRUMPTOPIC1's spent held-out (2026-08-06 to before 2026-10-03), the MENTTWIN held-out (2026-10-03 to before 2026-11-05, read once on the Head of R&D's go) and TRUMPTOPIC1's forward window (from 2026-11-05).",
           "allowed_endpoints": [{"name": "hist_market_candlesticks", "method": "GET", "path_pattern": "/historical/markets/(?P<ticker>[A-Z0-9][A-Z0-9._-]{0,63})/candlesticks", "params_allowed": ["start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": list(P.SERIES), "ticker_allowlist": sorted(r["id"][2:] for r in ch), "max_requests": len(ch),
           "notes": "Built by build_menttwin_candles.py from MENTDRIFT_LISTS_A (time fields and word titles only): %d twin pairs, %d requests in %d files; each window ends at D." % (len(ps), len(reqs), len(files)),
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
           "requests": ch}
    open("%s_P%d.json" % (pre, k), "w").write(json.dumps(job, indent=1) + "\n")
print(len(ps), "pairs", len(reqs), "requests", len(files), "files")
