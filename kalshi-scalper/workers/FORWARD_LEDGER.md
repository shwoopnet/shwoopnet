# FORWARD LEDGER (automatic; research only)

Written by `python -m scalper.fwdledger run` (once per AUTO pass, `scalper.autoscore check`). Last updated 2026-11-02 15:12 UTC.
Forward evidence counts only windows that CLOSED after a candidate's freeze time, had the data its rule needs and have settled.
Fees 7% x C x p x (1-p) rounded up to the cent per order, at 1 and 10 contracts; held to settlement pays the entry fee only. Win = net at 10 contracts above zero. Net per contract is at 10 contracts. Trades per week: forward trades over the time from the freeze to the last evaluated close.
This ledger never promotes anything. READY FOR THE FALSIFIER means only: forward PF 1.5+ at 1 and at 10 contracts on 30+ trades over 10+ trade days. It earns a falsifier read, nothing more. How a generator adds a candidate: `workers/candidates/README.md`.

| id | market | stage | freeze | fwd days | trades | wins | losses | PF 1c | PF 10c | net/contract | trades/week | updated | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| REF_GEN6_OIREL | KXBTC15M | reference | 2026-10-30 | 4 | 12 | 2 | 10 | 1.14 | 1.19 | +2.27c | 28.3 | 2026-11-02 15:12 UTC |  |
| LADFADE_BTC | KXBTC15M | validation | 2026-10-30 | 4 | 20 | 4 | 16 | 0.33 | 0.34 | -22.37c | 45.3 | 2026-11-02 15:12 UTC |  |
| REF_GEN6_OICORE | KXBTC15M | reference | 2026-10-30 | 4 | 17 | 5 | 12 | 2.10 | 2.20 | +11.90c | 34.3 | 2026-11-02 15:12 UTC |  |
| GEN6_B01 | KXBTC15M | validation | 2026-10-30 | 4 | 5 | 3 | 2 | 4.96 | 5.20 | +32.00c | 10.0 | 2026-11-02 15:12 UTC |  |
| GEN6_B02 | KXBTC15M | validation | 2026-10-30 | 4 | 3 | 0 | 3 | 0.00 | 0.00 | -1.47c | 6.0 | 2026-11-02 15:12 UTC |  |
| GEN6_B03 | KXBTC15M | validation | 2026-10-30 | 4 | 17 | 6 | 11 | 2.27 | 2.45 | +11.44c | 33.9 | 2026-11-02 15:12 UTC |  |
| GEN6_B04 | KXBTC15M | validation | 2026-10-30 | 4 | 14 | 4 | 10 | 1.56 | 1.66 | +6.13c | 27.9 | 2026-11-02 15:12 UTC |  |
| GEN6_B05 | KXBTC15M | validation | 2026-10-30 | 4 | 11 | 1 | 10 | 0.02 | 0.03 | -14.90c | 21.9 | 2026-11-02 15:12 UTC |  |
| GEN6_B06 | KXBTC15M | validation | 2026-10-30 | 4 | 7 | 3 | 4 | 3.86 | 4.13 | +21.44c | 14.0 | 2026-11-02 15:12 UTC |  |
| GEN6_B07 | KXBTC15M | validation | 2026-10-30 | 4 | 12 | 3 | 9 | 0.79 | 0.83 | -1.93c | 23.9 | 2026-11-02 15:12 UTC |  |
| GEN6_B08 | KXBTC15M | validation | 2026-10-30 | 4 | 15 | 2 | 13 | 0.57 | 0.60 | -5.27c | 29.9 | 2026-11-02 15:12 UTC |  |
| GEN6_B09 | KXBTC15M | validation | 2026-10-30 | 4 | 12 | 4 | 8 | 0.74 | 0.83 | -1.69c | 23.9 | 2026-11-02 15:12 UTC |  |
| GEN6_B10 | KXBTC15M | validation | 2026-10-30 | 4 | 34 | 6 | 28 | 1.19 | 1.25 | +2.70c | 67.8 | 2026-11-02 15:12 UTC |  |
| GEN6_B11 | KXBTC15M | validation | 2026-10-30 | 4 | 11 | 2 | 9 | 3.21 | 3.94 | +8.35c | 21.9 | 2026-11-02 15:12 UTC |  |
| GEN6_B12 | KXBTC15M | validation | 2026-10-30 | 4 | 6 | 1 | 5 | 0.56 | 0.58 | -6.80c | 12.0 | 2026-11-02 15:12 UTC |  |
| GEN6_B13 | KXBTC15M | validation | 2026-10-30 | 4 | 8 | 4 | 4 | 1.54 | 1.64 | +5.40c | 16.0 | 2026-11-02 15:12 UTC |  |
| REF_BTC_UNDERDOG_180 | KXBTC15M | reference | 2026-10-30 | 4 | 98 | 39 | 59 | 1.31 | 1.33 | +6.23c | 195.4 | 2026-11-02 15:12 UTC |  |
| GEN7_B01 | KXBTC15M | validation | 2026-10-30 | 4 | 7 | 2 | 5 | 2.67 | 3.21 | +8.84c | 13.8 | 2026-11-02 15:12 UTC |  |
| GEN7_B02 | KXBTC15M | validation | 2026-10-30 | 4 | 12 | 4 | 8 | 0.93 | 1.01 | +0.14c | 23.6 | 2026-11-02 15:12 UTC |  |
| REF_GEN6_OIDRIFT | KXBTC15M | reference | 2026-10-30 | 4 | 1 | 0 | 1 | 0.00 | 0.00 | -43.80c | 2.0 | 2026-11-02 15:12 UTC |  |
| REF_GOLD_UNDERDOG_180 | KXGOLD15M | reference | 2026-10-30 | 3 | 47 | 11 | 36 | 0.64 | 0.65 | -8.29c | 92.6 | 2026-11-02 15:12 UTC |  |
| REF_LATECAL_BTC | KXBTC15M | reference | 2026-10-30 | 4 | 21 | 20 | 1 | 0.53 | 0.68 | -1.45c | 41.4 | 2026-11-02 15:12 UTC |  |
| GEN4_B01 | KXBTC15M | validation | 2026-10-30 | 4 | 71 | 46 | 25 | 0.76 | 0.81 | -4.16c | 142.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B02 | KXBTC15M | validation | 2026-10-30 | 4 | 68 | 44 | 24 | 0.79 | 0.84 | -3.31c | 136.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B03 | KXBTC15M | validation | 2026-10-30 | 4 | 63 | 32 | 31 | 0.96 | 1.01 | +0.18c | 126.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B04 | KXBTC15M | validation | 2026-10-30 | 4 | 75 | 51 | 24 | 0.82 | 0.84 | -3.50c | 150.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B05 | KXBTC15M | validation | 2026-10-30 | 4 | 58 | 26 | 32 | 1.36 | 1.43 | +5.71c | 116.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B06 | KXBTC15M | validation | 2026-10-30 | 4 | 72 | 29 | 43 | 1.16 | 1.19 | +2.74c | 144.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B07 | KXBTC15M | validation | 2026-10-30 | 4 | 46 | 18 | 28 | 0.96 | 1.01 | +0.09c | 92.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B08 | KXBTC15M | validation | 2026-10-30 | 4 | 74 | 49 | 25 | 0.76 | 0.81 | -4.35c | 148.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B09 | KXBTC15M | validation | 2026-10-30 | 4 | 74 | 30 | 44 | 0.94 | 0.97 | -0.61c | 148.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B10 | KXBTC15M | validation | 2026-10-30 | 4 | 66 | 42 | 24 | 0.70 | 0.75 | -5.42c | 132.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B11 | KXBTC15M | validation | 2026-10-30 | 4 | 63 | 25 | 38 | 1.10 | 1.14 | +1.92c | 126.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B12 | KXBTC15M | validation | 2026-10-30 | 4 | 70 | 49 | 21 | 0.94 | 1.00 | -0.03c | 140.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B13 | KXBTC15M | validation | 2026-10-30 | 4 | 81 | 51 | 30 | 0.66 | 0.70 | -6.72c | 162.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B14 | KXBTC15M | validation | 2026-10-30 | 4 | 64 | 45 | 19 | 0.99 | 1.05 | +1.00c | 128.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B15 | KXBTC15M | validation | 2026-10-30 | 4 | 62 | 31 | 31 | 0.70 | 0.71 | -6.64c | 124.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B16 | KXBTC15M | validation | 2026-10-30 | 4 | 74 | 49 | 25 | 0.77 | 0.82 | -4.14c | 148.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B17 | KXBTC15M | validation | 2026-10-30 | 4 | 63 | 41 | 22 | 0.70 | 0.71 | -6.83c | 126.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B18 | KXBTC15M | validation | 2026-10-30 | 4 | 68 | 45 | 23 | 0.83 | 0.88 | -2.38c | 136.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B19 | KXBTC15M | validation | 2026-10-30 | 4 | 67 | 44 | 23 | 0.78 | 0.80 | -4.66c | 134.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B20 | KXBTC15M | validation | 2026-10-30 | 4 | 57 | 37 | 20 | 0.77 | 0.82 | -3.75c | 114.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B21 | KXBTC15M | validation | 2026-10-30 | 4 | 34 | 22 | 12 | 0.64 | 0.69 | -7.30c | 68.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B22 | KXBTC15M | validation | 2026-10-30 | 4 | 74 | 46 | 28 | 0.65 | 0.67 | -8.32c | 148.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B23 | KXBTC15M | validation | 2026-10-30 | 4 | 53 | 35 | 18 | 0.75 | 0.77 | -5.21c | 106.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B24 | KXBTC15M | validation | 2026-10-30 | 4 | 53 | 32 | 21 | 0.60 | 0.61 | -9.98c | 106.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B25 | KXBTC15M | validation | 2026-10-30 | 4 | 60 | 40 | 20 | 0.75 | 0.80 | -4.76c | 120.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B26 | KXBTC15M | validation | 2026-10-30 | 4 | 69 | 43 | 26 | 0.60 | 0.64 | -9.07c | 138.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B27 | KXBTC15M | validation | 2026-10-30 | 4 | 53 | 35 | 18 | 0.72 | 0.77 | -5.38c | 106.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B28 | KXBTC15M | validation | 2026-10-30 | 4 | 62 | 43 | 19 | 0.89 | 0.95 | -1.07c | 124.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B29 | KXBTC15M | validation | 2026-10-30 | 4 | 72 | 50 | 22 | 0.90 | 0.96 | -0.70c | 144.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B30 | KXBTC15M | validation | 2026-10-30 | 4 | 53 | 35 | 18 | 0.65 | 0.70 | -6.99c | 106.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B31 | KXBTC15M | validation | 2026-10-30 | 4 | 81 | 55 | 26 | 0.78 | 0.83 | -3.76c | 162.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B32 | KXBTC15M | validation | 2026-10-30 | 4 | 62 | 41 | 21 | 0.80 | 0.85 | -3.13c | 124.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B33 | KXBTC15M | validation | 2026-10-30 | 4 | 53 | 35 | 18 | 0.73 | 0.78 | -4.79c | 106.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B34 | KXBTC15M | validation | 2026-10-30 | 4 | 70 | 43 | 27 | 0.63 | 0.65 | -8.89c | 140.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B35 | KXBTC15M | validation | 2026-10-30 | 4 | 49 | 15 | 34 | 1.84 | 1.90 | +10.89c | 98.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B36 | KXBTC15M | validation | 2026-10-30 | 4 | 62 | 42 | 20 | 0.81 | 0.87 | -2.81c | 124.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B37 | KXBTC15M | validation | 2026-10-30 | 4 | 65 | 27 | 38 | 1.26 | 1.34 | +4.41c | 130.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B38 | KXBTC15M | validation | 2026-10-30 | 4 | 75 | 47 | 28 | 0.65 | 0.66 | -8.69c | 150.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B39 | KXBTC15M | validation | 2026-10-30 | 4 | 73 | 50 | 23 | 0.87 | 0.93 | -1.51c | 146.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B40 | KXBTC15M | validation | 2026-10-30 | 4 | 81 | 52 | 29 | 0.67 | 0.72 | -6.68c | 162.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B41 | KXBTC15M | validation | 2026-10-30 | 4 | 44 | 29 | 15 | 0.76 | 0.77 | -5.02c | 88.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B42 | KXBTC15M | validation | 2026-10-30 | 4 | 51 | 16 | 35 | 1.90 | 2.01 | +11.76c | 102.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B43 | KXBTC15M | validation | 2026-10-30 | 4 | 77 | 49 | 28 | 0.66 | 0.71 | -7.24c | 154.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B44 | KXBTC15M | validation | 2026-10-30 | 4 | 72 | 50 | 22 | 0.94 | 0.96 | -0.73c | 144.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B45 | KXBTC15M | validation | 2026-10-30 | 4 | 58 | 38 | 20 | 0.74 | 0.79 | -4.58c | 116.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B46 | KXBTC15M | validation | 2026-10-30 | 4 | 71 | 50 | 21 | 0.96 | 0.99 | -0.28c | 142.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B47 | KXBTC15M | validation | 2026-10-30 | 4 | 76 | 49 | 27 | 0.73 | 0.74 | -6.10c | 152.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B48 | KXBTC15M | validation | 2026-10-30 | 4 | 62 | 40 | 22 | 0.62 | 0.66 | -8.75c | 124.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B49 | KXBTC15M | validation | 2026-10-30 | 4 | 73 | 50 | 23 | 0.91 | 0.93 | -1.36c | 146.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B50 | KXBTC15M | validation | 2026-10-30 | 4 | 58 | 40 | 18 | 0.94 | 0.96 | -0.76c | 116.0 | 2026-11-02 15:12 UTC |  |
| GEN4_B51 | KXBTC15M | validation | 2026-10-30 | 4 | 70 | 47 | 23 | 0.76 | 0.80 | -4.36c | 140.0 | 2026-11-02 15:12 UTC |  |
| GEN4_REF_FAV150 | KXBTC15M | reference | 2026-10-30 | 4 | 71 | 46 | 25 | 0.72 | 0.74 | -6.12c | 142.0 | 2026-11-02 15:12 UTC |  |
| REF_L1_GOLD | KXGOLD15M | reference | 2026-10-30 | 3 | 31 | 30 | 1 | 2.10 | 2.26 | +3.69c | 60.4 | 2026-11-02 15:12 UTC |  |

