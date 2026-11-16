# SERIAL1 hand case, written BEFORE any code (Testing Desk, Nov 16, 2026)
One invented series; window k closes at C; entry candle ends at C - 600; b/a = YES bid / YES ask close there.
| W | close C | previous window | b/a at C-600 | result | outcome |
|---|---|---|---|---|---|
| W1 | 900 | none | 0.48 / 0.50 | yes | skip no_prev |
| W2 | 1800 | W1 yes | 0.48 / 0.50 | no | C: YES ask 0.50, loss. F: NO ask 1 - 0.48 = 0.52, win |
| W3 | 2700 | W2 no | 0.60 / 0.62 | no | C: NO ask 1 - 0.60 = 0.40, win. F: YES ask 0.62, loss |
| W4 | 3600 | W3 no | 0.80 / 0.82 | no | C: NO ask 0.20 out of band, skip. F: YES ask 0.82, skip |
| W5 | 5400 | none (no window closes at 4500) | 0.48 / 0.50 | yes | skip no_prev |
| W6 | 6300 | W5 yes | 0.38 / 0.40 | yes | C: YES ask 0.40, win. F: NO ask 0.62, loss |
| W7 | 7200 | W6 yes | no candle ending at 6600 | yes | skip no_candle |
| W8 | 8100 | W7 void (not yes or no) | 0.48 / 0.50 | void | skip no_prev |
Counts: no_prev 3, no_candle 1, out of band 1 (variant C and F each). A candle ending after its market's close, if present, is dropped first.
Fee: fee_up_order(p, 10) = ceil(round(70 p (1-p), 9)) / 100: p 0.50, 0.51, 0.52, 0.53, 0.54 fee 0.18; p 0.40, 0.41 fee 0.17; p 0.42 fee 0.18; p 0.62, 0.63, 0.64 fee 0.17.
## Variant C (continuation): trades W2, W3, W6 (n 3, wins 2)
Cash h0 / +1c / +2c: W2 loss -5.18 / -5.28 / -5.38; W3 win +5.83 / +5.73 / +5.62; W6 win +5.83 / +5.73 / +5.62.
Net +6.48 / +6.18 / +5.86. PF 11.66/5.18 = 2.2510; 11.46/5.28 = 2.1705; 11.24/5.38 = 2.0892.
Halves floor(3/2) = 1 by close: half 1 = W2 (PF 0, net -5.18 / -5.28 / -5.38), half 2 = W3, W6 (PF infinite).
Day z at +2c with W2 on day 1 and W3, W6 on day 2: day sums -5.38 and +11.24; mean 2.93; sd 16.62/sqrt2; z = 2.93 / (16.62/2) = 0.3526.
## Variant F (fade): trades W2, W3, W6 (n 3, wins 1)
Cash h0 / +1c / +2c: W2 win +4.62 / +4.52 / +4.42; W3 loss -6.37 / -6.47 / -6.57; W6 loss -6.37 / -6.47 / -6.57.
Net -8.12 / -8.42 / -8.72. PF 4.62/12.74 = 0.3626; 4.52/12.94 = 0.3493; 4.42/13.14 = 0.3364.
Halves: half 1 = W2 (infinite), half 2 = W3, W6 (PF 0).
