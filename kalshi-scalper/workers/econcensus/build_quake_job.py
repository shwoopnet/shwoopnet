#!/usr/bin/env python3
"""QUAKEH_LISTS (Desk B, Nov 16, 2026, the Head's order of 17:25Z): the settled markets of KXBIGGESTQUAKEH (earthquake hourly), counts only: settled markets and events per day. A fixed date window; no price or result is read."""
import json, sys
from datetime import datetime, timezone
MIN_C = int(datetime(2026, 9, 17, tzinfo=timezone.utc).timestamp())
MAX_C = int(datetime(2026, 10, 17, tzinfo=timezone.utc).timestamp()) - 1
def job():
    req = [{"id": "settled_KXBIGGESTQUAKEH", "path": "/markets", "params": {"series_ticker": "KXBIGGESTQUAKEH", "status": "settled", "min_close_ts": MIN_C, "max_close_ts": MAX_C, "limit": 1000}, "max_pages": 8}]
    return {"job_id": "QUAKEH_LISTS", "owner": "DESK_B", "status": "active", "registration": "kalshi-scalper/workers/econcensus/ECONCENSUS_NOTE.md",
            "purpose": "Counts of the settled markets of KXBIGGESTQUAKEH (earthquake hourly) for 30 days: markets and events a day. Tickers and close times only; no price or result is read.",
            "heldout": "FIXED date window: closes from 2026-09-17T00:00:00Z to 2026-10-16T23:59:59Z only (min_close_ts %d, max_close_ts %d); nothing at or after 2026-10-17T00:00:00Z is requested. The list carries results; the reader reads ticker, event ticker and close_time only; the run is listed on HELDOUT_PULL_RUNS.md." % (MIN_C, MAX_C),
            "allowed_endpoints": [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "min_close_ts", "max_close_ts", "limit", "cursor"]}],
            "series_allowlist": ["KXBIGGESTQUAKEH"], "ticker_allowlist": [], "max_requests": 12,
            "notes": "One series, at most 8 pages of 1,000, plus repeats after a 429; at 5 s about a minute.",
            "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
            "requests": req}
if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "QUAKEH_LISTS.json"; json.dump(job(), open(out, "w"), indent=1); print(out, "max_requests", job()["max_requests"])
