# FORWARD LEDGER (automatic; research only)

Written by `python -m scalper.fwdledger run` (once per AUTO pass, `scalper.autoscore check`). Last updated 2026-10-30 05:19 UTC.
Forward evidence counts only windows that CLOSED after a candidate's freeze time, had the data its rule needs and have settled.
Fees 7% x C x p x (1-p) rounded up to the cent per order, at 1 and 10 contracts; held to settlement pays the entry fee only. Win = net at 10 contracts above zero. Net per contract is at 10 contracts. Trades per week: forward trades over the time from the freeze to the last evaluated close.
This ledger never promotes anything. READY FOR THE FALSIFIER means only: forward PF 1.5+ at 1 and at 10 contracts on 30+ trades over 10+ trade days. It earns a falsifier read, nothing more. How a generator adds a candidate: `workers/candidates/README.md`.

| id | market | stage | freeze | fwd days | trades | wins | losses | PF 1c | PF 10c | net/contract | trades/week | updated | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| REF_GEN6_OICORE | KXBTC15M | reference | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B01 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B02 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B03 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B04 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B05 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B06 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B07 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B08 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B09 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B10 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B11 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B12 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN6_B13 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| REF_BTC_UNDERDOG_180 | KXBTC15M | reference | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN7_B01 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN7_B02 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| REF_GEN6_OIDRIFT | KXBTC15M | reference | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| REF_GOLD_UNDERDOG_180 | KXGOLD15M | reference | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| REF_LATECAL_BTC | KXBTC15M | reference | 2026-10-30 | 1 | 1 | 1 | 0 | inf | inf | +4.50c | 7.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B01 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 2 | 1 | 1.05 | 1.11 | +2.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B02 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 1 | 2 | 0.10 | 0.11 | -41.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B03 | KXBTC15M | validation | 2026-10-30 | 1 | 2 | 1 | 1 | 0.53 | 0.58 | -5.80c | 14.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B04 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 3 | 0 | inf | inf | +31.20c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B05 | KXBTC15M | validation | 2026-10-30 | 1 | 5 | 1 | 4 | 0.69 | 0.75 | -2.36c | 35.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B06 | KXBTC15M | validation | 2026-10-30 | 1 | 6 | 1 | 5 | 0.23 | 0.25 | -8.15c | 42.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B07 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B08 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 1 | 2 | 0.11 | 0.11 | -41.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B09 | KXBTC15M | validation | 2026-10-30 | 1 | 5 | 1 | 4 | 0.71 | 0.75 | -2.32c | 35.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B10 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 1 | 2 | 0.10 | 0.11 | -41.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B11 | KXBTC15M | validation | 2026-10-30 | 1 | 6 | 1 | 5 | 0.23 | 0.25 | -8.15c | 42.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B12 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 3 | 0 | inf | inf | +28.03c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B13 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 2 | 2 | 0.21 | 0.22 | -26.80c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B14 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 2 | 1 | 1.05 | 1.11 | +2.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B15 | KXBTC15M | validation | 2026-10-30 | 1 | 2 | 1 | 1 | 0.57 | 0.58 | -5.70c | 14.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B16 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 2 | 1 | 1.05 | 1.11 | +2.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B17 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 3 | 1 | 0.76 | 0.77 | -4.90c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B18 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 2 | 1 | 1.05 | 1.11 | +2.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B19 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 2 | 2 | 0.23 | 0.23 | -26.70c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B20 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 1 | 2 | 0.10 | 0.11 | -41.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B21 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 1 | 2 | 0.11 | 0.11 | -41.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B22 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 1 | 2 | 0.12 | 0.12 | -40.93c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B23 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B24 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 1 | 2 | 0.12 | 0.12 | -40.93c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B25 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 2 | 1 | 1.30 | 1.34 | +7.13c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B26 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 2 | 2 | 0.21 | 0.23 | -26.80c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B27 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B28 | KXBTC15M | validation | 2026-10-30 | 1 | 2 | 1 | 1 | 0.80 | 0.82 | -4.90c | 14.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B29 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 1 | 2 | 0.11 | 0.11 | -41.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B30 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 2 | 2 | 0.21 | 0.22 | -28.05c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B31 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 3 | 1 | 0.72 | 0.76 | -5.05c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B32 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 2 | 1 | 1.28 | 1.35 | +7.13c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B33 | KXBTC15M | validation | 2026-10-30 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B34 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 2 | 2 | 0.23 | 0.23 | -26.70c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B35 | KXBTC15M | validation | 2026-10-30 | 1 | 5 | 2 | 3 | 4.82 | 5.07 | +21.90c | 35.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B36 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 2 | 1 | 1.28 | 1.34 | +7.13c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B37 | KXBTC15M | validation | 2026-10-30 | 1 | 5 | 1 | 4 | 0.69 | 0.76 | -2.38c | 35.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B38 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 1 | 2 | 0.12 | 0.12 | -40.93c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B39 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 4 | 0 | inf | inf | +27.20c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B40 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 2 | 2 | 0.21 | 0.23 | -26.80c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B41 | KXBTC15M | validation | 2026-10-30 | 1 | 1 | 0 | 1 | 0.00 | 0.00 | -54.80c | 7.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B42 | KXBTC15M | validation | 2026-10-30 | 1 | 5 | 2 | 3 | 4.74 | 5.06 | +21.82c | 35.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B43 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 1 | 2 | 0.11 | 0.11 | -41.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B44 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 4 | 0 | inf | inf | +27.40c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B45 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 2 | 2 | 0.21 | 0.23 | -26.80c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B46 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 2 | 1 | 1.45 | 1.47 | +8.57c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B47 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 1 | 2 | 0.12 | 0.12 | -40.93c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B48 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 3 | 0 | inf | inf | +35.17c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B49 | KXBTC15M | validation | 2026-10-30 | 1 | 4 | 4 | 0 | inf | inf | +27.40c | 28.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B50 | KXBTC15M | validation | 2026-10-30 | 1 | 2 | 2 | 0 | inf | inf | +19.80c | 14.0 | 2026-10-30 05:19 UTC |  |
| GEN4_B51 | KXBTC15M | validation | 2026-10-30 | 1 | 3 | 2 | 1 | 0.55 | 0.57 | -12.00c | 21.0 | 2026-10-30 05:19 UTC |  |
| GEN4_REF_FAV150 | KXBTC15M | reference | 2026-10-30 | 1 | 4 | 2 | 2 | 0.23 | 0.23 | -26.70c | 28.0 | 2026-10-30 05:19 UTC |  |
| REF_L1_GOLD | KXGOLD15M | reference | 2026-10-30 | 1 | 1 | 1 | 0 | inf | inf | +4.90c | 7.0 | 2026-10-30 05:19 UTC |  |

