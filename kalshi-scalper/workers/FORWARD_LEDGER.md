# FORWARD LEDGER (automatic; research only)

Written by `python -m scalper.fwdledger run` (once per AUTO pass, `scalper.autoscore check`). Last updated 2026-10-31 04:09 UTC.
Forward evidence counts only windows that CLOSED after a candidate's freeze time, had the data its rule needs and have settled.
Fees 7% x C x p x (1-p) rounded up to the cent per order, at 1 and 10 contracts; held to settlement pays the entry fee only. Win = net at 10 contracts above zero. Net per contract is at 10 contracts. Trades per week: forward trades over the time from the freeze to the last evaluated close.
This ledger never promotes anything. READY FOR THE FALSIFIER means only: forward PF 1.5+ at 1 and at 10 contracts on 30+ trades over 10+ trade days. It earns a falsifier read, nothing more. How a generator adds a candidate: `workers/candidates/README.md`.

| id | market | stage | freeze | fwd days | trades | wins | losses | PF 1c | PF 10c | net/contract | trades/week | updated | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| REF_GEN6_OIREL | KXBTC15M | reference | 2026-10-30 | 2 | 2 | 0 | 2 | 0.00 | 0.00 | -26.60c | 14.0 | 2026-10-31 04:09 UTC |  |
| LADFADE_BTC | KXBTC15M | validation | 2026-10-30 | 2 | 1 | 0 | 1 | 0.00 | 0.00 | -44.80c | 7.0 | 2026-10-31 04:09 UTC |  |
| REF_GEN6_OICORE | KXBTC15M | reference | 2026-10-30 | 2 | 5 | 0 | 5 | 0.00 | 0.00 | -17.86c | 35.0 | 2026-10-31 04:09 UTC |  |
| GEN6_B01 | KXBTC15M | validation | 2026-10-30 | 2 | 1 | 0 | 1 | 0.00 | 0.00 | -34.60c | 6.7 | 2026-10-31 04:09 UTC |  |
| GEN6_B02 | KXBTC15M | validation | 2026-10-30 | 2 | 1 | 0 | 1 | 0.00 | 0.00 | -0.50c | 7.0 | 2026-10-31 04:09 UTC |  |
| GEN6_B03 | KXBTC15M | validation | 2026-10-30 | 2 | 5 | 0 | 5 | 0.00 | 0.00 | -17.86c | 33.6 | 2026-10-31 04:09 UTC |  |
| GEN6_B04 | KXBTC15M | validation | 2026-10-30 | 2 | 5 | 0 | 5 | 0.00 | 0.00 | -17.86c | 33.6 | 2026-10-31 04:09 UTC |  |
| GEN6_B05 | KXBTC15M | validation | 2026-10-30 | 2 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-31 04:09 UTC |  |
| GEN6_B06 | KXBTC15M | validation | 2026-10-30 | 2 | 3 | 0 | 3 | 0.00 | 0.00 | -14.83c | 20.2 | 2026-10-31 04:09 UTC |  |
| GEN6_B07 | KXBTC15M | validation | 2026-10-30 | 2 | 4 | 1 | 3 | 0.40 | 0.42 | -9.43c | 26.9 | 2026-10-31 04:09 UTC |  |
| GEN6_B08 | KXBTC15M | validation | 2026-10-30 | 2 | 5 | 1 | 4 | 0.78 | 0.82 | -2.08c | 33.6 | 2026-10-31 04:09 UTC |  |
| GEN6_B09 | KXBTC15M | validation | 2026-10-30 | 2 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-31 04:09 UTC |  |
| GEN6_B10 | KXBTC15M | validation | 2026-10-30 | 2 | 11 | 2 | 9 | 1.24 | 1.34 | +2.60c | 73.9 | 2026-10-31 04:09 UTC |  |
| GEN6_B11 | KXBTC15M | validation | 2026-10-30 | 2 | 4 | 1 | 3 | 2.63 | 2.96 | +8.38c | 26.9 | 2026-10-31 04:09 UTC |  |
| GEN6_B12 | KXBTC15M | validation | 2026-10-30 | 2 | 3 | 1 | 2 | 1.08 | 1.11 | +1.80c | 20.2 | 2026-10-31 04:09 UTC |  |
| GEN6_B13 | KXBTC15M | validation | 2026-10-30 | 2 | 3 | 0 | 3 | 0.00 | 0.00 | -21.83c | 20.2 | 2026-10-31 04:09 UTC |  |
| REF_BTC_UNDERDOG_180 | KXBTC15M | reference | 2026-10-30 | 2 | 32 | 8 | 24 | 0.66 | 0.68 | -7.48c | 215.0 | 2026-10-31 04:09 UTC |  |
| GEN7_B01 | KXBTC15M | validation | 2026-10-30 | 2 | 1 | 0 | 1 | 0.00 | 0.00 | -12.80c | 6.5 | 2026-10-31 04:09 UTC |  |
| GEN7_B02 | KXBTC15M | validation | 2026-10-30 | 2 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-31 04:09 UTC |  |
| REF_GEN6_OIDRIFT | KXBTC15M | reference | 2026-10-30 | 2 | 1 | 0 | 1 | 0.00 | 0.00 | -43.80c | 6.5 | 2026-10-31 04:09 UTC |  |
| REF_GOLD_UNDERDOG_180 | KXGOLD15M | reference | 2026-10-30 | 1 | 31 | 7 | 24 | 0.60 | 0.61 | -9.10c | 217.0 | 2026-10-31 04:09 UTC |  |
| REF_LATECAL_BTC | KXBTC15M | reference | 2026-10-30 | 2 | 6 | 5 | 1 | 0.14 | 0.17 | -13.25c | 38.8 | 2026-10-31 04:09 UTC |  |
| GEN4_B01 | KXBTC15M | validation | 2026-10-30 | 2 | 14 | 10 | 4 | 1.09 | 1.15 | +2.76c | 98.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B02 | KXBTC15M | validation | 2026-10-30 | 2 | 16 | 10 | 6 | 0.63 | 0.67 | -7.78c | 112.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B03 | KXBTC15M | validation | 2026-10-30 | 2 | 11 | 4 | 7 | 0.43 | 0.45 | -16.83c | 77.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B04 | KXBTC15M | validation | 2026-10-30 | 2 | 15 | 12 | 3 | 1.35 | 1.38 | +5.69c | 105.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B05 | KXBTC15M | validation | 2026-10-30 | 2 | 14 | 3 | 11 | 0.47 | 0.49 | -10.88c | 98.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B06 | KXBTC15M | validation | 2026-10-30 | 2 | 21 | 5 | 16 | 0.39 | 0.41 | -10.00c | 147.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B07 | KXBTC15M | validation | 2026-10-30 | 2 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B08 | KXBTC15M | validation | 2026-10-30 | 2 | 17 | 11 | 6 | 0.63 | 0.67 | -8.24c | 119.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B09 | KXBTC15M | validation | 2026-10-30 | 2 | 14 | 3 | 11 | 0.45 | 0.46 | -12.37c | 98.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B10 | KXBTC15M | validation | 2026-10-30 | 2 | 15 | 10 | 5 | 0.66 | 0.71 | -6.19c | 105.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B11 | KXBTC15M | validation | 2026-10-30 | 2 | 18 | 4 | 14 | 0.45 | 0.47 | -8.04c | 126.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B12 | KXBTC15M | validation | 2026-10-30 | 2 | 13 | 11 | 2 | 2.55 | 2.69 | +16.43c | 91.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B13 | KXBTC15M | validation | 2026-10-30 | 2 | 20 | 14 | 6 | 0.81 | 0.87 | -2.40c | 140.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B14 | KXBTC15M | validation | 2026-10-30 | 2 | 13 | 10 | 3 | 1.40 | 1.50 | +7.06c | 91.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B15 | KXBTC15M | validation | 2026-10-30 | 2 | 12 | 4 | 8 | 0.24 | 0.25 | -23.45c | 84.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B16 | KXBTC15M | validation | 2026-10-30 | 2 | 15 | 11 | 4 | 1.14 | 1.21 | +3.69c | 105.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B17 | KXBTC15M | validation | 2026-10-30 | 2 | 18 | 13 | 5 | 0.84 | 0.86 | -2.86c | 126.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B18 | KXBTC15M | validation | 2026-10-30 | 2 | 13 | 9 | 4 | 1.03 | 1.09 | +1.68c | 91.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B19 | KXBTC15M | validation | 2026-10-30 | 2 | 18 | 12 | 6 | 0.68 | 0.70 | -7.11c | 126.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B20 | KXBTC15M | validation | 2026-10-30 | 2 | 13 | 9 | 4 | 0.76 | 0.80 | -4.30c | 91.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B21 | KXBTC15M | validation | 2026-10-30 | 2 | 14 | 9 | 5 | 0.58 | 0.62 | -9.45c | 98.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B22 | KXBTC15M | validation | 2026-10-30 | 2 | 18 | 12 | 6 | 0.73 | 0.75 | -5.77c | 126.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B23 | KXBTC15M | validation | 2026-10-30 | 2 | 2 | 1 | 1 | 0.39 | 0.40 | -18.55c | 14.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B24 | KXBTC15M | validation | 2026-10-30 | 2 | 17 | 12 | 5 | 0.94 | 0.96 | -0.92c | 119.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B25 | KXBTC15M | validation | 2026-10-30 | 2 | 11 | 6 | 5 | 0.56 | 0.59 | -13.16c | 77.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B26 | KXBTC15M | validation | 2026-10-30 | 2 | 19 | 13 | 6 | 0.69 | 0.73 | -5.91c | 133.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B27 | KXBTC15M | validation | 2026-10-30 | 2 | 2 | 1 | 1 | 0.37 | 0.40 | -18.45c | 14.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B28 | KXBTC15M | validation | 2026-10-30 | 2 | 10 | 7 | 3 | 0.86 | 0.91 | -1.73c | 70.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B29 | KXBTC15M | validation | 2026-10-30 | 2 | 16 | 12 | 4 | 1.15 | 1.23 | +3.83c | 112.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B30 | KXBTC15M | validation | 2026-10-30 | 2 | 14 | 9 | 5 | 0.61 | 0.65 | -8.66c | 98.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B31 | KXBTC15M | validation | 2026-10-30 | 2 | 20 | 15 | 5 | 0.92 | 0.98 | -0.29c | 140.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B32 | KXBTC15M | validation | 2026-10-30 | 2 | 11 | 7 | 4 | 0.97 | 1.02 | +0.43c | 77.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B33 | KXBTC15M | validation | 2026-10-30 | 2 | 2 | 1 | 1 | 0.72 | 0.78 | -3.45c | 14.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B34 | KXBTC15M | validation | 2026-10-30 | 2 | 19 | 13 | 6 | 0.77 | 0.78 | -4.62c | 133.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B35 | KXBTC15M | validation | 2026-10-30 | 2 | 21 | 6 | 15 | 2.14 | 2.24 | +12.21c | 147.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B36 | KXBTC15M | validation | 2026-10-30 | 2 | 11 | 7 | 4 | 0.93 | 0.98 | -0.34c | 77.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B37 | KXBTC15M | validation | 2026-10-30 | 2 | 15 | 3 | 12 | 0.47 | 0.50 | -9.29c | 105.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B38 | KXBTC15M | validation | 2026-10-30 | 2 | 16 | 10 | 6 | 0.56 | 0.57 | -11.75c | 112.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B39 | KXBTC15M | validation | 2026-10-30 | 2 | 18 | 14 | 4 | 1.26 | 1.34 | +5.21c | 126.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B40 | KXBTC15M | validation | 2026-10-30 | 2 | 20 | 14 | 6 | 0.79 | 0.85 | -2.89c | 140.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B41 | KXBTC15M | validation | 2026-10-30 | 2 | 14 | 11 | 3 | 1.64 | 1.68 | +8.91c | 98.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B42 | KXBTC15M | validation | 2026-10-30 | 2 | 22 | 6 | 16 | 2.00 | 2.12 | +10.82c | 154.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B43 | KXBTC15M | validation | 2026-10-30 | 2 | 16 | 11 | 5 | 0.78 | 0.82 | -3.97c | 112.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B44 | KXBTC15M | validation | 2026-10-30 | 2 | 17 | 14 | 3 | 1.87 | 1.91 | +11.01c | 119.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B45 | KXBTC15M | validation | 2026-10-30 | 2 | 17 | 12 | 5 | 0.79 | 0.84 | -3.22c | 119.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B46 | KXBTC15M | validation | 2026-10-30 | 2 | 14 | 11 | 3 | 1.52 | 1.55 | +8.39c | 98.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B47 | KXBTC15M | validation | 2026-10-30 | 2 | 16 | 11 | 5 | 0.81 | 0.83 | -3.86c | 112.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B48 | KXBTC15M | validation | 2026-10-30 | 2 | 12 | 8 | 4 | 0.75 | 0.79 | -5.53c | 84.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B49 | KXBTC15M | validation | 2026-10-30 | 2 | 18 | 14 | 4 | 1.35 | 1.38 | +5.66c | 126.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B50 | KXBTC15M | validation | 2026-10-30 | 2 | 15 | 11 | 4 | 1.03 | 1.05 | +0.87c | 105.0 | 2026-10-31 04:09 UTC |  |
| GEN4_B51 | KXBTC15M | validation | 2026-10-30 | 2 | 16 | 12 | 4 | 0.94 | 1.00 | +0.06c | 112.0 | 2026-10-31 04:09 UTC |  |
| GEN4_REF_FAV150 | KXBTC15M | reference | 2026-10-30 | 2 | 19 | 13 | 6 | 0.72 | 0.74 | -5.79c | 133.0 | 2026-10-31 04:09 UTC |  |
| REF_L1_GOLD | KXGOLD15M | reference | 2026-10-30 | 1 | 15 | 14 | 1 | 0.95 | 1.03 | +0.17c | 105.0 | 2026-10-31 04:09 UTC |  |

