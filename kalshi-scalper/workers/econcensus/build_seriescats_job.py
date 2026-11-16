#!/usr/bin/env python3
"""SERIESCATS_LISTS (Desk B, Nov 16, 2026, the Head's GO 15:34Z): series metadata (ticker, frequency, title) of Kalshi categories (two: the runner refuses spaces in a param). 2 requests, no market, no price, no result."""
import json, sys
CATS = ["Companies", "Mentions"]   # the runner refuses a param value with a space, so "Climate and Weather" and "Science and Technology" cannot be asked until the runner allows it (a reviewed change)
def job():
    req = [{"id": "series_" + c.replace(" ", "_"), "path": "/series", "params": {"category": c, "limit": 20000}} for c in CATS]
    return {"job_id": "SERIESCATS_LISTS", "owner": "DESK_B", "status": "active", "registration": "kalshi-scalper/workers/econcensus/ECONCENSUS_NOTE.md",
            "purpose": "Series metadata of the Companies and Mentions categories (ticker, frequency, title), to find event-driven families (earnings, mentions, snow, hurricanes, launches) for engine specs. No market, price or result.",
            "heldout": "none (series metadata only: ticker, frequency, title; no market list, no price, no result, no date window)",
            "allowed_endpoints": [{"name": "series_list", "method": "GET", "path_pattern": "/series", "params_allowed": ["limit", "category"]}],
            "series_allowlist": [], "ticker_allowlist": [], "max_requests": 4,
            "notes": "Two requests; the earlier all-category list was cut by the runner's 5 MB cap, so one category at a time. Titles and frequencies only are read.",
            "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
            "requests": req}
if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "SERIESCATS_LISTS.json"; json.dump(job(), open(out, "w"), indent=1); print(out, len(job()["requests"]), "requests")
