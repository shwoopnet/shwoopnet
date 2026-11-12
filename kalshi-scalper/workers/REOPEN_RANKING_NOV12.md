# Re-open ranking: what stopped only for lack of reads (Idea Desk B for the Head of R&D, Nov 12, 2026)

**Counts: rows examined 344 (plus 19 queue rows that repeat them); clean class R found 3; reads-bound but able only to be FALSIFIED 4; never run for a reason nobody wrote down 4; re-opened by this file 0 (the Head of R&D decides); registered 0 so far.**

Asked for by the owner through the Head of R&D: pulls now run at 1 request a second and 1,200 a run, so "too many reads" is no longer a reason to retire anything. Every card or test that was retired, parked, demoted or orphaned was put in exactly one class by WHY it stopped. No Kalshi request was made. No live account figure is in this file; every number is a research count on public data, a request count or an estimate labelled as one.

## How it was done, and what is not verified

- Four inventories: this desk's own cards (read by me); Desk A's (worker, 39 rows, finished); Refinement's research files (worker, 104 rows plus 19 queue rows, finished); V2's perps program and its registrations with no result (worker draft, 137 rows, the worker was stopped by the account's usage limit after saving its tables); V2's power queue and two card files (read by me, 32 rows, after that worker was stopped before writing anything).
- I spot-checked the rows that matter (every R row and every named candidate) against the source files. I did NOT re-check every E, P, S and D row of the workers' tables; a mislabel there would hide an R row, and that is the main risk in this file.
- **Not covered:** V2's README holds a few hundred registrations WITH results. Those were not re-opened one by one; only the ones whose result says the read was cut by the rate limit were looked at (the last table of section 2).

## 1. Counts by class

R = stopped only for reads, enough independent events exist. P = too few independent events even with every request granted. E = closed by evidence. S = source barred or terms unread. D = on the declined list. ACTIVE = not stopped. UNCLEAR = the files give no reason, or a ruling that fits none of the five.

| Whose | Rows | R | P | E | S | D | ACTIVE | UNCLEAR |
|---|---|---|---|---|---|---|---|---|
| Desk B (16 cards, one of them in two arms, and 3 active items) | 20 | 0 | 8 | 4 | 2 | 2 | 4 | 0 |
| Desk A (11 cards and what it runs for others) | 39 | 1 | 6 | 11 | 1 | 3 | 11 | 6 |
| Refinement, research files | 104 | 3 | 19 | 28 | 19 | 9 | 16 | 10 |
| V2, power queue and card files B and C | 32 | 0 | 6 | 10 | 0 | 5 | 7 | 4 |
| V2, perps program from Nov 6 | 56 | 0 | 22 | 8 | 15 | 0 | 11 | 0 |
| V2, earlier perps tests | 14 | 0 | 3 | 8 | 3 | 0 | 0 | 0 |
| V2, registrations with no result | 67 | 0 | 1 | 3 | 2 | 50 | 6 | 5 |
| V2, results cut by the rate limit | 12 | 0 | 6 | 3 | 1 | 1 | 0 | 1 |
| Refinement's view of the queue (overlaps the rows above) | 19 | 0 | 3 | 3 | 0 | 3 | 9 | 1 |

The same test appears in more than one inventory (WXDAYEND, the approval calibration, ECONFADE), so the R column double counts: **the distinct clean R rows are three.**

## 2. The ranking

"Reads-bound" below means the stated reason was the read budget AND a verdict is now reachable. Where a verdict can only be FALSIFIED, that is said. Events needed are for a bet held to settlement at the price shown, at a one-sided z of 5.46 with 80% power: at 10c, 2,508 bets if the true PF is 1.5, 836 at PF 2, 314 at PF 3; at 20c, 1,430, 477 and 179; at 50c, 954, 318 and 119; at 75c, 1,318, 439 and 165. A time exit with results spread about 6c needs about 360 trades at a true 2c net and 160 at 3c.

"Value" is my estimate of the chance that the test reaches a verdict that CHANGES what we do (a lead, a paper listing, or a card closed for good), divided by days of desk time. It is a judgment, not a measurement.

| Rank | Test (owner) | Class | Events available with everything pulled | Events needed | Requests | Can it PASS, only be FALSIFIED, or neither | Probability of a pass | Value |
|---|---|---|---|---|---|---|---|---|
| 1 | **ECONFADE count** (Refinement row 87; Desk A protocol Q3): after a CPI or jobs print moves a Fed market 15c in 10 minutes and it retraces 4c by minute 20, buy against the move | reads-bound, falsify only | about 50 CPI and jobs prints in 25 months; about 24 a year | 360 at a true 2c | **0 extra**: widen ECONLAG's part B window from T+15 to T+25 minutes and the same pull counts the shocks | Only CLOSED (its own stop: under 40 confirmed retraces) or left as "no evidence" | under 1% | 60% that it closes the card for good, in 0.1 day: **6.0** |
| 2 | **WXDAYEND remainder** (Refinement row 74; Desk A Q1): is the decided daily-high bracket still for sale after the day ends | clean R | 40 city-days registered, 20 unpulled | a count: 3 of 40 | 22 | Only its registered FAIL or not-FAIL; 0 of 20 so far | 5% that 3 or more of the last 20 show a price | 90% that it confirms FAIL, in 0.1 day; already last in the dispatch order: **4.0** (it changes little: it is already treated as failed) |
| 3 | **POL-i2 overnight staleness** (Refinement card, never run, no reason written): a liquid politics market that moved 5c overnight and whose quote has not followed by 07:00 ET; 24 hour time exit | unknown, most likely reads | not counted by anyone; my guess 150 to 400 gaps a year on about 100 liquid politics series | 360 at 2c, 160 at 3c | not stated; a count step needs one list page per series and one hourly candle read per liquid market, about 300 to 600 | Can be FALSIFIED quickly; a pass needs a multi-cent lag in thin overnight politics books | 2% | 50% that the count step alone closes it (under 40 gaps a half), in 0.5 day: **1.0** |
| 4 | **UNRATEROUND under the paper screen** (Desk B card 4; class P on the main bar, listed here because the Head named it) | P | about 33 monthly events (unverified) | paper screen: 30 events, PF 1.3, both halves | about 40, plus the BLS API | Cannot pass the main bar. CAN be read against the slow-family screen if re-registered as one trade on every event | 5% of a real edge; about 15% of a listing by luck alone | a listing only starts paper logging: **0.4** |
| 5 | **Approval calibration remainder, W-POL-APPR1** (Refinement): calibration of the weekly approval markets by price cell | clean R, but see the note | 263 weekly RCP events (8 pulled) and 143 weekly 538 events (0 pulled; that series ended in March 2025) | 954 at PF 1.5, 318 at PF 2 (mid prices) | about 400 and 1,278 (the "1,680" is requests, not events) | PASS only if the true PF is about 2 or more, which a calibration cell does not give; realistically FALSIFIED or "no evidence". Needs a NEW registration (its event list is frozen) | 1% | Most of the RCP half arrives anyway with the queued NO-side pull (NOSIDE1_CANDLES, 1,034 requests); the 538 half is an old regime: **0.2** |
| 6 | **W-CAT-CAL1 finance and index slices** (Refinement): calibration by price cell, never scored (the queue lists the sweep as closed) | clean R | thousands of daily and hourly ladder events (179,892 index and 47,885 finance markets settled since Sep 12) | 1,430 at 20c and PF 1.5 | about 3,200 | Could reach either verdict on size. But it is a calibration sweep, and the index and stock ladders are the most tested ground we have (cheap tails, hourly ladders, lock scans: all failed) | 1% | **0.2** |
| 7 | **SPREAD historical block** (Refinement, not registered): the sports spread cell on games before Sep 12 | clean R, conditional | 1,211 game events; about 370 cell trades by the first block's rate | 2,508 at 10c and PF 1.5; 836 at PF 2 | 12,000 (ten runs), or about 6,000 for an outcome-blind sample | Only worth it as a second out-of-sample block IF the first read (W-SPREAD-CELL1, void after Nov 20) clears | 3% to 15% that the first read clears (the two estimates on the queue) | Nothing to do until that read: **0 now** |
| 8 | **POL-i1 news-reaction fade** (Refinement card; its row was removed from the file, so I have not read the rule): a politics market's jump, faded, daily candles, 3 day exit | unknown | "the only card with a large n on free Kalshi history" (Refinement's own ranking); not counted | 360 at 2c | not stated | Can be FALSIFIED. Its nearest relatives (SC1, SWING1, the shock-follow rows) all lost to cost | 2% | needs the card text from Main first: **0.3** |
| 9 | **ESPORTM1 remainder** (V2): cheap side of esports match winners against a Kalshi-only rating model | reads-bound, falsify only | 4,142 qualified events, 1,063 read; about 265 treated trades projected against a 150 floor | 836 at 10c and PF 2 | about 3,100 | Only FALSIFIED: the 68 treated trades read so far are PF 0.51 with every sign on the losing side | under 1% | A proper FALSIFIED in place of "not enough data" changes nothing we do: **0.05** |
| 10 | **USWEEP series never reached** (V2): 13,856 series the sweep did not get to before the rate limit | reads-bound | not known per series | n/a | over 14,000 | It is a sweep, not a test. The owner's new untouched-family census (task 5) is the right way to cover this ground | n/a | folded into the census: **0 as a test** |

