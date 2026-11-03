# IDXFUT1 result (2026-11-03; registered in 8bf1cde before any OKX bar was compared with a Kalshi quote; `src/scalper/idxfut1.py`, `tests/test_idxfut1.py`, run once; printout `studies/idxfut1_result_2026-11-03.txt`)

**NOT_ENOUGH_DATA: 5 treated trades in W1 + W2 pooled (bar 150). Reference FOUND (OKX SPY and QQQ equity-index perps, 1 minute), but it agrees with Kalshi: the rule almost never fires.** W3 holdout not read (never loaded). Not a pass, no promote verb. N +8 (4 tries).

Disclosure: the scored run was executed in the same shell line as the unit tests, and one of my own tests was wrong (it asserted a pick the registered rule correctly does not make), so the run happened before the code was committed. The code file was not changed between the run and its commit (only the test file was fixed), and the rule is exactly the registered one.

## Reference
OKX `SPY-USDT-SWAP` and `QQQ-USDT-SWAP` 1 minute candles for all 47 closes (100 bars each). Sanity (data only, no Kalshi quote): the perp scaled by the 75-minute-before ratio sat within 1.5 bp (S&P) and 1.3 bp (Nasdaq) of the Yahoo index level at the look on average, median 1 minute vol 1.6 to 1.8 bp. So the outside price is good; the basis fear in the registration did not materialise. `US500`/`US100` perps (listed 2026-09-10) not used. Other keyless sources: FRED `SP500` daily only; Yahoo 429, Stooq/CNBC/Binance refused.

## Numbers (W1 2026-08-24 to 09-14, W2 to 10-06; C = 10, fee 7% x C x p(1-p) rounded up)
- Event-looks with a reference: 31 per variant (4 variants, 124 in all). Every strike-side with an ask 0.03 to 0.30 and a two-sided candle at the fill minute: 1,064.
- **Treated (reference probability at least 3x the ask): 0 / 4 / 0 / 1 trades** (S&P 10: W1 0, W2 4; S&P 30: 0; Nasdaq 10: W1 0, W2 1; Nasdaq 30: 0). Pooled W1: none; W2: n 5 on 4 days, win 20% at price 0.188, PF 1.01, mean +0.8c (fees x1.2 -1.2c, +1c slippage -9.6c). W1 PF is undefined (no trade), so the registered FALSIFIED line in the printout comes from that and from fees x1.2, not from a loss record; the honest word is NOT_ENOUGH_DATA.
- **Calibration of all cheap strike-sides (information, pooled windows):** ratio under 1: n 949, price 0.110, win 0.120, model 0.037. Ratio 1 to 3: n 107, price 0.171, win 0.131, model 0.229. **Ratio at least 3: n 8, price 0.158, win 0.125, model 0.595.** Where the model is below the price the cheap side wins slightly MORE than its price (12.0% against 11.0%, the opposite of the favourite-longshot bias seen on crypto ladders); where the model claims a 3x edge, which is rare, the win rate is no higher than the price. A 60 minute RMS lognormal has thin tails (model 3.7% for asks at 11%), so it is wrong in the wings, not Kalshi.
- **Control (no model, nearest 0.10 ask), pooled:** W1 58 trades, win 6.9% at price 0.099, PF 0.62, mean -37c; W2 63 trades, win 12.7%, PF 1.24, mean +21.8c. Per variant the signs flip between windows (S&P 30: W1 0.62, W2 2.01; Nasdaq 30: W1 1.21, W2 0.58). W1 + W2 pooled about -7c per trade on 121 trades from 31 days: noise, not a lead.

## Prediction scorecard
Trades about 55 (predicted) vs 5: missed, in the direction of "fewer"; NOT_ENOUGH_DATA predicted 70% likely: hit. Win 9% at price 0.12 (predicted) vs 20% at 0.188 on n 5: no information. PF 0.6 predicted vs 1.01 on 5: no information. Control PF 0.7 (predicted) vs 0.62 and 1.24: both within the range. Calibration "win rate in the ratio at least 3 bucket 10 points under the model": hit (12.5% vs 59.5%), on n 8.

## Reading
With an outside real-time price, Kalshi's S&P and Nasdaq ladders rarely leave a cheap strike under a third of the reference probability: in 124 event-looks only 8 strike-sides (about 6%) had ratio at least 3, and they did not beat their price. That is the fourth independent read (INX1 VIX model, PUB20 P05 and P08, E4, now an actual futures-tracking price) saying Kalshi's index quoters track the index. The only place the model differs from the price is the ratio under 1 bucket (model too thin in the tails), which is not a tradable gap. No forward recorder recommended. To get power one would need years of history or a tail-risk-aware model (a counted new try with its own registration); the daily range series (`KXINX`, `KXNASDAQ100`) were not pulled.

## Capped-probe spec
Not recommended (no lead). For the record: 1 contract, hard limit 0.30, ratio at least 3, at most 4 orders a day, worst day about $1.26, worst single loss about 31.5c; at the measured rate of 5 trades in 31 days (about 0.16 a day) 40 fills would take about 250 trading days, so it cannot pay off.

## Printed result
See `studies/idxfut1_result_2026-11-03.txt` (verbatim from the one run).
