# FORWARD LEDGER (automatic; research only)

Written by `python -m scalper.fwdledger run` (once per AUTO pass, `scalper.autoscore check`). Last updated 2026-10-31 21:09 UTC.
Forward evidence counts only windows that CLOSED after a candidate's freeze time, had the data its rule needs and have settled.
Fees 7% x C x p x (1-p) rounded up to the cent per order, at 1 and 10 contracts; held to settlement pays the entry fee only. Win = net at 10 contracts above zero. Net per contract is at 10 contracts. Trades per week: forward trades over the time from the freeze to the last evaluated close.
This ledger never promotes anything. READY FOR THE FALSIFIER means only: forward PF 1.5+ at 1 and at 10 contracts on 30+ trades over 10+ trade days. It earns a falsifier read, nothing more. How a generator adds a candidate: `workers/candidates/README.md`.

| id | market | stage | freeze | fwd days | trades | wins | losses | PF 1c | PF 10c | net/contract | trades/week | updated | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| REF_GEN6_OIREL | KXBTC15M | reference | 2026-10-30 | 2 | 3 | 0 | 3 | 0.00 | 0.00 | -20.70c | 19.4 | 2026-10-31 21:09 UTC |  |
| LADFADE_BTC | KXBTC15M | validation | 2026-10-30 | 2 | 2 | 0 | 2 | 0.00 | 0.00 | -42.75c | 11.6 | 2026-10-31 21:09 UTC |  |
| REF_GEN6_OICORE | KXBTC15M | reference | 2026-10-30 | 2 | 6 | 0 | 6 | 0.00 | 0.00 | -16.37c | 26.5 | 2026-10-31 21:09 UTC |  |
| GEN6_B01 | KXBTC15M | validation | 2026-10-30 | 2 | 1 | 0 | 1 | 0.00 | 0.00 | -34.60c | 4.3 | 2026-10-31 21:09 UTC |  |
| GEN6_B02 | KXBTC15M | validation | 2026-10-30 | 2 | 1 | 0 | 1 | 0.00 | 0.00 | -0.50c | 4.5 | 2026-10-31 21:09 UTC |  |
| GEN6_B03 | KXBTC15M | validation | 2026-10-30 | 2 | 6 | 0 | 6 | 0.00 | 0.00 | -16.37c | 25.8 | 2026-10-31 21:09 UTC |  |
| GEN6_B04 | KXBTC15M | validation | 2026-10-30 | 2 | 6 | 0 | 6 | 0.00 | 0.00 | -16.37c | 25.8 | 2026-10-31 21:09 UTC |  |
| GEN6_B05 | KXBTC15M | validation | 2026-10-30 | 2 | 5 | 1 | 4 | 0.10 | 0.12 | -6.04c | 21.5 | 2026-10-31 21:09 UTC |  |
| GEN6_B06 | KXBTC15M | validation | 2026-10-30 | 2 | 3 | 0 | 3 | 0.00 | 0.00 | -14.83c | 12.9 | 2026-10-31 21:09 UTC |  |
| GEN6_B07 | KXBTC15M | validation | 2026-10-30 | 2 | 4 | 1 | 3 | 0.40 | 0.42 | -9.43c | 17.2 | 2026-10-31 21:09 UTC |  |
| GEN6_B08 | KXBTC15M | validation | 2026-10-30 | 2 | 8 | 1 | 7 | 0.66 | 0.71 | -2.40c | 34.5 | 2026-10-31 21:09 UTC |  |
| GEN6_B09 | KXBTC15M | validation | 2026-10-30 | 2 | 6 | 2 | 4 | 0.77 | 0.94 | -0.37c | 25.8 | 2026-10-31 21:09 UTC |  |
| GEN6_B10 | KXBTC15M | validation | 2026-10-30 | 2 | 15 | 2 | 13 | 1.02 | 1.11 | +0.73c | 64.6 | 2026-10-31 21:09 UTC |  |
| GEN6_B11 | KXBTC15M | validation | 2026-10-30 | 2 | 7 | 1 | 6 | 1.85 | 2.25 | +4.01c | 30.2 | 2026-10-31 21:09 UTC |  |
| GEN6_B12 | KXBTC15M | validation | 2026-10-30 | 2 | 3 | 1 | 2 | 1.08 | 1.11 | +1.80c | 12.9 | 2026-10-31 21:09 UTC |  |
| GEN6_B13 | KXBTC15M | validation | 2026-10-30 | 2 | 3 | 0 | 3 | 0.00 | 0.00 | -21.83c | 12.9 | 2026-10-31 21:09 UTC |  |
| REF_BTC_UNDERDOG_180 | KXBTC15M | reference | 2026-10-30 | 2 | 47 | 15 | 32 | 0.93 | 0.95 | -1.15c | 202.5 | 2026-10-31 21:09 UTC |  |
| GEN7_B01 | KXBTC15M | validation | 2026-10-30 | 2 | 2 | 0 | 2 | 0.00 | 0.00 | -9.30c | 8.4 | 2026-10-31 21:09 UTC |  |
| GEN7_B02 | KXBTC15M | validation | 2026-10-30 | 2 | 3 | 1 | 2 | 0.41 | 0.46 | -4.93c | 12.6 | 2026-10-31 21:09 UTC |  |
| REF_GEN6_OIDRIFT | KXBTC15M | reference | 2026-10-30 | 2 | 1 | 0 | 1 | 0.00 | 0.00 | -43.80c | 4.2 | 2026-10-31 21:09 UTC |  |
| REF_GOLD_UNDERDOG_180 | KXGOLD15M | reference | 2026-10-30 | 1 | 31 | 7 | 24 | 0.60 | 0.61 | -9.10c | 217.0 | 2026-10-31 21:09 UTC |  |
| REF_LATECAL_BTC | KXBTC15M | reference | 2026-10-30 | 2 | 10 | 9 | 1 | 0.26 | 0.32 | -6.52c | 42.0 | 2026-10-31 21:09 UTC |  |
| GEN4_B01 | KXBTC15M | validation | 2026-10-30 | 2 | 21 | 14 | 7 | 0.89 | 0.94 | -1.27c | 80.2 | 2026-10-31 21:09 UTC |  |
| GEN4_B02 | KXBTC15M | validation | 2026-10-30 | 2 | 22 | 13 | 9 | 0.60 | 0.63 | -9.43c | 84.0 | 2026-10-31 21:09 UTC |  |
| GEN4_B03 | KXBTC15M | validation | 2026-10-30 | 2 | 18 | 5 | 13 | 0.33 | 0.34 | -21.26c | 68.7 | 2026-10-31 21:09 UTC |  |
| GEN4_B04 | KXBTC15M | validation | 2026-10-30 | 2 | 23 | 17 | 6 | 1.05 | 1.08 | +1.44c | 87.8 | 2026-10-31 21:09 UTC |  |
| GEN4_B05 | KXBTC15M | validation | 2026-10-30 | 2 | 20 | 4 | 16 | 0.42 | 0.44 | -11.94c | 76.4 | 2026-10-31 21:09 UTC |  |
| GEN4_B06 | KXBTC15M | validation | 2026-10-30 | 2 | 28 | 6 | 22 | 0.36 | 0.37 | -11.66c | 106.9 | 2026-10-31 21:09 UTC |  |
| GEN4_B07 | KXBTC15M | validation | 2026-10-30 | 2 | 8 | 1 | 7 | 0.20 | 0.21 | -20.93c | 30.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B08 | KXBTC15M | validation | 2026-10-30 | 2 | 24 | 15 | 9 | 0.63 | 0.67 | -8.76c | 91.6 | 2026-10-31 21:09 UTC |  |
| GEN4_B09 | KXBTC15M | validation | 2026-10-30 | 2 | 24 | 4 | 20 | 0.28 | 0.29 | -19.70c | 91.6 | 2026-10-31 21:09 UTC |  |
| GEN4_B10 | KXBTC15M | validation | 2026-10-30 | 2 | 22 | 14 | 8 | 0.66 | 0.70 | -6.84c | 84.0 | 2026-10-31 21:09 UTC |  |
| GEN4_B11 | KXBTC15M | validation | 2026-10-30 | 2 | 25 | 5 | 20 | 0.39 | 0.40 | -10.22c | 95.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B12 | KXBTC15M | validation | 2026-10-30 | 2 | 21 | 17 | 4 | 1.95 | 2.07 | +13.17c | 80.2 | 2026-10-31 21:09 UTC |  |
| GEN4_B13 | KXBTC15M | validation | 2026-10-30 | 2 | 28 | 19 | 9 | 0.79 | 0.85 | -3.04c | 106.9 | 2026-10-31 21:09 UTC |  |
| GEN4_B14 | KXBTC15M | validation | 2026-10-30 | 2 | 20 | 14 | 6 | 1.02 | 1.08 | +1.58c | 76.4 | 2026-10-31 21:09 UTC |  |
| GEN4_B15 | KXBTC15M | validation | 2026-10-30 | 2 | 19 | 5 | 14 | 0.20 | 0.20 | -28.48c | 72.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B16 | KXBTC15M | validation | 2026-10-30 | 2 | 23 | 16 | 7 | 0.96 | 1.02 | +0.48c | 87.8 | 2026-10-31 21:09 UTC |  |
| GEN4_B17 | KXBTC15M | validation | 2026-10-30 | 2 | 23 | 15 | 8 | 0.65 | 0.66 | -8.57c | 87.8 | 2026-10-31 21:09 UTC |  |
| GEN4_B18 | KXBTC15M | validation | 2026-10-30 | 2 | 20 | 13 | 7 | 0.89 | 0.94 | -1.14c | 76.4 | 2026-10-31 21:09 UTC |  |
| GEN4_B19 | KXBTC15M | validation | 2026-10-30 | 2 | 25 | 16 | 9 | 0.68 | 0.69 | -7.89c | 95.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B20 | KXBTC15M | validation | 2026-10-30 | 2 | 20 | 13 | 7 | 0.73 | 0.77 | -5.44c | 76.4 | 2026-10-31 21:09 UTC |  |
| GEN4_B21 | KXBTC15M | validation | 2026-10-30 | 2 | 15 | 9 | 6 | 0.48 | 0.51 | -13.52c | 57.3 | 2026-10-31 21:09 UTC |  |
| GEN4_B22 | KXBTC15M | validation | 2026-10-30 | 2 | 25 | 17 | 8 | 0.90 | 0.91 | -1.90c | 95.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B23 | KXBTC15M | validation | 2026-10-30 | 2 | 8 | 4 | 4 | 0.49 | 0.50 | -17.33c | 30.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B24 | KXBTC15M | validation | 2026-10-30 | 2 | 21 | 14 | 7 | 0.81 | 0.82 | -4.14c | 80.2 | 2026-10-31 21:09 UTC |  |
| GEN4_B25 | KXBTC15M | validation | 2026-10-30 | 2 | 17 | 9 | 8 | 0.52 | 0.54 | -15.06c | 64.9 | 2026-10-31 21:09 UTC |  |
| GEN4_B26 | KXBTC15M | validation | 2026-10-30 | 2 | 26 | 17 | 9 | 0.67 | 0.71 | -7.02c | 99.3 | 2026-10-31 21:09 UTC |  |
| GEN4_B27 | KXBTC15M | validation | 2026-10-30 | 2 | 8 | 4 | 4 | 0.47 | 0.50 | -17.40c | 30.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B28 | KXBTC15M | validation | 2026-10-30 | 2 | 17 | 11 | 6 | 0.79 | 0.83 | -3.94c | 64.9 | 2026-10-31 21:09 UTC |  |
| GEN4_B29 | KXBTC15M | validation | 2026-10-30 | 2 | 23 | 16 | 7 | 0.92 | 0.98 | -0.42c | 87.8 | 2026-10-31 21:09 UTC |  |
| GEN4_B30 | KXBTC15M | validation | 2026-10-30 | 2 | 19 | 12 | 7 | 0.61 | 0.64 | -8.98c | 72.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B31 | KXBTC15M | validation | 2026-10-30 | 2 | 28 | 20 | 8 | 0.84 | 0.90 | -2.15c | 106.9 | 2026-10-31 21:09 UTC |  |
| GEN4_B32 | KXBTC15M | validation | 2026-10-30 | 2 | 19 | 12 | 7 | 0.87 | 0.92 | -1.72c | 72.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B33 | KXBTC15M | validation | 2026-10-30 | 2 | 8 | 4 | 4 | 0.54 | 0.57 | -12.64c | 30.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B34 | KXBTC15M | validation | 2026-10-30 | 2 | 25 | 17 | 8 | 0.85 | 0.87 | -2.87c | 95.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B35 | KXBTC15M | validation | 2026-10-30 | 2 | 23 | 6 | 17 | 1.64 | 1.70 | +8.32c | 87.8 | 2026-10-31 21:09 UTC |  |
| GEN4_B36 | KXBTC15M | validation | 2026-10-30 | 2 | 19 | 12 | 7 | 0.84 | 0.89 | -2.64c | 72.5 | 2026-10-31 21:09 UTC |  |
| GEN4_B37 | KXBTC15M | validation | 2026-10-30 | 2 | 23 | 4 | 19 | 0.38 | 0.41 | -10.62c | 87.8 | 2026-10-31 21:09 UTC |  |
| GEN4_B38 | KXBTC15M | validation | 2026-10-30 | 2 | 24 | 15 | 9 | 0.62 | 0.63 | -10.09c | 91.6 | 2026-10-31 21:09 UTC |  |
| GEN4_B39 | KXBTC15M | validation | 2026-10-30 | 2 | 24 | 17 | 7 | 0.96 | 1.01 | +0.21c | 91.6 | 2026-10-31 21:09 UTC |  |
| GEN4_B40 | KXBTC15M | validation | 2026-10-30 | 2 | 28 | 19 | 9 | 0.77 | 0.83 | -3.71c | 106.9 | 2026-10-31 21:09 UTC |  |
| GEN4_B41 | KXBTC15M | validation | 2026-10-30 | 2 | 18 | 13 | 5 | 1.10 | 1.12 | +2.17c | 68.7 | 2026-10-31 21:09 UTC |  |
| GEN4_B42 | KXBTC15M | validation | 2026-10-30 | 2 | 24 | 6 | 18 | 1.54 | 1.63 | +7.21c | 91.6 | 2026-10-31 21:09 UTC |  |
| GEN4_B43 | KXBTC15M | validation | 2026-10-30 | 2 | 24 | 16 | 8 | 0.76 | 0.80 | -4.87c | 91.6 | 2026-10-31 21:09 UTC |  |
| GEN4_B44 | KXBTC15M | validation | 2026-10-30 | 2 | 23 | 20 | 3 | 2.85 | 2.91 | +17.12c | 87.8 | 2026-10-31 21:09 UTC |  |
| GEN4_B45 | KXBTC15M | validation | 2026-10-30 | 2 | 23 | 16 | 7 | 0.85 | 0.90 | -2.08c | 87.8 | 2026-10-31 21:09 UTC |  |
| GEN4_B46 | KXBTC15M | validation | 2026-10-30 | 2 | 21 | 15 | 6 | 1.09 | 1.11 | +2.25c | 80.2 | 2026-10-31 21:09 UTC |  |
| GEN4_B47 | KXBTC15M | validation | 2026-10-30 | 2 | 24 | 16 | 8 | 0.79 | 0.80 | -4.75c | 91.6 | 2026-10-31 21:09 UTC |  |
| GEN4_B48 | KXBTC15M | validation | 2026-10-30 | 2 | 18 | 11 | 7 | 0.62 | 0.66 | -9.87c | 68.7 | 2026-10-31 21:09 UTC |  |
| GEN4_B49 | KXBTC15M | validation | 2026-10-30 | 2 | 24 | 17 | 7 | 1.01 | 1.03 | +0.58c | 91.6 | 2026-10-31 21:09 UTC |  |
| GEN4_B50 | KXBTC15M | validation | 2026-10-30 | 2 | 20 | 14 | 6 | 0.98 | 1.00 | -0.02c | 76.4 | 2026-10-31 21:09 UTC |  |
| GEN4_B51 | KXBTC15M | validation | 2026-10-30 | 2 | 23 | 16 | 7 | 0.80 | 0.85 | -3.30c | 87.8 | 2026-10-31 21:09 UTC |  |
| GEN4_REF_FAV150 | KXBTC15M | reference | 2026-10-30 | 2 | 26 | 17 | 9 | 0.70 | 0.72 | -6.97c | 99.3 | 2026-10-31 21:09 UTC |  |
| REF_L1_GOLD | KXGOLD15M | reference | 2026-10-30 | 1 | 15 | 14 | 1 | 0.95 | 1.03 | +0.17c | 105.0 | 2026-10-31 21:09 UTC |  |

