# RECREF: the reference-value recorder (2026-11-03, discovery infrastructure, N: +0)

A recorder is not a try. It adds no rule, scores nothing and has no promote verb. ENTER1 (`ENTER1_RESULT.md`) was NOT_RUNNABLE because Kalshi's entertainment and tech markets settle on a public number whose source shows only its CURRENT value, so there is no history to test "does the live reference already imply the outcome at the look". The only way to get that history is to record the reference and the Kalshi quote together, going forward. This does that.

## What it does
`.github/workflows/record-ref.yml` runs `scripts/record_ref.py` at minute 23 of every even hour (and by hand with workflow_dispatch). One run, per watched series: lists the open markets (kept if they close within 168 hours), lists markets settled in the last 3 days, and reads each reference page that series is paired with. It writes, on the `quote-data` branch with the built-in GITHUB_TOKEN (never main):
- `ref/quotes/<date>/<HHMM>.csv.gz`: one row per open market: slot_ts, poll_ts, server Date header, family, `refs` (the reference ids that apply to THIS market, so the join to refvals is a string match), series, ticker, event, title, open and close time, minutes to close, status, strike type, floor and cap strike, yes_bid, yes_ask, last, volume, open_interest.
- `ref/refvals/<date>/<HHMM>.csv.gz`: one row per reference item: slot_ts, poll_ts, ref_id (`rt_page:wild_horse_nine`, `kworb_us_weekly`, ...), adapter, url, http_status, rank, name, value, value2, note. For a chart: rank and name (and streams in `value`, running total in `value2` for kworb; the chart date in `note` for Billboard). For a score: the Tomatometer or Metascore in `value` and the review count in `value2`. For post counts: the number of posts in the 24 hours before the market's close.
- `ref/results/<date>/<HHMM>.csv.gz`: a market's result (yes or no) and expiration value, the first time it is seen settled.
- `ref/runs/<date>.csv`: one line per run: calls to Kalshi, calls to reference pages, 429 count, listing errors, **parse_failures** (a reference page that could not be read or whose layout no longer parses), rows written. A rising parse_failures is the sign a source changed its page; the adapter then writes no row, never a guess.
`<HHMM>` is the 2 hour slot, so a re-run of a slot replaces its files (idempotent) and a late or dropped schedule only widens the gap between polls. Each row also carries the recorder's own `poll_ts`; the reader takes the nearest poll to a look and counts a gap over 2 hours as NoData.

## The watchlist: `workers/RECREF_WATCHLIST.json` (9 series, 8 references)
Picked by rule on 2026-11-03: list every open, non-multivariate market (38,808 of them), keep series with open markets closing within 7 days that settle on a public number, then keep those whose number can be read keyless from a GitHub runner. The 131 entertainment series in ENTER1's cached list had only one with an open market (a monthly YouTube one); most of the cache is dead tickers, which is worth knowing.

| Series (open 2026-11-03) | Settles on | Reference recorded |
|---|---|---|
| KXRT (39 markets, 3 events) | Tomatometer at 10:00 ET on close day | the film's Rotten Tomatoes page, slug derived from the event title |
| KXMC (13, 1) | Metascore 7 days after release | the game's Metacritic page, slug from the title |
| KXTRUTHSOCIALD (8, 1) | Truth Social posts by Trump on one ET day | Polymarket xtracker posts in the 24 hours before the close (a count, not a rank) |
| KXTOPSONG (28, 1), KXBILLBOARDRUNNERUPSONG (28, 1), KXBBSINGLE (44, 4) | Billboard Hot 100 for the coming chart date | billboard.com Hot 100 (the last published chart), kworb Spotify US weekly and daily lists (the in-week streams that drive the next chart) |
| KXTOPALBUM (22, 1), KXBILLBOARDRUNNERUPALBUM (22, 1) | Billboard 200 for the coming chart date | billboard.com 200 (last published chart); no keyless in-week album source |
| KXSTEAMTOPSELLER (20, 1) | Steam USA weekly top sellers by revenue | the store's current top sellers list, a PROXY, not the same list |

Left out, with the reason (also in the file): YouTube Charts families (KXYTVIEWSW 244 markets, KXYTTOPSONGW, KXYTTOPSONGGW: charts.youtube.com has no keyless GET), KXALBUMSTREAMS and the Carbon Arc index series (no public source). The Spotify daily/weekly, App Store rank, Netflix and weekly post-count series (KXPOTUSTWEETS, KXELONTWEETS) had NO open market on 2026-11-03; the App Store (`apple` adapter, tested) and weekly xtracker windows are ready: add them to the watchlist when they list, no code change.
Adding a series or a source is a watchlist edit only; the script names no ticker (gate R3).

