# FORWARD LEDGER (automatic; research only)

Written by `python -m scalper.fwdledger run` (once per AUTO pass, `scalper.autoscore check`). Last updated 2026-11-01 21:16 UTC.
Forward evidence counts only windows that CLOSED after a candidate's freeze time, had the data its rule needs and have settled.
Fees 7% x C x p x (1-p) rounded up to the cent per order, at 1 and 10 contracts; held to settlement pays the entry fee only. Win = net at 10 contracts above zero. Net per contract is at 10 contracts. Trades per week: forward trades over the time from the freeze to the last evaluated close.
This ledger never promotes anything. READY FOR THE FALSIFIER means only: forward PF 1.5+ at 1 and at 10 contracts on 30+ trades over 10+ trade days. It earns a falsifier read, nothing more. How a generator adds a candidate: `workers/candidates/README.md`.

| id | market | stage | freeze | fwd days | trades | wins | losses | PF 1c | PF 10c | net/contract | trades/week | updated | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| REF_GEN6_OIREL | KXBTC15M | reference | 2026-10-30 | 3 | 10 | 2 | 8 | 1.45 | 1.52 | +5.83c | 32.3 | 2026-11-01 21:16 UTC |  |
| LADFADE_BTC | KXBTC15M | validation | 2026-10-30 | 3 | 13 | 3 | 10 | 0.41 | 0.42 | -18.14c | 39.7 | 2026-11-01 21:16 UTC |  |
| REF_GEN6_OICORE | KXBTC15M | reference | 2026-10-30 | 3 | 14 | 5 | 9 | 2.54 | 2.64 | +16.48c | 36.8 | 2026-11-01 21:16 UTC |  |
| GEN6_B01 | KXBTC15M | validation | 2026-10-30 | 3 | 4 | 3 | 1 | 5.56 | 5.73 | +40.87c | 10.3 | 2026-11-01 21:16 UTC |  |
| GEN6_B02 | KXBTC15M | validation | 2026-10-30 | 3 | 1 | 0 | 1 | 0.00 | 0.00 | -0.50c | 2.6 | 2026-11-01 21:16 UTC |  |
| GEN6_B03 | KXBTC15M | validation | 2026-10-30 | 3 | 14 | 6 | 8 | 2.91 | 3.11 | +15.91c | 36.2 | 2026-11-01 21:16 UTC |  |
| GEN6_B04 | KXBTC15M | validation | 2026-10-30 | 3 | 12 | 4 | 8 | 1.94 | 2.05 | +9.22c | 31.0 | 2026-11-01 21:16 UTC |  |
| GEN6_B05 | KXBTC15M | validation | 2026-10-30 | 3 | 10 | 1 | 9 | 0.03 | 0.03 | -13.97c | 25.8 | 2026-11-01 21:16 UTC |  |
| GEN6_B06 | KXBTC15M | validation | 2026-10-30 | 3 | 6 | 3 | 3 | 4.21 | 4.45 | +25.60c | 15.5 | 2026-11-01 21:16 UTC |  |
| GEN6_B07 | KXBTC15M | validation | 2026-10-30 | 3 | 11 | 2 | 9 | 0.76 | 0.80 | -2.55c | 28.4 | 2026-11-01 21:16 UTC |  |
| GEN6_B08 | KXBTC15M | validation | 2026-10-30 | 3 | 11 | 2 | 9 | 0.71 | 0.74 | -3.81c | 28.4 | 2026-11-01 21:16 UTC |  |
| GEN6_B09 | KXBTC15M | validation | 2026-10-30 | 3 | 10 | 3 | 7 | 0.33 | 0.38 | -5.80c | 25.8 | 2026-11-01 21:16 UTC |  |
| GEN6_B10 | KXBTC15M | validation | 2026-10-30 | 3 | 28 | 6 | 22 | 1.29 | 1.35 | +4.18c | 72.4 | 2026-11-01 21:16 UTC |  |
| GEN6_B11 | KXBTC15M | validation | 2026-10-30 | 3 | 9 | 2 | 7 | 4.12 | 5.06 | +10.97c | 23.3 | 2026-11-01 21:16 UTC |  |
| GEN6_B12 | KXBTC15M | validation | 2026-10-30 | 3 | 5 | 1 | 4 | 0.65 | 0.67 | -5.40c | 12.9 | 2026-11-01 21:16 UTC |  |
| GEN6_B13 | KXBTC15M | validation | 2026-10-30 | 3 | 6 | 3 | 3 | 0.70 | 0.75 | -2.75c | 15.5 | 2026-11-01 21:16 UTC |  |
| REF_BTC_UNDERDOG_180 | KXBTC15M | reference | 2026-10-30 | 3 | 77 | 27 | 50 | 1.07 | 1.09 | +1.78c | 199.0 | 2026-11-01 21:16 UTC |  |
| GEN7_B01 | KXBTC15M | validation | 2026-10-30 | 3 | 6 | 2 | 4 | 3.31 | 3.86 | +11.10c | 15.3 | 2026-11-01 21:16 UTC |  |
| GEN7_B02 | KXBTC15M | validation | 2026-10-30 | 3 | 9 | 4 | 5 | 1.39 | 1.49 | +5.81c | 22.9 | 2026-11-01 21:16 UTC |  |
| REF_GEN6_OIDRIFT | KXBTC15M | reference | 2026-10-30 | 3 | 1 | 0 | 1 | 0.00 | 0.00 | -43.80c | 2.5 | 2026-11-01 21:16 UTC |  |
| REF_GOLD_UNDERDOG_180 | KXGOLD15M | reference | 2026-10-30 | 1 | 31 | 7 | 24 | 0.60 | 0.61 | -9.10c | 217.0 | 2026-11-01 21:16 UTC |  |
| REF_LATECAL_BTC | KXBTC15M | reference | 2026-10-30 | 3 | 15 | 14 | 1 | 0.42 | 0.52 | -3.05c | 38.2 | 2026-11-01 21:16 UTC |  |
| GEN4_B01 | KXBTC15M | validation | 2026-10-30 | 3 | 55 | 37 | 18 | 0.89 | 0.95 | -1.01c | 135.9 | 2026-11-01 21:16 UTC |  |
| GEN4_B02 | KXBTC15M | validation | 2026-10-30 | 3 | 53 | 36 | 17 | 0.92 | 0.98 | -0.35c | 130.9 | 2026-11-01 21:16 UTC |  |
| GEN4_B03 | KXBTC15M | validation | 2026-10-30 | 3 | 49 | 21 | 28 | 0.64 | 0.68 | -8.00c | 121.1 | 2026-11-01 21:16 UTC |  |
| GEN4_B04 | KXBTC15M | validation | 2026-10-30 | 3 | 59 | 43 | 16 | 1.02 | 1.04 | +0.84c | 145.8 | 2026-11-01 21:16 UTC |  |
| GEN4_B05 | KXBTC15M | validation | 2026-10-30 | 3 | 42 | 16 | 26 | 0.81 | 0.85 | -2.47c | 103.8 | 2026-11-01 21:16 UTC |  |
| GEN4_B06 | KXBTC15M | validation | 2026-10-30 | 3 | 54 | 19 | 35 | 0.70 | 0.72 | -4.75c | 133.4 | 2026-11-01 21:16 UTC |  |
| GEN4_B07 | KXBTC15M | validation | 2026-10-30 | 3 | 34 | 12 | 22 | 0.72 | 0.76 | -4.84c | 84.0 | 2026-11-01 21:16 UTC |  |
| GEN4_B08 | KXBTC15M | validation | 2026-10-30 | 3 | 57 | 41 | 16 | 0.97 | 1.03 | +0.54c | 140.8 | 2026-11-01 21:16 UTC |  |
| GEN4_B09 | KXBTC15M | validation | 2026-10-30 | 3 | 55 | 19 | 36 | 0.60 | 0.62 | -8.05c | 135.9 | 2026-11-01 21:16 UTC |  |
| GEN4_B10 | KXBTC15M | validation | 2026-10-30 | 3 | 54 | 36 | 18 | 0.80 | 0.85 | -2.94c | 133.4 | 2026-11-01 21:16 UTC |  |
| GEN4_B11 | KXBTC15M | validation | 2026-10-30 | 3 | 45 | 14 | 31 | 0.62 | 0.64 | -6.40c | 111.2 | 2026-11-01 21:16 UTC |  |
| GEN4_B12 | KXBTC15M | validation | 2026-10-30 | 3 | 54 | 39 | 15 | 1.05 | 1.11 | +2.07c | 133.4 | 2026-11-01 21:16 UTC |  |
| GEN4_B13 | KXBTC15M | validation | 2026-10-30 | 3 | 64 | 43 | 21 | 0.80 | 0.86 | -2.72c | 158.1 | 2026-11-01 21:16 UTC |  |
| GEN4_B14 | KXBTC15M | validation | 2026-10-30 | 3 | 50 | 37 | 13 | 1.20 | 1.28 | +4.53c | 123.5 | 2026-11-01 21:16 UTC |  |
| GEN4_B15 | KXBTC15M | validation | 2026-10-30 | 3 | 48 | 20 | 28 | 0.43 | 0.44 | -15.27c | 118.6 | 2026-11-01 21:16 UTC |  |
| GEN4_B16 | KXBTC15M | validation | 2026-10-30 | 3 | 58 | 41 | 17 | 0.95 | 1.02 | +0.36c | 143.3 | 2026-11-01 21:16 UTC |  |
| GEN4_B17 | KXBTC15M | validation | 2026-10-30 | 3 | 53 | 37 | 16 | 0.81 | 0.83 | -3.66c | 130.9 | 2026-11-01 21:16 UTC |  |
| GEN4_B18 | KXBTC15M | validation | 2026-10-30 | 3 | 54 | 37 | 17 | 0.96 | 1.02 | +0.32c | 133.4 | 2026-11-01 21:16 UTC |  |
| GEN4_B19 | KXBTC15M | validation | 2026-10-30 | 3 | 55 | 39 | 16 | 0.96 | 0.98 | -0.40c | 135.9 | 2026-11-01 21:16 UTC |  |
| GEN4_B20 | KXBTC15M | validation | 2026-10-30 | 3 | 48 | 34 | 14 | 1.04 | 1.11 | +1.89c | 118.6 | 2026-11-01 21:16 UTC |  |
| GEN4_B21 | KXBTC15M | validation | 2026-10-30 | 3 | 26 | 18 | 8 | 0.71 | 0.76 | -5.13c | 64.2 | 2026-11-01 21:16 UTC |  |
| GEN4_B22 | KXBTC15M | validation | 2026-10-30 | 3 | 59 | 40 | 19 | 0.81 | 0.83 | -3.70c | 145.8 | 2026-11-01 21:16 UTC |  |
| GEN4_B23 | KXBTC15M | validation | 2026-10-30 | 3 | 40 | 28 | 12 | 0.91 | 0.93 | -1.43c | 98.8 | 2026-11-01 21:16 UTC |  |
| GEN4_B24 | KXBTC15M | validation | 2026-10-30 | 3 | 40 | 26 | 14 | 0.70 | 0.72 | -6.54c | 98.8 | 2026-11-01 21:16 UTC |  |
| GEN4_B25 | KXBTC15M | validation | 2026-10-30 | 3 | 46 | 31 | 15 | 0.78 | 0.83 | -3.90c | 113.6 | 2026-11-01 21:16 UTC |  |
| GEN4_B26 | KXBTC15M | validation | 2026-10-30 | 3 | 56 | 37 | 19 | 0.67 | 0.72 | -6.53c | 138.4 | 2026-11-01 21:16 UTC |  |
| GEN4_B27 | KXBTC15M | validation | 2026-10-30 | 3 | 40 | 28 | 12 | 0.87 | 0.92 | -1.60c | 98.8 | 2026-11-01 21:16 UTC |  |
| GEN4_B28 | KXBTC15M | validation | 2026-10-30 | 3 | 49 | 35 | 14 | 0.97 | 1.03 | +0.50c | 121.1 | 2026-11-01 21:16 UTC |  |
| GEN4_B29 | KXBTC15M | validation | 2026-10-30 | 3 | 56 | 42 | 14 | 1.17 | 1.25 | +3.98c | 138.4 | 2026-11-01 21:16 UTC |  |
| GEN4_B30 | KXBTC15M | validation | 2026-10-30 | 3 | 44 | 29 | 15 | 0.65 | 0.70 | -7.15c | 108.7 | 2026-11-01 21:16 UTC |  |
| GEN4_B31 | KXBTC15M | validation | 2026-10-30 | 3 | 64 | 46 | 18 | 0.90 | 0.96 | -0.72c | 158.1 | 2026-11-01 21:16 UTC |  |
| GEN4_B32 | KXBTC15M | validation | 2026-10-30 | 3 | 48 | 32 | 16 | 0.87 | 0.93 | -1.44c | 118.6 | 2026-11-01 21:16 UTC |  |
| GEN4_B33 | KXBTC15M | validation | 2026-10-30 | 3 | 40 | 28 | 12 | 0.90 | 0.96 | -0.76c | 98.8 | 2026-11-01 21:16 UTC |  |
| GEN4_B34 | KXBTC15M | validation | 2026-10-30 | 3 | 55 | 37 | 18 | 0.79 | 0.81 | -4.08c | 135.9 | 2026-11-01 21:16 UTC |  |
| GEN4_B35 | KXBTC15M | validation | 2026-10-30 | 3 | 36 | 12 | 24 | 2.21 | 2.30 | +14.03c | 88.9 | 2026-11-01 21:16 UTC |  |
| GEN4_B36 | KXBTC15M | validation | 2026-10-30 | 3 | 48 | 33 | 15 | 0.87 | 0.93 | -1.52c | 118.6 | 2026-11-01 21:16 UTC |  |
| GEN4_B37 | KXBTC15M | validation | 2026-10-30 | 3 | 51 | 18 | 33 | 0.79 | 0.84 | -2.36c | 126.0 | 2026-11-01 21:16 UTC |  |
| GEN4_B38 | KXBTC15M | validation | 2026-10-30 | 3 | 60 | 40 | 20 | 0.74 | 0.76 | -5.49c | 148.2 | 2026-11-01 21:16 UTC |  |
| GEN4_B39 | KXBTC15M | validation | 2026-10-30 | 3 | 58 | 42 | 16 | 1.01 | 1.08 | +1.44c | 143.3 | 2026-11-01 21:16 UTC |  |
| GEN4_B40 | KXBTC15M | validation | 2026-10-30 | 3 | 64 | 44 | 20 | 0.80 | 0.86 | -2.83c | 158.1 | 2026-11-01 21:16 UTC |  |
| GEN4_B41 | KXBTC15M | validation | 2026-10-30 | 3 | 34 | 23 | 11 | 0.79 | 0.81 | -4.14c | 84.0 | 2026-11-01 21:16 UTC |  |
| GEN4_B42 | KXBTC15M | validation | 2026-10-30 | 3 | 37 | 13 | 24 | 2.36 | 2.49 | +15.61c | 91.4 | 2026-11-01 21:16 UTC |  |
| GEN4_B43 | KXBTC15M | validation | 2026-10-30 | 3 | 60 | 41 | 19 | 0.80 | 0.85 | -3.27c | 148.2 | 2026-11-01 21:16 UTC |  |
| GEN4_B44 | KXBTC15M | validation | 2026-10-30 | 3 | 57 | 41 | 16 | 1.01 | 1.03 | +0.54c | 140.8 | 2026-11-01 21:16 UTC |  |
| GEN4_B45 | KXBTC15M | validation | 2026-10-30 | 3 | 47 | 34 | 13 | 0.96 | 1.03 | +0.58c | 116.1 | 2026-11-01 21:16 UTC |  |
| GEN4_B46 | KXBTC15M | validation | 2026-10-30 | 3 | 55 | 40 | 15 | 1.08 | 1.11 | +2.02c | 135.9 | 2026-11-01 21:16 UTC |  |
| GEN4_B47 | KXBTC15M | validation | 2026-10-30 | 3 | 60 | 41 | 19 | 0.83 | 0.86 | -3.13c | 148.2 | 2026-11-01 21:16 UTC |  |
| GEN4_B48 | KXBTC15M | validation | 2026-10-30 | 3 | 49 | 33 | 16 | 0.71 | 0.76 | -5.67c | 121.1 | 2026-11-01 21:16 UTC |  |
| GEN4_B49 | KXBTC15M | validation | 2026-10-30 | 3 | 58 | 42 | 16 | 1.06 | 1.09 | +1.59c | 143.3 | 2026-11-01 21:16 UTC |  |
| GEN4_B50 | KXBTC15M | validation | 2026-10-30 | 3 | 46 | 35 | 11 | 1.33 | 1.36 | +5.57c | 113.6 | 2026-11-01 21:16 UTC |  |
| GEN4_B51 | KXBTC15M | validation | 2026-10-30 | 3 | 58 | 40 | 18 | 0.78 | 0.83 | -3.55c | 143.3 | 2026-11-01 21:16 UTC |  |
| GEN4_REF_FAV150 | KXBTC15M | reference | 2026-10-30 | 3 | 58 | 40 | 18 | 0.84 | 0.86 | -2.97c | 143.3 | 2026-11-01 21:16 UTC |  |
| REF_L1_GOLD | KXGOLD15M | reference | 2026-10-30 | 1 | 15 | 14 | 1 | 0.95 | 1.03 | +0.17c | 105.0 | 2026-11-01 21:16 UTC |  |