## History per candidate

### REF_GEN6_OIREL

Evaluator `scalper.oirel:forward_eval`, source `candles`, frozen 2026-10-30T15:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) when open interest over the 3 minutes before rose by more than 26.76% of its level at 360 s (the discovery quantile matched to the core's 86,300 count), fill at the next candle's ask, held. History: discovery n 298 PF 1.73, validation n 286 PF 1.71 at 10 contracts (FALS5 check 2, one try). Not independent of REF_GEN6_OICORE (59% to 80% shared trades). workers/FALS5_REGISTRATION.md, workers/FALS5_RESULT.md.
Windows evaluated 104 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -21.03c at 1, -20.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -43.8c | -43.8c | 0.00 |
| 2026-10-31 | 2 | 0 | 2 | -18.3c | -62.1c | 0.00 |

### LADFADE_BTC

Evaluator `scalper.ladfade:forward_eval`, source `candles`, frozen 2026-10-30T12:00:00Z. Bitcoin 15 minute windows opening at :15 and :30: when the hourly KXBTCD ladder leans 5c+ from 50/50 at the first minute, buy the side the 15 minute book overshot AWAY from if its ask is 3c+ below the ladder's chance, at the next candle's ask (30c to 70c), held. Ladder from the book recorder. Discovery and validation spent (post hoc); holdout read once in workers/LADFADE_RESULT.md. 1 try; workers/LADFADE_REGISTRATION.md.
Windows evaluated 72 on 2 days; without the data the rule needs 44; evaluator errors 0. Trades 2 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -43.00c at 1, -42.75c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -44.8c | -44.8c | 0.00 |
| 2026-10-31 | 1 | 0 | 1 | -40.7c | -85.5c | 0.00 |

### REF_GEN6_OICORE

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T03:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest rose more than 86,300 contracts over the 3 minutes before, held to settlement, fill at the next candle's ask. History: discovery PF 2.28 (n 222), validation 1.85 (n 333, z 4.53). Forward days only; 1 try. Falsifier FALS4 running.
Windows evaluated 152 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -16.90c at 1, -16.37c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 4 | 0 | 4 | -53.9c | -98.2c | 0.00 |

### GEN6_B01

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | doi>8.63e+04 & m3>-0.25 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.81 (n 104), validation PF 1.90 (n 164), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -35.00c at 1, -34.60c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 1 | 0 | 1 | -34.6c | -34.6c | 0.00 |

### GEN6_B02

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | hour<=21 & xb_d2<=0.046 & doi>8.63e+04 | TP +8c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 2.42 (n 106), validation PF 1.80 (n 133), C=10.
Windows evaluated 113 on 2 days; without the data the rule needs 43; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -1.40c at 1, -0.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |

### GEN6_B03

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 | TP +5c stop -20c else hold]; fill at the next candle's ask. Discovery PF 2.41 (n 222), validation PF 1.73 (n 333), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -17.05c at 1, -16.37c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 4 | 0 | 4 | -53.9c | -98.2c | 0.00 |