## History per candidate

### REF_GEN6_OIREL

Evaluator `scalper.oirel:forward_eval`, source `candles`, frozen 2026-10-30T15:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) when open interest over the 3 minutes before rose by more than 26.76% of its level at 360 s (the discovery quantile matched to the core's 86,300 count), fill at the next candle's ask, held. History: discovery n 298 PF 1.73, validation n 286 PF 1.71 at 10 contracts (FALS5 check 2, one try). Not independent of REF_GEN6_OICORE (59% to 80% shared trades). workers/FALS5_REGISTRATION.md, workers/FALS5_RESULT.md.
Windows evaluated 48 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 2 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -26.90c at 1, -26.60c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -43.8c | -43.8c | 0.00 |
| 2026-10-31 | 1 | 0 | 1 | -9.4c | -53.2c | 0.00 |

### LADFADE_BTC

Evaluator `scalper.ladfade:forward_eval`, source `candles`, frozen 2026-10-30T12:00:00Z. Bitcoin 15 minute windows opening at :15 and :30: when the hourly KXBTCD ladder leans 5c+ from 50/50 at the first minute, buy the side the 15 minute book overshot AWAY from if its ask is 3c+ below the ladder's chance, at the next candle's ask (30c to 70c), held. Ladder from the book recorder. Discovery and validation spent (post hoc); holdout read once in workers/LADFADE_RESULT.md. 1 try; workers/LADFADE_REGISTRATION.md.
Windows evaluated 37 on 2 days; without the data the rule needs 23; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -45.00c at 1, -44.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -44.8c | -44.8c | 0.00 |

### REF_GEN6_OICORE

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T03:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest rose more than 86,300 contracts over the 3 minutes before, held to settlement, fill at the next candle's ask. History: discovery PF 2.28 (n 222), validation 1.85 (n 333, z 4.53). Forward days only; 1 try. Falsifier FALS4 running.
Windows evaluated 96 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -18.42c at 1, -17.86c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 3 | 0 | 3 | -45.0c | -89.3c | 0.00 |

### GEN6_B01

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | doi>8.63e+04 & m3>-0.25 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.81 (n 104), validation PF 1.90 (n 164), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -35.00c at 1, -34.60c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 1 | 0 | 1 | -34.6c | -34.6c | 0.00 |

### GEN6_B02

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | hour<=21 & xb_d2<=0.046 & doi>8.63e+04 | TP +8c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 2.42 (n 106), validation PF 1.80 (n 133), C=10.
Windows evaluated 89 on 2 days; without the data the rule needs 11; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -1.40c at 1, -0.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |

### GEN6_B03

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 | TP +5c stop -20c else hold]; fill at the next candle's ask. Discovery PF 2.41 (n 222), validation PF 1.73 (n 333), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -18.60c at 1, -17.86c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 3 | 0 | 3 | -45.0c | -89.3c | 0.00 |

