# COMDAY1 result (run once 2026-11-04; registered in 7c77742, sha256 `ba54ee187742fd98bf03135f57b3fcf8dcfc098e3d5f20b8511aacd681a0c61b`, before any Kalshi candle or outcome; `src/scalper/comday1.py`, `tests/test_comday1.py`, printout `studies/comday1_result_2026-11-04.txt`)

**Rule A (6 h before the close): NOT_ENOUGH_DATA (28 treated trades, bar 150). Rule B (1 h): NOT_ENOUGH_DATA (44 trades), and every one of the 44 lost.** W3 never fetched or loaded. Not a pass, no promote verb. N +4. Cheap side only (ask 3c to 30c); no favourite-side result was computed or printed.

## Data actually scored (disclosed deviation: partial fetch)
Series KXWTI, KXBRENTD, KXNATGASD, KXGOLDD (daily gold bracket), KXSILVERD, KXCOPPERD vs OKX CL, BZ, NG, XAU, XAG, XCU 5 minute bars. 158 close dates 2026-03-24 to 11-02; development 105 (W1 52, W2 53), 53 frozen and never stored. The Kalshi candle API is slow (about 1 series-day a minute; the 4 hour cap in the registration was reached across a container restart, plus a last 25 minutes after the restart). By the registered prefix rule the score uses the **first 27 md5-ranked series-days of every series (162 of 509 development series-days, about 32%)**, so the take-up is measured on a third of the days. A bug found at fetch time (OKX JSON keys were strings, so the first fetch pass produced empty states) was fixed and committed before any scoring; no rule changed.

## Numbers (C = 10, fee 7% x C x p x (1-p) rounded up, taker at the quote in force at D+60)
| | n | days | win | price | PF | mean | day-clustered z |
|---|---|---|---|---|---|---|---|
| A treated W1 | 19 | 10 | 21.1% | 0.101 | 2.51 | +10.28c | +1.02 |
| A treated W2 | 9 | 5 | 0.0% | 0.079 | 0.00 | -8.42c | -2.75 |
| A treated W1+W2 | 28 | 15 | 14.3% | 0.094 | 1.58 | +4.27c (x1.2 +4.16c, +1c slip +3.22c) | +0.59 |
| A control (every cheap strike-side) | 1,585 | 81 | 7.3% | 0.139 | 0.44 | -7.42c | -5.80 |
| B treated W1+W2 | 44 | 21 | 0.0% | 0.108 | 0.00 | -11.47c | -10.58 |
| B control | 416 | 75 | 4.8% | 0.143 | 0.26 | -10.34c | -8.85 |

Rule A treated is +10c in W1 on 19 trades and -8c in W2 on 9: noise, and its W2 fails the registered line (PF under 1.5, mean not above 0), so by the registered kill line it would read FALSIFIED if the count were sufficient. Per series (descriptive, n 2 to 18): natural gas 9 trades 0 wins, gold 4 and silver 3 and copper-less wins none, WTI/Brent/copper 3 trades each with one win. Duplicate check: no overlap with IDXFUT1 (index ladders), VOLGAP1 (hourly), SETTLE1 (15 minute metals); USWEEP1's KXGOLDD/KXNATGASD/KXBRENTD/KXSILVERD rows were favourites (not used); same underlyings as L1 gold but a different, daily, cheap-side bet.

## Calibration (the information that matters)
Every cheap strike-side, W1+W2, t4 model against price against outcome:
- Rule A: ratio under 1: n 803, price 0.154, win 0.071, model 0.094. Ratio 1 to 3: n 698, price 0.127, win 0.079, model 0.173. **Ratio at least 3: n 84, price 0.102, win 0.048, model 0.593.** By model p: 0.03-0.09: win 4.4% vs price 9.8%; 0.09-0.2: 7.7% vs 14.5%; 0.2-0.4: 12.6% vs 21.2%; 0.4-0.98: 8.9% vs 15.9% (model 69%).
- Rule B: ratio at least 3: n 58, price 0.094, **win 0.000**, model 0.441.
Cheap daily-commodity strikes lose at every model bucket (win about 5 to 8 points under the price): the same favourite-longshot loss as VOLGAP1 (tails win less than they cost), and a model-ratio of 3 or more points at strikes where the OKX-based model is wrong (the reference-wrong case: SETTLE1), not where Kalshi is. The t4 kernel is not too thin here (model 0.059 to 0.69 over buckets), the market is right and the model is over-confident when it disagrees.

## Prediction scorecard
Take-up 0.25 per series per look per day predicted; measured 28 / 162 = 0.17 (A) and 44 / 162 = 0.27 (B): in range. Trades at full data: A about 0.17 x 6 x 105 = 108, B about 170: **rule B would likely exceed 150 at full data and has 0 wins in 44**; A would likely stay under 150 (NOT_ENOUGH_DATA, 55% likely, hit). Win 8% at price 0.14 predicted vs 14.3% at 0.094 (A, n 28, no information) and 0% (B). PF 0.6 predicted vs 1.58 (A, 28) and 0.00 (B). Control PF 0.7 predicted vs 0.44 and 0.26: worse. Calibration "ratio at least 3 bucket wins 8 to 15 points under the model": far worse (5% vs 59%). FALSIFIED-or-NOT_ENOUGH_DATA 96%: hit.

## Verdict, forward plan, probe
- Verdict: NOT_ENOUGH_DATA on the count for both rules (partial fetch, 32% of days), with rule B's 44-for-44 losses and the control PF 0.26 to 0.44 pointing to FALSIFIED. No lead; no promote verb. No capped-probe spec (nothing is positive in both windows with a mechanism).
- Days to go for rule A: about 0.17 trades per series-day x 6 series = about 1.0 a trading day, so 150 trades needs about 150 trading days (about 7 months); the tool's "458 dates" line divides by all 105 development dates while only 27 per series were fetched and is too pessimistic. A second tranche of the remaining 70% of development days would add the rest (a continuation, not a new try, but a 6 hour API job at current speed).
- Forward freeze (registered): one read on or after 2027-01-31 on quotes from the recorder branch `claude/v2-recorder-daily` (not merged; watches KXGOLDD, KXSILVERD, KXNATGASD, KXBRENTD; KXWTI and KXCOPPERD would need a watchlist edit). Not recommended on this evidence: the control loses 7 to 10c a contract at every ratio.

## Printed result
`studies/comday1_result_2026-11-04.txt` (verbatim from the one run).
