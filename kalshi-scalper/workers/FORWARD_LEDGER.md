# FORWARD LEDGER (automatic; research only)

Written by `python -m scalper.fwdledger run` (once per AUTO pass, `scalper.autoscore check`). Last updated 2026-11-04 08:42 UTC.
Forward evidence counts only windows that CLOSED after a candidate's freeze time, had the data its rule needs and have settled.
Fees 7% x C x p x (1-p) rounded up to the cent per order, at 1 and 10 contracts; held to settlement pays the entry fee only. Win = net at 10 contracts above zero. Net per contract is at 10 contracts. Trades per week: forward trades over the time from the freeze to the last evaluated close.
This ledger never promotes anything. READY FOR THE FALSIFIER means only: forward PF 1.5+ at 1 and at 10 contracts on 30+ trades over 10+ trade days. It earns a falsifier read, nothing more. How a generator adds a candidate: `workers/candidates/README.md`.

| id | market | stage | freeze | fwd days | trades | wins | losses | PF 1c | PF 10c | net/contract | trades/week | updated | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BOOKCH1B_BTC | KXBTC15M | discovery | 2026-11-04 | 1 | 1 | 0 | 1 | 0.00 | 0.00 | -6.90c | 7.0 | 2026-11-04 08:42 UTC |  |
| BOOKCH1B_XRP | KXXRP15M | discovery | 2026-11-04 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-11-04 08:42 UTC |  |
| BOOKCH1_BTC | KXBTC15M | discovery | 2026-11-04 | 1 | 3 | 2 | 1 | 4.83 | 4.93 | +38.63c | 21.0 | 2026-11-04 08:42 UTC |  |
| BOOKCH1_XRP | KXXRP15M | discovery | 2026-11-04 | 1 | 1 | 0 | 1 | 0.00 | 0.00 | -42.70c | 7.0 | 2026-11-04 08:42 UTC |  |
| USWEEP1_KXBRENTD_FAV_60 | KXBRENTD | discovery | 2026-11-03 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-11-04 08:42 UTC |  |
| USWEEP1_KXGOLDD_FAV_360 | KXGOLDD | discovery | 2026-11-03 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-11-04 08:42 UTC |  |
| USWEEP1_KXHIGHTSATX_FAV_1440 | KXHIGHTSATX | discovery | 2026-11-03 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-11-04 08:42 UTC |  |
| USWEEP1_KXNATGASD_FAV_360 | KXNATGASD | discovery | 2026-11-03 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-11-04 08:42 UTC |  |
| USWEEP1_KXSILVERD_FAV_360 | KXSILVERD | discovery | 2026-11-03 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-11-04 08:42 UTC |  |
| EVENT830 | KXSILVER15M,KXCOPPER15M,KXWTI15M,KXEURUSD15M,KXGBPUSD15M,KXUSDJPY15M,KXHYPE15M,KXBNB15M | discovery | 2026-11-03 | 2 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-11-04 08:42 UTC |  |
| REF_GEN6_OIREL | KXBTC15M | reference | 2026-10-30 | 6 | 17 | 4 | 13 | 1.66 | 1.76 | +6.73c | 25.2 | 2026-11-04 08:42 UTC |  |
| LADFADE_BTC | KXBTC15M | validation | 2026-10-30 | 6 | 30 | 9 | 21 | 0.57 | 0.57 | -12.59c | 43.4 | 2026-11-04 08:42 UTC |  |
| REF_GEN6_OICORE | KXBTC15M | reference | 2026-10-30 | 6 | 31 | 8 | 23 | 2.40 | 2.58 | +10.95c | 41.5 | 2026-11-04 08:42 UTC |  |
| GEN6_B01 | KXBTC15M | validation | 2026-10-30 | 6 | 11 | 5 | 6 | 6.11 | 6.67 | +26.91c | 14.6 | 2026-11-04 08:42 UTC |  |
| GEN6_B02 | KXBTC15M | validation | 2026-10-30 | 6 | 12 | 1 | 11 | 1.48 | 2.13 | +2.69c | 15.9 | 2026-11-04 08:42 UTC |  |
| GEN6_B03 | KXBTC15M | validation | 2026-10-30 | 6 | 31 | 10 | 21 | 2.58 | 2.84 | +10.50c | 41.2 | 2026-11-04 08:42 UTC |  |
| GEN6_B04 | KXBTC15M | validation | 2026-10-30 | 6 | 26 | 6 | 20 | 1.53 | 1.67 | +4.43c | 34.5 | 2026-11-04 08:42 UTC |  |
| GEN6_B05 | KXBTC15M | validation | 2026-10-30 | 6 | 11 | 1 | 10 | 0.02 | 0.03 | -14.90c | 14.6 | 2026-11-04 08:42 UTC |  |
| GEN6_B06 | KXBTC15M | validation | 2026-10-30 | 6 | 16 | 6 | 10 | 4.82 | 5.39 | +18.29c | 21.2 | 2026-11-04 08:42 UTC |  |
| GEN6_B07 | KXBTC15M | validation | 2026-10-30 | 6 | 17 | 6 | 11 | 1.47 | 1.55 | +4.95c | 22.6 | 2026-11-04 08:42 UTC |  |
| GEN6_B08 | KXBTC15M | validation | 2026-10-30 | 6 | 27 | 3 | 24 | 0.72 | 0.77 | -2.36c | 35.9 | 2026-11-04 08:42 UTC |  |
| GEN6_B09 | KXBTC15M | validation | 2026-10-30 | 6 | 14 | 4 | 10 | 0.61 | 0.68 | -3.24c | 18.6 | 2026-11-04 08:42 UTC |  |
| GEN6_B10 | KXBTC15M | validation | 2026-10-30 | 6 | 62 | 12 | 50 | 1.35 | 1.43 | +3.65c | 82.3 | 2026-11-04 08:42 UTC |  |
| GEN6_B11 | KXBTC15M | validation | 2026-10-30 | 6 | 17 | 3 | 14 | 2.85 | 3.56 | +7.25c | 22.6 | 2026-11-04 08:42 UTC |  |
| GEN6_B12 | KXBTC15M | validation | 2026-10-30 | 6 | 8 | 1 | 7 | 0.53 | 0.56 | -5.53c | 10.6 | 2026-11-04 08:42 UTC |  |
| GEN6_B13 | KXBTC15M | validation | 2026-10-30 | 6 | 16 | 8 | 8 | 2.28 | 2.56 | +7.38c | 21.2 | 2026-11-04 08:42 UTC |  |
| REF_BTC_UNDERDOG_180 | KXBTC15M | reference | 2026-10-30 | 6 | 154 | 58 | 96 | 1.22 | 1.25 | +4.82c | 204.5 | 2026-11-04 08:42 UTC |  |
| GEN7_B01 | KXBTC15M | validation | 2026-10-30 | 6 | 12 | 4 | 8 | 4.39 | 5.53 | +13.02c | 15.8 | 2026-11-04 08:42 UTC |  |
| GEN7_B02 | KXBTC15M | validation | 2026-10-30 | 6 | 19 | 4 | 15 | 0.73 | 0.81 | -2.01c | 25.0 | 2026-11-04 08:42 UTC |  |
| REF_GEN6_OIDRIFT | KXBTC15M | reference | 2026-10-30 | 6 | 1 | 0 | 1 | 0.00 | 0.00 | -43.80c | 1.3 | 2026-11-04 08:42 UTC |  |
| REF_GOLD_UNDERDOG_180 | KXGOLD15M | reference | 2026-10-30 | 5 | 103 | 25 | 78 | 0.69 | 0.71 | -6.43c | 135.7 | 2026-11-04 08:42 UTC |  |
| REF_LATECAL_BTC | KXBTC15M | reference | 2026-10-30 | 6 | 31 | 30 | 1 | 0.73 | 0.96 | -0.12c | 40.8 | 2026-11-04 08:42 UTC |  |
| GEN4_B01 | KXBTC15M | validation | 2026-10-30 | 6 | 100 | 67 | 33 | 0.83 | 0.88 | -2.38c | 131.2 | 2026-11-04 08:42 UTC |  |
| GEN4_B02 | KXBTC15M | validation | 2026-10-30 | 6 | 99 | 66 | 33 | 0.81 | 0.86 | -2.64c | 129.9 | 2026-11-04 08:42 UTC |  |
| GEN4_B03 | KXBTC15M | validation | 2026-10-30 | 6 | 92 | 50 | 42 | 1.07 | 1.12 | +2.51c | 120.8 | 2026-11-04 08:42 UTC |  |
| GEN4_B04 | KXBTC15M | validation | 2026-10-30 | 6 | 102 | 71 | 31 | 0.91 | 0.93 | -1.41c | 133.9 | 2026-11-04 08:42 UTC |  |
| GEN4_B05 | KXBTC15M | validation | 2026-10-30 | 6 | 81 | 36 | 45 | 1.35 | 1.43 | +5.54c | 106.3 | 2026-11-04 08:42 UTC |  |
| GEN4_B06 | KXBTC15M | validation | 2026-10-30 | 6 | 104 | 45 | 59 | 1.35 | 1.39 | +5.17c | 136.5 | 2026-11-04 08:42 UTC |  |
| GEN4_B07 | KXBTC15M | validation | 2026-10-30 | 6 | 61 | 25 | 36 | 1.08 | 1.13 | +2.14c | 80.1 | 2026-11-04 08:42 UTC |  |
| GEN4_B08 | KXBTC15M | validation | 2026-10-30 | 6 | 106 | 72 | 34 | 0.80 | 0.85 | -3.31c | 139.1 | 2026-11-04 08:42 UTC |  |
| GEN4_B09 | KXBTC15M | validation | 2026-10-30 | 6 | 101 | 41 | 60 | 1.01 | 1.03 | +0.56c | 132.6 | 2026-11-04 08:42 UTC |  |
| GEN4_B10 | KXBTC15M | validation | 2026-10-30 | 6 | 93 | 60 | 33 | 0.68 | 0.73 | -5.92c | 122.1 | 2026-11-04 08:42 UTC |  |
| GEN4_B11 | KXBTC15M | validation | 2026-10-30 | 6 | 92 | 39 | 53 | 1.21 | 1.25 | +3.32c | 120.8 | 2026-11-04 08:42 UTC |  |
| GEN4_B12 | KXBTC15M | validation | 2026-10-30 | 6 | 100 | 72 | 28 | 1.06 | 1.12 | +2.27c | 131.2 | 2026-11-04 08:42 UTC |  |
| GEN4_B13 | KXBTC15M | validation | 2026-10-30 | 6 | 115 | 76 | 39 | 0.75 | 0.80 | -4.14c | 150.9 | 2026-11-04 08:42 UTC |  |
| GEN4_B14 | KXBTC15M | validation | 2026-10-30 | 6 | 88 | 64 | 24 | 1.10 | 1.17 | +3.08c | 115.5 | 2026-11-04 08:42 UTC |  |
| GEN4_B15 | KXBTC15M | validation | 2026-10-30 | 6 | 89 | 46 | 43 | 0.81 | 0.83 | -3.77c | 116.8 | 2026-11-04 08:42 UTC |  |
| GEN4_B16 | KXBTC15M | validation | 2026-10-30 | 6 | 103 | 70 | 33 | 0.83 | 0.88 | -2.50c | 135.2 | 2026-11-04 08:42 UTC |  |
| GEN4_B17 | KXBTC15M | validation | 2026-10-30 | 6 | 91 | 61 | 30 | 0.77 | 0.79 | -4.74c | 119.4 | 2026-11-04 08:42 UTC |  |
| GEN4_B18 | KXBTC15M | validation | 2026-10-30 | 6 | 97 | 64 | 33 | 0.80 | 0.85 | -3.05c | 127.3 | 2026-11-04 08:42 UTC |  |
| GEN4_B19 | KXBTC15M | validation | 2026-10-30 | 6 | 93 | 62 | 31 | 0.82 | 0.84 | -3.70c | 122.1 | 2026-11-04 08:42 UTC |  |
| GEN4_B20 | KXBTC15M | validation | 2026-10-30 | 6 | 81 | 52 | 29 | 0.70 | 0.75 | -5.46c | 106.3 | 2026-11-04 08:42 UTC |  |
| GEN4_B21 | KXBTC15M | validation | 2026-10-30 | 6 | 57 | 36 | 21 | 0.61 | 0.65 | -8.91c | 74.8 | 2026-11-04 08:42 UTC |  |
| GEN4_B22 | KXBTC15M | validation | 2026-10-30 | 6 | 105 | 70 | 35 | 0.79 | 0.80 | -4.39c | 137.8 | 2026-11-04 08:42 UTC |  |
| GEN4_B23 | KXBTC15M | validation | 2026-10-30 | 6 | 68 | 44 | 24 | 0.74 | 0.76 | -5.58c | 89.2 | 2026-11-04 08:42 UTC |  |
| GEN4_B24 | KXBTC15M | validation | 2026-10-30 | 6 | 85 | 55 | 30 | 0.70 | 0.72 | -6.68c | 111.6 | 2026-11-04 08:42 UTC |  |
| GEN4_B25 | KXBTC15M | validation | 2026-10-30 | 6 | 85 | 59 | 26 | 0.86 | 0.91 | -1.83c | 111.6 | 2026-11-04 08:42 UTC |  |
| GEN4_B26 | KXBTC15M | validation | 2026-10-30 | 6 | 96 | 62 | 34 | 0.67 | 0.72 | -6.75c | 126.0 | 2026-11-04 08:42 UTC |  |
| GEN4_B27 | KXBTC15M | validation | 2026-10-30 | 6 | 68 | 44 | 24 | 0.71 | 0.75 | -5.76c | 89.2 | 2026-11-04 08:42 UTC |  |
| GEN4_B28 | KXBTC15M | validation | 2026-10-30 | 6 | 84 | 58 | 26 | 0.88 | 0.93 | -1.50c | 110.2 | 2026-11-04 08:42 UTC |  |
| GEN4_B29 | KXBTC15M | validation | 2026-10-30 | 6 | 104 | 74 | 30 | 0.95 | 1.01 | +0.17c | 136.5 | 2026-11-04 08:42 UTC |  |
| GEN4_B30 | KXBTC15M | validation | 2026-10-30 | 6 | 79 | 54 | 25 | 0.74 | 0.78 | -4.67c | 103.7 | 2026-11-04 08:42 UTC |  |
| GEN4_B31 | KXBTC15M | validation | 2026-10-30 | 6 | 114 | 79 | 35 | 0.83 | 0.88 | -2.49c | 149.6 | 2026-11-04 08:42 UTC |  |
| GEN4_B32 | KXBTC15M | validation | 2026-10-30 | 6 | 87 | 61 | 26 | 0.95 | 1.01 | +0.23c | 114.2 | 2026-11-04 08:42 UTC |  |
| GEN4_B33 | KXBTC15M | validation | 2026-10-30 | 6 | 68 | 44 | 24 | 0.72 | 0.77 | -5.28c | 89.2 | 2026-11-04 08:42 UTC |  |
| GEN4_B34 | KXBTC15M | validation | 2026-10-30 | 6 | 102 | 66 | 36 | 0.71 | 0.73 | -6.38c | 133.9 | 2026-11-04 08:42 UTC |  |
| GEN4_B35 | KXBTC15M | validation | 2026-10-30 | 6 | 79 | 22 | 57 | 1.78 | 1.85 | +9.54c | 103.7 | 2026-11-04 08:42 UTC |  |
| GEN4_B36 | KXBTC15M | validation | 2026-10-30 | 6 | 87 | 62 | 25 | 0.95 | 1.01 | +0.16c | 114.2 | 2026-11-04 08:42 UTC |  |
| GEN4_B37 | KXBTC15M | validation | 2026-10-30 | 6 | 91 | 36 | 55 | 1.28 | 1.38 | +4.50c | 119.4 | 2026-11-04 08:42 UTC |  |
| GEN4_B38 | KXBTC15M | validation | 2026-10-30 | 6 | 108 | 70 | 38 | 0.68 | 0.70 | -7.45c | 141.8 | 2026-11-04 08:42 UTC |  |
| GEN4_B39 | KXBTC15M | validation | 2026-10-30 | 6 | 105 | 70 | 35 | 0.81 | 0.85 | -3.17c | 137.8 | 2026-11-04 08:42 UTC |  |
| GEN4_B40 | KXBTC15M | validation | 2026-10-30 | 6 | 114 | 76 | 38 | 0.75 | 0.80 | -4.33c | 149.6 | 2026-11-04 08:42 UTC |  |
| GEN4_B41 | KXBTC15M | validation | 2026-10-30 | 6 | 69 | 46 | 23 | 0.76 | 0.78 | -4.92c | 90.6 | 2026-11-04 08:42 UTC |  |
| GEN4_B42 | KXBTC15M | validation | 2026-10-30 | 6 | 81 | 24 | 57 | 1.87 | 1.98 | +10.73c | 106.3 | 2026-11-04 08:42 UTC |  |
| GEN4_B43 | KXBTC15M | validation | 2026-10-30 | 6 | 108 | 72 | 36 | 0.78 | 0.82 | -4.04c | 141.8 | 2026-11-04 08:42 UTC |  |
| GEN4_B44 | KXBTC15M | validation | 2026-10-30 | 6 | 106 | 77 | 29 | 1.09 | 1.12 | +2.10c | 139.1 | 2026-11-04 08:42 UTC |  |
| GEN4_B45 | KXBTC15M | validation | 2026-10-30 | 6 | 83 | 54 | 29 | 0.72 | 0.76 | -5.33c | 108.9 | 2026-11-04 08:42 UTC |  |
| GEN4_B46 | KXBTC15M | validation | 2026-10-30 | 6 | 98 | 68 | 30 | 0.91 | 0.93 | -1.56c | 128.6 | 2026-11-04 08:42 UTC |  |
| GEN4_B47 | KXBTC15M | validation | 2026-10-30 | 6 | 106 | 71 | 35 | 0.83 | 0.85 | -3.41c | 139.1 | 2026-11-04 08:42 UTC |  |
| GEN4_B48 | KXBTC15M | validation | 2026-10-30 | 6 | 86 | 58 | 28 | 0.71 | 0.75 | -5.86c | 112.9 | 2026-11-04 08:42 UTC |  |
| GEN4_B49 | KXBTC15M | validation | 2026-10-30 | 6 | 106 | 73 | 33 | 0.94 | 0.96 | -0.91c | 139.1 | 2026-11-04 08:42 UTC |  |
| GEN4_B50 | KXBTC15M | validation | 2026-10-30 | 6 | 81 | 54 | 27 | 0.84 | 0.86 | -3.13c | 106.3 | 2026-11-04 08:42 UTC |  |
| GEN4_B51 | KXBTC15M | validation | 2026-10-30 | 6 | 103 | 70 | 33 | 0.77 | 0.82 | -4.03c | 135.2 | 2026-11-04 08:42 UTC |  |
| GEN4_REF_FAV150 | KXBTC15M | reference | 2026-10-30 | 6 | 100 | 67 | 33 | 0.80 | 0.82 | -3.93c | 131.2 | 2026-11-04 08:42 UTC |  |
| REF_L1_GOLD | KXGOLD15M | reference | 2026-10-30 | 5 | 71 | 67 | 4 | 1.11 | 1.20 | +1.09c | 92.8 | 2026-11-04 08:42 UTC |  |