### GEN6_B04

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 & xa_spr<=0.02 & rng5>0.14 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.06 (n 175), validation PF 1.68 (n 269), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -16.90c at 1, -16.37c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 4 | 0 | 4 | -53.9c | -98.2c | 0.00 |

### GEN6_B05

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | d3<=-0.08 & m1<=0 & vol<=1.11e+05 | TP +20c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 1.60 (n 172), validation PF 1.66 (n 58), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 1 days; zero-volume trades 0.
PF at 1 contract 0.10, at 10 contracts 0.12, at 10 contracts with fees x1.2 0.11; net per contract -7.22c at 1, -6.04c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 5 | 1 | 4 | -30.2c | -30.2c | 0.12 |

### GEN6_B06

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | d1<=0.1 & doi>8.63e+04 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 3.51 (n 111), validation PF 1.57 (n 162), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -15.40c at 1, -14.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |
| 2026-10-31 | 2 | 0 | 2 | -44.0c | -44.5c | 0.00 |

### GEN6_B07

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 240..180s | m3>-0.08 & m5<=-0.24 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.72 (n 137), validation PF 1.45 (n 90), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 2 days; zero-volume trades 0.
PF at 1 contract 0.40, at 10 contracts 0.42, at 10 contracts with fees x1.2 0.41; net per contract -10.03c at 1, -9.43c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 1 | 1 | +20.1c | +20.1c | 3.64 |
| 2026-10-31 | 2 | 0 | 2 | -57.8c | -37.7c | 0.42 |

