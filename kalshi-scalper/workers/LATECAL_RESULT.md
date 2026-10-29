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

## Part 2: T3 holdout, read once after Part 1 was pushed (f457e25)

```
== T3 (holdout) all cells, information ==
gold    120- 90s ask 0.50-0.80  n    2 win 1.000 ask 0.760 gap +24.00pt z +0.80 PF1   inf net1 +22.00c PF10   inf net10 +22.70c NOT_ENOUGH_DATA
gold    120- 90s ask 0.80-0.90  n    1 win 1.000 ask 0.830 gap +17.00pt z +0.45 PF1   inf net1 +16.00c PF10   inf net10 +16.00c NOT_ENOUGH_DATA
gold    120- 90s ask 0.90-0.95  n    3 win 1.000 ask 0.932 gap  +6.77pt z +0.47 PF1   inf net1  +5.77c PF10   inf net10  +6.27c NOT_ENOUGH_DATA
gold    120- 90s ask 0.95-0.98  n    6 win 1.000 ask 0.965 gap  +3.53pt z +0.47 PF1   inf net1  +2.53c PF10   inf net10  +3.25c NOT_ENOUGH_DATA
gold     90- 60s ask 0.50-0.80  n    3 win 0.667 ask 0.677 gap  -1.00pt z -0.04 PF1  0.84 net1  -3.00c PF10  0.86 net10  -2.53c NOT_ENOUGH_DATA
gold     90- 60s ask 0.80-0.90  n    1 win 1.000 ask 0.880 gap +12.00pt z +0.37 PF1   inf net1 +11.00c PF10   inf net10 +11.20c NOT_ENOUGH_DATA
gold     90- 60s ask 0.90-0.95  n    3 win 1.000 ask 0.920 gap  +8.00pt z +0.51 PF1   inf net1  +7.00c PF10   inf net10  +7.43c NOT_ENOUGH_DATA
gold     90- 60s ask 0.95-0.98  n    2 win 1.000 ask 0.964 gap  +3.65pt z +0.28 PF1   inf net1  +2.65c PF10   inf net10  +3.40c NOT_ENOUGH_DATA
gold     60- 30s ask 0.50-0.80  n    1 win 1.000 ask 0.770 gap +23.00pt z +0.55 PF1   inf net1 +21.00c PF10   inf net10 +21.70c NOT_ENOUGH_DATA
gold     60- 30s ask 0.80-0.90  n    1 win 1.000 ask 0.830 gap +17.00pt z +0.45 PF1   inf net1 +16.00c PF10   inf net10 +16.00c NOT_ENOUGH_DATA
gold     60- 30s ask 0.90-0.95  n 0 NOT_ENOUGH_DATA
gold     60- 30s ask 0.95-0.98  n    3 win 1.000 ask 0.977 gap  +2.33pt z +0.27 PF1   inf net1  +1.33c PF10   inf net10  +2.13c NOT_ENOUGH_DATA
gold     30- 10s ask 0.50-0.80  n 0 NOT_ENOUGH_DATA
gold     30- 10s ask 0.80-0.90  n    1 win 1.000 ask 0.880 gap +12.00pt z +0.37 PF1   inf net1 +11.00c PF10   inf net10 +11.20c NOT_ENOUGH_DATA
gold     30- 10s ask 0.90-0.95  n    1 win 1.000 ask 0.946 gap  +5.40pt z +0.24 PF1   inf net1  +4.40c PF10   inf net10  +5.00c NOT_ENOUGH_DATA
gold     30- 10s ask 0.95-0.98  n    1 win 1.000 ask 0.953 gap  +4.70pt z +0.22 PF1   inf net1  +3.70c PF10   inf net10  +4.30c NOT_ENOUGH_DATA
bitcoin 120- 90s ask 0.50-0.80  n   20 win 0.750 ask 0.667 gap  +8.30pt z +0.80 PF1  1.37 net1  +6.30c PF10  1.40 net10  +6.72c NOT_ENOUGH_DATA
bitcoin 120- 90s ask 0.80-0.90  n   23 win 0.957 ask 0.846 gap +11.09pt z +1.48 PF1  3.71 net1  +9.78c PF10  3.84 net10 +10.14c NOT_ENOUGH_DATA
bitcoin 120- 90s ask 0.90-0.95  n   27 win 0.963 ask 0.918 gap  +4.46pt z +0.85 PF1  1.99 net1  +3.46c PF10  2.12 net10  +3.89c NOT_ENOUGH_DATA
bitcoin 120- 90s ask 0.95-0.98  n   23 win 0.957 ask 0.965 gap  -0.87pt z -0.23 PF1  0.56 net1  -1.87c PF10  0.72 net10  -1.16c NOT_ENOUGH_DATA
bitcoin  90- 60s ask 0.50-0.80  n   18 win 0.667 ask 0.662 gap  +0.44pt z +0.04 PF1  0.93 net1  -1.56c PF10  0.95 net10  -1.11c NOT_ENOUGH_DATA
bitcoin  90- 60s ask 0.80-0.90  n   14 win 0.857 ask 0.854 gap  +0.36pt z +0.04 PF1  0.93 net1  -0.86c PF10  0.95 net10  -0.55c NOT_ENOUGH_DATA
bitcoin  90- 60s ask 0.90-0.95  n   21 win 0.857 ask 0.923 gap  -6.61pt z -1.14 PF1  0.43 net1  -7.61c PF10  0.46 net10  -7.16c NOT_ENOUGH_DATA
bitcoin  90- 60s ask 0.95-0.98  n   23 win 1.000 ask 0.968 gap  +3.15pt z +0.87 PF1   inf net1  +2.15c PF10   inf net10  +2.90c NOT_ENOUGH_DATA
bitcoin  60- 30s ask 0.50-0.80  n    9 win 0.556 ask 0.590 gap  -3.44pt z -0.21 PF1  0.80 net1  -5.44c PF10  0.81 net10  -5.13c NOT_ENOUGH_DATA
bitcoin  60- 30s ask 0.80-0.90  n    8 win 0.625 ask 0.865 gap -24.00pt z -1.99 PF1  0.23 net1 -25.12c PF10  0.24 net10 -24.85c NOT_ENOUGH_DATA
bitcoin  60- 30s ask 0.90-0.95  n    7 win 0.857 ask 0.930 gap  -7.30pt z -0.76 PF1  0.39 net1  -8.30c PF10  0.42 net10  -7.81c NOT_ENOUGH_DATA
bitcoin  60- 30s ask 0.95-0.98  n    7 win 1.000 ask 0.966 gap  +3.40pt z +0.50 PF1   inf net1  +2.40c PF10   inf net10  +3.13c NOT_ENOUGH_DATA
bitcoin  30- 10s ask 0.50-0.80  n    4 win 0.500 ask 0.585 gap  -8.50pt z -0.35 PF1  0.64 net1 -10.50c PF10  0.65 net10 -10.20c NOT_ENOUGH_DATA
bitcoin  30- 10s ask 0.80-0.90  n    3 win 0.667 ask 0.880 gap -21.33pt z -1.14 PF1  0.25 net1 -22.33c PF10  0.25 net10 -22.10c NOT_ENOUGH_DATA
bitcoin  30- 10s ask 0.90-0.95  n 0 NOT_ENOUGH_DATA
bitcoin  30- 10s ask 0.95-0.98  n    4 win 1.000 ask 0.966 gap  +3.43pt z +0.38 PF1   inf net1  +2.43c PF10   inf net10  +3.15c NOT_ENOUGH_DATA

== all thirds pooled, per cell (information) ==
gold    120- 90s ask 0.50-0.80  n   13 win 0.692 ask 0.682 gap  +1.08pt z +0.09 PF1  0.95 net1  -0.92c PF10  0.98 net10  -0.42c  | next-poll PF1  0.95 net1 -0.92c
gold    120- 90s ask 0.80-0.90  n   11 win 0.818 ask 0.838 gap  -2.00pt z -0.18 PF1  0.77 net1  -3.36c PF10  0.80 net10  -2.99c  | next-poll PF1  0.87 net1 -1.73c
gold    120- 90s ask 0.90-0.95  n   11 win 1.000 ask 0.923 gap  +7.71pt z +0.96 PF1   inf net1  +6.71c PF10   inf net10  +7.15c  | next-poll PF1   inf net1 +6.71c
gold    120- 90s ask 0.95-0.98  n   14 win 1.000 ask 0.964 gap  +3.56pt z +0.72 PF1   inf net1  +2.56c PF10   inf net10  +3.28c  | next-poll PF1   inf net1 +2.56c
gold     90- 60s ask 0.50-0.80  n   11 win 0.636 ask 0.673 gap  -3.64pt z -0.26 PF1  0.75 net1  -5.64c PF10  0.77 net10  -5.17c  | next-poll PF1  0.75 net1 -5.64c
gold     90- 60s ask 0.80-0.90  n    9 win 0.778 ask 0.844 gap  -6.67pt z -0.55 PF1  0.57 net1  -8.00c PF10  0.59 net10  -7.62c  | next-poll PF1  0.57 net1 -8.00c
gold     90- 60s ask 0.90-0.95  n    7 win 1.000 ask 0.922 gap  +7.83pt z +0.77 PF1   inf net1  +6.83c PF10   inf net10  +7.27c  | next-poll PF1   inf net1 +7.89c
gold     90- 60s ask 0.95-0.98  n    7 win 1.000 ask 0.966 gap  +3.40pt z +0.50 PF1   inf net1  +2.40c PF10   inf net10  +3.14c  | next-poll PF1   inf net1 +2.40c
gold     60- 30s ask 0.50-0.80  n   10 win 0.700 ask 0.705 gap  -0.50pt z -0.04 PF1  0.87 net1  -2.50c PF10  0.90 net10  -1.95c  | next-poll PF1  1.10 net1 +1.60c
gold     60- 30s ask 0.80-0.90  n    7 win 1.000 ask 0.823 gap +17.71pt z +1.23 PF1   inf net1 +16.29c PF10   inf net10 +16.66c  | next-poll PF1   inf net1 +16.43c
gold     60- 30s ask 0.90-0.95  n    6 win 1.000 ask 0.923 gap  +7.72pt z +0.71 PF1   inf net1  +6.72c PF10   inf net10  +7.17c  | next-poll PF1   inf net1 +6.72c
gold     60- 30s ask 0.95-0.98  n    8 win 1.000 ask 0.974 gap  +2.59pt z +0.46 PF1   inf net1  +1.59c PF10   inf net10  +2.36c  | next-poll PF1   inf net1 +1.59c
gold     30- 10s ask 0.50-0.80  n    4 win 0.750 ask 0.705 gap  +4.50pt z +0.20 PF1  1.13 net1  +2.50c PF10  1.16 net10  +3.05c  | next-poll PF1  1.71 net1 +13.75c
gold     30- 10s ask 0.80-0.90  n    5 win 0.800 ask 0.856 gap  -5.60pt z -0.36 PF1  0.61 net1  -6.60c PF10  0.62 net10  -6.50c  | next-poll PF1  0.61 net1 -6.60c
gold     30- 10s ask 0.90-0.95  n    5 win 1.000 ask 0.924 gap  +7.64pt z +0.64 PF1   inf net1  +6.64c PF10   inf net10  +7.08c  | next-poll PF1   inf net1 +6.64c
gold     30- 10s ask 0.95-0.98  n    7 win 1.000 ask 0.966 gap  +3.36pt z +0.49 PF1   inf net1  +2.36c PF10   inf net10  +3.07c  | next-poll PF1   inf net1 +2.36c
bitcoin 120- 90s ask 0.50-0.80  n   60 win 0.667 ask 0.661 gap  +0.52pt z +0.09 PF1  0.93 net1  -1.48c PF10  0.95 net10  -1.05c  | next-poll PF1  0.93 net1 -1.50c
bitcoin 120- 90s ask 0.80-0.90  n   59 win 0.898 ask 0.845 gap  +5.36pt z +1.14 PF1  1.47 net1  +4.05c PF10  1.51 net10  +4.41c  | next-poll PF1  1.47 net1 +4.05c
bitcoin 120- 90s ask 0.90-0.95  n   69 win 0.899 ask 0.919 gap  -2.09pt z -0.64 PF1  0.67 net1  -3.09c PF10  0.72 net10  -2.66c  | next-poll PF1  0.67 net1 -3.14c
bitcoin 120- 90s ask 0.95-0.98  n   67 win 0.970 ask 0.966 gap  +0.40pt z +0.18 PF1  0.79 net1  -0.60c PF10  1.04 net10  +0.13c  | next-poll PF1  0.79 net1 -0.60c
bitcoin  90- 60s ask 0.50-0.80  n   47 win 0.638 ask 0.661 gap  -2.30pt z -0.34 PF1  0.82 net1  -4.30c PF10  0.84 net10  -3.88c  | next-poll PF1  0.81 net1 -4.65c
bitcoin  90- 60s ask 0.80-0.90  n   36 win 0.833 ask 0.857 gap  -2.33pt z -0.40 PF1  0.76 net1  -3.53c PF10  0.78 net10  -3.23c  | next-poll PF1  0.75 net1 -3.57c
bitcoin  90- 60s ask 0.90-0.95  n   55 win 0.873 ask 0.922 gap  -4.95pt z -1.37 PF1  0.50 net1  -5.95c PF10  0.53 net10  -5.51c  | next-poll PF1  0.52 net1 -5.70c
bitcoin  90- 60s ask 0.95-0.98  n   61 win 1.000 ask 0.967 gap  +3.32pt z +1.45 PF1   inf net1  +2.32c PF10   inf net10  +3.05c  | next-poll PF1   inf net1 +2.33c
bitcoin  60- 30s ask 0.50-0.80  n   24 win 0.625 ask 0.650 gap  -2.54pt z -0.27 PF1  0.81 net1  -4.54c PF10  0.83 net10  -4.12c  | next-poll PF1  0.76 net1 -5.72c
bitcoin  60- 30s ask 0.80-0.90  n   22 win 0.818 ask 0.855 gap  -3.64pt z -0.49 PF1  0.69 net1  -4.86c PF10  0.71 net10  -4.53c  | next-poll PF1  0.69 net1 -4.86c
bitcoin  60- 30s ask 0.90-0.95  n   21 win 0.952 ask 0.926 gap  +2.69pt z +0.47 PF1  1.37 net1  +1.69c PF10  1.47 net10  +2.14c  | next-poll PF1  1.37 net1 +1.69c
bitcoin  60- 30s ask 0.95-0.98  n   33 win 1.000 ask 0.965 gap  +3.47pt z +1.09 PF1   inf net1  +2.47c PF10   inf net10  +3.18c  | next-poll PF1   inf net1 +2.42c
bitcoin  30- 10s ask 0.50-0.80  n    8 win 0.625 ask 0.619 gap  +0.62pt z +0.04 PF1  0.94 net1  -1.38c PF10  0.95 net10  -1.00c  | next-poll PF1  1.22 net1 +3.75c
bitcoin  30- 10s ask 0.80-0.90  n    6 win 0.833 ask 0.873 gap  -4.00pt z -0.29 PF1  0.66 net1  -5.00c PF10  0.68 net10  -4.80c  | next-poll PF1  0.57 net1 -6.33c
bitcoin  30- 10s ask 0.90-0.95  n    2 win 1.000 ask 0.940 gap  +6.05pt z +0.36 PF1   inf net1  +5.05c PF10   inf net10  +5.60c  | next-poll PF1   inf net1 +5.05c
bitcoin  30- 10s ask 0.95-0.98  n   12 win 1.000 ask 0.966 gap  +3.35pt z +0.65 PF1   inf net1  +2.35c PF10   inf net10  +3.08c  | next-poll PF1 30.13 net1 +1.94c

== rule ==
thirds [1]: n   25 win 1.000 ask 0.966 gap  +3.45pt z +0.95 PF1   inf net1  +2.45c PF10   inf net10  +3.16c | next PF1 inf | x1.2 net1 +2.25c
thirds [2]: n   13 win 1.000 ask 0.966 gap  +3.37pt z +0.67 PF1   inf net1  +2.37c PF10   inf net10  +3.09c | next PF1 inf | x1.2 net1 +2.17c
thirds [3]: n   23 win 1.000 ask 0.968 gap  +3.15pt z +0.87 PF1   inf net1  +2.15c PF10   inf net10  +2.90c | next PF1 inf | x1.2 net1 +1.95c
thirds [1, 2, 3]: n   61 win 1.000 ask 0.967 gap  +3.32pt z +1.45 PF1   inf net1  +2.32c PF10   inf net10  +3.05c | next PF1 inf | x1.2 net1 +2.12c
```

