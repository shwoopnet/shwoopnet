# FORWARD LEDGER (automatic; research only)

Written by `python -m scalper.fwdledger run` (once per AUTO pass, `scalper.autoscore check`). Last updated 2026-10-30 20:08 UTC.
Forward evidence counts only windows that CLOSED after a candidate's freeze time, had the data its rule needs and have settled.
Fees 7% x C x p x (1-p) rounded up to the cent per order, at 1 and 10 contracts; held to settlement pays the entry fee only. Win = net at 10 contracts above zero. Net per contract is at 10 contracts. Trades per week: forward trades over the time from the freeze to the last evaluated close.
This ledger never promotes anything. READY FOR THE FALSIFIER means only: forward PF 1.5+ at 1 and at 10 contracts on 30+ trades over 10+ trade days. It earns a falsifier read, nothing more. How a generator adds a candidate: `workers/candidates/README.md`.

| id | market | stage | freeze | fwd days | trades | wins | losses | PF 1c | PF 10c | net/contract | trades/week | updated | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| REF_GEN6_OIREL | KXBTC15M | reference | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 20:08 UTC |  |
| LADFADE_BTC | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 20:08 UTC |  |
| REF_GEN6_OICORE | KXBTC15M | reference | 2026-10-30 | 1 | 1 | 0 | 1 | 0.00 | 0.00 | -0.50c | 7.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B01 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B02 | KXBTC15M | validation | 2026-10-30 | 1 | 1 | 0 | 1 | 0.00 | 0.00 | -0.50c | 7.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B03 | KXBTC15M | validation | 2026-10-30 | 1 | 1 | 0 | 1 | 0.00 | 0.00 | -0.50c | 7.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B04 | KXBTC15M | validation | 2026-10-30 | 1 | 1 | 0 | 1 | 0.00 | 0.00 | -0.50c | 7.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B05 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B06 | KXBTC15M | validation | 2026-10-30 | 1 | 1 | 0 | 1 | 0.00 | 0.00 | -0.50c | 7.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B07 | KXBTC15M | validation | 2026-10-30 | 1 | 1 | 0 | 1 | 0.00 | 0.00 | -7.60c | 7.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B08 | KXBTC15M | validation | 2026-10-30 | 1 | 1 | 0 | 1 | 0.00 | 0.00 | -3.70c | 7.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B09 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B10 | KXBTC15M | validation | 2026-10-30 | 1 | 2 | 0 | 2 | 0.00 | 0.00 | -2.10c | 14.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B11 | KXBTC15M | validation | 2026-10-30 | 1 | 2 | 0 | 2 | 0.00 | 0.00 | -1.65c | 14.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B12 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 20:08 UTC |  |
| GEN6_B13 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 20:08 UTC |  |
| REF_BTC_UNDERDOG_180 | KXBTC15M | reference | 2026-10-30 | 1 | 12 | 2 | 10 | 0.37 | 0.38 | -17.12c | 84.0 | 2026-10-30 20:08 UTC |  |
| GEN7_B01 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 20:08 UTC |  |
| GEN7_B02 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 20:08 UTC |  |
| REF_GEN6_OIDRIFT | KXBTC15M | reference | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 20:08 UTC |  |
| REF_GOLD_UNDERDOG_180 | KXGOLD15M | reference | 2026-10-30 | 1 | 16 | 3 | 13 | 0.53 | 0.55 | -10.01c | 112.0 | 2026-10-30 20:08 UTC |  |
| REF_LATECAL_BTC | KXBTC15M | reference | 2026-10-30 | 1 | 5 | 4 | 1 | 0.12 | 0.15 | -16.28c | 35.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B01 | KXBTC15M | validation | 2026-10-30 | 1 | 8 | 5 | 3 | 0.66 | 0.70 | -8.11c | 56.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B02 | KXBTC15M | validation | 2026-10-30 | 1 | 10 | 6 | 4 | 0.53 | 0.56 | -12.57c | 70.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B03 | KXBTC15M | validation | 2026-10-30 | 1 | 8 | 3 | 5 | 0.32 | 0.34 | -18.50c | 56.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B04 | KXBTC15M | validation | 2026-10-30 | 1 | 9 | 7 | 2 | 1.29 | 1.32 | +5.34c | 63.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B05 | KXBTC15M | validation | 2026-10-30 | 1 | 9 | 2 | 7 | 0.32 | 0.34 | -11.69c | 63.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B06 | KXBTC15M | validation | 2026-10-30 | 1 | 14 | 3 | 11 | 0.32 | 0.34 | -9.97c | 98.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B07 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B08 | KXBTC15M | validation | 2026-10-30 | 1 | 11 | 7 | 4 | 0.61 | 0.65 | -9.19c | 77.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B09 | KXBTC15M | validation | 2026-10-30 | 1 | 9 | 2 | 7 | 0.30 | 0.32 | -13.04c | 63.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B10 | KXBTC15M | validation | 2026-10-30 | 1 | 9 | 5 | 4 | 0.40 | 0.43 | -18.19c | 63.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B11 | KXBTC15M | validation | 2026-10-30 | 1 | 13 | 3 | 10 | 0.47 | 0.50 | -5.51c | 91.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B12 | KXBTC15M | validation | 2026-10-30 | 1 | 7 | 6 | 1 | 2.34 | 2.45 | +16.86c | 49.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B13 | KXBTC15M | validation | 2026-10-30 | 1 | 12 | 8 | 4 | 0.66 | 0.70 | -7.13c | 84.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B14 | KXBTC15M | validation | 2026-10-30 | 1 | 8 | 6 | 2 | 1.22 | 1.30 | +5.11c | 56.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B15 | KXBTC15M | validation | 2026-10-30 | 1 | 8 | 3 | 5 | 0.33 | 0.34 | -18.81c | 56.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B16 | KXBTC15M | validation | 2026-10-30 | 1 | 9 | 6 | 3 | 0.77 | 0.82 | -4.48c | 63.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B17 | KXBTC15M | validation | 2026-10-30 | 1 | 10 | 7 | 3 | 0.79 | 0.81 | -4.47c | 70.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B18 | KXBTC15M | validation | 2026-10-30 | 1 | 7 | 4 | 3 | 0.60 | 0.63 | -10.69c | 49.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B19 | KXBTC15M | validation | 2026-10-30 | 1 | 11 | 7 | 4 | 0.61 | 0.62 | -9.85c | 77.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B20 | KXBTC15M | validation | 2026-10-30 | 1 | 9 | 5 | 4 | 0.45 | 0.47 | -16.79c | 63.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B21 | KXBTC15M | validation | 2026-10-30 | 1 | 10 | 6 | 4 | 0.53 | 0.56 | -12.55c | 70.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B22 | KXBTC15M | validation | 2026-10-30 | 1 | 11 | 7 | 4 | 0.64 | 0.65 | -9.06c | 77.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B23 | KXBTC15M | validation | 2026-10-30 | 1 | 1 | 1 | 0 | inf | inf | +24.60c | 7.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B24 | KXBTC15M | validation | 2026-10-30 | 1 | 11 | 7 | 4 | 0.64 | 0.65 | -9.06c | 77.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B25 | KXBTC15M | validation | 2026-10-30 | 1 | 7 | 4 | 3 | 0.55 | 0.58 | -12.90c | 49.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B26 | KXBTC15M | validation | 2026-10-30 | 1 | 11 | 7 | 4 | 0.59 | 0.62 | -9.97c | 77.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B27 | KXBTC15M | validation | 2026-10-30 | 1 | 1 | 1 | 0 | inf | inf | +24.40c | 7.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B28 | KXBTC15M | validation | 2026-10-30 | 1 | 5 | 3 | 2 | 0.65 | 0.68 | -7.86c | 35.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B29 | KXBTC15M | validation | 2026-10-30 | 1 | 10 | 7 | 3 | 0.76 | 0.81 | -4.22c | 70.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B30 | KXBTC15M | validation | 2026-10-30 | 1 | 9 | 6 | 3 | 0.63 | 0.67 | -7.73c | 63.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B31 | KXBTC15M | validation | 2026-10-30 | 1 | 12 | 9 | 3 | 0.95 | 1.01 | +0.14c | 84.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B32 | KXBTC15M | validation | 2026-10-30 | 1 | 7 | 4 | 3 | 0.54 | 0.57 | -12.93c | 49.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B33 | KXBTC15M | validation | 2026-10-30 | 1 | 1 | 1 | 0 | inf | inf | +24.40c | 7.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B34 | KXBTC15M | validation | 2026-10-30 | 1 | 12 | 8 | 4 | 0.70 | 0.71 | -6.98c | 84.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B35 | KXBTC15M | validation | 2026-10-30 | 1 | 13 | 4 | 9 | 2.38 | 2.49 | +13.57c | 91.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B36 | KXBTC15M | validation | 2026-10-30 | 1 | 7 | 4 | 3 | 0.54 | 0.58 | -12.90c | 49.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B37 | KXBTC15M | validation | 2026-10-30 | 1 | 10 | 2 | 8 | 0.30 | 0.33 | -11.83c | 70.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B38 | KXBTC15M | validation | 2026-10-30 | 1 | 9 | 5 | 4 | 0.48 | 0.49 | -16.43c | 63.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B39 | KXBTC15M | validation | 2026-10-30 | 1 | 11 | 9 | 2 | 1.72 | 1.81 | +10.36c | 77.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B40 | KXBTC15M | validation | 2026-10-30 | 1 | 12 | 8 | 4 | 0.66 | 0.70 | -7.11c | 84.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B41 | KXBTC15M | validation | 2026-10-30 | 1 | 8 | 6 | 2 | 1.30 | 1.33 | +5.09c | 56.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B42 | KXBTC15M | validation | 2026-10-30 | 1 | 14 | 4 | 10 | 2.25 | 2.40 | +12.24c | 98.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B43 | KXBTC15M | validation | 2026-10-30 | 1 | 10 | 6 | 4 | 0.52 | 0.55 | -12.94c | 70.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B44 | KXBTC15M | validation | 2026-10-30 | 1 | 10 | 9 | 1 | 3.83 | 3.89 | +20.69c | 70.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B45 | KXBTC15M | validation | 2026-10-30 | 1 | 11 | 7 | 4 | 0.58 | 0.62 | -9.97c | 77.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B46 | KXBTC15M | validation | 2026-10-30 | 1 | 8 | 6 | 2 | 1.28 | 1.31 | +5.37c | 56.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B47 | KXBTC15M | validation | 2026-10-30 | 1 | 10 | 6 | 4 | 0.54 | 0.55 | -12.82c | 70.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B48 | KXBTC15M | validation | 2026-10-30 | 1 | 7 | 5 | 2 | 0.90 | 0.95 | -1.01c | 49.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B49 | KXBTC15M | validation | 2026-10-30 | 1 | 11 | 9 | 2 | 1.87 | 1.90 | +11.05c | 77.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B50 | KXBTC15M | validation | 2026-10-30 | 1 | 9 | 7 | 2 | 1.35 | 1.38 | +5.73c | 63.0 | 2026-10-30 20:08 UTC |  |
| GEN4_B51 | KXBTC15M | validation | 2026-10-30 | 1 | 9 | 7 | 2 | 1.25 | 1.31 | +5.17c | 63.0 | 2026-10-30 20:08 UTC |  |
| GEN4_REF_FAV150 | KXBTC15M | reference | 2026-10-30 | 1 | 11 | 7 | 4 | 0.61 | 0.62 | -9.85c | 77.0 | 2026-10-30 20:08 UTC |  |
| REF_L1_GOLD | KXGOLD15M | reference | 2026-10-30 | 1 | 12 | 12 | 0 | inf | inf | +6.64c | 84.0 | 2026-10-30 20:08 UTC |  |

