#!/usr/bin/env python3
"""CFRTIK_STRIKES_DAILY job builder (Desk A, Nov 15 2026; the Head's order of 14:31Z). Offline, sends nothing.
  python3 -I build_cfrtik_strikes_job.py <out.json>
One public GET /markets list per series per 10 day close range, from 2026-11-14T00:00:00Z to 2027-01-02T00:00:00Z, status settled, for the six CFRTI-K place markets (KXBTC15M probation seat, KXSILVER15M, KXCOPPER15M, KXWTI15M, KXHYPE15M, KXBNB15M). A reader uses ONLY ticker, close_time and floor_strike (the strike source of the CFRTI-K places, sheet section 1); no result is read from it. The job is the same every day: the runner re-asks the whole range each run (Main runs it once a day), so a later run adds the newly settled windows; yesterday's windows are what the next-day run delivers (an unsettled market is not listed)."""
import sys, json, calendar, time
def ts(s): return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
SERIES = ["KXBTC15M", "KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXHYPE15M", "KXBNB15M"]
START, END, STEP = ts("2026-11-14T00:00:00Z"), ts("2027-01-02T00:00:00Z"), 10 * 86400
PAGES = 2; RETRY_SLACK = 6
def build():
    reqs, a, i = [], START, 0
    ranges = []
    while a < END: ranges.append((a, min(a + STEP, END) - 1)); a += STEP
    for s in SERIES:
        for n, (lo, hi) in enumerate(ranges, 1):
            reqs.append({"id": "strikes_%s_%02d" % (s, n), "path": "/markets", "params": {"series_ticker": s, "status": "settled", "min_close_ts": lo, "max_close_ts": hi, "limit": 1000}, "max_pages": PAGES})
    return {
        "job_id": "CFRTIK_STRIKES_DAILY", "registration": "kalshi-scalper/workers/DESK_A_FROZEN_WHEEL_DEFINITIONS_NOV13.md",
        "purpose": "Settled markets of the six CFRTI-K place series (Bitcoin probation seat, silver, copper, WTI, HYPE, BNB) closing 2026-11-14 to 2027-01-02, in 10 day close ranges, to give each window's floor_strike to the CFRTI-K place logger (the strike is in no book or coverage file). A reader takes ticker, close_time and floor_strike only; it never reads a result.",
        "heldout": "Not a card read. The landed runs hold results of windows other cards may hold out; they go into HELDOUT_PULL_RUNS.md like every pull run, and a reader opens them only through heldout_guard_v2 and takes the strike field only. Nothing before 2026-11-14T00:00Z is asked (Nov 11 to 13 strikes come from the landed NC15 lists runs).",
        "allowed_endpoints": [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "min_close_ts", "max_close_ts", "limit", "cursor"]}],
        "series_allowlist": SERIES, "max_requests": len(reqs) * PAGES + RETRY_SLACK, "requests": reqs,
        "notes": "One run a day (Main). %d requests, at most %d pages (each range holds at most 960 markets per series at 96 windows a day, so one page of 1000 is normal; the second page is margin). Pacing 5.0 s; the whole job is about %d minutes. max_requests = pages budget + %d for 429 retries." % (len(reqs), len(reqs) * PAGES, len(reqs) * 5 // 60 + 1, RETRY_SLACK),
        "owner": "DESK_A", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0, "status": "active",
        "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    j = build(); json.dump(j, open(sys.argv[1], "w"), indent=1); open(sys.argv[1], "a").write("\n"); print(len(j["requests"]), "requests, cap", j["max_requests"])
