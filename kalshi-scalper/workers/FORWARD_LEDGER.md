# FORWARD LEDGER (automatic; research only)

Written by `python -m scalper.fwdledger run` (once per AUTO pass, `scalper.autoscore check`). Last updated 2026-10-30 00:17 UTC.
Forward evidence counts only windows that CLOSED after a candidate's freeze time, had the data its rule needs and have settled.
Fees 7% x C x p x (1-p) rounded up to the cent per order, at 1 and 10 contracts; held to settlement pays the entry fee only. Win = net at 10 contracts above zero. Net per contract is at 10 contracts. Trades per week: forward trades over the time from the freeze to the last evaluated close.
This ledger never promotes anything. READY FOR THE FALSIFIER means only: forward PF 1.5+ at 1 and at 10 contracts on 30+ trades over 10+ trade days. It earns a falsifier read, nothing more. How a generator adds a candidate: `workers/candidates/README.md`.

| id | market | stage | freeze | fwd days | trades | wins | losses | PF 1c | PF 10c | net/contract | trades/week | updated | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GEN6_B01 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B02 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B03 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B04 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B05 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B06 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B07 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B08 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B09 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B10 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B11 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B12 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN6_B13 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| REF_BTC_UNDERDOG_180 | KXBTC15M | reference | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| REF_GOLD_UNDERDOG_180 | KXGOLD15M | reference | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| REF_LATECAL_BTC | KXBTC15M | reference | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B01 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B02 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B03 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B04 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B05 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B06 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B07 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B08 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B09 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B10 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B11 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B12 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B13 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B14 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B15 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B16 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B17 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B18 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B19 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B20 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B21 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B22 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B23 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B24 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B25 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B26 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B27 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B28 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B29 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B30 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B31 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B32 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B33 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B34 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B35 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B36 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B37 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B38 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B39 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B40 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B41 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B42 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B43 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B44 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B45 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B46 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B47 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B48 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B49 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B50 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_B51 | KXBTC15M | validation | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| GEN4_REF_FAV150 | KXBTC15M | reference | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |
| REF_L1_GOLD | KXGOLD15M | reference | 2026-10-30 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | +0.00c | 0.0 | 2026-10-30 00:17 UTC |  |

## History per candidate

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