## History per candidate

### REF_GEN6_OICORE

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T03:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest rose more than 86,300 contracts over the 3 minutes before, held to settlement, fill at the next candle's ask. History: discovery PF 2.28 (n 222), validation 1.85 (n 333, z 4.53). Forward days only; 1 try. Falsifier FALS4 running.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B01

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | doi>8.63e+04 & m3>-0.25 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.81 (n 104), validation PF 1.90 (n 164), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B02

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | hour<=21 & xb_d2<=0.046 & doi>8.63e+04 | TP +8c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 2.42 (n 106), validation PF 1.80 (n 133), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B03

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 | TP +5c stop -20c else hold]; fill at the next candle's ask. Discovery PF 2.41 (n 222), validation PF 1.73 (n 333), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B04

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 180..180s | doi>8.63e+04 & xa_spr<=0.02 & rng5>0.14 | TP +20c stop none else hold]; fill at the next candle's ask. Discovery PF 2.06 (n 175), validation PF 1.68 (n 269), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B05

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | d3<=-0.08 & m1<=0 & vol<=1.11e+05 | TP +20c stop none else sell 60s]; fill at the next candle's ask. Discovery PF 1.60 (n 172), validation PF 1.66 (n 58), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B06

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | d1<=0.1 & doi>8.63e+04 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 3.51 (n 111), validation PF 1.57 (n 162), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B07

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 240..180s | m3>-0.08 & m5<=-0.24 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.72 (n 137), validation PF 1.45 (n 90), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B08

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | rng5<=0.273 & doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.14 (n 205), validation PF 1.43 (n 316), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B09

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | vol<=1.28e+05 & m1<=-0.0507 | TP +3c stop -20c else sell 60s]; fill at the next candle's ask. Discovery PF 1.55 (n 192), validation PF 1.42 (n 86), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B10

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [both 240..180s | doi>8.63e+04 | hold]; fill at the next candle's ask. Discovery PF 2.19 (n 433), validation PF 1.41 (n 587), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B11

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | ask<=0.19 & xa_spr<=0.003 & d1<=-0.05 | TP +5c stop -5c else hold]; fill at the next candle's ask. Discovery PF 1.82 (n 110), validation PF 1.37 (n 93), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B12

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [yes 180..180s | rng5>0.32 & hour>19 | TP +8c stop none else hold]; fill at the next candle's ask. Discovery PF 1.83 (n 102), validation PF 1.32 (n 72), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN6_B13

