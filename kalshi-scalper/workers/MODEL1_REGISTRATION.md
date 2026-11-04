# MODEL1 registration: a pooled, price-matched model of the CHEAP side (2026-11-04)

Registered before any outcome of the test split (or of the train split, in this file's commit) was touched. Discovery only: no live code, no `functions/`, no L1, no OICORE, no promote verb. **Owner rule (strict): CHEAP SIDE ONLY, ask 3c to 30c.** No entry above 0.30 is built, counted, scored or printed (the code asserts it); no favourite-side result is computed; no 15 minute crypto or gold candle trigger.

## Duplicate check
README and workers searched for logistic, gradient, boosted, model, enrichment, CALIB1, LIQ1, OVERROUND1, RULES1B, STRESSDAY1, AUDIT1, POWER1 and OICORE_SHAPE_INVENTORY. Pooled logistic models exist only on the 88c to 97c FAVOURITE band (TREE2/FEAT1/FEAT2/FEAT3, 15 minute crypto and gold); on the cheap side the conditioners were run ONE AT A TIME (CALIB1 ask by category, OVERROUND1 tercile, LIQ1 spread and volume, USWEEP/NEWLIST1 look). AUDIT1 found no enrichment table. No cheap-side pooled multi-feature model has been run. Not a duplicate. Changed against LIQ1: a joint model, price-matched by construction (the ask and its log odds are features and the decision is model probability minus ask), a fixed out-of-fit test and a permutation baseline.

## Hypothesis and mechanism
Each of the single conditioners ranks the loss with quote quality (tight spread -2.8c, wide -10.0c; low overround -1.6c, high -7.5c; Sports near break-even) but is confounded with the ask level and with each other. If any region of cheap entries is fairly priced or underpriced, a joint model that separates price from quality should find it; if the cheap side loses to its price everywhere (the working belief: the favourite-longshot premium plus the fee), the model's probabilities will track the ask and select nothing that wins.

## Data (no new fetch)
The LIQ1 feature table (`/tmp/.../liq1/features.jsonl`, rebuilt by `python3 -m scalper.liq1_spread extract`; 16,201 cheap entries of the CALIB1 development caches USWEEP1/2/3 and `data/newlist1.sqlite`), results from `res.json`, and the OVERROUND1 structure (event overround where the registered B/T bracket structure exists, structure only). **Frozen third: every row whose market closes at or after 2026-10-03T16:00Z (1791043200) is DROPPED in `load_rows`**, which removes 9,679 of the 16,201 rows (those caches' own development dates run to Oct 29, later than this study's frozen cut; I apply the stricter cut and say so). Pool after the cut: **6,522 rows, 1,953 events**.

## Features (all known at the look; no outcome)
ask; log odds of the ask; quote spread in cents; log(1 + candle volume); volume-zero flag; log(1 + minutes to close at the look) with a missing flag (age looks A1h/A3h/A6h have none, 22.9% of rows); event overround with a missing flag (missing on 71.6% of rows); side bought (yes); category one-hot (a category with at least 100 TRAIN rows, else "other"); life class D/W/H; entry look; series one-hot (at least 200 TRAIN rows, else "other"). Standardisation and the category and series lists are fitted on TRAIN rows only. Missing rate of spread and volume: 0 (volume 52.9% zero).

## Split (fixed here; events ordered by earliest close time, ties by event id)
- **Train** = first two thirds of events (1,302 events, 4,203 rows). **Test** = last third (651 events, 2,319 rows; closes 2026-09-24 to 2026-10-03). The test third is touched once, by `score`.
- **Inner selection** inside train, time ordered: the first 3/4 of train events fit, the last 1/4 validates by log loss; the hyperparameter with the lowest validation log loss is then refit on ALL train. No hyperparameter is tuned on the test.
- The `fit` stage loads train outcomes only; test outcomes are not attached until `score`, and `fit` prints the number of selected TEST trades from the test FEATURES alone.

## Models (hyperparameters registered)
1. **Logistic**, L2 penalty on the squared weights of the standardised features (intercept unpenalised), Newton steps; penalty lambda in {0.1, 1, 10, 100}.
2. **Gradient-boosted shallow trees** (own numpy code, log loss, Newton leaves, 32 quantile bins, learning rate 0.1, minimum leaf 100 rows, leaf L2 10): depth in {2, 3} x trees in {50, 150}.

## Decision rule (fixed before scoring)
Take an entry when model probability minus ask EXCEEDS the margin **m = 2c** or **m = 4c**; held to settlement, one contract basis (C = 10 fee, 7% x p x (1-p) rounded up to the cent per 10 contracts), at most **2 per event** (largest margin first, ties by md5(market|look)). Reported per model and margin: n, events, win vs price, net after fee with an event-cluster bootstrap 95% (2,000 draws, seed 20261104), PF, each test half (events by close time), and the calibration of model probability vs outcome on all test rows (deciles). Control: every test row.

## Permutation baseline
Outcomes are shuffled **within the five CALIB1 ask buckets across train and test together** (row level, so event clustering is not preserved: this null is somewhat narrower than the true one, which only makes a claim harder). The pipeline is refit with the chosen hyperparameters on the shuffled train outcomes and applied to the test features; the statistic is the mean net of the selected test trades, scored on the shuffled test outcomes (a permutation selecting under 20 trades does not exceed). B = 500 (logistic) and 200 (trees). p = (exceedances + 1)/(B + 1) for the observed mean net. The grid's hyperparameter selection is not repeated inside permutations (disclosed).

## Prediction (before any score)
Model probabilities track the ask within about 1c on the test, the margin rule selects a few hundred trades at 2c and far fewer at 4c, the selected trades win less than they cost (net -2c to -8c, PF 0.3 to 0.9), and the permutation p is above 0.3. FALSIFIED about 80%, NOT_ENOUGH_DATA at the 4c margin or for trees about 50%. A pass under 1%.

## Kill and verdict rules
- **NOT_ENOUGH_DATA**: under 150 selected test trades (a margin and model with fewer is reported as such with its numbers, not scored further). If the `fit` stage shows under 150 selected test trades at m = 2c for BOTH models, the study stops there as NOT_ENOUGH_DATA and `score` is not run.
- **FALSIFIED**: test mean net after fees not above 0, or PF under 1.5.
- **LEAD**: needs mean net above 0, PF at least 1.5, both test halves positive, and permutation p under 0.01. A LEAD is only a place to look with a registered forward test on data after the cut; it is not a trading rule.
- The score is read once (`score` refuses a second run).

## N
2 models x 2 margins = 4 tries, +2 each = **N +8**. Hyperparameter grids are selected on the inner split and charged nothing further.

## Disclosures
Cached data only (no Kalshi fetch). The table's looks are the caches' own, so entries from one market at different looks are separate rows (capped by the 2 per event rule). Overround is available on 28% of rows (weather and similar B/T ladders) so the model cannot use it elsewhere. Code `src/scalper/model1.py`, tests `tests/test_model1.py` (synthetic data only).
