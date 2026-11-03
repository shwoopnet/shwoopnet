# VOLGAP1 result (2026-11-03; registered in c62a7c5 before any candle or kline was fetched; `src/scalper/volgap1.py`, `tests/test_volgap1.py`, run once)

**CRYPTO (KXBTCD + KXETHD): NOT_ENOUGH_DATA (67 treated trades, bar 150). GOLD (KXGOLDH): NOT_ENOUGH_DATA (6 treated trades; 713 closes with a fit, under the 800 rule).** W3 holdout not read (W1 and W2 did not pass). Not a pass, no promote verb. No parameter, rule or file was changed after the registration commit; the fetch ran unattended and the scored run executed once without error.

By the registered precedence (count first) the word is NOT_ENOUGH_DATA, but every informational line points the same way as FALSIFIED: the 38 scored crypto treated trades in W1 + W2 all lost (PF 0.00 in both windows, win rate 0%), and the control did not behave as predicted for gold (below).

Data: 102,288 near-spot settled strikes (BTC 283,638 / ETH / gold 45,685 listed before the spot filter), 93,384 with candles; 3,097 crypto closes (BTC 1,549, ETH 1,548) of which 1,387 had a vol and a fit (45%), 1,038 gold closes of which 713 had a fit (69%). OKX 96,700 one minute klines per pair. C = 10, taker at the next minute's ask, hard limit 0.30 and 3c slippage, fee 7% x C x p x (1-p) rounded up. N = 728,740, z bar 5.27.

Windows (dates with a fit, equal thirds): CRYPTO W1 2026-08-28 to 09-18 (20 dates), W2 09-19 to 10-09 (20), W3 10-11 to 10-31 (21, unread); GOLD W1 08-27 to 09-18 (17), W2 09-21 to 10-09 (17), W3 10-12 to 10-30 (17, unread).

## Headline (crypto, BTC + ETH pooled)
- Ratio realised / implied: median 0.98, quartiles 0.82 / 1.14, 95th percentile 1.54. Trigger (>= 1.5) in 82 of 1,387 fit hours (5.9%; predicted 7%); control (<= 0.67) 102 (7.4%).
- Treated model-edge rule: 67 trades (15 more had a model trade but no fill); **W1 n 16 PF 0.00 mean -9.88c; W2 n 22 PF 0.00 mean -8.50c**; W1 + W2 38 trades, win rate 0.0%, mean loss 9.1c. Predicted win rate 11%, PF 0.85. At an 11% true win rate the chance of 0 wins in 38 trades is 1%, but the trades are clustered in 22 days and the model picks the cheap side the realised-vol model likes most, which is where the realised-vol model is most wrong.
- **Calibration of every cheap tail (price 0.03 to 0.30), W1 + W2:** ratio <= 0.67: n 719, price 0.105, win 0.078, model 0.036; middle: n 6,103, price 0.106, win 0.077, model 0.103; ratio >= 1.5: n 426, price 0.108, **win 0.094, model(realised vol) 0.218**. So tails win less than they cost in every bucket (the favourite-longshot loss, again, about 3 points), and the win rate rises only from 7.7% to 9.4% when realised vol is 1.5x implied, against a model that says 21.8%: the ratio is mostly noise (a 15 minute RMS from 15 returns), and the ladder's smile already prices the wings above a single lognormal.
- TREATED-ALT (nearest 0.10, ratio >= 1.5): 43 trades, win 4.7%, PF 0.52 (W1 0.00, W2 1.03). CONTROL (nearest 0.10, ratio <= 0.67): 68 trades, win 2.9%, PF 0.30 (W1 0.27, W2 0.34). Control loses as predicted (PF 0.30 against 0.75). Treated-alt minus control PF is +0.22 (under the 0.25 rule), on 43 and 68 trades; nothing to read.
- Cost: mean loss 8.6c to 9.2c per losing trade at C = 10 incl. fee.