Evaluator `scalper.gen6:forward_eval`, source `candles`, frozen 2026-10-30T02:00:00Z. Bitcoin underdog (ask 5c to 50c at the signal), [no 180..180s | m1>-0.2 & hour>19 | TP +8c stop -20c else hold]; fill at the next candle's ask. Discovery PF 1.70 (n 173), validation PF 1.31 (n 129), C=10.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_BTC_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T02:00:00Z. The mirror of FALS3's finding (Bitcoin favourites at 50c to 85c are overpriced 2 to 3 minutes before the close: PF 0.77 on 2,576 windows, z -4.97): buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held to settlement. History already read (UNDER1 found this side positive), so only forward days count; REV1 is the registered forward read of the related cheap-NO rule (2026-11-05). 1 try.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN7_B01

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 240..240s | npv1>0.281 & vol>1.32e+05 | sell at 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 3.28 (n 101), validation PF 1.80 (n 126), C=10.
Windows evaluated 1 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN7_B02

Evaluator `scalper.gen7:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin cheap side (ask 5c to 50c at the signal), [cheap both 300..240s | npv1>0.393 & doi5>9.78e+04 | TP +20c stop -20c else sell 60s]; npv1 = open interest change over the last minute divided by that minute's volume; fill at the next candle's ask. Discovery PF 1.75 (n 135), validation PF 1.71 (n 101), C=10.
Windows evaluated 1 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_GEN6_OIDRIFT

Evaluator `scalper.oidrift:forward_eval`, source `candles`, frozen 2026-10-30T01:00:00Z. Bitcoin underdog (ask 5c to 50c at the candle ending 180 s before the close) after open interest over the 3 minutes before rose above the 90th percentile of that change over the 30 UTC days before (earlier days only, 20+ days needed), fill at the next candle's ask, held. History validation n 67, PF 2.65 (FALS4 check 5, reproduced). Not independent of REF_GEN6_OICORE. 1 try; workers/OIDRIFT_REGISTRATION.md.
Windows evaluated 1 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_GOLD_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. Gold version of REF_BTC_UNDERDOG_180: FALS3 found gold favourites at 50c to 85c, 2 to 3 minutes before the close, also below break-even (PF 0.85). Buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held. Forward days only. 1 try.
Windows evaluated 1 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_LATECAL_BTC

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. LATECAL's one chosen cell (Bitcoin, 90 to 60 s left, ask 0.95 to 0.98: 61 of 61 won on the recorder, NOT_ENOUGH_DATA; needs about 800 windows to clear the 97.7% break-even) tracked forward. Candles only: the nearest candle is the one ending 60 s before the close, so this approximates the recorder's 90 to 60 s cell. L1-family, held to settlement.
Windows evaluated 1 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +3.90c at 1, +4.50c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +4.5c | +4.5c | inf |

### GEN4_B01

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and zd >= -1.585; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.13 n 46; validation PF1 2.64 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 1.05, at 10 contracts 1.11, at 10 contracts with fees x1.2 1.10; net per contract +0.97c at 1, +2.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 2 | 1 | +6.0c | +6.0c | 1.11 |

### GEN4_B02

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and zd >= -2.066; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.09 n 51; validation PF1 2.40 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.10, at 10 contracts 0.11, at 10 contracts with fees x1.2 0.11; net per contract -41.67c at 1, -41.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | -123.0c | -123.0c | 0.11 |

### GEN4_B03

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and sp15 >= -0.1949 and zd >= -0.3503; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.62 n 40; validation PF1 2.39 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 2 on 1 days; zero-volume trades 0.
PF at 1 contract 0.53, at 10 contracts 0.58, at 10 contracts with fees x1.2 0.56; net per contract -6.55c at 1, -5.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 1 | 1 | -11.6c | -11.6c | 0.58 |

### GEN4_B04

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.17 and lsz_ask <= 8.072 and lsz_bid <= 8.053; bought at that ask; held to settlement. Discovery PF1 2.04 n 41; validation PF1 2.27 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +31.00c at 1, +31.20c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 3 | 0 | +93.6c | +93.6c | inf |

### GEN4_B05

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 41; validation PF1 2.18 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 1 days; zero-volume trades 0.
PF at 1 contract 0.69, at 10 contracts 0.75, at 10 contracts with fees x1.2 0.73; net per contract -3.06c at 1, -2.36c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 5 | 1 | 4 | -11.8c | -11.8c | 0.75 |

### GEN4_B06

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.54 n 52; validation PF1 2.08 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 1 days; zero-volume trades 0.
PF at 1 contract 0.23, at 10 contracts 0.25, at 10 contracts with fees x1.2 0.24; net per contract -8.70c at 1, -8.15c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 6 | 1 | 5 | -48.9c | -48.9c | 0.25 |

### GEN4_B07

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= 0.3412 and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.68 n 43; validation PF1 2.08 n 24 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B08

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.24 n 52; validation PF1 1.99 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.11, at 10 contracts 0.11, at 10 contracts with fees x1.2 0.11; net per contract -41.37c at 1, -41.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | -123.0c | -123.0c | 0.11 |

### GEN4_B09

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= -0.06831; bought at that ask; held to settlement. Discovery PF1 1.51 n 49; validation PF1 1.94 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 1 days; zero-volume trades 0.
PF at 1 contract 0.71, at 10 contracts 0.75, at 10 contracts with fees x1.2 0.74; net per contract -2.84c at 1, -2.32c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 5 | 1 | 4 | -11.6c | -11.6c | 0.75 |

### GEN4_B10

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 <= 2.256 and sp5 <= 0.353; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.79 n 46; validation PF1 1.93 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.10, at 10 contracts 0.11, at 10 contracts with fees x1.2 0.11; net per contract -41.67c at 1, -41.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | -123.0c | -123.0c | 0.11 |

### GEN4_B11

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp30 >= 0.5295; bought at that ask; held to settlement. Discovery PF1 1.50 n 46; validation PF1 1.91 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 6 on 1 days; zero-volume trades 0.
PF at 1 contract 0.23, at 10 contracts 0.25, at 10 contracts with fees x1.2 0.24; net per contract -8.70c at 1, -8.15c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 6 | 1 | 5 | -48.9c | -48.9c | 0.25 |

### GEN4_B12

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.16 and lsz_ask <= 7.779 and sp5 >= 0.1732; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.32 n 43; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +26.87c at 1, +28.03c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 3 | 0 | +84.1c | +84.1c | inf |

### GEN4_B13

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.65 n 56; validation PF1 1.90 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract 0.21, at 10 contracts 0.22, at 10 contracts with fees x1.2 0.22; net per contract -27.52c at 1, -26.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 2 | 2 | -107.2c | -107.2c | 0.22 |

### GEN4_B14

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and lsz_ask <= 7.779; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.30 n 44; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 1.05, at 10 contracts 1.11, at 10 contracts with fees x1.2 1.09; net per contract +0.97c at 1, +2.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 2 | 1 | +6.0c | +6.0c | 1.11 |

### GEN4_B15

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26 and sp15 >= -0.01237 and spread >= 0.001; bought at that ask; held to settlement. Discovery PF1 1.55 n 42; validation PF1 1.86 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 2 on 1 days; zero-volume trades 0.
PF at 1 contract 0.57, at 10 contracts 0.58, at 10 contracts with fees x1.2 0.57; net per contract -6.00c at 1, -5.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 1 | 1 | -11.4c | -11.4c | 0.58 |

### GEN4_B16

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and spread <= 0.01; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.14 n 48; validation PF1 1.83 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 1.05, at 10 contracts 1.11, at 10 contracts with fees x1.2 1.09; net per contract +0.97c at 1, +2.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 2 | 1 | +6.0c | +6.0c | 1.11 |

### GEN4_B17

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.4847 and zd >= -2.066; bought at that ask; held to settlement. Discovery PF1 1.52 n 48; validation PF1 1.82 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract 0.76, at 10 contracts 0.77, at 10 contracts with fees x1.2 0.76; net per contract -5.00c at 1, -4.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 3 | 1 | -19.6c | -19.6c | 0.77 |

### GEN4_B18

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and lsz_ask <= 7.779 and zd >= -0.6765; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.63 n 43; validation PF1 1.81 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 1.05, at 10 contracts 1.11, at 10 contracts with fees x1.2 1.10; net per contract +0.97c at 1, +2.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 2 | 1 | +6.0c | +6.0c | 1.11 |

### GEN4_B19

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and imb >= -0.6701; bought at that ask; held to settlement. Discovery PF1 1.78 n 48; validation PF1 1.81 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract 0.23, at 10 contracts 0.23, at 10 contracts with fees x1.2 0.23; net per contract -26.75c at 1, -26.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 2 | 2 | -106.8c | -106.8c | 0.23 |

### GEN4_B20

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and imb >= -0.4281 and sp5 <= 0; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.66 n 43; validation PF1 1.77 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.10, at 10 contracts 0.11, at 10 contracts with fees x1.2 0.11; net per contract -41.67c at 1, -41.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | -123.0c | -123.0c | 0.11 |

### GEN4_B21

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.902 and lsz_bid >= 7.292; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.54 n 44; validation PF1 1.76 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.11, at 10 contracts 0.11, at 10 contracts with fees x1.2 0.11; net per contract -41.37c at 1, -41.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | -123.0c | -123.0c | 0.11 |

### GEN4_B22

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.456 and lsz_bid >= 6.195; bought at that ask; held to settlement. Discovery PF1 1.63 n 49; validation PF1 1.73 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.12, at 10 contracts 0.12, at 10 contracts with fees x1.2 0.11; net per contract -41.00c at 1, -40.93c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | -122.8c | -122.8c | 0.12 |

### GEN4_B23

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; held to settlement. Discovery PF1 1.55 n 40; validation PF1 1.71 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B24

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.292; bought at that ask; held to settlement. Discovery PF1 2.01 n 50; validation PF1 1.65 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.12, at 10 contracts 0.12, at 10 contracts with fees x1.2 0.11; net per contract -41.00c at 1, -40.93c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | -122.8c | -122.8c | 0.12 |

### GEN4_B25

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.00 n 40; validation PF1 1.64 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 1.30, at 10 contracts 1.34, at 10 contracts with fees x1.2 1.32; net per contract +6.27c at 1, +7.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 2 | 1 | +21.4c | +21.4c | 1.34 |

### GEN4_B26

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and lsz_bid >= 5.465; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.57 n 49; validation PF1 1.63 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract 0.21, at 10 contracts 0.23, at 10 contracts with fees x1.2 0.22; net per contract -27.30c at 1, -26.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 2 | 2 | -107.2c | -107.2c | 0.23 |

### GEN4_B27

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.52 n 40; validation PF1 1.63 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B28

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and lsz_ask <= 7.388; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.92 n 40; validation PF1 1.61 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 2 on 1 days; zero-volume trades 0.
PF at 1 contract 0.80, at 10 contracts 0.82, at 10 contracts with fees x1.2 0.81; net per contract -5.55c at 1, -4.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 1 | 1 | -9.8c | -9.8c | 0.82 |

### GEN4_B29

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.1233; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.26 n 51; validation PF1 1.61 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.11, at 10 contracts 0.11, at 10 contracts with fees x1.2 0.11; net per contract -41.67c at 1, -41.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | -123.0c | -123.0c | 0.11 |

### GEN4_B30

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask >= 7.388 and sp15 >= -0.9017 and sp30 <= 2.256; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 45; validation PF1 1.61 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract 0.21, at 10 contracts 0.22, at 10 contracts with fees x1.2 0.22; net per contract -28.55c at 1, -28.05c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 2 | 2 | -112.2c | -112.2c | 0.22 |

### GEN4_B31

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid <= 8.422; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.71 n 55; validation PF1 1.59 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract 0.72, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.75; net per contract -5.82c at 1, -5.05c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 3 | 1 | -20.2c | -20.2c | 0.76 |

### GEN4_B32

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.95 n 40; validation PF1 1.57 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 1.28, at 10 contracts 1.35, at 10 contracts with fees x1.2 1.33; net per contract +5.97c at 1, +7.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 2 | 1 | +21.4c | +21.4c | 1.35 |

### GEN4_B33

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and spread >= 0.001 and vol <= 0.311; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.59 n 40; validation PF1 1.54 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B34

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 6.824 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.83 n 52; validation PF1 1.54 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract 0.23, at 10 contracts 0.23, at 10 contracts with fees x1.2 0.23; net per contract -26.75c at 1, -26.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 2 | 2 | -106.8c | -106.8c | 0.23 |

### GEN4_B35

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and sp15 >= 1.584 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 2.38 n 41; validation PF1 1.52 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 1 days; zero-volume trades 0.
PF at 1 contract 4.82, at 10 contracts 5.07, at 10 contracts with fees x1.2 5.00; net per contract +21.56c at 1, +21.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 5 | 2 | 3 | +109.5c | +109.5c | 5.07 |

### GEN4_B36

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.83 n 40; validation PF1 1.52 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 1.28, at 10 contracts 1.34, at 10 contracts with fees x1.2 1.32; net per contract +5.97c at 1, +7.13c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 2 | 1 | +21.4c | +21.4c | 1.34 |

### GEN4_B37

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm30 <= 0.17 and sp5 >= 0.353 and spread >= 0.001; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.52 n 43; validation PF1 1.49 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 1 days; zero-volume trades 0.
PF at 1 contract 0.69, at 10 contracts 0.76, at 10 contracts with fees x1.2 0.75; net per contract -3.40c at 1, -2.38c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 5 | 1 | 4 | -11.9c | -11.9c | 0.76 |

### GEN4_B38

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 <= 0.0315; bought at that ask; held to settlement. Discovery PF1 1.50 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.12, at 10 contracts 0.12, at 10 contracts with fees x1.2 0.11; net per contract -41.00c at 1, -40.93c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | -122.8c | -122.8c | 0.12 |

### GEN4_B39

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.01237; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.44 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +26.15c at 1, +27.20c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 4 | 0 | +108.8c | +108.8c | inf |

### GEN4_B40

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.9734; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.57 n 55; validation PF1 1.44 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract 0.21, at 10 contracts 0.23, at 10 contracts with fees x1.2 0.22; net per contract -27.52c at 1, -26.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 2 | 2 | -107.2c | -107.2c | 0.23 |

### GEN4_B41

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.733 and spread >= 0.01; bought at that ask; held to settlement. Discovery PF1 1.52 n 43; validation PF1 1.43 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract -55.00c at 1, -54.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 0 | 1 | -54.8c | -54.8c | 0.00 |

### GEN4_B42

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= -0.07 and imb >= -0.9734 and sp15 >= 1.584; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.23 n 41; validation PF1 1.42 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 5 on 1 days; zero-volume trades 0.
PF at 1 contract 4.74, at 10 contracts 5.06, at 10 contracts with fees x1.2 4.98; net per contract +21.12c at 1, +21.82c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 5 | 2 | 3 | +109.1c | +109.1c | 5.06 |

### GEN4_B43

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.75 n 48; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.11, at 10 contracts 0.11, at 10 contracts with fees x1.2 0.11; net per contract -41.37c at 1, -41.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | -123.0c | -123.0c | 0.11 |

### GEN4_B44

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 >= 0.353; bought at that ask; held to settlement. Discovery PF1 2.35 n 51; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +27.25c at 1, +27.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 4 | 0 | +109.6c | +109.6c | inf |

### GEN4_B45

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and lsz_bid >= 6.824; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.02 n 47; validation PF1 1.37 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract 0.21, at 10 contracts 0.23, at 10 contracts with fees x1.2 0.22; net per contract -27.52c at 1, -26.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 2 | 2 | -107.2c | -107.2c | 0.23 |

### GEN4_B46

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.11 and lsz_ask <= 7.388; bought at that ask; held to settlement. Discovery PF1 2.64 n 45; validation PF1 1.34 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 1.45, at 10 contracts 1.47, at 10 contracts with fees x1.2 1.45; net per contract +8.33c at 1, +8.57c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 2 | 1 | +25.7c | +25.7c | 1.47 |

### GEN4_B47

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; held to settlement. Discovery PF1 1.79 n 48; validation PF1 1.33 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.12, at 10 contracts 0.12, at 10 contracts with fees x1.2 0.11; net per contract -41.00c at 1, -40.93c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 1 | 2 | -122.8c | -122.8c | 0.12 |

### GEN4_B48

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm15 >= -0.09 and sp30 >= -2.625; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.70 n 41; validation PF1 1.33 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +33.90c at 1, +35.17c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 3 | 0 | +105.5c | +105.5c | inf |

### GEN4_B49

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; held to settlement. Discovery PF1 2.47 n 55; validation PF1 1.33 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +27.25c at 1, +27.40c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 4 | 0 | +109.6c | +109.6c | inf |

### GEN4_B50

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp15 >= -0.1949 and zd >= -1.214; bought at that ask; held to settlement. Discovery PF1 1.87 n 41; validation PF1 1.31 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 2 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +19.50c at 1, +19.80c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 2 | 2 | 0 | +39.6c | +39.6c | inf |

### GEN4_B51

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0.04 and imb <= 0.4847; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.72 n 50; validation PF1 1.30 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 3 on 1 days; zero-volume trades 0.
PF at 1 contract 0.55, at 10 contracts 0.57, at 10 contracts with fees x1.2 0.56; net per contract -12.73c at 1, -12.00c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 3 | 2 | 1 | -36.0c | -36.0c | 0.57 |

### GEN4_REF_FAV150

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. The unconditional core of 41 of the 51 GEN4 validation passes: buy the favourite (side ask 0.50 to 0.85) at the first poll 150 to 120 s before the close, hold. Discovery PF1 1.61 n 50; validation PF1 1.57 n 35. Shows whether the conditions add anything forward.
Windows evaluated 16 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 4 on 1 days; zero-volume trades 0.
PF at 1 contract 0.23, at 10 contracts 0.23, at 10 contracts with fees x1.2 0.23; net per contract -26.75c at 1, -26.70c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 4 | 2 | 2 | -106.8c | -106.8c | 0.23 |

### REF_L1_GOLD

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T00:00:00Z. The live L1 gold rule as a known baseline: the side whose ask is 0.88 to 0.97 at the candle ending 6 minutes before the close, bought at that ask, held to settlement. Candles only, so it ignores the live 25c exit and the window limit.
Windows evaluated 5 on 1 days; without the data the rule needs 0; evaluator errors 0. Trades 1 on 1 days; zero-volume trades 0.
PF at 1 contract inf, at 10 contracts inf, at 10 contracts with fees x1.2 inf; net per contract +4.30c at 1, +4.90c at 10.

| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |
|---|---|---|---|---|---|---|
| 2026-10-30 | 1 | 1 | 0 | +4.9c | +4.9c | inf |