**Also unknown, not ranked because nothing can be said until someone answers:** W-CAT-POLENT1 (politics, elections, mentions and entertainment calibration: held-out never read and no result line in the folder) and ROUNDCENT (round-cent clustering: marked running, no result). Both are Refinement's; one question to Refinement or Main settles each.

## 3. Results that the rate limit cut short, and why they are not R

| Test (V2) | What the limit cut | The other reason | Class |
|---|---|---|---|
| PROPS1, TENNIS1, SEASON1, NHLG1, BOOKNCAA1 | candles for a fraction of the sample | each model was built on a sports data site that is now barred, or the rule was empty | S or P |
| USWEEP2, USWEEP3 | about 14,000 and 10,000 series not reached | pooled results negative on what was read | E, P |
| XLADDER1 | 20 events fetched | lock and parity scans are on the declined list | D |
| MENTPERSIST1 (also Refinement row 84) | half sample; held-out never pulled | development kill bar met (PF under 1.0 in both parts) | E |
| NEWLIST1 | candle fetch rate-limited, scored on a stratified sample | FALSIFIED on the cheap side | E |

## 4. The candidates the Head named, one line each

| Candidate | Finding | Class |
|---|---|---|
| Approval and generic ballot calibration, "1,680 unpulled events" | It is 1,678 REQUESTS for 406 weekly events (263 RCP, 143 old 538). Rank 5 above | R, weak |
| AVG1 | Development is frozen at 28 rows by its own pinned cut, and its outcome is the same index its model uses. Reopening needs a new registration and real settled results | P |
| STALE1 | About 8.5 gap events a day against 1,000 to 4,000 needed; pinned cuts hold development at 74 or fewer | P |
| EARLYCLOSE1 | The testable cells are negative (PF 0.77 and 0.86). One calibration bin was positive after the fact (63 markets); it would need about 1,200 | E |
| CLINICAL2's remainder | One event a month, 17 held | P |
| COMBO1, now that combo quotes exist | Superseded: the combo recorder answers it, and S3 (combo house side) is registered with its paper read on Nov 26 | ACTIVE |
| The economics fade count | Rank 1 above, at zero extra requests | reads-bound |
| POL-n1 | Ten people is ten clusters; a person-clustered statistic cannot reach the bar. Its 7 day exit also breaks the politics hold rule | P |
| WXDAYEND's 22 requests | Rank 2 above | R |
| UNRATEROUND's descriptive read | Rank 4 above (paper screen only) | P |
| V2's perps program | **52 named tests were registered on Nov 6 and 7 (110 tries), plus the PERPGEN sweep of 500,000 rules: far more than the "10 to 20" the owner approved. 35 ran, 17 did not. 5 were FALSIFIED, as were two of the three PERPGEN slices; every other read was NOT_ENOUGH_DATA; no lead.** Stock perps only began trading on Nov 5, so the limit is days of history, not reads. 15 tests depended on the Yahoo price saver that was stopped on Nov 11. 11 have registered forward reads (the first on Dec 1 and Dec 22, the earnings tests on Jun 1, 2027). The 30 second recorder the tests were approved for holds one file | P 22, S 15, E 8, ACTIVE 11; R none |

