# FORWARD LEDGER (automatic; research only)

Written by `python -m scalper.fwdledger run` (once per AUTO pass, `scalper.autoscore check`). Last updated 2026-11-02 04:08 UTC.
Forward evidence counts only windows that CLOSED after a candidate's freeze time, had the data its rule needs and have settled.
Fees 7% x C x p x (1-p) rounded up to the cent per order, at 1 and 10 contracts; held to settlement pays the entry fee only. Win = net at 10 contracts above zero. Net per contract is at 10 contracts. Trades per week: forward trades over the time from the freeze to the last evaluated close.
This ledger never promotes anything. READY FOR THE FALSIFIER means only: forward PF 1.5+ at 1 and at 10 contracts on 30+ trades over 10+ trade days. It earns a falsifier read, nothing more. How a generator adds a candidate: `workers/candidates/README.md`.

| id | market | stage | freeze | fwd days | trades | wins | losses | PF 1c | PF 10c | net/contract | trades/week | updated | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| REF_GEN6_OIREL | KXBTC15M | reference | 2026-10-30 | 4 | 10 | 2 | 8 | 1.45 | 1.52 | +5.83c | 28.6 | 2026-11-02 04:08 UTC |  |
| LADFADE_BTC | KXBTC15M | validation | 2026-10-30 | 4 | 17 | 3 | 14 | 0.29 | 0.29 | -24.06c | 46.3 | 2026-11-02 04:08 UTC |  |
| REF_GEN6_OICORE | KXBTC15M | reference | 2026-10-30 | 4 | 15 | 5 | 10 | 2.47 | 2.58 | +15.15c | 35.6 | 2026-11-02 04:08 UTC |  |
| GEN6_B01 | KXBTC15M | validation | 2026-10-30 | 4 | 5 | 3 | 2 | 4.96 | 5.20 | +32.00c | 11.7 | 2026-11-02 04:08 UTC |  |
| GEN6_B02 | KXBTC15M | validation | 2026-10-30 | 4 | 2 | 0 | 2 | 0.00 | 0.00 | -1.90c | 4.7 | 2026-11-02 04:08 UTC |  |
| GEN6_B03 | KXBTC15M | validation | 2026-10-30 | 4 | 15 | 6 | 9 | 2.80 | 3.01 | +14.62c | 35.1 | 2026-11-02 04:08 UTC |  |
| GEN6_B04 | KXBTC15M | validation | 2026-10-30 | 4 | 12 | 4 | 8 | 1.94 | 2.05 | +9.22c | 28.1 | 2026-11-02 04:08 UTC |  |
| GEN6_B05 | KXBTC15M | validation | 2026-10-30 | 4 | 10 | 1 | 9 | 0.03 | 0.03 | -13.97c | 23.4 | 2026-11-02 04:08 UTC |  |
| GEN6_B06 | KXBTC15M | validation | 2026-10-30 | 4 | 7 | 3 | 4 | 3.86 | 4.13 | +21.44c | 16.4 | 2026-11-02 04:08 UTC |  |
| GEN6_B07 | KXBTC15M | validation | 2026-10-30 | 4 | 11 | 2 | 9 | 0.76 | 0.80 | -2.55c | 25.8 | 2026-11-02 04:08 UTC |  |
| GEN6_B08 | KXBTC15M | validation | 2026-10-30 | 4 | 13 | 2 | 11 | 0.67 | 0.70 | -3.92c | 30.4 | 2026-11-02 04:08 UTC |  |
| GEN6_B09 | KXBTC15M | validation | 2026-10-30 | 4 | 11 | 4 | 7 | 0.93 | 1.04 | +0.35c | 25.8 | 2026-11-02 04:08 UTC |  |
| GEN6_B10 | KXBTC15M | validation | 2026-10-30 | 4 | 30 | 6 | 24 | 1.25 | 1.31 | +3.60c | 70.2 | 2026-11-02 04:08 UTC |  |
| GEN6_B11 | KXBTC15M | validation | 2026-10-30 | 4 | 9 | 2 | 7 | 4.12 | 5.06 | +10.97c | 21.1 | 2026-11-02 04:08 UTC |  |
| GEN6_B12 | KXBTC15M | validation | 2026-10-30 | 4 | 6 | 1 | 5 | 0.56 | 0.58 | -6.80c | 14.0 | 2026-11-02 04:08 UTC |  |
| GEN6_B13 | KXBTC15M | validation | 2026-10-30 | 4 | 8 | 4 | 4 | 1.54 | 1.64 | +5.40c | 18.7 | 2026-11-02 04:08 UTC |  |
| REF_BTC_UNDERDOG_180 | KXBTC15M | reference | 2026-10-30 | 4 | 83 | 31 | 52 | 1.20 | 1.23 | +4.31c | 194.3 | 2026-11-02 04:08 UTC |  |
| GEN7_B01 | KXBTC15M | validation | 2026-10-30 | 4 | 6 | 2 | 4 | 3.31 | 3.86 | +11.10c | 13.9 | 2026-11-02 04:08 UTC |  |
| GEN7_B02 | KXBTC15M | validation | 2026-10-30 | 4 | 12 | 4 | 8 | 0.93 | 1.01 | +0.14c | 27.7 | 2026-11-02 04:08 UTC |  |
| REF_GEN6_OIDRIFT | KXBTC15M | reference | 2026-10-30 | 4 | 1 | 0 | 1 | 0.00 | 0.00 | -43.80c | 2.3 | 2026-11-02 04:08 UTC |  |
| REF_GOLD_UNDERDOG_180 | KXGOLD15M | reference | 2026-10-30 | 3 | 32 | 7 | 25 | 0.57 | 0.58 | -9.80c | 73.9 | 2026-11-02 04:08 UTC |  |
| REF_LATECAL_BTC | KXBTC15M | reference | 2026-10-30 | 4 | 19 | 18 | 1 | 0.50 | 0.63 | -1.86c | 43.9 | 2026-11-02 04:08 UTC |  |
| GEN4_B01 | KXBTC15M | validation | 2026-10-30 | 4 | 59 | 39 | 20 | 0.84 | 0.90 | -2.13c | 137.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B02 | KXBTC15M | validation | 2026-10-30 | 4 | 57 | 38 | 19 | 0.86 | 0.92 | -1.56c | 133.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B03 | KXBTC15M | validation | 2026-10-30 | 4 | 52 | 23 | 29 | 0.70 | 0.74 | -6.40c | 121.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B04 | KXBTC15M | validation | 2026-10-30 | 4 | 63 | 45 | 18 | 0.95 | 0.97 | -0.59c | 147.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B05 | KXBTC15M | validation | 2026-10-30 | 4 | 46 | 17 | 29 | 0.84 | 0.89 | -1.78c | 107.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B06 | KXBTC15M | validation | 2026-10-30 | 4 | 58 | 20 | 38 | 0.75 | 0.77 | -3.83c | 135.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B07 | KXBTC15M | validation | 2026-10-30 | 4 | 39 | 13 | 26 | 0.69 | 0.72 | -5.51c | 91.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B08 | KXBTC15M | validation | 2026-10-30 | 4 | 62 | 43 | 19 | 0.85 | 0.90 | -2.14c | 144.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B09 | KXBTC15M | validation | 2026-10-30 | 4 | 61 | 21 | 40 | 0.64 | 0.65 | -7.24c | 142.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B10 | KXBTC15M | validation | 2026-10-30 | 4 | 57 | 37 | 20 | 0.72 | 0.78 | -4.79c | 133.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B11 | KXBTC15M | validation | 2026-10-30 | 4 | 49 | 15 | 34 | 0.68 | 0.70 | -5.16c | 114.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B12 | KXBTC15M | validation | 2026-10-30 | 4 | 58 | 41 | 17 | 0.97 | 1.04 | +0.69c | 135.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B13 | KXBTC15M | validation | 2026-10-30 | 4 | 69 | 45 | 24 | 0.73 | 0.78 | -4.72c | 161.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B14 | KXBTC15M | validation | 2026-10-30 | 4 | 54 | 39 | 15 | 1.08 | 1.15 | +2.70c | 126.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B15 | KXBTC15M | validation | 2026-10-30 | 4 | 52 | 22 | 30 | 0.47 | 0.48 | -14.13c | 121.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B16 | KXBTC15M | validation | 2026-10-30 | 4 | 63 | 43 | 20 | 0.84 | 0.89 | -2.26c | 147.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B17 | KXBTC15M | validation | 2026-10-30 | 4 | 56 | 38 | 18 | 0.74 | 0.76 | -5.53c | 130.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B18 | KXBTC15M | validation | 2026-10-30 | 4 | 58 | 39 | 19 | 0.90 | 0.96 | -0.76c | 135.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B19 | KXBTC15M | validation | 2026-10-30 | 4 | 57 | 39 | 18 | 0.84 | 0.86 | -3.00c | 133.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B20 | KXBTC15M | validation | 2026-10-30 | 4 | 49 | 34 | 15 | 0.96 | 1.02 | +0.44c | 114.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B21 | KXBTC15M | validation | 2026-10-30 | 4 | 26 | 18 | 8 | 0.71 | 0.76 | -5.13c | 60.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B22 | KXBTC15M | validation | 2026-10-30 | 4 | 63 | 41 | 22 | 0.71 | 0.73 | -6.42c | 147.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B23 | KXBTC15M | validation | 2026-10-30 | 4 | 44 | 30 | 14 | 0.84 | 0.86 | -3.10c | 102.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B24 | KXBTC15M | validation | 2026-10-30 | 4 | 43 | 27 | 16 | 0.63 | 0.64 | -8.79c | 100.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B25 | KXBTC15M | validation | 2026-10-30 | 4 | 50 | 33 | 17 | 0.74 | 0.79 | -5.00c | 116.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B26 | KXBTC15M | validation | 2026-10-30 | 4 | 59 | 38 | 21 | 0.62 | 0.66 | -8.24c | 137.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B27 | KXBTC15M | validation | 2026-10-30 | 4 | 44 | 30 | 14 | 0.80 | 0.85 | -3.26c | 102.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B28 | KXBTC15M | validation | 2026-10-30 | 4 | 53 | 37 | 16 | 0.90 | 0.96 | -0.89c | 123.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B29 | KXBTC15M | validation | 2026-10-30 | 4 | 61 | 44 | 17 | 0.98 | 1.05 | +0.98c | 142.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B30 | KXBTC15M | validation | 2026-10-30 | 4 | 47 | 31 | 16 | 0.64 | 0.68 | -7.53c | 109.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B31 | KXBTC15M | validation | 2026-10-30 | 4 | 69 | 48 | 21 | 0.81 | 0.86 | -3.04c | 161.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B32 | KXBTC15M | validation | 2026-10-30 | 4 | 52 | 34 | 18 | 0.83 | 0.88 | -2.42c | 121.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B33 | KXBTC15M | validation | 2026-10-30 | 4 | 44 | 30 | 14 | 0.82 | 0.88 | -2.50c | 102.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B34 | KXBTC15M | validation | 2026-10-30 | 4 | 59 | 38 | 21 | 0.69 | 0.70 | -6.96c | 137.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B35 | KXBTC15M | validation | 2026-10-30 | 4 | 37 | 13 | 24 | 2.35 | 2.44 | +15.14c | 86.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B36 | KXBTC15M | validation | 2026-10-30 | 4 | 52 | 35 | 17 | 0.82 | 0.88 | -2.69c | 121.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B37 | KXBTC15M | validation | 2026-10-30 | 4 | 57 | 20 | 37 | 0.85 | 0.91 | -1.34c | 133.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B38 | KXBTC15M | validation | 2026-10-30 | 4 | 64 | 42 | 22 | 0.72 | 0.73 | -6.40c | 149.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B39 | KXBTC15M | validation | 2026-10-30 | 4 | 62 | 44 | 18 | 0.94 | 1.00 | +0.03c | 144.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B40 | KXBTC15M | validation | 2026-10-30 | 4 | 69 | 46 | 23 | 0.72 | 0.78 | -4.99c | 161.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B41 | KXBTC15M | validation | 2026-10-30 | 4 | 36 | 24 | 12 | 0.74 | 0.76 | -5.53c | 84.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B42 | KXBTC15M | validation | 2026-10-30 | 4 | 39 | 14 | 25 | 2.45 | 2.59 | +16.07c | 91.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B43 | KXBTC15M | validation | 2026-10-30 | 4 | 65 | 43 | 22 | 0.72 | 0.76 | -5.55c | 151.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B44 | KXBTC15M | validation | 2026-10-30 | 4 | 61 | 43 | 18 | 0.95 | 0.97 | -0.54c | 142.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B45 | KXBTC15M | validation | 2026-10-30 | 4 | 49 | 34 | 15 | 0.84 | 0.90 | -2.04c | 114.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B46 | KXBTC15M | validation | 2026-10-30 | 4 | 60 | 42 | 18 | 0.94 | 0.96 | -0.87c | 140.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B47 | KXBTC15M | validation | 2026-10-30 | 4 | 64 | 43 | 21 | 0.80 | 0.81 | -4.20c | 149.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B48 | KXBTC15M | validation | 2026-10-30 | 4 | 52 | 34 | 18 | 0.65 | 0.70 | -7.55c | 121.3 | 2026-11-02 04:08 UTC |  |
| GEN4_B49 | KXBTC15M | validation | 2026-10-30 | 4 | 62 | 44 | 18 | 0.99 | 1.01 | +0.25c | 144.7 | 2026-11-02 04:08 UTC |  |
| GEN4_B50 | KXBTC15M | validation | 2026-10-30 | 4 | 48 | 35 | 13 | 1.10 | 1.12 | +2.23c | 112.0 | 2026-11-02 04:08 UTC |  |
| GEN4_B51 | KXBTC15M | validation | 2026-10-30 | 4 | 61 | 41 | 20 | 0.72 | 0.77 | -5.26c | 142.3 | 2026-11-02 04:08 UTC |  |
| GEN4_REF_FAV150 | KXBTC15M | reference | 2026-10-30 | 4 | 61 | 41 | 20 | 0.77 | 0.79 | -4.86c | 142.3 | 2026-11-02 04:08 UTC |  |
| REF_L1_GOLD | KXGOLD15M | reference | 2026-10-30 | 3 | 19 | 18 | 1 | 1.26 | 1.36 | +1.73c | 43.3 | 2026-11-02 04:08 UTC |  |