## History per candidate

### REF_GEN6_OIREL

Evaluator `scalper.oirel:forward_eval`, source `candles`, frozen 2026-10-30T15:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) when open interest over the 3 minutes before rose by more than 26.76% of its level at 360 s (the discovery quantile matched to the core's 86,300 count), fill at the next candle's ask, held. History: discovery n 298 PF 1.73, validation n 286 PF 1.71 at 10 contracts (FALS5 check 2, one try). Not independent of REF_GEN6_OICORE (59% to 80% shared trades). workers/FALS5_REGISTRATION.md, workers/FALS5_RESULT.md.
Windows evaluated 285 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 4 days; zero-volume trades 0.
PF at 1 contract 1.14, at 10 contracts 1.19, at 10 contracts with fees x1.2 1.18; net per contract +1.70c at 1, +2.27c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -43.8c | -43.8c | 0.00 |
| 2026-10-31 | 3 | 1 | 2 | +61.6c | +17.8c | 1.29 |
| 2026-11-01 | 6 | 1 | 5 | +40.5c | +58.3c | 1.52 |
| 2026-11-02 | 2 | 0 | 2 | -31.1c | +27.2c | 1.19 |

### LADFADE_BTC

Evaluator `scalper.ladfade:forward_eval`, source `candles`, frozen 2026-10-30T12:00:00Z. Bitcoin 15 minute windows opening at :15 and :30: when the hourly KXBTCD ladder leans 5c+ from 50/50 at the first minute, buy the side the 15 minute book overshot AWAY from if its ask is 3c+ below the ladder's chance, at the next candle's ask (30c to 70c), held. Ladder from the book recorder. Discovery and validation spent (post hoc); holdout read once in workers/LADFADE_RESULT.md. 1 try; workers/LADFADE_REGISTRATION.md.
Windows evaluated 245 on 4 days; without the data the rule needs 52; evaluator errors 0. Trades 20 on 4 days; zero-volume trades 0.
PF at 1 contract 0.33, at 10 contracts 0.34, at 10 contracts with fees x1.2 0.33; net per contract -22.70c at 1, -22.37c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -44.8c | -44.8c | 0.00 |
| 2026-10-31 | 4 | 0 | 4 | -144.4c | -189.2c | 0.00 |
| 2026-11-01 | 10 | 3 | 7 | -113.7c | -302.9c | 0.36 |
| 2026-11-02 | 5 | 1 | 4 | -144.5c | -447.4c | 0.34 |

### REF_GEN6_OICORE

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T03:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest rose more than 86,300 contracts over the 3 minutes before, held to settlement, fill at the next candle's ask. History: discovery PF 2.28 (n 222), validation 1.85 (n 333, z 4.53). Forward days only; 1 try. Falsifier FALS4 running.
Windows evaluated 333 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 17 on 4 days; zero-volume trades 0.
PF at 1 contract 2.10, at 10 contracts 2.20, at 10 contracts with fees x1.2 2.18; net per contract +11.35c at 1, +11.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 7 | 3 | 4 | +177.6c | +133.3c | 2.36 |
| 2026-11-01 | 5 | 2 | 3 | +97.4c | +230.7c | 2.64 |
| 2026-11-02 | 3 | 0 | 3 | -28.4c | +202.3c | 2.20 |

### GEN6_B01

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | doi>8.63e+04 & m3>-0.25 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.81 (n 104), validation PF 1.90 (n 164), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 3 days; zero-volume trades 0.
PF at 1 contract 4.96, at 10 contracts 5.20, at 10 contracts with fees x1.2 5.13; net per contract +31.08c at 1, +32.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 3 | 2 | 1 | +77.5c | +77.5c | 3.24 |
| 2026-11-01 | 1 | 1 | 0 | +86.0c | +163.5c | 5.73 |
| 2026-11-02 | 1 | 0 | 1 | -3.5c | +160.0c | 5.20 |

### GEN6_B02

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | hour<=21 & xb_d2<=0.046 & doi>8.63e+04 | TP +8c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 2.42 (n 106), validation PF 1.80 (n 133), C=10.
Windows evaluated 240 on 4 days; without the data the rule needs 97; evaluator errors 0. Trades 3 on 2 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -2.60c at 1, -1.47c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |
| 2026-11-02 | 2 | 0 | 2 | -3.9c | -4.4c | 0.00 |

### GEN6_B03

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 | TP +5c stop -20c else hold]; fill at the next candle's ask. Discovery PF 2.41 (n 222), validation PF 1.73 (n 333), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 17 on 4 days; zero-volume trades 0.
PF at 1 contract 2.27, at 10 contracts 2.45, at 10 contracts with fees x1.2 2.41; net per contract +10.64c at 1, +11.44c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 7 | 3 | 4 | +130.6c | +86.3c | 1.88 |
| 2026-11-01 | 5 | 3 | 2 | +136.5c | +222.8c | 3.11 |
| 2026-11-02 | 3 | 0 | 3 | -28.3c | +194.5c | 2.45 |

