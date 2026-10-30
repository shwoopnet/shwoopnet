# GEN6 result (2026-10-30): late-window underdog generator. Gold FALSIFIED; Bitcoin 13 rules sent to FORWARD, 7 of them one bet

Registration `workers/GEN6_REGISTRATION.md` (commit b8e514d, pushed before any row was built). Survivors frozen in `workers/GEN6_FROZEN.md` (commit 5ee454a, sha256 btc 0b0b8e4b..., gold 2acb19e6...; control lists hashed there too) before any validation row was built. Validation read once. Code `src/scalper/gen6.py`. Fills at the next candle's closing ask (gates; at the 60 s look the signal ask + 2c), C = 10, fee rounded up per order.

## Funnel

| | Bitcoin | Gold |
|---|---|---|
| Discovery windows / days (Aug 6 to Sep 20) | 4,357 / 46 | 3,192 / 45 |
| Validation windows / days | 3,512 / 37 (Sep 21 to Oct 27) | 2,620 / 34 (Sep 21 to Oct 29) |
| Generated (all in N) | 30,890 | 31,251 |
| rejected: exit not allowed for the look range / under 30 trades / REV1 or REF duplicate / duplicate | 21,337 / 1,096 / 34 / 3,423 | 21,637 / 1,011 / 14 / 3,589 |
| Distinct | 5,000 | 5,000 |
| Discovery PF over all distinct: median / 95th pct | 0.96 / 1.56 | 0.73 / 1.12 |
| Distinct at screen size (100+ trades, 15+ days) | 3,906 | 3,776 |
| Passed discovery (PF 1.5, size, zero volume 20% or less) | 128 | 10 |
| Passed validation (PF 1.3, 50+ trades, stress PF above 1.0) | **13 (10.2%)** | **0** |
| Family control: discovery failures at size passing the same validation screen | 103 of 3,778 (2.7%) | 6 of 3,766 (0.2%) |
| Control rule (survivors at least control + 5 points) | **met** (+7.4 points) | not met (0 survivors) |

No entry or exit in any row below fell on a zero-volume candle. N added: 30,890 + 31,251 draws + 21 information looks (base cores below) = **62,162**; running count about **563,336**, Bonferroni z bar about **5.22**.

## Every validation survivor (all Bitcoin; PF at C = 10)

Side, look range (seconds left), conditions, exit. `doi` = open interest change over the 3 minutes to the signal candle; 86,300 contracts is its discovery 90th percentile.

| id | rule | Disc PF (n, z) | Val PF (n, days) | Val C=1 / stress / signal fill | Val z | Trades/week |
|---|---|---|---|---|---|---|
| B01 | YES 180, doi > 86.3k, m3 > -0.25; TP +20c else hold | 2.81 (104, 4.41) | **1.90** (164, 36) | 1.77 / 1.87 / 1.61 | 3.31 | 31 |
| B02 | both 180, hour <= 21, gold d2 <= 0.046, doi > 86.3k; TP +8c else sell at 60 s | 2.42 (106, 2.65) | **1.80** (133, 27) | 1.53 / 1.75 / 1.45 | 2.49 | 25 |
| B03 | both 180, doi > 86.3k; TP +5c, stop -20c, else hold | 2.41 (222, 5.40) | **1.73** (333, 37) | 1.59 / 1.69 / 1.57 | 3.44 | 63 |
| B04 | both 180, doi > 86.3k, ETH spread <= 2c, rng5 > 0.14; TP +20c else hold | 2.06 (175, 3.38) | **1.68** (269, 37) | 1.58 / 1.65 / 1.56 | 4.05 | 51 |
| B05 | NO 180, d3 <= -0.08, m1 <= 0, vol <= 111k; TP +20c else sell at 60 s | 1.60 (172, 2.03) | **1.66** (58, 26) | 1.43 / 1.61 / 1.35 | 1.36 | 11 |
| B06 | YES 180, d1 <= 0.10, doi > 86.3k; TP +8c else hold | 3.51 (111, 5.37) | **1.57** (162, 36) | 1.46 / 1.55 / 1.35 | 2.07 | 31 |
| B07 | YES 240 to 180, m3 > -0.08, m5 <= -0.24; TP +8c else hold | 1.72 (137, 2.30) | **1.45** (90, 32) | 1.35 / 1.42 / 1.22 | 1.28 | 17 |
| B08 | both 240 to 180, rng5 <= 0.273, doi > 86.3k; hold | 2.14 (205, 3.33) | **1.43** (316, 37) | 1.36 / 1.41 / 1.30 | 2.06 | 60 |
| B09 | NO 180, vol <= 128k, m1 <= -0.05; TP +3c, stop -20c, else sell at 60 s | 1.55 (192, 1.54) | **1.42** (86, 31) | 1.25 / 1.38 / 0.98 | 1.32 | 16 |
| B10 | both 240 to 180, doi > 86.3k; hold | 2.19 (433, 5.04) | **1.41** (587, 37) | 1.34 / 1.40 / 1.35 | 2.95 | 111 |
| B11 | NO 180, ask <= 0.19, ETH spread <= 0.3c, d1 <= -0.05; TP +5c, stop -5c, else hold | 1.82 (110, 1.87) | **1.37** (93, 33) | 1.14 / 1.33 / 0.79 | 0.75 | 18 |
| B12 | YES 180, rng5 > 0.32, hour > 19 UTC; TP +8c else hold | 1.83 (102, 2.34) | **1.32** (72, 30) | 1.25 / 1.30 / 0.98 | 1.03 | 14 |
| B13 | NO 180, m1 > -0.2, hour > 19 UTC; TP +8c, stop -20c, else hold | 1.70 (173, 2.55) | **1.31** (129, 36) | 1.24 / 1.29 / 1.20 | 1.22 | 24 |

