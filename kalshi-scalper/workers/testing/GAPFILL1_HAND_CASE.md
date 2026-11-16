# GAPFILL1 hand case, written BEFORE any code (Testing Desk, Nov 16, 2026)
One invented series; entry candle ends at C - 600; b/a = YES bid / YES ask there; strikes invented.
| M | close C | step from previous close | strike | role | b/a at C-600 | result | outcome |
|---|---|---|---|---|---|---|---|
| M1 | 900 | start | 100.0 | pre-halt reference | n/a | yes | not traded (not K1 or K2) |
| M2 | 3600 | 2700, halt | 101.0 | K1, gap +1.0 vs 100.0, buy NO | 0.48 / 0.50 (NO ask 0.52) | no | trade, win |
| M3 | 4500 | 900 | 101.4 | K2 (close = K1 + 900), gap +1.4 vs 100.0, buy NO | 0.58 / 0.60 (NO ask 0.42) | yes | trade, loss |
| M4 | 5400 | 900 | 101.0 | third window, not counted; last before the next halt, so the reference | n/a | no | not traded |
| M5 | 9000 | 3600, halt | 99.0 | K1, gap -2.0 vs 101.0, buy YES | 0.60 / 0.62 (YES ask 0.62) | yes | trade, win |
| M6 | 9900 | 900 | 98.5 | K2, gap -2.5 vs 101.0, buy YES | 0.70 / 0.72 (YES ask 0.72) | yes | skip band |
| M7 | 14400 | 4500, halt | 98.5 | K1, gap 0 vs 98.5 (M6 strike) | 0.48 / 0.50 | no | skip zero gap |
| M8 | 15300 | 900 | 98.8 | K2, gap +0.3 vs 98.5 | no candle ending at 14700 | no | skip no_candle |
| M9 | 18000 | 2700, halt | missing | K1, strike missing | 0.48 / 0.50 | yes | skip no_strike |
| M10 | 19800 | 1800, halt (exactly 1800 counts) | 99.0 | K1, reference = M9's strike, missing | 0.48 / 0.50 | no | skip no_strike |
| M11 | 21599 | 1799, not a halt | 100.0 | ordinary window | 0.48 / 0.50 | yes | not traded |
Counts: trades 3; skips band 1, zero gap 1, no_candle 1, no_strike 2.
Fee: fee_up_order(p, 10) = ceil(round(70 p (1-p), 9)) / 100: p 0.52, 0.53, 0.54, 0.42, 0.43, 0.44 fee 0.18; p 0.62, 0.63, 0.64 fee 0.17.
Cash h0 / +1c / +2c: M2 win NO +4.62 / +4.52 / +4.42; M3 loss NO -4.38 / -4.48 / -4.58; M5 win YES +3.63 / +3.53 / +3.43.
Net +3.87 / +3.57 / +3.27 (n 3, wins 2). PF 8.25/4.38 = 1.8836; 8.05/4.48 = 1.7969; 7.85/4.58 = 1.7140.
Halves floor(3/2) = 1 by close: half 1 = M2 (infinite); half 2 = M3, M5: PF 3.63/4.38 = 0.8288; 3.53/4.48 = 0.7879; 3.43/4.58 = 0.7489.
Day z at +2c with M2, M3 on day 1 and M5 on day 2: sums -0.16 and +3.43, mean 1.635, se 3.59/2 = 1.795, z = 0.9109.
