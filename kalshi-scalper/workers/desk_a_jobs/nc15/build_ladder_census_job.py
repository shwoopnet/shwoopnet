#!/usr/bin/env python3
"""LADDER_CENSUS_LISTS job builder (Desk A, Nov 15 2026; the Head's yes of 14:42Z, item 3 'all of Kalshi'). Offline, sends nothing.
  python3 -I build_ladder_census_job.py <out.json>
Settled-market LISTS only (public GET /markets; a reader uses ticker, close_time, result, volume and last price only; no candles, no orders) for the daily, weekly and hourly ladder series the research archive does not cover, so the calibration-map census can count markets per family. The series names come from the repo's own notes and recorders and are NOT verified against Kalshi: a name Kalshi does not list simply returns an empty list (one wasted request). Truncation is by max_pages: an hourly ladder holds thousands of markets a day (the archive's ladders file has 166,479 rows for 40 days of Bitcoin, Ethereum and S&P), so for the hourly series the answer is a CAPPED SAMPLE and its count is a lower bound, never the family size; daily and weekly series are small and are expected to list in full."""
import sys, json, calendar, time
def ts(s): return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
START, END = ts("2026-09-07T00:00:00Z"), ts("2026-11-15T00:00:00Z")           # public history reaches back about 69 days
DAILY_WEEKLY = ["KXGOLDD", "KXSILVERD", "KXXRPD", "KXSOLD", "KXHYPED", "KXDOGED", "KXCOPPERD", "KXBRENTD", "KXNATGASD", "KXAAAGASD", "KXGOLDW", "KXWTIW", "KXTNOTEW", "KXAAAGASW"]
HOURLY_NEW = ["KXNASDAQ100U", "KXGOLDH", "KXWTIH", "KXSILVERH"]
HOURLY_ARCHIVED = ["KXBTCD", "KXETHD", "KXINXU"]                            # archive covers Sep 4 to Oct 13: only Oct 14 onward is asked
ARCH_END = ts("2026-10-14T00:00:00Z")
RETRY_SLACK = 14
def ranges(a, b, n):
    out, step = [], (b - a + n - 1) // n
    while a < b: out.append((a, min(a + step, b) - 1)); a += step
    return out
def build():
    reqs, pages = [], 0
    def add(series, lo, hi, k, mp):
        nonlocal pages
        reqs.append({"id": "census_%s_%02d" % (series, k), "path": "/markets", "params": {"series_ticker": series, "status": "settled", "min_close_ts": lo, "max_close_ts": hi, "limit": 1000}, "max_pages": mp}); pages += mp
    for s in DAILY_WEEKLY:
        for k, (lo, hi) in enumerate(ranges(START, END, 3), 1): add(s, lo, hi, k, 4)
    for s in HOURLY_NEW:
        for k, (lo, hi) in enumerate(ranges(START, END, 7), 1): add(s, lo, hi, k, 3)
    for s in HOURLY_ARCHIVED:
        for k, (lo, hi) in enumerate(ranges(ARCH_END, END, 3), 1): add(s, lo, hi, k, 6)
    return {
        "job_id": "LADDER_CENSUS_LISTS", "registration": "kalshi-scalper/workers/DESK_A_ALLKALSHI_CENSUS_NOV15.md",
        "purpose": "Settled-market lists (ticker, close_time, result, volume, last price; no candles) of daily, weekly and hourly ladder series not in the research archive, 2026-09-07 to 2026-11-15, for the all-of-Kalshi calibration-map census (counts of settled markets per family and date).",
        "heldout": "A census of counts only. The landed run carries results of windows other cards may hold out: it goes into HELDOUT_PULL_RUNS.md like every pull run; a reader opens it only through heldout_guard_v2, takes the fields above, and applies its own card's cutoff and the open W3 cuts.",
        "allowed_endpoints": [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "min_close_ts", "max_close_ts", "limit", "cursor"]}],
        "series_allowlist": DAILY_WEEKLY + HOURLY_NEW + HOURLY_ARCHIVED, "max_requests": pages + RETRY_SLACK, "requests": reqs,
        "notes": "%d requests, page budget %d plus %d for 429 retries. Pacing 5.0 s (12 a minute). Hourly series are CAPPED SAMPLES (max_pages 3 or 6): the count is a lower bound. Series names are unverified; an unlisted name returns empty." % (len(reqs), pages, RETRY_SLACK),
        "owner": "DESK_A", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0, "status": "active",
        "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    j = build(); json.dump(j, open(sys.argv[1], "w"), indent=1); open(sys.argv[1], "a").write("\n"); print(len(j["requests"]), "requests, cap", j["max_requests"])