### GEN6_B08

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | rng5<=0.273 & doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.14 (n 205), validation PF 1.43 (n 316), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 2 days; zero-volume trades 0.
PF at 1 contract 0.66, at 10 contracts 0.71, at 10 contracts with fees x1.2 0.70; net per contract -3.05c at 1, -2.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -56.6c | -56.6c | 0.00 |
| 2026-10-31 | 5 | 1 | 4 | +37.4c | -19.2c | 0.71 |

### GEN6_B09

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | vol<=1.28e+05 & m1<=-0.0507 | TP +3c stop -20c else sell 60s]; fill at the next candle's ask. Discovery PF 1.55 (n 192), validation PF 1.42 (n 86), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 1 days; zero-volume trades 0.
PF at 1 contract 0.77, at 10 contracts 0.94, at 10 contracts with fees x1.2 0.91; net per contract -1.52c at 1, -0.37c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 6 | 2 | 4 | -2.2c | -2.2c | 0.94 |

### GEN6_B10

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.19 (n 433), validation PF 1.41 (n 587), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 2 days; zero-volume trades 0.
PF at 1 contract 1.02, at 10 contracts 1.11, at 10 contracts with fees x1.2 1.09; net per contract +0.12c at 1, +0.73c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 1 | 6 | -6.3c | -6.3c | 0.91 |
| 2026-10-31 | 8 | 1 | 7 | +17.2c | +10.9c | 1.11 |

### GEN6_B11

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | ask<=0.19 & xa_spr<=0.003 & d1<=-0.05 | TP +5c stop -5c else hold]; fill at the next candle's ask. Discovery PF 1.82 (n 110), validation PF 1.37 (n 93), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 7 on 2 days; zero-volume trades 0.
PF at 1 contract 1.85, at 10 contracts 2.25, at 10 contracts with fees x1.2 2.18; net per contract +3.29c at 1, +4.01c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +47.3c | +47.3c | 15.33 |
| 2026-10-31 | 4 | 0 | 4 | -19.2c | +28.1c | 2.25 |

### GEN6_B12

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | rng5>0.32 & hour>19 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.83 (n 102), validation PF 1.32 (n 72), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 1.08, at 10 contracts 1.11, at 10 contracts with fees x1.2 1.08; net per contract +1.33c at 1, +1.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +5.4c | +5.4c | 1.11 |

### GEN6_B13

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | m1>-0.2 & hour>19 | TP +8c stop -20c else hold]; fill at the next candle's ask. Discovery PF 1.70 (n 173), validation PF 1.31 (n 129), C=10.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -22.40c at 1, -21.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -65.5c | -65.5c | 0.00 |

### REF_BTC_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T02:00:00Z. The mirror of FALS3's finding (Bitcoin favourites at 50c to 85c are overpriced 2 to 3 minutes before the close: PF 0.77 on 2,576 windows, z -4.97): buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held to settlement. History already read (UNDER1 found this side positive), so only forward days count; REV1 is the registered forward read of the related cheap-NO rule (2026-11-05). 1 try.
Windows evaluated 156 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 47 on 2 days; zero-volume trades 0.
PF at 1 contract 0.93, at 10 contracts 0.95, at 10 contracts with fees x1.2 0.93; net per contract -1.55c at 1, -1.15c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 25 | 6 | 19 | -206.1c | -206.1c | 0.65 |
| 2026-10-31 | 22 | 9 | 13 | +152.2c | -53.9c | 0.95 |

### GEN7_B01

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 240..240s | npv1>0.281 & vol>1.32e+05 | sell at 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 3.28 (n 101), validation PF 1.80 (n 126), C=10.
Windows evaluated 160 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 2 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -10.15c at 1, -9.30c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -12.8c | -12.8c | 0.00 |
| 2026-10-31 | 1 | 0 | 1 | -5.8c | -18.6c | 0.00 |

### GEN7_B02

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 300..240s | npv1>0.393 & doi5>9.78e+04 | TP +20c stop -20c else sell 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 1.75 (n 135), validation PF 1.71 (n 101), C=10.
Windows evaluated 160 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.41, at 10 contracts 0.46, at 10 contracts with fees x1.2 0.45; net per contract -5.73c at 1, -4.93c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 3 | 1 | 2 | -14.8c | -14.8c | 0.46 |

