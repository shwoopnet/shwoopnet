#!/usr/bin/env python3
"""REMATCH stage 1: build the candle job from the e-soccer LISTS answers that INPLAYJUMP already pulls.
Committed Nov 12, 2026, before any e-soccer list or candle was pulled.

Reads ONLY tickers, scheduled starts (from the ticker) and close times. It never reads a result or a price.
For every pair that qualifies by schedule it asks for the two team contracts of the LATER match, from the
earlier match's scheduled start minus 8 minutes (the reference minute less the 5 minute carry window) to the later match's
scheduled start minus 3 minutes.
The sample is never cut to save requests: if the job would need more than MAX_REQUESTS, nothing is written
and the count is printed for the Head of R&D.

Usage: python3 build_stage1_job.py <folder of the lists run> <out dir>
Writes pairs.json and REMATCH_STAGE1_CANDLES.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BEFORE_S, CARRY_S, DROPS, SERIES, STAGE1_FROM, STAGE1_BEFORE, read_events, pairs_by_schedule, ts  # noqa: E402

MAX_REQUESTS = 150            # the Head approved "about 110"
GROUP_TICKERS, MAX_CANDLES = 100, 8500
LEAD_S, TAIL_S = BEFORE_S + CARRY_S + 60, 3 * 60     # from the reference minute less the carry window, to two minutes after the entry candle


def main():
    run, out = sys.argv[1], sys.argv[2]
    lo, hi = ts(STAGE1_FROM), ts(STAGE1_BEFORE)
    events = read_events(run)
    pairs = [(a, b) for a, b in pairs_by_schedule(events) if lo <= b["close"] < hi and lo <= a["close"] < hi]
    rows = [{"A": a["event"], "B": b["event"], "codes": b["codes"], "S_A": a["S"], "S_B": b["S"], "A_close": a["close"],
             "tickers": ["%s-%s" % (b["event"], c) for c in b["codes"]], "start_ts": a["S"] - LEAD_S, "end_ts": b["S"] - TAIL_S} for a, b in pairs]
    rows.sort(key=lambda r: (r["start_ts"], r["B"]))
    groups = []
    for r in rows:
        g = groups[-1] if groups else None
        if g:
            s, e, n = min(g["start"], r["start_ts"]), max(g["end"], r["end_ts"]), g["n"] + 2
            if n <= GROUP_TICKERS and n * ((e - s) // 60 + 1) <= MAX_CANDLES:
                g["rows"].append(r)
                g["start"], g["end"], g["n"] = s, e, n
                continue
        groups.append({"rows": [r], "start": r["start_ts"], "end": r["end_ts"], "n": 2})
    print(f"e-soccer events in the lists {len(events)} | pairs qualifying by schedule inside the stage 1 slice {len(rows)} | requests needed {len(groups)} (cap {MAX_REQUESTS})")
    print("events left out of the lists read, counted: " + ", ".join("%s %d" % kv for kv in DROPS.items()))
    if any(g["end"] >= hi for g in groups):
        sys.exit("REFUSED: a request would end at or after the held-out cut (standing rule (h): development pulls are bounded by date in the job)")
    if len(groups) > MAX_REQUESTS:
        print("OVER THE CAP: no job written. The sample is not cut; the count goes to the Head of R&D.")
        return
    reqs = [{"id": "r%03d" % (k + 1), "path": "/markets/candlesticks",
             "params": {"market_tickers": ",".join(t for r in g["rows"] for t in r["tickers"]), "start_ts": g["start"], "end_ts": g["end"], "period_interval": 1}}
            for k, g in enumerate(groups)]
    job = {"job_id": "REMATCH_STAGE1_CANDLES", "owner": "DESK_B", "registration": "kalshi-scalper/workers/rematch/REMATCH_REGISTRATION.md",
           "purpose": "REMATCH stage 1 (zero tries): one minute candles of the two team contracts of each later e-soccer match, from before the earlier meeting to five minutes before its own start. Counts and cost only; no bet is scored.",
           "heldout": "none (counts and cost on the Oct 15 to Oct 23 development slice; no bet is scored and the held-out block from 2026-10-23 is not listed or pulled)",
           "allowed_endpoints": [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": [SERIES], "ticker_allowlist": sorted({t for r in rows for t in r["tickers"]}),
           "max_requests": MAX_REQUESTS, "requests": reqs,
           "notes": "Built by workers/rematch/build_stage1_job.py from INPLAYJUMP's e-soccer lists answers: every pair that qualifies by schedule, never cut. Every market closes before 2026-10-23.",
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                          "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "pairs.json"), "w"), indent=1)
    json.dump(job, open(os.path.join(out, "REMATCH_STAGE1_CANDLES.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
