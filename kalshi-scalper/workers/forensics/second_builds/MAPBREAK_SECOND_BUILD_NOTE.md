# MAPBREAK step 1: second build against the Testing Desk's build, on made-up rows (Forensics desk, 2026-11-13)

Ordered by the Head of R&D. `mapbreak_second.py` was built from Desk B's registration and Amendments 1 to 7. Disclosure: this desk leak-audited the Testing Desk's `mapbreak.py` and `breakplay.py` on Nov 12, so it is not a clean-room reader. Invented rows only (`make_mapbreak_fixture.py`, seed 7: 1,120 made-up matches); no landed file and no result was opened. The Testing Desk's build was run at `c5476d64` (state from the map results, Amendments 4 to 6; Amendment 7 was not yet coded there).

## Result: not the same output. Three differences, in order of weight

1. **The 4c spread line is a raw float comparison in the Testing Desk's build, so some spreads of exactly 4c are treated as wider than 4c.** Example: 0.54 minus 0.50 is 0.040000000000000036 in floating point and fails "at most 0.04"; 0.29 minus 0.25 passes. The registration says "a spread of 4c or less". Effect on the made-up fixture, share of looks with a gap of 8c or more and a spread of 4c or less: 12.8% against 14.2% (CS2, first look), 18.5% against 19.9% (Dota 2), 15.0% against 16.7% (Valorant), 15.9% against 17.5% (LoL, second look). With the tolerance removed from this build the two agree on every one of those shares to the last digit, which proves the cause. **This is the number the registered kill line reads (10%), and the same comparison decides which bets fire.** The size of the effect on real quotes depends on how many qualifying looks have a spread of exactly 4c; it can only make the share LOWER than the registered rule gives.
2. **Best-of-three.** The registration (state point 1 and the series file) needs map markets 1 AND 2 for the key. The Testing Desk's build gives a first look to a match with no map-2 market. On the fixture that is 31 matches. This build follows the text; a switch (`--first-look-without-map-2`) exists only to compare like for like.
3. **The denominator of the "winner's bid at 0.90 before the map closed" count.** The Testing Desk counts every match with a pre-match minute; this build counts filled looks. The text says "for each look". Shares differ by under 2 points on the fixture.

Also: the Testing Desk's top line `sampled` (944) is not the sum of its per-title `sampled` (894); the top line is taken before the start guard and the missing-map-1-result drop.

## What agrees (with the map-2 switch set for a like-for-like run)

98 of 128 compared figures: matches filled at the pre-match minute, matches lost because the map-1 contracts were never two-sided in the same minute, fills at both looks, minutes from the map close to the look, the median spread, the one-way entry cost, the gap's median, quartiles and 90th percentile, every placebo figure, the second-look counts, and every verdict label on this fixture. The 30 that differ are the shares of point 1 and the counts of point 3.

## Places where the text did not settle a choice

Fifteen are listed in `mapbreak_second.py` (`AMBIGUITIES`) and printed with every run. The ones that could move a figure: what "qualifying decision minutes" means for the one-way cost (every filled look, or only the looks where the rule fires; both are printed), the cheaper side on equal gaps, and the denominators of the second look and of the 0.90 count.

## Not done yet