## History per candidate

### REF_GEN6_OIREL

Evaluator `scalper.oirel:forward_eval`, source `candles`, frozen 2026-10-30T15:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) when open interest over the 3 minutes before rose by more than 26.76% of its level at 360 s (the discovery quantile matched to the core's 86,300 count), fill at the next candle's ask, held. History: discovery n 298 PF 1.73, validation n 286 PF 1.71 at 10 contracts (FALS5 check 2, one try). Not independent of REF_GEN6_OICORE (59% to 80% shared trades). workers/FALS5_REGISTRATION.md, workers/FALS5_RESULT.md.
Windows evaluated 235 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 3 days; zero-volume trades 0.
PF at 1 contract 1.45, at 10 contracts 1.52, at 10 contracts with fees x1.2 1.50; net per contract +5.29c at 1, +5.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -43.8c | -43.8c | 0.00 |
| 2026-10-31 | 3 | 1 | 2 | +61.6c | +17.8c | 1.29 |
| 2026-11-01 | 6 | 1 | 5 | +40.5c | +58.3c | 1.52 |

### LADFADE_BTC

Evaluator `scalper.ladfade:forward_eval`, source `candles`, frozen 2026-10-30T12:00:00Z. Bitcoin 15 minute windows opening at :15 and :30: when the hourly KXBTCD ladder leans 5c+ from 50/50 at the first minute, buy the side the 15 minute book overshot AWAY from if its ask is 3c+ below the ladder's chance, at the next candle's ask (30c to 70c), held. Ladder from the book recorder. Discovery and validation spent (post hoc); holdout read once in workers/LADFADE_RESULT.md. 1 try; workers/LADFADE_REGISTRATION.md.
Windows evaluated 199 on 4 days; without the data the rule needs 48; evaluator errors 0. Trades 17 on 4 days; zero-volume trades 0.
PF at 1 contract 0.29, at 10 contracts 0.29, at 10 contracts with fees x1.2 0.29; net per contract -24.41c at 1, -24.06c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -44.8c | -44.8c | 0.00 |
| 2026-10-31 | 4 | 0 | 4 | -144.4c | -189.2c | 0.00 |
| 2026-11-01 | 10 | 3 | 7 | -113.7c | -302.9c | 0.36 |
| 2026-11-02 | 2 | 0 | 2 | -106.2c | -409.1c | 0.29 |

### REF_GEN6_OICORE

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T03:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest rose more than 86,300 contracts over the 3 minutes before, held to settlement, fill at the next candle's ask. History: discovery PF 2.28 (n 222), validation 1.85 (n 333, z 4.53). Forward days only; 1 try. Falsifier FALS4 running.
Windows evaluated 283 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 4 days; zero-volume trades 0.
PF at 1 contract 2.47, at 10 contracts 2.58, at 10 contracts with fees x1.2 2.55; net per contract +14.63c at 1, +15.15c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 7 | 3 | 4 | +177.6c | +133.3c | 2.36 |
| 2026-11-01 | 5 | 2 | 3 | +97.4c | +230.7c | 2.64 |
| 2026-11-02 | 1 | 0 | 1 | -3.5c | +227.2c | 2.58 |

### GEN6_B01

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | doi>8.63e+04 & m3>-0.25 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.81 (n 104), validation PF 1.90 (n 164), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 3 days; zero-volume trades 0.
PF at 1 contract 4.96, at 10 contracts 5.20, at 10 contracts with fees x1.2 5.13; net per contract +31.08c at 1, +32.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 3 | 2 | 1 | +77.5c | +77.5c | 3.24 |
| 2026-11-01 | 1 | 1 | 0 | +86.0c | +163.5c | 5.73 |
| 2026-11-02 | 1 | 0 | 1 | -3.5c | +160.0c | 5.20 |

### GEN6_B02

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | hour<=21 & xb_d2<=0.046 & doi>8.63e+04 | TP +8c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 2.42 (n 106), validation PF 1.80 (n 133), C=10.
Windows evaluated 190 on 4 days; without the data the rule needs 97; evaluator errors 0. Trades 2 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -3.15c at 1, -1.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |
| 2026-11-02 | 1 | 0 | 1 | -3.3c | -3.8c | 0.00 |

### GEN6_B03

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 | TP +5c stop -20c else hold]; fill at the next candle's ask. Discovery PF 2.41 (n 222), validation PF 1.73 (n 333), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 4 days; zero-volume trades 0.
PF at 1 contract 2.80, at 10 contracts 3.01, at 10 contracts with fees x1.2 2.96; net per contract +13.88c at 1, +14.62c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 7 | 3 | 4 | +130.6c | +86.3c | 1.88 |
| 2026-11-01 | 5 | 3 | 2 | +136.5c | +222.8c | 3.11 |
| 2026-11-02 | 1 | 0 | 1 | -3.5c | +219.3c | 3.01 |