## History per candidate

### REF_GEN6_OIREL

Evaluator `scalper.oirel:forward_eval`, source `candles`, frozen 2026-10-30T15:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) when open interest over the 3 minutes before rose by more than 26.76% of its level at 360 s (the discovery quantile matched to the core's 86,300 count), fill at the next candle's ask, held. History: discovery n 298 PF 1.73, validation n 286 PF 1.71 at 10 contracts (FALS5 check 2, one try). Not independent of REF_GEN6_OICORE (59% to 80% shared trades). workers/FALS5_REGISTRATION.md, workers/FALS5_RESULT.md.
Windows evaluated 208 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 3 days; zero-volume trades 0.
PF at 1 contract 1.45, at 10 contracts 1.52, at 10 contracts with fees x1.2 1.50; net per contract +5.29c at 1, +5.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -43.8c | -43.8c | 0.00 |
| 2026-10-31 | 3 | 1 | 2 | +61.6c | +17.8c | 1.29 |
| 2026-11-01 | 6 | 1 | 5 | +40.5c | +58.3c | 1.52 |

### LADFADE_BTC

Evaluator `scalper.ladfade:forward_eval`, source `candles`, frozen 2026-10-30T12:00:00Z. Bitcoin 15 minute windows opening at :15 and :30: when the hourly KXBTCD ladder leans 5c+ from 50/50 at the first minute, buy the side the 15 minute book overshot AWAY from if its ask is 3c+ below the ladder's chance, at the next candle's ask (30c to 70c), held. Ladder from the book recorder. Discovery and validation spent (post hoc); holdout read once in workers/LADFADE_RESULT.md. 1 try; workers/LADFADE_REGISTRATION.md.
Windows evaluated 174 on 3 days; without the data the rule needs 46; evaluator errors 0. Trades 13 on 3 days; zero-volume trades 0.
PF at 1 contract 0.41, at 10 contracts 0.42, at 10 contracts with fees x1.2 0.41; net per contract -18.46c at 1, -18.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -44.8c | -44.8c | 0.00 |
| 2026-10-31 | 4 | 0 | 4 | -144.4c | -189.2c | 0.00 |
| 2026-11-01 | 8 | 3 | 5 | -46.6c | -235.8c | 0.42 |

### REF_GEN6_OICORE

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T03:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest rose more than 86,300 contracts over the 3 minutes before, held to settlement, fill at the next candle's ask. History: discovery PF 2.28 (n 222), validation 1.85 (n 333, z 4.53). Forward days only; 1 try. Falsifier FALS4 running.
Windows evaluated 256 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 3 days; zero-volume trades 0.
PF at 1 contract 2.54, at 10 contracts 2.64, at 10 contracts with fees x1.2 2.62; net per contract +15.97c at 1, +16.48c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 7 | 3 | 4 | +177.6c | +133.3c | 2.36 |
| 2026-11-01 | 5 | 2 | 3 | +97.4c | +230.7c | 2.64 |

### GEN6_B01

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | doi>8.63e+04 & m3>-0.25 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.81 (n 104), validation PF 1.90 (n 164), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 2 days; zero-volume trades 0.
PF at 1 contract 5.56, at 10 contracts 5.73, at 10 contracts with fees x1.2 5.64; net per contract +39.90c at 1, +40.87c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 3 | 2 | 1 | +77.5c | +77.5c | 3.24 |
| 2026-11-01 | 1 | 1 | 0 | +86.0c | +163.5c | 5.73 |

### GEN6_B02

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | hour<=21 & xb_d2<=0.046 & doi>8.63e+04 | TP +8c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 2.42 (n 106), validation PF 1.80 (n 133), C=10.
Windows evaluated 169 on 3 days; without the data the rule needs 91; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -1.40c at 1, -0.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |

### GEN6_B03

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 | TP +5c stop -20c else hold]; fill at the next candle's ask. Discovery PF 2.41 (n 222), validation PF 1.73 (n 333), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 3 days; zero-volume trades 0.
PF at 1 contract 2.91, at 10 contracts 3.11, at 10 contracts with fees x1.2 3.06; net per contract +15.17c at 1, +15.91c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 7 | 3 | 4 | +130.6c | +86.3c | 1.88 |
| 2026-11-01 | 5 | 3 | 2 | +136.5c | +222.8c | 3.11 |

