# OICORE on every market, second build: hand case (Testing Desk, Nov 17 2026), written BEFORE the code was run

Series S. Closes are epoch seconds; the oi pair for a window is the candle ending close-360 (level) and close-180 (signal candle). Floor of 10 SEARCH rises for this case only (floor_n=10); the real floor is 20.
SEARCH: ten windows A1..A10 with rises 1..10 (level 100, signal 100+r), plus A11 whose close-360 candle is absent (no candle, left out of T). T = nearest rank 0.9 of ten = the 9th smallest = 9. Fires when rise >= 9.
VALIDATE (two calendar days, so days = 2):
- V1 rise 9 (equals T, fires). Signal candle yes bid .28 ask .30 (NO ask .72): YES, cheaper; price = this candle's ask .30 (the Head's O5: side AND price on the candle ending close-180; the fill candle is not read). Result yes. h=1c: price .31, fee ceil(.7 x .31 x .69 x 100 = 14.973) = 15c per order of 10, .015 a contract, net 1 - .31 - .015 = .675. h=2c: price .32, 15.232 -> 16, net 1 - .32 - .016 = .664.
- V2 rise 10. Signal yes bid .68 ask .70 (NO ask .32): NO, cheaper, price .32. Result yes (NO loses). h=1c: .33, 15.477 -> 16, net -.33 - .016 = -.346. h=2c: .34, 15.708 -> 16, net -.356.
- V3 rise 8 < T: no fire, not counted anywhere.
- V4 rise 12, signal yes ask .04 (cheaper YES), fill ask .04: below the 8c floor: no signal (band), counted.
- V5 rise 11 but its close-360 candle absent: no candle, counted.
- V6 rise 9. Signal yes bid .48 ask .50 (NO ask .52): YES. Fill yes_ask .50 (inclusive band). Result no. h=1c: .51, .7 x .51 x .49 x 100 = 17.493 -> 18, net -.51 - .018 = -.528. h=2c: .52, 17.472 -> 18, net -.52 - .018 = -.538.
VALIDATE: n 3, wins 1, days 2, signals a day 1.5. PF 1c = .675 / (.346 + .528) = .675 / .874. PF 2c = .664 / (.356 + .538) = .664 / .894. Net cents 1c = 100 x (.675 - .346 - .528) / 3 = -6.6333...; 2c = 100 x (.664 - .356 - .538) / 3 = -7.6667...
HELD (one day): H1 rise 20, signal yes bid .18 ask .20, price .20, result yes. h=1c .21: .7 x .21 x .79 x 100 = 11.613 -> 12, net 1 - .21 - .012 = .778; h=2c .22: 12.012 -> 13, net 1 - .22 - .013 = .767. n 1, wins 1, no losing trade so PF is null, net cents 77.8 and 76.7, signals a day 1.
No-signal counts VALIDATE+HELD: no_candle 1, band 1.