### GEN6_B04

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 & xa_spr<=0.02 & rng5>0.14 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.06 (n 175), validation PF 1.68 (n 269), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -18.42c at 1, -17.86c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 3 | 0 | 3 | -45.0c | -89.3c | 0.00 |

### GEN6_B05

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | d3<=-0.08 & m1<=0 & vol<=1.11e+05 | TP +20c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 1.60 (n 172), validation PF 1.66 (n 58), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B06

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | d1<=0.1 & doi>8.63e+04 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 3.51 (n 111), validation PF 1.57 (n 162), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -15.40c at 1, -14.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |
| 2026-10-31 | 2 | 0 | 2 | -44.0c | -44.5c | 0.00 |

### GEN6_B07

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 240..180s | m3>-0.08 & m5<=-0.24 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.72 (n 137), validation PF 1.45 (n 90), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 2 days; zero-volume trades 0.
PF at 1 contract 0.40, at 10 contracts 0.42, at 10 contracts with fees x1.2 0.41; net per contract -10.03c at 1, -9.43c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 1 | 1 | +20.1c | +20.1c | 3.64 |
| 2026-10-31 | 2 | 0 | 2 | -57.8c | -37.7c | 0.42 |

### GEN6_B08

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | rng5<=0.273 & doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.14 (n 205), validation PF 1.43 (n 316), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 2 days; zero-volume trades 0.
PF at 1 contract 0.78, at 10 contracts 0.82, at 10 contracts with fees x1.2 0.81; net per contract -2.66c at 1, -2.08c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -56.6c | -56.6c | 0.00 |
| 2026-10-31 | 2 | 1 | 1 | +46.2c | -10.4c | 0.82 |