## Verdict

**LATECAL rule (Bitcoin, 90 to 60 s left, ask 0.95 to 0.98): NOT_ENOUGH_DATA.** T3 has 23 trades against the 30 required (T1 25, T2 13, T3 23; all 61 won; mean ask 0.967; +2.15c a contract on T3 after the rounded fee, +1.95c at fees x1.2; PF infinite in every third because there is no loss). Pooled z is **+1.45** against the bar of 5.17, so even with more T3 trades this sample could not pass. **All 32 cells: NOT_ENOUGH_DATA for a verdict** in at least one third (every gold cell has at most 14 windows over all three thirds; no Bitcoin cell reaches 30 windows in T3). Tries: **33** (32 cells + 1 rule); running count about 438,973 plus other workers'.

What the numbers say, without deciding anything:
- **Outside the 0.95 to 0.98 band the touch looks calibrated.** Pooled over the three thirds, the Bitcoin cells with 30 or more windows sit at -4.95 to +5.36 points of win minus ask with |z| at most 1.45, signs flip between thirds (for example 120 to 90 s, 0.80 to 0.90: T1 +11.2, T2 -15.2, T3 +11.1), and most lose after the fee. That is the "scatter around zero" predicted.
- **The 0.95 to 0.98 band won every time in the last 120 s on Bitcoin** (61 of 61 at 90 to 60 s, 33 of 33 at 60 to 30 s, 12 of 12 at 30 to 10 s, overlapping windows) and on gold (36 of 36 over the four time cells). That is not evidence of underpricing yet: at ask 0.967 the break-even after a 1c fee is a 97.7% win rate, and with 61 of 61 the one-sided 95% lower bound on the true win rate is 95.2%, below break-even. One loss costs about 97c, about 40 wins. HUNT2 named this trap ("no losses yet" makes the profit factor print infinite on a trade worth about 2c) and the null produced the same cells there. A pass on this band needs roughly 800 independent windows with the gap holding, which is about 9 more recorder days per market at Bitcoin's rate if every window lands in the cell (it does not; about a quarter do).
- **The 0.95 to 0.98 band is L1's own territory pushed later** (a late favourite held to settlement) and holding to settlement is outside the owner's rule for new cards (see `LATECAL_CHECK.md`), so even a later pass would be an L1-variant question for the owner, not a new strategy.
- **The book thins out before 30 s.** Bitcoin 30 to 10 s cells hold 2 to 12 windows over 256, matching BTCAVG's 72% one-sided polls; a sub-30 s calibration edge, if any, would carry very few windows.
- Fill check: the next-poll ask gives the same answer (same cells, nets within about 0.5c except tiny cells).

A rerun on more recorder days would need its own registration. Prediction for it: the 0.95 to 0.98 band shows its first losses and lands near break-even (L1's history at 4 minutes, HUNT2: gold 0.95-0.985 +1.93c on 565 with 5 losses, is the best guide), prior of a pass about 3%.

Files: `workers/LATECAL_CHECK.md`, `workers/LATECAL_REGISTRATION.md`, `workers/LATECAL_score.py`, this file. Raw outputs in the scratchpad (`latecal/stageA.txt`, `latecal/stageB.txt`), not in git.