## 5. What this says, plainly

1. **Almost nothing stopped only for reads.** Three clean rows in about 340, and none of the three is a test I would expect to pass. The read limit hid less than it seemed: nearly everything that stopped had a power, evidence, source or declined reason as well.
2. **What free reads really buy is cheap closures.** Ranks 1, 2 and 3 can each end a card for good in a day or less. That is tidying, not finding.
3. **Finding has to come from new ground.** The 13,856 series the old sweep never reached, and the perps that are only a week old, are where untested markets are. That is the owner's census (task 5), which this desk has started.
4. **Two orphans need an owner, not reads:** POL-i1 (its card text is missing from the file) and W-CAT-POLENT1 (held-out never read).

## 6. Proposed top 3 in this desk's lane, for registration today if the Head agrees

1. **ECONFADE count**, on ECONLAG's own pull: one amendment (part B's window ends at T+25 minutes), a count script, its stop rule as Desk A wrote it (under 40 confirmed retraces closes the card). Zero extra requests, zero tries.
2. **POL-i2 overnight staleness**, count step first: how many qualifying overnight gaps exist, on a fixed list of liquid politics series, before any outcome is read. Kill as the card says: fewer than 40 gaps in either half.
3. **UNRATEROUND against the slow-family screen**, re-registered as one trade on every monthly release. It would be try number 2 against that screen.

None of the three is likely to be a strategy. I am naming them because they are the honest top of a thin list.
