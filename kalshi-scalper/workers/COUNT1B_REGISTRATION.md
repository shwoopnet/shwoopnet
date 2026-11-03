# COUNT1B registration (Strategy Research V2, written 2026-11-03 BEFORE any match between an archive count and a settled bracket was computed; measurement only, not a trading try)

Question: which counting rule over CNN's public Truth Social archive (`https://ix.cnn.io/data/truth-social/truth_archive.json`) reproduces the WINNING BRACKET Kalshi settled on (Roll Call / Factba.se count) for KXTRUTHSOCIAL (weekly) and KXTRUTHSOCIALD (daily)? COUNT1 got 65% (17 of 26 weekly periods) with "all posts". No price, candle or trading outcome is read by this worker.

## Duplicate check
COUNT1 (workers/COUNT1_REGISTRATION.md, COUNT1_RESULT.md, src/scalper/count1.py) used definition D1 only and tagged SOURCE_MISMATCH. No other worker reconciles the definition. Not a duplicate.

## Rules text read (public market fields, in `/tmp/count1_cache/count_all.json`)
- Weekly: "Truths, ReTruths, and Quote Truths are included in the total count. Replies are included only if captured by Roll Call. The post count will be recorded at 10:00 AM ET on [the day after the period]. Posts deleted as of the Expiration Time will not be included. Between is inclusive." Period 12:00 AM ET first day to 11:59 PM ET last day, source Roll Call.
- Daily: same inclusions, "Replies are included if captured by Roll Call", period 12:00:00 AM to 11:59:59 PM ET, "Posts deleted as of 12:00 AM ET" do not count.
- Neither text cites a Factba.se definition beyond "Roll Call". Settlement field `expiration_value` is the winning bracket label only (e.g. "140-159", "25-29"), not the count; the exact count is therefore unknown and the match test is "archive count falls inside the winning bracket".
- Archive fields: id, created_at, content, url, media, replies_count, reblogs_count, favourites_count. There is NO reblog, reply or quote flag: those can only be inferred from the content text (ReTruths appear as content beginning "RT"; media-only posts have empty content). Composition since 2026-08-01 (counts only, no matching): 2,915 posts, 847 empty content (all with media), 351 begin "RT", 47 are a bare URL.

## Match test
Winning bracket = the market of the event with `result == "yes"` (its lo..hi, or the open end for less / greater). Match = archive count in [period start, period end) under the definition falls inside that bracket (inclusive). Periods start/end parsed from rules text as in COUNT1 (`parse_period`, midnight ET to midnight ET after the last day). Events used: ONLY periods starting before 2026-10-20. Periods starting 2026-10-20 or later are held out and not touched.

## Candidate definitions (8, fixed now; no more will be added)
D1 all posts, ET day boundaries (the COUNT1 baseline).
D2 exclude posts with empty content (media-only), ET.
D3 exclude posts whose stripped content begins "RT" (ReTruths), ET.
D4 exclude both empty content and "RT" posts, ET.
D5 exclude empty content and bare-URL-only posts (content is one http(s) URL), ET.
D6 exclude "RT" posts and bare-URL-only posts, keep media-only, ET.
D7 D1 with UTC day boundaries (period start/end taken as the same calendar dates at 00:00 UTC).
D8 D4 with UTC day boundaries.

## Split and selection
All events (weekly and daily pooled) with period start before 2026-10-20, sorted by period start; first half (floor n/2) = SELECTION, second half = CONFIRMATION. The definition with the highest exact-bracket match rate on the SELECTION half wins (ties: lowest number). Per-series rates are reported but not used to choose. Weekly and daily are not mixed within a tie-break. The confirmation half is scored for the chosen definition only (the other seven are also printed for reference, never used to choose).

## Pass / fail (fixed now)
- PASS: chosen definition match rate >= 90% on the CONFIRMATION half (and at least 10 events in it). Then an addendum registers the pace-model rule forward-only.
- Otherwise **NO_DEFINITION_MATCHES**: report best rates and stop. Not a trading try, N +0 for the matching step.
- Prediction (before computing): best definition is D4 or D2 or D3; selection rate 75% to 90%; PASS probability 30% (Roll Call may count differently in ways the archive cannot show, e.g. replies, deleted posts).

## Weakness stated up front
Match is on brackets, whose widths are 20 weekly and 5 daily, so the test cannot see small count differences; it only cares about the bracket the model needs. An open-ended winning bracket (">240", "40+") is an easy match; they are counted and reported separately.

N: +0 for this step.
