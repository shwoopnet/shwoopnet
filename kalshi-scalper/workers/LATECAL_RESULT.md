# LATECAL result (V2 worker, 2026-10-29, research only)

Registration `workers/LATECAL_REGISTRATION.md` (commit 63804e0, pushed before any outcome was read). Ledger check `workers/LATECAL_CHECK.md`. Scorer `workers/LATECAL_score.py`, data `origin/quote-data` at b7dc9cbe8. Nothing in the cells, bands, rule or bar changed after scoring.

## Part 1: T1 + T2 (selection set), written and pushed before T3 was read

Gold: 58 windows with polls, 57 with a result, thirds 19 / 19 / 19 (T3 from 2026-10-29 06:30Z). Bitcoin: 257 with polls, 256 with a result, thirds 86 / 85 / 85 (T3 from 2026-10-27 17:45Z). Gap = win rate minus mean ask; PF and net after the fee rounded up per order at 1 and 10 contracts.

```
== T1+T2 (selection set) ==
gold    120- 90s ask 0.50-0.80  n   11 win 0.636 ask 0.667 gap  -3.09pt z -0.22 PF1  0.79 net1  -5.09c PF10  0.81 net10  -4.63c  T1gap -14.62 T2gap +27.67 NOT_ENOUGH_DATA
gold    120- 90s ask 0.80-0.90  n   10 win 0.800 ask 0.839 gap  -3.90pt z -0.34 PF1  0.68 net1  -5.30c PF10  0.70 net10  -4.89c  T1gap -23.40 T2gap +15.60 NOT_ENOUGH_DATA
gold    120- 90s ask 0.90-0.95  n    8 win 1.000 ask 0.919 gap  +8.06pt z +0.84 PF1   inf net1  +7.06c PF10   inf net10  +7.47c  T1gap +7.32 T2gap +8.80 NOT_ENOUGH_DATA
gold    120- 90s ask 0.95-0.98  n    8 win 1.000 ask 0.964 gap  +3.59pt z +0.55 PF1   inf net1  +2.59c PF10   inf net10  +3.30c  T1gap +3.48 T2gap +3.77 NOT_ENOUGH_DATA
gold     90- 60s ask 0.50-0.80  n    8 win 0.625 ask 0.671 gap  -4.63pt z -0.28 PF1  0.73 net1  -6.63c PF10  0.75 net10  -6.16c  T1gap -15.00 T2gap +26.50 NOT_ENOUGH_DATA
gold     90- 60s ask 0.80-0.90  n    8 win 0.750 ask 0.840 gap  -9.00pt z -0.70 PF1  0.50 net1 -10.37c PF10  0.52 net10  -9.97c  T1gap -23.20 T2gap +14.67 NOT_ENOUGH_DATA
gold     90- 60s ask 0.90-0.95  n    4 win 1.000 ask 0.923 gap  +7.70pt z +0.58 PF1   inf net1  +6.70c PF10   inf net10  +7.15c  T1gap +nan T2gap +7.70 NOT_ENOUGH_DATA
gold     90- 60s ask 0.95-0.98  n    5 win 1.000 ask 0.967 gap  +3.30pt z +0.41 PF1   inf net1  +2.30c PF10   inf net10  +3.04c  T1gap +3.05 T2gap +4.30 NOT_ENOUGH_DATA
gold     60- 30s ask 0.50-0.80  n    9 win 0.667 ask 0.698 gap  -3.11pt z -0.21 PF1  0.77 net1  -5.11c PF10  0.79 net10  -4.58c  T1gap -1.29 T2gap -9.50 NOT_ENOUGH_DATA
gold     60- 30s ask 0.80-0.90  n    6 win 1.000 ask 0.822 gap +17.83pt z +1.14 PF1   inf net1 +16.33c PF10   inf net10 +16.77c  T1gap +19.00 T2gap +16.67 NOT_ENOUGH_DATA
gold     60- 30s ask 0.90-0.95  n    6 win 1.000 ask 0.923 gap  +7.72pt z +0.71 PF1   inf net1  +6.72c PF10   inf net10  +7.17c  T1gap +6.80 T2gap +7.90 NOT_ENOUGH_DATA
gold     60- 30s ask 0.95-0.98  n    5 win 1.000 ask 0.973 gap  +2.74pt z +0.38 PF1   inf net1  +1.74c PF10   inf net10  +2.50c  T1gap +2.40 T2gap +3.25 NOT_ENOUGH_DATA
gold     30- 10s ask 0.50-0.80  n    4 win 0.750 ask 0.705 gap  +4.50pt z +0.20 PF1  1.13 net1  +2.50c PF10  1.16 net10  +3.05c  T1gap +4.50 T2gap +nan NOT_ENOUGH_DATA
gold     30- 10s ask 0.80-0.90  n    4 win 0.750 ask 0.850 gap -10.00pt z -0.56 PF1  0.48 net1 -11.00c PF10  0.49 net10 -10.92c  T1gap -33.50 T2gap +13.50 NOT_ENOUGH_DATA
gold     30- 10s ask 0.90-0.95  n    4 win 1.000 ask 0.918 gap  +8.20pt z +0.60 PF1   inf net1  +7.20c PF10   inf net10  +7.60c  T1gap +9.60 T2gap +7.73 NOT_ENOUGH_DATA
gold     30- 10s ask 0.95-0.98  n    6 win 1.000 ask 0.969 gap  +3.13pt z +0.44 PF1   inf net1  +2.13c PF10   inf net10  +2.87c  T1gap +2.67 T2gap +3.60 NOT_ENOUGH_DATA
bitcoin 120- 90s ask 0.50-0.80  n   40 win 0.625 ask 0.659 gap  -3.38pt z -0.46 PF1  0.79 net1  -5.38c PF10  0.80 net10  -4.94c  T1gap +1.91 T2gap -9.83
bitcoin 120- 90s ask 0.80-0.90  n   36 win 0.861 ask 0.844 gap  +1.69pt z +0.28 PF1  1.03 net1  +0.39c PF10  1.06 net10  +0.74c  T1gap +11.22 T2gap -15.15
bitcoin 120- 90s ask 0.90-0.95  n   42 win 0.857 ask 0.920 gap  -6.30pt z -1.51 PF1  0.45 net1  -7.30c PF10  0.48 net10  -6.86c  T1gap -2.23 T2gap -9.66
bitcoin 120- 90s ask 0.95-0.98  n   44 win 0.977 ask 0.967 gap  +1.07pt z +0.40 PF1  1.03 net1  +0.07c PF10  1.37 net10  +0.80c  T1gap +3.52 T2gap -0.62
bitcoin  90- 60s ask 0.50-0.80  n   29 win 0.621 ask 0.661 gap  -4.00pt z -0.46 PF1  0.76 net1  -6.00c PF10  0.78 net10  -5.59c  T1gap +7.13 T2gap -17.69 NOT_ENOUGH_DATA
bitcoin  90- 60s ask 0.80-0.90  n   22 win 0.818 ask 0.859 gap  -4.05pt z -0.55 PF1  0.67 net1  -5.23c PF10  0.69 net10  -4.93c  T1gap +7.67 T2gap -29.14 NOT_ENOUGH_DATA
bitcoin  90- 60s ask 0.90-0.95  n   34 win 0.882 ask 0.922 gap  -3.93pt z -0.85 PF1  0.55 net1  -4.93c PF10  0.59 net10  -4.48c  T1gap +2.61 T2gap -12.21
bitcoin  90- 60s ask 0.95-0.98  n   38 win 1.000 ask 0.966 gap  +3.42pt z +1.16 PF1   inf net1  +2.42c PF10   inf net10  +3.14c  T1gap +3.45 T2gap +3.37 CHOSEN
bitcoin  60- 30s ask 0.50-0.80  n   15 win 0.667 ask 0.687 gap  -2.00pt z -0.17 PF1  0.82 net1  -4.00c PF10  0.84 net10  -3.51c  T1gap +16.67 T2gap -14.44 NOT_ENOUGH_DATA
bitcoin  60- 30s ask 0.80-0.90  n   14 win 0.929 ask 0.849 gap  +8.00pt z +0.84 PF1  2.15 net1  +6.71c PF10  2.22 net10  +7.09c  T1gap +15.60 T2gap +3.78 NOT_ENOUGH_DATA
bitcoin  60- 30s ask 0.90-0.95  n   14 win 1.000 ask 0.923 gap  +7.68pt z +1.08 PF1   inf net1  +6.68c PF10   inf net10  +7.12c  T1gap +7.47 T2gap +8.06 NOT_ENOUGH_DATA
bitcoin  60- 30s ask 0.95-0.98  n   26 win 1.000 ask 0.965 gap  +3.48pt z +0.97 PF1   inf net1  +2.48c PF10   inf net10  +3.20c  T1gap +3.56 T2gap +3.29 NOT_ENOUGH_DATA
bitcoin  30- 10s ask 0.50-0.80  n    4 win 0.750 ask 0.653 gap  +9.75pt z +0.42 PF1  1.54 net1  +7.75c PF10  1.58 net10  +8.20c  T1gap -14.50 T2gap +34.00 NOT_ENOUGH_DATA
bitcoin  30- 10s ask 0.80-0.90  n    3 win 1.000 ask 0.867 gap +13.33pt z +0.68 PF1   inf net1 +12.33c PF10   inf net10 +12.50c  T1gap +12.50 T2gap +15.00 NOT_ENOUGH_DATA
bitcoin  30- 10s ask 0.90-0.95  n    2 win 1.000 ask 0.940 gap  +6.05pt z +0.36 PF1   inf net1  +5.05c PF10   inf net10  +5.60c  T1gap +5.40 T2gap +6.70 NOT_ENOUGH_DATA
bitcoin  30- 10s ask 0.95-0.98  n    8 win 1.000 ask 0.967 gap  +3.31pt z +0.52 PF1   inf net1  +2.31c PF10   inf net10  +3.04c  T1gap +3.20 T2gap +3.38 NOT_ENOUGH_DATA

chosen: [('bitcoin', ' 90- 60s ask 0.95-0.98')]
```

**Chosen by the registered screen (gap at least +3 points on T1 + T2, positive in each, at least 30 windows): one cell, Bitcoin, 90 to 60 s left, ask 0.95 to 0.98** (38 windows, 38 wins, mean ask 0.966, +3.42 points, z +1.16). As predicted, the one cell to pass is a 0.95 to 0.98 band where "no loss yet" makes the gap equal to 1 minus the price; z +1.16 is no evidence. Every gold cell is NOT_ENOUGH_DATA (at most 11 windows on T1 + T2). Of the 32 cells only 7 Bitcoin cells reach 30 windows; the late Bitcoin cells (30 to 10 s) hold 2 to 8 windows, because the book is one-sided by then (BTCAVG: 72% at 30 s).
