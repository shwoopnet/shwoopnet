# WXDAYEND second count, scorer committed (History Miner, Nov 13, 2026)

Built from the registration text only (card 74 as stated in kalshi-scalper/workers/testing/WXDAYEND_REGISTRATION.md, "The registration" and "What this desk added" items 1 and 2). The Testing Desk's wxdayend.py was not read. The count was first run ad hoc on Nov 13 at about 00:30Z (0 of 22, sent to the Head); this file and the scorer make it reproducible with a hash. No new try.

## Rule as built
- City-day = one event. The winning bracket for Nov 10 is the single market with result yes in that event's list (zero or two is unresolved and stays unread). For Nov 1 to 9 no results list was pulled, so the winner is the candle request's ticker, flagged as unconfirmed.
- day_end = market close minus 3600 s. For Nov 10 the close comes from the list's close_time. For Nov 1 to 9 it comes from the request's end_ts, which must equal local STANDARD midnight after the event date plus 3600 s (DAL UTC-6, DEN UTC-7, NY UTC-5, LAX UTC-8); a mismatch stops the run.
- Shows: any candle with end_period_ts strictly after day_end and yes_ask close at or under 0.96 (1e-9 tolerance). Reported beside it, not used: the same test on yes_ask low, and city-days with no candle after day_end.
- Kill rule: FAIL if fewer than 3 of 40 show. Only the city-days in landed runs are counted; the others are listed as not recounted.
- Both runs: status complete, every row 200 with sha256 and bytes checked, files inside the folder, hm_guard on every path.

## Made-up runs (test_wxdayend2.py)
A list run with a DAL Nov 10 list (one yes market, B78.5, closing 2026-11-11T07:00Z) and two Nov 1 candle requests; a candle run with the Nov 10 winner.
- DAL Nov 1 (B79.5, window 05:00Z to 07:00Z Nov 2, day_end 06:00Z): one candle ending exactly 06:00Z with ask 0.50 (not after day_end), one ending 06:30Z with ask 0.96. **Shows.**
- DEN Nov 1 (T65, window 06:00Z to 08:00Z, day_end 07:00Z): a candle ending 07:30Z with ask close 0.97 and low 0.90. **Does not show on close; shows on low.**
- DAL Nov 10 (B78.5, day_end 06:00Z Nov 11): only a candle ending 05:30Z. **No post-day candle; does not show.**
Expected: covered 3, shows_close 1, shows_low 2, no_post_day_candle 1, not_recounted 37, verdict FAIL by the letter only when all 40 are read, so it prints "incomplete: 37 city-days not recounted".
Refusals: a Nov 10 list with two yes markets (unresolved, reported, not counted as covered); a Nov 1 request whose end_ts is an hour off standard midnight + 1 h (stop); a HELDOUT_ path.

## Two fixes found by the first test run (not changes to the expected figures)
- The made-up DAL Nov 1 candle at 06:30Z lacked a `low` field, so the low basis could not show it; a candle's low is never above its close, so the input now carries low 0.96. The expected figures are unchanged.
- A Nov 10 list with two yes markets stopped the run (its candle was not the list winner); as written above it is reported as unresolved and stays unread. Expected for that case: unresolved [KXHIGHTDAL-26NOV10], covered 2.
