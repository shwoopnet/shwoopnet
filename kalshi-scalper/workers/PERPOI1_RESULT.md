# PERPOI1 result (development read, run once 2026-11-03; rule, bars and split exactly as registered in `PERPOI1_REGISTRATION.md`, sha256 0204ed74...74c4; code `src/scalper/perpoi1.py`, tests `tests/test_perpoi1.py` committed before the run; output `workers/PERPOI1_output.txt`)

**Data reach.** Perp KXBTCPERP 1 minute candles with open interest (SNAPBACK1 cache, 2026-06-03 to 2026-11-03) and `data/conf2_lad.sqlite` KXBTCD hourly candles. Development = first two thirds by date of the ladder span (closes to 2026-10-09 or so); **772 hourly closes with a ladder** (the local ladder cache has gaps, so fewer than the 1,500 listed). The holdout (last third) was never computed. Bitcoin only (no ETH or daily ladder history).

**Trigger rate.** Surge at 34 of 772 closes (4.4%); price direction nonzero at all of them. Try A trades: 20 (14 surge events had no strike with a quote priced 3c to 30c on the needed side), **12.7 a month**; Try B: 34.

| development (C = 10) | n | win | mean price | net per contract | PF | PF at fees x1.2 |
|---|---|---|---|---|---|---|
| A, surge, toward the perp move | 20 | 15.0% | 0.217 | -7.9c | 0.58 | 0.57 |
| B, surge, cheaper tail either side | 34 | 14.7% | 0.214 | -7.9c | 0.58 | 0.57 |
| Control, no surge, same trade | 330 | 16.7% | 0.201 | -4.6c | 0.74 | 0.73 |

Half 1 / half 2: A n 12 / 8, PF 0.73 / 0.40; control PF 0.77 / 0.65. **Trigger minus control (net per contract): -3.3c overall (bootstrap by close 5th to 95th percentile -15.9c to +11.0c), -0.8c in half 1, -6.6c in half 2: not positive in either half.** At C = 1 the net is -8.4c (A) and -5.1c (control).

**Win versus price.** Win rate 15.0% against a mean price 21.7c (control 16.7% against 20.1c): the tails are priced about fairly, and the fee plus the spread paid at the ask is the whole loss. The surge changes nothing measurable (A is below the control in both halves, but with n 12 and 8 the interval spans zero).

**Verdict: NOT_ENOUGH_DATA** (20 development A trades against 100 required; 150 trades in all three windows would need about 10 more months at 12.7 a month). As registered, no FALSIFIED is declared below 100 trades, but the point estimates are all against the idea: A and B both lose more than the no-surge control, PF 0.58 (prediction 0.6 to 1.1), trigger rate 12.7 a month (prediction about 20, so lower), win rate 15% (predicted 13%). The frozen holdout stays unread. **No probe spec:** nothing is positive in both halves, so there is no capped probe. Months to 150 trades is not worth waiting for at these odds. N +4 (A and B at +2 per rule).