### GEN6_B09

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | vol<=1.28e+05 & m1<=-0.0507 | TP +3c stop -20c else sell 60s]; fill at the next candle's ask. Discovery PF 1.55 (n 192), validation PF 1.42 (n 86), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B10

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.19 (n 433), validation PF 1.41 (n 587), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 2 days; zero-volume trades 0.
PF at 1 contract 1.24, at 10 contracts 1.34, at 10 contracts with fees x1.2 1.32; net per contract +2.02c at 1, +2.60c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 1 | 6 | -6.3c | -6.3c | 0.91 |
| 2026-10-31 | 4 | 1 | 3 | +34.9c | +28.6c | 1.34 |

### GEN6_B11

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | ask<=0.19 & xa_spr<=0.003 & d1<=-0.05 | TP +5c stop -5c else hold]; fill at the next candle's ask. Discovery PF 1.82 (n 110), validation PF 1.37 (n 93), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 2 days; zero-volume trades 0.
PF at 1 contract 2.63, at 10 contracts 2.96, at 10 contracts with fees x1.2 2.88; net per contract +7.75c at 1, +8.38c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +47.3c | +47.3c | 15.33 |
| 2026-10-31 | 1 | 0 | 1 | -13.8c | +33.5c | 2.96 |

### GEN6_B12

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | rng5>0.32 & hour>19 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.83 (n 102), validation PF 1.32 (n 72), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 1.08, at 10 contracts 1.11, at 10 contracts with fees x1.2 1.08; net per contract +1.33c at 1, +1.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +5.4c | +5.4c | 1.11 |

### GEN6_B13

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | m1>-0.2 & hour>19 | TP +8c stop -20c else hold]; fill at the next candle's ask. Discovery PF 1.70 (n 173), validation PF 1.31 (n 129), C=10.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -22.40c at 1, -21.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -65.5c | -65.5c | 0.00 |

### REF_BTC_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T02:00:00Z. The mirror of FALS3's finding (Bitcoin favourites at 50c to 85c are overpriced 2 to 3 minutes before the close: PF 0.77 on 2,576 windows, z -4.97): buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held to settlement. History already read (UNDER1 found this side positive), so only forward days count; REV1 is the registered forward read of the related cheap-NO rule (2026-11-05). 1 try.
Windows evaluated 100 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 32 on 2 days; zero-volume trades 0.
PF at 1 contract 0.66, at 10 contracts 0.68, at 10 contracts with fees x1.2 0.67; net per contract -7.91c at 1, -7.48c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 25 | 6 | 19 | -206.1c | -206.1c | 0.65 |
| 2026-10-31 | 7 | 2 | 5 | -33.3c | -239.4c | 0.68 |

### GEN7_B01

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 240..240s | npv1>0.281 & vol>1.32e+05 | sell at 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 3.28 (n 101), validation PF 1.80 (n 126), C=10.
Windows evaluated 104 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -13.90c at 1, -12.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -12.8c | -12.8c | 0.00 |

### GEN7_B02

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 300..240s | npv1>0.393 & doi5>9.78e+04 | TP +20c stop -20c else sell 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 1.75 (n 135), validation PF 1.71 (n 101), C=10.
Windows evaluated 104 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_GEN6_OIDRIFT

