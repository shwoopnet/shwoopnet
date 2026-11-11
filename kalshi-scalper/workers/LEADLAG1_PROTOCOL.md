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
