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

To compare: `python3 -I make_mapbreak_fixture.py <dir> 7`, then both builds on `<dir>/lists` and `<dir>/candles`. Not yet compared: the Testing Desk's build for Amendments 8 to 10 had not been pushed when this was written.
