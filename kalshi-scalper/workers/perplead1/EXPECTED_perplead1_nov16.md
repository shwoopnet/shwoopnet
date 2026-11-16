# PERPLEAD1 scorer: expected figures, written BEFORE the code (Desk B, Nov 16, 2026)

Scope: the pure scoring functions only (no file read, no allow line); the loader that reads the ladder files and the perp candle runs comes after the pull jobs land and Auditor B has cleared the design (the card, specs/PERPLEAD1_CARD.md).

## Functions
- `implied_median(strike_mids)`: strikes sorted ascending with YES mids; the FIRST adjacent pair (k1 < k2) with mid(k1) >= 0.5 > mid(k2) gives k = k1 + (mid(k1) - 0.5) / (mid(k1) - mid(k2)) * (k2 - k1); no such pair, or fewer than 2 strikes: None (no signal).
- `gap_bps(median, perp_mid, scale)` = 1e4 * (median / (perp_mid * scale) - 1).
- `trade(side_dir, entry_bid, entry_ask, exit_bid, exit_ask, fee_bps)`: long buys at the entry ASK and sells at the exit BID; short sells at the entry BID and buys at the exit ASK; net bps = 1e4 * dir * (exit - entry) / entry - fee_bps (entry price of the leg that was opened).
- `score_rule(events, theta, exit_key, direction, fee_bps)`: one trade per event with a signal and |gap| >= theta; convergence goes with the sign of the gap (gap > 0: long), fade goes against it; a missing entry or exit candle: no trade, counted.
- `summary(nets, days)`: n, days, mean net bps, profit factor = sum of positive nets / sum of absolute negative nets (inf if no losses, nan if no trades).
- `margin_print(mean_net_bps)`: for leverage shares 10%, 25%, 50% of Lmax = 1 / 0.045: leverage 2.2222, 5.5556, 11.1111; margin fraction 0.45, 0.18, 0.09; return on margin % = mean_net_bps / (1e4 * margin fraction) * 100; liquidation distance % of notional = (margin fraction - 0.045) * 100 = 40.5, 13.5, 4.5.

## Hand cases (scale 1, the ETH perp mid 2000.00 = bid 1999.9, ask 2000.1 at the entry candle; theta 4 bps, exit key "m60", convergence, taker fee 24 bps)
- A: strikes 1990 (mid 0.9) and 2010 (mid 0.3): median 1990 + (0.9 - 0.5) / (0.9 - 0.3) * 20 = 2003.3333; gap = +16.667 bps; long at ask 2000.1; exit bid 2001.0: gross 4.4998 bps, net -19.5002.
- B: strikes 1990 (0.6) and 2000 (0.4): median 1995.0; gap = -25.0 bps; short at bid 1999.9; exit ask 1996.0: gross 19.5010 bps, net -4.4990.
- C: strikes 1990 (0.9), 2010 (0.3) as A: gap +16.667; long at ask 2000.1; exit bid 2008.0: gross 39.4980 bps, net +15.4980.
- D: strikes 1999 (0.52) and 2001 (0.48): median 2000.0; gap 0.0: no trade (under theta).
- E: strikes 1990 (0.9) and 2010 (0.8): no bracketing pair: no signal.
- F: strikes as A but the exit candle is missing: no trade, counted as "exit candle missing".
Exit candles (bid, ask): A (2001.0, 2001.2); B (1995.8, 1996.0); C (2008.0, 2008.2). (The convergence exits above use A bid 2001.0, B ask 1996.0, C bid 2008.0.)
Expected (convergence): 3 trades (A, B, C); nets -19.5002, -4.4990, +15.4980; mean net -2.8337 bps; PF = 15.4980 / 23.9992 = 0.6458; n 3; counts: no signal 1 (E), under theta 1 (D), exit missing 1 (F).
Fade on the same events: A short at bid 1999.9, buy back at ask 2001.2: gross -6.5003, net -30.5003; B long at ask 2000.1, sell at bid 1995.8: gross -21.4989, net -45.4989; C short at bid 1999.9, buy back at ask 2008.2: gross -41.5021, net -65.5021; PF 0.0 (no winners).
Margin print for mean net -2.8337 bps: return on margin = mean / (1e4 x fraction) x 100 = -0.0630%, -0.1574%, -0.3149% at margin fraction 0.45, 0.18, 0.09; liquidation distance 40.5, 13.5, 4.5 % of notional.
Split rule: closes on 19 distinct dates: the first floor(19/2) = 9 are SEARCH, the other 10 VALIDATE.