### GEN6_B04

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 & xa_spr<=0.02 & rng5>0.14 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.06 (n 175), validation PF 1.68 (n 269), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 3 days; zero-volume trades 0.
PF at 1 contract 1.94, at 10 contracts 2.05, at 10 contracts with fees x1.2 2.02; net per contract +8.64c at 1, +9.22c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 5 | 1 | 4 | +18.5c | -25.8c | 0.74 |
| 2026-11-01 | 5 | 3 | 2 | +136.5c | +110.7c | 2.05 |

### GEN6_B05

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | d3<=-0.08 & m1<=0 & vol<=1.11e+05 | TP +20c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 1.60 (n 172), validation PF 1.66 (n 58), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 2 days; zero-volume trades 0.
PF at 1 contract 0.03, at 10 contracts 0.03, at 10 contracts with fees x1.2 0.03; net per contract -15.12c at 1, -13.97c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 5 | 1 | 4 | -30.2c | -30.2c | 0.12 |
| 2026-11-01 | 5 | 0 | 5 | -109.5c | -139.7c | 0.03 |

### GEN6_B06

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | d1<=0.1 & doi>8.63e+04 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 3.51 (n 111), validation PF 1.57 (n 162), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 3 days; zero-volume trades 0.
PF at 1 contract 4.21, at 10 contracts 4.45, at 10 contracts with fees x1.2 4.39; net per contract +24.73c at 1, +25.60c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |
| 2026-10-31 | 4 | 2 | 2 | +68.1c | +67.6c | 2.52 |
| 2026-11-01 | 1 | 1 | 0 | +86.0c | +153.6c | 4.45 |

