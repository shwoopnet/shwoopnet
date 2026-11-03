# COUNT1 registration (Strategy Research V2, written 2026-11-03 BEFORE any bracket candle of a COUNT1 market was downloaded and before any result flag, price or PnL of a COUNT1 trade was read; research only)

Brief: count / pace markets (how many times someone posts or something happens in a day or week). A live OUTSIDE feed shows the running count; a pace model turns "count so far" into bracket probabilities; buy the cheap bracket (ask 3c to 30c) where the model probability is at least 3x the ask, hold to settlement. Counterparty claim: retail anchored on last period's final count.

## Duplicate check (done first)
README / workers read for MENT1 (mention markets, different mechanism), TSA1, EQUAKE1, RAINCAL, ESPORT1, ENTER1 (streams / charts / views: NOT touched, its series are excluded below), USWEEP1 and USWEEP2 (generic sweeps; USWEEP1 tested 119 series, its list is not a count-pace model), `workers/OICORE_SHAPE_INVENTORY.md`. `grep -i -E "truthsocial|KXEOWEEK|KXELONTWEETS|truth social"` over README and workers found no worker that models a running post count. Not a duplicate. (Disclosure: USWEEP1 may have touched KXTRUTHSOCIAL as a generic row; this is a different test, a mid-period count-conditional model, not a price-only sweep.)

## What was looked at before registering (disclosure)
Metadata only: the public series list (15,680 series; title / ticker search for tweet, post, how many, count, executive order), the settled market listings (live `/markets` and `/historical/markets`) of KXTRUTHSOCIAL, KXTRUTHSOCIALD, KXELONTWEETS, KXPOTUSTWEETS, KXWEFTWEETS, KXFEDTWEETS, KXIMFTWEETS, KXEOWEEK, KXPRESSBRIEFINGCOUNT, KXBILLSCOUNT, KXMAMDANIEO (counts of events and markets, first and last close, strike types, rules text). The listing rows carry `result`; I printed exactly ONE market's result (the last KXTRUTHSOCIAL and KXEOWEEK rows, in the rules print) and none were used. No candle, no price, no Truth Social count versus a bracket. Tracker reachability was tested (see below).

## What exists (census)
| Series | Cadence | Settled events on file | Settlement source | Outside tracker | Verdict on runnability |
|---|---|---|---|---|---|
| KXTRUTHSOCIAL | weekly, Sunday 12:00 AM ET to Saturday 11:59 PM ET | 39 (2026-02-15 to 2026-10-31 closes; 9 to 10 markets: less, 7 or 8 between, greater) | Roll Call (Truths, ReTruths, Quote Truths; replies only if Roll Call captured them) | CNN's public archive `https://ix.cnn.io/data/truth-social/truth_archive.json` (37,934 posts, 2022-02-14 to today, reachable here, 21 MB, no key) | RUNNABLE |
| KXTRUTHSOCIALD | daily ET calendar day | 33 (2026-10-02 to 2026-11-02; 8 markets: less than 5, six between, greater or equal 40) | same | same | RUNNABLE |
| KXEOWEEK | weekly | 54 events, 1 to 5 mixed markets (any / above 0,1,2) | signing date in the Federal Register | federalregister.gov API (reachable, keyless) | NOT_RUNNABLE mid-period: publication lags signing by 3 to 7 days (40 recent orders: median 5), so the count so far at a mid-week look is not observable; whitehouse.gov/presidential-actions is reachable (HTTP 200) but has no history of when each order was posted. Needs a recorder of that page's post times. Not a try. |
| KXELONTWEETS | weekly | 9 events, all Feb to Apr 2025 | | xtracker.io: connection failed from this sandbox (proxy 502) | NOT_RUNNABLE (series dormant since 2025-04, tracker unreachable) |
| KXPOTUSTWEETS, KXWEFTWEETS, KXFEDTWEETS, KXIMFTWEETS | weekly | 3 events each | | none tested | NOT_ENOUGH_DATA by listing (3 events) |
| KXPRESSBRIEFINGCOUNT, KXBILLSCOUNT, KXMAMDANIEO | monthly / weekly | 3, 2, 10 events | | | too few events; not tested |
Excluded as ENTER1 / other workers' territory: all Spotify, YouTube, chart, stream-count series. KXKEVCOUNT, KXBILLSCOUNTWEEKLY: no settled markets.

