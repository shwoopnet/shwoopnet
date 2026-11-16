# SHADOW_CLUSTER_MAP_NOV16 (Desk A, 2026-11-16)

Source: the 190 rules that passed VALIDATE in ENGINE1 run 2 (1c PF 1.3+, 2c PF 1.0+, both halves, n 100+), re-scored with the same audited driver code (reproduces the listing to 1e-9; no new rule tried, m 2,347,488 unchanged). **None is a pass:** BH survivors 0 at m 2.35 million; these are candidates for a log-only forward test, upper bound, not fill-checked. Paper research figures only. Dollars a week = signals a day (validate) x cash edge at 1c per contract x 5 contracts x 7, scaled linearly from the 10 contract cash.

Excluded before clustering: **35 Dogecoin rules** (7e: Dogecoin removed from the bot, any Dogecoin strategy declined). Admission: validate and search signals a day both at least 3 (all 190 met it).

Clustering: near-duplicates merged when same market, same side rule, same exit, entry time within one bucket step (60 s) and price band within one band (5c); the cluster's best by dollars a week represents it. 55 clusters of 155 rules.

Families (cap 5 each): the entry condition kind (plain band, spread filter, momentum or volume filter, open-interest trigger) x the price region bought (cheap tail 5c to 35c, middle 35c to 85c, high 85c+), with the favourite-late shape (price band 17+ and 10 minutes or less left) as its own family, flagged as the closed gold L1 mechanism. Cap 3 per market.

## Picks (ranked by dollars a week at 1c, 5 contracts)