## History per candidate

### REF_GEN6_OIREL

Evaluator `scalper.oirel:forward_eval`, source `candles`, frozen 2026-10-30T15:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) when open interest over the 3 minutes before rose by more than 26.76% of its level at 360 s (the discovery quantile matched to the core's 86,300 count), fill at the next candle's ask, held. History: discovery n 298 PF 1.73, validation n 286 PF 1.71 at 10 contracts (FALS5 check 2, one try). Not independent of REF_GEN6_OICORE (59% to 80% shared trades). workers/FALS5_REGISTRATION.md, workers/FALS5_RESULT.md.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### LADFADE_BTC

Evaluator `scalper.ladfade:forward_eval`, source `candles`, frozen 2026-10-30T12:00:00Z. Bitcoin 15 minute windows opening at :15 and :30: when the hourly KXBTCD ladder leans 5c+ from 50/50 at the first minute, buy the side the 15 minute book overshot AWAY from if its ask is 3c+ below the ladder's chance, at the next candle's ask (30c to 70c), held. Ladder from the book recorder. Discovery and validation spent (post hoc); holdout read once in workers/LADFADE_RESULT.md. 1 try; workers/LADFADE_REGISTRATION.md.
Windows evaluated 5 on 1 days; without the data the rule needs 4; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_GEN6_OICORE

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T03:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest rose more than 86,300 contracts over the 3 minutes before, held to settlement, fill at the next candle's ask. History: discovery PF 2.28 (n 222), validation 1.85 (n 333, z 4.53). Forward days only; 1 try. Falsifier FALS4 running.
Windows evaluated 45 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -1.40c at 1, -0.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |

### GEN6_B01

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | doi>8.63e+04 & m3>-0.25 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.81 (n 104), validation PF 1.90 (n 164), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B02

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | hour<=21 & xb_d2<=0.046 & doi>8.63e+04 | TP +8c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 2.42 (n 106), validation PF 1.80 (n 133), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -1.40c at 1, -0.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |

### GEN6_B03

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 | TP +5c stop -20c else hold]; fill at the next candle's ask. Discovery PF 2.41 (n 222), validation PF 1.73 (n 333), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -1.40c at 1, -0.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |

