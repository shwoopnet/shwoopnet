# ENDNET: the hand check of the "hand" fixture (MADE-UP rows, Nov 13, 2026)

Each game exercises one edge. The printed lines are in `EXPECTED_OUTPUT_MADE_UP_DATA.txt`; the arithmetic below was done by hand, not by the scorer.
Fee per contract = ceiling to the cent of (7% x p x (1 - p) x 10 contracts x 100) cents, over 10 contracts.

| game | what it tests | outcome |
|---|---|---|
| g01_win | total 5, line 5.5, bid 28 ask 30, YES | entry; pay 31; fee: .07 x 10 x .31 x .69 x 100 = 14.97 -> 15c on the order = 1.5c; pnl 1 - .31 - .015 = +0.675 |
| g02_loss | bid 38 ask 40, NO | entry; pay 41; fee 16.9 -> 17c = 1.7c; pnl -.41 - .017 = -0.427 |
| g03_two_goals | score 4 to 2 | no state minute (two goals apart) |
| g04_ask_50 | ask 50 | ask out of band |
| g05_spread_6 | bid 24 ask 30 | spread too wide |
| g06_no_candle | the candle ends one minute after the entry minute | no candle at the entry minute (nothing carried) |
| g07_two_away | total 5, line 6.5 | no strike one goal away |
| g08_period2 | period 2 | no state minute |
| g09_tied | 2 to 2 | no state minute |
| g10 | total 3, INTEGER line 3.0, bid 11 ask 15 (the lower edge of the band, spread exactly 4) | entry (floor - total = 0 qualifies); pay 16; fee 9.408 -> 10c = 1.0c; pnl 1 - .16 - .01 = +0.830 |
| g11 | total 3, line 3.5, bid 41 ask 45 (the upper edge) | entry; pay 46; fee 17.39 -> 18c = 1.8c; pnl -.46 - .018 = -0.478 |
| g12 | bid 0 | not two-sided |

Totals: entries 4 (g01, g02, g10, g11); skips: state 3, strike 1, candle 1, band 1, spread 1, two-sided 1 = 8, and 4 + 8 = 12 games.
Net = .675 - .427 + .830 - .478 = **+0.600**; wins 2; mean +0.150; gains 1.505 against losses 0.905: **cash PF 1.66**.
Halves (the second half starts 2026-12-01; g11 closes on 12-01, the others earlier): first half n 3, net +1.078, PF 1.505 / .427 = **3.52**; second half n 1, net -0.478, PF 0.00.
Median ask over (30, 40, 15, 45) = (30 + 40) / 2 = **35.0**; entries a week over 4 weeks = **1.00**, so stage 1 reads CLOSED on the week line (not on the ask line).
Verdict: NOT_ENOUGH_DATA (4 of 150).
The "pass" and "fail" fixtures are 160 identical-price games (ask 30, pay 31) with 106 and 40 wins: pass net = 106 x .675 - 54 x .325 = +54.000, PF 71.55 / 17.55 = 4.08; fail net = 40 x .675 - 120 x .325 = -12.000, PF 27 / 39 = 0.69. "outside" holds one game closing 2026-12-15: both commands stop.