| # | spec | market | side | look (s left) | band | filter | exit | n | signals/day | PF 1c | PF 2c | edge 1c c/ct | edge 2c c/ct | $/wk 1c | $/wk 2c | family | cluster (size) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | SH1_01_HYPE | KXHYPE15M | cheap | 600 | 3 | spread:low | M60 | 139 | 4.79 | 1.84 | 1.67 | 9.73 | 8.25 | 16.3 | 13.8 | spread filter, cheap tail (5c to 35c) | 1 (4) |
| 2 | SH1_02_ETH | KXETH15M | yes | 600 | 16 | none | H | 183 | 6.31 | 1.74 | 1.62 | 6.09 | 5.13 | 13.4 | 11.3 | plain band, middle (35c to 85c) | 2 (4) |
| 3 | SH1_03_ETH | KXETH15M | yes | 660 | 6 | spread:low | M60 | 121 | 4.17 | 1.54 | 1.43 | 9.20 | 7.55 | 13.4 | 11.0 | spread filter, cheap tail (5c to 35c) | 3 (1) |
| 4 | SH1_04_BTC | KXBTC15M | cheap | 180 | 5 | spread:low | H | 149 | 5.14 | 1.37 | 1.30 | 6.84 | 5.82 | 12.3 | 10.5 | spread filter, cheap tail (5c to 35c) | 4 (2) |
| 5 | SH1_05_BTC | KXBTC15M | cheap | 120 | 2 | mom5:down | H | 160 | 5.52 | 1.58 | 1.45 | 6.36 | 5.30 | 12.3 | 10.2 | momentum or volume filter, cheap tail (5c to 35c) | 5 (6) |
| 6 | SH1_06_HYPE | KXHYPE15M | yes | 600 | 3 | oi3:up | M60 | 121 | 4.17 | 1.69 | 1.53 | 8.15 | 6.69 | 11.9 | 9.8 | open-interest trigger, cheap tail (5c to 35c) | 6 (1) |
| 7 | SH1_07_BTC | KXBTC15M | cheap | 120 | 2 | mom5:down | S | 160 | 5.52 | 1.56 | 1.41 | 5.78 | 4.66 | 11.2 | 9.0 | momentum or volume filter, cheap tail (5c to 35c) | 7 (7) |
| 8 | SH1_08_HYPE | KXHYPE15M | cheap | 420 | 1 | oi6:up | M60 | 268 | 9.24 | 1.53 | 1.27 | 3.19 | 1.92 | 10.3 | 6.2 | open-interest trigger, cheap tail (5c to 35c) | 9 (5) |
| 9 | SH1_09_ETH | KXETH15M | yes | 420 | 15 | none | H | 100 | 3.45 | 1.76 | 1.66 | 7.81 | 6.85 | 9.4 | 8.3 | plain band, middle (35c to 85c) | 12 (2) |
| 10 | SH1_10_NEAR | KXNEAR15M | cheap | 420 | 4 | vol3:up | M60 | 107 | 3.69 | 1.44 | 1.32 | 6.22 | 4.74 | 8.0 | 6.1 | momentum or volume filter, cheap tail (5c to 35c) | 13 (1) |
| 11 | SH1_11_SOL | KXSOL15M | favourite | 540 | 16 | vol3:up | S | 122 | 5.45 | 1.33 | 1.21 | 3.31 | 2.20 | 6.3 | 4.2 | momentum or volume filter, middle (35c to 85c) | 20 (1) |
| 12 | SH1_12_GOLD | KXGOLD15M | favourite | 420 | 18 | oi3:up | H | 237 | 8.21 | 1.50 | 1.27 | 2.15 | 1.20 | 6.2 | 3.4 | F1 favourite-late shape | 22 (8) |
| 13 | SH1_13_XRP | KXXRP15M | yes | 540 | 17 | mom3:up | H | 152 | 5.24 | 1.45 | 1.31 | 3.11 | 2.17 | 5.7 | 4.0 | F1 favourite-late shape | 24 (26) |
| 14 | SH1_14_SOL | KXSOL15M | favourite | 480 | 18 | vol3:up | H | 137 | 6.12 | 1.65 | 1.41 | 2.63 | 1.68 | 5.6 | 3.6 | F1 favourite-late shape | 26 (2) |
| 15 | SH1_15_XRP | KXXRP15M | favourite | 360 | 18 | mom1:up | H | 307 | 10.59 | 1.31 | 1.11 | 1.51 | 0.56 | 5.6 | 2.1 | F1 favourite-late shape | 27 (2) |
| 16 | SH1_16_BNB | KXBNB15M | cheap | 420 | 1 | spread:low | M60 | 166 | 5.73 | 1.47 | 1.21 | 2.71 | 1.45 | 5.4 | 2.9 | spread filter, cheap tail (5c to 35c) | 28 (2) |
| 17 | SH1_17_NEAR | KXNEAR15M | yes | 420 | 18 | mom3:up | H | 201 | 6.93 | 1.50 | 1.27 | 2.06 | 1.12 | 5.0 | 2.7 | F1 favourite-late shape | 31 (2) |

Totals: 17 picks; per market {'KXHYPE15M': 3, 'KXETH15M': 3, 'KXBTC15M': 3, 'KXNEAR15M': 2, 'KXSOL15M': 2, 'KXGOLD15M': 1, 'KXXRP15M': 2, 'KXBNB15M': 1}; per family {'spread filter, cheap tail (5c to 35c)': 4, 'plain band, middle (35c to 85c)': 2, 'momentum or volume filter, cheap tail (5c to 35c)': 3, 'open-interest trigger, cheap tail (5c to 35c)': 2, 'momentum or volume filter, middle (35c to 85c)': 1, 'F1 favourite-late shape': 5}.

## Flags (7e and uniqueness; nothing silently dropped)