### GEN6_B04

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 & xa_spr<=0.02 & rng5>0.14 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.06 (n 175), validation PF 1.68 (n 269), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 3 days; zero-volume trades 0.
PF at 1 contract 1.94, at 10 contracts 2.05, at 10 contracts with fees x1.2 2.02; net per contract +8.64c at 1, +9.22c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 5 | 1 | 4 | +18.5c | -25.8c | 0.74 |
| 2026-11-01 | 5 | 3 | 2 | +136.5c | +110.7c | 2.05 |

### GEN6_B05

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | d3<=-0.08 & m1<=0 & vol<=1.11e+05 | TP +20c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 1.60 (n 172), validation PF 1.66 (n 58), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 2 days; zero-volume trades 0.
PF at 1 contract 0.03, at 10 contracts 0.03, at 10 contracts with fees x1.2 0.03; net per contract -15.12c at 1, -13.97c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 5 | 1 | 4 | -30.2c | -30.2c | 0.12 |
| 2026-11-01 | 5 | 0 | 5 | -109.5c | -139.7c | 0.03 |

### GEN6_B06

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | d1<=0.1 & doi>8.63e+04 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 3.51 (n 111), validation PF 1.57 (n 162), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 7 on 4 days; zero-volume trades 0.
PF at 1 contract 3.86, at 10 contracts 4.13, at 10 contracts with fees x1.2 4.07; net per contract +20.60c at 1, +21.44c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |
| 2026-10-31 | 4 | 2 | 2 | +68.1c | +67.6c | 2.52 |
| 2026-11-01 | 1 | 1 | 0 | +86.0c | +153.6c | 4.45 |
| 2026-11-02 | 1 | 0 | 1 | -3.5c | +150.1c | 4.13 |

### GEN6_B07

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 240..180s | m3>-0.08 & m5<=-0.24 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.72 (n 137), validation PF 1.45 (n 90), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 3 days; zero-volume trades 0.
PF at 1 contract 0.76, at 10 contracts 0.80, at 10 contracts with fees x1.2 0.78; net per contract -3.09c at 1, -2.55c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 1 | 1 | +20.1c | +20.1c | 3.64 |
| 2026-10-31 | 4 | 0 | 4 | -89.5c | -69.4c | 0.29 |
| 2026-11-01 | 5 | 1 | 4 | +41.4c | -28.0c | 0.80 |

### GEN6_B08

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | rng5<=0.273 & doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.14 (n 205), validation PF 1.43 (n 316), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 13 on 4 days; zero-volume trades 0.
PF at 1 contract 0.67, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -4.52c at 1, -3.92c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -56.6c | -56.6c | 0.00 |
| 2026-10-31 | 7 | 2 | 5 | +48.3c | -8.3c | 0.94 |
| 2026-11-01 | 2 | 0 | 2 | -39.1c | -47.4c | 0.72 |
| 2026-11-02 | 1 | 0 | 1 | -3.5c | -50.9c | 0.70 |

### GEN6_B09

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | vol<=1.28e+05 & m1<=-0.0507 | TP +3c stop -20c else sell 60s]; fill at the next candle's ask. Discovery PF 1.55 (n 192), validation PF 1.42 (n 86), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 2 days; zero-volume trades 0.
PF at 1 contract 0.93, at 10 contracts 1.04, at 10 contracts with fees x1.2 1.02; net per contract -0.69c at 1, +0.35c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 6 | 2 | 4 | -2.2c | -2.2c | 0.94 |
| 2026-11-01 | 5 | 2 | 3 | +6.1c | +3.9c | 1.04 |

### GEN6_B10

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.19 (n 433), validation PF 1.41 (n 587), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 30 on 4 days; zero-volume trades 0.
PF at 1 contract 1.25, at 10 contracts 1.31, at 10 contracts with fees x1.2 1.30; net per contract +3.04c at 1, +3.60c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 1 | 6 | -6.3c | -6.3c | 0.91 |
| 2026-10-31 | 11 | 3 | 8 | +112.2c | +105.9c | 1.64 |
| 2026-11-01 | 11 | 2 | 9 | +5.6c | +111.5c | 1.33 |
| 2026-11-02 | 1 | 0 | 1 | -3.5c | +108.0c | 1.31 |

### GEN6_B11

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | ask<=0.19 & xa_spr<=0.003 & d1<=-0.05 | TP +5c stop -5c else hold]; fill at the next candle's ask. Discovery PF 1.82 (n 110), validation PF 1.37 (n 93), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 3 days; zero-volume trades 0.
PF at 1 contract 4.12, at 10 contracts 5.06, at 10 contracts with fees x1.2 4.92; net per contract +10.27c at 1, +10.97c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +47.3c | +47.3c | 15.33 |
| 2026-10-31 | 5 | 1 | 4 | +53.2c | +100.5c | 5.47 |
| 2026-11-01 | 1 | 0 | 1 | -1.8c | +98.7c | 5.06 |