### REF_GEN6_OIDRIFT

Evaluator `scalper.oidrift:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest over the 3 minutes before rose above the 90th percentile of that change over the 30 UTC days before (earlier days only, 20+ days needed), fill at the next candle's ask, held. History validation n 67, PF 2.65 (FALS4 check 5, reproduced). Not independent of REF_GEN6_OICORE. 1 try; workers/OIDRIFT_REGISTRATION.md.
Windows evaluated 160 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
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
Windows evaluated 160 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 2 days; zero-volume trades 0.
PF at 1 contract 0.26, at 10 contracts 0.32, at 10 contracts with fees x1.2 0.32; net per contract -7.21c at 1, -6.52c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 6 | 5 | 1 | -79.5c | -79.5c | 0.17 |
| 2026-10-31 | 4 | 4 | 0 | +14.3c | -65.2c | 0.32 |

### GEN4_B01

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and zd >= -1.585; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.13 n 46; validation PF1 2.64 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 21 on 2 days; zero-volume trades 0.
PF at 1 contract 0.89, at 10 contracts 0.94, at 10 contracts with fees x1.2 0.93; net per contract -2.42c at 1, -1.27c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +73.8c | +73.8c | 1.34 |
| 2026-10-31 | 8 | 4 | 4 | -100.4c | -26.6c | 0.94 |

### GEN4_B02

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and zd >= -2.066; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.09 n 51; validation PF1 2.40 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 22 on 2 days; zero-volume trades 0.
PF at 1 contract 0.60, at 10 contracts 0.63, at 10 contracts with fees x1.2 0.62; net per contract -10.51c at 1, -9.43c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -89.3c | -89.3c | 0.74 |
| 2026-10-31 | 7 | 3 | 4 | -118.1c | -207.4c | 0.63 |

### GEN4_B03

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and sp15 >= -0.1949 and zd >= -0.3503; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.62 n 40; validation PF1 2.39 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 18 on 2 days; zero-volume trades 0.
PF at 1 contract 0.33, at 10 contracts 0.34, at 10 contracts with fees x1.2 0.34; net per contract -22.05c at 1, -21.26c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 4 | 6 | -110.1c | -110.1c | 0.58 |
| 2026-10-31 | 8 | 1 | 7 | -272.6c | -382.7c | 0.34 |

### GEN4_B04

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.17 and lsz_ask <= 8.072 and lsz_bid <= 8.053; bought at that ask; held to settlement. Discovery PF1 2.04 n 41; validation PF1 2.27 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 23 on 2 days; zero-volume trades 0.
PF at 1 contract 1.05, at 10 contracts 1.08, at 10 contracts with fees x1.2 1.06; net per contract +0.96c at 1, +1.44c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 12 | 2 | +160.7c | +160.7c | 2.08 |
| 2026-10-31 | 9 | 5 | 4 | -127.6c | +33.1c | 1.08 |

### GEN4_B05

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 41; validation PF1 2.18 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 20 on 2 days; zero-volume trades 0.
PF at 1 contract 0.42, at 10 contracts 0.44, at 10 contracts with fees x1.2 0.44; net per contract -12.69c at 1, -11.94c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -91.0c | -91.0c | 0.62 |
| 2026-10-31 | 7 | 1 | 6 | -147.8c | -238.8c | 0.44 |

### GEN4_B06

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.54 n 52; validation PF1 2.08 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 28 on 2 days; zero-volume trades 0.
PF at 1 contract 0.36, at 10 contracts 0.37, at 10 contracts with fees x1.2 0.36; net per contract -12.11c at 1, -11.66c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | -148.3c | -148.3c | 0.49 |
| 2026-10-31 | 8 | 1 | 7 | -178.1c | -326.4c | 0.37 |

### GEN4_B07

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= 0.3412 and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.68 n 43; validation PF1 2.08 n 24 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 1 days; zero-volume trades 0.
PF at 1 contract 0.20, at 10 contracts 0.21, at 10 contracts with fees x1.2 0.21; net per contract -21.50c at 1, -20.93c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 8 | 1 | 7 | -167.4c | -167.4c | 0.21 |

### GEN4_B08

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.24 n 52; validation PF1 1.99 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 24 on 2 days; zero-volume trades 0.
PF at 1 contract 0.63, at 10 contracts 0.67, at 10 contracts with fees x1.2 0.66; net per contract -9.76c at 1, -8.76c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -65.0c | -65.0c | 0.81 |
| 2026-10-31 | 8 | 4 | 4 | -145.2c | -210.2c | 0.67 |

### GEN4_B09

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= -0.06831; bought at that ask; held to settlement. Discovery PF1 1.51 n 49; validation PF1 1.94 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 24 on 2 days; zero-volume trades 0.
PF at 1 contract 0.28, at 10 contracts 0.29, at 10 contracts with fees x1.2 0.28; net per contract -20.17c at 1, -19.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -122.4c | -122.4c | 0.55 |
| 2026-10-31 | 11 | 1 | 10 | -350.5c | -472.9c | 0.29 |

### GEN4_B10

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 <= 2.256 and sp5 <= 0.353; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.79 n 46; validation PF1 1.93 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 22 on 2 days; zero-volume trades 0.
PF at 1 contract 0.66, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -7.98c at 1, -6.84c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 10 | 4 | -57.6c | -57.6c | 0.80 |
| 2026-10-31 | 8 | 4 | 4 | -92.9c | -150.5c | 0.70 |

### GEN4_B11

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp30 >= 0.5295; bought at that ask; held to settlement. Discovery PF1 1.50 n 46; validation PF1 1.91 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 25 on 2 days; zero-volume trades 0.
PF at 1 contract 0.39, at 10 contracts 0.40, at 10 contracts with fees x1.2 0.40; net per contract -10.69c at 1, -10.22c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 4 | 13 | -83.1c | -83.1c | 0.60 |
| 2026-10-31 | 8 | 1 | 7 | -172.4c | -255.5c | 0.40 |

### GEN4_B12

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.16 and lsz_ask <= 7.779 and sp5 >= 0.1732; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.32 n 43; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 21 on 2 days; zero-volume trades 0.
PF at 1 contract 1.95, at 10 contracts 2.07, at 10 contracts with fees x1.2 2.04; net per contract +11.97c at 1, +13.17c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 11 | 1 | +258.6c | +258.6c | 4.18 |
| 2026-10-31 | 9 | 6 | 3 | +18.0c | +276.6c | 2.07 |

### GEN4_B13

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.65 n 56; validation PF1 1.90 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 28 on 2 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.84; net per contract -4.22c at 1, -3.04c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.8c | -12.8c | 0.96 |
| 2026-10-31 | 9 | 5 | 4 | -72.4c | -85.2c | 0.85 |

### GEN4_B14

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and lsz_ask <= 7.779; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.30 n 44; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 20 on 2 days; zero-volume trades 0.
PF at 1 contract 1.02, at 10 contracts 1.08, at 10 contracts with fees x1.2 1.07; net per contract +0.32c at 1, +1.58c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 10 | 2 | +136.8c | +136.8c | 1.99 |
| 2026-10-31 | 8 | 4 | 4 | -105.1c | +31.7c | 1.08 |

### GEN4_B15

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26 and sp15 >= -0.01237 and spread >= 0.001; bought at that ask; held to settlement. Discovery PF1 1.55 n 42; validation PF1 1.86 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 19 on 2 days; zero-volume trades 0.
PF at 1 contract 0.20, at 10 contracts 0.20, at 10 contracts with fees x1.2 0.20; net per contract -28.89c at 1, -28.48c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 4 | 7 | -206.0c | -206.0c | 0.31 |
| 2026-10-31 | 8 | 1 | 7 | -335.2c | -541.2c | 0.20 |

### GEN4_B16

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and spread <= 0.01; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.14 n 48; validation PF1 1.83 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 23 on 2 days; zero-volume trades 0.
PF at 1 contract 0.96, at 10 contracts 1.02, at 10 contracts with fees x1.2 1.01; net per contract -0.78c at 1, +0.48c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +100.3c | +100.3c | 1.46 |
| 2026-10-31 | 9 | 5 | 4 | -89.3c | +11.0c | 1.02 |

### GEN4_B17

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.4847 and zd >= -2.066; bought at that ask; held to settlement. Discovery PF1 1.52 n 48; validation PF1 1.82 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 23 on 2 days; zero-volume trades 0.
PF at 1 contract 0.65, at 10 contracts 0.66, at 10 contracts with fees x1.2 0.65; net per contract -9.00c at 1, -8.57c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 13 | 4 | +24.0c | +24.0c | 1.08 |
| 2026-10-31 | 6 | 2 | 4 | -221.1c | -197.1c | 0.66 |

### GEN4_B18

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and lsz_ask <= 7.779 and zd >= -0.6765; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.63 n 43; validation PF1 1.81 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 20 on 2 days; zero-volume trades 0.
PF at 1 contract 0.89, at 10 contracts 0.94, at 10 contracts with fees x1.2 0.93; net per contract -2.24c at 1, -1.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 9 | 3 | +57.1c | +57.1c | 1.28 |
| 2026-10-31 | 8 | 4 | 4 | -79.9c | -22.8c | 0.94 |

### GEN4_B19

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and imb >= -0.6701; bought at that ask; held to settlement. Discovery PF1 1.78 n 48; validation PF1 1.81 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 25 on 2 days; zero-volume trades 0.
PF at 1 contract 0.68, at 10 contracts 0.69, at 10 contracts with fees x1.2 0.68; net per contract -8.28c at 1, -7.89c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -52.6c | -52.6c | 0.85 |
| 2026-10-31 | 8 | 4 | 4 | -144.6c | -197.2c | 0.69 |

### GEN4_B20

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and imb >= -0.4281 and sp5 <= 0; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.66 n 43; validation PF1 1.77 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 20 on 2 days; zero-volume trades 0.
PF at 1 contract 0.73, at 10 contracts 0.77, at 10 contracts with fees x1.2 0.76; net per contract -6.53c at 1, -5.44c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -55.9c | -55.9c | 0.80 |
| 2026-10-31 | 7 | 4 | 3 | -52.9c | -108.8c | 0.77 |

### GEN4_B21

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.902 and lsz_bid >= 7.292; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.54 n 44; validation PF1 1.76 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 2 days; zero-volume trades 0.
PF at 1 contract 0.48, at 10 contracts 0.51, at 10 contracts with fees x1.2 0.51; net per contract -14.46c at 1, -13.52c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 9 | 5 | -132.3c | -132.3c | 0.62 |
| 2026-10-31 | 1 | 0 | 1 | -70.5c | -202.8c | 0.51 |

### GEN4_B22

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.456 and lsz_bid >= 6.195; bought at that ask; held to settlement. Discovery PF1 1.63 n 49; validation PF1 1.73 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 25 on 2 days; zero-volume trades 0.
PF at 1 contract 0.90, at 10 contracts 0.91, at 10 contracts with fees x1.2 0.90; net per contract -2.28c at 1, -1.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -44.0c | -44.0c | 0.87 |
| 2026-10-31 | 8 | 5 | 3 | -3.5c | -47.5c | 0.91 |

### GEN4_B23

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; held to settlement. Discovery PF1 1.55 n 40; validation PF1 1.71 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 2 days; zero-volume trades 0.
PF at 1 contract 0.49, at 10 contracts 0.50, at 10 contracts with fees x1.2 0.49; net per contract -17.75c at 1, -17.33c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.6c | +24.6c | inf |
| 2026-10-31 | 7 | 3 | 4 | -163.2c | -138.6c | 0.50 |

### GEN4_B24

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.292; bought at that ask; held to settlement. Discovery PF1 2.01 n 50; validation PF1 1.65 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 21 on 2 days; zero-volume trades 0.
PF at 1 contract 0.81, at 10 contracts 0.82, at 10 contracts with fees x1.2 0.81; net per contract -4.52c at 1, -4.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -54.9c | -54.9c | 0.84 |
| 2026-10-31 | 5 | 3 | 2 | -32.0c | -86.9c | 0.82 |

### GEN4_B25

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.00 n 40; validation PF1 1.64 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 17 on 2 days; zero-volume trades 0.
PF at 1 contract 0.52, at 10 contracts 0.54, at 10 contracts with fees x1.2 0.54; net per contract -16.04c at 1, -15.06c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 6 | 4 | -85.4c | -85.4c | 0.71 |
| 2026-10-31 | 7 | 3 | 4 | -170.7c | -256.1c | 0.54 |

### GEN4_B26

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and lsz_bid >= 5.465; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.57 n 49; validation PF1 1.63 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 26 on 2 days; zero-volume trades 0.
PF at 1 contract 0.67, at 10 contracts 0.71, at 10 contracts with fees x1.2 0.70; net per contract -8.05c at 1, -7.02c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -37.3c | -37.3c | 0.89 |
| 2026-10-31 | 8 | 4 | 4 | -145.2c | -182.5c | 0.71 |

### GEN4_B27

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.52 n 40; validation PF1 1.63 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 2 days; zero-volume trades 0.
PF at 1 contract 0.47, at 10 contracts 0.50, at 10 contracts with fees x1.2 0.49; net per contract -18.39c at 1, -17.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 7 | 3 | 4 | -163.6c | -139.2c | 0.50 |

### GEN4_B28

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and lsz_ask <= 7.388; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.92 n 40; validation PF1 1.61 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 17 on 2 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.83, at 10 contracts with fees x1.2 0.82; net per contract -4.99c at 1, -3.94c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 7 | 2 | +57.7c | +57.7c | 1.46 |
| 2026-10-31 | 8 | 4 | 4 | -124.6c | -66.9c | 0.83 |

### GEN4_B29

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.1233; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.26 n 51; validation PF1 1.61 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 23 on 2 days; zero-volume trades 0.
PF at 1 contract 0.92, at 10 contracts 0.98, at 10 contracts with fees x1.2 0.97; net per contract -1.65c at 1, -0.42c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +106.3c | +106.3c | 1.48 |
| 2026-10-31 | 8 | 4 | 4 | -115.9c | -9.6c | 0.98 |

### GEN4_B30

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask >= 7.388 and sp15 >= -0.9017 and sp30 <= 2.256; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 45; validation PF1 1.61 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 19 on 2 days; zero-volume trades 0.
PF at 1 contract 0.61, at 10 contracts 0.64, at 10 contracts with fees x1.2 0.63; net per contract -9.99c at 1, -8.98c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -46.3c | -46.3c | 0.83 |
| 2026-10-31 | 6 | 3 | 3 | -124.3c | -170.6c | 0.64 |

### GEN4_B31

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid <= 8.422; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.71 n 55; validation PF1 1.59 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 28 on 2 days; zero-volume trades 0.
PF at 1 contract 0.84, at 10 contracts 0.90, at 10 contracts with fees x1.2 0.88; net per contract -3.28c at 1, -2.15c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 15 | 4 | +69.2c | +69.2c | 1.24 |
| 2026-10-31 | 9 | 5 | 4 | -129.4c | -60.2c | 0.90 |

### GEN4_B32

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.95 n 40; validation PF1 1.57 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 19 on 2 days; zero-volume trades 0.
PF at 1 contract 0.87, at 10 contracts 0.92, at 10 contracts with fees x1.2 0.91; net per contract -2.85c at 1, -1.72c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +24.3c | +24.3c | 1.11 |
| 2026-10-31 | 9 | 5 | 4 | -56.9c | -32.6c | 0.92 |

### GEN4_B33

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and spread >= 0.001 and vol <= 0.311; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.59 n 40; validation PF1 1.54 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 2 days; zero-volume trades 0.
PF at 1 contract 0.54, at 10 contracts 0.57, at 10 contracts with fees x1.2 0.56; net per contract -13.84c at 1, -12.64c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 7 | 3 | 4 | -125.5c | -101.1c | 0.57 |

### GEN4_B34

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 6.824 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.83 n 52; validation PF1 1.54 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 25 on 2 days; zero-volume trades 0.
PF at 1 contract 0.85, at 10 contracts 0.87, at 10 contracts with fees x1.2 0.86; net per contract -3.24c at 1, -2.87c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -28.0c | -28.0c | 0.92 |
| 2026-10-31 | 7 | 4 | 3 | -43.8c | -71.8c | 0.87 |

### GEN4_B35

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and sp15 >= 1.584 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 2.38 n 41; validation PF1 1.52 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 23 on 2 days; zero-volume trades 0.
PF at 1 contract 1.64, at 10 contracts 1.70, at 10 contracts with fees x1.2 1.68; net per contract +7.82c at 1, +8.32c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | +180.7c | +180.7c | 1.87 |
| 2026-10-31 | 3 | 1 | 2 | +10.7c | +191.4c | 1.70 |

### GEN4_B36

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.83 n 40; validation PF1 1.52 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 19 on 2 days; zero-volume trades 0.
PF at 1 contract 0.84, at 10 contracts 0.89, at 10 contracts with fees x1.2 0.87; net per contract -3.87c at 1, -2.64c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +25.7c | +25.7c | 1.12 |
| 2026-10-31 | 9 | 5 | 4 | -75.8c | -50.1c | 0.89 |

### GEN4_B37

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm30 <= 0.17 and sp5 >= 0.353 and spread >= 0.001; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.52 n 43; validation PF1 1.49 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 23 on 2 days; zero-volume trades 0.
PF at 1 contract 0.38, at 10 contracts 0.41, at 10 contracts with fees x1.2 0.40; net per contract -11.54c at 1, -10.62c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 3 | 11 | -119.8c | -119.8c | 0.54 |
| 2026-10-31 | 9 | 1 | 8 | -124.4c | -244.2c | 0.41 |

### GEN4_B38

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 <= 0.0315; bought at that ask; held to settlement. Discovery PF1 1.50 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 24 on 2 days; zero-volume trades 0.
PF at 1 contract 0.62, at 10 contracts 0.63, at 10 contracts with fees x1.2 0.62; net per contract -10.54c at 1, -10.09c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -112.6c | -112.6c | 0.69 |
| 2026-10-31 | 9 | 5 | 4 | -129.6c | -242.2c | 0.63 |

### GEN4_B39

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.01237; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.44 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 24 on 2 days; zero-volume trades 0.
PF at 1 contract 0.96, at 10 contracts 1.01, at 10 contracts with fees x1.2 1.00; net per contract -0.85c at 1, +0.21c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +168.7c | +168.7c | 1.84 |
| 2026-10-31 | 7 | 3 | 4 | -163.7c | +5.0c | 1.01 |

### GEN4_B40

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.9734; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.57 n 55; validation PF1 1.44 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 28 on 2 days; zero-volume trades 0.
PF at 1 contract 0.77, at 10 contracts 0.83, at 10 contracts with fees x1.2 0.81; net per contract -4.95c at 1, -3.71c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.7c | -12.7c | 0.96 |
| 2026-10-31 | 9 | 5 | 4 | -91.3c | -104.0c | 0.83 |

### GEN4_B41

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.733 and spread >= 0.01; bought at that ask; held to settlement. Discovery PF1 1.52 n 43; validation PF1 1.43 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 18 on 2 days; zero-volume trades 0.
PF at 1 contract 1.10, at 10 contracts 1.12, at 10 contracts with fees x1.2 1.10; net per contract +1.78c at 1, +2.17c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +85.5c | +85.5c | 1.46 |
| 2026-10-31 | 5 | 3 | 2 | -46.5c | +39.0c | 1.12 |

### GEN4_B42

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= -0.07 and imb >= -0.9734 and sp15 >= 1.584; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.23 n 41; validation PF1 1.42 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 24 on 2 days; zero-volume trades 0.
PF at 1 contract 1.54, at 10 contracts 1.63, at 10 contracts with fees x1.2 1.60; net per contract +6.45c at 1, +7.21c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 21 | 5 | 16 | +163.0c | +163.0c | 1.77 |
| 2026-10-31 | 3 | 1 | 2 | +10.0c | +173.0c | 1.63 |

### GEN4_B43

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.75 n 48; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 24 on 2 days; zero-volume trades 0.
PF at 1 contract 0.76, at 10 contracts 0.80, at 10 contracts with fees x1.2 0.79; net per contract -5.93c at 1, -4.87c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +11.5c | +11.5c | 1.04 |
| 2026-10-31 | 9 | 5 | 4 | -128.4c | -116.9c | 0.80 |

### GEN4_B44

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 >= 0.353; bought at that ask; held to settlement. Discovery PF1 2.35 n 51; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 23 on 2 days; zero-volume trades 0.
PF at 1 contract 2.85, at 10 contracts 2.91, at 10 contracts with fees x1.2 2.87; net per contract +16.74c at 1, +17.12c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 14 | 2 | +262.6c | +262.6c | 3.00 |
| 2026-10-31 | 7 | 6 | 1 | +131.2c | +393.8c | 2.91 |

### GEN4_B45

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and lsz_bid >= 6.824; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.02 n 47; validation PF1 1.37 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 23 on 2 days; zero-volume trades 0.
PF at 1 contract 0.85, at 10 contracts 0.90, at 10 contracts with fees x1.2 0.89; net per contract -3.24c at 1, -2.08c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -54.8c | -54.8c | 0.84 |
| 2026-10-31 | 6 | 4 | 2 | +7.0c | -47.8c | 0.90 |

### GEN4_B46

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.11 and lsz_ask <= 7.388; bought at that ask; held to settlement. Discovery PF1 2.64 n 45; validation PF1 1.34 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 21 on 2 days; zero-volume trades 0.
PF at 1 contract 1.09, at 10 contracts 1.11, at 10 contracts with fees x1.2 1.10; net per contract +1.81c at 1, +2.25c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 11 | 2 | +192.8c | +192.8c | 2.40 |
| 2026-10-31 | 8 | 4 | 4 | -145.5c | +47.3c | 1.11 |

### GEN4_B47

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; held to settlement. Discovery PF1 1.79 n 48; validation PF1 1.33 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 24 on 2 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.80, at 10 contracts with fees x1.2 0.79; net per contract -5.17c at 1, -4.75c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +13.7c | +13.7c | 1.05 |
| 2026-10-31 | 9 | 5 | 4 | -127.6c | -113.9c | 0.80 |

### GEN4_B48

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm15 >= -0.09 and sp30 >= -2.625; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.70 n 41; validation PF1 1.33 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 18 on 2 days; zero-volume trades 0.
PF at 1 contract 0.62, at 10 contracts 0.66, at 10 contracts with fees x1.2 0.65; net per contract -10.93c at 1, -9.87c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 8 | 3 | +12.6c | +12.6c | 1.05 |
| 2026-10-31 | 7 | 3 | 4 | -190.2c | -177.6c | 0.66 |

### GEN4_B49

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; held to settlement. Discovery PF1 2.47 n 55; validation PF1 1.33 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 24 on 2 days; zero-volume trades 0.
PF at 1 contract 1.01, at 10 contracts 1.03, at 10 contracts with fees x1.2 1.02; net per contract +0.21c at 1, +0.58c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +177.3c | +177.3c | 1.91 |
| 2026-10-31 | 7 | 3 | 4 | -163.3c | +14.0c | 1.03 |

### GEN4_B50

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp15 >= -0.1949 and zd >= -1.214; bought at that ask; held to settlement. Discovery PF1 1.87 n 41; validation PF1 1.31 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 20 on 2 days; zero-volume trades 0.
PF at 1 contract 0.98, at 10 contracts 1.00, at 10 contracts with fees x1.2 0.99; net per contract -0.40c at 1, -0.02c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +88.5c | +88.5c | 1.45 |
| 2026-10-31 | 6 | 3 | 3 | -88.8c | -0.3c | 1.00 |

### GEN4_B51

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0.04 and imb <= 0.4847; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.72 n 50; validation PF1 1.30 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 23 on 2 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.84; net per contract -4.40c at 1, -3.30c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +75.9c | +75.9c | 1.33 |
| 2026-10-31 | 8 | 4 | 4 | -151.9c | -76.0c | 0.85 |

### GEN4_REF_FAV150

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. The unconditional core of 41 of the 51 GEN4 validation passes: buy the favourite (side ask 0.50 to 0.85) at the first poll 150 to 120 s before the close, hold. Discovery PF1 1.61 n 50; validation PF1 1.57 n 35. Shows whether the conditions add anything forward.
Windows evaluated 85 on 2 days; without the data the rule needs 0; evaluator errors 0. Trades 26 on 2 days; zero-volume trades 0.
PF at 1 contract 0.70, at 10 contracts 0.72, at 10 contracts with fees x1.2 0.71; net per contract -7.38c at 1, -6.97c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -34.7c | -34.7c | 0.90 |
| 2026-10-31 | 8 | 4 | 4 | -146.5c | -181.2c | 0.72 |

### REF_L1_GOLD

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T00:00:00Z. The live L1 gold rule as a known baseline: the side whose ask is 0.88 to 0.97 at the candle ending 6 minutes before the close, bought at that ask, held to settlement. Candles only, so it ignores the live 25c exit and the window limit.
Windows evaluated 84 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 1 days; zero-volume trades 0.
PF at 1 contract 0.95, at 10 contracts 1.03, at 10 contracts with fees x1.2 1.01; net per contract -0.31c at 1, +0.17c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 14 | 1 | +2.5c | +2.5c | 1.03 |

