# OIREL 8c-or-more split: hand case, written BEFORE the code (Idea Desk A, Nov 15, 2026; the Head's yes of 15:25Z: same landed file, same rule, no new try, information only, print once committed blind, after FLIPS0-X)
What it is: the OIREL haircut recompute (OIREL_HAND_CASE_NOV15.md, reader oirel_haircut.py, extract sha 53f2f8c3...) restricted to trades whose FILL price, the ask of the bought side on the candle ending 120 s before the close (the OIREL1 row's price in the shadow spec), is 0.08 or more (OICORE's own entry floor, SLOT_SKIP_BELOW), inclusive with a 1e-9 tolerance; and the full 5c to 50c band beside it. Everything else (rule, haircut at price + h, per-order rounded fee, halves floor(n/2) by fill order, candles after the close dropped) is unchanged. Nothing new is tried.
## Invented windows: the nine of the OIREL hand case (W1 to W9, unchanged) plus two
| W | oi at C-360 | oi at C-180 | b/a at C-180 | b/a at C-120 | result | expected |
|---|---|---|---|---|---|---|
| T1 | 1000 | 1300 | 0.05 / 0.06 | 0.06 / 0.07 | yes | YES, fill ask 0.07: in the full band, NOT in the 8c-or-more subset |
| T2 | 1000 | 1300 | 0.07 / 0.08 | 0.07 / 0.08 | no | YES, fill ask 0.08 (on the line): in both, loss |
Window times: W k closes at base + 900 k for k = 1 to 9, T1 at k = 10, T2 at k = 11.
## Expected, by hand (fee_up_order(price, 10))
T1: raw price 0.07, fee 0.05, cash +9.25; +1c price 0.08, fee 0.06, +9.14; +2c price 0.09, fee 0.06, +9.04.
T2: raw price 0.08, fee 0.06, cash -0.86; +1c price 0.09, fee 0.06, -0.96; +2c price 0.10, fee 0.07, -1.07.
**Subset 8c or more** (W1, W3, W4, W6, W9, T2): wins +7.36, +7.67, +5.52, +7.88 and losses -3.15 (W4), -0.86 (T2); n 6, 4 wins, 2 losses. Raw net +24.42, PF 28.43 / 4.01 = 7.0898; +1c net +23.82, PF 28.03 / 4.21 = 6.6580; +2c net +23.19, PF 27.62 / 4.43 = 6.2349. Halves floor(6/2) = 3 by fill order: half 1 = W1, W3, W4: raw 15.03 / 3.15 = 4.7714, +1c 14.83 / 3.25 = 4.5631, +2c 14.63 / 3.36 = 4.3542; half 2 = W6, W9, T2: raw 13.40 / 0.86 = 15.5814, +1c 13.20 / 0.96 = 13.75, +2c 12.99 / 1.07 = 12.1402.
**Full band** (adds T1, which closes between W9 and T2): n 7, 5 wins, 2 losses. Raw net +33.67, PF 37.68 / 4.01 = 9.3965; +1c net +32.96, PF 37.17 / 4.21 = 8.8290; +2c net +32.23, PF 36.66 / 4.43 = 8.2754. Halves floor(7/2) = 3 and 4: half 1 = W1, W3, W4 (same as above); half 2 = W6, W9, T1, T2: raw 22.65 / 0.86 = 26.3372.