### GEN6_B04

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 & xa_spr<=0.02 & rng5>0.14 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.06 (n 175), validation PF 1.68 (n 269), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 4 days; zero-volume trades 0.
PF at 1 contract 1.56, at 10 contracts 1.66, at 10 contracts with fees x1.2 1.63; net per contract +5.51c at 1, +6.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -44.3c | -44.3c | 0.00 |
| 2026-10-31 | 5 | 1 | 4 | +18.5c | -25.8c | 0.74 |
| 2026-11-01 | 5 | 3 | 2 | +136.5c | +110.7c | 2.05 |
| 2026-11-02 | 2 | 0 | 2 | -24.9c | +85.8c | 1.66 |

### GEN6_B05

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | d3<=-0.08 & m1<=0 & vol<=1.11e+05 | TP +20c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 1.60 (n 172), validation PF 1.66 (n 58), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 3 days; zero-volume trades 0.
PF at 1 contract 0.02, at 10 contracts 0.03, at 10 contracts with fees x1.2 0.02; net per contract -16.09c at 1, -14.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 5 | 1 | 4 | -30.2c | -30.2c | 0.12 |
| 2026-11-01 | 5 | 0 | 5 | -109.5c | -139.7c | 0.03 |
| 2026-11-02 | 1 | 0 | 1 | -24.2c | -163.9c | 0.03 |

### GEN6_B06

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | d1<=0.1 & doi>8.63e+04 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 3.51 (n 111), validation PF 1.57 (n 162), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 7 on 4 days; zero-volume trades 0.
PF at 1 contract 3.86, at 10 contracts 4.13, at 10 contracts with fees x1.2 4.07; net per contract +20.60c at 1, +21.44c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |
| 2026-10-31 | 4 | 2 | 2 | +68.1c | +67.6c | 2.52 |
| 2026-11-01 | 1 | 1 | 0 | +86.0c | +153.6c | 4.45 |
| 2026-11-02 | 1 | 0 | 1 | -3.5c | +150.1c | 4.13 |

### GEN6_B07

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 240..180s | m3>-0.08 & m5<=-0.24 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.72 (n 137), validation PF 1.45 (n 90), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 4 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.83, at 10 contracts with fees x1.2 0.82; net per contract -2.48c at 1, -1.93c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 1 | 1 | +20.1c | +20.1c | 3.64 |
| 2026-10-31 | 4 | 0 | 4 | -89.5c | -69.4c | 0.29 |
| 2026-11-01 | 5 | 1 | 4 | +41.4c | -28.0c | 0.80 |
| 2026-11-02 | 1 | 1 | 0 | +4.8c | -23.2c | 0.83 |

### GEN6_B08

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | rng5<=0.273 & doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.14 (n 205), validation PF 1.43 (n 316), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 15 on 4 days; zero-volume trades 0.
PF at 1 contract 0.57, at 10 contracts 0.60, at 10 contracts with fees x1.2 0.60; net per contract -5.89c at 1, -5.27c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -56.6c | -56.6c | 0.00 |
| 2026-10-31 | 7 | 2 | 5 | +48.3c | -8.3c | 0.94 |
| 2026-11-01 | 2 | 0 | 2 | -39.1c | -47.4c | 0.72 |
| 2026-11-02 | 3 | 0 | 3 | -31.7c | -79.1c | 0.60 |

### GEN6_B09

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | vol<=1.28e+05 & m1<=-0.0507 | TP +3c stop -20c else sell 60s]; fill at the next candle's ask. Discovery PF 1.55 (n 192), validation PF 1.42 (n 86), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 3 days; zero-volume trades 0.
PF at 1 contract 0.74, at 10 contracts 0.83, at 10 contracts with fees x1.2 0.81; net per contract -2.78c at 1, -1.69c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 6 | 2 | 4 | -2.2c | -2.2c | 0.94 |
| 2026-11-01 | 5 | 2 | 3 | +6.1c | +3.9c | 1.04 |
| 2026-11-02 | 1 | 0 | 1 | -24.2c | -20.3c | 0.83 |

### GEN6_B10

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.19 (n 433), validation PF 1.41 (n 587), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 34 on 4 days; zero-volume trades 0.
PF at 1 contract 1.19, at 10 contracts 1.25, at 10 contracts with fees x1.2 1.24; net per contract +2.12c at 1, +2.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 1 | 6 | -6.3c | -6.3c | 0.91 |
| 2026-10-31 | 11 | 3 | 8 | +112.2c | +105.9c | 1.64 |
| 2026-11-01 | 11 | 2 | 9 | +5.6c | +111.5c | 1.33 |
| 2026-11-02 | 5 | 0 | 5 | -19.7c | +91.8c | 1.25 |

### GEN6_B11

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | ask<=0.19 & xa_spr<=0.003 & d1<=-0.05 | TP +5c stop -5c else hold]; fill at the next candle's ask. Discovery PF 1.82 (n 110), validation PF 1.37 (n 93), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 4 days; zero-volume trades 0.
PF at 1 contract 3.21, at 10 contracts 3.94, at 10 contracts with fees x1.2 3.84; net per contract +7.64c at 1, +8.35c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +47.3c | +47.3c | 15.33 |
| 2026-10-31 | 5 | 1 | 4 | +53.2c | +100.5c | 5.47 |
| 2026-11-01 | 1 | 0 | 1 | -1.8c | +98.7c | 5.06 |
| 2026-11-02 | 2 | 0 | 2 | -6.9c | +91.8c | 3.94 |

