# MODEL1 result (2026-11-04): NOT_ENOUGH_DATA (0 and 14 selected test trades of 150 at m = 2c); score stage not run

Registration `workers/MODEL1_REGISTRATION.md` (sha256 `f0a261bb9dc83368081121718a647c233a531bcc600a9025ff4b7fbcdc233df8`, commit f4a37b4). Code `src/scalper/model1.py`, tests `tests/test_model1.py`, fit record `workers/MODEL1_FIT.json`. Cheap side only (ask 3c to 30c); no favourite-side figure was computed.

## What ran
Census, then the `fit` stage: train outcomes only; **no test outcome was loaded or aggregated**. The registered stop rule (under 150 selected test trades at m = 2c for BOTH models, decided from the test FEATURES and the train-fitted model alone) fired, so `score` (test outcomes, calibration, permutation baseline) was NOT run, as registered.

## Numbers
- Pool after dropping every market closing at or after 2026-10-03T16:00Z: 6,522 cheap rows, 1,953 events (16,201 before the cut; the LIQ1 caches' own development dates run to Oct 29). Train 4,203 rows / 1,302 events, test 2,319 rows / 651 events (closes 2026-09-24 to 2026-10-03).
- Missing rates: overround missing 71.6% (weather and similar ladders only), time-to-close missing 22.9% (age looks), volume zero 52.9%, spread never missing.
- Train: win rate 8.83% against a mean price of 13.55c (a 4.7 point gap before fees), the same shape as CALIB1.
- Inner selection (time-ordered, validation log loss): logistic lambda 100 (the edge of the grid; 0.2999, improving monotonically with shrinkage, i.e. the data prefer the intercept plus little else); boosted trees depth 3, 50 trees (0.2961).
- **Selected test trades (margin over the ask, max 2 per event): logistic 0 at 2c and 0 at 4c; trees 14 at 2c and 3 at 4c.** Required: 150.

## Reading
A price-matched model of this table essentially never believes a cheap entry is worth more than its ask: with the ask and its log odds as features and a train win rate 4.7 points under the price, the fitted probabilities sit at or under the ask on almost every test row. The one model flexible enough to disagree (trees) found 14 test candidates, far too few to score (and scoring them would be a look at a handful of rows). Joint conditioning on spread, volume, category, series, look, overround and time did not find a region the market misprices in the cheap direction. It does not prove none exists: the pool is 6.5 thousand rows with 70% of the unconditioned loss concentrated in a few families, and the 150-trade bar needs a region of at least 7% of the test rows to disagree with the price by 2c, which the train data do not support.

## Verdict and N
**NOT_ENOUGH_DATA** (both models, both margins; the prediction "a few hundred trades at 2c" was wrong, selections were 0 and 14; the prediction that nothing wins was not testable). No LEAD, no forward test, no probe, no promote verb. The test third's outcomes were never read, so it remains unspent for a future, differently specified model. N +8 charged as registered (four tries). Forward plan: none; reopening needs more cheap-side rows than the cut leaves (the frozen third's candles are not fetched here).

## Deviations disclosed
The frozen-third cut (2026-10-03T16:00Z) was applied to rows from caches whose own development period runs later, shrinking the pool from 16,201 to 6,522 rows. This was decided and written in the registration before any outcome was read.
