# PERPEQ2 registration: a stock perp against its sector partner, ratio reversion (written 2026-11-06 about 16:20 UTC, before any outcome; shared rules `PERPEQ_COMMON.md`)

Discovery only. No live code. RV1 registered sector pairs while the stocks were inactive and was NOT_ENOUGH_DATA with 0 quotes; this is the first test with live quotes, on a fixed pair list chosen below, with a fresh cut.

## Mechanism and counterparty
Two stocks of one sector share news; the log ratio of their perp prices should mean-revert after a one-sided order-flow burst in one perp's thin book. Counterparty: the taker who pushed one name through its partner on a $1,000 to $3,000 touch. Honest alternative: sector pairs drift on names' own news and the ratio does not revert inside a day, and four crossings plus four fees (0.48%) exceed any reversion. The prediction is that it fails on cost.

## Pairs (fixed now; both legs in U, so chosen on cost, and on the sector name only)
XOM-CVX, KO-PG, AAPL-MSFT, GOOGL-META, NVDA-MU. Nothing else.

## Rule (fixed, no tuning)
At each sample where both legs are active and under the 3 times median spread screen, r = ln(mid A / mid B). Baseline: the last 12 prior samples of that pair spanning at least 3 distinct New York trading dates (otherwise no signal). z = (r - mean) / sd of the baseline. Trigger: |z| at least 2.0. Trade: sell the rich leg at the bid and buy the cheap leg at the ask, equal dollar notional at the mids. Exit: the first sample at or after 18 hours later and no later than 48 hours (both legs at the recorded ask or bid), else no trade (counted). One open trade per pair at a time. Control: the reverse direction on the same triggers.

## Numeric prediction
Triggers: about 5 pairs x 3 per month limited by the one-open-trade rule and the 18 hour hold = about 15 trades in development (range 6 to 30). Gross +3 bps on a ratio that moves about 100 bps a day (range -20 to +25), cost = 48 bps fees plus about 10 bps spread, net -55 bps, PF 0.0 to 0.3, win rate about 35%. Break-even fee per side will be reported (expected under 3 bps). Probabilities: NOT_ENOUGH_DATA 90%, FALSIFIED 10%.

## Kill, bars and cut
As the common file; development read date **2026-12-01** (baseline needs 3 dates, so the first possible trigger is about 2026-11-11); held out from 2026-12-01 read once on or after 2026-12-30 only after a LEAD. The date 100 trades is met at the observed rate is reported (about 2027-04).

## Count
N +7 (pooled rule, control, and five per-pair readouts, which are information only).
