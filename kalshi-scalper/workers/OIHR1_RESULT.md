# OIHR1 result: the OICORE shape on the hourly Bitcoin ladder KXBTCD (2026-11-03)

Registered and pushed first (`workers/OIHR1_REGISTRATION.md`, sha256 `d198f142121c7ce48727e1eb217517fb7d8231a11ffc4ddae9f102e678d9c0cf`), code `src/scalper/oihr1.py` committed before the score, tests `tests/test_oihr1.py`. Scored once (`python -m scalper.oihr1 score`, refuses a second run; raw `data/oihr1_score.json`, not committed). No code change after registration. W3 (last third, 293 eligible events, 2026-09-20 to 2026-11-03) NOT read.

## Verdict: FALSIFIED (both tries), and NOT_ENOUGH_DATA by count (70 and 69 trades, floor 150)
Data reach: 956 hourly closes with 55 minutes of candles and open interest (Aug 24 to Nov 3), 877 eligible after the 24 hour trailing set; trigger rate 113 of 877 = 12.9% (W1 40, W2 39, W3 34). KXETHD and KXGOLDH not runnable (no 30 minute open interest history locally), not tested.

C = 10, taker at the next candle's ask, hard limit 0.30, fee 7% x C x p x (1-p) rounded up. Cents per contract; PF at fee x1.2 in brackets.

| try, window | n | win rate | avg fill | PF | mean c | day-clustered z |
|---|---|---|---|---|---|---|
| A (lean side) W1 trigger | 35 | 11.4% | 15.9c | 0.63 (0.62) | -5.39 | -1.01 |
| A W1 control | 219 | 14.6% | 15.4c | 0.87 | -1.73 | -0.69 |
| A W2 trigger | 35 | 20.0% | 16.3c | 1.21 (1.20) | +2.70 | +0.49 |
| A W2 control | 227 | 14.1% | 17.0c | 0.74 | -3.87 | -1.83 |
| A pooled trigger | 70 | 15.7% | 16.1c | 0.90 | -1.34 | -0.34 |
| A pooled control | 446 | 14.3% | 16.2c | 0.80 | -2.82 | -1.69 |
| B (cheaper side) W1 trigger | 35 | 8.6% | 18.8c | 0.37 | -11.29 | -2.40 |
| B W1 control | 206 | 13.6% | 18.8c | 0.63 | -6.29 | -3.22 |
| B W2 trigger | 34 | 23.5% | 19.0c | 1.22 | +3.46 | +0.53 |
| B W2 control | 217 | 14.7% | 19.7c | 0.65 | -6.09 | -2.88 |
| B pooled trigger | 69 | 15.9% | 18.9c | 0.76 | -4.02 | -0.93 |
| B pooled control | 423 | 14.2% | 19.3c | 0.64 | -6.19 | -4.18 |

Trigger minus control (mean c per contract): A W1 -3.66, W2 +6.58; B W1 -5.00, W2 +9.55. Not positive in both halves, so the registered kill (not positive in both) fires; PF is also under 1.5 in W1 and W2 for both tries. The win rate sits at or just under the price paid (A pooled trigger 15.7% vs 16.1c paid; control 14.3% vs 16.2c): no sign the cheap tail is mispriced, and the control (any cheap tail, no jump) loses 2.8c to 6.2c a contract, which is the ordinary cost of a 3c to 30c tail plus the fee. The positive W2 triggers are 7 wins of 35 and 8 of 34; one half does not make a finding.

Prediction check: trigger rate 9% to 11% (observed 12.9%, over), trades per half 15 to 35 (A 35, B 35/34, at the top), win rate 12% to 24% (inside), PF pooled 0.6 to 1.1 (0.90 and 0.76, inside), trigger-minus-control within +-3c (outside: pooled A +1.5c, B +2.2c, halves swing wide), NOT_ENOUGH_DATA 90% (also true by count, but the sign test fires first).

Months to go: at about 1.4 triggered trades a day the 150 floor needs about 107 days of the same data (it has 71); moot, since the halves disagree in sign.

## Probe spec
None. Not positive in both halves, no mechanism beyond the stated one (makers not repricing tails after new positions), whose observable consequence (the cheap tail wins more often than its price after a jump) did not appear in W1. Not recommended for a capped probe.

N +4 (two rules at +2). Running about 730,007.