- **SH1_02_ETH** (KXETH15M plain band, middle (35c to 85c)): Ethereum high-price side: Ethereum as L1 is declined (7e); shadow only
- **SH1_06_HYPE** (KXHYPE15M open-interest trigger, cheap tail (5c to 35c)): open-interest trigger: check against OICORE (cheap side, open interest rise); different market
- **SH1_08_HYPE** (KXHYPE15M open-interest trigger, cheap tail (5c to 35c)): open-interest trigger: check against OICORE (cheap side, open interest rise); different market
- **SH1_09_ETH** (KXETH15M plain band, middle (35c to 85c)): Ethereum high-price side: Ethereum as L1 is declined (7e); shadow only
- **SH1_12_GOLD** (KXGOLD15M F1 favourite-late shape): favourite-late shape (88c-97c class, late look): a duplicate of gold L1 unless it differs; here it differs only by market and exit, so it is flagged, not claimed unique; gold: the gold L1 family and the closed gold variants (maker entries, 94.5c floor) are on 7e; compare before any step beyond shadow
- **SH1_13_XRP** (KXXRP15M F1 favourite-late shape): favourite-late shape (88c-97c class, late look): a duplicate of gold L1 unless it differs; here it differs only by market and exit, so it is flagged, not claimed unique; XRP YES held to settlement: the same mechanism as the retired XRPYES10 (7e: favourite-and-hold ban, XRP declined as an L1 market); shadow only, never live without the owner's named exception
- **SH1_14_SOL** (KXSOL15M F1 favourite-late shape): favourite-late shape (88c-97c class, late look): a duplicate of gold L1 unless it differs; here it differs only by market and exit, so it is flagged, not claimed unique
- **SH1_15_XRP** (KXXRP15M F1 favourite-late shape): favourite-late shape (88c-97c class, late look): a duplicate of gold L1 unless it differs; here it differs only by market and exit, so it is flagged, not claimed unique
- **SH1_17_NEAR** (KXNEAR15M F1 favourite-late shape): favourite-late shape (88c-97c class, late look): a duplicate of gold L1 unless it differs; here it differs only by market and exit, so it is flagged, not claimed unique

## All clusters (representative, size, why not picked if not)