### REF_GOLD_UNDERDOG_180

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. Gold version of REF_BTC_UNDERDOG_180: FALS3 found gold favourites at 50c to 85c, 2 to 3 minutes before the close, also below break-even (PF 0.85). Buy the cheap side whose ask is 15c to 49c at the candle ending 180 s before the close, held. Forward days only. 1 try.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_LATECAL_BTC

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T01:00:00Z. LATECAL's one chosen cell (Bitcoin, 90 to 60 s left, ask 0.95 to 0.98: 61 of 61 won on the recorder, NOT_ENOUGH_DATA; needs about 800 windows to clear the 97.7% break-even) tracked forward. Candles only: the nearest candle is the one ending 60 s before the close, so this approximates the recorder's 90 to 60 s cell. L1-family, held to settlement.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B01

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and zd >= -1.585; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.13 n 46; validation PF1 2.64 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B02

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and zd >= -2.066; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 2.09 n 51; validation PF1 2.40 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B03

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and sp15 >= -0.1949 and zd >= -0.3503; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.62 n 40; validation PF1 2.39 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B04

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.17 and lsz_ask <= 8.072 and lsz_bid <= 8.053; bought at that ask; held to settlement. Discovery PF1 2.04 n 41; validation PF1 2.27 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B05

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 41; validation PF1 2.18 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B06

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= 0.5295 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.54 n 52; validation PF1 2.08 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B07

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= 0.3412 and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.68 n 43; validation PF1 2.08 n 24 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B08

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.24 n 52; validation PF1 1.99 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B09

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 >= -0.06831; bought at that ask; held to settlement. Discovery PF1 1.51 n 49; validation PF1 1.94 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B10

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp30 <= 2.256 and sp5 <= 0.353; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.79 n 46; validation PF1 1.93 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B11

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp30 >= 0.5295; bought at that ask; held to settlement. Discovery PF1 1.50 n 46; validation PF1 1.91 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B12

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.16 and lsz_ask <= 7.779 and sp5 >= 0.1732; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.32 n 43; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B13

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.65 n 56; validation PF1 1.90 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B14

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and lsz_ask <= 7.779; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.30 n 44; validation PF1 1.90 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B15

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.26 and sp15 >= -0.01237 and spread >= 0.001; bought at that ask; held to settlement. Discovery PF1 1.55 n 42; validation PF1 1.86 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B16

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 7.779 and spread <= 0.01; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.14 n 48; validation PF1 1.83 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B17

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.4847 and zd >= -2.066; bought at that ask; held to settlement. Discovery PF1 1.52 n 48; validation PF1 1.82 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B18

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and lsz_ask <= 7.779 and zd >= -0.6765; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.63 n 43; validation PF1 1.81 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B19

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and imb >= -0.6701; bought at that ask; held to settlement. Discovery PF1 1.78 n 48; validation PF1 1.81 n 33 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B20

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and imb >= -0.4281 and sp5 <= 0; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.66 n 43; validation PF1 1.77 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B21

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb <= 0.902 and lsz_bid >= 7.292; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.54 n 44; validation PF1 1.76 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B22

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.456 and lsz_bid >= 6.195; bought at that ask; held to settlement. Discovery PF1 1.63 n 49; validation PF1 1.73 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B23

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; held to settlement. Discovery PF1 1.55 n 40; validation PF1 1.71 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B24

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 30 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.292; bought at that ask; held to settlement. Discovery PF1 2.01 n 50; validation PF1 1.65 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B25

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.00 n 40; validation PF1 1.64 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B26

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.36 and lsz_bid >= 5.465; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.57 n 49; validation PF1 1.63 n 35 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B27

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and vol <= 0.311; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.52 n 40; validation PF1 1.63 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B28

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0 and lsz_ask <= 7.388; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.92 n 40; validation PF1 1.61 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B29

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.1233; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.26 n 51; validation PF1 1.61 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B30

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask >= 7.388 and sp15 >= -0.9017 and sp30 <= 2.256; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.78 n 45; validation PF1 1.61 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B31

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid <= 8.422; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.71 n 55; validation PF1 1.59 n 38 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B32

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.95 n 40; validation PF1 1.57 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B33

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and spread >= 0.001 and vol <= 0.311; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.59 n 40; validation PF1 1.54 n 28 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B34

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 6.824 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 1.83 n 52; validation PF1 1.54 n 41 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B35

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= 0 and sp15 >= 1.584 and spread <= 0.01; bought at that ask; held to settlement. Discovery PF1 2.38 n 41; validation PF1 1.52 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B36

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.459; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.83 n 40; validation PF1 1.52 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B37

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side NO; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm30 <= 0.17 and sp5 >= 0.353 and spread >= 0.001; bought at that ask; sold at the side's bid at 30 s left (held if no bid). Discovery PF1 1.52 n 43; validation PF1 1.49 n 39 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B38

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 <= 0.0315; bought at that ask; held to settlement. Discovery PF1 1.50 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B39

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.01237; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.44 n 55; validation PF1 1.46 n 40 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B40

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.9734; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 1.57 n 55; validation PF1 1.44 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B41

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_bid >= 7.733 and spread >= 0.01; bought at that ask; held to settlement. Discovery PF1 1.52 n 43; validation PF1 1.43 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B42

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side DOG; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 >= -0.07 and imb >= -0.9734 and sp15 >= 1.584; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 2.23 n 41; validation PF1 1.42 n 31 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B43

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.75 n 48; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B44

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp5 >= 0.353; bought at that ask; held to settlement. Discovery PF1 2.35 n 51; validation PF1 1.38 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B45

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and ask >= 0.0742 and lsz_bid >= 6.824; bought at that ask; sold at the side's bid at 15 s left (held if no bid). Discovery PF1 2.02 n 47; validation PF1 1.37 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B46

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 20 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and bid >= 0.11 and lsz_ask <= 7.388; bought at that ask; held to settlement. Discovery PF1 2.64 n 45; validation PF1 1.34 n 34 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B47

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 60 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and lsz_ask <= 8.072; bought at that ask; held to settlement. Discovery PF1 1.79 n 48; validation PF1 1.33 n 37 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B48

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 120 to 10 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm15 >= -0.09 and sp30 >= -2.625; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.70 n 41; validation PF1 1.33 n 32 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B49

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 45 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and sp15 >= -0.1949; bought at that ask; held to settlement. Discovery PF1 2.47 n 55; validation PF1 1.33 n 42 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B50

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 120 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and imb >= -0.4281 and sp15 >= -0.1949 and zd >= -1.214; bought at that ask; held to settlement. Discovery PF1 1.87 n 41; validation PF1 1.31 n 30 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_B51

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. Bitcoin 15 minute, recorder quotes. Side FAV; first poll with 150 to 90 s left, side ask 0.03 to 0.85, at least 1 contract at the ask, and dm5 <= 0.04 and imb <= 0.4847; bought at that ask; sold at the side's bid at 5 s left (held if no bid). Discovery PF1 1.72 n 50; validation PF1 1.30 n 36 on 3 dates. Passed the GEN4 screens only; not a candidate in the owner's sense.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### GEN4_REF_FAV150

Evaluator `scalper.gen4:evaluate`, source `quotes`, frozen 2026-10-30T00:00:00Z. The unconditional core of 41 of the 51 GEN4 validation passes: buy the favourite (side ask 0.50 to 0.85) at the first poll 150 to 120 s before the close, hold. Discovery PF1 1.61 n 50; validation PF1 1.57 n 35. Shows whether the conditions add anything forward.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

### REF_L1_GOLD

Evaluator `scalper.fwdeval:l1_like`, source `candles`, frozen 2026-10-30T00:00:00Z. The live L1 gold rule as a known baseline: the side whose ask is 0.88 to 0.97 at the candle ending 6 minutes before the close, bought at that ask, held to settlement. Candles only, so it ignores the live 25c exit and the window limit.
Windows evaluated 0 on 0 days; without the data the rule needs 0; evaluator errors 0. Trades 0 on 0 days; zero-volume trades 0.
PF at 1 contract 0.00, at 10 contracts 0.00, at 10 contracts with fees x1.2 0.00; net per contract +0.00c at 1, +0.00c at 10.

No forward trades yet.