### GEN6_B04

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 & xa_spr<=0.02 & rng5>0.14 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.06 (n 175), validation PF 1.68 (n 269), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -1.40c at 1, -0.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |

### GEN6_B05

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | d3<=-0.08 & m1<=0 & vol<=1.11e+05 | TP +20c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 1.60 (n 172), validation PF 1.66 (n 58), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B06

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | d1<=0.1 & doi>8.63e+04 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 3.51 (n 111), validation PF 1.57 (n 162), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -1.40c at 1, -0.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -0.5c | -0.5c | 0.00 |

### GEN6_B07

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 240..180s | m3>-0.08 & m5<=-0.24 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.72 (n 137), validation PF 1.45 (n 90), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -8.10c at 1, -7.60c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -7.6c | -7.6c | 0.00 |

### GEN6_B08

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | rng5<=0.273 & doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.14 (n 205), validation PF 1.43 (n 316), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -4.40c at 1, -3.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -3.7c | -3.7c | 0.00 |

### GEN6_B09

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | vol<=1.28e+05 & m1<=-0.0507 | TP +3c stop -20c else sell 60s]; fill at the next candle's ask. Discovery PF 1.55 (n 192), validation PF 1.42 (n 86), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B10

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.19 (n 433), validation PF 1.41 (n 587), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 2 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -2.90c at 1, -2.10c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -4.2c | -4.2c | 0.00 |