## History per candidate

### BOOKCH1B_BTC

Evaluator `scalper.bookch1:forward_eval`, source `r6`, frozen 2026-11-04T00:00:00Z. Cheaper side's top-5 bid size down from 360 s to 180 s, below 0 and under the 10th percentile of the market's own trailing 24 hours (depth withdrawal; the separately counted second try). Cheaper side (ask 0.05 to 0.50, 10+ displayed) at the first ask 1 s after the 180 s look, held to settlement. Trailing 24 hour cut, 48 window minimum. No backtest; forward windows only. Verdict is the pooled Bitcoin and XRP rows. 2 tries counted (primary and alternative). workers/BOOKCH1_REGISTRATION.md.
Windows evaluated 27 on 1 days; without the data the rule needs 4; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -7.40c at 1, -6.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-11-04 | 1 | 0 | 1 | -6.9c | -6.9c | 0.00 |

### BOOKCH1B_XRP

Evaluator `scalper.bookch1:forward_eval`, source `r6`, frozen 2026-11-04T00:00:00Z. Cheaper side's top-5 bid size down from 360 s to 180 s, below 0 and under the 10th percentile of the market's own trailing 24 hours (depth withdrawal; the separately counted second try). Cheaper side (ask 0.05 to 0.50, 10+ displayed) at the first ask 1 s after the 180 s look, held to settlement. Trailing 24 hour cut, 48 window minimum. No backtest; forward windows only. Verdict is the pooled Bitcoin and XRP rows. 2 tries counted (primary and alternative). workers/BOOKCH1_REGISTRATION.md.
Windows evaluated 31 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### BOOKCH1_BTC

Evaluator `scalper.bookch1:forward_eval`, source `r6`, frozen 2026-11-04T00:00:00Z. Top-5 bid size of the cheaper side over the other side in the highest tertile of the market's own trailing 24 hours. Cheaper side (ask 0.05 to 0.50, 10+ displayed) at the first ask 1 s after the 180 s look, held to settlement. Trailing 24 hour cut, 48 window minimum. No backtest; forward windows only. Verdict is the pooled Bitcoin and XRP rows. 2 tries counted (primary and alternative). workers/BOOKCH1_REGISTRATION.md.
Windows evaluated 27 on 1 days; without the data the rule needs 4; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 4.83, at 10 contracts 4.93, at 10 contracts with fees x1.2 4.88; net per contract +38.33c at 1, +38.63c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-11-04 | 3 | 2 | 1 | +115.9c | +115.9c | 4.93 |

### BOOKCH1_XRP

Evaluator `scalper.bookch1:forward_eval`, source `r6`, frozen 2026-11-04T00:00:00Z. Top-5 bid size of the cheaper side over the other side in the highest tertile of the market's own trailing 24 hours. Cheaper side (ask 0.05 to 0.50, 10+ displayed) at the first ask 1 s after the 180 s look, held to settlement. Trailing 24 hour cut, 48 window minimum. No backtest; forward windows only. Verdict is the pooled Bitcoin and XRP rows. 2 tries counted (primary and alternative). workers/BOOKCH1_REGISTRATION.md.
Windows evaluated 31 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -43.00c at 1, -42.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-11-04 | 1 | 0 | 1 | -42.7c | -42.7c | 0.00 |

### USWEEP1_KXBRENTD_FAV_60