## Sources and what happened from this sandbox (one live GET each, 2026-11-03)
- kworb Spotify US daily and weekly: reachable, parsed (rank, title, streams, total). The "daily" page is the previous day's chart.
- billboard.com Hot 100 and 200: reachable, parsed 25 rows each and the chart date (2026-11-07). The page is 3 to 5 MB per read and the markup is a website, not an API: it is the most likely adapter to break (parse_failures will show it).
- Rotten Tomatoes (two films) and Metacritic (one game): reachable, parsed from the page's embedded data (Tomatometer 93 and 92 with review counts 122 and 63; Metascore 88 with 46 reviews).
- Polymarket xtracker posts: reachable, parsed (176 Trump posts so far in the Nov 3 ET day).
- Steam store top sellers JSON: reachable, parsed.
- Apple App Store RSS: reachable, adapter tested on a fixture, not in the watchlist (no open App Store market).
- Failed or not used: charts.youtube.com (not tried: needs a POST), Steam's weekly revenue chart (JS page, its API paths returned 404), the Netflix Tudum Top 10 page (reachable, 2 MB, not parsed: no open Netflix market, so no adapter).
- Kalshi from this sandbox was throttled (10 HTTP 429s on a full run, 4 listings dropped). The shared sandbox address is the cause, not the recorder: the GitHub runner has its own address, and the recorder retries a refused read twice (3 s, then 6 s) before counting it.

## Requests and cost per run
- Kalshi: 2 per series (open, settled), 18 minimum for 9 series, more on retries or when a series passes 1,000 markets; 1 per second per host. Observed 24 including retries.
- References: one fixed GET each for kworb daily, kworb weekly, Hot 100, 200, Steam (5), plus one per open film (up to 8), game (up to 6) and post-count day (up to 3). About 9 to 11 now, at most 22. 
- Wall time about 40 seconds observed, under 3 minutes expected with retries. 12 runs a day, about 1 to 2 billed Actions minutes each: roughly 400 to 700 minutes a month. The repo is public (Pages), where Actions minutes are free. Billboard's pages are about 8 MB a run.
- Storage on `quote-data`: about 15 to 30 KB gzipped per run, under 150 MB a year.
- Politeness: descriptive User-Agent, one request per second per host, no keys, no cookies, no login, GET only.

## Turn it off
Delete `.github/workflows/record-ref.yml`. Nothing else depends on it; the data already pushed stays on `quote-data`.

## What main must do
1. Merge branch `claude/v2-recorder-ref` into main. The workflow checks out the script and watchlist FROM MAIN, and scheduled workflows run only from the default branch.
2. Run the workflow once by hand (Actions tab, workflow_dispatch) and confirm a `ref/` folder with quotes, refvals and runs appears on `quote-data`; read `ref/runs` for the 429 and parse_failures counts. Scheduled starts of a new workflow are often late or dropped for a few hours.
3. Nothing to configure: no secret. Enable Actions if disabled.
4. The branch also changes `kalshi-scalper/run_tests.sh` (adds `test_recref`), shares `quote-data` with the other recorders (different folder, `ref/`), and builds on `claude/v2-recorder-daily` (its commit is merged into this branch for the test runner line only).

## How long until a first test
The recorder cannot make a test earlier than the events settle. A first test of "the reference at the look already implies the outcome" needs **at least 8 weeks of data and about 100 settled markets per family**, counting independent events, not strikes (one film's strikes move together):
- Billboard Hot 100 / 200: one event per series per week, 8 weeks is 8 events (each with 22 to 44 strikes). The binding count is events; a test on 8 events is a pilot, not a verdict.
- Rotten Tomatoes: 3 events this week; at that pace about 24 films in 8 weeks. Metacritic: about 1 game a week. Truth Social: 1 event a day, 56 days in 8 weeks, the fastest family.
- Steam: 1 event a week, and the reference is a proxy, so it can only be a weak test.
Earliest read if the recorder starts running about 2026-11-05: **the week of 2027-01-04** for a pilot; a verdict at the registered bar needs more events than 8 weeks gives for every family but Truth Social posts. The reader (like `recdaily.py`) takes the nearest poll to each look and returns None when none is within 2 hours; it is not written here (a recorder, not an evaluator).

## Tests
`tests/test_recref.py` (13 tests, adapters on saved fixtures under `tests/fixtures/ref_*`, the recorder on faked reads: window filter, per-event slugs, idempotent slot, results written once, 429 counted, one request a second per host, watchlist shape) and `test/refRecorderGates.test.js` R1 to R6 (GET only, no secret, push only to quote-data, watchlist-driven, no ticker hard-coded, row shape, politeness).