### GEN6_B12

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | rng5>0.32 & hour>19 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.83 (n 102), validation PF 1.32 (n 72), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 3 days; zero-volume trades 0.
PF at 1 contract 0.56, at 10 contracts 0.58, at 10 contracts with fees x1.2 0.57; net per contract -7.27c at 1, -6.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | +5.4c | +5.4c | 1.11 |
| 2026-10-31 | 2 | 0 | 2 | -32.4c | -27.0c | 0.67 |
| 2026-11-01 | 1 | 0 | 1 | -13.8c | -40.8c | 0.58 |

### GEN6_B13

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | m1>-0.2 & hour>19 | TP +8c stop -20c else hold]; fill at the next candle's ask. Discovery PF 1.70 (n 173), validation PF 1.31 (n 129), C=10.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 3 days; zero-volume trades 0.
PF at 1 contract 1.54, at 10 contracts 1.64, at 10 contracts with fees x1.2 1.60; net per contract +4.71c at 1, +5.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 0 | 3 | -65.5c | -65.5c | 0.00 |
| 2026-10-31 | 3 | 3 | 0 | +49.0c | -16.5c | 0.75 |
| 2026-11-01 | 2 | 1 | 1 | +59.7c | +43.2c | 1.64 |

### REF_BTC_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T02:00:00Z. The mirror of FALS3's finding (Bitcoin favourites at 50c to 85c are overpriced 2 to 3 minutes before the close: PF 0.77 on 2,576 windows, z -4.97): buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held to settlement. History already read (UNDER1 found this side positive), so only forward days count; REV1 is the registered forward read of the related cheap-NO rule (2026-11-05). 1 try.
Windows evaluated 337 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 98 on 4 days; zero-volume trades 0.
PF at 1 contract 1.31, at 10 contracts 1.33, at 10 contracts with fees x1.2 1.31; net per contract +5.83c at 1, +6.23c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 25 | 6 | 19 | -206.1c | -206.1c | 0.65 |
| 2026-10-31 | 31 | 13 | 18 | +261.8c | +55.7c | 1.05 |
| 2026-11-01 | 24 | 10 | 14 | +194.0c | +249.7c | 1.16 |
| 2026-11-02 | 18 | 10 | 8 | +361.3c | +611.0c | 1.33 |

### GEN7_B01

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 240..240s | npv1>0.281 & vol>1.32e+05 | sell at 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 3.28 (n 101), validation PF 1.80 (n 126), C=10.
Windows evaluated 341 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 7 on 4 days; zero-volume trades 0.
PF at 1 contract 2.67, at 10 contracts 3.21, at 10 contracts with fees x1.2 3.13; net per contract +7.87c at 1, +8.84c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -12.8c | -12.8c | 0.00 |
| 2026-10-31 | 1 | 0 | 1 | -5.8c | -18.6c | 0.00 |
| 2026-11-01 | 4 | 2 | 2 | +85.2c | +66.6c | 3.86 |
| 2026-11-02 | 1 | 0 | 1 | -4.7c | +61.9c | 3.21 |

### GEN7_B02

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 300..240s | npv1>0.393 & doi5>9.78e+04 | TP +20c stop -20c else sell 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 1.75 (n 135), validation PF 1.71 (n 101), C=10.
Windows evaluated 341 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 3 days; zero-volume trades 0.
PF at 1 contract 0.93, at 10 contracts 1.01, at 10 contracts with fees x1.2 0.99; net per contract -0.95c at 1, +0.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 4 | 1 | 3 | -54.8c | -54.8c | 0.19 |
| 2026-11-01 | 7 | 3 | 4 | +86.4c | +31.6c | 1.25 |
| 2026-11-02 | 1 | 0 | 1 | -29.9c | +1.7c | 1.01 |

### REF_GEN6_OIDRIFT