### GEN6_B12

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | rng5>0.32 & hour>19 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.83 (n 102), validation PF 1.32 (n 72), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 3 days; zero-volume trades 0.
PF at 1 contract 0.56, at 10 contracts 0.58, at 10 contracts with fees x1.2 0.57; net per contract -7.27c at 1, -6.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +5.4c | +5.4c | 1.11 |
| 2026-10-31 | 2 | 0 | 2 | -32.4c | -27.0c | 0.67 |
| 2026-11-01 | 1 | 0 | 1 | -13.8c | -40.8c | 0.58 |

### GEN6_B13

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | m1>-0.2 & hour>19 | TP +8c stop -20c else hold]; fill at the next candle's ask. Discovery PF 1.70 (n 173), validation PF 1.31 (n 129), C=10.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 3 days; zero-volume trades 0.
PF at 1 contract 1.54, at 10 contracts 1.64, at 10 contracts with fees x1.2 1.60; net per contract +4.71c at 1, +5.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -65.5c | -65.5c | 0.00 |
| 2026-10-31 | 3 | 3 | 0 | +49.0c | -16.5c | 0.75 |
| 2026-11-01 | 2 | 1 | 1 | +59.7c | +43.2c | 1.64 |

### REF_BTC_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T02:00:00Z. The mirror of FALS3's finding (Bitcoin favourites at 50c to 85c are overpriced 2 to 3 minutes before the close: PF 0.77 on 2,576 windows, z -4.97): buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held to settlement. History already read (UNDER1 found this side positive), so only forward days count; REV1 is the registered forward read of the related cheap-NO rule (2026-11-05). 1 try.
Windows evaluated 287 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 83 on 4 days; zero-volume trades 0.
PF at 1 contract 1.20, at 10 contracts 1.23, at 10 contracts with fees x1.2 1.21; net per contract +3.90c at 1, +4.31c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 25 | 6 | 19 | -206.1c | -206.1c | 0.65 |
| 2026-10-31 | 31 | 13 | 18 | +261.8c | +55.7c | 1.05 |
| 2026-11-01 | 24 | 10 | 14 | +194.0c | +249.7c | 1.16 |
| 2026-11-02 | 3 | 2 | 1 | +107.9c | +357.6c | 1.23 |

### GEN7_B01

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 240..240s | npv1>0.281 & vol>1.32e+05 | sell at 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 3.28 (n 101), validation PF 1.80 (n 126), C=10.
Windows evaluated 291 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 3 days; zero-volume trades 0.
PF at 1 contract 3.31, at 10 contracts 3.86, at 10 contracts with fees x1.2 3.77; net per contract +10.23c at 1, +11.10c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -12.8c | -12.8c | 0.00 |
| 2026-10-31 | 1 | 0 | 1 | -5.8c | -18.6c | 0.00 |
| 2026-11-01 | 4 | 2 | 2 | +85.2c | +66.6c | 3.86 |

### GEN7_B02

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 300..240s | npv1>0.393 & doi5>9.78e+04 | TP +20c stop -20c else sell 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 1.75 (n 135), validation PF 1.71 (n 101), C=10.
Windows evaluated 291 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 3 days; zero-volume trades 0.
PF at 1 contract 0.93, at 10 contracts 1.01, at 10 contracts with fees x1.2 0.99; net per contract -0.95c at 1, +0.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 4 | 1 | 3 | -54.8c | -54.8c | 0.19 |
| 2026-11-01 | 7 | 3 | 4 | +86.4c | +31.6c | 1.25 |
| 2026-11-02 | 1 | 0 | 1 | -29.9c | +1.7c | 1.01 |

### REF_GEN6_OIDRIFT

