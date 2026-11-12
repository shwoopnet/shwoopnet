# W-SPREAD-CELL1 (registered Nov 12, 2026, before any new candle is pulled; NOT started until Main says so)

Source of the idea: in W-CAT-SPORTS1 (SPORTS_CAL_REGISTRATION.md, SPORTS_CAL_RESULT.txt) the cell SPREAD, YES, price bucket 0.05 to 0.15, look more than 24 h before close, showed PF at +1c of 1.62 (train, n 56) and 1.45 (validate, n 57), with a negative lower 90 percent bound. It was the best of many cells, so it is a lead, not a finding. Desk A's caveat, stated here: a cell with zero true edge at 10c shows PF 1.45 in both thirds at n 56 about 2 percent of the time, and this one was chosen as the best of about 58 main-grid cells.

## The one cell (frozen)
- Series: the six sports SPREAD series of W-CAT-SPORTS1 (MLB, NBA, NCAAF, NCAAMB, NFL, NHL spreads).
- Observation: one per event, the market whose YES mid is nearest 0.5 at the look (outcome blind, the same rule as the original scorer); the look is the same one hour candle more than 24 h before close; buy YES at the ask when the ask is 0.05 to 0.15; hold to settlement; 1 contract; fee 0.07*p*(1-p) unrounded; slippage +0c and +1c; +1c is the pass basis.
- Data: ONLY events NOT already scored in W-CAT-SPORTS1 (the 360 events in candles_sp.jsonl are excluded entirely, including its unread newest third). That is the 1,041 live-range SPREAD events whose candles were never pulled. The lists of those events are already held (no market list read needed). Events are in the registration by ticker list fixed at the time of the pull (SPREAD_CELL1_EVENTS.json, committed before the first request); an event not in the file is in no sample.
- Sample: these events are out of sample for the lead, so they are pooled in one block, read ONCE after the pull is complete (no running tally, no peeking: the scorer prints nothing until the pull is complete and the file is marked READ-ONCE-DONE).
- Pass bar: n of 100 events or more in the cell, PF at +1c of 1.5 or more, and the event-clustered 90 percent lower bound of the mean at +1c above 0. Multiplicity: the lead was the best of about 58 cells, so the pass also needs a one-sided z of 3.1 or more (Bonferroni over 58 at 0.05); N for the shared deflation is 9,465 + 1 cell.
- Kill: n of 100 reached and PF at +1c under 1.2, or lower bound below 0, is FAIL for this cell; below n 100 it is UNDERPOWERED and reported as 'no evidence at n = x', never FAIL.
- Cutoffs: the old thirds stay as constants (cut1 1791195907, cut2 1793328799, from CUTS_W-CAT-SPORTS1.json). This test does not use them to score; it is one pooled out-of-sample block. HELD-OUT of W-CAT-SPORTS1 (the newest third of the 360) stays UNREAD.

## Read count and time
- 274 batched candle requests (55 tickers each, events within 2 days), no market-list reads. At the 25 reads an hour the shared address allows, 274 requests need about 11 hours if no other pull uses a read, longer if the NO-arm pull continues alongside.
- Expected cell n: the old 360 events gave 56 + 57 observations in the cell (about 0.31 per event); 1,041 events would give about 320, comfortably above 100.
- NOT STARTED. Waiting for Main's go.

READ-ONCE MARKER: NEW HELD-OUT BLOCK NOT READ as of 2026-11-12.

## Outcome labels (added Nov 12, 2026, BEFORE SPREADCELL1 is dispatched; Head of R&D request)
- PASS: n of 100 or more events in the cell, PF at +1c of 1.5 or more, event-clustered 90 percent lower bound above 0, one-sided z of 3.1 or more.
- FAIL: n of 100 or more and (PF at +1c under 1.2 or lower 90 percent bound below 0).
- LEAD (the middle): n of 100 or more and neither PASS nor FAIL. A LEAD is not a pass: no probe, no popup; the forward shadow S2 (SHADOW_RULES_NOV12.md) continues to a stated n of 100 shadow fills and is read once.
- UNDERPOWERED: n under 100, reported as 'no evidence at n = x', never FAIL.
- One command prints the read (spread_cell1_score.py); it prints nothing but 'pull incomplete' until the pull is marked complete.

## Clarification of the look and bucket (Nov 12, 2026, before dispatch)
- The scorer reproduces the original W-CAT-SPORTS1 definition exactly: the 'more than 24 h before close' look is the last hourly candle at or before close minus 48 hours, no more than 2 hours old (the original scorer's gt24h bucket is 48 hours); the YES ask bucket is 0.05 up to but not including 0.15; the bucket filter is applied before choosing the market nearest 0.5 mid. Under n 100 the scorer prints only the label ('no evidence at n = x'), no PF, mean, bound or z.

## Partial pull rule and marker (committed Nov 12, 2026, before dispatch; Head of R&D request)
- Output layout: kalshi-pull writes raw answers (one gzipped file per request, 0001.json.gz onward), manifest.json (one row per request: status, bytes, sha256) and STATUS under pull/SPREADCELL1/<run>/ on branch kalshi-pull-data. A converter (spread_cell1_convert.py, tested on a synthetic answer) turns them into the candles jsonl.
- DERIVED marker: SPREADCELL1_PULL_COMPLETE is written only by the converter, and only when every one of the 274 requests (across all runs of this job) has a manifest row with an answered status (or 404 meaning no candles, which counts as answered) and the STATUS of the latest run says complete. It is never written by hand.
- PARTIAL PULL RULE: if a run stops early (three 429s end a run), the remaining unanswered requests are re-dispatched as further runs of the same job (the explicit request list is not changed); the read WAITS for all 274. If all 274 are not answered by 2026-11-20T00:00Z, the read is VOID: no candle is scored, and a new registration is needed. No candle is looked at before the marker exists.