Evaluator `scalper.oidrift:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest over the 3 minutes before rose above the 90th percentile of that change over the 30 UTC days before (earlier days only, 20+ days needed), fill at the next candle's ask, held. History validation n 67, PF 2.65 (FALS4 check 5, reproduced). Not independent of REF_GEN6_OICORE. 1 try; workers/OIDRIFT_REGISTRATION.md.
Windows evaluated 341 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -44.00c at 1, -43.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -43.8c | -43.8c | 0.00 |

### REF_GOLD_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. Gold version of REF_BTC_UNDERDOG_180: FALS3 found gold favourites at 50c to 85c, 2 to 3 minutes before the close, also below break-even (PF 0.85). Buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held. Forward days only. 1 try.
Windows evaluated 140 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 47 on 2 days; zero-volume trades 0.
PF at 1 contract 0.64, at 10 contracts 0.65, at 10 contracts with fees x1.2 0.64; net per contract -8.74c at 1, -8.29c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 31 | 7 | 24 | -282.0c | -282.0c | 0.61 |
| 2026-11-02 | 16 | 4 | 12 | -107.5c | -389.5c | 0.65 |

### REF_LATECAL_BTC

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. LATECAL's one chosen cell (Bitcoin, 90 to 60 s left, ask 0.95 to 0.98: 61 of 61 won on the recorder, NOT_ENOUGH_DATA; needs about 800 windows to clear the 97.7% break-even) tracked forward. Candles only: the nearest candle is the one ending 60 s before the close, so this approximates the recorder's 90 to 60 s cell. L1-family, held to settlement.
Windows evaluated 341 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 21 on 4 days; zero-volume trades 0.
PF at 1 contract 0.53, at 10 contracts 0.68, at 10 contracts with fees x1.2 0.68; net per contract -2.15c at 1, -1.45c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 6 | 5 | 1 | -79.5c | -79.5c | 0.17 |
| 2026-10-31 | 5 | 5 | 0 | +17.4c | -62.1c | 0.35 |
| 2026-11-01 | 7 | 7 | 0 | +24.9c | -37.2c | 0.61 |
| 2026-11-02 | 3 | 3 | 0 | +6.7c | -30.5c | 0.68 |

### GEN4_B01

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and zd >= -1.585; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.13 n 46; validation PF1 2.64 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 71 on 4 days; zero-volume trades 0.
PF at 1 contract 0.76, at 10 contracts 0.81, at 10 contracts with fees x1.2 0.79; net per contract -5.30c at 1, -4.16c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +73.8c | +73.8c | 1.34 |
| 2026-10-31 | 17 | 10 | 7 | -165.8c | -92.0c | 0.86 |
| 2026-11-01 | 28 | 18 | 10 | -57.7c | -149.7c | 0.88 |
| 2026-11-02 | 13 | 8 | 5 | -145.7c | -295.4c | 0.81 |

### GEN4_B02

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and zd >= -2.066; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.09 n 51; validation PF1 2.40 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 68 on 4 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.84, at 10 contracts with fees x1.2 0.82; net per contract -4.41c at 1, -3.31c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -89.3c | -89.3c | 0.74 |
| 2026-10-31 | 14 | 9 | 5 | -10.8c | -100.1c | 0.84 |
| 2026-11-01 | 27 | 18 | 9 | -12.8c | -112.9c | 0.90 |
| 2026-11-02 | 12 | 7 | 5 | -112.2c | -225.1c | 0.84 |

### GEN4_B03

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and sp15 >= -0.1949 and zd >= -0.3503; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.62 n 40; validation PF1 2.39 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 63 on 4 days; zero-volume trades 0.
PF at 1 contract 0.96, at 10 contracts 1.01, at 10 contracts with fees x1.2 1.00; net per contract -0.77c at 1, +0.18c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 4 | 6 | -110.1c | -110.1c | 0.58 |
| 2026-10-31 | 17 | 8 | 9 | -42.3c | -152.4c | 0.78 |
| 2026-11-01 | 25 | 11 | 14 | -180.6c | -333.0c | 0.74 |
| 2026-11-02 | 11 | 9 | 2 | +344.6c | +11.6c | 1.01 |

### GEN4_B04

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.17 and lsz_ask <= 8.072 and lsz_bid <= 8.053; bought at that ask; held to settlement. Discovery PF1 2.04 n 41; validation PF1 2.27 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 75 on 4 days; zero-volume trades 0.
PF at 1 contract 0.82, at 10 contracts 0.84, at 10 contracts with fees x1.2 0.83; net per contract -4.00c at 1, -3.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 12 | 2 | +160.7c | +160.7c | 2.08 |
| 2026-10-31 | 19 | 11 | 8 | -274.5c | -113.8c | 0.85 |
| 2026-11-01 | 29 | 21 | 8 | +57.7c | -56.1c | 0.96 |
| 2026-11-02 | 13 | 7 | 6 | -206.6c | -262.7c | 0.84 |

### GEN4_B05

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 41; validation PF1 2.18 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 58 on 4 days; zero-volume trades 0.
PF at 1 contract 1.36, at 10 contracts 1.43, at 10 contracts with fees x1.2 1.41; net per contract +4.79c at 1, +5.71c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -91.0c | -91.0c | 0.62 |
| 2026-10-31 | 16 | 8 | 8 | +64.4c | -26.6c | 0.94 |
| 2026-11-01 | 16 | 6 | 10 | -27.0c | -53.6c | 0.93 |
| 2026-11-02 | 13 | 9 | 4 | +384.5c | +330.9c | 1.43 |

### GEN4_B06

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.54 n 52; validation PF1 2.08 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 72 on 4 days; zero-volume trades 0.
PF at 1 contract 1.16, at 10 contracts 1.19, at 10 contracts with fees x1.2 1.18; net per contract +2.27c at 1, +2.74c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | -148.3c | -148.3c | 0.49 |
| 2026-10-31 | 17 | 8 | 9 | +78.9c | -69.4c | 0.88 |
| 2026-11-01 | 20 | 7 | 13 | -123.4c | -192.8c | 0.80 |
| 2026-11-02 | 15 | 9 | 6 | +390.3c | +197.5c | 1.19 |

### GEN4_B07

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= 0.3412 and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.68 n 43; validation PF1 2.08 n 24 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 46 on 3 days; zero-volume trades 0.
PF at 1 contract 0.96, at 10 contracts 1.01, at 10 contracts with fees x1.2 0.99; net per contract -0.78c at 1, +0.09c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-31 | 16 | 7 | 9 | +25.3c | +25.3c | 1.08 |
| 2026-11-01 | 22 | 6 | 16 | -210.7c | -185.4c | 0.75 |
| 2026-11-02 | 8 | 5 | 3 | +189.4c | +4.0c | 1.01 |

### GEN4_B08

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.24 n 52; validation PF1 1.99 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 74 on 4 days; zero-volume trades 0.
PF at 1 contract 0.76, at 10 contracts 0.81, at 10 contracts with fees x1.2 0.79; net per contract -5.45c at 1, -4.35c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -65.0c | -65.0c | 0.81 |
| 2026-10-31 | 17 | 12 | 5 | -0.6c | -65.6c | 0.90 |
| 2026-11-01 | 28 | 19 | 9 | -91.5c | -157.1c | 0.88 |
| 2026-11-02 | 13 | 7 | 6 | -164.5c | -321.6c | 0.81 |

### GEN4_B09

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= -0.06831; bought at that ask; held to settlement. Discovery PF1 1.51 n 49; validation PF1 1.94 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 74 on 4 days; zero-volume trades 0.
PF at 1 contract 0.94, at 10 contracts 0.97, at 10 contracts with fees x1.2 0.95; net per contract -1.05c at 1, -0.61c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -122.4c | -122.4c | 0.55 |
| 2026-10-31 | 21 | 9 | 12 | -122.9c | -245.3c | 0.68 |
| 2026-11-01 | 26 | 9 | 17 | -168.2c | -413.5c | 0.67 |
| 2026-11-02 | 14 | 9 | 5 | +368.4c | -45.1c | 0.97 |

### GEN4_B10

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 <= 2.256 and sp5 <= 0.353; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.79 n 46; validation PF1 1.93 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 66 on 4 days; zero-volume trades 0.
PF at 1 contract 0.70, at 10 contracts 0.75, at 10 contracts with fees x1.2 0.74; net per contract -6.58c at 1, -5.42c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 10 | 4 | -57.6c | -57.6c | 0.80 |
| 2026-10-31 | 17 | 9 | 8 | -254.0c | -311.6c | 0.61 |
| 2026-11-01 | 25 | 17 | 8 | +13.5c | -298.1c | 0.76 |
| 2026-11-02 | 10 | 6 | 4 | -59.4c | -357.5c | 0.75 |

### GEN4_B11

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp30 >= 0.5295; bought at that ask; held to settlement. Discovery PF1 1.50 n 46; validation PF1 1.91 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 63 on 4 days; zero-volume trades 0.
PF at 1 contract 1.10, at 10 contracts 1.14, at 10 contracts with fees x1.2 1.12; net per contract +1.42c at 1, +1.92c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 4 | 13 | -83.1c | -83.1c | 0.60 |
| 2026-10-31 | 14 | 5 | 9 | -30.3c | -113.4c | 0.76 |
| 2026-11-01 | 17 | 6 | 11 | -110.0c | -223.4c | 0.72 |
| 2026-11-02 | 15 | 10 | 5 | +344.2c | +120.8c | 1.14 |

### GEN4_B12

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.16 and lsz_ask <= 7.779 and sp5 >= 0.1732; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.32 n 43; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 70 on 4 days; zero-volume trades 0.
PF at 1 contract 0.94, at 10 contracts 1.00, at 10 contracts with fees x1.2 0.98; net per contract -1.24c at 1, -0.03c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 11 | 1 | +258.6c | +258.6c | 4.18 |
| 2026-10-31 | 19 | 13 | 6 | -25.6c | +233.0c | 1.48 |
| 2026-11-01 | 26 | 16 | 10 | -217.1c | +15.9c | 1.01 |
| 2026-11-02 | 13 | 9 | 4 | -17.8c | -1.9c | 1.00 |

### GEN4_B13

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.65 n 56; validation PF1 1.90 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 81 on 4 days; zero-volume trades 0.
PF at 1 contract 0.66, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -7.89c at 1, -6.72c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.8c | -12.8c | 0.96 |
| 2026-10-31 | 19 | 11 | 8 | -215.6c | -228.4c | 0.73 |
| 2026-11-01 | 30 | 19 | 11 | -122.7c | -351.1c | 0.76 |
| 2026-11-02 | 13 | 7 | 6 | -193.1c | -544.2c | 0.70 |

### GEN4_B14

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and lsz_ask <= 7.779; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.30 n 44; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 64 on 4 days; zero-volume trades 0.
PF at 1 contract 0.99, at 10 contracts 1.05, at 10 contracts with fees x1.2 1.04; net per contract -0.25c at 1, +1.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 10 | 2 | +136.8c | +136.8c | 1.99 |
| 2026-10-31 | 16 | 11 | 5 | +25.4c | +162.2c | 1.37 |
| 2026-11-01 | 25 | 17 | 8 | -40.7c | +121.5c | 1.13 |
| 2026-11-02 | 11 | 7 | 4 | -57.6c | +63.9c | 1.05 |

### GEN4_B15

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26 and sp15 >= -0.01237 and spread >= 0.001; bought at that ask; held to settlement. Discovery PF1 1.55 n 42; validation PF1 1.86 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 62 on 4 days; zero-volume trades 0.
PF at 1 contract 0.70, at 10 contracts 0.71, at 10 contracts with fees x1.2 0.70; net per contract -7.06c at 1, -6.64c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 4 | 7 | -206.0c | -206.0c | 0.31 |
| 2026-10-31 | 17 | 8 | 9 | -194.7c | -400.7c | 0.49 |
| 2026-11-01 | 23 | 10 | 13 | -304.5c | -705.2c | 0.49 |
| 2026-11-02 | 11 | 9 | 2 | +293.3c | -411.9c | 0.71 |

### GEN4_B16

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and spread <= 0.01; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.14 n 48; validation PF1 1.83 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 74 on 4 days; zero-volume trades 0.
PF at 1 contract 0.77, at 10 contracts 0.82, at 10 contracts with fees x1.2 0.81; net per contract -5.40c at 1, -4.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +100.3c | +100.3c | 1.46 |
| 2026-10-31 | 19 | 12 | 7 | -135.8c | -35.5c | 0.95 |
| 2026-11-01 | 29 | 19 | 10 | -131.2c | -166.7c | 0.88 |
| 2026-11-02 | 12 | 7 | 5 | -140.0c | -306.7c | 0.82 |

### GEN4_B17

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.4847 and zd >= -2.066; bought at that ask; held to settlement. Discovery PF1 1.52 n 48; validation PF1 1.82 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 63 on 4 days; zero-volume trades 0.
PF at 1 contract 0.70, at 10 contracts 0.71, at 10 contracts with fees x1.2 0.70; net per contract -7.29c at 1, -6.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 13 | 4 | +24.0c | +24.0c | 1.08 |
| 2026-10-31 | 14 | 6 | 8 | -419.1c | -395.1c | 0.55 |
| 2026-11-01 | 24 | 18 | 6 | +60.0c | -335.1c | 0.74 |
| 2026-11-02 | 8 | 4 | 4 | -95.3c | -430.4c | 0.71 |

### GEN4_B18

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and lsz_ask <= 7.779 and zd >= -0.6765; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.63 n 43; validation PF1 1.81 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 68 on 4 days; zero-volume trades 0.
PF at 1 contract 0.83, at 10 contracts 0.88, at 10 contracts with fees x1.2 0.87; net per contract -3.50c at 1, -2.38c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 9 | 3 | +57.1c | +57.1c | 1.28 |
| 2026-10-31 | 17 | 10 | 7 | -145.2c | -88.1c | 0.86 |
| 2026-11-01 | 28 | 19 | 9 | +19.9c | -68.2c | 0.94 |
| 2026-11-02 | 11 | 7 | 4 | -93.3c | -161.5c | 0.88 |

### GEN4_B19

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and imb >= -0.6701; bought at that ask; held to settlement. Discovery PF1 1.78 n 48; validation PF1 1.81 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 67 on 4 days; zero-volume trades 0.
PF at 1 contract 0.78, at 10 contracts 0.80, at 10 contracts with fees x1.2 0.78; net per contract -5.09c at 1, -4.66c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -52.6c | -52.6c | 0.85 |
| 2026-10-31 | 16 | 10 | 6 | -136.8c | -189.4c | 0.76 |
| 2026-11-01 | 24 | 17 | 7 | +18.5c | -170.9c | 0.86 |
| 2026-11-02 | 10 | 5 | 5 | -141.2c | -312.1c | 0.80 |

### GEN4_B20

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and imb >= -0.4281 and sp5 <= 0; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.66 n 43; validation PF1 1.77 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 57 on 4 days; zero-volume trades 0.
PF at 1 contract 0.77, at 10 contracts 0.82, at 10 contracts with fees x1.2 0.81; net per contract -4.86c at 1, -3.75c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -55.9c | -55.9c | 0.80 |
| 2026-10-31 | 13 | 9 | 4 | +24.2c | -31.7c | 0.94 |
| 2026-11-01 | 23 | 16 | 7 | +53.3c | +21.6c | 1.02 |
| 2026-11-02 | 8 | 3 | 5 | -235.6c | -214.0c | 0.82 |

### GEN4_B21

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.902 and lsz_bid >= 7.292; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.54 n 44; validation PF1 1.76 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 34 on 4 days; zero-volume trades 0.
PF at 1 contract 0.64, at 10 contracts 0.69, at 10 contracts with fees x1.2 0.68; net per contract -8.39c at 1, -7.30c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 9 | 5 | -132.3c | -132.3c | 0.62 |
| 2026-10-31 | 1 | 0 | 1 | -70.5c | -202.8c | 0.51 |
| 2026-11-01 | 11 | 9 | 2 | +69.5c | -133.3c | 0.76 |
| 2026-11-02 | 8 | 4 | 4 | -114.9c | -248.2c | 0.69 |

### GEN4_B22

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.456 and lsz_bid >= 6.195; bought at that ask; held to settlement. Discovery PF1 1.63 n 49; validation PF1 1.73 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 74 on 4 days; zero-volume trades 0.
PF at 1 contract 0.65, at 10 contracts 0.67, at 10 contracts with fees x1.2 0.66; net per contract -8.78c at 1, -8.32c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -44.0c | -44.0c | 0.87 |
| 2026-10-31 | 18 | 12 | 6 | -67.7c | -111.7c | 0.86 |
| 2026-11-01 | 27 | 16 | 11 | -317.3c | -429.0c | 0.71 |
| 2026-11-02 | 12 | 6 | 6 | -187.0c | -616.0c | 0.67 |

### GEN4_B23

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; held to settlement. Discovery PF1 1.55 n 40; validation PF1 1.71 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 53 on 4 days; zero-volume trades 0.
PF at 1 contract 0.75, at 10 contracts 0.77, at 10 contracts with fees x1.2 0.76; net per contract -5.70c at 1, -5.21c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.6c | +24.6c | inf |
| 2026-10-31 | 16 | 8 | 8 | -326.0c | -301.4c | 0.47 |
| 2026-11-01 | 26 | 20 | 6 | +139.6c | -161.8c | 0.83 |
| 2026-11-02 | 10 | 6 | 4 | -114.2c | -276.0c | 0.77 |

### GEN4_B24

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.292; bought at that ask; held to settlement. Discovery PF1 2.01 n 50; validation PF1 1.65 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 53 on 4 days; zero-volume trades 0.
PF at 1 contract 0.60, at 10 contracts 0.61, at 10 contracts with fees x1.2 0.60; net per contract -10.42c at 1, -9.98c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 11 | 5 | -54.9c | -54.9c | 0.84 |
| 2026-10-31 | 7 | 5 | 2 | +28.0c | -26.9c | 0.94 |
| 2026-11-01 | 19 | 10 | 9 | -375.6c | -402.5c | 0.62 |
| 2026-11-02 | 11 | 6 | 5 | -126.4c | -528.9c | 0.61 |

### GEN4_B25

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.00 n 40; validation PF1 1.64 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 60 on 4 days; zero-volume trades 0.
PF at 1 contract 0.75, at 10 contracts 0.80, at 10 contracts with fees x1.2 0.78; net per contract -5.87c at 1, -4.76c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 6 | 4 | -85.4c | -85.4c | 0.71 |
| 2026-10-31 | 17 | 10 | 7 | -216.7c | -302.1c | 0.61 |
| 2026-11-01 | 22 | 16 | 6 | +27.5c | -274.6c | 0.77 |
| 2026-11-02 | 11 | 8 | 3 | -10.8c | -285.4c | 0.80 |

### GEN4_B26

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and lsz_bid >= 5.465; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.57 n 49; validation PF1 1.63 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 69 on 4 days; zero-volume trades 0.
PF at 1 contract 0.60, at 10 contracts 0.64, at 10 contracts with fees x1.2 0.63; net per contract -10.17c at 1, -9.07c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -37.3c | -37.3c | 0.89 |
| 2026-10-31 | 16 | 8 | 8 | -347.5c | -384.8c | 0.59 |
| 2026-11-01 | 24 | 16 | 8 | -129.8c | -514.6c | 0.64 |
| 2026-11-02 | 11 | 6 | 5 | -111.2c | -625.8c | 0.64 |

### GEN4_B27

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.52 n 40; validation PF1 1.63 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 53 on 4 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.77, at 10 contracts with fees x1.2 0.76; net per contract -6.56c at 1, -5.38c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 16 | 8 | 8 | -327.4c | -303.0c | 0.47 |
| 2026-11-01 | 26 | 20 | 6 | +134.2c | -168.8c | 0.83 |
| 2026-11-02 | 10 | 6 | 4 | -116.1c | -284.9c | 0.77 |

### GEN4_B28

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and lsz_ask <= 7.388; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.92 n 40; validation PF1 1.61 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 62 on 4 days; zero-volume trades 0.
PF at 1 contract 0.89, at 10 contracts 0.95, at 10 contracts with fees x1.2 0.94; net per contract -2.22c at 1, -1.07c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 7 | 2 | +57.7c | +57.7c | 1.46 |
| 2026-10-31 | 18 | 11 | 7 | -180.5c | -122.8c | 0.80 |
| 2026-11-01 | 25 | 18 | 7 | +51.3c | -71.5c | 0.93 |
| 2026-11-02 | 10 | 7 | 3 | +5.1c | -66.4c | 0.95 |

### GEN4_B29

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.1233; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.26 n 51; validation PF1 1.61 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 72 on 4 days; zero-volume trades 0.
PF at 1 contract 0.90, at 10 contracts 0.96, at 10 contracts with fees x1.2 0.95; net per contract -1.95c at 1, -0.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +106.3c | +106.3c | 1.48 |
| 2026-10-31 | 17 | 12 | 5 | +29.0c | +135.3c | 1.26 |
| 2026-11-01 | 28 | 19 | 9 | -99.6c | +35.7c | 1.03 |
| 2026-11-02 | 12 | 7 | 5 | -86.1c | -50.4c | 0.96 |

### GEN4_B30

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask >= 7.388 and sp15 >= -0.9017 and sp30 <= 2.256; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 45; validation PF1 1.61 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 53 on 4 days; zero-volume trades 0.
PF at 1 contract 0.65, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -8.08c at 1, -6.99c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 9 | 4 | -46.3c | -46.3c | 0.83 |
| 2026-10-31 | 12 | 6 | 6 | -275.9c | -322.2c | 0.55 |
| 2026-11-01 | 21 | 15 | 6 | -56.9c | -379.1c | 0.66 |
| 2026-11-02 | 7 | 5 | 2 | +8.5c | -370.6c | 0.70 |

### GEN4_B31

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid <= 8.422; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.71 n 55; validation PF1 1.59 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 81 on 4 days; zero-volume trades 0.
PF at 1 contract 0.78, at 10 contracts 0.83, at 10 contracts with fees x1.2 0.82; net per contract -4.92c at 1, -3.76c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 15 | 4 | +69.2c | +69.2c | 1.24 |
| 2026-10-31 | 19 | 11 | 8 | -277.5c | -208.3c | 0.76 |
| 2026-11-01 | 30 | 21 | 9 | -26.9c | -235.2c | 0.84 |
| 2026-11-02 | 13 | 8 | 5 | -69.7c | -304.9c | 0.83 |

### GEN4_B32

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.95 n 40; validation PF1 1.57 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 62 on 4 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.85, at 10 contracts with fees x1.2 0.83; net per contract -4.26c at 1, -3.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +24.3c | +24.3c | 1.11 |
| 2026-10-31 | 19 | 12 | 7 | -100.0c | -75.7c | 0.88 |
| 2026-11-01 | 22 | 14 | 8 | -78.2c | -153.9c | 0.86 |
| 2026-11-02 | 11 | 8 | 3 | -40.1c | -194.0c | 0.85 |

### GEN4_B33

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and spread >= 0.001 and vol <= 0.311; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.59 n 40; validation PF1 1.54 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 53 on 4 days; zero-volume trades 0.
PF at 1 contract 0.73, at 10 contracts 0.78, at 10 contracts with fees x1.2 0.77; net per contract -6.11c at 1, -4.79c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |
| 2026-10-31 | 16 | 8 | 8 | -288.5c | -264.1c | 0.50 |
| 2026-11-01 | 26 | 20 | 6 | +129.0c | -135.1c | 0.86 |
| 2026-11-02 | 10 | 6 | 4 | -118.7c | -253.8c | 0.78 |

### GEN4_B34

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 6.824 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.83 n 52; validation PF1 1.54 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 70 on 4 days; zero-volume trades 0.
PF at 1 contract 0.63, at 10 contracts 0.65, at 10 contracts with fees x1.2 0.64; net per contract -9.30c at 1, -8.89c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -28.0c | -28.0c | 0.92 |
| 2026-10-31 | 13 | 8 | 5 | -71.3c | -99.3c | 0.85 |
| 2026-11-01 | 27 | 16 | 11 | -335.8c | -435.1c | 0.69 |
| 2026-11-02 | 12 | 6 | 6 | -187.0c | -622.1c | 0.65 |

### GEN4_B35

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and sp15 >= 1.584 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 2.38 n 41; validation PF1 1.52 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 49 on 4 days; zero-volume trades 0.
PF at 1 contract 1.84, at 10 contracts 1.90, at 10 contracts with fees x1.2 1.88; net per contract +10.40c at 1, +10.89c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 20 | 5 | 15 | +180.7c | +180.7c | 1.87 |
| 2026-10-31 | 7 | 3 | 4 | +92.6c | +273.3c | 1.85 |
| 2026-11-01 | 10 | 5 | 5 | +286.9c | +560.2c | 2.44 |
| 2026-11-02 | 12 | 2 | 10 | -26.8c | +533.4c | 1.90 |

### GEN4_B36

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.83 n 40; validation PF1 1.52 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 62 on 4 days; zero-volume trades 0.
PF at 1 contract 0.81, at 10 contracts 0.87, at 10 contracts with fees x1.2 0.86; net per contract -4.06c at 1, -2.81c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | +25.7c | +25.7c | 1.12 |
| 2026-10-31 | 19 | 12 | 7 | -121.6c | -95.9c | 0.85 |
| 2026-11-01 | 22 | 15 | 7 | -72.0c | -167.9c | 0.85 |
| 2026-11-02 | 11 | 8 | 3 | -6.5c | -174.4c | 0.87 |

### GEN4_B37

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm30 <= 0.17 and sp5 >= 0.353 and spread >= 0.001; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.52 n 43; validation PF1 1.49 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 65 on 4 days; zero-volume trades 0.
PF at 1 contract 1.26, at 10 contracts 1.34, at 10 contracts with fees x1.2 1.32; net per contract +3.45c at 1, +4.41c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 3 | 11 | -119.8c | -119.8c | 0.54 |
| 2026-10-31 | 17 | 7 | 10 | +90.6c | -29.2c | 0.94 |
| 2026-11-01 | 25 | 10 | 15 | -25.0c | -54.2c | 0.93 |
| 2026-11-02 | 9 | 7 | 2 | +340.8c | +286.6c | 1.34 |

### GEN4_B38

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 <= 0.0315; bought at that ask; held to settlement. Discovery PF1 1.50 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 75 on 4 days; zero-volume trades 0.
PF at 1 contract 0.65, at 10 contracts 0.66, at 10 contracts with fees x1.2 0.65; net per contract -9.16c at 1, -8.69c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 10 | 5 | -112.6c | -112.6c | 0.69 |
| 2026-10-31 | 19 | 11 | 8 | -285.1c | -397.7c | 0.59 |
| 2026-11-01 | 29 | 20 | 9 | -37.5c | -435.2c | 0.72 |
| 2026-11-02 | 12 | 6 | 6 | -216.4c | -651.6c | 0.66 |

### GEN4_B39

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.01237; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.44 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 73 on 4 days; zero-volume trades 0.
PF at 1 contract 0.87, at 10 contracts 0.93, at 10 contracts with fees x1.2 0.91; net per contract -2.63c at 1, -1.51c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +168.7c | +168.7c | 1.84 |
| 2026-10-31 | 17 | 9 | 8 | -306.9c | -138.2c | 0.82 |
| 2026-11-01 | 27 | 20 | 7 | +115.7c | -22.5c | 0.98 |
| 2026-11-02 | 12 | 7 | 5 | -87.5c | -110.0c | 0.93 |

### GEN4_B40

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.9734; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.57 n 55; validation PF1 1.44 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 81 on 4 days; zero-volume trades 0.
PF at 1 contract 0.67, at 10 contracts 0.72, at 10 contracts with fees x1.2 0.71; net per contract -7.94c at 1, -6.68c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 19 | 14 | 5 | -12.7c | -12.7c | 0.96 |
| 2026-10-31 | 19 | 11 | 8 | -245.4c | -258.1c | 0.71 |
| 2026-11-01 | 30 | 20 | 10 | -111.5c | -369.6c | 0.76 |
| 2026-11-02 | 13 | 7 | 6 | -171.1c | -540.7c | 0.72 |

### GEN4_B41

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.733 and spread >= 0.01; bought at that ask; held to settlement. Discovery PF1 1.52 n 43; validation PF1 1.43 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 44 on 4 days; zero-volume trades 0.
PF at 1 contract 0.76, at 10 contracts 0.77, at 10 contracts with fees x1.2 0.76; net per contract -5.43c at 1, -5.02c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 10 | 3 | +85.5c | +85.5c | 1.46 |
| 2026-10-31 | 7 | 5 | 2 | -5.0c | +80.5c | 1.25 |
| 2026-11-01 | 15 | 8 | 7 | -304.2c | -223.7c | 0.73 |
| 2026-11-02 | 9 | 6 | 3 | +2.9c | -220.8c | 0.77 |

### GEN4_B42

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= -0.07 and imb >= -0.9734 and sp15 >= 1.584; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.23 n 41; validation PF1 1.42 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 51 on 4 days; zero-volume trades 0.
PF at 1 contract 1.90, at 10 contracts 2.01, at 10 contracts with fees x1.2 1.98; net per contract +10.91c at 1, +11.76c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 21 | 5 | 16 | +163.0c | +163.0c | 1.77 |
| 2026-10-31 | 7 | 4 | 3 | +185.6c | +348.6c | 2.09 |
| 2026-11-01 | 11 | 5 | 6 | +278.0c | +626.6c | 2.59 |
| 2026-11-02 | 12 | 2 | 10 | -26.9c | +599.7c | 2.01 |

### GEN4_B43

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.75 n 48; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 77 on 4 days; zero-volume trades 0.
PF at 1 contract 0.66, at 10 contracts 0.71, at 10 contracts with fees x1.2 0.70; net per contract -8.35c at 1, -7.24c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +11.5c | +11.5c | 1.04 |
| 2026-10-31 | 19 | 11 | 8 | -276.5c | -265.0c | 0.70 |
| 2026-11-01 | 30 | 20 | 10 | -119.9c | -384.9c | 0.75 |
| 2026-11-02 | 13 | 7 | 6 | -172.4c | -557.3c | 0.71 |

### GEN4_B44

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 >= 0.353; bought at that ask; held to settlement. Discovery PF1 2.35 n 51; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 72 on 4 days; zero-volume trades 0.
PF at 1 contract 0.94, at 10 contracts 0.96, at 10 contracts with fees x1.2 0.95; net per contract -1.13c at 1, -0.73c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 14 | 2 | +262.6c | +262.6c | 3.00 |
| 2026-10-31 | 17 | 11 | 6 | -106.5c | +156.1c | 1.28 |
| 2026-11-01 | 27 | 17 | 10 | -221.4c | -65.3c | 0.95 |
| 2026-11-02 | 12 | 8 | 4 | +13.0c | -52.3c | 0.96 |

### GEN4_B45

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and lsz_bid >= 6.824; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.02 n 47; validation PF1 1.37 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 58 on 4 days; zero-volume trades 0.
PF at 1 contract 0.74, at 10 contracts 0.79, at 10 contracts with fees x1.2 0.78; net per contract -5.77c at 1, -4.58c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 12 | 5 | -54.8c | -54.8c | 0.84 |
| 2026-10-31 | 11 | 8 | 3 | +65.8c | +11.0c | 1.02 |
| 2026-11-01 | 21 | 14 | 7 | -111.0c | -100.0c | 0.90 |
| 2026-11-02 | 9 | 4 | 5 | -165.7c | -265.7c | 0.79 |

### GEN4_B46

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.11 and lsz_ask <= 7.388; bought at that ask; held to settlement. Discovery PF1 2.64 n 45; validation PF1 1.34 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 71 on 4 days; zero-volume trades 0.
PF at 1 contract 0.96, at 10 contracts 0.99, at 10 contracts with fees x1.2 0.97; net per contract -0.76c at 1, -0.28c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 11 | 2 | +192.8c | +192.8c | 2.40 |
| 2026-10-31 | 18 | 11 | 7 | -196.2c | -3.4c | 0.99 |
| 2026-11-01 | 28 | 19 | 9 | -73.1c | -76.5c | 0.94 |
| 2026-11-02 | 12 | 9 | 3 | +56.8c | -19.7c | 0.99 |

### GEN4_B47

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; held to settlement. Discovery PF1 1.79 n 48; validation PF1 1.33 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 76 on 4 days; zero-volume trades 0.
PF at 1 contract 0.73, at 10 contracts 0.74, at 10 contracts with fees x1.2 0.73; net per contract -6.57c at 1, -6.10c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 11 | 4 | +13.7c | +13.7c | 1.05 |
| 2026-10-31 | 19 | 11 | 8 | -274.5c | -260.8c | 0.70 |
| 2026-11-01 | 29 | 20 | 9 | -32.6c | -293.4c | 0.80 |
| 2026-11-02 | 13 | 7 | 6 | -170.3c | -463.7c | 0.74 |

### GEN4_B48

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm15 >= -0.09 and sp30 >= -2.625; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.70 n 41; validation PF1 1.33 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 62 on 4 days; zero-volume trades 0.
PF at 1 contract 0.62, at 10 contracts 0.66, at 10 contracts with fees x1.2 0.65; net per contract -9.85c at 1, -8.75c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 8 | 3 | +12.6c | +12.6c | 1.05 |
| 2026-10-31 | 17 | 9 | 8 | -348.4c | -335.8c | 0.59 |
| 2026-11-01 | 23 | 16 | 7 | -81.2c | -417.0c | 0.68 |
| 2026-11-02 | 11 | 7 | 4 | -125.3c | -542.3c | 0.66 |

### GEN4_B49

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; held to settlement. Discovery PF1 2.47 n 55; validation PF1 1.33 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 73 on 4 days; zero-volume trades 0.
PF at 1 contract 0.91, at 10 contracts 0.93, at 10 contracts with fees x1.2 0.92; net per contract -1.81c at 1, -1.36c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 17 | 14 | 3 | +177.3c | +177.3c | 1.91 |
| 2026-10-31 | 17 | 9 | 8 | -310.2c | -132.9c | 0.82 |
| 2026-11-01 | 27 | 20 | 7 | +119.8c | -13.1c | 0.99 |
| 2026-11-02 | 12 | 7 | 5 | -86.1c | -99.2c | 0.93 |

### GEN4_B50

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp15 >= -0.1949 and zd >= -1.214; bought at that ask; held to settlement. Discovery PF1 1.87 n 41; validation PF1 1.31 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 58 on 4 days; zero-volume trades 0.
PF at 1 contract 0.94, at 10 contracts 0.96, at 10 contracts with fees x1.2 0.95; net per contract -1.19c at 1, -0.76c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 11 | 3 | +88.5c | +88.5c | 1.45 |
| 2026-10-31 | 10 | 7 | 3 | +21.5c | +110.0c | 1.27 |
| 2026-11-01 | 24 | 17 | 7 | -2.9c | +107.1c | 1.12 |
| 2026-11-02 | 10 | 5 | 5 | -150.9c | -43.8c | 0.96 |

### GEN4_B51

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0.04 and imb <= 0.4847; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.72 n 50; validation PF1 1.30 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 70 on 4 days; zero-volume trades 0.
PF at 1 contract 0.76, at 10 contracts 0.80, at 10 contracts with fees x1.2 0.79; net per contract -5.46c at 1, -4.36c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 12 | 3 | +75.9c | +75.9c | 1.33 |
| 2026-10-31 | 18 | 10 | 8 | -301.9c | -226.0c | 0.72 |
| 2026-11-01 | 27 | 18 | 9 | -120.0c | -346.0c | 0.75 |
| 2026-11-02 | 10 | 7 | 3 | +40.7c | -305.3c | 0.80 |

### GEN4_REF_FAV150

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. The unconditional core of 41 of the 51 GEN4 validation passes: buy the favourite (side ask 0.50 to 0.85) at the first poll 150 to 120 s before the close, hold. Discovery PF1 1.61 n 50; validation PF1 1.57 n 35. Shows whether the conditions add anything forward.
Windows evaluated 223 on 4 days; without the data the rule needs 0; evaluator errors 0. Trades 71 on 4 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.74, at 10 contracts with fees x1.2 0.73; net per contract -6.58c at 1, -6.12c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 18 | 13 | 5 | -34.7c | -34.7c | 0.90 |
| 2026-10-31 | 17 | 9 | 8 | -314.1c | -348.8c | 0.63 |
| 2026-11-01 | 25 | 18 | 7 | +26.8c | -322.0c | 0.77 |
| 2026-11-02 | 11 | 6 | 5 | -112.7c | -434.7c | 0.74 |

### REF_L1_GOLD

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T00:00:00Z. The live L1 gold rule as a known baseline: the side whose ask is 0.88 to 0.97 at the candle ending 6 minutes before the close, bought at that ask, held to settlement. Candles only, so it ignores the live 25c exit and the window limit.
Windows evaluated 144 on 3 days; without the data the rule needs 0; evaluator errors 0. Trades 31 on 2 days; zero-volume trades 0.
PF at 1 contract 2.10, at 10 contracts 2.26, at 10 contracts with fees x1.2 2.23; net per contract +3.22c at 1, +3.69c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 15 | 14 | 1 | +2.5c | +2.5c | 1.03 |
| 2026-11-02 | 16 | 16 | 0 | +111.9c | +114.4c | 2.26 |

