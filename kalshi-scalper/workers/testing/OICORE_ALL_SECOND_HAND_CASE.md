# OICORE on every market, second build: hand case (Testing Desk, Nov 17 2026), written BEFORE the code was run

Series S. Closes are epoch seconds; the oi pair for a window is the candle ending close-360 (level) and close-180 (signal candle). Floor of 10 SEARCH rises for this case only (floor_n=10); the real floor is 20.
SEARCH: ten windows A1..A10 with rises 1..10 (level 100, signal 100+r), plus A11 whose close-360 candle is absent (no candle, left out of T). T = nearest rank 0.9 of ten = the 9th smallest = 9. Fires when rise >= 9.
VALIDATE (two calendar days, so days = 2):
- V1 rise 9 (equals T, fires). Signal candle yes bid .28 ask .30 (NO ask .72): YES, cheaper. Fill candle yes_ask .32. Result yes. h=1c: price .33, fee ceil(.7 x .33 x .67 x 100 = 15.477) = 16c per order of 10, .016 a contract, net 1 - .33 - .016 = .654. h=2c: price .34, 15.708 -> 16, net .644.
- V2 rise 10. Signal yes bid .68 ask .70 (NO ask .32): NO, cheaper. Fill candle yes bid .66 so NO ask .34. Result yes (NO loses). h=1c: .35, 15.925 -> 16, net -.35 - .016 = -.366. h=2c: .36, 16.128 -> 17, net -.36 - .017 = -.377.
- V3 rise 8 < T: no fire, not counted anywhere.
- V4 rise 12, signal yes ask .04 (cheaper YES), fill ask .04: below the 8c floor: no signal (band), counted.
- V5 rise 11 but its close-360 candle absent: no candle, counted.
- V6 rise 9. Signal yes bid .48 ask .50 (NO ask .52): YES. Fill yes_ask .50 (inclusive band). Result no. h=1c: .51, .7 x .51 x .49 x 100 = 17.493 -> 18, net -.51 - .018 = -.528. h=2c: .52, 17.472 -> 18, net -.52 - .018 = -.538.
VALIDATE: n 3, wins 1, days 2, signals a day 1.5. PF 1c = .654 / (.366 + .528) = .654 / .894. PF 2c = .644 / (.377 + .538) = .644 / .915. Net cents 1c = 100 x (.654 - .366 - .528) / 3 = -8; 2c = 100 x (.644 - .377 - .538) / 3 = -9.0333...
HELD (one day): H1 rise 20, signal yes bid .18 ask .20, fill ask .22, result yes. h=1c .23: .7 x .23 x .77 x 100 = 12.397 -> 13, net 1 - .23 - .013 = .757; h=2c .24: .7 x .24 x .76 x 100 = 12.768 -> 13, net .747. n 1, wins 1, no losing trade so PF is null (undefined), net cents 75.7 and 74.7, signals a day 1.
No-signal counts VALIDATE+HELD: no_candle 1, band 1.
