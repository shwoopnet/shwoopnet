# GEN9 frozen discovery results (pushed before any validation row is built)

## Gold (KXGOLD15M), frozen 2026-10-30 11:20 UTC

Fetch: all 3,072 sampled gold markets (1 returned no trades), 1,704 discovery windows on 23 days, 141,121 rows. 23,272 draws to 5,000 distinct. Median discovery PF 0.24, 95th percentile 0.46; 4,151 distinct at screen size, none with PF 1.0 or more (best 0.845). **0 survivors.** Gold is `FALSIFIED` at discovery; validation is read once only for the family control and, as information, the best 10.

- `workers/GEN9_frozen_gold.json` (0 survivors): sha256 951c20a23a0068ee8a361d21b56f732317297f8046daa58e592caa6cd5c129bd
- `data/gen9/gold_controls.json` (4,151 controls, not committed): sha256 b48e20fc20afab3bcf415905e988239767399d53c76284401493e50b60f554e7
- `data/gen9/gold_distinct.json` (not committed): sha256 478a6adc87e40223e57ac6117cb8e46637facc3a14fb70a4701fcb9eca81b2f3

## Bitcoin (KXBTC15M), frozen 2026-10-30 13:54 UTC

Fetch stopped at the 6 hour budget (both streams finished at about 13:48 UTC): 1,004 of 3,983 sampled Bitcoin markets (a front prefix and a tail suffix of the seeded order), 558 discovery windows on 23 days (above the 300-window, 15-day minimum, so searched), 48,206 rows. 27,783 draws to 5,000 distinct. Median discovery PF 0.25, 95th percentile 0.53; 2,795 distinct at screen size, none with PF 1.0 or more (best 0.979). **0 survivors.** Bitcoin is `FALSIFIED` at discovery; validation is read once only for the family control and, as information, the best 10.

- `workers/GEN9_frozen_btc.json` (0 survivors): sha256 d6fb6d55478f347d649c9e629338864aa081c06694814de879fd01644719bd4f
- `data/gen9/btc_controls.json` (2,795 controls, not committed): sha256 9a564e2582b70081d7c44e2235e4bc5e3b1979783197f1e8b8bb39a0a8733f4f
- `data/gen9/btc_distinct.json` (not committed): sha256 95ad87a096689565123feb0c55f751ef8f1ae915c41f4581aae8986e42653c4c

Gold's validation was read once at 2026-10-30 about 11:25 UTC, after the gold freeze above was pushed (commit 620b6ed).