Evaluator `scalper.usweep1:forward_eval`, source `candles`, frozen 2026-11-03T17:00:00Z. Brent Oil Daily: favourite (ask 0.85 to 0.97, hard limit 0.97) 60 min before the close, taker, held. Development n 44 on 18 dates, win 97.7% vs 93.0c paid, net +4.22c, z 2.10, halves +2.8c / +6.1c. Probe: 1 contract, kill at 40 fills with PF under 1.0; worst loss 98c per contract (about $9.73 at 10); about 2.4 entries a day in development, so 40 fills in roughly 16 days (strikes on one day are not independent). Not a lead; below the deflated bar.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### USWEEP1_KXGOLDD_FAV_360

Evaluator `scalper.usweep1:forward_eval`, source `candles`, frozen 2026-11-03T17:00:00Z. Gold Daily: favourite (ask 0.85 to 0.97, hard limit 0.97) 360 min before the close, taker, held. Development n 48 on 10 dates, win 97.9% vs 93.0c paid, net +4.44c, z 2.22, halves +6.4c / +2.5c. Probe: 1 contract, kill at 40 fills with PF under 1.0; worst loss 98c per contract (about $9.73 at 10); about 4.8 entries a day in development, so 40 fills in roughly 8 days (strikes on one day are not independent). Not a lead; below the deflated bar.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### USWEEP1_KXHIGHTSATX_FAV_1440

Evaluator `scalper.usweep1:forward_eval`, source `candles`, frozen 2026-11-03T17:00:00Z. San Antonio Daily Maximum Temperature: favourite (ask 0.85 to 0.97, hard limit 0.97) 1440 min before the close, taker, held. Development n 52 on 32 dates, win 96.2% vs 91.1c paid, net +4.49c, z 1.79, halves +4.6c / +4.4c. Probe: 1 contract, kill at 40 fills with PF under 1.0; worst loss 98c per contract (about $9.73 at 10); about 1.6 entries a day in development, so 40 fills in roughly 25 days (strikes on one day are not independent). Not a lead; below the deflated bar.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### USWEEP1_KXNATGASD_FAV_360

Evaluator `scalper.usweep1:forward_eval`, source `candles`, frozen 2026-11-03T17:00:00Z. Natural Gas Daily: favourite (ask 0.85 to 0.97, hard limit 0.97) 360 min before the close, taker, held. Development n 67 on 6 dates, win 98.5% vs 92.4c paid, net +5.60c, z 3.71, halves +7.3c / +4.2c. Probe: 1 contract, kill at 40 fills with PF under 1.0; worst loss 98c per contract (about $9.73 at 10); about 11.2 entries a day in development, so 40 fills in roughly 4 days (strikes on one day are not independent). Not a lead; below the deflated bar.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### USWEEP1_KXSILVERD_FAV_360

Evaluator `scalper.usweep1:forward_eval`, source `candles`, frozen 2026-11-03T17:00:00Z. Silver daily: favourite (ask 0.85 to 0.97, hard limit 0.97) 360 min before the close, taker, held. Development n 41 on 10 dates, win 100.0% vs 93.0c paid, net +6.50c, z 22.25, halves +6.7c / +6.3c. Probe: 1 contract, kill at 40 fills with PF under 1.0; worst loss 98c per contract (about $9.73 at 10); about 4.1 entries a day in development, so 40 fills in roughly 10 days (strikes on one day are not independent). Not a lead; below the deflated bar.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### EVENT830

Evaluator `scalper.event830:forward_eval`, source `candles`, frozen 2026-11-03T15:00:00Z. Cheaper side (ask 0.05 to 0.50, hard fill limit 0.50) of 8 L1-free 15 minute series at the 180 s look in the window closing at a listed US 8:30 ET release (CPI, PPI, jobs, retail, GDP and PCE, weekly claims), fill at the next candle ask, held. Calendar frozen to 2026-12-31. 1 try. Kill: PF under 1.0 at 40 trades, or under 1.2 / event minus Eastern-clock control not positive at 150.
Windows evaluated 550 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_GEN6_OIREL

Evaluator `scalper.oirel:forward_eval`, source `candles`, frozen 2026-10-30T15:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) when open interest over the 3 minutes before rose by more than 26.76% of its level at 360 s (the discovery quantile matched to the core's 86,300 count), fill at the next candle's ask, held. History: discovery n 298 PF 1.73, validation n 286 PF 1.71 at 10 contracts (FALS5 check 2, one try). Not independent of REF_GEN6_OICORE (59% to 80% shared trades). workers/FALS5_REGISTRATION.md, workers/FALS5_RESULT.md.
Windows evaluated 454 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 17 on 5 days; zero-volume trades 0.
PF at 1 contract 1.66, at 10 contracts 1.76, at 10 contracts with fees x1.2 1.74; net per contract +6.18c at 1, +6.73c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -43.8c | -43.8c | 0.00 |
| 2026-10-31 | 3 | 1 | 2 | +61.6c | +17.8c | 1.29 |
| 2026-11-01 | 6 | 1 | 5 | +40.5c | +58.3c | 1.52 |
| 2026-11-02 | 3 | 1 | 2 | -19.9c | +38.4c | 1.27 |
| 2026-11-03 | 4 | 1 | 3 | +76.0c | +114.4c | 1.76 |

### LADFADE_BTC

Evaluator `scalper.ladfade:forward_eval`, source `candles`, frozen 2026-10-30T12:00:00Z. Bitcoin 15 minute windows opening at :15 and :30: when the hourly KXBTCD ladder leans 5c+ from 50/50 at the first minute, buy the side the 15 minute book overshot AWAY from if its ask is 3c+ below the ladder's chance, at the next candle's ask (30c to 70c), held. Ladder from the book recorder. Discovery and validation spent (post hoc); holdout read once in workers/LADFADE_RESULT.md. 1 try; workers/LADFADE_REGISTRATION.md.
Windows evaluated 393 on 6 days; without the data the rule needs 73; evaluator errors 0. Trades 30 on 6 days; zero-volume trades 0.
PF at 1 contract 0.57, at 10 contracts 0.57, at 10 contracts with fees x1.2 0.57; net per contract -12.90c at 1, -12.59c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -44.8c | -44.8c | 0.00 |
| 2026-10-31 | 4 | 0 | 4 | -144.4c | -189.2c | 0.00 |
| 2026-11-01 | 10 | 3 | 7 | -113.7c | -302.9c | 0.36 |
| 2026-11-02 | 10 | 4 | 6 | -45.9c | -348.8c | 0.53 |
| 2026-11-03 | 4 | 2 | 2 | +15.0c | -333.8c | 0.60 |
| 2026-11-04 | 1 | 0 | 1 | -43.8c | -377.6c | 0.57 |

### REF_GEN6_OICORE

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T03:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest rose more than 86,300 contracts over the 3 minutes before, held to settlement, fill at the next candle's ask. History: discovery PF 2.28 (n 222), validation 1.85 (n 333, z 4.53). Forward days only; 1 try. Falsifier FALS4 running.
Windows evaluated 502 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 31 on 6 days; zero-volume trades 0.
PF at 1 contract 2.40, at 10 contracts 2.58, at 10 contracts with fees x1.2 2.55; net per contract +10.39c at 1, +10.95c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 7 | 3 | 4 | +177.6c | +133.3c | 2.36 |
| 2026-11-01 | 5 | 2 | 3 | +97.4c | +230.7c | 2.64 |
| 2026-11-02 | 8 | 2 | 6 | +55.8c | +286.5c | 2.55 |
| 2026-11-03 | 7 | 1 | 6 | +59.6c | +346.1c | 2.66 |
| 2026-11-04 | 2 | 0 | 2 | -6.5c | +339.6c | 2.58 |

### GEN6_B01

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | doi>8.63e+04 & m3>-0.25 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.81 (n 104), validation PF 1.90 (n 164), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 5 days; zero-volume trades 0.
PF at 1 contract 6.11, at 10 contracts 6.67, at 10 contracts with fees x1.2 6.59; net per contract +26.13c at 1, +26.91c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 3 | 2 | 1 | +77.5c | +77.5c | 3.24 |
| 2026-11-01 | 1 | 1 | 0 | +86.0c | +163.5c | 5.73 |
| 2026-11-02 | 2 | 1 | 1 | +85.8c | +249.3c | 7.54 |
| 2026-11-03 | 4 | 1 | 3 | +47.2c | +296.5c | 6.74 |
| 2026-11-04 | 1 | 0 | 1 | -0.5c | +296.0c | 6.67 |

### GEN6_B02

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | hour<=21 & xb_d2<=0.046 & doi>8.63e+04 | TP +8c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 2.42 (n 106), validation PF 1.80 (n 133), C=10.
Windows evaluated 409 on 6 days; without the data the rule needs 97; evaluator errors 0. Trades 12 on 4 days; zero-volume trades 0.
PF at 1 contract 1.48, at 10 contracts 2.13, at 10 contracts with fees x1.2 2.08; net per contract +1.62c at 1, +2.69c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |
| 2026-11-02 | 6 | 0 | 6 | -21.4c | -21.9c | 0.00 |
| 2026-11-03 | 3 | 1 | 2 | +56.1c | +34.2c | 2.29 |
| 2026-11-04 | 2 | 0 | 2 | -1.9c | +32.3c | 2.13 |

### GEN6_B03

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 | TP +5c stop -20c else hold]; fill at the next candle's ask. Discovery PF 2.41 (n 222), validation PF 1.73 (n 333), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 31 on 6 days; zero-volume trades 0.
PF at 1 contract 2.58, at 10 contracts 2.84, at 10 contracts with fees x1.2 2.80; net per contract +9.78c at 1, +10.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 7 | 3 | 4 | +130.6c | +86.3c | 1.88 |
| 2026-11-01 | 5 | 3 | 2 | +136.5c | +222.8c | 3.11 |
| 2026-11-02 | 8 | 2 | 6 | +55.9c | +278.7c | 2.85 |
| 2026-11-03 | 7 | 2 | 5 | +53.4c | +332.1c | 2.95 |
| 2026-11-04 | 2 | 0 | 2 | -6.5c | +325.6c | 2.84 |

### GEN6_B04

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 & xa_spr<=0.02 & rng5>0.14 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.06 (n 175), validation PF 1.68 (n 269), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 26 on 6 days; zero-volume trades 0.
PF at 1 contract 1.53, at 10 contracts 1.67, at 10 contracts with fees x1.2 1.64; net per contract +3.80c at 1, +4.43c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 5 | 1 | 4 | +18.5c | -25.8c | 0.74 |
| 2026-11-01 | 5 | 3 | 2 | +136.5c | +110.7c | 2.05 |
| 2026-11-02 | 6 | 1 | 5 | -30.0c | +80.7c | 1.55 |
| 2026-11-03 | 6 | 1 | 5 | +41.1c | +121.8c | 1.73 |
| 2026-11-04 | 2 | 0 | 2 | -6.5c | +115.3c | 1.67 |

### GEN6_B05

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | d3<=-0.08 & m1<=0 & vol<=1.11e+05 | TP +20c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 1.60 (n 172), validation PF 1.66 (n 58), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 3 days; zero-volume trades 0.
PF at 1 contract 0.02, at 10 contracts 0.03, at 10 contracts with fees x1.2 0.02; net per contract -16.09c at 1, -14.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 5 | 1 | 4 | -30.2c | -30.2c | 0.12 |
| 2026-11-01 | 5 | 0 | 5 | -109.5c | -139.7c | 0.03 |
| 2026-11-02 | 1 | 0 | 1 | -24.2c | -163.9c | 0.03 |