| cluster | market | family | best $/wk 1c | size | picked |
|---|---|---|---|---|---|
| 1 | KXHYPE15M | spread filter, cheap tail (5c to 35c) | 16.3 | 4 | picked |
| 2 | KXETH15M | plain band, middle (35c to 85c) | 13.5 | 4 | picked |
| 3 | KXETH15M | spread filter, cheap tail (5c to 35c) | 13.4 | 1 | picked |
| 4 | KXBTC15M | spread filter, cheap tail (5c to 35c) | 12.3 | 2 | picked |
| 5 | KXBTC15M | momentum or volume filter, cheap tail (5c to 35c) | 12.3 | 6 | picked |
| 6 | KXHYPE15M | open-interest trigger, cheap tail (5c to 35c) | 11.9 | 1 | picked |
| 7 | KXBTC15M | momentum or volume filter, cheap tail (5c to 35c) | 11.2 | 7 | picked |
| 8 | KXBTC15M | plain band, middle (35c to 85c) | 10.9 | 2 | market cap 3 |
| 9 | KXHYPE15M | open-interest trigger, cheap tail (5c to 35c) | 10.3 | 5 | picked |
| 10 | KXHYPE15M | plain band, cheap tail (5c to 35c) | 9.6 | 1 | market cap 3 |
| 11 | KXBTC15M | plain band, cheap tail (5c to 35c) | 9.6 | 3 | market cap 3 |
| 12 | KXETH15M | plain band, middle (35c to 85c) | 9.4 | 2 | picked |
| 13 | KXNEAR15M | momentum or volume filter, cheap tail (5c to 35c) | 8.0 | 1 | picked |
| 14 | KXETH15M | spread filter, middle (35c to 85c) | 7.8 | 1 | market cap 3 |
| 15 | KXBTC15M | momentum or volume filter, cheap tail (5c to 35c) | 7.4 | 1 | market cap 3 |
| 16 | KXETH15M | F1 favourite-late shape | 7.4 | 8 | market cap 3 |
| 17 | KXBTC15M | F1 favourite-late shape | 6.9 | 1 | market cap 3 |
| 18 | KXBTC15M | F1 favourite-late shape | 6.9 | 2 | market cap 3 |
| 19 | KXETH15M | F1 favourite-late shape | 6.4 | 1 | market cap 3 |
| 20 | KXSOL15M | momentum or volume filter, middle (35c to 85c) | 6.3 | 1 | picked |
| 21 | KXETH15M | F1 favourite-late shape | 6.2 | 1 | market cap 3 |
| 22 | KXGOLD15M | F1 favourite-late shape | 6.2 | 8 | picked |
| 23 | KXETH15M | F1 favourite-late shape | 5.8 | 1 | market cap 3 |
| 24 | KXXRP15M | F1 favourite-late shape | 5.7 | 26 | picked |
| 25 | KXBTC15M | momentum or volume filter, cheap tail (5c to 35c) | 5.7 | 1 | market cap 3 |
| 26 | KXSOL15M | F1 favourite-late shape | 5.6 | 2 | picked |
| 27 | KXXRP15M | F1 favourite-late shape | 5.6 | 2 | picked |
| 28 | KXBNB15M | spread filter, cheap tail (5c to 35c) | 5.4 | 2 | picked |
| 29 | KXETH15M | F1 favourite-late shape | 5.3 | 3 | market cap 3 |
| 30 | KXBTC15M | momentum or volume filter, cheap tail (5c to 35c) | 5.3 | 2 | market cap 3 |
| 31 | KXNEAR15M | F1 favourite-late shape | 5.0 | 2 | picked |
| 32 | KXWTI15M | F1 favourite-late shape | 4.7 | 1 | family cap 5 |
| 33 | KXXRP15M | F1 favourite-late shape | 4.7 | 1 | family cap 5 |
| 34 | KXBTC15M | F1 favourite-late shape | 4.7 | 5 | market cap 3 |
| 35 | KXBTC15M | momentum or volume filter, cheap tail (5c to 35c) | 4.5 | 6 | market cap 3 |
| 36 | KXXRP15M | F1 favourite-late shape | 4.5 | 1 | family cap 5 |
| 37 | KXBNB15M | F1 favourite-late shape | 4.4 | 1 | family cap 5 |
| 38 | KXXRP15M | F1 favourite-late shape | 4.3 | 7 | family cap 5 |
| 39 | KXGOLD15M | F1 favourite-late shape | 4.2 | 7 | family cap 5 |
| 40 | KXETH15M | F1 favourite-late shape | 4.1 | 1 | market cap 3 |
| 41 | KXSOL15M | F1 favourite-late shape | 4.1 | 1 | family cap 5 |
| 42 | KXETH15M | F1 favourite-late shape | 4.0 | 1 | market cap 3 |
| 43 | KXXRP15M | F1 favourite-late shape | 4.0 | 1 | family cap 5 |
| 44 | KXZEC15M | F1 favourite-late shape | 3.7 | 1 | family cap 5 |
| 45 | KXHYPE15M | momentum or volume filter, cheap tail (5c to 35c) | 3.7 | 1 | market cap 3 |
| 46 | KXSOL15M | F1 favourite-late shape | 3.6 | 1 | family cap 5 |
| 47 | KXBTC15M | momentum or volume filter, cheap tail (5c to 35c) | 3.6 | 2 | market cap 3 |
| 48 | KXWTI15M | F1 favourite-late shape | 3.5 | 1 | family cap 5 |
| 49 | KXSOL15M | F1 favourite-late shape | 3.2 | 1 | family cap 5 |
| 50 | KXWTI15M | F1 favourite-late shape | 3.2 | 3 | family cap 5 |
| 51 | KXSILVER15M | F1 favourite-late shape | 3.0 | 1 | family cap 5 |
| 52 | KXETH15M | momentum or volume filter, cheap tail (5c to 35c) | 2.8 | 1 | market cap 3 |
| 53 | KXGOLD15M | F1 favourite-late shape | 2.8 | 1 | family cap 5 |
| 54 | KXBTC15M | F1 favourite-late shape | 2.7 | 4 | market cap 3 |
| 55 | KXGOLD15M | F1 favourite-late shape | 2.4 | 1 | family cap 5 |
