# INPLAY1 result (run once 2026-11-03; games before the frozen cut 2026-10-03T16:00Z only): NOT_ENOUGH_DATA, and the 30 trades all lost

Registration `INPLAY1_REGISTRATION.md` (pushed before any join). Code `src/scalper/inplay1.py`, tests `tests/test_inplay1.py`, output `data/inplay1_result.txt`. Cheap side only; no favourite-side result computed. Frozen W3 not read.

| | n | win | mean ask | mean ESPN p | mean net (C=10) | PF |
|---|---|---|---|---|---|---|
| W1 | 9 | 0.000 | 0.063 | 0.258 | -6.80c | 0.00 |
| W2 | 21 | 0.000 | 0.083 | 0.332 | -8.86c | 0.00 |
| W1+W2 | 30 | 0.000 | 0.077 | 0.310 | -8.24c (x1.2: -8.35c) | 0.00 |
| Control, all cheap sides at the looks | 1,388 | 0.126 | 0.144 | 0.165 | -2.64c | 0.79 |

Games 920 (college football 525, MLB 395). Ratio rule hit 30 games (college football 24, MLB 6), against the kill bar of 150: **NOT_ENOUGH_DATA**. At about 15 treated trades a month of games (season dependent, the football and MLB seasons end soon) 120 more trades is about 8 months. The two halves (15 and 15) are both negative, so if it ever reached 150 it would be FALSIFIED on the present direction (0 wins of 30 at a mean ask of 7.7c; the chance of 0 of 30 at those prices is about 8%, a mild result, not a finding).

Reading: when ESPN says 3x or more of the ask, the Kalshi mid is right: on the 38 rows with that ratio, Brier ESPN 0.1137 against Kalshi mid 0.0069 (Kalshi's price is nearly exact; ESPN's is the error). Over all 1,388 cheap-side rows ESPN Brier 0.1087 vs Kalshi 0.1006. Control cheap sides win 12.6% against a 14.4% ask (the ordinary longshot bias, same as SWING1 and BOOKS1). The prediction (10 to 40 trades, net -2c to -5c) was right on count and too mild on net.

Forward plan: none worth a recorder. The same rule scored from 2026-10-03T16:00Z on the games already on file would add roughly 10 trades and is not read (frozen). No probe spec. **N: +2.** Running count about 730,291.