## Gold (information)
Ratio median 0.86; trigger in 15 of 713 fit hours (2.1%, predicted 9%); control hours 131 (18.4%). Treated 6 trades (2 scored, both lost). **Control nearest-0.10 W1 + W2: 34 trades, win 23.5%, PF 2.41 (W1 1.58, W2 3.50), mean +11.6c, z about +1.5 per window: the opposite of the predicted loss, on 34 trades from 19 days, not a finding** (gold's tails win 14% to 15% against a 16% to 18% price in every bucket, so unconditional tails still lose slightly; the control subset is the lucky one). Only 713 hours fit; gold is NOT_ENOUGH_DATA, not tested.

## Prediction scorecard
Trigger rate 5.9% (predicted 7%, range 3% to 15%): hit. Fits: 45% of crypto hours (predicted 85% to 97%): missed, because 6 strikes with mid 0.03 to 0.97 and R^2 >= 0.90 inside 1.5% (BTC) or 2% (ETH) of spot are often not there at 25 minutes. Treated trades 67 (predicted about 120, NOT_ENOUGH_DATA 60% likely): NOT_ENOUGH_DATA, as the most likely outcome. Win rate 0% of 38 (predicted 11%) and PF 0.00 (predicted 0.85): worse than predicted. Control PF 0.30 (predicted 0.75): worse. Treated-alt minus control +0.22 (predicted +0.1): in range. Calibration: tails win less than their price in all three buckets (predicted): hit. Gold control PF 2.41 (predicted 0.75): missed, n 34.

## Reading
The mechanism does not show up in the hourly crypto ladders: when the last 15 minutes of spot ran 1.5x the vol the ladder implied, the cheap far strikes did not win more than their price by anything near the 8c edge the model claimed (win 9.4% against 10.8% paid, model 21.8%). Either the quoters already move with the tape, or the ratio is dominated by estimation noise. The count is too small to call it a statistical FALSIFIED (the registered NOT_ENOUGH_DATA precedence), and a larger sample would need a longer history than the 68 days of 1 minute candles on file, a looser fit (fewer strikes) or a second look time, each of which is a new counted try. No forward recorder was built; none is recommended. Gold's control result is a curiosity at n 34, not a lead.

## Printed result (verbatim from the one run)
```
VOLGAP1 run 2026-11-03T14:11:05.055842+00:00 N=728740 z bar 5.27 cost: fee 7% x C x p x (1-p) rounded up, C=10, taker at the next minute's ask
markets near spot 102288, with candles 93384
--- GROUP CRYPTO (KXBTCD, KXETHD)
closes with listed near-spot strikes: KXBTCD 1549, KXETHD 1548; with a vol and a fit: 1387
ratio realised/implied quantiles 5/25/50/75/95: 0.62 0.82 0.98 1.14 1.54
trigger hours ratio >= 1.5: 82 (5.9%); control hours ratio <= 0.67: 102 (7.4%)
trades (outcome-free count, all windows): treated 67, treated-alt nearest-0.10 73, control nearest-0.10 85, model rule in control hours 0; treated with a model trade but no fill 15
TREATED model edge W1: n 16 days 11 PF 0.00 mean -9.88c z -7.54 | fees x1.2 mean -9.97c
TREATED model edge W2: n 22 days 11 PF 0.00 mean -8.50c z -20.62 | fees x1.2 mean -8.60c
TREATED model edge W1+W2: win rate 0.0% of 38, mean win 0.0c, mean loss 9.1c, payoff ratio 0.00
TREATED-ALT nearest 0.10 W1: n 19 days 12 PF 0.00 mean -9.28c z -15.44 | fees x1.2 mean -9.39c
TREATED-ALT nearest 0.10 W2: n 24 days 12 PF 1.03 mean +0.21c z +0.03 | fees x1.2 mean +0.12c
TREATED-ALT nearest 0.10 W1+W2: win rate 4.7% of 43, mean win 91.4c, mean loss 8.6c, payoff ratio 10.58
CONTROL nearest 0.10 W1: n 34 days 13 PF 0.27 mean -7.17c z -2.47 | fees x1.2 mean -7.29c
CONTROL nearest 0.10 W2: n 34 days 13 PF 0.34 mean -5.40c z -2.24 | fees x1.2 mean -5.50c
CONTROL nearest 0.10 W1+W2: win rate 2.9% of 68, mean win 90.4c, mean loss 9.2c, payoff ratio 9.81
model rule in control hours W1: n 0 days 0 PF 0.00 mean +0.00c z +0.00 | fees x1.2 mean +0.00c
model rule in control hours W2: n 0 days 0 PF 0.00 mean +0.00c z +0.00 | fees x1.2 mean +0.00c
calibration of cheap tails at the look (price 0.03 to 0.30, every strike and side), W1+W2 only: bucket n, mean price, win rate, model(realised) mean prob
  ratio<=0.67: n 719 price 0.105 win 0.078 model 0.036
  0.67<ratio<1.5: n 6103 price 0.106 win 0.077 model 0.103
  ratio>=1.5: n 426 price 0.108 win 0.094 model 0.218
CRYPTO Try A: NOT_ENOUGH_DATA | trades 67 under 150 (windows read below for information)
CRYPTO control PF (nearest 0.10, ratio<=0.67, W1+W2) 0.30 mean -6.29c n 68; treated-alt PF 0.52 mean -3.99c n 43
--- GROUP GOLD (KXGOLDH)
closes with listed near-spot strikes: KXGOLDH 1038; with a vol and a fit: 713
ratio realised/implied quantiles 5/25/50/75/95: 0.52 0.71 0.86 1.04 1.32
trigger hours ratio >= 1.5: 15 (2.1%); control hours ratio <= 0.67: 131 (18.4%)
trades (outcome-free count, all windows): treated 6, treated-alt nearest-0.10 6, control nearest-0.10 71, model rule in control hours 2; treated with a model trade but no fill 7
TREATED model edge W1: n 1 days 1 PF 0.00 mean +0.00c z +0.00 | fees x1.2 mean +0.00c
TREATED model edge W2: n 1 days 1 PF 0.00 mean +0.00c z +0.00 | fees x1.2 mean +0.00c
TREATED model edge W1+W2: win rate 0.0% of 2, mean win 0.0c, mean loss 16.5c, payoff ratio 0.00
TREATED-ALT nearest 0.10 W1: n 0 days 0 PF 0.00 mean +0.00c z +0.00 | fees x1.2 mean +0.00c
TREATED-ALT nearest 0.10 W2: n 1 days 1 PF 0.00 mean +0.00c z +0.00 | fees x1.2 mean +0.00c
TREATED-ALT nearest 0.10 W1+W2: win rate 0.0% of 1, mean win 0.0c, mean loss 11.7c, payoff ratio 0.00
CONTROL nearest 0.10 W1: n 17 days 8 PF 1.58 mean +5.41c z +0.70 | fees x1.2 mean +5.25c
CONTROL nearest 0.10 W2: n 17 days 11 PF 3.50 mean +17.88c z +1.53 | fees x1.2 mean +17.75c
CONTROL nearest 0.10 W1+W2: win rate 23.5% of 34, mean win 84.5c, mean loss 10.8c, payoff ratio 7.84
model rule in control hours W1: n 1 days 1 PF 0.00 mean +0.00c z +0.00 | fees x1.2 mean +0.00c
model rule in control hours W2: n 0 days 0 PF 0.00 mean +0.00c z +0.00 | fees x1.2 mean +0.00c
model rule in control hours W1+W2: win rate 0.0% of 1, mean win 0.0c, mean loss 27.4c, payoff ratio 0.00
calibration of cheap tails at the look (price 0.03 to 0.30, every strike and side), W1+W2 only: bucket n, mean price, win rate, model(realised) mean prob
  ratio<=0.67: n 439 price 0.160 win 0.144 model 0.067
  0.67<ratio<1.5: n 1572 price 0.176 win 0.149 model 0.151
  ratio>=1.5: n 45 price 0.156 win 0.111 model 0.246
GOLD Try A: NOT_ENOUGH_DATA | trades 6 under 150 (windows read below for information)
GOLD control PF (nearest 0.10, ratio<=0.67, W1+W2) 2.41 mean +11.64c n 34; treated-alt PF 0.00 mean +0.00c n 1
```
