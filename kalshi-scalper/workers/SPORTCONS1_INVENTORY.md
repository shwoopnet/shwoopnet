# SPORTCONS1 inventory (2026-10-30; counts, quotes, spreads and volumes only; no settled result and no lock was computed)

Produced by `PYTHONPATH=src python -m scalper.sportcons1 inventory`. A relation is testable only if both legs have a candle in the SAME minute (no forward fill) and each leg traded at least 10 contracts in that minute. Candles carry closing bid, ask and minute volume, no sizes.

## Relations that exist on file

| Id | Relation | Legs | Source |
|---|---|---|---|
| R2 | Winner complement: exactly one team wins, so YES home + YES away pays 1 (no ties: MLB, NBA, college football only) and NO home + NO away pays at least 1 (all four sports) | the two team markets of one game winner event | `espn1.sqlite` (1-minute candles, including in play) |
| R3 | Game total vs first-half total: 1H over K_1H implies game over K_game when K_game <= K_1H, so game YES + 1H NO pays at least 1 | one game-total strike, one 1H strike of the same game | `sports1.sqlite` |

## Counts

```
R1/R2 winner complement (home YES + away YES, or both NO), espn1.sqlite candles, same-minute pairs only
  KXMLBGAME: games 424, games with >=1 same-minute pair 424, pair-minutes 77802, median wider-leg spread 1.0c, p90 2.0c, median leg volume/min 3645 contracts
  KXNBAGAME: games 120, games with >=1 same-minute pair 120, pair-minutes 18900, median wider-leg spread 1.0c, p90 2.0c, median leg volume/min 4112 contracts
  KXNCAAFGAME: games 962, games with >=1 same-minute pair 962, pair-minutes 188029, median wider-leg spread 1.0c, p90 5.0c, median leg volume/min 282 contracts
  KXNFLGAME: games 107, games with >=1 same-minute pair 107, pair-minutes 21460, median wider-leg spread 1.0c, p90 1.0c, median leg volume/min 18878 contracts
R3 game total vs first-half total, strikes with K_game <= K_1H (the only strict implication: 1H over K_1H => game over K_game)
  KXNBA: games with both a game and a 1H market 115, strike pairs with K_game<=K_1H 0, games with a same-minute pair 0, pair-minutes 0
  KXNFL: games with both a game and a 1H market 105, strike pairs with K_game<=K_1H 3024, games with a same-minute pair 104, pair-minutes 13855, median wider-leg spread 1.0c, median volume game/1H 0/0
  KXNHL: games with both a game and a 1H market 0, strike pairs with K_game<=K_1H 0, games with a same-minute pair 0, pair-minutes 0
R3b strike ranges (median per game): 
  KXNBA: median lowest game strike 204.5, median highest 1H strike 124.5
  KXNFL: median lowest game strike 23.5, median highest 1H strike 42.5
series on file: sports1 ['KXNBATOTAL', 'KXNFLTOTAL', 'KXNHLTOTAL', 'KXNBA1HTOTAL', 'KXNFL1HTOTAL']; espn1 ['KXNFLGAME', 'KXNCAAFGAME', 'KXNBAGAME', 'KXMLBGAME']; sports.sqlite 12 game-winner series (hourly candles, pre-game only)
NOT on file: first-half winner, spread ladders (win by 5+/10+), game winner vs spread, first-half spread: no such series in any local database.
```

Usable with the volume rule (both legs at least 10 contracts that minute, a count of minutes only): R2 about 244,000 pair-minutes in 1,606 games (using volume above 0; the 10 contract rule is applied in the test); R3 only 110 pair-minutes in 16 NFL games at volume above 0 on both legs (sports1 candles in the far in-the-money game strikes are almost all zero volume). NBA has NO strike pair with K_game <= K_1H (lowest game strike median 204.5, highest 1H strike median 124.5), NHL has no first-half series.

## Relations the owner listed that are NOT on file

- First-half winner, first-half spread: no such series in any local database.
- Spread ladders (win by 5+/10+), so P(win by 10+) <= P(win by 5+) <= P(win), and winner against the spread ladder: no spread series on file.
- P(total over 50) vs first-half total over 25 as a SOFT relation: both ladders are on file for NFL, but the relation is not model-free (it needs an assumed first-half share of the total), so it is not a consistency test, it would be a model. Not run.
- Within one totals ladder (monotone strikes): on file, already tested (ARB5, 691 games, zero locks), not repeated.
- Winner events are on file for MLB, NBA, college football and NFL only (hockey winners, tennis in play are not in `espn1`; `sports.sqlite` has 12 winner series but hourly pre-game candles, not used).

## Limits

R3 pairs are structurally degenerate: a game strike at or below the 1H strike is a deep in-the-money game market (priced about 0.99) against an out-of-the-money 1H market (priced near 0.02), so the lock margin is bounded by how far from 1 the two quotes sit. R2 is the only deep, liquid relation (1c spreads, thousands of contracts a minute).
