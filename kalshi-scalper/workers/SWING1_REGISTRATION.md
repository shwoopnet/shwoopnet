# SWING1: after a large sudden in-play swing, is the side that just lost win probability (priced 5c to 30c) mispriced when held to settlement?

Registered 2026-11-03 BEFORE any outcome of any SWING1 trade was computed or looked at. Worker ID SWING1, session "Strategy Research V2". 2 tries (Try A: the swing rule; Try B is only the matched control, not a second claim). **N: +2.** Running count about 730,005 (coordinator keeps the total); z bar about 5.27.

## Duplicate check (done first, 2026-11-03)
Not run before. Nearest work, none of it this test:
- **SC1** (tennis, 62,747 jump events): a 5c jump, then MOM or FADE with a 2 or 5 minute scalp exit, two fees and two spreads. Different exit (round trip, not settlement), different size of move, different sport.
- **ESPN1** (football, college football, NBA, MLB game-winner asks held to settlement, one entry per game): the signal was ESPN's win probability against the Kalshi ask, no price swing trigger and no cheap-side band. Same data file, different question.
- **SPORTCONS1, SP1, F6, F7, ARB5, FAMSPORTS, FAMXV, SPORTSPRE, ESPORT1**: consistency locks, pre-game favourites, totals, pre-game ESPN gap, Polymarket pre-game. None conditions on an in-play price swing.
- **IDEAS20 MOM_FADE / SURGE_FADE and LADFADE** (Bitcoin only): the same overreaction idea on 15 minute crypto, FALSIFIED (MOM_FADE -3.28c). Different market, so this is a new test of the same mechanism on a new venue of it. OICORE_SHAPE_INVENTORY.md lists no in-play sports swing fade held to settlement.
Verdict: NOT a duplicate. A try is spent.

## Mechanism and counterparty
After a score run, a turnover or a goal, retail flow reacts to the scoreboard. If the market OVERREACTS, the side that just lost win probability is priced below its true chance and the cheap side wins more often than its price. If it UNDERREACTS (a run is the start of a collapse) the cheap side wins less often than its price. **Counterparty:** the panic sellers of the trailing side (they sell YES on the faller into a thin book). **Honest prior:** sports in-play prices on Kalshi follow the sharp books closely and a swing of 25c is usually a real information event (a score), so a pass is unlikely (prior of a pass 4%).

## Data
`data/espn1.sqlite` (built by ESPN1): `egame` (ESPN start time), `match` (home and away Kalshi game-winner tickers), `kmarket` (result), `candle` (1 minute closing bid and ask in dollars, aligned to ESPN start). 2026-08-29 to 2026-10-28. Kalshi public data only; no new API calls are made by this test.

## Universe (fixed on metadata, before any outcome)
Leagues with at least 150 matched games in the file: **college football (KXNCAAFGAME, 963 games) and MLB (KXMLBGAME, 426 games)**. NFL (107) and NBA (123) are below 150 and are excluded. 1,389 games. Windows by ESPN start time (equal thirds of games, set now): **W1 start before 2026-09-13T01:00Z; W2 from then to before 2026-10-03T16:00Z; W3 from 2026-10-03T16:00Z (FROZEN, last third, unread, scored only if W1 and W2 both pass).**

## Trigger (ONE definition, no tuning, no variants)
For a game, a candle is valid if `0 <= bid < ask <= 1` and ask minus bid is at most 0.10; mid = (bid + ask) / 2. In-play: candle end time at or after ESPN start and at most start + 16,200 s (college football) or 14,400 s (MLB); the 5 minute look-back must also be in-play.
For ticker X at candle time t: **drop = (highest mid of X over the valid candles ending t-300 s to t-60 s) minus mid(X, t)**. A **swing** is drop >= 0.25 (the YES mid fell by at least 25 cents within 5 minutes). X is the **faller**.
**Entry:** the candle ending exactly t + 60 s must exist and be valid; if the faller's ask there is in [0.05, 0.30], buy the faller's YES (the cheap side) at that ask, C = 10 contracts, **hard limit 0.30**, held to settlement. **Max one per game** (the first swing that qualifies, either ticker of the game; the two tickers are complements so this is one position). A swing whose next ask is outside [0.05, 0.30] is skipped and a later swing in the same game may still qualify.
**Fee:** 7% x C x p x (1-p), rounded UP to the cent per order, divided by C for per-contract figures; fees x1.2 as a check. At these prices that is 0.4c a contract at 5c up to 1.5c at 30c, i.e. about 5% to 8% of the price paid, so the break-even win rate sits 0.4 to 1.5 points above the price. No exit fee. Net per contract = (1 if the faller's market settled yes else 0) - ask - fee/C.

## Control (same cheap-side band, non-swing minutes, same game phase)
Every in-play candle t' of a game (same universe and validity) where **neither ticker has drop >= 0.10 over the look-back** and no swing (drop >= 0.25) has yet occurred in that game; the cheaper ticker by mid at t' is bought at its ask on the candle ending t' + 60 s if that ask is in [0.05, 0.30]. Controls are grouped in cells of **phase** (elapsed time divided by the game cap, thirds) x **ask band** (5 bands of 5c). Each swing trade is compared with the mean net of the control cell it falls in (a game's controls in a cell are averaged first, then games). **Excess = swing net minus matched control net.** Reported: win rate against mean ask, mean net, PF, and excess, day-clustered (UTC date of the game start) z.

## Numeric prediction (stated before)
Cheap-side win rate within 1.5 points of the mean ask (no overreaction either way), net -1.5c to -3c a contract after fees, PF 0.6 to 1.1, excess within +-1.5c. About 250 to 450 swing trades in W1+W2. FALSIFIED with probability about 92%.

## Kill rules
- **FALSIFIED** if profit factor (sum of positive net divided by absolute sum of negative net, after fees) is under 1.5 in W1 or in W2 (the frozen W3 is the third window), or the excess (swing minus control) is not positive in both halves (first and second half of the W1+W2 trades by date).
- **NOT_ENOUGH_DATA** if fewer than 150 swing trades in W1+W2 pooled, with the message "needs N more trades, about M months at the observed rate" (the file stops at 2026-10-28; sports seasons change, so the rate is stated per month of games).
- A pass requires also pooled day-clustered z of the excess at the deflated bar (about 5.27) and fees x1.2 still positive. Anything else is not a pass.
- Frozen W3 is not opened unless W1 and W2 both pass. No re-tuning of 25c, 5 minutes, 5c to 30c or the leagues after any result.

## Capped-probe spec (only if positive in both halves with a mechanism; otherwise none)
1 contract, hard limit 0.30 on the ask, one per game, college football and MLB game-winner markets only, no overlap with L1 (different series), a kill rule of 3 losses in the first 10 fills or net under zero after 40 fills, worst day = 1 contract x 0.30 x number of games with a swing that day (about $3 to $6 at 10 to 20 qualifying games). 40 fills would exist about N/(trades per month) months out (stated in the result). No live code is written by this test and there is no promote verb.

## Look-ahead and hygiene
Trigger uses only candles ending at or before t; the fill is the next minute's ask (one minute latency). The result of a ticker is read only after the entry is fixed. Game cap and universe are fixed above. Gentle on APIs: none are called.
Code `src/scalper/swing1.py`, tests `tests/test_swing1.py` (synthetic). Result file `workers/SWING1_RESULT.md`, and `data/swing1_result.txt`.
