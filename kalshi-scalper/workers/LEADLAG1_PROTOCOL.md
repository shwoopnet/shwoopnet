# LEADLAG1 protocol (registered before any scoring)

Research only. No live, functions/ or page change. Data: local sqlite files only (alts2, alts3, alts4, fresh, rep, l1b, book, five, hist15 BTC, ETH, gold). No API calls, no outside sources.

## Idea
Kalshi's own 15 minute markets close in the same window. When a LEADER series' yes-mid moves by at least m over the last L one-minute candles, a FOLLOWER series in the same close window whose quote has not yet moved the same way is slow. Buy the follower side aligned with the leader's move and sell it at the bid k minutes later (a TIME exit; settlement is never used, so this is not a favourite-and-hold). Bitcoin, Ethereum and Dogecoin are declined as strategy markets (STRATEGY_LIFECYCLE 7e), so they are leaders only (information), never followers.

## Pairs (fixed now, 19)
Leaders BTC and ETH to followers XRP, SOL, HYPE, BNB, NEAR, ZEC (12 pairs). Non-crypto: gold->silver, silver->platinum, platinum->palladium, gold->copper, WTI->natural gas, EUR/USD->GBP/USD, GBP/USD->EUR/USD (7 pairs).

## Rule (fixed now)
- Decision candle: the candle ending E minutes before the shared close_ts (exact, tolerance 8 s), E in {10, 8, 6}.
- Leader move = leader mid(decision) minus leader mid(decision minus L minutes), mid = (bid_c + ask_c) / 2, L in {2, 3}. Fires when |move| >= m, m in {0.03, 0.06, 0.10}. Up means buy follower YES, down means buy follower NO.
- Follower not yet moved: the follower's own mid change over the same L minutes, signed in the leader's direction, is below m / 2 (a follower that already moved is skipped).
- Entry: at the candle ask for YES, 1 minus the candle bid for NO (conservative, the far side of the book). Entry price must be 0.20 to 0.80 and spread (ask - bid) at most 0.05.
- Exit: the candle ending k minutes after the decision candle, k in {2, 3, 4}; sell at its bid (YES) or 1 minus its ask (NO) (conservative). A missing candle skips the trade.
- Cash PnL per contract = sale - entry - fee(entry) - fee(sale), fee(p) = 0.07 p (1 - p), unrounded.
- Grid: 3 m x 2 L x 3 E x 3 k = 54 combos per pair x 19 pairs = 1026 cells, all counted into N. Shared N for the Bonferroni bar is about 1,100,000 (z 5.34); the bar at N 8,795 (z 4.39) is also reported.
- Split per follower series by follower close time: first two thirds development, last third held out. Held out is read ONCE, only for cells that pass development.
- Gate (development, then held out): cash PF >= 1.5 AND n >= 150 AND z (mean / standard error of per trade cash PnL) above the Bonferroni bar. n < 150 is NOT_ENOUGH_DATA. A survivor must pass the same gate on the held-out third (z judged against the bar for its own n; stated plainly in the result).
- Caveat stated in advance: trades in the same window across cells and pairs are heavily overlapping, so z is optimistic.

## Result (script src/scalper/leadlag1.py, development only; held out unread because nobody passed)

117,560 settled markets loaded. 1026 cells (19 pairs x 54), all counted. Gate counts on development:

| Gate | Cells passing |
|---|---|
| any trade | 1026 |
| n >= 150 | 894 (132 NOT_ENOUGH_DATA) |
| and cash PF >= 1.5 | 0 |
| and z > 4.39 | 0 |
| and z > 5.34 | 0 |

Only 6 of 894 cells with n >= 150 had a positive mean; the best PF is 1.09 (z 0.68). Fills at the far side of the book are conservative, and the cost of crossing twice is the likely reason the aligned follower never pays.

Best dev cell per pair (m, lookback, entry minute, exit k):

| Pair | Cell | n | cash PF | mean | z | days |
|---|---|---|---|---|---|---|
| GOLD->SILVER | 0.06,2,6,3 | 320 | 1.09 | +0.0098 | 0.68 | 51 |
| ETH->BNB | 0.10,2,6,4 | 315 | 1.07 | +0.0095 | 0.53 | 62 |
| ETH->XRP | 0.06,3,8,3 | 436 | 0.97 | -0.0034 | -0.29 | 43 |
| BTC->XRP | 0.10,2,6,4 | 181 | 0.95 | -0.0071 | -0.28 | 42 |
| ETH->NEAR | 0.10,2,6,4 | 238 | 0.93 | -0.0107 | -0.46 | 58 |
| EURUSD->GBPUSD | 0.03,3,10,3 | 180 | 0.85 | -0.0136 | -0.90 | 23 |
| ETH->HYPE | 0.10,2,6,4 | 379 | 0.87 | -0.0218 | -1.22 | 60 |
| BTC->SOL | 0.10,2,10,4 | 216 | 0.80 | -0.0242 | -1.37 | 45 |
| PLATINUM->PALLADIUM | 0.03,2,6,3 | 173 | 0.80 | -0.0191 | -1.21 | 25 |
| BTC->NEAR | 0.06,2,6,4 | 327 | 0.82 | -0.0295 | -1.55 | 57 |
| BTC->BNB | 0.10,2,6,4 | 297 | 0.79 | -0.0335 | -1.74 | 61 |
| ETH->SOL | 0.10,2,6,4 | 164 | 0.82 | -0.0303 | -1.14 | 44 |
| SILVER->PLATINUM | 0.03,3,8,4 | 199 | 0.71 | -0.0352 | -2.04 | 24 |
| BTC->HYPE | 0.10,2,8,4 | 495 | 0.79 | -0.0303 | -2.31 | 61 |
| ETH->ZEC | 0.10,2,6,4 | 271 | 0.72 | -0.0468 | -2.31 | 57 |
| BTC->ZEC | 0.10,3,8,4 | 468 | 0.76 | -0.0339 | -2.46 | 59 |
| GOLD->COPPER | 0.06,2,6,3 | 358 | 0.73 | -0.0317 | -2.46 | 42 |
| WTI->NATGAS | 0.10,2,10,4 | 630 | 0.72 | -0.0317 | -3.47 | 46 |
| GBPUSD->EURUSD | 0.03,3,10,4 | 171 | 0.56 | -0.0592 | -3.18 | 23 |

Verdict: FALSIFIED. No cell passes development, so the held-out third was never read. The follower does not reprice in the leader's direction within 2 to 4 minutes by more than the round trip spread and fees.