### GEN6_B07

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 240..180s | m3>-0.08 & m5<=-0.24 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.72 (n 137), validation PF 1.45 (n 90), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 3 days; zero-volume trades 0.
PF at 1 contract 0.76, at 10 contracts 0.80, at 10 contracts with fees x1.2 0.78; net per contract -3.09c at 1, -2.55c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 1 | 1 | +20.1c | +20.1c | 3.64 |
| 2026-10-31 | 4 | 0 | 4 | -89.5c | -69.4c | 0.29 |
| 2026-11-01 | 5 | 1 | 4 | +41.4c | -28.0c | 0.80 |

### GEN6_B08

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | rng5<=0.273 & doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.14 (n 205), validation PF 1.43 (n 316), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 3 days; zero-volume trades 0.
PF at 1 contract 0.71, at 10 contracts 0.74, at 10 contracts with fees x1.2 0.73; net per contract -4.40c at 1, -3.81c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -56.6c | -56.6c | 0.00 |
| 2026-10-31 | 7 | 2 | 5 | +48.3c | -8.3c | 0.94 |
| 2026-11-01 | 1 | 0 | 1 | -33.6c | -41.9c | 0.74 |

### GEN6_B09

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | vol<=1.28e+05 & m1<=-0.0507 | TP +3c stop -20c else sell 60s]; fill at the next candle's ask. Discovery PF 1.55 (n 192), validation PF 1.42 (n 86), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 2 days; zero-volume trades 0.
PF at 1 contract 0.33, at 10 contracts 0.38, at 10 contracts with fees x1.2 0.37; net per contract -6.85c at 1, -5.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 6 | 2 | 4 | -2.2c | -2.2c | 0.94 |
| 2026-11-01 | 4 | 1 | 3 | -55.8c | -58.0c | 0.38 |

### GEN6_B10

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.19 (n 433), validation PF 1.41 (n 587), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 28 on 3 days; zero-volume trades 0.
PF at 1 contract 1.29, at 10 contracts 1.35, at 10 contracts with fees x1.2 1.33; net per contract +3.62c at 1, +4.18c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 1 | 6 | -6.3c | -6.3c | 0.91 |
| 2026-10-31 | 11 | 3 | 8 | +112.2c | +105.9c | 1.64 |
| 2026-11-01 | 10 | 2 | 8 | +11.1c | +117.0c | 1.35 |

### GEN6_B11

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | ask<=0.19 & xa_spr<=0.003 & d1<=-0.05 | TP +5c stop -5c else hold]; fill at the next candle's ask. Discovery PF 1.82 (n 110), validation PF 1.37 (n 93), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 3 days; zero-volume trades 0.
PF at 1 contract 4.12, at 10 contracts 5.06, at 10 contracts with fees x1.2 4.92; net per contract +10.27c at 1, +10.97c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +47.3c | +47.3c | 15.33 |
| 2026-10-31 | 5 | 1 | 4 | +53.2c | +100.5c | 5.47 |
| 2026-11-01 | 1 | 0 | 1 | -1.8c | +98.7c | 5.06 |

### GEN6_B12

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | rng5>0.32 & hour>19 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.83 (n 102), validation PF 1.32 (n 72), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 2 days; zero-volume trades 0.
PF at 1 contract 0.65, at 10 contracts 0.67, at 10 contracts with fees x1.2 0.66; net per contract -5.92c at 1, -5.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +5.4c | +5.4c | 1.11 |
| 2026-10-31 | 2 | 0 | 2 | -32.4c | -27.0c | 0.67 |

### GEN6_B13

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | m1>-0.2 & hour>19 | TP +8c stop -20c else hold]; fill at the next candle's ask. Discovery PF 1.70 (n 173), validation PF 1.31 (n 129), C=10.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 2 days; zero-volume trades 0.
PF at 1 contract 0.70, at 10 contracts 0.75, at 10 contracts with fees x1.2 0.72; net per contract -3.37c at 1, -2.75c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -65.5c | -65.5c | 0.00 |
| 2026-10-31 | 3 | 3 | 0 | +49.0c | -16.5c | 0.75 |

### REF_BTC_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T02:00:00Z. The mirror of FALS3's finding (Bitcoin favourites at 50c to 85c are overpriced 2 to 3 minutes before the close: PF 0.77 on 2,576 windows, z -4.97): buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held to settlement. History already read (UNDER1 found this side positive), so only forward days count; REV1 is the registered forward read of the related cheap-NO rule (2026-11-05). 1 try.
Windows evaluated 260 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 77 on 3 days; zero-volume trades 0.
PF at 1 contract 1.07, at 10 contracts 1.09, at 10 contracts with fees x1.2 1.07; net per contract +1.38c at 1, +1.78c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 25 | 6 | 19 | -206.1c | -206.1c | 0.65 |
| 2026-10-31 | 31 | 13 | 18 | +261.8c | +55.7c | 1.05 |
| 2026-11-01 | 21 | 8 | 13 | +81.0c | +136.7c | 1.09 |

### GEN7_B01

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 240..240s | npv1>0.281 & vol>1.32e+05 | sell at 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 3.28 (n 101), validation PF 1.80 (n 126), C=10.
Windows evaluated 264 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 3 days; zero-volume trades 0.
PF at 1 contract 3.31, at 10 contracts 3.86, at 10 contracts with fees x1.2 3.77; net per contract +10.23c at 1, +11.10c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -12.8c | -12.8c | 0.00 |
| 2026-10-31 | 1 | 0 | 1 | -5.8c | -18.6c | 0.00 |
| 2026-11-01 | 4 | 2 | 2 | +85.2c | +66.6c | 3.86 |

### GEN7_B02

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 300..240s | npv1>0.393 & doi5>9.78e+04 | TP +20c stop -20c else sell 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 1.75 (n 135), validation PF 1.71 (n 101), C=10.
Windows evaluated 264 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 2 days; zero-volume trades 0.
PF at 1 contract 1.39, at 10 contracts 1.49, at 10 contracts with fees x1.2 1.46; net per contract +4.86c at 1, +5.81c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 4 | 1 | 3 | -54.8c | -54.8c | 0.19 |
| 2026-11-01 | 5 | 3 | 2 | +107.1c | +52.3c | 1.49 |

### REF_GEN6_OIDRIFT

