#!/usr/bin/env python3
"""POL-i2 count step, stage 2: build the hourly candle job from the POLI2_LISTS answers.
Committed Nov 12, 2026, before any list or candle was pulled. Registration:
workers/pol_i2/POLI2_COUNT_REGISTRATION.md.

Uses ONLY tickers, open and close times and the list's total volume. It never reads a price
or a result field. Markets are taken most traded first, at most 600, six a request.

Usage: python3 build_candles_job.py <folder of the POLI2_LISTS run> <out dir>
Writes markets.json and POLI2_CANDLES.json.
"""
import gzip, json, os, sys
from datetime import datetime

START_TS = 1788652800      # 2026-09-06 00:00 UTC: seven days of volume before the first gap day
END_TS = 1794484800        # 2026-11-12 12:00 UTC = 07:00 ET on the last gap day; nothing later is pulled
MAX_MARKETS, PER_REQUEST, MAX_REQUESTS = 600, 6, 100


def ts(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def main():
    run, out = sys.argv[1], sys.argv[2]
    man = json.load(open(os.path.join(run, "manifest.json")))
    mk = {}
    for row in man.get("rows", []):
        if row.get("status") != 200 or "file" not in row:
            continue
        body = json.load(gzip.open(os.path.join(run, row["file"]), "rt"))
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            try:
                vol = float(m.get("volume_fp", m.get("volume", 0)) or 0)
                mk[m["ticker"]] = {"ticker": m["ticker"], "series": m["ticker"].split("-")[0], "event": m.get("event_ticker", ""),
                                   "open_ts": ts(m["open_time"]), "close_ts": ts(m["close_time"]), "volume_total": vol}
            except (KeyError, TypeError, ValueError):
                continue
    live = [m for m in mk.values() if m["close_ts"] > START_TS and m["open_ts"] < END_TS]
    live.sort(key=lambda m: (-m["volume_total"], m["ticker"]))
    kept = live[:MAX_MARKETS]
    groups = [kept[i:i + PER_REQUEST] for i in range(0, len(kept), PER_REQUEST)][:MAX_REQUESTS]
    kept = [m for g in groups for m in g]
    reqs = [{"id": "p%03d" % (k + 1), "path": "/markets/candlesticks",
             "params": {"market_tickers": ",".join(m["ticker"] for m in g), "start_ts": START_TS, "end_ts": END_TS, "period_interval": 60}} for k, g in enumerate(groups)]
    job = {"job_id": "POLI2_CANDLES", "owner": "DESK_B", "registration": "kalshi-scalper/workers/pol_i2/POLI2_COUNT_REGISTRATION.md",
           "purpose": "POL-i2 overnight gaps, COUNT step (zero tries), stage 2: hourly candles from 2026-09-06 to 07:00 ET on 2026-11-12 for the most traded markets of the 61 fixed politics series. Counting only; no trade is scored and no result is read.",
           "heldout": "gap days from 2026-11-13 are not pulled; this stage scores nothing",
           "allowed_endpoints": [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": [], "ticker_allowlist": sorted(m["ticker"] for m in kept), "max_requests": MAX_REQUESTS, "requests": reqs,
           "notes": "DISPATCH ORDER (Head of R&D, Nov 12): after TIE3, before SOCDERIV. Built by workers/pol_i2/build_candles_job.py from the POLI2_LISTS answers: most traded first, at most 600 markets, six a request.",
           "status": "superseded", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                          "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
    os.makedirs(out, exist_ok=True)
    json.dump(kept, open(os.path.join(out, "markets.json"), "w"))
    json.dump(job, open(os.path.join(out, "POLI2_CANDLES.json"), "w"), indent=1)
    print(f"markets in the lists {len(mk)} | open at some time in the window {len(live)} | kept {len(kept)} (cap {MAX_MARKETS}; cut {max(0, len(live) - len(kept))}) | series with a market {len({m['series'] for m in live})} | requests {len(reqs)}")


if __name__ == "__main__":
    main()