Amendment 7 (state observed from the map contracts' last candle) is built here (`measure observed`) and runs on the fixture; it cannot be compared until the Testing Desk has coded it.

## Rebuilt to the final text, Amendments 1 to 10 (2026-11-13, after the note above)

The Head of R&D approved Desk B's clarifying Amendment 10 (final text at 6872b365 on `claude/idea-desk-b`), which settles the open places listed above: map markets 1 AND 2 are required; the cost line is over every look left, on the cheaper side's contract, as (limit minus mid) plus the fee at the limit; observability is counted per look reached; equal gaps are no bet; a quote candle carries a bid or an ask; every "or less" and "or more" carries a 1e-9 tolerance; the candle that names the winner must end no earlier than 10 minutes before the map market's close. Amendments 8 and 9 changed the rule itself: the winner is named only by its OWN map contract's best bid of 0.90 or more while the other's does not show it, and a decision is a bet only if the NEXT minute's candle shows an ask at or under the limit (the look candle's ask plus 1c).

`mapbreak_second.py` now follows that text only (sha256 `ffa557fa...`; the Amendment 7 version is at commit db1c0354). Fourteen places where the text still leaves a choice are listed in the file and printed with every run; the ones most likely to differ between two builds are 2 (an empty-book candle is not a quote), 3 (the age limit applies to both teams' candles), 4 (what "look reached" means when no winner can be named), 6 (an equal-gap look stays in the gap share's denominator) and 7 (no candle in the next minute is "not filled").

`make_mapbreak_fixture.py` is version 2 (sha256 `650e513b...`): 4,820 invented matches at seed 7, with planted cases for the new rules: only quotes 12 to 15 minutes old, both teams at 0.90, the loser's contract with no quote, empty-book candles last, quotes that name the wrong team, a quote that usually stands for the next minute, and cheap map-1 contracts in one match of nine so the placebo share is not zero. My output on it is `MAPBREAK_SECOND_OUTPUT_fixture_v2_seed7_MADE_UP_DATA.json`. On it one title and look passes the 150 minimum and reads "IN", the rest read "no evidence at n = x", so the comparison exercises the counts, the shares, the cost line and both kinds of verdict line.

To compare: `python3 -I make_mapbreak_fixture.py <dir> 7`, then both builds on `<dir>/lists` and `<dir>/candles`.

## Second comparison, Amendments 1 to 10 (2026-11-13): NOT the same output yet; four readings differ, no arithmetic differs

Run against the Testing Desk's `mapbreak.py` at 8eab7e0e (sha256 `881988a5...`) on fixture version 2, seed 7. Invented rows only.

| # | What differs | Testing Desk's build | The text, as I read it (this build) | Size on the made-up fixture |
|---|---|---|---|---|
| 1 | Which candle may name the map's winner | it must end at or before the map market's CLOSE (and no earlier than 10 minutes before it) | the last quote candle ending at or before the LOOK minute (Amendment 8 point 1), no earlier than 10 minutes before the close (Amendment 10 line 7). No upper limit at the close is written. | CS2 first look: 1,082 looks left against 1,866. The fixture plants many quotes after the close, so this is far larger here than it would be on real candles. On real candles the case that matters is the candle of the minute in which the map market closed: it ends AFTER the close and before the look. |
| 2 | The one-way cost line | (ask minus mid) plus the fee | (limit minus mid) plus the fee at the limit, the limit being the ask plus 1c (Amendment 10 line 8) | exactly 1c: 3.0c against 4.0c on most cells. It decides the 4c kill line. |
| 3 | The placebo share used at the second look | all of the title's first-look matches (their output flags "DIFFERENT SETS") | the same matches as the second look's looks left (Amendment 3: "measured on the same matches"; Amendment 7 point 3: "per title and per look") | CS2: 0.071 over 1,082 against 0.060 over 248. It feeds the "twice the placebo" line. |
| 4 | Which matches can have a second look | only matches whose POSTED map results say one map each (used to plan the candle pull; their page discloses it as a limit) | any match whose OBSERVED winners are one map each (Amendment 7 point 2); the result field names nobody | 1 to 2 looks a title (a match with no posted map-1 result but quotes that show one map each). One fired bet differs in one title. |

With readings 1 and 4 set equal (a switch in this build for 1, a scratch variant for 4), **every count, every gap figure, the shares, the spread and the minutes agree at both looks in all four titles**; what is then left is the 1c on the cost line and the placebo set. The shares are printed to three decimals there and four here.

Reading 4 is not a look-ahead in the bet (the bet still needs the observed state), but it does select the second-look sample with a result that is posted after the look. On landed data both builds are limited by the candles that were pulled, which were planned the same way.

Each of the four needs one sentence from Desk B (or the Head) before the recount, because under rule 16b the two builds must print the same figures.

## Third comparison, on the landed development candles (2026-11-13): the same figures at the first look, except the cost line by exactly 1c

After Amendment 10 lines 9 (an empty book is not a quote) and 10 (the candle that names the winner ends at or before the map market's close; ruled by the Head on Auditor B's finding, which settles reading 1 above in the Testing Desk's favour), this build was changed to match the text (sha256 `87398c20...`) and run on the whole first pull: lists `MAPBREAK_LISTS/2026-11-12T1919Z_43289005222`, candles `MAPBREAK_CANDLES/2026-11-12T1954Z_43294876878` and `MAPBREAK_CANDLES_REST/2026-11-13T0023Z_43336673397` (282 of 282 requests). Development only, counts only, no match result read by either build. The Testing Desk's build is `mapbreak.py` sha256 `881988a5...` (7aa6d6d3, audited CLEAN).

| First look | CS2 | Dota 2 | Valorant | LoL |
|---|---|---|---|---|
| Looks left (state observable, both match contracts two-sided, a pre-match minute) | 874 | 219 | 49 | 35 |
| Fired / filled at the next minute / fired, not filled | 62 / 45 / 17 | 3 / 0 / 3 | 3 / 3 / 0 | 2 / 2 / 0 |
| State not observable, look reached / no pre-match minute | 42 / 37 | 12 / 4 | 4 / 4 | 6 / 1 |
| No look minute | 108 | 34 | 6 | 6 |
| Gap share (8c or more, spread 4c or less) | 7.1% | 1.4% | 6.1% | 5.7% |
| Placebo share, same matches | 0.6% | 1.8% | 2.0% | 0% |
| Gap on the cheaper side: median, quartiles, 90th percentile | 1.6c, -0.1c to 4.4c, 9.6c | 0.2c, -0.9c to 1.7c, 4.1c | 1.4c, 0.2c to 2.5c, 7.5c | 1.0c, -0.4c to 3.2c, 6.9c |
| Median spread of the match contracts; minutes from the map close to the look | 3c; 2.7 | 3c; 2.7 | 3c; 2.6 | 3c; 2.5 |
| One-way cost, this build (limit minus mid plus the fee, Amendment 10 line 8) | 4.0c | 4.5c | 4.0c | 4.0c |
| One-way cost, Testing Desk's build (ask minus mid plus the fee) | 3.0c | 3.5c | 3.0c | 3.0c |
| Verdict, both builds | no evidence at n = 45 | no evidence at n = 0 | no evidence at n = 3 | no evidence at n = 2 |

24 figures a title were compared (counts, the gap distribution, the three shares, the placebo's n, share, median and 90th percentile, spread, minutes, cost). 23 are identical in every title. The one that differs is the cost line, by exactly 1c in every title: reading 2 of the table above, still to be ruled. Under the text's reading CS2's median cost is exactly 4.0c, which is AT the kill line and not above it, and Dota 2's 4.5c is above it. Neither changes a verdict here: every title is under 150 fired and filled bets and under the 10% gap share line at the first look.

Readings 3 (the placebo set at the second look) and 4 (second-look matches planned from posted map results) bear on the second look only, which waits for the `MAPBREAK_CANDLES_M2` run.

Output: `MAPBREAK_SECOND_OUTPUT_landed_first_pull_282_requests_counts_only.json`.

## Fourth comparison, after the Head's final rulings and Amendment 11 (2026-11-13): the same output

Rulings: (1) the state candle is capped at the map market's close (Amendment 10 line 10); (2) the KILL reads the standing template, (ask minus mid) plus the fee as charged at the limit, and (limit minus mid) plus the fee is printed beside it as "cost as paid at the limit, information only" (the finding on line 8 was correct as the text stood; the text was corrected to the template); (3) the second look's placebo is over the second look's own looks; (4) the text stands on observed winners, and the landed data's restriction to matches whose posted results say one map each is printed as a disclosed limit that can only flatter the second look.

This build (sha256 `6be8be28...`) follows Amendment 11. The Testing Desk's final build is 0794063a (`breakplay.py` sha256 `a8e64bbe...`, `mapbreak.py` `881988a5...`).

- **Fixture version 2, seed 7 (invented rows), with the disclosed limit applied (`--second-look-planned-from-posted-results`): 212 figures compared at both looks in four titles, all identical** (one apparent difference of 0.001 in a share was my comparison script rounding a figure twice; the two builds print 5 of 68 as 0.0735 and 0.074).
- By the text alone (observed winners), the second look has 1 to 2 more looks a title on the fixture; the count is printed by this build ("observed one map each but the posted results do not say so": 1, 2, 1, 2).
- **Landed first pull (282 requests), first look: 27 figures a title, all identical**, including both cost figures: the kill's 3.0c (Dota 2 3.5c) and the as-paid 4.0c (4.5c). The count of first looks where the observed winner differs from the posted map result is 0 in every title. The first look is recorded by the Head as out at step 1 for every title (45, 0, 3 and 2 fired and filled bets against 150; gap shares 7.1%, 1.4%, 6.1%, 5.7% against 10%).

The second look waits for the `MAPBREAK_CANDLES_M2` run.

## Fifth comparison: both looks on all landed candles, the second-look run included (2026-11-13): the same output

Lists `MAPBREAK_LISTS/2026-11-12T1919Z_43289005222`; candles `MAPBREAK_CANDLES` (165 requests), `MAPBREAK_CANDLES_REST` (117) and `MAPBREAK_CANDLES_M2/2026-11-13T0030Z_43337581556` (65). Development only, counts only, no match result read by either build. This build `6be8be28...` with the disclosed second-look limit; the Testing Desk's 0794063a.

**212 figures compared at both looks in four titles: all identical.**

| Second look (one map each, before map 3) | CS2 | Dota 2 | Valorant | LoL |
|---|---|---|---|---|
| Looks reached / state observable / looks left | 388 / 363 / 363 | 109 / 101 / 101 | 20 / 19 / 19 | 17 / 13 / 13 |
| Fired / filled at the next minute | 34 / 27 | 5 / 4 | 1 / 0 | 0 / 0 |
| Gap share (8c or more, spread 4c or less) | 9.4% | 5.0% | 5.3% | 0% |
| Placebo share, the second look's own looks | 0.8% | 1.0% | 0% | 0% |
| One-way cost the kill reads / as paid at the limit | 3.5c / 4.5c | 4.0c / 5.0c | 3.0c / 4.0c | 2.5c / 3.5c |
| Verdict, both builds | no evidence at n = 27 | no evidence at n = 4 | no evidence at n = 0 | no evidence at n = 0 |

The disclosed limit, measured: on the landed candles the text's reading (observed winners) and the posted-results plan give the same looks left in every title, and the count of second looks where the observed map-2 winner differs from the posted one is 0 in every title. The limit's size here is therefore nil as far as the pulled candles can show; matches outside the plan have no candles and cannot be checked.

Every title is under 150 fired and filled bets at the second look, and CS2's gap share (9.4%) is also under the 10% line. Dota 2's kill-line cost is exactly 4.0c, at the line and not above it; it does not decide anything because the count rule comes first.

Output: `MAPBREAK_SECOND_OUTPUT_landed_all_347_requests_counts_only.json` (replaces the first-pull file's second-look block; the first look is unchanged).