Evaluator `scalper.oidrift:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest over the 3 minutes before rose above the 90th percentile of that change over the 30 UTC days before (earlier days only, 20+ days needed), fill at the next candle's ask, held. History validation n 67, PF 2.65 (FALS4 check 5, reproduced). Not independent of REF_GEN6_OICORE. 1 try; workers/OIDRIFT_REGISTRATION.md.
Windows evaluated 264 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -44.00c at 1, -43.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -43.8c | -43.8c | 0.00 |

### REF_GOLD_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. Gold version of REF_BTC_UNDERDOG_180: FALS3 found gold favourites at 50c to 85c, 2 to 3 minutes before the close, also below break-even (PF 0.85). Buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held. Forward days only. 1 try.
Windows evaluated 80 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 31 on 1 days; zero-volume trades 0.
PF at 1 contract 0.60, at 10 contracts 0.61, at 10 contracts with fees x1.2 0.60; net per contract -9.55c at 1, -9.10c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 31 | 7 | 24 | -282.0c | -282.0c | 0.61 |

### REF_LATECAL_BTC

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. LATECAL's one chosen cell (Bitcoin, 90 to 60 s left, ask 0.95 to 0.98: 61 of 61 won on the recorder, NOT_ENOUGH_DATA; needs about 800 windows to clear the 97.7% break-even) tracked forward. Candles only: the nearest candle is the one ending 60 s before the close, so this approximates the recorder's 90 to 60 s cell. L1-family, held to settlement.
Windows evaluated 264 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 3 days; zero-volume trades 0.
PF at 1 contract 0.42, at 10 contracts 0.52, at 10 contracts with fees x1.2 0.52; net per contract -3.73c at 1, -3.05c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 6 | 5 | 1 | -79.5c | -79.5c | 0.17 |
| 2026-10-31 | 5 | 5 | 0 | +17.4c | -62.1c | 0.35 |
| 2026-11-01 | 4 | 4 | 0 | +16.3c | -45.8c | 0.52 |

### GEN4_B01

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and zd >= -1.585; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.13 n 46; validation PF1 2.64 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 55 on 3 days; zero-volume trades 0.
PF at 1 contract 0.89, at 10 contracts 0.95, at 10 contracts with fees x1.2 0.93; net per contract -2.16c at 1, -1.01c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +73.8c | +73.8c | 1.34 |
| 2026-10-31 | 17 | 10 | 7 | -165.8c | -92.0c | 0.86 |
| 2026-11-01 | 25 | 17 | 8 | +36.6c | -55.4c | 0.95 |

### GEN4_B02

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and zd >= -2.066; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.09 n 51; validation PF1 2.40 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 53 on 3 days; zero-volume trades 0.
PF at 1 contract 0.92, at 10 contracts 0.98, at 10 contracts with fees x1.2 0.96; net per contract -1.48c at 1, -0.35c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -89.3c | -89.3c | 0.74 |
| 2026-10-31 | 14 | 9 | 5 | -10.8c | -100.1c | 0.84 |
| 2026-11-01 | 24 | 17 | 7 | +81.5c | -18.6c | 0.98 |

### GEN4_B03

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and sp15 >= -0.1949 and zd >= -0.3503; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.62 n 40; validation PF1 2.39 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 49 on 3 days; zero-volume trades 0.
PF at 1 contract 0.64, at 10 contracts 0.68, at 10 contracts with fees x1.2 0.67; net per contract -8.89c at 1, -8.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 4 | 6 | -110.1c | -110.1c | 0.58 |
| 2026-10-31 | 17 | 8 | 9 | -42.3c | -152.4c | 0.78 |
| 2026-11-01 | 22 | 9 | 13 | -239.4c | -391.8c | 0.68 |

### GEN4_B04

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.17 and lsz_ask <= 8.072 and lsz_bid <= 8.053; bought at that ask; held to settlement. Discovery PF1 2.04 n 41; validation PF1 2.27 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 59 on 3 days; zero-volume trades 0.
PF at 1 contract 1.02, at 10 contracts 1.04, at 10 contracts with fees x1.2 1.03; net per contract +0.34c at 1, +0.84c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 12 | 2 | +160.7c | +160.7c | 2.08 |
| 2026-10-31 | 19 | 11 | 8 | -274.5c | -113.8c | 0.85 |
| 2026-11-01 | 26 | 20 | 6 | +163.3c | +49.5c | 1.04 |

### GEN4_B05

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 41; validation PF1 2.18 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 42 on 3 days; zero-volume trades 0.
PF at 1 contract 0.81, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.84; net per contract -3.30c at 1, -2.47c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -91.0c | -91.0c | 0.62 |
| 2026-10-31 | 16 | 8 | 8 | +64.4c | -26.6c | 0.94 |
| 2026-11-01 | 13 | 5 | 8 | -77.3c | -103.9c | 0.85 |

### GEN4_B06

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.54 n 52; validation PF1 2.08 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 54 on 3 days; zero-volume trades 0.
PF at 1 contract 0.70, at 10 contracts 0.72, at 10 contracts with fees x1.2 0.71; net per contract -5.21c at 1, -4.75c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | -148.3c | -148.3c | 0.49 |
| 2026-10-31 | 17 | 8 | 9 | +78.9c | -69.4c | 0.88 |
| 2026-11-01 | 17 | 6 | 11 | -187.0c | -256.4c | 0.72 |

### GEN4_B07

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= 0.3412 and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.68 n 43; validation PF1 2.08 n 24 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 34 on 2 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.75; net per contract -5.67c at 1, -4.84c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 16 | 7 | 9 | +25.3c | +25.3c | 1.08 |
| 2026-11-01 | 18 | 5 | 13 | -189.9c | -164.6c | 0.76 |

### GEN4_B08

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.24 n 52; validation PF1 1.99 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 57 on 3 days; zero-volume trades 0.
PF at 1 contract 0.97, at 10 contracts 1.03, at 10 contracts with fees x1.2 1.01; net per contract -0.58c at 1, +0.54c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -65.0c | -65.0c | 0.81 |
| 2026-10-31 | 17 | 12 | 5 | -0.6c | -65.6c | 0.90 |
| 2026-11-01 | 24 | 18 | 6 | +96.5c | +30.9c | 1.03 |

### GEN4_B09

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= -0.06831; bought at that ask; held to settlement. Discovery PF1 1.51 n 49; validation PF1 1.94 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 55 on 3 days; zero-volume trades 0.
PF at 1 contract 0.60, at 10 contracts 0.62, at 10 contracts with fees x1.2 0.61; net per contract -8.47c at 1, -8.05c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -122.4c | -122.4c | 0.55 |
| 2026-10-31 | 21 | 9 | 12 | -122.9c | -245.3c | 0.68 |
| 2026-11-01 | 21 | 7 | 14 | -197.2c | -442.5c | 0.62 |

### GEN4_B10

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 <= 2.256 and sp5 <= 0.353; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.79 n 46; validation PF1 1.93 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 54 on 3 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.84; net per contract -4.14c at 1, -2.94c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 10 | 4 | -57.6c | -57.6c | 0.80 |
| 2026-10-31 | 17 | 9 | 8 | -254.0c | -311.6c | 0.61 |
| 2026-11-01 | 23 | 17 | 6 | +152.7c | -158.9c | 0.85 |

### GEN4_B11

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp30 >= 0.5295; bought at that ask; held to settlement. Discovery PF1 1.50 n 46; validation PF1 1.91 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 45 on 3 days; zero-volume trades 0.
PF at 1 contract 0.62, at 10 contracts 0.64, at 10 contracts with fees x1.2 0.63; net per contract -6.88c at 1, -6.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 4 | 13 | -83.1c | -83.1c | 0.60 |
| 2026-10-31 | 14 | 5 | 9 | -30.3c | -113.4c | 0.76 |
| 2026-11-01 | 14 | 5 | 9 | -174.8c | -288.2c | 0.64 |

### GEN4_B12

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.16 and lsz_ask <= 7.779 and sp5 >= 0.1732; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.32 n 43; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 54 on 3 days; zero-volume trades 0.
PF at 1 contract 1.05, at 10 contracts 1.11, at 10 contracts with fees x1.2 1.10; net per contract +0.86c at 1, +2.07c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 11 | 1 | +258.6c | +258.6c | 4.18 |
| 2026-10-31 | 19 | 13 | 6 | -25.6c | +233.0c | 1.48 |
| 2026-11-01 | 23 | 15 | 8 | -121.2c | +111.8c | 1.11 |

### GEN4_B13

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.65 n 56; validation PF1 1.90 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 64 on 3 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.86, at 10 contracts with fees x1.2 0.85; net per contract -3.91c at 1, -2.72c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.8c | -12.8c | 0.96 |
| 2026-10-31 | 19 | 11 | 8 | -215.6c | -228.4c | 0.73 |
| 2026-11-01 | 26 | 18 | 8 | +54.3c | -174.1c | 0.86 |

### GEN4_B14

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and lsz_ask <= 7.779; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.30 n 44; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 50 on 3 days; zero-volume trades 0.
PF at 1 contract 1.20, at 10 contracts 1.28, at 10 contracts with fees x1.2 1.26; net per contract +3.25c at 1, +4.53c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 10 | 2 | +136.8c | +136.8c | 1.99 |
| 2026-10-31 | 16 | 11 | 5 | +25.4c | +162.2c | 1.37 |
| 2026-11-01 | 22 | 16 | 6 | +64.1c | +226.3c | 1.28 |

### GEN4_B15

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26 and sp15 >= -0.01237 and spread >= 0.001; bought at that ask; held to settlement. Discovery PF1 1.55 n 42; validation PF1 1.86 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 48 on 3 days; zero-volume trades 0.
PF at 1 contract 0.43, at 10 contracts 0.44, at 10 contracts with fees x1.2 0.43; net per contract -15.71c at 1, -15.27c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 4 | 7 | -206.0c | -206.0c | 0.31 |
| 2026-10-31 | 17 | 8 | 9 | -194.7c | -400.7c | 0.49 |
| 2026-11-01 | 20 | 8 | 12 | -332.3c | -733.0c | 0.44 |

### GEN4_B16

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and spread <= 0.01; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.14 n 48; validation PF1 1.83 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 58 on 3 days; zero-volume trades 0.
PF at 1 contract 0.95, at 10 contracts 1.02, at 10 contracts with fees x1.2 1.00; net per contract -0.92c at 1, +0.36c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +100.3c | +100.3c | 1.46 |
| 2026-10-31 | 19 | 12 | 7 | -135.8c | -35.5c | 0.95 |
| 2026-11-01 | 25 | 18 | 7 | +56.1c | +20.6c | 1.02 |

### GEN4_B17

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.4847 and zd >= -2.066; bought at that ask; held to settlement. Discovery PF1 1.52 n 48; validation PF1 1.82 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 53 on 3 days; zero-volume trades 0.
PF at 1 contract 0.81, at 10 contracts 0.83, at 10 contracts with fees x1.2 0.82; net per contract -4.13c at 1, -3.66c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 13 | 4 | +24.0c | +24.0c | 1.08 |
| 2026-10-31 | 14 | 6 | 8 | -419.1c | -395.1c | 0.55 |
| 2026-11-01 | 22 | 18 | 4 | +200.9c | -194.2c | 0.83 |

### GEN4_B18

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and lsz_ask <= 7.779 and zd >= -0.6765; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.63 n 43; validation PF1 1.81 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 54 on 3 days; zero-volume trades 0.
PF at 1 contract 0.96, at 10 contracts 1.02, at 10 contracts with fees x1.2 1.00; net per contract -0.83c at 1, +0.32c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 9 | 3 | +57.1c | +57.1c | 1.28 |
| 2026-10-31 | 17 | 10 | 7 | -145.2c | -88.1c | 0.86 |
| 2026-11-01 | 25 | 18 | 7 | +105.3c | +17.2c | 1.02 |

### GEN4_B19

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and imb >= -0.6701; bought at that ask; held to settlement. Discovery PF1 1.78 n 48; validation PF1 1.81 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 55 on 3 days; zero-volume trades 0.
PF at 1 contract 0.96, at 10 contracts 0.98, at 10 contracts with fees x1.2 0.97; net per contract -0.84c at 1, -0.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -52.6c | -52.6c | 0.85 |
| 2026-10-31 | 16 | 10 | 6 | -136.8c | -189.4c | 0.76 |
| 2026-11-01 | 22 | 17 | 5 | +167.4c | -22.0c | 0.98 |

### GEN4_B20

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and imb >= -0.4281 and sp5 <= 0; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.66 n 43; validation PF1 1.77 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 48 on 3 days; zero-volume trades 0.
PF at 1 contract 1.04, at 10 contracts 1.11, at 10 contracts with fees x1.2 1.09; net per contract +0.75c at 1, +1.89c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -55.9c | -55.9c | 0.80 |
| 2026-10-31 | 13 | 9 | 4 | +24.2c | -31.7c | 0.94 |
| 2026-11-01 | 22 | 16 | 6 | +122.3c | +90.6c | 1.11 |

### GEN4_B21

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.902 and lsz_bid >= 7.292; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.54 n 44; validation PF1 1.76 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 26 on 3 days; zero-volume trades 0.
PF at 1 contract 0.71, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.75; net per contract -6.23c at 1, -5.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 9 | 5 | -132.3c | -132.3c | 0.62 |
| 2026-10-31 | 1 | 0 | 1 | -70.5c | -202.8c | 0.51 |
| 2026-11-01 | 11 | 9 | 2 | +69.5c | -133.3c | 0.76 |

### GEN4_B22

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.456 and lsz_bid >= 6.195; bought at that ask; held to settlement. Discovery PF1 1.63 n 49; validation PF1 1.73 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 59 on 3 days; zero-volume trades 0.
PF at 1 contract 0.81, at 10 contracts 0.83, at 10 contracts with fees x1.2 0.82; net per contract -4.17c at 1, -3.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -44.0c | -44.0c | 0.87 |
| 2026-10-31 | 18 | 12 | 6 | -67.7c | -111.7c | 0.86 |
| 2026-11-01 | 24 | 16 | 8 | -106.8c | -218.5c | 0.83 |

### GEN4_B23

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; held to settlement. Discovery PF1 1.55 n 40; validation PF1 1.71 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 40 on 3 days; zero-volume trades 0.
PF at 1 contract 0.91, at 10 contracts 0.93, at 10 contracts with fees x1.2 0.92; net per contract -1.93c at 1, -1.43c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.6c | +24.6c | inf |
| 2026-10-31 | 16 | 8 | 8 | -326.0c | -301.4c | 0.47 |
| 2026-11-01 | 23 | 19 | 4 | +244.3c | -57.1c | 0.93 |

### GEN4_B24

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.292; bought at that ask; held to settlement. Discovery PF1 2.01 n 50; validation PF1 1.65 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 40 on 3 days; zero-volume trades 0.
PF at 1 contract 0.70, at 10 contracts 0.72, at 10 contracts with fees x1.2 0.71; net per contract -6.98c at 1, -6.54c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -54.9c | -54.9c | 0.84 |
| 2026-10-31 | 7 | 5 | 2 | +28.0c | -26.9c | 0.94 |
| 2026-11-01 | 17 | 10 | 7 | -234.7c | -261.6c | 0.72 |

### GEN4_B25

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.00 n 40; validation PF1 1.64 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 46 on 3 days; zero-volume trades 0.
PF at 1 contract 0.78, at 10 contracts 0.83, at 10 contracts with fees x1.2 0.82; net per contract -5.01c at 1, -3.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 6 | 4 | -85.4c | -85.4c | 0.71 |
| 2026-10-31 | 17 | 10 | 7 | -216.7c | -302.1c | 0.61 |
| 2026-11-01 | 19 | 15 | 4 | +122.7c | -179.4c | 0.83 |

### GEN4_B26

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and lsz_bid >= 5.465; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.57 n 49; validation PF1 1.63 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 56 on 3 days; zero-volume trades 0.
PF at 1 contract 0.67, at 10 contracts 0.72, at 10 contracts with fees x1.2 0.71; net per contract -7.66c at 1, -6.53c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -37.3c | -37.3c | 0.89 |
| 2026-10-31 | 16 | 8 | 8 | -347.5c | -384.8c | 0.59 |
| 2026-11-01 | 22 | 16 | 6 | +19.1c | -365.7c | 0.72 |

### GEN4_B27

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.52 n 40; validation PF1 1.63 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 40 on 3 days; zero-volume trades 0.
PF at 1 contract 0.87, at 10 contracts 0.92, at 10 contracts with fees x1.2 0.91; net per contract -2.79c at 1, -1.60c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 16 | 8 | 8 | -327.4c | -303.0c | 0.47 |
| 2026-11-01 | 23 | 19 | 4 | +239.1c | -63.9c | 0.92 |

### GEN4_B28

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and lsz_ask <= 7.388; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.92 n 40; validation PF1 1.61 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 49 on 3 days; zero-volume trades 0.
PF at 1 contract 0.97, at 10 contracts 1.03, at 10 contracts with fees x1.2 1.01; net per contract -0.66c at 1, +0.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 7 | 2 | +57.7c | +57.7c | 1.46 |
| 2026-10-31 | 18 | 11 | 7 | -180.5c | -122.8c | 0.80 |
| 2026-11-01 | 22 | 17 | 5 | +147.3c | +24.5c | 1.03 |

### GEN4_B29

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.1233; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.26 n 51; validation PF1 1.61 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 56 on 3 days; zero-volume trades 0.
PF at 1 contract 1.17, at 10 contracts 1.25, at 10 contracts with fees x1.2 1.23; net per contract +2.70c at 1, +3.98c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +106.3c | +106.3c | 1.48 |
| 2026-10-31 | 17 | 12 | 5 | +29.0c | +135.3c | 1.26 |
| 2026-11-01 | 24 | 18 | 6 | +87.7c | +223.0c | 1.25 |

### GEN4_B30

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask >= 7.388 and sp15 >= -0.9017 and sp30 <= 2.256; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 45; validation PF1 1.61 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 44 on 3 days; zero-volume trades 0.
PF at 1 contract 0.65, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -8.21c at 1, -7.15c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -46.3c | -46.3c | 0.83 |
| 2026-10-31 | 12 | 6 | 6 | -275.9c | -322.2c | 0.55 |
| 2026-11-01 | 19 | 14 | 5 | +7.5c | -314.7c | 0.70 |

### GEN4_B31

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid <= 8.422; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.71 n 55; validation PF1 1.59 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 64 on 3 days; zero-volume trades 0.
PF at 1 contract 0.90, at 10 contracts 0.96, at 10 contracts with fees x1.2 0.95; net per contract -1.90c at 1, -0.72c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 15 | 4 | +69.2c | +69.2c | 1.24 |
| 2026-10-31 | 19 | 11 | 8 | -277.5c | -208.3c | 0.76 |
| 2026-11-01 | 26 | 20 | 6 | +162.0c | -46.3c | 0.96 |

### GEN4_B32

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.95 n 40; validation PF1 1.57 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 48 on 3 days; zero-volume trades 0.
PF at 1 contract 0.87, at 10 contracts 0.93, at 10 contracts with fees x1.2 0.91; net per contract -2.59c at 1, -1.44c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +24.3c | +24.3c | 1.11 |
| 2026-10-31 | 19 | 12 | 7 | -100.0c | -75.7c | 0.88 |
| 2026-11-01 | 19 | 13 | 6 | +6.4c | -69.3c | 0.93 |

### GEN4_B33

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and spread >= 0.001 and vol <= 0.311; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.59 n 40; validation PF1 1.54 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 40 on 3 days; zero-volume trades 0.
PF at 1 contract 0.90, at 10 contracts 0.96, at 10 contracts with fees x1.2 0.95; net per contract -2.10c at 1, -0.76c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 16 | 8 | 8 | -288.5c | -264.1c | 0.50 |
| 2026-11-01 | 23 | 19 | 4 | +233.8c | -30.3c | 0.96 |

### GEN4_B34

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 6.824 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.83 n 52; validation PF1 1.54 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 55 on 3 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.81, at 10 contracts with fees x1.2 0.80; net per contract -4.49c at 1, -4.08c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -28.0c | -28.0c | 0.92 |
| 2026-10-31 | 13 | 8 | 5 | -71.3c | -99.3c | 0.85 |
| 2026-11-01 | 24 | 16 | 8 | -125.3c | -224.6c | 0.81 |

### GEN4_B35

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and sp15 >= 1.584 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 2.38 n 41; validation PF1 1.52 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 36 on 3 days; zero-volume trades 0.
PF at 1 contract 2.21, at 10 contracts 2.30, at 10 contracts with fees x1.2 2.27; net per contract +13.56c at 1, +14.03c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | +180.7c | +180.7c | 1.87 |
| 2026-10-31 | 7 | 3 | 4 | +92.6c | +273.3c | 1.85 |
| 2026-11-01 | 9 | 4 | 5 | +231.7c | +505.0c | 2.30 |

### GEN4_B36

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.83 n 40; validation PF1 1.52 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 48 on 3 days; zero-volume trades 0.
PF at 1 contract 0.87, at 10 contracts 0.93, at 10 contracts with fees x1.2 0.91; net per contract -2.77c at 1, -1.52c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +25.7c | +25.7c | 1.12 |
| 2026-10-31 | 19 | 12 | 7 | -121.6c | -95.9c | 0.85 |
| 2026-11-01 | 19 | 14 | 5 | +23.1c | -72.8c | 0.93 |

### GEN4_B37

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm30 <= 0.17 and sp5 >= 0.353 and spread >= 0.001; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.52 n 43; validation PF1 1.49 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 51 on 3 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.84, at 10 contracts with fees x1.2 0.83; net per contract -3.31c at 1, -2.36c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 3 | 11 | -119.8c | -119.8c | 0.54 |
| 2026-10-31 | 17 | 7 | 10 | +90.6c | -29.2c | 0.94 |
| 2026-11-01 | 20 | 8 | 12 | -91.0c | -120.2c | 0.84 |

### GEN4_B38

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 <= 0.0315; bought at that ask; held to settlement. Discovery PF1 1.50 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 60 on 3 days; zero-volume trades 0.
PF at 1 contract 0.74, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.75; net per contract -5.97c at 1, -5.49c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -112.6c | -112.6c | 0.69 |
| 2026-10-31 | 19 | 11 | 8 | -285.1c | -397.7c | 0.59 |
| 2026-11-01 | 26 | 19 | 7 | +68.1c | -329.6c | 0.76 |

### GEN4_B39

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.01237; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.44 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 58 on 3 days; zero-volume trades 0.
PF at 1 contract 1.01, at 10 contracts 1.08, at 10 contracts with fees x1.2 1.06; net per contract +0.28c at 1, +1.44c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +168.7c | +168.7c | 1.84 |
| 2026-10-31 | 17 | 9 | 8 | -306.9c | -138.2c | 0.82 |
| 2026-11-01 | 24 | 19 | 5 | +221.5c | +83.3c | 1.08 |

### GEN4_B40

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.9734; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.57 n 55; validation PF1 1.44 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 64 on 3 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.86, at 10 contracts with fees x1.2 0.85; net per contract -4.12c at 1, -2.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.7c | -12.7c | 0.96 |
| 2026-10-31 | 19 | 11 | 8 | -245.4c | -258.1c | 0.71 |
| 2026-11-01 | 26 | 19 | 7 | +76.7c | -181.4c | 0.86 |

### GEN4_B41

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.733 and spread >= 0.01; bought at that ask; held to settlement. Discovery PF1 1.52 n 43; validation PF1 1.43 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 34 on 3 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.81, at 10 contracts with fees x1.2 0.80; net per contract -4.53c at 1, -4.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +85.5c | +85.5c | 1.46 |
| 2026-10-31 | 7 | 5 | 2 | -5.0c | +80.5c | 1.25 |
| 2026-11-01 | 14 | 8 | 6 | -221.1c | -140.6c | 0.81 |

### GEN4_B42

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= -0.07 and imb >= -0.9734 and sp15 >= 1.584; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.23 n 41; validation PF1 1.42 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 37 on 3 days; zero-volume trades 0.
PF at 1 contract 2.36, at 10 contracts 2.49, at 10 contracts with fees x1.2 2.46; net per contract +14.76c at 1, +15.61c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 21 | 5 | 16 | +163.0c | +163.0c | 1.77 |
| 2026-10-31 | 7 | 4 | 3 | +185.6c | +348.6c | 2.09 |
| 2026-11-01 | 9 | 4 | 5 | +229.0c | +577.6c | 2.49 |

### GEN4_B43

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.75 n 48; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 60 on 3 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.84; net per contract -4.40c at 1, -3.27c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +11.5c | +11.5c | 1.04 |
| 2026-10-31 | 19 | 11 | 8 | -276.5c | -265.0c | 0.70 |
| 2026-11-01 | 26 | 19 | 7 | +69.0c | -196.0c | 0.85 |

### GEN4_B44

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 >= 0.353; bought at that ask; held to settlement. Discovery PF1 2.35 n 51; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 57 on 3 days; zero-volume trades 0.
PF at 1 contract 1.01, at 10 contracts 1.03, at 10 contracts with fees x1.2 1.01; net per contract +0.12c at 1, +0.54c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 14 | 2 | +262.6c | +262.6c | 3.00 |
| 2026-10-31 | 17 | 11 | 6 | -106.5c | +156.1c | 1.28 |
| 2026-11-01 | 24 | 16 | 8 | -125.6c | +30.5c | 1.03 |

### GEN4_B45

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and lsz_bid >= 6.824; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.02 n 47; validation PF1 1.37 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 47 on 3 days; zero-volume trades 0.
PF at 1 contract 0.96, at 10 contracts 1.03, at 10 contracts with fees x1.2 1.02; net per contract -0.65c at 1, +0.58c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -54.8c | -54.8c | 0.84 |
| 2026-10-31 | 11 | 8 | 3 | +65.8c | +11.0c | 1.02 |
| 2026-11-01 | 19 | 14 | 5 | +16.3c | +27.3c | 1.03 |

### GEN4_B46

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.11 and lsz_ask <= 7.388; bought at that ask; held to settlement. Discovery PF1 2.64 n 45; validation PF1 1.34 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 55 on 3 days; zero-volume trades 0.
PF at 1 contract 1.08, at 10 contracts 1.11, at 10 contracts with fees x1.2 1.09; net per contract +1.55c at 1, +2.02c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 11 | 2 | +192.8c | +192.8c | 2.40 |
| 2026-10-31 | 18 | 11 | 7 | -196.2c | -3.4c | 0.99 |
| 2026-11-01 | 24 | 18 | 6 | +114.7c | +111.3c | 1.11 |

### GEN4_B47

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; held to settlement. Discovery PF1 1.79 n 48; validation PF1 1.33 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 60 on 3 days; zero-volume trades 0.
PF at 1 contract 0.83, at 10 contracts 0.86, at 10 contracts with fees x1.2 0.84; net per contract -3.60c at 1, -3.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +13.7c | +13.7c | 1.05 |
| 2026-10-31 | 19 | 11 | 8 | -274.5c | -260.8c | 0.70 |
| 2026-11-01 | 26 | 19 | 7 | +73.0c | -187.8c | 0.86 |

### GEN4_B48

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm15 >= -0.09 and sp30 >= -2.625; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.70 n 41; validation PF1 1.33 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 49 on 3 days; zero-volume trades 0.
PF at 1 contract 0.71, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.75; net per contract -6.79c at 1, -5.67c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 8 | 3 | +12.6c | +12.6c | 1.05 |
| 2026-10-31 | 17 | 9 | 8 | -348.4c | -335.8c | 0.59 |
| 2026-11-01 | 21 | 16 | 5 | +58.0c | -277.8c | 0.76 |

### GEN4_B49

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; held to settlement. Discovery PF1 2.47 n 55; validation PF1 1.33 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 58 on 3 days; zero-volume trades 0.
PF at 1 contract 1.06, at 10 contracts 1.09, at 10 contracts with fees x1.2 1.07; net per contract +1.14c at 1, +1.59c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +177.3c | +177.3c | 1.91 |
| 2026-10-31 | 17 | 9 | 8 | -310.2c | -132.9c | 0.82 |
| 2026-11-01 | 24 | 19 | 5 | +225.4c | +92.5c | 1.09 |

### GEN4_B50

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp15 >= -0.1949 and zd >= -1.214; bought at that ask; held to settlement. Discovery PF1 1.87 n 41; validation PF1 1.31 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 46 on 3 days; zero-volume trades 0.
PF at 1 contract 1.33, at 10 contracts 1.36, at 10 contracts with fees x1.2 1.34; net per contract +5.13c at 1, +5.57c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +88.5c | +88.5c | 1.45 |
| 2026-10-31 | 10 | 7 | 3 | +21.5c | +110.0c | 1.27 |
| 2026-11-01 | 22 | 17 | 5 | +146.0c | +256.0c | 1.36 |

### GEN4_B51

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0.04 and imb <= 0.4847; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.72 n 50; validation PF1 1.30 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 58 on 3 days; zero-volume trades 0.
PF at 1 contract 0.78, at 10 contracts 0.83, at 10 contracts with fees x1.2 0.82; net per contract -4.67c at 1, -3.55c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +75.9c | +75.9c | 1.33 |
| 2026-10-31 | 18 | 10 | 8 | -301.9c | -226.0c | 0.72 |
| 2026-11-01 | 25 | 18 | 7 | +20.0c | -206.0c | 0.83 |

### GEN4_REF_FAV150

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. The unconditional core of 41 of the 51 GEN4 validation passes: buy the favourite (side ask 0.50 to 0.85) at the first poll 150 to 120 s before the close, hold. Discovery PF1 1.61 n 50; validation PF1 1.57 n 35. Shows whether the conditions add anything forward.
Windows evaluated 175 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 58 on 3 days; zero-volume trades 0.
PF at 1 contract 0.84, at 10 contracts 0.86, at 10 contracts with fees x1.2 0.85; net per contract -3.43c at 1, -2.97c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -34.7c | -34.7c | 0.90 |
| 2026-10-31 | 17 | 9 | 8 | -314.1c | -348.8c | 0.63 |
| 2026-11-01 | 23 | 18 | 5 | +176.6c | -172.2c | 0.86 |

### REF_L1_GOLD

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T00:00:00Z. The live L1 gold rule as a known baseline: the side whose ask is 0.88 to 0.97 at the candle ending 6 minutes before the close, bought at that ask, held to settlement. Candles only, so it ignores the live 25c exit and the window limit.
Windows evaluated 84 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 1 days; zero-volume trades 0.
PF at 1 contract 0.95, at 10 contracts 1.03, at 10 contracts with fees x1.2 1.01; net per contract -0.31c at 1, +0.17c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 14 | 1 | +2.5c | +2.5c | 1.03 |