## Rules (two cells, fixed now)
Tested universe: KXTRUTHSOCIAL (rule COUNT1-W) and KXTRUTHSOCIALD (rule COUNT1-D), every settled event on file. Strike semantics: `between` lo..hi inclusive on the total, `less` total < cap_strike, `greater` total > floor_strike, `greater_or_equal` total >= floor_strike.
**Period and look.** Period start / end are parsed from the rules text (midnight ET of the first day to midnight ET after the last). Look = 50% of the period elapsed: weekly Wednesday 12:00 ET (start + 84 h), daily 12:00 ET (start + 12 h).
**Count so far.** c = number of archive posts with `created_at` in [start, look - 10 minutes]. (The 10 minute lag stands in for archive latency; every post in the archive is counted, reblogs included, since Roll Call counts Truths, ReTruths and Quotes.)
**Pace model (parameters frozen now, no tuning).** profile[h] = mean archive posts per hour for ET hour h over the 28 full ET days before the period start. E_sofar / E_rem = sum of profile over the elapsed / remaining hours of the period (partial hours pro rata). rho = clip((c + 10) / (E_sofar + 10), 0.5, 2.0). Remaining count R ~ negative binomial with mean mu = E_rem x rho and variance mu + mu^2 / r with r = 10. Total = c + R; bracket probability from that distribution. Sensitivity (reported, never used to choose): r = 4 and r = 30.
**Entry.** Quotes: Kalshi one minute candles for each bracket market in [look - 60 min, look + 15 min]. Signal quote = ask close of the last candle ending at or before the look, at most 60 minutes old; FILL = ask close of the first candle ending after the look (within 15 minutes), a trade needs fill ask in [0.03, 0.30] (hard limit 0.30). Signal: p_model >= 3 x fill ask. At most 2 brackets per period (highest p_model / ask), 1 contract each, held to settlement (the market's `result`, no early exit). A market with no valid quote is skipped and counted.
**Fees.** 7% x C x p x (1 - p) rounded up to the cent with C = 10, divided by 10 for one contract (p = fill ask). Net per contract = payoff - ask - fee.
**Control.** Every bracket of the same periods with fill ask in [0.03, 0.30], equal weight, one contract each (the cheap-bracket baseline). Reported next to each rule.
**Source check (data quality, not a selection tool).** In the development periods, the share where the archive's full-period total falls inside the winning bracket. If under 70%, tag SOURCE_MISMATCH and the verdict is NOT_ENOUGH_DATA whatever the P&L.

## Split
Per series, events sorted by period start: first 2/3 DEVELOPMENT (halves: first half and second half of the development events by time), last 1/3 FROZEN HOLDOUT. For the frozen holdout NO candle is downloaded and no result is read until the single holdout read, which happens only if development shows mean net above 0 in both halves and PF at least 1.5 with n at least 30, and not before 2026-11-17. Counts of holdout events are listed in the result (weekly 13, daily 11 expected).

## Numeric predictions (before any outcome)
- Development trades: weekly 3 to 20, daily 5 to 30 (total under 40; probability 85%). Take-up per period 10% to 50%.
- Mean net per contract, pooled: between -4c and +2c; PF under 1.5: 85%. Source check passes (70% or more): 60% (the archive may omit replies Roll Call includes).
- Verdict **NOT_ENOUGH_DATA** (92%); if n were large enough, FALSIFIED.

## Kill rules / verdicts (fixed now)
- **NOT_ENOUGH_DATA**: fewer than 150 trades in a cell (development plus holdout, after any holdout read). Then: report n, mean net, PF, and the date 150 trades would exist at the observed take-up rate (months to go).
- **FALSIFIED**: at 150 or more trades, mean net after fees not above 0 in BOTH halves, or PF under 1.5, or the control does as well as the rule (rule mean net minus control mean net under 1c).
- **SURVIVES (for a forward test only)**: all of the above clear and the holdout agrees. Nothing here promotes anything; a pass allows only the probe below.
- Multiple testing: two cells registered, N +4 (the coordinator keeps the running total of about 730,060, z bar about 5.27); the verdict cannot be a pass at n under 150 whatever the PF.

## Capped probe spec (only if a cell is positive in both halves with a mechanism)
1 contract, ask 3c to 30c (hard limit 0.30), at most 2 brackets per period, held to settlement; worst loss per period 60c (2 x 30c), worst day $0.60 daily cell and $0.60 weekly cell; kill after 20 fills with net under -$3.00 or 40 fills with PF under 1.0; 40 fills exist after (40 / take-up per period / periods per month) months, computed in the result.

## Forward freeze (if NOT_ENOUGH_DATA)
This exact rule (series, look, 28 day profile, r = 10, 3x, 0.30, 2 per period, fee) is frozen as of this commit for periods starting after 2026-11-03 (daily from 2026-11-04, weekly from the week of 2026-11-08), tracker `ix.cnn.io/data/truth-social/truth_archive.json`, quotes read from candles after each period (the 1 minute candles stay available), so the forward read can be run from the public record without a recorder. Earliest forward read: when 40 forward trades exist.

## Code
`src/scalper/count1.py`, tests `tests/test_count1.py` (NB pmf sums to 1, strike semantics, ET boundaries around the DST change on 2026-11-01, fee, 2-per-period cap). Cache outside the repo. One thread, sleeps, backoff on 429.

## Amendment 1 (2026-11-03, before any outcome; coordinator note from ENTER1)
ENTER1 enumerated X post counts: KXELONTWEETS has zero overlap with xtracker.polymarket.com (Elon only from 2025-11-18), KXPOTUSTWEETS 114 markets on 14 events but only 6 markets on 5 events overlap xtracker realDonaldTrump (from 2026-01-21), KXFEDTWEETS no tracker account. Not re-enumerated. Consequence: KXPOTUSTWEETS (5 overlapping events) is NOT_ENOUGH_DATA and is registered as a FORWARD freeze only, same rule shape (look 50% of the period, 28 day profile, r = 10, 3x, 0.30, 2 per period), tracker xtracker.polymarket.com realDonaldTrump; its 2026 events are checked for newer series in the result (series list search for tweets / posts with 2026 events). KXEOWEEK stays NOT_RUNNABLE mid-period (publication lag). No extra N (nothing scored).

N: +4 (2 rules x +2).

## Amendment 2 (2026-11-03, before any scoring; coordinator decision)
The daily candle fetch competes with other workers for Kalshi's rate limit and is slow. The fetch order is by event date (development events in time order, all markets of an event together), NOT by any outcome or price. At scoring time: weekly KXTRUTHSOCIAL has all 26 development events (238 markets) fetched and is scored in full (primary). Daily KXTRUTHSOCIALD has 5 of 22 development events complete (40 of 176 markets); the daily rule is scored ONLY on those events whose markets are all fetched (the earliest 5 by date, a prefix by date, not selected on results); the other 17 are listed as not scored. The daily fetch continues for the forward record. The frozen third of both series is never touched. A daily result on 5 events is a smoke test only and cannot carry a verdict beyond NOT_ENOUGH_DATA. Scorer patched to skip incomplete events (`incomplete_events_not_scored`).
