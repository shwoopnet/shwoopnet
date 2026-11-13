# INPLAYJUMP pilot and tennis screen validation report (Desk A, Nov 13, 2026; counts and validation only, NO result read)
Run: INPLAYJUMP_PILOTVAL, kalshi-pull run 43338597423 (22 of 22 requests 200), lists run 43333651862, series file sha256 34f708687df24f5a..., engine sha256 c889c333..., screencheck bd465202. Driver: `inplayjump_pilot_run.py` (pilot mode of the engine, markets restricted to tickers with a pilot candle).

## Pilot (cost and tradeability), per family
| family | matches | qualifying decisions with a two-sided entry minute | passing ask 0.20-0.85 and spread <= 4c | median one-way cost |
|---|---|---|---|---|
| ESOCCER | 33 | 17 | 0 (0%) | 5.5c |
| TABLE_TENNIS | 10 | 1 | 0 | 28.0c |
| EBASKETBALL | 10 | 0 | 0 | n/a |
| ITF_TENNIS | 4 | 2 | 2 | 2.5c |
| CHALLENGER_TENNIS | 3 | 2 | 2 | 3.0c |
Reasons not a bet (ESOCCER): ask or spread outside the band 17, entry minute not two-sided 1. Samples are tiny (the first batch of each family, development days only): the ESOCCER line (17 decisions, 0 passing, median 5.5c over the 4c kill) is the only one with any weight; TABLE_TENNIS has 1 decision, EBASKETBALL 0, tennis 2 each.

## Tennis screen validation (Amendment 5 point 3; Amendment 6)
ITF_TENNIS: 10 matches; (a) minute candles in an hour with no hourly candle 21; (b) minute closes outside their hour's low to high 0; screened vs full engine mismatches 0 -> SCREEN VOID.
CHALLENGER_TENNIS: 10 matches; (a) 126; (b) 0; mismatches 0 -> SCREEN VOID.
By the text (either count above zero voids the screen) both tennis screens are void: both are clean on (b) and on every engine comparison, and the text decides, not my reading. The Head rules full-from-open pull or dropping a family.

## Match with the Testing Desk's second scorer (9fb6ac99)
Identical on ESOCCER (33 / 17 / 0 / 5.5c), TABLE_TENNIS (10 / 1 / 0 / 28c), EBASKETBALL (10 / 0), CHALLENGER (2 bets, cost 3.0c) and on the screen counts (21, 126, 0, 0, no mismatch). ONE DIFFERENCE: ITF. Mine: 2 qualifying decisions, both pass (KXITFMATCH-26OCT09DELERE-DEL price 0.59 one-way 2.5c; KXITFWMATCH-26OCT09WANSHI-WAN price 0.23 (ask 0.22) one-way 2.5c), median 2.5c. Theirs: 1 bet and 1 outside the band, costs 4.0c over all and 2.5c for entries. The candidate for the difference is the WANSHI entry at price 0.23, close to the 0.20 edge of the entry band: whether the band test is on the ask (0.22) or the ask plus the 0.01 slip (0.23), or the registered rounding. Needs Testing Desk's entry ask for that match.

## Pull plan under the 1,800 ceiling (numbers from the lists)
clock families 284 requests (ESOCCER 113, TABLE_TENNIS 82, EBASKETBALL 89); tennis plain from open 1,329 (ITF 726, CHALLENGER 603); the hourly pass (92) is moot with the screen void. Full-from-open for both tennis families: 284 + 1,329 = 1,613, inside 1,800 and over 1,200, so split: clock families first, then ITF, then CHALLENGER. Dropping a family is the Head's call; the pilot alone gives ESOCCER little chance of clearing the 4c cost kill (median 5.5c, 0 of 17 passing), so the clock pull could be ordered last or ESOCCER pulled only for the cost line.