Evaluator `scalper.oidrift:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest over the 3 minutes before rose above the 90th percentile of that change over the 30 UTC days before (earlier days only, 20+ days needed), fill at the next candle's ask, held. History validation n 67, PF 2.65 (FALS4 check 5, reproduced). Not independent of REF_GEN6_OICORE. 1 try; workers/OIDRIFT_REGISTRATION.md.
Windows evaluated 104 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
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
Windows evaluated 104 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 1 days; zero-volume trades 0.
PF at 1 contract 0.14, at 10 contracts 0.17, at 10 contracts with fees x1.2 0.17; net per contract -13.95c at 1, -13.25c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 6 | 5 | 1 | -79.5c | -79.5c | 0.17 |

### GEN4_B01

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and zd >= -1.585; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.13 n 46; validation PF1 2.64 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 2 days; zero-volume trades 0.
PF at 1 contract 1.09, at 10 contracts 1.15, at 10 contracts with fees x1.2 1.14; net per contract +1.56c at 1, +2.76c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +73.8c | +73.8c | 1.34 |
| 2026-10-31 | 1 | 0 | 1 | -35.2c | +38.6c | 1.15 |

### GEN4_B02

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and zd >= -2.066; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.09 n 51; validation PF1 2.40 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 16 on 2 days; zero-volume trades 0.
PF at 1 contract 0.63, at 10 contracts 0.67, at 10 contracts with fees x1.2 0.66; net per contract -8.91c at 1, -7.78c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -89.3c | -89.3c | 0.74 |
| 2026-10-31 | 1 | 0 | 1 | -35.2c | -124.5c | 0.67 |

### GEN4_B03

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and sp15 >= -0.1949 and zd >= -0.3503; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.62 n 40; validation PF1 2.39 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 2 days; zero-volume trades 0.
PF at 1 contract 0.43, at 10 contracts 0.45, at 10 contracts with fees x1.2 0.45; net per contract -17.72c at 1, -16.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 4 | 6 | -110.1c | -110.1c | 0.58 |
| 2026-10-31 | 1 | 0 | 1 | -75.0c | -185.1c | 0.45 |

### GEN4_B04

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.17 and lsz_ask <= 8.072 and lsz_bid <= 8.053; bought at that ask; held to settlement. Discovery PF1 2.04 n 41; validation PF1 2.27 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 2 days; zero-volume trades 0.
PF at 1 contract 1.35, at 10 contracts 1.38, at 10 contracts with fees x1.2 1.36; net per contract +5.20c at 1, +5.69c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 12 | 2 | +160.7c | +160.7c | 2.08 |
| 2026-10-31 | 1 | 0 | 1 | -75.4c | +85.3c | 1.38 |

### GEN4_B05

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 41; validation PF1 2.18 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 2 days; zero-volume trades 0.
PF at 1 contract 0.47, at 10 contracts 0.49, at 10 contracts with fees x1.2 0.49; net per contract -11.65c at 1, -10.88c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -91.0c | -91.0c | 0.62 |
| 2026-10-31 | 1 | 0 | 1 | -61.3c | -152.3c | 0.49 |

### GEN4_B06

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.54 n 52; validation PF1 2.08 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 21 on 2 days; zero-volume trades 0.
PF at 1 contract 0.39, at 10 contracts 0.41, at 10 contracts with fees x1.2 0.40; net per contract -10.49c at 1, -10.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | -148.3c | -148.3c | 0.49 |
| 2026-10-31 | 1 | 0 | 1 | -61.7c | -210.0c | 0.41 |

### GEN4_B07

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= 0.3412 and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.68 n 43; validation PF1 2.08 n 24 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B08

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.24 n 52; validation PF1 1.99 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 17 on 2 days; zero-volume trades 0.
PF at 1 contract 0.63, at 10 contracts 0.67, at 10 contracts with fees x1.2 0.66; net per contract -9.27c at 1, -8.24c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -65.0c | -65.0c | 0.81 |
| 2026-10-31 | 1 | 0 | 1 | -75.0c | -140.0c | 0.67 |

### GEN4_B09

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= -0.06831; bought at that ask; held to settlement. Discovery PF1 1.51 n 49; validation PF1 1.94 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 2 days; zero-volume trades 0.
PF at 1 contract 0.45, at 10 contracts 0.46, at 10 contracts with fees x1.2 0.46; net per contract -12.88c at 1, -12.37c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -122.4c | -122.4c | 0.55 |
| 2026-10-31 | 1 | 0 | 1 | -50.8c | -173.2c | 0.46 |

### GEN4_B10

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 <= 2.256 and sp5 <= 0.353; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.79 n 46; validation PF1 1.93 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 2 days; zero-volume trades 0.
PF at 1 contract 0.66, at 10 contracts 0.71, at 10 contracts with fees x1.2 0.70; net per contract -7.38c at 1, -6.19c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 10 | 4 | -57.6c | -57.6c | 0.80 |
| 2026-10-31 | 1 | 0 | 1 | -35.2c | -92.8c | 0.71 |

### GEN4_B11

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp30 >= 0.5295; bought at that ask; held to settlement. Discovery PF1 1.50 n 46; validation PF1 1.91 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 18 on 2 days; zero-volume trades 0.
PF at 1 contract 0.45, at 10 contracts 0.47, at 10 contracts with fees x1.2 0.46; net per contract -8.53c at 1, -8.04c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 4 | 13 | -83.1c | -83.1c | 0.60 |
| 2026-10-31 | 1 | 0 | 1 | -61.7c | -144.8c | 0.47 |

### GEN4_B12

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.16 and lsz_ask <= 7.779 and sp5 >= 0.1732; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.32 n 43; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 13 on 2 days; zero-volume trades 0.
PF at 1 contract 2.55, at 10 contracts 2.69, at 10 contracts with fees x1.2 2.65; net per contract +15.26c at 1, +16.43c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 11 | 1 | +258.6c | +258.6c | 4.18 |
| 2026-10-31 | 1 | 0 | 1 | -45.0c | +213.6c | 2.69 |

### GEN4_B13

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.65 n 56; validation PF1 1.90 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 20 on 2 days; zero-volume trades 0.
PF at 1 contract 0.81, at 10 contracts 0.87, at 10 contracts with fees x1.2 0.86; net per contract -3.60c at 1, -2.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.8c | -12.8c | 0.96 |
| 2026-10-31 | 1 | 0 | 1 | -35.2c | -48.0c | 0.87 |

### GEN4_B14

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and lsz_ask <= 7.779; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.30 n 44; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 13 on 2 days; zero-volume trades 0.
PF at 1 contract 1.40, at 10 contracts 1.50, at 10 contracts with fees x1.2 1.48; net per contract +5.78c at 1, +7.06c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 10 | 2 | +136.8c | +136.8c | 1.99 |
| 2026-10-31 | 1 | 0 | 1 | -45.0c | +91.8c | 1.50 |

### GEN4_B15

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26 and sp15 >= -0.01237 and spread >= 0.001; bought at that ask; held to settlement. Discovery PF1 1.55 n 42; validation PF1 1.86 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 2 days; zero-volume trades 0.
PF at 1 contract 0.24, at 10 contracts 0.25, at 10 contracts with fees x1.2 0.25; net per contract -23.92c at 1, -23.45c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 4 | 7 | -206.0c | -206.0c | 0.31 |
| 2026-10-31 | 1 | 0 | 1 | -75.4c | -281.4c | 0.25 |

### GEN4_B16

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and spread <= 0.01; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.14 n 48; validation PF1 1.83 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 2 days; zero-volume trades 0.
PF at 1 contract 1.14, at 10 contracts 1.21, at 10 contracts with fees x1.2 1.19; net per contract +2.45c at 1, +3.69c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +100.3c | +100.3c | 1.46 |
| 2026-10-31 | 1 | 0 | 1 | -45.0c | +55.3c | 1.21 |

### GEN4_B17

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.4847 and zd >= -2.066; bought at that ask; held to settlement. Discovery PF1 1.52 n 48; validation PF1 1.82 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 18 on 2 days; zero-volume trades 0.
PF at 1 contract 0.84, at 10 contracts 0.86, at 10 contracts with fees x1.2 0.85; net per contract -3.28c at 1, -2.86c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 13 | 4 | +24.0c | +24.0c | 1.08 |
| 2026-10-31 | 1 | 0 | 1 | -75.4c | -51.4c | 0.86 |

### GEN4_B18

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and lsz_ask <= 7.779 and zd >= -0.6765; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.63 n 43; validation PF1 1.81 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 13 on 2 days; zero-volume trades 0.
PF at 1 contract 1.03, at 10 contracts 1.09, at 10 contracts with fees x1.2 1.08; net per contract +0.54c at 1, +1.68c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 9 | 3 | +57.1c | +57.1c | 1.28 |
| 2026-10-31 | 1 | 0 | 1 | -35.2c | +21.9c | 1.09 |

### GEN4_B19

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and imb >= -0.6701; bought at that ask; held to settlement. Discovery PF1 1.78 n 48; validation PF1 1.81 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 18 on 2 days; zero-volume trades 0.
PF at 1 contract 0.68, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -7.50c at 1, -7.11c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -52.6c | -52.6c | 0.85 |
| 2026-10-31 | 1 | 0 | 1 | -75.4c | -128.0c | 0.70 |

### GEN4_B20

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and imb >= -0.4281 and sp5 <= 0; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.66 n 43; validation PF1 1.77 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 13 on 1 days; zero-volume trades 0.
PF at 1 contract 0.76, at 10 contracts 0.80, at 10 contracts with fees x1.2 0.79; net per contract -5.43c at 1, -4.30c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -55.9c | -55.9c | 0.80 |

### GEN4_B21

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.902 and lsz_bid >= 7.292; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.54 n 44; validation PF1 1.76 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 1 days; zero-volume trades 0.
PF at 1 contract 0.58, at 10 contracts 0.62, at 10 contracts with fees x1.2 0.61; net per contract -10.42c at 1, -9.45c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 9 | 5 | -132.3c | -132.3c | 0.62 |

### GEN4_B22

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.456 and lsz_bid >= 6.195; bought at that ask; held to settlement. Discovery PF1 1.63 n 49; validation PF1 1.73 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 18 on 2 days; zero-volume trades 0.
PF at 1 contract 0.73, at 10 contracts 0.75, at 10 contracts with fees x1.2 0.73; net per contract -6.17c at 1, -5.77c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -44.0c | -44.0c | 0.87 |
| 2026-10-31 | 1 | 0 | 1 | -59.8c | -103.8c | 0.75 |

### GEN4_B23

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; held to settlement. Discovery PF1 1.55 n 40; validation PF1 1.71 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 2 on 2 days; zero-volume trades 0.
PF at 1 contract 0.39, at 10 contracts 0.40, at 10 contracts with fees x1.2 0.39; net per contract -19.00c at 1, -18.55c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.6c | +24.6c | inf |
| 2026-10-31 | 1 | 0 | 1 | -61.7c | -37.1c | 0.40 |

### GEN4_B24

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.292; bought at that ask; held to settlement. Discovery PF1 2.01 n 50; validation PF1 1.65 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 17 on 2 days; zero-volume trades 0.
PF at 1 contract 0.94, at 10 contracts 0.96, at 10 contracts with fees x1.2 0.94; net per contract -1.29c at 1, -0.92c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -54.9c | -54.9c | 0.84 |
| 2026-10-31 | 1 | 1 | 0 | +39.3c | -15.6c | 0.96 |

### GEN4_B25

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.00 n 40; validation PF1 1.64 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 2 days; zero-volume trades 0.
PF at 1 contract 0.56, at 10 contracts 0.59, at 10 contracts with fees x1.2 0.59; net per contract -14.19c at 1, -13.16c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 6 | 4 | -85.4c | -85.4c | 0.71 |
| 2026-10-31 | 1 | 0 | 1 | -59.4c | -144.8c | 0.59 |

### GEN4_B26

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and lsz_bid >= 5.465; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.57 n 49; validation PF1 1.63 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 19 on 2 days; zero-volume trades 0.
PF at 1 contract 0.69, at 10 contracts 0.73, at 10 contracts with fees x1.2 0.72; net per contract -6.99c at 1, -5.91c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -37.3c | -37.3c | 0.89 |
| 2026-10-31 | 1 | 0 | 1 | -75.0c | -112.3c | 0.73 |

### GEN4_B27

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.52 n 40; validation PF1 1.63 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 2 on 2 days; zero-volume trades 0.
PF at 1 contract 0.37, at 10 contracts 0.40, at 10 contracts with fees x1.2 0.39; net per contract -19.80c at 1, -18.45c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 1 | 0 | 1 | -61.3c | -36.9c | 0.40 |

### GEN4_B28

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and lsz_ask <= 7.388; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.92 n 40; validation PF1 1.61 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 2 days; zero-volume trades 0.
PF at 1 contract 0.86, at 10 contracts 0.91, at 10 contracts with fees x1.2 0.90; net per contract -2.92c at 1, -1.73c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 7 | 2 | +57.7c | +57.7c | 1.46 |
| 2026-10-31 | 1 | 0 | 1 | -75.0c | -17.3c | 0.91 |

### GEN4_B29

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.1233; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.26 n 51; validation PF1 1.61 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 16 on 2 days; zero-volume trades 0.
PF at 1 contract 1.15, at 10 contracts 1.23, at 10 contracts with fees x1.2 1.21; net per contract +2.61c at 1, +3.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +106.3c | +106.3c | 1.48 |
| 2026-10-31 | 1 | 0 | 1 | -45.0c | +61.3c | 1.23 |

### GEN4_B30

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask >= 7.388 and sp15 >= -0.9017 and sp30 <= 2.256; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 45; validation PF1 1.61 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 2 days; zero-volume trades 0.
PF at 1 contract 0.61, at 10 contracts 0.65, at 10 contracts with fees x1.2 0.64; net per contract -9.67c at 1, -8.66c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -46.3c | -46.3c | 0.83 |
| 2026-10-31 | 1 | 0 | 1 | -75.0c | -121.3c | 0.65 |

### GEN4_B31

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid <= 8.422; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.71 n 55; validation PF1 1.59 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 20 on 2 days; zero-volume trades 0.
PF at 1 contract 0.92, at 10 contracts 0.98, at 10 contracts with fees x1.2 0.97; net per contract -1.45c at 1, -0.29c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 15 | 4 | +69.2c | +69.2c | 1.24 |
| 2026-10-31 | 1 | 0 | 1 | -75.0c | -5.8c | 0.98 |

### GEN4_B32

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.95 n 40; validation PF1 1.57 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 2 days; zero-volume trades 0.
PF at 1 contract 0.97, at 10 contracts 1.02, at 10 contracts with fees x1.2 1.01; net per contract -0.74c at 1, +0.43c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +24.3c | +24.3c | 1.11 |
| 2026-10-31 | 1 | 0 | 1 | -19.6c | +4.7c | 1.02 |

### GEN4_B33

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and spread >= 0.001 and vol <= 0.311; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.59 n 40; validation PF1 1.54 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 2 on 2 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.78, at 10 contracts with fees x1.2 0.75; net per contract -4.55c at 1, -3.45c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 1 | 0 | 1 | -31.3c | -6.9c | 0.78 |

### GEN4_B34

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 6.824 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.83 n 52; validation PF1 1.54 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 19 on 2 days; zero-volume trades 0.
PF at 1 contract 0.77, at 10 contracts 0.78, at 10 contracts with fees x1.2 0.77; net per contract -5.00c at 1, -4.62c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -28.0c | -28.0c | 0.92 |
| 2026-10-31 | 1 | 0 | 1 | -59.8c | -87.8c | 0.78 |

### GEN4_B35

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and sp15 >= 1.584 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 2.38 n 41; validation PF1 1.52 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 21 on 2 days; zero-volume trades 0.
PF at 1 contract 2.14, at 10 contracts 2.24, at 10 contracts with fees x1.2 2.21; net per contract +11.70c at 1, +12.21c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | +180.7c | +180.7c | 1.87 |
| 2026-10-31 | 1 | 1 | 0 | +75.7c | +256.4c | 2.24 |

### GEN4_B36

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.83 n 40; validation PF1 1.52 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 2 days; zero-volume trades 0.
PF at 1 contract 0.93, at 10 contracts 0.98, at 10 contracts with fees x1.2 0.97; net per contract -1.53c at 1, -0.34c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +25.7c | +25.7c | 1.12 |
| 2026-10-31 | 1 | 0 | 1 | -29.4c | -3.7c | 0.98 |

### GEN4_B37

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm30 <= 0.17 and sp5 >= 0.353 and spread >= 0.001; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.52 n 43; validation PF1 1.49 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 2 days; zero-volume trades 0.
PF at 1 contract 0.47, at 10 contracts 0.50, at 10 contracts with fees x1.2 0.49; net per contract -10.18c at 1, -9.29c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 3 | 11 | -119.8c | -119.8c | 0.54 |
| 2026-10-31 | 1 | 0 | 1 | -19.6c | -139.4c | 0.50 |

### GEN4_B38

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 <= 0.0315; bought at that ask; held to settlement. Discovery PF1 1.50 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 16 on 2 days; zero-volume trades 0.
PF at 1 contract 0.56, at 10 contracts 0.57, at 10 contracts with fees x1.2 0.57; net per contract -12.19c at 1, -11.75c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -112.6c | -112.6c | 0.69 |
| 2026-10-31 | 1 | 0 | 1 | -75.4c | -188.0c | 0.57 |

### GEN4_B39

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.01237; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.44 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 18 on 2 days; zero-volume trades 0.
PF at 1 contract 1.26, at 10 contracts 1.34, at 10 contracts with fees x1.2 1.32; net per contract +4.06c at 1, +5.21c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +168.7c | +168.7c | 1.84 |
| 2026-10-31 | 1 | 0 | 1 | -75.0c | +93.7c | 1.34 |

### GEN4_B40

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.9734; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.57 n 55; validation PF1 1.44 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 20 on 2 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.84; net per contract -4.10c at 1, -2.89c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.7c | -12.7c | 0.96 |
| 2026-10-31 | 1 | 0 | 1 | -45.0c | -57.7c | 0.85 |

### GEN4_B41

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.733 and spread >= 0.01; bought at that ask; held to settlement. Discovery PF1 1.52 n 43; validation PF1 1.43 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 2 days; zero-volume trades 0.
PF at 1 contract 1.64, at 10 contracts 1.68, at 10 contracts with fees x1.2 1.65; net per contract +8.50c at 1, +8.91c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +85.5c | +85.5c | 1.46 |
| 2026-10-31 | 1 | 1 | 0 | +39.3c | +124.8c | 1.68 |

### GEN4_B42

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= -0.07 and imb >= -0.9734 and sp15 >= 1.584; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.23 n 41; validation PF1 1.42 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 22 on 2 days; zero-volume trades 0.
PF at 1 contract 2.00, at 10 contracts 2.12, at 10 contracts with fees x1.2 2.10; net per contract +10.04c at 1, +10.82c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 21 | 5 | 16 | +163.0c | +163.0c | 1.77 |
| 2026-10-31 | 1 | 1 | 0 | +75.0c | +238.0c | 2.12 |

### GEN4_B43

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.75 n 48; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 16 on 2 days; zero-volume trades 0.
PF at 1 contract 0.78, at 10 contracts 0.82, at 10 contracts with fees x1.2 0.81; net per contract -5.04c at 1, -3.97c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +11.5c | +11.5c | 1.04 |
| 2026-10-31 | 1 | 0 | 1 | -75.0c | -63.5c | 0.82 |

### GEN4_B44

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 >= 0.353; bought at that ask; held to settlement. Discovery PF1 2.35 n 51; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 17 on 2 days; zero-volume trades 0.
PF at 1 contract 1.87, at 10 contracts 1.91, at 10 contracts with fees x1.2 1.88; net per contract +10.65c at 1, +11.01c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 14 | 2 | +262.6c | +262.6c | 3.00 |
| 2026-10-31 | 1 | 0 | 1 | -75.4c | +187.2c | 1.91 |

### GEN4_B45

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and lsz_bid >= 6.824; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.02 n 47; validation PF1 1.37 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 17 on 1 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.84, at 10 contracts with fees x1.2 0.83; net per contract -4.39c at 1, -3.22c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -54.8c | -54.8c | 0.84 |

### GEN4_B46

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.11 and lsz_ask <= 7.388; bought at that ask; held to settlement. Discovery PF1 2.64 n 45; validation PF1 1.34 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 2 days; zero-volume trades 0.
PF at 1 contract 1.52, at 10 contracts 1.55, at 10 contracts with fees x1.2 1.53; net per contract +7.93c at 1, +8.39c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 11 | 2 | +192.8c | +192.8c | 2.40 |
| 2026-10-31 | 1 | 0 | 1 | -75.4c | +117.4c | 1.55 |

### GEN4_B47

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; held to settlement. Discovery PF1 1.79 n 48; validation PF1 1.33 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 16 on 2 days; zero-volume trades 0.
PF at 1 contract 0.81, at 10 contracts 0.83, at 10 contracts with fees x1.2 0.82; net per contract -4.25c at 1, -3.86c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +13.7c | +13.7c | 1.05 |
| 2026-10-31 | 1 | 0 | 1 | -75.4c | -61.7c | 0.83 |

### GEN4_B48

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm15 >= -0.09 and sp30 >= -2.625; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.70 n 41; validation PF1 1.33 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 2 days; zero-volume trades 0.
PF at 1 contract 0.75, at 10 contracts 0.79, at 10 contracts with fees x1.2 0.78; net per contract -6.69c at 1, -5.53c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 8 | 3 | +12.6c | +12.6c | 1.05 |
| 2026-10-31 | 1 | 0 | 1 | -78.9c | -66.3c | 0.79 |

### GEN4_B49

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; held to settlement. Discovery PF1 2.47 n 55; validation PF1 1.33 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 18 on 2 days; zero-volume trades 0.
PF at 1 contract 1.35, at 10 contracts 1.38, at 10 contracts with fees x1.2 1.36; net per contract +5.28c at 1, +5.66c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +177.3c | +177.3c | 1.91 |
| 2026-10-31 | 1 | 0 | 1 | -75.4c | +101.9c | 1.38 |

### GEN4_B50

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp15 >= -0.1949 and zd >= -1.214; bought at that ask; held to settlement. Discovery PF1 1.87 n 41; validation PF1 1.31 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 2 days; zero-volume trades 0.
PF at 1 contract 1.03, at 10 contracts 1.05, at 10 contracts with fees x1.2 1.03; net per contract +0.47c at 1, +0.87c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +88.5c | +88.5c | 1.45 |
| 2026-10-31 | 1 | 0 | 1 | -75.4c | +13.1c | 1.05 |

### GEN4_B51

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0.04 and imb <= 0.4847; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.72 n 50; validation PF1 1.30 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 16 on 2 days; zero-volume trades 0.
PF at 1 contract 0.94, at 10 contracts 1.00, at 10 contracts with fees x1.2 0.99; net per contract -1.11c at 1, +0.06c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +75.9c | +75.9c | 1.33 |
| 2026-10-31 | 1 | 0 | 1 | -75.0c | +0.9c | 1.00 |

### GEN4_REF_FAV150

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. The unconditional core of 41 of the 51 GEN4 validation passes: buy the favourite (side ask 0.50 to 0.85) at the first poll 150 to 120 s before the close, hold. Discovery PF1 1.61 n 50; validation PF1 1.57 n 35. Shows whether the conditions add anything forward.
Windows evaluated 55 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 19 on 2 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.74, at 10 contracts with fees x1.2 0.73; net per contract -6.21c at 1, -5.79c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -34.7c | -34.7c | 0.90 |
| 2026-10-31 | 1 | 0 | 1 | -75.4c | -110.1c | 0.74 |

### REF_L1_GOLD

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T00:00:00Z. The live L1 gold rule as a known baseline: the side whose ask is 0.88 to 0.97 at the candle ending 6 minutes before the close, bought at that ask, held to settlement. Candles only, so it ignores the live 25c exit and the window limit.
Windows evaluated 84 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 1 days; zero-volume trades 0.
PF at 1 contract 0.95, at 10 contracts 1.03, at 10 contracts with fees x1.2 1.01; net per contract -0.31c at 1, +0.17c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 14 | 1 | +2.5c | +2.5c | 1.03 |