### GEN6_B06

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | d1<=0.1 & doi>8.63e+04 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 3.51 (n 111), validation PF 1.57 (n 162), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 16 on 6 days; zero-volume trades 0.
PF at 1 contract 4.82, at 10 contracts 5.39, at 10 contracts with fees x1.2 5.32; net per contract +17.56c at 1, +18.29c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |
| 2026-10-31 | 4 | 2 | 2 | +68.1c | +67.6c | 2.52 |
| 2026-11-01 | 1 | 1 | 0 | +86.0c | +153.6c | 4.45 |
| 2026-11-02 | 5 | 2 | 3 | +92.4c | +246.0c | 5.68 |
| 2026-11-03 | 4 | 1 | 3 | +47.2c | +293.2c | 5.43 |
| 2026-11-04 | 1 | 0 | 1 | -0.5c | +292.7c | 5.39 |

### GEN6_B07

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 240..180s | m3>-0.08 & m5<=-0.24 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.72 (n 137), validation PF 1.45 (n 90), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 17 on 5 days; zero-volume trades 0.
PF at 1 contract 1.47, at 10 contracts 1.55, at 10 contracts with fees x1.2 1.52; net per contract +4.36c at 1, +4.95c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 1 | 1 | +20.1c | +20.1c | 3.64 |
| 2026-10-31 | 4 | 0 | 4 | -89.5c | -69.4c | 0.29 |
| 2026-11-01 | 5 | 1 | 4 | +41.4c | -28.0c | 0.80 |
| 2026-11-02 | 1 | 1 | 0 | +4.8c | -23.2c | 0.83 |
| 2026-11-03 | 5 | 3 | 2 | +107.3c | +84.1c | 1.55 |

### GEN6_B08

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | rng5<=0.273 & doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.14 (n 205), validation PF 1.43 (n 316), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 27 on 6 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.77, at 10 contracts with fees x1.2 0.76; net per contract -2.93c at 1, -2.36c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -56.6c | -56.6c | 0.00 |
| 2026-10-31 | 7 | 2 | 5 | +48.3c | -8.3c | 0.94 |
| 2026-11-01 | 2 | 0 | 2 | -39.1c | -47.4c | 0.72 |
| 2026-11-02 | 9 | 1 | 8 | +11.7c | -35.7c | 0.85 |
| 2026-11-03 | 4 | 0 | 4 | -23.3c | -59.0c | 0.78 |
| 2026-11-04 | 2 | 0 | 2 | -4.7c | -63.7c | 0.77 |

### GEN6_B09

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | vol<=1.28e+05 & m1<=-0.0507 | TP +3c stop -20c else sell 60s]; fill at the next candle's ask. Discovery PF 1.55 (n 192), validation PF 1.42 (n 86), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 4 days; zero-volume trades 0.
PF at 1 contract 0.61, at 10 contracts 0.68, at 10 contracts with fees x1.2 0.67; net per contract -4.33c at 1, -3.24c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 6 | 2 | 4 | -2.2c | -2.2c | 0.94 |
| 2026-11-01 | 5 | 2 | 3 | +6.1c | +3.9c | 1.04 |
| 2026-11-02 | 2 | 0 | 2 | -34.5c | -30.6c | 0.76 |
| 2026-11-03 | 1 | 0 | 1 | -14.8c | -45.4c | 0.68 |

### GEN6_B10

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.19 (n 433), validation PF 1.41 (n 587), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 62 on 6 days; zero-volume trades 0.
PF at 1 contract 1.35, at 10 contracts 1.43, at 10 contracts with fees x1.2 1.41; net per contract +3.13c at 1, +3.65c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 1 | 6 | -6.3c | -6.3c | 0.91 |
| 2026-10-31 | 11 | 3 | 8 | +112.2c | +105.9c | 1.64 |
| 2026-11-01 | 11 | 2 | 9 | +5.6c | +111.5c | 1.33 |
| 2026-11-02 | 15 | 2 | 13 | +12.8c | +124.3c | 1.29 |
| 2026-11-03 | 13 | 3 | 10 | +76.1c | +200.4c | 1.40 |
| 2026-11-04 | 5 | 1 | 4 | +26.1c | +226.5c | 1.43 |

### GEN6_B11

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | ask<=0.19 & xa_spr<=0.003 & d1<=-0.05 | TP +5c stop -5c else hold]; fill at the next candle's ask. Discovery PF 1.82 (n 110), validation PF 1.37 (n 93), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 17 on 6 days; zero-volume trades 0.
PF at 1 contract 2.85, at 10 contracts 3.56, at 10 contracts with fees x1.2 3.47; net per contract +6.45c at 1, +7.25c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +47.3c | +47.3c | 15.33 |
| 2026-10-31 | 5 | 1 | 4 | +53.2c | +100.5c | 5.47 |
| 2026-11-01 | 1 | 0 | 1 | -1.8c | +98.7c | 5.06 |
| 2026-11-02 | 5 | 1 | 4 | +30.2c | +128.9c | 4.04 |
| 2026-11-03 | 1 | 0 | 1 | -1.5c | +127.4c | 3.90 |
| 2026-11-04 | 2 | 0 | 2 | -4.2c | +123.2c | 3.56 |

### GEN6_B12

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | rng5>0.32 & hour>19 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.83 (n 102), validation PF 1.32 (n 72), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 4 days; zero-volume trades 0.
PF at 1 contract 0.53, at 10 contracts 0.56, at 10 contracts with fees x1.2 0.55; net per contract -6.09c at 1, -5.53c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +5.4c | +5.4c | 1.11 |
| 2026-10-31 | 2 | 0 | 2 | -32.4c | -27.0c | 0.67 |
| 2026-11-01 | 1 | 0 | 1 | -13.8c | -40.8c | 0.58 |
| 2026-11-02 | 2 | 0 | 2 | -3.4c | -44.2c | 0.56 |

### GEN6_B13

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | m1>-0.2 & hour>19 | TP +8c stop -20c else hold]; fill at the next candle's ask. Discovery PF 1.70 (n 173), validation PF 1.31 (n 129), C=10.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 16 on 5 days; zero-volume trades 0.
PF at 1 contract 2.28, at 10 contracts 2.56, at 10 contracts with fees x1.2 2.51; net per contract +6.53c at 1, +7.38c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -65.5c | -65.5c | 0.00 |
| 2026-10-31 | 3 | 3 | 0 | +49.0c | -16.5c | 0.75 |
| 2026-11-01 | 2 | 1 | 1 | +59.7c | +43.2c | 1.64 |
| 2026-11-02 | 3 | 2 | 1 | +55.7c | +98.9c | 2.44 |
| 2026-11-03 | 5 | 2 | 3 | +19.2c | +118.1c | 2.56 |

### REF_BTC_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T02:00:00Z. The mirror of FALS3's finding (Bitcoin favourites at 50c to 85c are overpriced 2 to 3 minutes before the close: PF 0.77 on 2,576 windows, z -4.97): buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held to settlement. History already read (UNDER1 found this side positive), so only forward days count; REV1 is the registered forward read of the related cheap-NO rule (2026-11-05). 1 try.
Windows evaluated 506 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 154 on 6 days; zero-volume trades 0.
PF at 1 contract 1.22, at 10 contracts 1.25, at 10 contracts with fees x1.2 1.23; net per contract +4.42c at 1, +4.82c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 25 | 6 | 19 | -206.1c | -206.1c | 0.65 |
| 2026-10-31 | 31 | 13 | 18 | +261.8c | +55.7c | 1.05 |
| 2026-11-01 | 24 | 10 | 14 | +194.0c | +249.7c | 1.16 |
| 2026-11-02 | 28 | 12 | 16 | +265.8c | +515.5c | 1.25 |
| 2026-11-03 | 38 | 14 | 24 | +191.4c | +706.9c | 1.25 |
| 2026-11-04 | 8 | 3 | 5 | +36.0c | +742.9c | 1.25 |

### GEN7_B01

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 240..240s | npv1>0.281 & vol>1.32e+05 | sell at 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 3.28 (n 101), validation PF 1.80 (n 126), C=10.
Windows evaluated 510 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 5 days; zero-volume trades 0.
PF at 1 contract 4.39, at 10 contracts 5.53, at 10 contracts with fees x1.2 5.41; net per contract +12.04c at 1, +13.02c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -12.8c | -12.8c | 0.00 |
| 2026-10-31 | 1 | 0 | 1 | -5.8c | -18.6c | 0.00 |
| 2026-11-01 | 4 | 2 | 2 | +85.2c | +66.6c | 3.86 |
| 2026-11-02 | 3 | 1 | 2 | +51.1c | +117.7c | 4.69 |
| 2026-11-03 | 3 | 1 | 2 | +38.5c | +156.2c | 5.53 |

### GEN7_B02

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 300..240s | npv1>0.393 & doi5>9.78e+04 | TP +20c stop -20c else sell 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 1.75 (n 135), validation PF 1.71 (n 101), C=10.
Windows evaluated 510 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 19 on 5 days; zero-volume trades 0.
PF at 1 contract 0.73, at 10 contracts 0.81, at 10 contracts with fees x1.2 0.79; net per contract -3.02c at 1, -2.01c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 4 | 1 | 3 | -54.8c | -54.8c | 0.19 |
| 2026-11-01 | 7 | 3 | 4 | +86.4c | +31.6c | 1.25 |
| 2026-11-02 | 4 | 0 | 4 | -44.6c | -13.0c | 0.92 |
| 2026-11-03 | 3 | 0 | 3 | -21.7c | -34.7c | 0.82 |
| 2026-11-04 | 1 | 0 | 1 | -3.4c | -38.1c | 0.81 |

### REF_GEN6_OIDRIFT

