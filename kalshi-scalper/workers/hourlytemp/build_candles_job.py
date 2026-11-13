#!/usr/bin/env python3
"""Hourly city temperature, cost and timing measurement, stage 2: build the candle job from
the HOURLYTEMP_LISTS answers. Committed Nov 12, 2026, before any list or candle was pulled.
Note: workers/HOURLYTEMP_MEASUREMENT_NOTE.md.

Uses ONLY tickers, event tickers, strikes and open and close times of the SETTLED lists. It
never reads a result or a price field. Each market lives the 60 minutes before its hour, so
one request covers the strikes of all four cities for two consecutive clock hours (one hour
if that would pass 100 tickers).

Usage: python3 build_candles_job.py <folder of the HOURLYTEMP_LISTS run> <out dir>
Writes markets.json and HOURLYTEMP_CANDLES.json.
"""
import gzip, json, os, sys
from datetime import datetime
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
from deskb_guard import refuse_all as _refuse_all
_refuse_all()   # standing rule (h): refuse any HELDOUT_ folder before the first open or glob

MAX_TICKERS, MAX_CANDLES, MAX_REQUESTS = 100, 9800, 110


def ts(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def main():
    run, out = sys.argv[1], sys.argv[2]
    man = json.load(open(os.path.join(run, "manifest.json")))
    mk = {}
    for row in man.get("rows", []):
        if row.get("status") != 200 or not str(row.get("id", "")).startswith("settled_"):
            continue
        body = json.load(gzip.open(os.path.join(run, row["file"]), "rt"))
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            try:
                mk[m["ticker"]] = {"ticker": m["ticker"], "event": m["event_ticker"], "series": m["ticker"].split("-")[0],
                                   "strike": float(m["floor_strike"]), "open_ts": ts(m["open_time"]), "close_ts": ts(m["close_time"])}
            except (KeyError, TypeError, ValueError):
                continue
    hours = {}
    for m in mk.values():
        hours.setdefault(m["close_ts"], []).append(m["ticker"])
    groups, keys = [], sorted(hours)
    i = 0
    while i < len(keys):
        a = keys[i]
        b = keys[i + 1] if i + 1 < len(keys) else None
        n2 = len(hours[a]) + (len(hours[b]) if b is not None else 0)
        if b is not None and b - a <= 3600 and n2 <= MAX_TICKERS and n2 * ((b - (a - 3600)) // 60 + 1) <= MAX_CANDLES:
            groups.append((a - 3600, b, sorted(hours[a] + hours[b])))
            i += 2
        else:
            groups.append((a - 3600, a, sorted(hours[a])))
            i += 1
    groups = groups[:MAX_REQUESTS]
    kept = sorted(t for g in groups for t in g[2])
    reqs = [{"id": "h%03d" % (k + 1), "path": "/markets/candlesticks",
             "params": {"market_tickers": ",".join(g[2]), "start_ts": g[0], "end_ts": g[1], "period_interval": 1}} for k, g in enumerate(groups)]
    job = {"job_id": "HOURLYTEMP_CANDLES", "owner": "DESK_B", "registration": "kalshi-scalper/workers/HOURLYTEMP_MEASUREMENT_NOTE.md",
           "purpose": "Hourly city temperature, cost and timing measurement (zero tries), stage 2: one minute candles of every strike of the four hourly temperature series for the 60 minutes each market lived, seven fixed days. No result is read by the reader.",
           "heldout": "none (a cost measurement; no result is read and no rule is scored)",
           "allowed_endpoints": [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": [], "ticker_allowlist": kept, "max_requests": MAX_REQUESTS, "requests": reqs,
           "notes": "DISPATCH ORDER (Head of R&D, Nov 12): LAST, behind TIE3, POL-i2 and SOCDERIV. Built by workers/hourlytemp/build_candles_job.py from the HOURLYTEMP_LISTS answers; the seven days are never extended.",
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                          "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
    os.makedirs(out, exist_ok=True)
    json.dump([mk[t] for t in kept], open(os.path.join(out, "markets.json"), "w"))
    json.dump(job, open(os.path.join(out, "HOURLYTEMP_CANDLES.json"), "w"), indent=1)
    print(f"settled markets in the lists {len(mk)} | clock hours {len(keys)} | requests {len(reqs)} (cap {MAX_REQUESTS}) | markets kept {len(kept)}")


if __name__ == "__main__":
    main()
