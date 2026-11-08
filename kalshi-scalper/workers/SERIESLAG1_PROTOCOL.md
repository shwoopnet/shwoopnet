# SERIESLAG1 PROTOCOL (registered Nov 8, 2026, before any series-market or game-market candle is fetched)

Research only. No trading code, no key, no order. Public Kalshi `/historical` only. Owner/main request (Nov 8): the next best test, a genuinely new mechanism. Overlap check: TIE1 (two-leg Conference League ties split by the leg-1 deficit, pre-leg-2, NOT_ENOUGH_DATA), ESPN1/SWING1/SC1 (in-play within one game), ARB1 to ARB5 (static consistency). Never done: the REPRICING LAG of a series or advance market right after the public result of the underlying game.
**Mechanism and counterparty:** when a game ends its result is public at once; the series market (who wins the best-of-N series) must jump. A maker who updates the game market but not the series market for a few minutes leaves a stale quote. Counterparty: the slow maker. It is a causal timing test: all inputs are known at the decision time.

## Universe (fixed from listings and tickers only)
Playoff series: KXNBASERIES (24 events, Apr to Jun 2026), KXNHLSERIES (24), KXMLBSERIES (9). Each game of the series is a market of KXNBAGAME / KXNHLGAME / KXMLBGAME whose ticker carries the same two team codes (set match) inside the series dates; the game market's `close_time` is the game-end instant G; its result says who won. UEFA advance ties are NOT in this registration (game-market matching exists only for UCL; a later amendment).
Candles: 1 minute candles of the two series markets (YES of each team) from G-20 minutes to G+90 minutes for every game of the series (about 1,000 requests). Games with no two-sided quote at G-5 minutes or none at G+3 minutes are dropped and counted.

## Measurement (information, not a try): lag profile
For each game end: mid of the winner's series market at G-5, G+1, G+3, G+5, G+10, G+30, G+60 minutes and the jump (mid(G+60) minus mid(G-5)). Report the share of the eventual jump already in the price at each lag (median, quartiles), and bid-ask spread by lag. This answers how many minutes a series price lags a public result, whatever the trade.

## The one registered rule (cheap side only, causal)
At the first 1 minute candle ending at least 3 minutes after G, with a valid two-sided quote: let P0 = the series YES mid at G-5 (before the result), W = the game's winner, and q = the fair series probability after the result from a fixed Markov model: each remaining game is a coin with p = 0.5, series length best-of-7 (NBA, NHL) or the number of games in the series (MLB is a best-of-3: model with the same rule); the state is the games already won by each team after this result. Buy YES of the side whose series ask is 3c to 30c AND q minus ask minus fee/100 is at least 0.05. One contract, taker at the ask, hold to the series settlement, fee `ceil(0.07 x 10 x p x (1-p) x 100 - 1e-9)` cents per 10-contract order divided by 10, stress x1.2.
Cuts: series by date, first 2/3 development, last third held out and read ONCE if NOT_YET_FALSIFIED. Judging: unit = series; `NOT_ENOUGH_DATA` under 150 development trades or under 40 distinct series-days; `FALSIFIED` if mean net not above 0, or PF under 1.5, or series-clustered z under 2.5. 1 try counted.

## Prediction (before anything is fetched)
The lag is under a minute for NBA and NHL (makers update series markets automatically from the game result); the trade count will be far below 150 (cheap side only), so NOT_ENOUGH_DATA (about 60 percent), FALSIFIED (about 36 percent), pass 4 percent. The lag profile is the deliverable. No promote verb.
