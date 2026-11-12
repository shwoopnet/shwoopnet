#!/usr/bin/env python3
"""Stage 2 of CFRTI-K: builds the candle job from the stage 1 answers (CFRTI_K_LISTS). Offline: it sends no request.
  python3 -I build_cfrti_k_candles.py <stage 1 run folder> live            > CFRTI_K_CANDLES.json        (batched, markets closing after 2026-09-12)
  python3 -I build_cfrti_k_candles.py <stage 1 run folder> hist <offset>   > CFRTI_K_CANDLES_H<offset>.json  (one request per older market, 1,000 a file)
Rules: settled markets with result yes/no that close before the cutoff 2026-11-05T00:00:00Z (a later market is dropped, never requested), 1 minute candles,
window = 3,600 s before the close to the close. live: up to 55 tickers a request on /markets/candlesticks, tickers in close-time order, the window of a batch is
(first close - 3,600) to (last close). hist: /historical/markets/{ticker}/candlesticks, one request each (so the old half of the history costs about one request a market)."""
import gzip, json, os, sys, calendar, time, re
CUTOFF = calendar.timegm(time.strptime("2026-11-05", "%Y-%m-%d"))
CUTOVER = calendar.timegm(time.strptime("2026-09-12", "%Y-%m-%d"))
BATCH, HIST_FILE = 55, 1000
def iso_ts(s):
    try: return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None
def read_markets(folder):
    man = json.load(open(os.path.join(folder, "manifest.json"))); out = {}
    for row in man["rows"]:
        if row.get("status") != 200 or "file" not in row: continue
        body = json.load(gzip.open(os.path.join(folder, row["file"])))
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            c = iso_ts(m.get("close_time")) if isinstance(m, dict) else None
            if c and m.get("ticker") and m.get("result") in ("yes", "no") and c < CUTOFF and str(m["ticker"]).startswith("KXBTC15M-"):
                out[m["ticker"]] = c
    return sorted(out.items(), key=lambda kv: (kv[1], kv[0]))
def job(reqs, tickers, endpoints, name):
    return {"job_id": name, "owner": "DESK_A", "registration": "kalshi-scalper/workers/CFRTI_K_REGISTRATION.md",
            "purpose": "Stage 2 of CFRTI-K: 1 minute candles of the settled KXBTC15M markets of the development window. Development markets only (close before 2026-11-05T00:00Z).",
            "heldout": "CFRTI-K: no market closing on or after 2026-11-05T00:00:00Z is in the allowlist", "allowed_endpoints": endpoints,
            "series_allowlist": ["KXBTC15M"], "ticker_allowlist": sorted(tickers), "max_requests": len(reqs), "status": "active", "host": "api.elections.kalshi.com",
            "base_path": "/trade-api/v2", "pacing_seconds": 1.0, "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out; three in a row end the run; no other address, no proxy, no retry around a refusal"}, "requests": reqs}
def main(folder, part, offset=0):
    mk = read_markets(folder)
    if part == "live":
        mk = [x for x in mk if x[1] > CUTOVER]
        reqs = []
        for i in range(0, len(mk), BATCH):
            b = mk[i:i + BATCH]
            reqs.append({"id": "b%04d" % (i // BATCH), "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for t, _ in b), "start_ts": b[0][1] - 3600, "end_ts": b[-1][1], "period_interval": 1}})
        j = job(reqs, [t for t, _ in mk], [{"name": "markets_candlesticks_batch", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}], "CFRTI_K_CANDLES")
    else:
        mk = [x for x in mk if x[1] <= CUTOVER][int(offset):int(offset) + HIST_FILE]
        reqs = [{"id": t, "path": "/historical/markets/%s/candlesticks" % t, "params": {"start_ts": c - 3600, "end_ts": c, "period_interval": 1}} for t, c in mk]
        j = job(reqs, [t for t, _ in mk], [{"name": "historical_market_candlesticks", "method": "GET", "path_pattern": "/historical/markets/(?P<ticker>[A-Za-z0-9_.-]+)/candlesticks", "params_allowed": ["start_ts", "end_ts", "period_interval"]}], "CFRTI_K_CANDLES_H%s" % offset)
    json.dump(j, sys.stdout, indent=1); sys.stdout.write("\n")
if __name__ == "__main__":
    main(*sys.argv[1:])