### GEN6_B11

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | ask<=0.19 & xa_spr<=0.003 & d1<=-0.05 | TP +5c stop -5c else hold]; fill at the next candle's ask. Discovery PF 1.82 (n 110), validation PF 1.37 (n 93), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 2 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -2.50c at 1, -1.65c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 0 | 2 | -3.3c | -3.3c | 0.00 |

### GEN6_B12

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | rng5>0.32 & hour>19 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.83 (n 102), validation PF 1.32 (n 72), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B13

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | m1>-0.2 & hour>19 | TP +8c stop -20c else hold]; fill at the next candle's ask. Discovery PF 1.70 (n 173), validation PF 1.31 (n 129), C=10.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_BTC_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T02:00:00Z. The mirror of FALS3's finding (Bitcoin favourites at 50c to 85c are overpriced 2 to 3 minutes before the close: PF 0.77 on 2,576 windows, z -4.97): buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held to settlement. History already read (UNDER1 found this side positive), so only forward days count; REV1 is the registered forward read of the related cheap-NO rule (2026-11-05). 1 try.
Windows evaluated 49 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 1 days; zero-volume trades 0.
PF at 1 contract 0.37, at 10 contracts 0.38, at 10 contracts with fees x1.2 0.37; net per contract -17.50c at 1, -17.12c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 2 | 10 | -205.5c | -205.5c | 0.38 |

### GEN7_B01

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 240..240s | npv1>0.281 & vol>1.32e+05 | sell at 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 3.28 (n 101), validation PF 1.80 (n 126), C=10.
Windows evaluated 53 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN7_B02

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 300..240s | npv1>0.393 & doi5>9.78e+04 | TP +20c stop -20c else sell 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 1.75 (n 135), validation PF 1.71 (n 101), C=10.
Windows evaluated 53 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_GEN6_OIDRIFT

