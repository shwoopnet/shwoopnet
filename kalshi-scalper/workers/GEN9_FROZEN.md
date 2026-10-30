# GEN9 frozen discovery results (pushed before any validation row is built)

## Gold (KXGOLD15M), frozen 2026-10-30 11:20 UTC

Fetch: all 3,072 sampled gold markets (1 returned no trades), 1,704 discovery windows on 23 days, 141,121 rows. 23,272 draws to 5,000 distinct. Median discovery PF 0.24, 95th percentile 0.46; 4,151 distinct at screen size, none with PF 1.0 or more (best 0.845). **0 survivors.** Gold is `FALSIFIED` at discovery; validation is read once only for the family control and, as information, the best 10.

- `workers/GEN9_frozen_gold.json` (0 survivors): sha256 951c20a23a0068ee8a361d21b56f732317297f8046daa58e592caa6cd5c129bd
- `data/gen9/gold_controls.json` (4,151 controls, not committed): sha256 b48e20fc20afab3bcf415905e988239767399d53c76284401493e50b60f554e7
- `data/gen9/gold_distinct.json` (not committed): sha256 478a6adc87e40223e57ac6117cb8e46637facc3a14fb70a4701fcb9eca81b2f3

## Bitcoin (KXBTC15M)

Pending: the fetch runs to its 6 hour budget (no new market after about 13:47 UTC).
