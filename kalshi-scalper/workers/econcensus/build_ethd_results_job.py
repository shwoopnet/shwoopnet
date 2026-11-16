#!/usr/bin/env python3
"""ETHD_RESULTS (Desk B, Nov 16, 2026): the settled hourly Ethereum ladder markets (KXETHD) for 2026-10-28 to 2026-11-15, so ETHLATE1 can be scored. The recorder's results.csv holds only the 15 minute markets' results, not the ladder strikes'. Fixed window: closes before 2026-11-16T00:00Z."""
import json, sys
from datetime import datetime, timezone
MIN_C = int(datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp())
MAX_C = int(datetime(2026, 11, 16, tzinfo=timezone.utc).timestamp()) - 1
def job():
    req = [{"id": "settled_KXETHD", "path": "/markets", "params": {"series_ticker": "KXETHD", "status": "settled", "min_close_ts": MIN_C, "max_close_ts": MAX_C, "limit": 1000}, "max_pages": 40}]
    return {"job_id": "ETHD_RESULTS", "owner": "DESK_B", "status": "active", "registration": "kalshi-scalper/workers/specs/ETHLATE1_CARD.md",
            "purpose": "Settled hourly Ethereum ladder markets (KXETHD) with results, closes 2026-10-28 to 2026-11-15, to score ETHLATE1 (the recorder's results file holds only 15 minute markets).",
            "heldout": "FIXED window: closes from 2026-10-28T00:00:00Z to 2026-11-15T23:59:59Z (min_close_ts %d, max_close_ts %d); nothing at or after 2026-11-16T00:00:00Z is requested. KXETHD has no row in Main's HOLDS.json for these closes (Auditor B, Nov 16); the reader of this run is ETHLATE1's loader only." % (MIN_C, MAX_C),
            "allowed_endpoints": [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "min_close_ts", "max_close_ts", "limit", "cursor"]}],
            "series_allowlist": ["KXETHD"], "ticker_allowlist": [], "max_requests": 52,
            "notes": "One series, at most 40 pages of 1,000 plus repeats after a 429; about 323 events a month with 40 to 100 strikes each, so about 15 to 35 pages expected; at 5 s about 4 minutes.",
            "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
            "requests": req}
if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "ETHD_RESULTS.json"; json.dump(job(), open(out, "w"), indent=1); print(out, "max_requests", job()["max_requests"])