Evaluator `scalper.oidrift:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest over the 3 minutes before rose above the 90th percentile of that change over the 30 UTC days before (earlier days only, 20+ days needed), fill at the next candle's ask, held. History validation n 67, PF 2.65 (FALS4 check 5, reproduced). Not independent of REF_GEN6_OICORE. 1 try; workers/OIDRIFT_REGISTRATION.md.
Windows evaluated 53 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_GOLD_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. Gold version of REF_BTC_UNDERDOG_180: FALS3 found gold favourites at 50c to 85c, 2 to 3 minutes before the close, also below break-even (PF 0.85). Buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held. Forward days only. 1 try.
Windows evaluated 53 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 16 on 1 days; zero-volume trades 0.
PF at 1 contract 0.53, at 10 contracts 0.55, at 10 contracts with fees x1.2 0.54; net per contract -10.56c at 1, -10.01c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 16 | 3 | 13 | -160.1c | -160.1c | 0.55 |

### REF_LATECAL_BTC

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. LATECAL's one chosen cell (Bitcoin, 90 to 60 s left, ask 0.95 to 0.98: 61 of 61 won on the recorder, NOT_ENOUGH_DATA; needs about 800 windows to clear the 97.7% break-even) tracked forward. Candles only: the nearest candle is the one ending 60 s before the close, so this approximates the recorder's 90 to 60 s cell. L1-family, held to settlement.
Windows evaluated 53 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 1 days; zero-volume trades 0.
PF at 1 contract 0.12, at 10 contracts 0.15, at 10 contracts with fees x1.2 0.15; net per contract -16.96c at 1, -16.28c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 5 | 4 | 1 | -81.4c | -81.4c | 0.15 |

### GEN4_B01

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and zd >= -1.585; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.13 n 46; validation PF1 2.64 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 1 days; zero-volume trades 0.
PF at 1 contract 0.66, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -9.31c at 1, -8.11c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 8 | 5 | 3 | -64.9c | -64.9c | 0.70 |

### GEN4_B02

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and zd >= -2.066; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.09 n 51; validation PF1 2.40 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 1 days; zero-volume trades 0.
PF at 1 contract 0.53, at 10 contracts 0.56, at 10 contracts with fees x1.2 0.55; net per contract -13.66c at 1, -12.57c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 6 | 4 | -125.7c | -125.7c | 0.56 |

### GEN4_B03

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and sp15 >= -0.1949 and zd >= -0.3503; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.62 n 40; validation PF1 2.39 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 1 days; zero-volume trades 0.
PF at 1 contract 0.32, at 10 contracts 0.34, at 10 contracts with fees x1.2 0.33; net per contract -19.29c at 1, -18.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 8 | 3 | 5 | -148.0c | -148.0c | 0.34 |

### GEN4_B04

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.17 and lsz_ask <= 8.072 and lsz_bid <= 8.053; bought at that ask; held to settlement. Discovery PF1 2.04 n 41; validation PF1 2.27 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 1 days; zero-volume trades 0.
PF at 1 contract 1.29, at 10 contracts 1.32, at 10 contracts with fees x1.2 1.31; net per contract +4.89c at 1, +5.34c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 7 | 2 | +48.1c | +48.1c | 1.32 |

### GEN4_B05

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 41; validation PF1 2.18 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 1 days; zero-volume trades 0.
PF at 1 contract 0.32, at 10 contracts 0.34, at 10 contracts with fees x1.2 0.34; net per contract -12.49c at 1, -11.69c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 2 | 7 | -105.2c | -105.2c | 0.34 |

### GEN4_B06

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.54 n 52; validation PF1 2.08 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 1 days; zero-volume trades 0.
PF at 1 contract 0.32, at 10 contracts 0.34, at 10 contracts with fees x1.2 0.33; net per contract -10.54c at 1, -9.97c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 3 | 11 | -139.6c | -139.6c | 0.34 |

### GEN4_B07

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= 0.3412 and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.68 n 43; validation PF1 2.08 n 24 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B08

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.24 n 52; validation PF1 1.99 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 1 days; zero-volume trades 0.
PF at 1 contract 0.61, at 10 contracts 0.65, at 10 contracts with fees x1.2 0.64; net per contract -10.15c at 1, -9.19c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 7 | 4 | -101.1c | -101.1c | 0.65 |

### GEN4_B09

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= -0.06831; bought at that ask; held to settlement. Discovery PF1 1.51 n 49; validation PF1 1.94 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 1 days; zero-volume trades 0.
PF at 1 contract 0.30, at 10 contracts 0.32, at 10 contracts with fees x1.2 0.31; net per contract -13.69c at 1, -13.04c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 2 | 7 | -117.4c | -117.4c | 0.32 |

### GEN4_B10

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 <= 2.256 and sp5 <= 0.353; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.79 n 46; validation PF1 1.93 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 1 days; zero-volume trades 0.
PF at 1 contract 0.40, at 10 contracts 0.43, at 10 contracts with fees x1.2 0.42; net per contract -19.28c at 1, -18.19c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 5 | 4 | -163.7c | -163.7c | 0.43 |

### GEN4_B11

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp30 >= 0.5295; bought at that ask; held to settlement. Discovery PF1 1.50 n 46; validation PF1 1.91 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 13 on 1 days; zero-volume trades 0.
PF at 1 contract 0.47, at 10 contracts 0.50, at 10 contracts with fees x1.2 0.49; net per contract -6.07c at 1, -5.51c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 3 | 10 | -71.6c | -71.6c | 0.50 |

### GEN4_B12

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.16 and lsz_ask <= 7.779 and sp5 >= 0.1732; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.32 n 43; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 7 on 1 days; zero-volume trades 0.
PF at 1 contract 2.34, at 10 contracts 2.45, at 10 contracts with fees x1.2 2.43; net per contract +15.74c at 1, +16.86c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 6 | 1 | +118.0c | +118.0c | 2.45 |

### GEN4_B13

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.65 n 56; validation PF1 1.90 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 1 days; zero-volume trades 0.
PF at 1 contract 0.66, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -8.23c at 1, -7.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 8 | 4 | -85.5c | -85.5c | 0.70 |

### GEN4_B14

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and lsz_ask <= 7.779; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.30 n 44; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 1 days; zero-volume trades 0.
PF at 1 contract 1.22, at 10 contracts 1.30, at 10 contracts with fees x1.2 1.28; net per contract +3.82c at 1, +5.11c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 8 | 6 | 2 | +40.9c | +40.9c | 1.30 |

### GEN4_B15

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26 and sp15 >= -0.01237 and spread >= 0.001; bought at that ask; held to settlement. Discovery PF1 1.55 n 42; validation PF1 1.86 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 1 days; zero-volume trades 0.
PF at 1 contract 0.33, at 10 contracts 0.34, at 10 contracts with fees x1.2 0.33; net per contract -19.25c at 1, -18.81c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 8 | 3 | 5 | -150.5c | -150.5c | 0.34 |

### GEN4_B16

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and spread <= 0.01; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.14 n 48; validation PF1 1.83 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 1 days; zero-volume trades 0.
PF at 1 contract 0.77, at 10 contracts 0.82, at 10 contracts with fees x1.2 0.81; net per contract -5.71c at 1, -4.48c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 6 | 3 | -40.3c | -40.3c | 0.82 |

### GEN4_B17

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.4847 and zd >= -2.066; bought at that ask; held to settlement. Discovery PF1 1.52 n 48; validation PF1 1.82 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 1 days; zero-volume trades 0.
PF at 1 contract 0.79, at 10 contracts 0.81, at 10 contracts with fees x1.2 0.80; net per contract -4.80c at 1, -4.47c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | -44.7c | -44.7c | 0.81 |

### GEN4_B18

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and lsz_ask <= 7.779 and zd >= -0.6765; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.63 n 43; validation PF1 1.81 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 7 on 1 days; zero-volume trades 0.
PF at 1 contract 0.60, at 10 contracts 0.63, at 10 contracts with fees x1.2 0.63; net per contract -11.77c at 1, -10.69c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 4 | 3 | -74.8c | -74.8c | 0.63 |

### GEN4_B19

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and imb >= -0.6701; bought at that ask; held to settlement. Discovery PF1 1.78 n 48; validation PF1 1.81 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 1 days; zero-volume trades 0.
PF at 1 contract 0.61, at 10 contracts 0.62, at 10 contracts with fees x1.2 0.62; net per contract -10.18c at 1, -9.85c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 7 | 4 | -108.3c | -108.3c | 0.62 |

### GEN4_B20

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and imb >= -0.4281 and sp5 <= 0; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.66 n 43; validation PF1 1.77 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 1 days; zero-volume trades 0.
PF at 1 contract 0.45, at 10 contracts 0.47, at 10 contracts with fees x1.2 0.47; net per contract -17.83c at 1, -16.79c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 5 | 4 | -151.1c | -151.1c | 0.47 |

### GEN4_B21

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.902 and lsz_bid >= 7.292; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.54 n 44; validation PF1 1.76 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 1 days; zero-volume trades 0.
PF at 1 contract 0.53, at 10 contracts 0.56, at 10 contracts with fees x1.2 0.56; net per contract -13.46c at 1, -12.55c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 6 | 4 | -125.5c | -125.5c | 0.56 |

### GEN4_B22

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.456 and lsz_bid >= 6.195; bought at that ask; held to settlement. Discovery PF1 1.63 n 49; validation PF1 1.73 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 1 days; zero-volume trades 0.
PF at 1 contract 0.64, at 10 contracts 0.65, at 10 contracts with fees x1.2 0.64; net per contract -9.45c at 1, -9.06c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 7 | 4 | -99.7c | -99.7c | 0.65 |

### GEN4_B23

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; held to settlement. Discovery PF1 1.55 n 40; validation PF1 1.71 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +24.00c at 1, +24.60c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.6c | +24.6c | inf |

### GEN4_B24

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.292; bought at that ask; held to settlement. Discovery PF1 2.01 n 50; validation PF1 1.65 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 1 days; zero-volume trades 0.
PF at 1 contract 0.64, at 10 contracts 0.65, at 10 contracts with fees x1.2 0.64; net per contract -9.45c at 1, -9.06c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 7 | 4 | -99.7c | -99.7c | 0.65 |

### GEN4_B25

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.00 n 40; validation PF1 1.64 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 7 on 1 days; zero-volume trades 0.
PF at 1 contract 0.55, at 10 contracts 0.58, at 10 contracts with fees x1.2 0.57; net per contract -13.91c at 1, -12.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 4 | 3 | -90.3c | -90.3c | 0.58 |

### GEN4_B26

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and lsz_bid >= 5.465; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.57 n 49; validation PF1 1.63 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 1 days; zero-volume trades 0.
PF at 1 contract 0.59, at 10 contracts 0.62, at 10 contracts with fees x1.2 0.61; net per contract -10.88c at 1, -9.97c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 7 | 4 | -109.7c | -109.7c | 0.62 |

### GEN4_B27

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.52 n 40; validation PF1 1.63 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +22.90c at 1, +24.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |

### GEN4_B28

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and lsz_ask <= 7.388; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.92 n 40; validation PF1 1.61 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 1 days; zero-volume trades 0.
PF at 1 contract 0.65, at 10 contracts 0.68, at 10 contracts with fees x1.2 0.68; net per contract -8.86c at 1, -7.86c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 5 | 3 | 2 | -39.3c | -39.3c | 0.68 |

### GEN4_B29

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.1233; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.26 n 51; validation PF1 1.61 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 1 days; zero-volume trades 0.
PF at 1 contract 0.76, at 10 contracts 0.81, at 10 contracts with fees x1.2 0.80; net per contract -5.45c at 1, -4.22c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 7 | 3 | -42.2c | -42.2c | 0.81 |

### GEN4_B30

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask >= 7.388 and sp15 >= -0.9017 and sp30 <= 2.256; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 45; validation PF1 1.61 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 1 days; zero-volume trades 0.
PF at 1 contract 0.63, at 10 contracts 0.67, at 10 contracts with fees x1.2 0.66; net per contract -8.62c at 1, -7.73c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 6 | 3 | -69.6c | -69.6c | 0.67 |

### GEN4_B31

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid <= 8.422; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.71 n 55; validation PF1 1.59 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 1 days; zero-volume trades 0.
PF at 1 contract 0.95, at 10 contracts 1.01, at 10 contracts with fees x1.2 0.99; net per contract -0.91c at 1, +0.14c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 9 | 3 | +1.7c | +1.7c | 1.01 |

### GEN4_B32

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.95 n 40; validation PF1 1.57 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 7 on 1 days; zero-volume trades 0.
PF at 1 contract 0.54, at 10 contracts 0.57, at 10 contracts with fees x1.2 0.57; net per contract -14.20c at 1, -12.93c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 4 | 3 | -90.5c | -90.5c | 0.57 |

### GEN4_B33

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and spread >= 0.001 and vol <= 0.311; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.59 n 40; validation PF1 1.54 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +22.90c at 1, +24.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +24.4c | +24.4c | inf |

### GEN4_B34

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 6.824 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.83 n 52; validation PF1 1.54 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 1 days; zero-volume trades 0.
PF at 1 contract 0.70, at 10 contracts 0.71, at 10 contracts with fees x1.2 0.70; net per contract -7.33c at 1, -6.98c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 8 | 4 | -83.7c | -83.7c | 0.71 |

### GEN4_B35

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and sp15 >= 1.584 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 2.38 n 41; validation PF1 1.52 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 13 on 1 days; zero-volume trades 0.
PF at 1 contract 2.38, at 10 contracts 2.49, at 10 contracts with fees x1.2 2.46; net per contract +13.07c at 1, +13.57c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 13 | 4 | 9 | +176.4c | +176.4c | 2.49 |

### GEN4_B36

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.83 n 40; validation PF1 1.52 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 7 on 1 days; zero-volume trades 0.
PF at 1 contract 0.54, at 10 contracts 0.58, at 10 contracts with fees x1.2 0.57; net per contract -14.17c at 1, -12.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 4 | 3 | -90.3c | -90.3c | 0.58 |

### GEN4_B37

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm30 <= 0.17 and sp5 >= 0.353 and spread >= 0.001; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.52 n 43; validation PF1 1.49 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 1 days; zero-volume trades 0.
PF at 1 contract 0.30, at 10 contracts 0.33, at 10 contracts with fees x1.2 0.32; net per contract -12.92c at 1, -11.83c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 2 | 8 | -118.3c | -118.3c | 0.33 |

### GEN4_B38

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 <= 0.0315; bought at that ask; held to settlement. Discovery PF1 1.50 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 1 days; zero-volume trades 0.
PF at 1 contract 0.48, at 10 contracts 0.49, at 10 contracts with fees x1.2 0.48; net per contract -16.78c at 1, -16.43c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 5 | 4 | -147.9c | -147.9c | 0.49 |

### GEN4_B39

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.01237; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.44 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 1 days; zero-volume trades 0.
PF at 1 contract 1.72, at 10 contracts 1.81, at 10 contracts with fees x1.2 1.78; net per contract +9.28c at 1, +10.36c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 9 | 2 | +114.0c | +114.0c | 1.81 |

### GEN4_B40

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.9734; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.57 n 55; validation PF1 1.44 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 1 days; zero-volume trades 0.
PF at 1 contract 0.66, at 10 contracts 0.70, at 10 contracts with fees x1.2 0.69; net per contract -8.22c at 1, -7.11c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 8 | 4 | -85.3c | -85.3c | 0.70 |

### GEN4_B41

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.733 and spread >= 0.01; bought at that ask; held to settlement. Discovery PF1 1.52 n 43; validation PF1 1.43 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 1 days; zero-volume trades 0.
PF at 1 contract 1.30, at 10 contracts 1.33, at 10 contracts with fees x1.2 1.31; net per contract +4.62c at 1, +5.09c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 8 | 6 | 2 | +40.7c | +40.7c | 1.33 |

### GEN4_B42

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= -0.07 and imb >= -0.9734 and sp15 >= 1.584; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.23 n 41; validation PF1 1.42 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 14 on 1 days; zero-volume trades 0.
PF at 1 contract 2.25, at 10 contracts 2.40, at 10 contracts with fees x1.2 2.37; net per contract +11.47c at 1, +12.24c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 14 | 4 | 10 | +171.4c | +171.4c | 2.40 |

### GEN4_B43

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.75 n 48; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 1 days; zero-volume trades 0.
PF at 1 contract 0.52, at 10 contracts 0.55, at 10 contracts with fees x1.2 0.54; net per contract -13.86c at 1, -12.94c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 6 | 4 | -129.4c | -129.4c | 0.55 |

### GEN4_B44

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 >= 0.353; bought at that ask; held to settlement. Discovery PF1 2.35 n 51; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 1 days; zero-volume trades 0.
PF at 1 contract 3.83, at 10 contracts 3.89, at 10 contracts with fees x1.2 3.85; net per contract +20.40c at 1, +20.69c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 9 | 1 | +206.9c | +206.9c | 3.89 |

### GEN4_B45

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and lsz_bid >= 6.824; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.02 n 47; validation PF1 1.37 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 1 days; zero-volume trades 0.
PF at 1 contract 0.58, at 10 contracts 0.62, at 10 contracts with fees x1.2 0.61; net per contract -11.05c at 1, -9.97c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 7 | 4 | -109.7c | -109.7c | 0.62 |

### GEN4_B46

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.11 and lsz_ask <= 7.388; bought at that ask; held to settlement. Discovery PF1 2.64 n 45; validation PF1 1.34 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 8 on 1 days; zero-volume trades 0.
PF at 1 contract 1.28, at 10 contracts 1.31, at 10 contracts with fees x1.2 1.30; net per contract +4.87c at 1, +5.37c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 8 | 6 | 2 | +43.0c | +43.0c | 1.31 |

### GEN4_B47

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; held to settlement. Discovery PF1 1.79 n 48; validation PF1 1.33 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 10 on 1 days; zero-volume trades 0.
PF at 1 contract 0.54, at 10 contracts 0.55, at 10 contracts with fees x1.2 0.55; net per contract -13.20c at 1, -12.82c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 10 | 6 | 4 | -128.2c | -128.2c | 0.55 |

### GEN4_B48

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm15 >= -0.09 and sp30 >= -2.625; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.70 n 41; validation PF1 1.33 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 7 on 1 days; zero-volume trades 0.
PF at 1 contract 0.90, at 10 contracts 0.95, at 10 contracts with fees x1.2 0.94; net per contract -2.21c at 1, -1.01c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 7 | 5 | 2 | -7.1c | -7.1c | 0.95 |

### GEN4_B49

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; held to settlement. Discovery PF1 2.47 n 55; validation PF1 1.33 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 1 days; zero-volume trades 0.
PF at 1 contract 1.87, at 10 contracts 1.90, at 10 contracts with fees x1.2 1.87; net per contract +10.73c at 1, +11.05c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 9 | 2 | +121.6c | +121.6c | 1.90 |

### GEN4_B50

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp15 >= -0.1949 and zd >= -1.214; bought at that ask; held to settlement. Discovery PF1 1.87 n 41; validation PF1 1.31 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 1 days; zero-volume trades 0.
PF at 1 contract 1.35, at 10 contracts 1.38, at 10 contracts with fees x1.2 1.36; net per contract +5.33c at 1, +5.73c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 7 | 2 | +51.6c | +51.6c | 1.38 |

### GEN4_B51

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0.04 and imb <= 0.4847; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.72 n 50; validation PF1 1.30 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 9 on 1 days; zero-volume trades 0.
PF at 1 contract 1.25, at 10 contracts 1.31, at 10 contracts with fees x1.2 1.29; net per contract +4.14c at 1, +5.17c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 9 | 7 | 2 | +46.5c | +46.5c | 1.31 |

### GEN4_REF_FAV150

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. The unconditional core of 41 of the 51 GEN4 validation passes: buy the favourite (side ask 0.50 to 0.85) at the first poll 150 to 120 s before the close, hold. Discovery PF1 1.61 n 50; validation PF1 1.57 n 35. Shows whether the conditions add anything forward.
Windows evaluated 39 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 11 on 1 days; zero-volume trades 0.
PF at 1 contract 0.61, at 10 contracts 0.62, at 10 contracts with fees x1.2 0.62; net per contract -10.18c at 1, -9.85c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 11 | 7 | 4 | -108.3c | -108.3c | 0.62 |

### REF_L1_GOLD

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T00:00:00Z. The live L1 gold rule as a known baseline: the side whose ask is 0.88 to 0.97 at the candle ending 6 minutes before the close, bought at that ask, held to settlement. Candles only, so it ignores the live 25c exit and the window limit.
Windows evaluated 57 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 12 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +6.14c at 1, +6.64c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 12 | 12 | 0 | +79.7c | +79.7c | inf |