Evaluator `scalper.oidrift:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest over the 3 minutes before rose above the 90th percentile of that change over the 30 UTC days before (earlier days only, 20+ days needed), fill at the next candle's ask, held. History validation n 67, PF 2.65 (FALS4 check 5, reproduced). Not independent of REF_GEN6_OICORE. 1 try; workers/OIDRIFT_REGISTRATION.md.
Windows evaluated 291 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -44.00c at 1, -43.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -43.8c | -43.8c | 0.00 |

### REF_GOLD_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. Gold version of REF_BTC_UNDERDOG_180: FALS3 found gold favourites at 50c to 85c, 2 to 3 minutes before the close, also below break-even (PF 0.85). Buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held. Forward days only. 1 try.
Windows evaluated 90 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 32 on 2 days; zero-volume trades 0.
PF at 1 contract 0.57, at 10 contracts 0.58, at 10 contracts with fees x1.2 0.57; net per contract -10.25c at 1, -9.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 31 | 7 | 24 | -282.0c | -282.0c | 0.61 |
| 2026-11-02 | 1 | 0 | 1 | -31.5c | -313.5c | 0.58 |

### REF_LATECAL_BTC

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. LATECAL's one chosen cell (Bitcoin, 90 to 60 s left, ask 0.95 to 0.98: 61 of 61 won on the recorder, NOT_ENOUGH_DATA; needs about 800 windows to clear the 97.7% break-even) tracked forward. Candles only: the nearest candle is the one ending 60 s before the close, so this approximates the recorder's 90 to 60 s cell. L1-family, held to settlement.
Windows evaluated 291 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 19 on 4 days; zero-volume trades 0.
PF at 1 contract 0.50, at 10 contracts 0.63, at 10 contracts with fees x1.2 0.63; net per contract -2.55c at 1, -1.86c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 6 | 5 | 1 | -79.5c | -79.5c | 0.17 |
| 2026-10-31 | 5 | 5 | 0 | +17.4c | -62.1c | 0.35 |
| 2026-11-01 | 7 | 7 | 0 | +24.9c | -37.2c | 0.61 |
| 2026-11-02 | 1 | 1 | 0 | +1.8c | -35.4c | 0.63 |

### GEN4_B01

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and zd >= -1.585; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.13 n 46; validation PF1 2.64 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 59 on 4 days; zero-volume trades 0.
PF at 1 contract 0.84, at 10 contracts 0.90, at 10 contracts with fees x1.2 0.88; net per contract -3.28c at 1, -2.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +73.8c | +73.8c | 1.34 |
| 2026-10-31 | 17 | 10 | 7 | -165.8c | -92.0c | 0.86 |
| 2026-11-01 | 28 | 18 | 10 | -57.7c | -149.7c | 0.88 |
| 2026-11-02 | 1 | 1 | 0 | +24.2c | -125.5c | 0.90 |

### GEN4_B02

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and zd >= -2.066; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.09 n 51; validation PF1 2.40 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 57 on 4 days; zero-volume trades 0.
PF at 1 contract 0.86, at 10 contracts 0.92, at 10 contracts with fees x1.2 0.90; net per contract -2.69c at 1, -1.56c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -89.3c | -89.3c | 0.74 |
| 2026-10-31 | 14 | 9 | 5 | -10.8c | -100.1c | 0.84 |
| 2026-11-01 | 27 | 18 | 9 | -12.8c | -112.9c | 0.90 |
| 2026-11-02 | 1 | 1 | 0 | +24.2c | -88.7c | 0.92 |

### GEN4_B03

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and sp15 >= -0.1949 and zd >= -0.3503; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.62 n 40; validation PF1 2.39 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 52 on 3 days; zero-volume trades 0.
PF at 1 contract 0.70, at 10 contracts 0.74, at 10 contracts with fees x1.2 0.73; net per contract -7.30c at 1, -6.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 4 | 6 | -110.1c | -110.1c | 0.58 |
| 2026-10-31 | 17 | 8 | 9 | -42.3c | -152.4c | 0.78 |
| 2026-11-01 | 25 | 11 | 14 | -180.6c | -333.0c | 0.74 |

### GEN4_B04

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.17 and lsz_ask <= 8.072 and lsz_bid <= 8.053; bought at that ask; held to settlement. Discovery PF1 2.04 n 41; validation PF1 2.27 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 63 on 4 days; zero-volume trades 0.
PF at 1 contract 0.95, at 10 contracts 0.97, at 10 contracts with fees x1.2 0.96; net per contract -1.10c at 1, -0.59c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 12 | 2 | +160.7c | +160.7c | 2.08 |
| 2026-10-31 | 19 | 11 | 8 | -274.5c | -113.8c | 0.85 |
| 2026-11-01 | 29 | 21 | 8 | +57.7c | -56.1c | 0.96 |
| 2026-11-02 | 1 | 1 | 0 | +18.8c | -37.3c | 0.97 |

### GEN4_B05

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 41; validation PF1 2.18 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 46 on 4 days; zero-volume trades 0.
PF at 1 contract 0.84, at 10 contracts 0.89, at 10 contracts with fees x1.2 0.88; net per contract -2.60c at 1, -1.78c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -91.0c | -91.0c | 0.62 |
| 2026-10-31 | 16 | 8 | 8 | +64.4c | -26.6c | 0.94 |
| 2026-11-01 | 16 | 6 | 10 | -27.0c | -53.6c | 0.93 |
| 2026-11-02 | 1 | 0 | 1 | -28.4c | -82.0c | 0.89 |

### GEN4_B06

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.54 n 52; validation PF1 2.08 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 58 on 4 days; zero-volume trades 0.
PF at 1 contract 0.75, at 10 contracts 0.77, at 10 contracts with fees x1.2 0.76; net per contract -4.30c at 1, -3.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | -148.3c | -148.3c | 0.49 |
| 2026-10-31 | 17 | 8 | 9 | +78.9c | -69.4c | 0.88 |
| 2026-11-01 | 20 | 7 | 13 | -123.4c | -192.8c | 0.80 |
| 2026-11-02 | 1 | 0 | 1 | -29.5c | -222.3c | 0.77 |

### GEN4_B07

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= 0.3412 and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.68 n 43; validation PF1 2.08 n 24 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 39 on 3 days; zero-volume trades 0.
PF at 1 contract 0.69, at 10 contracts 0.72, at 10 contracts with fees x1.2 0.71; net per contract -6.31c at 1, -5.51c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 16 | 7 | 9 | +25.3c | +25.3c | 1.08 |
| 2026-11-01 | 22 | 6 | 16 | -210.7c | -185.4c | 0.75 |
| 2026-11-02 | 1 | 0 | 1 | -29.5c | -214.9c | 0.72 |

### GEN4_B08

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.24 n 52; validation PF1 1.99 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 62 on 4 days; zero-volume trades 0.
PF at 1 contract 0.85, at 10 contracts 0.90, at 10 contracts with fees x1.2 0.88; net per contract -3.24c at 1, -2.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -65.0c | -65.0c | 0.81 |
| 2026-10-31 | 17 | 12 | 5 | -0.6c | -65.6c | 0.90 |
| 2026-11-01 | 28 | 19 | 9 | -91.5c | -157.1c | 0.88 |
| 2026-11-02 | 1 | 1 | 0 | +24.4c | -132.7c | 0.90 |

### GEN4_B09

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= -0.06831; bought at that ask; held to settlement. Discovery PF1 1.51 n 49; validation PF1 1.94 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 61 on 4 days; zero-volume trades 0.
PF at 1 contract 0.64, at 10 contracts 0.65, at 10 contracts with fees x1.2 0.64; net per contract -7.67c at 1, -7.24c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -122.4c | -122.4c | 0.55 |
| 2026-10-31 | 21 | 9 | 12 | -122.9c | -245.3c | 0.68 |
| 2026-11-01 | 26 | 9 | 17 | -168.2c | -413.5c | 0.67 |
| 2026-11-02 | 1 | 0 | 1 | -28.4c | -441.9c | 0.65 |

### GEN4_B10

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 <= 2.256 and sp5 <= 0.353; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.79 n 46; validation PF1 1.93 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 57 on 4 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.78, at 10 contracts with fees x1.2 0.76; net per contract -5.99c at 1, -4.79c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 10 | 4 | -57.6c | -57.6c | 0.80 |
| 2026-10-31 | 17 | 9 | 8 | -254.0c | -311.6c | 0.61 |
| 2026-11-01 | 25 | 17 | 8 | +13.5c | -298.1c | 0.76 |
| 2026-11-02 | 1 | 1 | 0 | +25.2c | -272.9c | 0.78 |

### GEN4_B11

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp30 >= 0.5295; bought at that ask; held to settlement. Discovery PF1 1.50 n 46; validation PF1 1.91 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 49 on 4 days; zero-volume trades 0.
PF at 1 contract 0.68, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -5.65c at 1, -5.16c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 4 | 13 | -83.1c | -83.1c | 0.60 |
| 2026-10-31 | 14 | 5 | 9 | -30.3c | -113.4c | 0.76 |
| 2026-11-01 | 17 | 6 | 11 | -110.0c | -223.4c | 0.72 |
| 2026-11-02 | 1 | 0 | 1 | -29.5c | -252.9c | 0.70 |

### GEN4_B12

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.16 and lsz_ask <= 7.779 and sp5 >= 0.1732; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.32 n 43; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 58 on 4 days; zero-volume trades 0.
PF at 1 contract 0.97, at 10 contracts 1.04, at 10 contracts with fees x1.2 1.02; net per contract -0.51c at 1, +0.69c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 11 | 1 | +258.6c | +258.6c | 4.18 |
| 2026-10-31 | 19 | 13 | 6 | -25.6c | +233.0c | 1.48 |
| 2026-11-01 | 26 | 16 | 10 | -217.1c | +15.9c | 1.01 |
| 2026-11-02 | 1 | 1 | 0 | +24.3c | +40.2c | 1.04 |

### GEN4_B13

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.65 n 56; validation PF1 1.90 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 69 on 4 days; zero-volume trades 0.
PF at 1 contract 0.73, at 10 contracts 0.78, at 10 contracts with fees x1.2 0.77; net per contract -5.92c at 1, -4.72c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.8c | -12.8c | 0.96 |
| 2026-10-31 | 19 | 11 | 8 | -215.6c | -228.4c | 0.73 |
| 2026-11-01 | 30 | 19 | 11 | -122.7c | -351.1c | 0.76 |
| 2026-11-02 | 1 | 1 | 0 | +25.2c | -325.9c | 0.78 |

### GEN4_B14

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and lsz_ask <= 7.779; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.30 n 44; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 54 on 4 days; zero-volume trades 0.
PF at 1 contract 1.08, at 10 contracts 1.15, at 10 contracts with fees x1.2 1.14; net per contract +1.43c at 1, +2.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 10 | 2 | +136.8c | +136.8c | 1.99 |
| 2026-10-31 | 16 | 11 | 5 | +25.4c | +162.2c | 1.37 |
| 2026-11-01 | 25 | 17 | 8 | -40.7c | +121.5c | 1.13 |
| 2026-11-02 | 1 | 1 | 0 | +24.3c | +145.8c | 1.15 |

### GEN4_B15

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26 and sp15 >= -0.01237 and spread >= 0.001; bought at that ask; held to settlement. Discovery PF1 1.55 n 42; validation PF1 1.86 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 52 on 4 days; zero-volume trades 0.
PF at 1 contract 0.47, at 10 contracts 0.48, at 10 contracts with fees x1.2 0.47; net per contract -14.56c at 1, -14.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 4 | 7 | -206.0c | -206.0c | 0.31 |
| 2026-10-31 | 17 | 8 | 9 | -194.7c | -400.7c | 0.49 |
| 2026-11-01 | 23 | 10 | 13 | -304.5c | -705.2c | 0.49 |
| 2026-11-02 | 1 | 0 | 1 | -29.5c | -734.7c | 0.48 |

### GEN4_B16

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and spread <= 0.01; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.14 n 48; validation PF1 1.83 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 63 on 4 days; zero-volume trades 0.
PF at 1 contract 0.84, at 10 contracts 0.89, at 10 contracts with fees x1.2 0.88; net per contract -3.53c at 1, -2.26c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +100.3c | +100.3c | 1.46 |
| 2026-10-31 | 19 | 12 | 7 | -135.8c | -35.5c | 0.95 |
| 2026-11-01 | 29 | 19 | 10 | -131.2c | -166.7c | 0.88 |
| 2026-11-02 | 1 | 1 | 0 | +24.3c | -142.4c | 0.89 |

### GEN4_B17

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.4847 and zd >= -2.066; bought at that ask; held to settlement. Discovery PF1 1.52 n 48; validation PF1 1.82 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 56 on 4 days; zero-volume trades 0.
PF at 1 contract 0.74, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.75; net per contract -6.00c at 1, -5.53c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 13 | 4 | +24.0c | +24.0c | 1.08 |
| 2026-10-31 | 14 | 6 | 8 | -419.1c | -395.1c | 0.55 |
| 2026-11-01 | 24 | 18 | 6 | +60.0c | -335.1c | 0.74 |
| 2026-11-02 | 1 | 1 | 0 | +25.6c | -309.5c | 0.76 |

### GEN4_B18

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and lsz_ask <= 7.779 and zd >= -0.6765; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.63 n 43; validation PF1 1.81 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 58 on 4 days; zero-volume trades 0.
PF at 1 contract 0.90, at 10 contracts 0.96, at 10 contracts with fees x1.2 0.95; net per contract -1.91c at 1, -0.76c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 9 | 3 | +57.1c | +57.1c | 1.28 |
| 2026-10-31 | 17 | 10 | 7 | -145.2c | -88.1c | 0.86 |
| 2026-11-01 | 28 | 19 | 9 | +19.9c | -68.2c | 0.94 |
| 2026-11-02 | 1 | 1 | 0 | +24.2c | -44.0c | 0.96 |

### GEN4_B19

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and imb >= -0.6701; bought at that ask; held to settlement. Discovery PF1 1.78 n 48; validation PF1 1.81 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 57 on 3 days; zero-volume trades 0.
PF at 1 contract 0.84, at 10 contracts 0.86, at 10 contracts with fees x1.2 0.85; net per contract -3.44c at 1, -3.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -52.6c | -52.6c | 0.85 |
| 2026-10-31 | 16 | 10 | 6 | -136.8c | -189.4c | 0.76 |
| 2026-11-01 | 24 | 17 | 7 | +18.5c | -170.9c | 0.86 |

### GEN4_B20

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and imb >= -0.4281 and sp5 <= 0; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.66 n 43; validation PF1 1.77 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 49 on 3 days; zero-volume trades 0.
PF at 1 contract 0.96, at 10 contracts 1.02, at 10 contracts with fees x1.2 1.01; net per contract -0.70c at 1, +0.44c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -55.9c | -55.9c | 0.80 |
| 2026-10-31 | 13 | 9 | 4 | +24.2c | -31.7c | 0.94 |
| 2026-11-01 | 23 | 16 | 7 | +53.3c | +21.6c | 1.02 |

### GEN4_B21

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.902 and lsz_bid >= 7.292; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.54 n 44; validation PF1 1.76 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 26 on 3 days; zero-volume trades 0.
PF at 1 contract 0.71, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.75; net per contract -6.23c at 1, -5.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 9 | 5 | -132.3c | -132.3c | 0.62 |
| 2026-10-31 | 1 | 0 | 1 | -70.5c | -202.8c | 0.51 |
| 2026-11-01 | 11 | 9 | 2 | +69.5c | -133.3c | 0.76 |

### GEN4_B22

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.456 and lsz_bid >= 6.195; bought at that ask; held to settlement. Discovery PF1 1.63 n 49; validation PF1 1.73 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 63 on 4 days; zero-volume trades 0.
PF at 1 contract 0.71, at 10 contracts 0.73, at 10 contracts with fees x1.2 0.72; net per contract -6.89c at 1, -6.42c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -44.0c | -44.0c | 0.87 |
| 2026-10-31 | 18 | 12 | 6 | -67.7c | -111.7c | 0.86 |
| 2026-11-01 | 27 | 16 | 11 | -317.3c | -429.0c | 0.71 |
| 2026-11-02 | 1 | 1 | 0 | +24.6c | -404.4c | 0.73 |

### GEN4_B23

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; held to settlement. Discovery PF1 1.55 n 40; validation PF1 1.71 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 44 on 4 days; zero-volume trades 0.
PF at 1 contract 0.84, at 10 contracts 0.86, at 10 contracts with fees x1.2 0.85; net per contract -3.59c at 1, -3.10c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.6c | +24.6c | inf |
| 2026-10-31 | 16 | 8 | 8 | -326.0c | -301.4c | 0.47 |
| 2026-11-01 | 26 | 20 | 6 | +139.6c | -161.8c | 0.83 |
| 2026-11-02 | 1 | 1 | 0 | +25.6c | -136.2c | 0.86 |

### GEN4_B24

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.292; bought at that ask; held to settlement. Discovery PF1 2.01 n 50; validation PF1 1.65 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 43 on 4 days; zero-volume trades 0.
PF at 1 contract 0.63, at 10 contracts 0.64, at 10 contracts with fees x1.2 0.63; net per contract -9.23c at 1, -8.79c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -54.9c | -54.9c | 0.84 |
| 2026-10-31 | 7 | 5 | 2 | +28.0c | -26.9c | 0.94 |
| 2026-11-01 | 19 | 10 | 9 | -375.6c | -402.5c | 0.62 |
| 2026-11-02 | 1 | 1 | 0 | +24.6c | -377.9c | 0.64 |

### GEN4_B25

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.00 n 40; validation PF1 1.64 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 50 on 4 days; zero-volume trades 0.
PF at 1 contract 0.74, at 10 contracts 0.79, at 10 contracts with fees x1.2 0.78; net per contract -6.09c at 1, -5.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 6 | 4 | -85.4c | -85.4c | 0.71 |
| 2026-10-31 | 17 | 10 | 7 | -216.7c | -302.1c | 0.61 |
| 2026-11-01 | 22 | 16 | 6 | +27.5c | -274.6c | 0.77 |
| 2026-11-02 | 1 | 1 | 0 | +24.4c | -250.2c | 0.79 |

### GEN4_B26

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and lsz_bid >= 5.465; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.57 n 49; validation PF1 1.63 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 59 on 4 days; zero-volume trades 0.
PF at 1 contract 0.62, at 10 contracts 0.66, at 10 contracts with fees x1.2 0.65; net per contract -9.36c at 1, -8.24c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -37.3c | -37.3c | 0.89 |
| 2026-10-31 | 16 | 8 | 8 | -347.5c | -384.8c | 0.59 |
| 2026-11-01 | 24 | 16 | 8 | -129.8c | -514.6c | 0.64 |
| 2026-11-02 | 1 | 1 | 0 | +28.3c | -486.3c | 0.66 |

### GEN4_B27

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.52 n 40; validation PF1 1.63 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 44 on 4 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.84; net per contract -4.43c at 1, -3.26c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 16 | 8 | 8 | -327.4c | -303.0c | 0.47 |
| 2026-11-01 | 26 | 20 | 6 | +134.2c | -168.8c | 0.83 |
| 2026-11-02 | 1 | 1 | 0 | +25.4c | -143.4c | 0.85 |

### GEN4_B28

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and lsz_ask <= 7.388; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.92 n 40; validation PF1 1.61 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 53 on 4 days; zero-volume trades 0.
PF at 1 contract 0.90, at 10 contracts 0.96, at 10 contracts with fees x1.2 0.94; net per contract -2.02c at 1, -0.89c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 7 | 2 | +57.7c | +57.7c | 1.46 |
| 2026-10-31 | 18 | 11 | 7 | -180.5c | -122.8c | 0.80 |
| 2026-11-01 | 25 | 18 | 7 | +51.3c | -71.5c | 0.93 |
| 2026-11-02 | 1 | 1 | 0 | +24.4c | -47.1c | 0.96 |

### GEN4_B29

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.1233; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.26 n 51; validation PF1 1.61 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 61 on 4 days; zero-volume trades 0.
PF at 1 contract 0.98, at 10 contracts 1.05, at 10 contracts with fees x1.2 1.04; net per contract -0.30c at 1, +0.98c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +106.3c | +106.3c | 1.48 |
| 2026-10-31 | 17 | 12 | 5 | +29.0c | +135.3c | 1.26 |
| 2026-11-01 | 28 | 19 | 9 | -99.6c | +35.7c | 1.03 |
| 2026-11-02 | 1 | 1 | 0 | +24.3c | +60.0c | 1.05 |

### GEN4_B30

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask >= 7.388 and sp15 >= -0.9017 and sp30 <= 2.256; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 45; validation PF1 1.61 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 47 on 4 days; zero-volume trades 0.
PF at 1 contract 0.64, at 10 contracts 0.68, at 10 contracts with fees x1.2 0.67; net per contract -8.59c at 1, -7.53c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -46.3c | -46.3c | 0.83 |
| 2026-10-31 | 12 | 6 | 6 | -275.9c | -322.2c | 0.55 |
| 2026-11-01 | 21 | 15 | 6 | -56.9c | -379.1c | 0.66 |
| 2026-11-02 | 1 | 1 | 0 | +25.4c | -353.7c | 0.68 |

### GEN4_B31

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid <= 8.422; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.71 n 55; validation PF1 1.59 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 69 on 4 days; zero-volume trades 0.
PF at 1 contract 0.81, at 10 contracts 0.86, at 10 contracts with fees x1.2 0.85; net per contract -4.20c at 1, -3.04c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 15 | 4 | +69.2c | +69.2c | 1.24 |
| 2026-10-31 | 19 | 11 | 8 | -277.5c | -208.3c | 0.76 |
| 2026-11-01 | 30 | 21 | 9 | -26.9c | -235.2c | 0.84 |
| 2026-11-02 | 1 | 1 | 0 | +25.4c | -209.8c | 0.86 |

### GEN4_B32

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.95 n 40; validation PF1 1.57 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 52 on 4 days; zero-volume trades 0.
PF at 1 contract 0.83, at 10 contracts 0.88, at 10 contracts with fees x1.2 0.87; net per contract -3.56c at 1, -2.42c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +24.3c | +24.3c | 1.11 |
| 2026-10-31 | 19 | 12 | 7 | -100.0c | -75.7c | 0.88 |
| 2026-11-01 | 22 | 14 | 8 | -78.2c | -153.9c | 0.86 |
| 2026-11-02 | 1 | 1 | 0 | +28.1c | -125.8c | 0.88 |

### GEN4_B33

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and spread >= 0.001 and vol <= 0.311; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.59 n 40; validation PF1 1.54 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 44 on 4 days; zero-volume trades 0.
PF at 1 contract 0.82, at 10 contracts 0.88, at 10 contracts with fees x1.2 0.87; net per contract -3.82c at 1, -2.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 16 | 8 | 8 | -288.5c | -264.1c | 0.50 |
| 2026-11-01 | 26 | 20 | 6 | +129.0c | -135.1c | 0.86 |
| 2026-11-02 | 1 | 1 | 0 | +25.3c | -109.8c | 0.88 |

### GEN4_B34

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 6.824 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.83 n 52; validation PF1 1.54 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 59 on 4 days; zero-volume trades 0.
PF at 1 contract 0.69, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -7.37c at 1, -6.96c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -28.0c | -28.0c | 0.92 |
| 2026-10-31 | 13 | 8 | 5 | -71.3c | -99.3c | 0.85 |
| 2026-11-01 | 27 | 16 | 11 | -335.8c | -435.1c | 0.69 |
| 2026-11-02 | 1 | 1 | 0 | +24.6c | -410.5c | 0.70 |

### GEN4_B35

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and sp15 >= 1.584 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 2.38 n 41; validation PF1 1.52 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 37 on 3 days; zero-volume trades 0.
PF at 1 contract 2.35, at 10 contracts 2.44, at 10 contracts with fees x1.2 2.41; net per contract +14.68c at 1, +15.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | +180.7c | +180.7c | 1.87 |
| 2026-10-31 | 7 | 3 | 4 | +92.6c | +273.3c | 1.85 |
| 2026-11-01 | 10 | 5 | 5 | +286.9c | +560.2c | 2.44 |

### GEN4_B36

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.83 n 40; validation PF1 1.52 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 52 on 4 days; zero-volume trades 0.
PF at 1 contract 0.82, at 10 contracts 0.88, at 10 contracts with fees x1.2 0.86; net per contract -3.93c at 1, -2.69c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +25.7c | +25.7c | 1.12 |
| 2026-10-31 | 19 | 12 | 7 | -121.6c | -95.9c | 0.85 |
| 2026-11-01 | 22 | 15 | 7 | -72.0c | -167.9c | 0.85 |
| 2026-11-02 | 1 | 1 | 0 | +28.2c | -139.7c | 0.88 |

### GEN4_B37

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm30 <= 0.17 and sp5 >= 0.353 and spread >= 0.001; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.52 n 43; validation PF1 1.49 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 57 on 4 days; zero-volume trades 0.
PF at 1 contract 0.85, at 10 contracts 0.91, at 10 contracts with fees x1.2 0.89; net per contract -2.30c at 1, -1.34c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 3 | 11 | -119.8c | -119.8c | 0.54 |
| 2026-10-31 | 17 | 7 | 10 | +90.6c | -29.2c | 0.94 |
| 2026-11-01 | 25 | 10 | 15 | -25.0c | -54.2c | 0.93 |
| 2026-11-02 | 1 | 0 | 1 | -22.1c | -76.3c | 0.91 |

### GEN4_B38

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 <= 0.0315; bought at that ask; held to settlement. Discovery PF1 1.50 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 64 on 4 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.73, at 10 contracts with fees x1.2 0.72; net per contract -6.88c at 1, -6.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -112.6c | -112.6c | 0.69 |
| 2026-10-31 | 19 | 11 | 8 | -285.1c | -397.7c | 0.59 |
| 2026-11-01 | 29 | 20 | 9 | -37.5c | -435.2c | 0.72 |
| 2026-11-02 | 1 | 1 | 0 | +25.6c | -409.6c | 0.73 |

### GEN4_B39

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.01237; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.44 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 62 on 4 days; zero-volume trades 0.
PF at 1 contract 0.94, at 10 contracts 1.00, at 10 contracts with fees x1.2 0.99; net per contract -1.11c at 1, +0.03c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +168.7c | +168.7c | 1.84 |
| 2026-10-31 | 17 | 9 | 8 | -306.9c | -138.2c | 0.82 |
| 2026-11-01 | 27 | 20 | 7 | +115.7c | -22.5c | 0.98 |
| 2026-11-02 | 1 | 1 | 0 | +24.4c | +1.9c | 1.00 |

### GEN4_B40

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.9734; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.57 n 55; validation PF1 1.44 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 69 on 4 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.78, at 10 contracts with fees x1.2 0.77; net per contract -6.28c at 1, -4.99c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.7c | -12.7c | 0.96 |
| 2026-10-31 | 19 | 11 | 8 | -245.4c | -258.1c | 0.71 |
| 2026-11-01 | 30 | 20 | 10 | -111.5c | -369.6c | 0.76 |
| 2026-11-02 | 1 | 1 | 0 | +25.3c | -344.3c | 0.78 |

### GEN4_B41

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.733 and spread >= 0.01; bought at that ask; held to settlement. Discovery PF1 1.52 n 43; validation PF1 1.43 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 36 on 4 days; zero-volume trades 0.
PF at 1 contract 0.74, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.74; net per contract -5.94c at 1, -5.53c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +85.5c | +85.5c | 1.46 |
| 2026-10-31 | 7 | 5 | 2 | -5.0c | +80.5c | 1.25 |
| 2026-11-01 | 15 | 8 | 7 | -304.2c | -223.7c | 0.73 |
| 2026-11-02 | 1 | 1 | 0 | +24.6c | -199.1c | 0.76 |

### GEN4_B42

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= -0.07 and imb >= -0.9734 and sp15 >= 1.584; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.23 n 41; validation PF1 1.42 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 39 on 3 days; zero-volume trades 0.
PF at 1 contract 2.45, at 10 contracts 2.59, at 10 contracts with fees x1.2 2.56; net per contract +15.22c at 1, +16.07c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 21 | 5 | 16 | +163.0c | +163.0c | 1.77 |
| 2026-10-31 | 7 | 4 | 3 | +185.6c | +348.6c | 2.09 |
| 2026-11-01 | 11 | 5 | 6 | +278.0c | +626.6c | 2.59 |

### GEN4_B43

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.75 n 48; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 65 on 4 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.75; net per contract -6.66c at 1, -5.55c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +11.5c | +11.5c | 1.04 |
| 2026-10-31 | 19 | 11 | 8 | -276.5c | -265.0c | 0.70 |
| 2026-11-01 | 30 | 20 | 10 | -119.9c | -384.9c | 0.75 |
| 2026-11-02 | 1 | 1 | 0 | +24.4c | -360.5c | 0.76 |

### GEN4_B44

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 >= 0.353; bought at that ask; held to settlement. Discovery PF1 2.35 n 51; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 61 on 4 days; zero-volume trades 0.
PF at 1 contract 0.95, at 10 contracts 0.97, at 10 contracts with fees x1.2 0.96; net per contract -0.95c at 1, -0.54c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 14 | 2 | +262.6c | +262.6c | 3.00 |
| 2026-10-31 | 17 | 11 | 6 | -106.5c | +156.1c | 1.28 |
| 2026-11-01 | 27 | 17 | 10 | -221.4c | -65.3c | 0.95 |
| 2026-11-02 | 1 | 1 | 0 | +32.4c | -32.9c | 0.97 |

### GEN4_B45

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and lsz_bid >= 6.824; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.02 n 47; validation PF1 1.37 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 49 on 3 days; zero-volume trades 0.
PF at 1 contract 0.84, at 10 contracts 0.90, at 10 contracts with fees x1.2 0.88; net per contract -3.25c at 1, -2.04c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -54.8c | -54.8c | 0.84 |
| 2026-10-31 | 11 | 8 | 3 | +65.8c | +11.0c | 1.02 |
| 2026-11-01 | 21 | 14 | 7 | -111.0c | -100.0c | 0.90 |

### GEN4_B46

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.11 and lsz_ask <= 7.388; bought at that ask; held to settlement. Discovery PF1 2.64 n 45; validation PF1 1.34 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 60 on 4 days; zero-volume trades 0.
PF at 1 contract 0.94, at 10 contracts 0.96, at 10 contracts with fees x1.2 0.95; net per contract -1.35c at 1, -0.87c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 11 | 2 | +192.8c | +192.8c | 2.40 |
| 2026-10-31 | 18 | 11 | 7 | -196.2c | -3.4c | 0.99 |
| 2026-11-01 | 28 | 19 | 9 | -73.1c | -76.5c | 0.94 |
| 2026-11-02 | 1 | 1 | 0 | +24.6c | -51.9c | 0.96 |

### GEN4_B47

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; held to settlement. Discovery PF1 1.79 n 48; validation PF1 1.33 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 64 on 4 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.81, at 10 contracts with fees x1.2 0.80; net per contract -4.67c at 1, -4.20c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +13.7c | +13.7c | 1.05 |
| 2026-10-31 | 19 | 11 | 8 | -274.5c | -260.8c | 0.70 |
| 2026-11-01 | 29 | 20 | 9 | -32.6c | -293.4c | 0.80 |
| 2026-11-02 | 1 | 1 | 0 | +24.6c | -268.8c | 0.81 |

### GEN4_B48

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm15 >= -0.09 and sp30 >= -2.625; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.70 n 41; validation PF1 1.33 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 52 on 4 days; zero-volume trades 0.
PF at 1 contract 0.65, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -8.65c at 1, -7.55c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 8 | 3 | +12.6c | +12.6c | 1.05 |
| 2026-10-31 | 17 | 9 | 8 | -348.4c | -335.8c | 0.59 |
| 2026-11-01 | 23 | 16 | 7 | -81.2c | -417.0c | 0.68 |
| 2026-11-02 | 1 | 1 | 0 | +24.4c | -392.6c | 0.70 |

### GEN4_B49

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; held to settlement. Discovery PF1 2.47 n 55; validation PF1 1.33 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 62 on 4 days; zero-volume trades 0.
PF at 1 contract 0.99, at 10 contracts 1.01, at 10 contracts with fees x1.2 1.00; net per contract -0.21c at 1, +0.25c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +177.3c | +177.3c | 1.91 |
| 2026-10-31 | 17 | 9 | 8 | -310.2c | -132.9c | 0.82 |
| 2026-11-01 | 27 | 20 | 7 | +119.8c | -13.1c | 0.99 |
| 2026-11-02 | 1 | 1 | 0 | +28.5c | +15.4c | 1.01 |

### GEN4_B50

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp15 >= -0.1949 and zd >= -1.214; bought at that ask; held to settlement. Discovery PF1 1.87 n 41; validation PF1 1.31 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 48 on 3 days; zero-volume trades 0.
PF at 1 contract 1.10, at 10 contracts 1.12, at 10 contracts with fees x1.2 1.11; net per contract +1.79c at 1, +2.23c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +88.5c | +88.5c | 1.45 |
| 2026-10-31 | 10 | 7 | 3 | +21.5c | +110.0c | 1.27 |
| 2026-11-01 | 24 | 17 | 7 | -2.9c | +107.1c | 1.12 |

### GEN4_B51

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0.04 and imb <= 0.4847; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.72 n 50; validation PF1 1.30 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 61 on 4 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.77, at 10 contracts with fees x1.2 0.76; net per contract -6.36c at 1, -5.26c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +75.9c | +75.9c | 1.33 |
| 2026-10-31 | 18 | 10 | 8 | -301.9c | -226.0c | 0.72 |
| 2026-11-01 | 27 | 18 | 9 | -120.0c | -346.0c | 0.75 |
| 2026-11-02 | 1 | 1 | 0 | +25.4c | -320.6c | 0.77 |

### GEN4_REF_FAV150

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. The unconditional core of 41 of the 51 GEN4 validation passes: buy the favourite (side ask 0.50 to 0.85) at the first poll 150 to 120 s before the close, hold. Discovery PF1 1.61 n 50; validation PF1 1.57 n 35. Shows whether the conditions add anything forward.
Windows evaluated 190 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 61 on 4 days; zero-volume trades 0.
PF at 1 contract 0.77, at 10 contracts 0.79, at 10 contracts with fees x1.2 0.78; net per contract -5.33c at 1, -4.86c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -34.7c | -34.7c | 0.90 |
| 2026-10-31 | 17 | 9 | 8 | -314.1c | -348.8c | 0.63 |
| 2026-11-01 | 25 | 18 | 7 | +26.8c | -322.0c | 0.77 |
| 2026-11-02 | 1 | 1 | 0 | +25.6c | -296.4c | 0.79 |

### REF_L1_GOLD

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T00:00:00Z. The live L1 gold rule as a known baseline: the side whose ask is 0.88 to 0.97 at the candle ending 6 minutes before the close, bought at that ask, held to settlement. Candles only, so it ignores the live 25c exit and the window limit.
Windows evaluated 94 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 19 on 2 days; zero-volume trades 0.
PF at 1 contract 1.26, at 10 contracts 1.36, at 10 contracts with fees x1.2 1.34; net per contract +1.27c at 1, +1.73c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 14 | 1 | +2.5c | +2.5c | 1.03 |
| 2026-11-02 | 4 | 4 | 0 | +30.4c | +32.9c | 1.36 |

