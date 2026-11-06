# PERPEQ2 registration: a stock perp against its sector partner, ratio reversion (written 2026-11-06 about 16:20 UTC, before any outcome; shared rules `PERPEQ_COMMON.md`)

Discovery only. No live code. RV1 registered sector pairs while the stocks were inactive and was NOT_ENOUGH_DATA with 0 quotes; this is the first test with live quotes, on a fixed pair list chosen below, with a fresh cut.

## Mechanism and counterparty
Two stocks of one sector share news; the log ratio of their perp prices should mean-revert after a one-sided order-flow burst in one perp's thin book. Counterparty: the taker who pushed one name through its partner on a $1,000 to $3,000 touch. Honest alternative: sector pairs drift on names' own news and the ratio does not revert inside a day, and four crossings plus four fees (0.48%) exceed any reversion. The prediction is that it fails on cost.

## Pairs (fixed now; both legs in U, so chosen on cost, and on the sector name only)
XOM-CVX, KO-PG, AAPL-MSFT, GOOGL-META, NVDA-MU. Nothing else.

## Rule (fixed, no tuning)
Grid: the exchange 1 minute candles ending at 10:00, 11:00, 12:00, 13:00, 14:00, 15:00 and 15:55 New York on each trading day (7 a day); r = ln(mid A / mid B) where mid = (close bid + close ask) / 2; a grid point is skipped if either candle is missing or either spread is over 3 times its cost-map median. Baseline: the last 20 prior grid points of the pair (about 3 trading days; fewer than 20 or fewer than 3 dates means no signal). z = (r - mean) / sd of the baseline. Trigger: |z| at least 2.0. Trade: sell the rich leg at the close bid and buy the cheap leg at the close ask, equal dollar notional at the mids. Exit: the first grid point at least 18 hours later and no later than 48 hours (both legs at the close ask or bid), else no trade (counted). One open trade per pair at a time. Control: the reverse direction on the same triggers.

## Numeric prediction
Triggers: 5 pairs x 15 dates x 7 grid points x P(|z| >= 2, about 0.05) = about 26, limited to about 15 to 25 trades by the one-open-trade rule and the 18 hour hold. Gross +3 bps on a ratio that moves about 100 bps a day (range -20 to +25), cost = 48 bps fees plus about 10 bps spread, net -55 bps, PF 0.0 to 0.3, win rate about 35%. Break-even fee per side will be reported (expected under 3 bps). Probabilities: NOT_ENOUGH_DATA 92%, FALSIFIED 8%.

## Kill, bars and cut
As the common file; development read date **2026-12-01** (the first possible trigger is about 2026-11-12); held out from 2026-12-01 read once on or after 2026-12-30 only after a LEAD. The date 100 trades is met at the observed rate is reported (about 2027-05 at 20 trades a month).

## Count
N +7 (pooled rule, control, and five per-pair readouts, which are information only).