Evaluator `scalper.oidrift:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest over the 3 minutes before rose above the 90th percentile of that change over the 30 UTC days before (earlier days only, 20+ days needed), fill at the next candle's ask, held. History validation n 67, PF 2.65 (FALS4 check 5, reproduced). Not independent of REF_GEN6_OICORE. 1 try; workers/OIDRIFT_REGISTRATION.md.
Windows evaluated 510 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -44.00c at 1, -43.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -43.8c | -43.8c | 0.00 |

### REF_GOLD_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. Gold version of REF_BTC_UNDERDOG_180: FALS3 found gold favourites at 50c to 85c, 2 to 3 minutes before the close, also below break-even (PF 0.85). Buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held. Forward days only. 1 try.
Windows evaluated 299 on 5 days; without the data the rule needs 0; evaluator errors 0. Trades 103 on 4 days; zero-volume trades 0.
PF at 1 contract 0.69, at 10 contracts 0.71, at 10 contracts with fees x1.2 0.70; net per contract -6.93c at 1, -6.43c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 31 | 7 | 24 | -282.0c | -282.0c | 0.61 |
| 2026-11-02 | 29 | 6 | 23 | -311.5c | -593.5c | 0.59 |
| 2026-11-03 | 34 | 11 | 23 | +100.6c | -492.9c | 0.76 |
| 2026-11-04 | 9 | 1 | 8 | -169.9c | -662.8c | 0.71 |

### REF_LATECAL_BTC

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. LATECAL's one chosen cell (Bitcoin, 90 to 60 s left, ask 0.95 to 0.98: 61 of 61 won on the recorder, NOT_ENOUGH_DATA; needs about 800 windows to clear the 97.7% break-even) tracked forward. Candles only: the nearest candle is the one ending 60 s before the close, so this approximates the recorder's 90 to 60 s cell. L1-family, held to settlement.
Windows evaluated 510 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 31 on 6 days; zero-volume trades 0.
PF at 1 contract 0.73, at 10 contracts 0.96, at 10 contracts with fees x1.2 0.95; net per contract -0.84c at 1, -0.12c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 6 | 5 | 1 | -79.5c | -79.5c | 0.17 |
| 2026-10-31 | 5 | 5 | 0 | +17.4c | -62.1c | 0.35 |
| 2026-11-01 | 7 | 7 | 0 | +24.9c | -37.2c | 0.61 |
| 2026-11-02 | 4 | 4 | 0 | +9.8c | -27.4c | 0.71 |
| 2026-11-03 | 8 | 8 | 0 | +19.0c | -8.4c | 0.91 |
| 2026-11-04 | 1 | 1 | 0 | +4.6c | -3.8c | 0.96 |

### GEN4_B01

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and zd >= -1.585; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.13 n 46; validation PF1 2.64 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 100 on 6 days; zero-volume trades 0.
PF at 1 contract 0.83, at 10 contracts 0.88, at 10 contracts with fees x1.2 0.87; net per contract -3.50c at 1, -2.38c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +73.8c | +73.8c | 1.34 |
| 2026-10-31 | 17 | 10 | 7 | -165.8c | -92.0c | 0.86 |
| 2026-11-01 | 28 | 18 | 10 | -57.7c | -149.7c | 0.88 |
| 2026-11-02 | 20 | 13 | 7 | -120.1c | -269.8c | 0.83 |
| 2026-11-03 | 15 | 11 | 4 | +18.2c | -251.6c | 0.87 |
| 2026-11-04 | 7 | 5 | 2 | +13.2c | -238.4c | 0.88 |

### GEN4_B02

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and zd >= -2.066; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.09 n 51; validation PF1 2.40 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 99 on 6 days; zero-volume trades 0.
PF at 1 contract 0.81, at 10 contracts 0.86, at 10 contracts with fees x1.2 0.85; net per contract -3.71c at 1, -2.64c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -89.3c | -89.3c | 0.74 |
| 2026-10-31 | 14 | 9 | 5 | -10.8c | -100.1c | 0.84 |
| 2026-11-01 | 27 | 18 | 9 | -12.8c | -112.9c | 0.90 |
| 2026-11-02 | 18 | 11 | 7 | -100.5c | -213.4c | 0.85 |
| 2026-11-03 | 17 | 12 | 5 | -78.4c | -291.8c | 0.84 |
| 2026-11-04 | 8 | 6 | 2 | +30.4c | -261.4c | 0.86 |

### GEN4_B03

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and sp15 >= -0.1949 and zd >= -0.3503; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.62 n 40; validation PF1 2.39 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 92 on 6 days; zero-volume trades 0.
PF at 1 contract 1.07, at 10 contracts 1.12, at 10 contracts with fees x1.2 1.11; net per contract +1.52c at 1, +2.51c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 4 | 6 | -110.1c | -110.1c | 0.58 |
| 2026-10-31 | 17 | 8 | 9 | -42.3c | -152.4c | 0.78 |
| 2026-11-01 | 25 | 11 | 14 | -180.6c | -333.0c | 0.74 |
| 2026-11-02 | 18 | 12 | 6 | +237.2c | -95.8c | 0.94 |
| 2026-11-03 | 16 | 10 | 6 | +89.8c | -6.0c | 1.00 |
| 2026-11-04 | 6 | 5 | 1 | +236.6c | +230.6c | 1.12 |

### GEN4_B04

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.17 and lsz_ask <= 8.072 and lsz_bid <= 8.053; bought at that ask; held to settlement. Discovery PF1 2.04 n 41; validation PF1 2.27 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 102 on 6 days; zero-volume trades 0.
PF at 1 contract 0.91, at 10 contracts 0.93, at 10 contracts with fees x1.2 0.92; net per contract -1.89c at 1, -1.41c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 12 | 2 | +160.7c | +160.7c | 2.08 |
| 2026-10-31 | 19 | 11 | 8 | -274.5c | -113.8c | 0.85 |
| 2026-11-01 | 29 | 21 | 8 | +57.7c | -56.1c | 0.96 |
| 2026-11-02 | 20 | 12 | 8 | -241.0c | -297.1c | 0.84 |
| 2026-11-03 | 14 | 11 | 3 | +163.3c | -133.8c | 0.93 |
| 2026-11-04 | 6 | 4 | 2 | -10.3c | -144.1c | 0.93 |

### GEN4_B05

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 41; validation PF1 2.18 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 81 on 6 days; zero-volume trades 0.
PF at 1 contract 1.35, at 10 contracts 1.43, at 10 contracts with fees x1.2 1.41; net per contract +4.66c at 1, +5.54c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -91.0c | -91.0c | 0.62 |
| 2026-10-31 | 16 | 8 | 8 | +64.4c | -26.6c | 0.94 |
| 2026-11-01 | 16 | 6 | 10 | -27.0c | -53.6c | 0.93 |
| 2026-11-02 | 18 | 10 | 8 | +371.1c | +317.5c | 1.38 |
| 2026-11-03 | 11 | 5 | 6 | -56.6c | +260.9c | 1.25 |
| 2026-11-04 | 7 | 4 | 3 | +188.0c | +448.9c | 1.43 |

### GEN4_B06

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.54 n 52; validation PF1 2.08 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 104 on 6 days; zero-volume trades 0.
PF at 1 contract 1.35, at 10 contracts 1.39, at 10 contracts with fees x1.2 1.37; net per contract +4.72c at 1, +5.17c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | -148.3c | -148.3c | 0.49 |
| 2026-10-31 | 17 | 8 | 9 | +78.9c | -69.4c | 0.88 |
| 2026-11-01 | 20 | 7 | 13 | -123.4c | -192.8c | 0.80 |
| 2026-11-02 | 23 | 12 | 11 | +380.0c | +187.2c | 1.16 |
| 2026-11-03 | 15 | 8 | 7 | +137.1c | +324.3c | 1.24 |
| 2026-11-04 | 9 | 5 | 4 | +213.9c | +538.2c | 1.39 |

### GEN4_B07

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= 0.3412 and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.68 n 43; validation PF1 2.08 n 24 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 61 on 5 days; zero-volume trades 0.
PF at 1 contract 1.08, at 10 contracts 1.13, at 10 contracts with fees x1.2 1.12; net per contract +1.25c at 1, +2.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 16 | 7 | 9 | +25.3c | +25.3c | 1.08 |
| 2026-11-01 | 22 | 6 | 16 | -210.7c | -185.4c | 0.75 |
| 2026-11-02 | 12 | 7 | 5 | +236.8c | +51.4c | 1.06 |
| 2026-11-03 | 10 | 5 | 5 | +86.1c | +137.5c | 1.14 |
| 2026-11-04 | 1 | 0 | 1 | -7.1c | +130.4c | 1.13 |

### GEN4_B08

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.24 n 52; validation PF1 1.99 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 106 on 6 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.83; net per contract -4.40c at 1, -3.31c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -65.0c | -65.0c | 0.81 |
| 2026-10-31 | 17 | 12 | 5 | -0.6c | -65.6c | 0.90 |
| 2026-11-01 | 28 | 19 | 9 | -91.5c | -157.1c | 0.88 |
| 2026-11-02 | 19 | 11 | 8 | -215.6c | -372.7c | 0.79 |
| 2026-11-03 | 17 | 12 | 5 | -35.5c | -408.2c | 0.81 |
| 2026-11-04 | 9 | 7 | 2 | +57.7c | -350.5c | 0.85 |

### GEN4_B09

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= -0.06831; bought at that ask; held to settlement. Discovery PF1 1.51 n 49; validation PF1 1.94 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 101 on 6 days; zero-volume trades 0.
PF at 1 contract 1.01, at 10 contracts 1.03, at 10 contracts with fees x1.2 1.02; net per contract +0.13c at 1, +0.56c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -122.4c | -122.4c | 0.55 |
| 2026-10-31 | 21 | 9 | 12 | -122.9c | -245.3c | 0.68 |
| 2026-11-01 | 26 | 9 | 17 | -168.2c | -413.5c | 0.67 |
| 2026-11-02 | 19 | 10 | 9 | +361.3c | -52.2c | 0.96 |
| 2026-11-03 | 15 | 6 | 9 | -80.2c | -132.4c | 0.92 |
| 2026-11-04 | 7 | 4 | 3 | +188.8c | +56.4c | 1.03 |

### GEN4_B10

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 <= 2.256 and sp5 <= 0.353; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.79 n 46; validation PF1 1.93 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 93 on 6 days; zero-volume trades 0.
PF at 1 contract 0.68, at 10 contracts 0.73, at 10 contracts with fees x1.2 0.72; net per contract -7.05c at 1, -5.92c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 10 | 4 | -57.6c | -57.6c | 0.80 |
| 2026-10-31 | 17 | 9 | 8 | -254.0c | -311.6c | 0.61 |
| 2026-11-01 | 25 | 17 | 8 | +13.5c | -298.1c | 0.76 |
| 2026-11-02 | 15 | 9 | 6 | -68.2c | -366.3c | 0.76 |
| 2026-11-03 | 15 | 10 | 5 | -121.6c | -487.9c | 0.74 |
| 2026-11-04 | 7 | 5 | 2 | -62.3c | -550.2c | 0.73 |

### GEN4_B11

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp30 >= 0.5295; bought at that ask; held to settlement. Discovery PF1 1.50 n 46; validation PF1 1.91 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 92 on 6 days; zero-volume trades 0.
PF at 1 contract 1.21, at 10 contracts 1.25, at 10 contracts with fees x1.2 1.23; net per contract +2.84c at 1, +3.32c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 4 | 13 | -83.1c | -83.1c | 0.60 |
| 2026-10-31 | 14 | 5 | 9 | -30.3c | -113.4c | 0.76 |
| 2026-11-01 | 17 | 6 | 11 | -110.0c | -223.4c | 0.72 |
| 2026-11-02 | 22 | 12 | 10 | +274.3c | +50.9c | 1.05 |
| 2026-11-03 | 14 | 8 | 6 | +79.8c | +130.7c | 1.11 |
| 2026-11-04 | 8 | 4 | 4 | +174.9c | +305.6c | 1.25 |

### GEN4_B12

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.16 and lsz_ask <= 7.779 and sp5 >= 0.1732; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.32 n 43; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 100 on 6 days; zero-volume trades 0.
PF at 1 contract 1.06, at 10 contracts 1.12, at 10 contracts with fees x1.2 1.11; net per contract +1.10c at 1, +2.27c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 11 | 1 | +258.6c | +258.6c | 4.18 |
| 2026-10-31 | 19 | 13 | 6 | -25.6c | +233.0c | 1.48 |
| 2026-11-01 | 26 | 16 | 10 | -217.1c | +15.9c | 1.01 |
| 2026-11-02 | 20 | 13 | 7 | -112.7c | -96.8c | 0.94 |
| 2026-11-03 | 15 | 12 | 3 | +171.5c | +74.7c | 1.04 |
| 2026-11-04 | 8 | 7 | 1 | +152.4c | +227.1c | 1.12 |

### GEN4_B13

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.65 n 56; validation PF1 1.90 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 115 on 6 days; zero-volume trades 0.
PF at 1 contract 0.75, at 10 contracts 0.80, at 10 contracts with fees x1.2 0.79; net per contract -5.28c at 1, -4.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.8c | -12.8c | 0.96 |
| 2026-10-31 | 19 | 11 | 8 | -215.6c | -228.4c | 0.73 |
| 2026-11-01 | 30 | 19 | 11 | -122.7c | -351.1c | 0.76 |
| 2026-11-02 | 21 | 13 | 8 | -111.0c | -462.1c | 0.76 |
| 2026-11-03 | 17 | 12 | 5 | -44.5c | -506.6c | 0.77 |
| 2026-11-04 | 9 | 7 | 2 | +30.8c | -475.8c | 0.80 |

### GEN4_B14

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and lsz_ask <= 7.779; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.30 n 44; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 88 on 6 days; zero-volume trades 0.
PF at 1 contract 1.10, at 10 contracts 1.17, at 10 contracts with fees x1.2 1.16; net per contract +1.84c at 1, +3.08c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 10 | 2 | +136.8c | +136.8c | 1.99 |
| 2026-10-31 | 16 | 11 | 5 | +25.4c | +162.2c | 1.37 |
| 2026-11-01 | 25 | 17 | 8 | -40.7c | +121.5c | 1.13 |
| 2026-11-02 | 16 | 11 | 5 | -33.3c | +88.2c | 1.07 |
| 2026-11-03 | 14 | 11 | 3 | +114.4c | +202.6c | 1.14 |
| 2026-11-04 | 5 | 4 | 1 | +68.1c | +270.7c | 1.17 |

### GEN4_B15

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26 and sp15 >= -0.01237 and spread >= 0.001; bought at that ask; held to settlement. Discovery PF1 1.55 n 42; validation PF1 1.86 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 89 on 6 days; zero-volume trades 0.
PF at 1 contract 0.81, at 10 contracts 0.83, at 10 contracts with fees x1.2 0.82; net per contract -4.19c at 1, -3.77c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 4 | 7 | -206.0c | -206.0c | 0.31 |
| 2026-10-31 | 17 | 8 | 9 | -194.7c | -400.7c | 0.49 |
| 2026-11-01 | 23 | 10 | 13 | -304.5c | -705.2c | 0.49 |
| 2026-11-02 | 19 | 12 | 7 | +207.6c | -497.6c | 0.70 |
| 2026-11-03 | 14 | 9 | 5 | +95.8c | -401.8c | 0.79 |
| 2026-11-04 | 5 | 3 | 2 | +66.5c | -335.3c | 0.83 |

### GEN4_B16

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and spread <= 0.01; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.14 n 48; validation PF1 1.83 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 103 on 6 days; zero-volume trades 0.
PF at 1 contract 0.83, at 10 contracts 0.88, at 10 contracts with fees x1.2 0.87; net per contract -3.73c at 1, -2.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +100.3c | +100.3c | 1.46 |
| 2026-10-31 | 19 | 12 | 7 | -135.8c | -35.5c | 0.95 |
| 2026-11-01 | 29 | 19 | 10 | -131.2c | -166.7c | 0.88 |
| 2026-11-02 | 19 | 12 | 7 | -169.2c | -335.9c | 0.82 |
| 2026-11-03 | 15 | 11 | 4 | +61.6c | -274.3c | 0.87 |
| 2026-11-04 | 7 | 5 | 2 | +16.4c | -257.9c | 0.88 |

### GEN4_B17

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.4847 and zd >= -2.066; bought at that ask; held to settlement. Discovery PF1 1.52 n 48; validation PF1 1.82 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 91 on 6 days; zero-volume trades 0.
PF at 1 contract 0.77, at 10 contracts 0.79, at 10 contracts with fees x1.2 0.78; net per contract -5.18c at 1, -4.74c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 13 | 4 | +24.0c | +24.0c | 1.08 |
| 2026-10-31 | 14 | 6 | 8 | -419.1c | -395.1c | 0.55 |
| 2026-11-01 | 24 | 18 | 6 | +60.0c | -335.1c | 0.74 |
| 2026-11-02 | 14 | 8 | 6 | -120.2c | -455.3c | 0.72 |
| 2026-11-03 | 14 | 10 | 4 | +47.6c | -407.7c | 0.79 |
| 2026-11-04 | 8 | 6 | 2 | -23.5c | -431.2c | 0.79 |

### GEN4_B18

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and lsz_ask <= 7.779 and zd >= -0.6765; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.63 n 43; validation PF1 1.81 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 97 on 6 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.84; net per contract -4.16c at 1, -3.05c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 9 | 3 | +57.1c | +57.1c | 1.28 |
| 2026-10-31 | 17 | 10 | 7 | -145.2c | -88.1c | 0.86 |
| 2026-11-01 | 28 | 19 | 9 | +19.9c | -68.2c | 0.94 |
| 2026-11-02 | 18 | 12 | 6 | -67.7c | -135.9c | 0.91 |
| 2026-11-03 | 15 | 9 | 6 | -151.4c | -287.3c | 0.84 |
| 2026-11-04 | 7 | 5 | 2 | -8.3c | -295.6c | 0.85 |

### GEN4_B19

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and imb >= -0.6701; bought at that ask; held to settlement. Discovery PF1 1.78 n 48; validation PF1 1.81 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 93 on 6 days; zero-volume trades 0.
PF at 1 contract 0.82, at 10 contracts 0.84, at 10 contracts with fees x1.2 0.82; net per contract -4.12c at 1, -3.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -52.6c | -52.6c | 0.85 |
| 2026-10-31 | 16 | 10 | 6 | -136.8c | -189.4c | 0.76 |
| 2026-11-01 | 24 | 17 | 7 | +18.5c | -170.9c | 0.86 |
| 2026-11-02 | 15 | 8 | 7 | -220.1c | -391.0c | 0.77 |
| 2026-11-03 | 15 | 11 | 4 | +57.8c | -333.2c | 0.83 |
| 2026-11-04 | 6 | 4 | 2 | -10.8c | -344.0c | 0.84 |

### GEN4_B20

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and imb >= -0.4281 and sp5 <= 0; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.66 n 43; validation PF1 1.77 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 81 on 6 days; zero-volume trades 0.
PF at 1 contract 0.70, at 10 contracts 0.75, at 10 contracts with fees x1.2 0.74; net per contract -6.53c at 1, -5.46c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -55.9c | -55.9c | 0.80 |
| 2026-10-31 | 13 | 9 | 4 | +24.2c | -31.7c | 0.94 |
| 2026-11-01 | 23 | 16 | 7 | +53.3c | +21.6c | 1.02 |
| 2026-11-02 | 13 | 6 | 7 | -249.2c | -227.6c | 0.82 |
| 2026-11-03 | 14 | 9 | 5 | -125.6c | -353.2c | 0.78 |
| 2026-11-04 | 5 | 3 | 2 | -89.0c | -442.2c | 0.75 |

### GEN4_B21

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.902 and lsz_bid >= 7.292; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.54 n 44; validation PF1 1.76 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 57 on 6 days; zero-volume trades 0.
PF at 1 contract 0.61, at 10 contracts 0.65, at 10 contracts with fees x1.2 0.64; net per contract -9.96c at 1, -8.91c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 9 | 5 | -132.3c | -132.3c | 0.62 |
| 2026-10-31 | 1 | 0 | 1 | -70.5c | -202.8c | 0.51 |
| 2026-11-01 | 11 | 9 | 2 | +69.5c | -133.3c | 0.76 |
| 2026-11-02 | 13 | 7 | 6 | -194.3c | -327.6c | 0.66 |
| 2026-11-03 | 12 | 7 | 5 | -142.6c | -470.2c | 0.63 |
| 2026-11-04 | 6 | 4 | 2 | -37.8c | -508.0c | 0.65 |

### GEN4_B22

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.456 and lsz_bid >= 6.195; bought at that ask; held to settlement. Discovery PF1 1.63 n 49; validation PF1 1.73 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 105 on 6 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.80, at 10 contracts with fees x1.2 0.79; net per contract -4.82c at 1, -4.39c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -44.0c | -44.0c | 0.87 |
| 2026-10-31 | 18 | 12 | 6 | -67.7c | -111.7c | 0.86 |
| 2026-11-01 | 27 | 16 | 11 | -317.3c | -429.0c | 0.71 |
| 2026-11-02 | 18 | 10 | 8 | -240.2c | -669.2c | 0.67 |
| 2026-11-03 | 17 | 14 | 3 | +169.4c | -499.8c | 0.77 |
| 2026-11-04 | 8 | 6 | 2 | +39.2c | -460.6c | 0.80 |

### GEN4_B23

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; held to settlement. Discovery PF1 1.55 n 40; validation PF1 1.71 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 68 on 5 days; zero-volume trades 0.
PF at 1 contract 0.74, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.75; net per contract -6.06c at 1, -5.58c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.6c | +24.6c | inf |
| 2026-10-31 | 16 | 8 | 8 | -326.0c | -301.4c | 0.47 |
| 2026-11-01 | 26 | 20 | 6 | +139.6c | -161.8c | 0.83 |
| 2026-11-02 | 14 | 8 | 6 | -159.0c | -320.8c | 0.76 |
| 2026-11-03 | 11 | 7 | 4 | -58.6c | -379.4c | 0.76 |

### GEN4_B24

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.292; bought at that ask; held to settlement. Discovery PF1 2.01 n 50; validation PF1 1.65 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 85 on 6 days; zero-volume trades 0.
PF at 1 contract 0.70, at 10 contracts 0.72, at 10 contracts with fees x1.2 0.70; net per contract -7.09c at 1, -6.68c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -54.9c | -54.9c | 0.84 |
| 2026-10-31 | 7 | 5 | 2 | +28.0c | -26.9c | 0.94 |
| 2026-11-01 | 19 | 10 | 9 | -375.6c | -402.5c | 0.62 |
| 2026-11-02 | 18 | 11 | 7 | -157.0c | -559.5c | 0.63 |
| 2026-11-03 | 17 | 12 | 5 | -53.1c | -612.6c | 0.67 |
| 2026-11-04 | 8 | 6 | 2 | +45.2c | -567.4c | 0.72 |

### GEN4_B25

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.00 n 40; validation PF1 1.64 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 85 on 6 days; zero-volume trades 0.
PF at 1 contract 0.86, at 10 contracts 0.91, at 10 contracts with fees x1.2 0.90; net per contract -2.93c at 1, -1.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 6 | 4 | -85.4c | -85.4c | 0.71 |
| 2026-10-31 | 17 | 10 | 7 | -216.7c | -302.1c | 0.61 |
| 2026-11-01 | 22 | 16 | 6 | +27.5c | -274.6c | 0.77 |
| 2026-11-02 | 17 | 10 | 7 | -223.1c | -497.7c | 0.70 |
| 2026-11-03 | 14 | 12 | 2 | +192.4c | -305.3c | 0.83 |
| 2026-11-04 | 5 | 5 | 0 | +149.5c | -155.8c | 0.91 |

### GEN4_B26

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and lsz_bid >= 5.465; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.57 n 49; validation PF1 1.63 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 96 on 6 days; zero-volume trades 0.
PF at 1 contract 0.67, at 10 contracts 0.72, at 10 contracts with fees x1.2 0.71; net per contract -7.84c at 1, -6.75c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -37.3c | -37.3c | 0.89 |
| 2026-10-31 | 16 | 8 | 8 | -347.5c | -384.8c | 0.59 |
| 2026-11-01 | 24 | 16 | 8 | -129.8c | -514.6c | 0.64 |
| 2026-11-02 | 16 | 9 | 7 | -187.7c | -702.3c | 0.63 |
| 2026-11-03 | 15 | 11 | 4 | +51.2c | -651.1c | 0.70 |
| 2026-11-04 | 7 | 5 | 2 | +3.2c | -647.9c | 0.72 |

### GEN4_B27

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.52 n 40; validation PF1 1.63 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 68 on 5 days; zero-volume trades 0.
PF at 1 contract 0.71, at 10 contracts 0.75, at 10 contracts with fees x1.2 0.74; net per contract -6.91c at 1, -5.76c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 16 | 8 | 8 | -327.4c | -303.0c | 0.47 |
| 2026-11-01 | 26 | 20 | 6 | +134.2c | -168.8c | 0.83 |
| 2026-11-02 | 14 | 8 | 6 | -161.3c | -330.1c | 0.75 |
| 2026-11-03 | 11 | 7 | 4 | -61.5c | -391.6c | 0.75 |

### GEN4_B28

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and lsz_ask <= 7.388; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.92 n 40; validation PF1 1.61 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 84 on 6 days; zero-volume trades 0.
PF at 1 contract 0.88, at 10 contracts 0.93, at 10 contracts with fees x1.2 0.92; net per contract -2.63c at 1, -1.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 7 | 2 | +57.7c | +57.7c | 1.46 |
| 2026-10-31 | 18 | 11 | 7 | -180.5c | -122.8c | 0.80 |
| 2026-11-01 | 25 | 18 | 7 | +51.3c | -71.5c | 0.93 |
| 2026-11-02 | 15 | 11 | 4 | +30.4c | -41.1c | 0.97 |
| 2026-11-03 | 13 | 8 | 5 | -110.4c | -151.5c | 0.91 |
| 2026-11-04 | 4 | 3 | 1 | +25.1c | -126.4c | 0.93 |

### GEN4_B29

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.1233; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.26 n 51; validation PF1 1.61 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 104 on 6 days; zero-volume trades 0.
PF at 1 contract 0.95, at 10 contracts 1.01, at 10 contracts with fees x1.2 0.99; net per contract -1.04c at 1, +0.17c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +106.3c | +106.3c | 1.48 |
| 2026-10-31 | 17 | 12 | 5 | +29.0c | +135.3c | 1.26 |
| 2026-11-01 | 28 | 19 | 9 | -99.6c | +35.7c | 1.03 |
| 2026-11-02 | 18 | 11 | 7 | -131.1c | -95.4c | 0.94 |
| 2026-11-03 | 17 | 13 | 4 | +59.2c | -36.2c | 0.98 |
| 2026-11-04 | 9 | 7 | 2 | +53.6c | +17.4c | 1.01 |

### GEN4_B30

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask >= 7.388 and sp15 >= -0.9017 and sp30 <= 2.256; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 45; validation PF1 1.61 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 79 on 6 days; zero-volume trades 0.
PF at 1 contract 0.74, at 10 contracts 0.78, at 10 contracts with fees x1.2 0.77; net per contract -5.75c at 1, -4.67c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -46.3c | -46.3c | 0.83 |
| 2026-10-31 | 12 | 6 | 6 | -275.9c | -322.2c | 0.55 |
| 2026-11-01 | 21 | 15 | 6 | -56.9c | -379.1c | 0.66 |
| 2026-11-02 | 14 | 9 | 5 | -94.9c | -474.0c | 0.66 |
| 2026-11-03 | 13 | 10 | 3 | +59.0c | -415.0c | 0.74 |
| 2026-11-04 | 6 | 5 | 1 | +46.2c | -368.8c | 0.78 |

### GEN4_B31

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid <= 8.422; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.71 n 55; validation PF1 1.59 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 114 on 6 days; zero-volume trades 0.
PF at 1 contract 0.83, at 10 contracts 0.88, at 10 contracts with fees x1.2 0.87; net per contract -3.64c at 1, -2.49c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 15 | 4 | +69.2c | +69.2c | 1.24 |
| 2026-10-31 | 19 | 11 | 8 | -277.5c | -208.3c | 0.76 |
| 2026-11-01 | 30 | 21 | 9 | -26.9c | -235.2c | 0.84 |
| 2026-11-02 | 21 | 14 | 7 | -56.0c | -291.2c | 0.85 |
| 2026-11-03 | 15 | 10 | 5 | -29.4c | -320.6c | 0.86 |
| 2026-11-04 | 10 | 8 | 2 | +36.6c | -284.0c | 0.88 |

### GEN4_B32

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.95 n 40; validation PF1 1.57 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 87 on 6 days; zero-volume trades 0.
PF at 1 contract 0.95, at 10 contracts 1.01, at 10 contracts with fees x1.2 1.00; net per contract -0.86c at 1, +0.23c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +24.3c | +24.3c | 1.11 |
| 2026-10-31 | 19 | 12 | 7 | -100.0c | -75.7c | 0.88 |
| 2026-11-01 | 22 | 14 | 8 | -78.2c | -153.9c | 0.86 |
| 2026-11-02 | 17 | 12 | 5 | -30.0c | -183.9c | 0.86 |
| 2026-11-03 | 14 | 11 | 3 | +61.9c | -122.0c | 0.92 |
| 2026-11-04 | 5 | 5 | 0 | +142.2c | +20.2c | 1.01 |

### GEN4_B33

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and spread >= 0.001 and vol <= 0.311; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.59 n 40; validation PF1 1.54 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 68 on 5 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.77, at 10 contracts with fees x1.2 0.76; net per contract -6.56c at 1, -5.28c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 16 | 8 | 8 | -288.5c | -264.1c | 0.50 |
| 2026-11-01 | 26 | 20 | 6 | +129.0c | -135.1c | 0.86 |
| 2026-11-02 | 14 | 8 | 6 | -163.9c | -299.0c | 0.77 |
| 2026-11-03 | 11 | 7 | 4 | -60.3c | -359.3c | 0.77 |

### GEN4_B34

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 6.824 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.83 n 52; validation PF1 1.54 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 102 on 6 days; zero-volume trades 0.
PF at 1 contract 0.71, at 10 contracts 0.73, at 10 contracts with fees x1.2 0.72; net per contract -6.79c at 1, -6.38c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -28.0c | -28.0c | 0.92 |
| 2026-10-31 | 13 | 8 | 5 | -71.3c | -99.3c | 0.85 |
| 2026-11-01 | 27 | 16 | 11 | -335.8c | -435.1c | 0.69 |
| 2026-11-02 | 19 | 11 | 8 | -217.6c | -652.7c | 0.66 |
| 2026-11-03 | 17 | 12 | 5 | -43.5c | -696.2c | 0.69 |
| 2026-11-04 | 8 | 6 | 2 | +45.2c | -651.0c | 0.73 |

### GEN4_B35

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and sp15 >= 1.584 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 2.38 n 41; validation PF1 1.52 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 79 on 6 days; zero-volume trades 0.
PF at 1 contract 1.78, at 10 contracts 1.85, at 10 contracts with fees x1.2 1.82; net per contract +9.04c at 1, +9.54c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | +180.7c | +180.7c | 1.87 |
| 2026-10-31 | 7 | 3 | 4 | +92.6c | +273.3c | 1.85 |
| 2026-11-01 | 10 | 5 | 5 | +286.9c | +560.2c | 2.44 |
| 2026-11-02 | 20 | 3 | 17 | -50.1c | +510.1c | 1.74 |
| 2026-11-03 | 10 | 4 | 6 | +175.1c | +685.2c | 1.88 |
| 2026-11-04 | 12 | 2 | 10 | +68.7c | +753.9c | 1.85 |

### GEN4_B36

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.83 n 40; validation PF1 1.52 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 87 on 6 days; zero-volume trades 0.
PF at 1 contract 0.95, at 10 contracts 1.01, at 10 contracts with fees x1.2 0.99; net per contract -1.04c at 1, +0.16c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +25.7c | +25.7c | 1.12 |
| 2026-10-31 | 19 | 12 | 7 | -121.6c | -95.9c | 0.85 |
| 2026-11-01 | 22 | 15 | 7 | -72.0c | -167.9c | 0.85 |
| 2026-11-02 | 17 | 12 | 5 | -51.3c | -219.2c | 0.85 |
| 2026-11-03 | 14 | 11 | 3 | +83.6c | -135.6c | 0.92 |
| 2026-11-04 | 5 | 5 | 0 | +149.4c | +13.8c | 1.01 |

### GEN4_B37

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm30 <= 0.17 and sp5 >= 0.353 and spread >= 0.001; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.52 n 43; validation PF1 1.49 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 91 on 6 days; zero-volume trades 0.
PF at 1 contract 1.28, at 10 contracts 1.38, at 10 contracts with fees x1.2 1.35; net per contract +3.53c at 1, +4.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 3 | 11 | -119.8c | -119.8c | 0.54 |
| 2026-10-31 | 17 | 7 | 10 | +90.6c | -29.2c | 0.94 |
| 2026-11-01 | 25 | 10 | 15 | -25.0c | -54.2c | 0.93 |
| 2026-11-02 | 15 | 8 | 7 | +323.3c | +269.1c | 1.29 |
| 2026-11-03 | 12 | 4 | 8 | -52.8c | +216.3c | 1.20 |
| 2026-11-04 | 8 | 4 | 4 | +193.0c | +409.3c | 1.38 |

### GEN4_B38

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 <= 0.0315; bought at that ask; held to settlement. Discovery PF1 1.50 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 108 on 6 days; zero-volume trades 0.
PF at 1 contract 0.68, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -7.91c at 1, -7.45c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -112.6c | -112.6c | 0.69 |
| 2026-10-31 | 19 | 11 | 8 | -285.1c | -397.7c | 0.59 |
| 2026-11-01 | 29 | 20 | 9 | -37.5c | -435.2c | 0.72 |
| 2026-11-02 | 19 | 11 | 8 | -247.0c | -682.2c | 0.67 |
| 2026-11-03 | 17 | 11 | 6 | -110.6c | -792.8c | 0.68 |
| 2026-11-04 | 9 | 7 | 2 | -11.7c | -804.5c | 0.70 |

### GEN4_B39

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.01237; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.44 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 105 on 6 days; zero-volume trades 0.
PF at 1 contract 0.81, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.84; net per contract -4.25c at 1, -3.17c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +168.7c | +168.7c | 1.84 |
| 2026-10-31 | 17 | 9 | 8 | -306.9c | -138.2c | 0.82 |
| 2026-11-01 | 27 | 20 | 7 | +115.7c | -22.5c | 0.98 |
| 2026-11-02 | 20 | 11 | 9 | -220.8c | -243.3c | 0.86 |
| 2026-11-03 | 16 | 11 | 5 | -25.3c | -268.6c | 0.87 |
| 2026-11-04 | 8 | 5 | 3 | -64.4c | -333.0c | 0.85 |

### GEN4_B40

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.9734; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.57 n 55; validation PF1 1.44 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 114 on 6 days; zero-volume trades 0.
PF at 1 contract 0.75, at 10 contracts 0.80, at 10 contracts with fees x1.2 0.79; net per contract -5.56c at 1, -4.33c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.7c | -12.7c | 0.96 |
| 2026-10-31 | 19 | 11 | 8 | -245.4c | -258.1c | 0.71 |
| 2026-11-01 | 30 | 20 | 10 | -111.5c | -369.6c | 0.76 |
| 2026-11-02 | 20 | 12 | 8 | -181.9c | -551.5c | 0.73 |
| 2026-11-03 | 17 | 12 | 5 | -1.0c | -552.5c | 0.77 |
| 2026-11-04 | 9 | 7 | 2 | +59.1c | -493.4c | 0.80 |

### GEN4_B41

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.733 and spread >= 0.01; bought at that ask; held to settlement. Discovery PF1 1.52 n 43; validation PF1 1.43 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 69 on 6 days; zero-volume trades 0.
PF at 1 contract 0.76, at 10 contracts 0.78, at 10 contracts with fees x1.2 0.77; net per contract -5.32c at 1, -4.92c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +85.5c | +85.5c | 1.46 |
| 2026-10-31 | 7 | 5 | 2 | -5.0c | +80.5c | 1.25 |
| 2026-11-01 | 15 | 8 | 7 | -304.2c | -223.7c | 0.73 |
| 2026-11-02 | 15 | 10 | 5 | -44.6c | -268.3c | 0.76 |
| 2026-11-03 | 13 | 9 | 4 | -47.9c | -316.2c | 0.77 |
| 2026-11-04 | 6 | 4 | 2 | -23.5c | -339.7c | 0.78 |

### GEN4_B42

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= -0.07 and imb >= -0.9734 and sp15 >= 1.584; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.23 n 41; validation PF1 1.42 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 81 on 6 days; zero-volume trades 0.
PF at 1 contract 1.87, at 10 contracts 1.98, at 10 contracts with fees x1.2 1.95; net per contract +9.91c at 1, +10.73c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 21 | 5 | 16 | +163.0c | +163.0c | 1.77 |
| 2026-10-31 | 7 | 4 | 3 | +185.6c | +348.6c | 2.09 |
| 2026-11-01 | 11 | 5 | 6 | +278.0c | +626.6c | 2.59 |
| 2026-11-02 | 21 | 4 | 17 | -7.9c | +618.7c | 1.88 |
| 2026-11-03 | 10 | 4 | 6 | +174.5c | +793.2c | 2.00 |
| 2026-11-04 | 11 | 2 | 9 | +76.2c | +869.4c | 1.98 |

### GEN4_B43

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.75 n 48; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 108 on 6 days; zero-volume trades 0.
PF at 1 contract 0.78, at 10 contracts 0.82, at 10 contracts with fees x1.2 0.81; net per contract -5.16c at 1, -4.04c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +11.5c | +11.5c | 1.04 |
| 2026-10-31 | 19 | 11 | 8 | -276.5c | -265.0c | 0.70 |
| 2026-11-01 | 30 | 20 | 10 | -119.9c | -384.9c | 0.75 |
| 2026-11-02 | 20 | 12 | 8 | -203.8c | -588.7c | 0.71 |
| 2026-11-03 | 16 | 12 | 4 | +96.0c | -492.7c | 0.79 |
| 2026-11-04 | 8 | 6 | 2 | +56.3c | -436.4c | 0.82 |

### GEN4_B44

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 >= 0.353; bought at that ask; held to settlement. Discovery PF1 2.35 n 51; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 106 on 6 days; zero-volume trades 0.
PF at 1 contract 1.09, at 10 contracts 1.12, at 10 contracts with fees x1.2 1.10; net per contract +1.71c at 1, +2.10c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 14 | 2 | +262.6c | +262.6c | 3.00 |
| 2026-10-31 | 17 | 11 | 6 | -106.5c | +156.1c | 1.28 |
| 2026-11-01 | 27 | 17 | 10 | -221.4c | -65.3c | 0.95 |
| 2026-11-02 | 20 | 14 | 6 | +39.2c | -26.1c | 0.98 |
| 2026-11-03 | 16 | 13 | 3 | +175.9c | +149.8c | 1.09 |
| 2026-11-04 | 10 | 8 | 2 | +72.3c | +222.1c | 1.12 |

### GEN4_B45

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and lsz_bid >= 6.824; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.02 n 47; validation PF1 1.37 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 83 on 6 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.75; net per contract -6.49c at 1, -5.33c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -54.8c | -54.8c | 0.84 |
| 2026-10-31 | 11 | 8 | 3 | +65.8c | +11.0c | 1.02 |
| 2026-11-01 | 21 | 14 | 7 | -111.0c | -100.0c | 0.90 |
| 2026-11-02 | 14 | 7 | 7 | -234.3c | -334.3c | 0.76 |
| 2026-11-03 | 14 | 9 | 5 | -96.9c | -431.2c | 0.75 |
| 2026-11-04 | 6 | 4 | 2 | -11.0c | -442.2c | 0.76 |

### GEN4_B46

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.11 and lsz_ask <= 7.388; bought at that ask; held to settlement. Discovery PF1 2.64 n 45; validation PF1 1.34 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 98 on 6 days; zero-volume trades 0.
PF at 1 contract 0.91, at 10 contracts 0.93, at 10 contracts with fees x1.2 0.91; net per contract -2.01c at 1, -1.56c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 11 | 2 | +192.8c | +192.8c | 2.40 |
| 2026-10-31 | 18 | 11 | 7 | -196.2c | -3.4c | 0.99 |
| 2026-11-01 | 28 | 19 | 9 | -73.1c | -76.5c | 0.94 |
| 2026-11-02 | 18 | 13 | 5 | -3.0c | -79.5c | 0.95 |
| 2026-11-03 | 14 | 9 | 5 | -93.1c | -172.6c | 0.91 |
| 2026-11-04 | 7 | 5 | 2 | +20.0c | -152.6c | 0.93 |

### GEN4_B47

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; held to settlement. Discovery PF1 1.79 n 48; validation PF1 1.33 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 106 on 6 days; zero-volume trades 0.
PF at 1 contract 0.83, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.84; net per contract -3.86c at 1, -3.41c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +13.7c | +13.7c | 1.05 |
| 2026-10-31 | 19 | 11 | 8 | -274.5c | -260.8c | 0.70 |
| 2026-11-01 | 29 | 20 | 9 | -32.6c | -293.4c | 0.80 |
| 2026-11-02 | 20 | 12 | 8 | -200.8c | -494.2c | 0.75 |
| 2026-11-03 | 16 | 12 | 4 | +99.9c | -394.3c | 0.82 |
| 2026-11-04 | 7 | 5 | 2 | +32.9c | -361.4c | 0.85 |

### GEN4_B48

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm15 >= -0.09 and sp30 >= -2.625; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.70 n 41; validation PF1 1.33 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 86 on 6 days; zero-volume trades 0.
PF at 1 contract 0.71, at 10 contracts 0.75, at 10 contracts with fees x1.2 0.74; net per contract -6.95c at 1, -5.86c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 8 | 3 | +12.6c | +12.6c | 1.05 |
| 2026-10-31 | 17 | 9 | 8 | -348.4c | -335.8c | 0.59 |
| 2026-11-01 | 23 | 16 | 7 | -81.2c | -417.0c | 0.68 |
| 2026-11-02 | 17 | 11 | 6 | -186.6c | -603.6c | 0.65 |
| 2026-11-03 | 13 | 10 | 3 | +49.2c | -554.4c | 0.71 |
| 2026-11-04 | 5 | 4 | 1 | +50.8c | -503.6c | 0.75 |

### GEN4_B49

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; held to settlement. Discovery PF1 2.47 n 55; validation PF1 1.33 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 106 on 6 days; zero-volume trades 0.
PF at 1 contract 0.94, at 10 contracts 0.96, at 10 contracts with fees x1.2 0.94; net per contract -1.33c at 1, -0.91c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +177.3c | +177.3c | 1.91 |
| 2026-10-31 | 17 | 9 | 8 | -310.2c | -132.9c | 0.82 |
| 2026-11-01 | 27 | 20 | 7 | +119.8c | -13.1c | 0.99 |
| 2026-11-02 | 20 | 11 | 9 | -218.7c | -231.8c | 0.87 |
| 2026-11-03 | 17 | 13 | 4 | +96.4c | -135.4c | 0.93 |
| 2026-11-04 | 8 | 6 | 2 | +38.5c | -96.9c | 0.96 |

### GEN4_B50

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp15 >= -0.1949 and zd >= -1.214; bought at that ask; held to settlement. Discovery PF1 1.87 n 41; validation PF1 1.31 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 81 on 6 days; zero-volume trades 0.
PF at 1 contract 0.84, at 10 contracts 0.86, at 10 contracts with fees x1.2 0.85; net per contract -3.56c at 1, -3.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +88.5c | +88.5c | 1.45 |
| 2026-10-31 | 10 | 7 | 3 | +21.5c | +110.0c | 1.27 |
| 2026-11-01 | 24 | 17 | 7 | -2.9c | +107.1c | 1.12 |
| 2026-11-02 | 14 | 7 | 7 | -249.5c | -142.4c | 0.89 |
| 2026-11-03 | 14 | 9 | 5 | -75.7c | -218.1c | 0.87 |
| 2026-11-04 | 5 | 3 | 2 | -35.6c | -253.7c | 0.86 |

### GEN4_B51

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0.04 and imb <= 0.4847; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.72 n 50; validation PF1 1.30 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 103 on 6 days; zero-volume trades 0.
PF at 1 contract 0.77, at 10 contracts 0.82, at 10 contracts with fees x1.2 0.81; net per contract -5.13c at 1, -4.03c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +75.9c | +75.9c | 1.33 |
| 2026-10-31 | 18 | 10 | 8 | -301.9c | -226.0c | 0.72 |
| 2026-11-01 | 27 | 18 | 9 | -120.0c | -346.0c | 0.75 |
| 2026-11-02 | 18 | 13 | 5 | +47.3c | -298.7c | 0.83 |
| 2026-11-03 | 16 | 10 | 6 | -133.0c | -431.7c | 0.79 |
| 2026-11-04 | 9 | 7 | 2 | +16.2c | -415.5c | 0.82 |

### GEN4_REF_FAV150

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. The unconditional core of 41 of the 51 GEN4 validation passes: buy the favourite (side ask 0.50 to 0.85) at the first poll 150 to 120 s before the close, hold. Discovery PF1 1.61 n 50; validation PF1 1.57 n 35. Shows whether the conditions add anything forward.
Windows evaluated 324 on 6 days; without the data the rule needs 0; evaluator errors 0. Trades 100 on 6 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.82, at 10 contracts with fees x1.2 0.81; net per contract -4.37c at 1, -3.93c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -34.7c | -34.7c | 0.90 |
| 2026-10-31 | 17 | 9 | 8 | -314.1c | -348.8c | 0.63 |
| 2026-11-01 | 25 | 18 | 7 | +26.8c | -322.0c | 0.77 |
| 2026-11-02 | 17 | 10 | 7 | -137.6c | -459.6c | 0.75 |
| 2026-11-03 | 15 | 11 | 4 | +59.7c | -399.9c | 0.81 |
| 2026-11-04 | 8 | 6 | 2 | +6.6c | -393.3c | 0.82 |

### REF_L1_GOLD

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T00:00:00Z. The live L1 gold rule as a known baseline: the side whose ask is 0.88 to 0.97 at the candle ending 6 minutes before the close, bought at that ask, held to settlement. Candles only, so it ignores the live 25c exit and the window limit.
Windows evaluated 303 on 5 days; without the data the rule needs 0; evaluator errors 0. Trades 71 on 4 days; zero-volume trades 0.
PF at 1 contract 1.11, at 10 contracts 1.20, at 10 contracts with fees x1.2 1.19; net per contract +0.60c at 1, +1.09c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 14 | 1 | +2.5c | +2.5c | 1.03 |
| 2026-11-02 | 23 | 23 | 0 | +153.7c | +156.2c | 2.72 |
| 2026-11-03 | 27 | 24 | 3 | -125.1c | +31.1c | 1.08 |
| 2026-11-04 | 6 | 6 | 0 | +46.0c | +77.1c | 1.20 |