Best gold survivor at validation: NO 240, spread > 1c, BTC 2 minute move against <= -0.025, hold: discovery 1.77 (137), validation 2.56 on only **26** trades (fails the 50 trade gate); the other nine 0.50 to 0.93. Gold's median discovery PF of 0.73 says the cheap side at 4 to 1 minutes left loses about a quarter of its stake there.

## Distinct bets, or one rule with filters?

**Mostly one rule.** 7 of the 13 (B01, B02, B03, B04, B06, B08, B10) contain the same condition, `doi > 86,300`, at the 180 s look (B08 and B10 also allow 240 s). Their bases without any condition are flat (validation PF 0.82 to 1.02). The core alone, scored once as information (not a survivor, never drawn):

| `doi > 86,300`, both sides, held | discovery PF (n, z) | validation PF (n, z) |
|---|---|---|
| look 240 s | 2.34 (328, 4.46) | 1.38 (434, 2.48) |
| **look 180 s** | **2.28 (222, 4.41)** | **1.85 (333, 4.53)** |
| look 120 s | 0.80 (173, -0.89) | 1.03 (268, 0.15) |
| look 60 s | 0.68 (95, -1.24) | 0.65 (156, -2.01) |
| no condition, 180 s (the base) | 1.18 (2,431, 2.67) | 1.01 (1,863, 0.19) |

The other conditions in the 7 change little: their validation PFs sit around the core's 1.85 at 180 s. At 180 s the core held in every third of each stage (discovery 2.23 / 2.94 / 1.81, validation 2.49 / 1.59 / 1.66), on both sides (validation YES 1.97, NO 1.72), and it does not hang on a few trades (B03 without its best 3 trades: 1.62). The other 6 survivors (B05, B07, B09, B11, B12, B13) are path or hour filters on bases with validation PF 0.81 to 1.02, discovery-to-validation shrinkage of 0.1 to 0.5, and z 0.75 to 1.36. Read them as the 2.7% control rate plus a little: likely noise.

**Hypothesis for the doi core, untested:** a jump in open interest 3 to 6 minutes before the close means a wave of new contracts. The likeliest source is late favourite buyers (bots that buy the near-certain side, like L1, which buys at 6 and 10 minutes). Their buying pushes the cheap side under its fair price, and FALS3's favourite overpricing would be largest in those windows. A cheap check of this (1 try): the favourite at 180 s conditioned on doi > 86.3k should be WORSE than FALS3's 0.77. It was not run here.

## Caveats (they point both ways)

- **The threshold is an absolute count, and open interest grows.** The 90th percentile of doi at 180 s rose from 83k in discovery to 112k in validation, so the rule fired more often later (222 entries, then 333). In forward it will fire more again, and on a different mix of windows.
- **Fill realism.** 34% to 42% of the doi entries filled below 5c. On fills at 5c or more, PF is still 1.39 to 1.90, but candles do not show the size at the ask. R6 (from Oct 29) records 5 levels with sizes, so a forward check of fill size is possible. FALS3's lesson applies: a minute candle's closing quote matches the recorder about 5 s after its end.
- The next-candle fill was often BETTER than the signal fill for doi rules (B03: 1.73 against 1.57). The cheap side kept getting cheaper over the next minute and still won.
- **Not a clean validation of the base:** FALS3 read the favourite side at 180 and 120 s on all 85 days. The doi condition, though, had never been read.
- The best day-clustered validation z is **4.05** (B04), against a bar of 5.22. The core's 4.53 is an information look, not a survivor.

## Verdicts

- **Gold: FALSIFIED** (0 of 10 discovery survivors passed validation; family control not met).
- **Bitcoin: 13 rules NOT_YET_FALSIFIED at the GEN6 screens** and sent to FORWARD as `workers/candidates/GEN6_B01.json` to `GEN6_B13.json` (stage validation, freeze 2026-10-30T02:00:00Z, evaluator `scalper.gen6:forward_eval`). The family control rule is met (10.2% against 2.7%). Against the RULES bar all 13 are **NOT_ENOUGH_DATA**: two windows only, and z below 5.22. Parity check: `forward_eval` against the history scorer on all 3,512 validation windows for all 13 rules gave **0 mismatches** in 45,656 checks (`python -m scalper.gen6 parity btc`). The ledger loads them (first run: 0 forward trades, as expected).
- **Prediction check.** Bitcoin: 128 discovery survivors (predicted 100 to 400, right). Validation pass rate 10% (predicted 25% to 45%, lower). Control rule met (predicted not met; wrong in the strategy's direction, and the reason is one shared condition, as with GEN4). Gold: 10 discovery survivors (predicted 30 to 150, fewer), 0 validation passes (predicted 10% to 25%), control not met (right).

## For the lead

- The doi core at 180 s (both sides, held, no other condition) is the bet. If one forward row is wanted for it rather than 7 filtered relatives, it needs a new id with its own freeze; it was not added here because it did not come out of the grammar's draws.
- The mechanism check above (favourite at 180 s given doi) would cost 1 try and would make the counterparty concrete.
- It is an underdog buy, not a favourite buy, so it sits outside the owner's ban on buying the favourite and holding. It does sit at the same minute as REV1 and REF_BTC_UNDERDOG_180, with which its entries partly overlap (the REV1 and REF Jaccard rejection applied only to the HOLD exits).

## Files

`src/scalper/gen6.py`, `workers/GEN6_REGISTRATION.md`, `workers/GEN6_FROZEN.md`, `workers/GEN6_frozen_btc.json`, `workers/GEN6_frozen_gold.json`, `workers/candidates/GEN6_B01.json` to `GEN6_B13.json`, this file. Row and validation files in `data/gen6_*` (not committed).
