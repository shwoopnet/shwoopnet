# ENDNET: expected decisions for the Head's rulings of Nov 13, 2026 (MADE-UP rows), written 15:35Z by this desk's clock

HONEST ORDER NOTE: the scorer's provisional lines (items 2, 7, 11, 13 and the z line) were edited at 15:33Z BEFORE this file was written, but the scorer had NOT been run on any fixture since the edit. This file and its edge set script are committed before the first run. The scorer sha at that point is recorded in the commit message.

Rules in force (the Head, 15:32Z): item 2 the stage 1 kill reads the median ask over every state with a strike and a two-sided quote, before the band and spread filters (median over entries is printed for information); item 7 more than one matching strike means NONE, "ambiguous strike"; item 11 an explicit void is a fee-only loss counted in n and PF, a missing or null result is unsettled, excluded, counted and flagged; item 13 a game closing before 2026-11-17 is counted as outside and not used, a game closing on or after 2026-12-15T00:00Z refuses the whole run; z is day-clustered by US Central game day, one-sided, mean net per entry, bar 5.46, information beside the bar.

## EDGE2 = the 18 edge games (EXPECTED_DECISIONS_edge.md) plus two new games
| k | game | edge | decision |
|---|---|---|---|
| 19 | a19_ambiguous | total 5, lines 5.0 (bid 28 ask 30) and 5.5 (bid 28 ask 30), both within one goal (0 <= f - total < 1) | SKIP "ambiguous strike" (and NOT in the seen-state list) |
| 20 | a20_early_close | closes 2026-11-10 (before the development window) | counted as "closed before", not used, no skip, no entry |
The new game 19 closes Nov 20 + 19 days at 02:00Z = 2026-12-09. Games 1 to 18 are as in the edge file, EXCEPT item 11 changes game 11 (void).

## Expected printed figures
- measure: games 19 (and 1 closed before the development window, not used) | entries 9 | skipped: ambiguous strike 1, ask out of band 2, no candle at the entry minute 2, no state minute 2, no strike one goal away 2, spread too wide 1 (10 skips; 9 + 10 = 19). Ask over every quoted state (12 states: 14, 15, 15, 30 x 7, 40, 46): median 30.0, lowest 14, highest 46. Ask over the entries made (information only): median 30.0, lowest 15, highest 40. Entries a week 2.25. STAGE 1: CLOSED on the week line.
- score: entries 9 | settled 8 (game 11 is a void and now counts) | unsettled 1 (game 12) with the FLAG line. Wins 4. Game 11 pnl = -fee(pay 31) = -0.015. Development: n 8 | net 4 x .675 - .170 - .015 - .325 - .427 = +1.763 | mean +0.2204 | gains 2.700 against losses 0.937: cash PF 2.88. First half (games 1 to 10): unchanged, n 4, PF 11.91. Second half (games 11 to 20): n 4, wins 1, net -0.092, PF .675 / .767 = 0.88.
- Day-clustered z (every game on its own Central day, so each cluster is one entry): 8 pnls (.675, .675, .675, -.170, -.015, -.325, .675, -.427): mean .2204, se .1654, z = 1.33 against the bar 5.46. (The one-entry cluster formula, hand calculated outside the scorer.)
- VERDICT: NOT_ENOUGH_DATA (8 settled, need 150).

## HAND set (12 games): measure unchanged except the new wording; score: 4 entries, 4 settled; z of (.675, -.427, .830, -.478): mean .150, se .3026, z = 0.50. Stage 1 median over quoted states (30, 40, 30, 50, 15, 45): sorted 15, 30, 30, 40, 45, 50 median 35.0, so the same CLOSED on the week line. The unchanged lines (entries 4, net +0.600, PF 1.66, halves 3.52 and 0.00) must still print.
## OUTSIDE set: one game closing 2026-12-15T01:00Z still REFUSES the whole run (the held-out date). A game closing 2026-11-10 alone gives: games 0 (and 1 closed before), entries 0, STAGE 1: NOT_ENOUGH_DATA (no state with a quote).

## SECOND AMENDMENT of the expectations, 15:40Z (the Head's two rulings of 15:40Z), written BEFORE the scorer is edited or run
1. z = mean of the DAILY means (US Central game day) over the SAMPLE sd (n - 1) of the daily means divided by sqrt(days), one-sided, bar 5.46; fewer than 2 days prints n/a. With one entry a day this equals the per-entry mean over sample sd / sqrt(n). Hand arithmetic: edge2 (8 entries on 8 days): sd = .1654 x sqrt(8) x sqrt(1/7) ... = .1768, z = .2204 / .1768 = **1.25**. Hand set (4 on 4 days): se .3494, z = .150 / .3494 = **0.43**. Pass fixture (160 games, 25 Central days, daily means): mean .3121, sd .1476, z **10.57**. Fail fixture: mean -.0483, sd .1670, z **-1.45** (independent script, not the scorer). Note the pass and fail point estimates change from the per-entry mean (.3375 and -.0788 before) to the mean of daily means (.3121 and -.0483) because days hold several entries.
2. No in-window game at all (the file holds only games outside the window, or none): the run REFUSES as "no in-window data" in both measure and score. The early_only fixture therefore prints REFUSED, not NOT_ENOUGH_DATA. In-window games with no qualifying state still read STAGE 1: CLOSED on the 6 a week line (the edge2 and hand figures are unchanged).
