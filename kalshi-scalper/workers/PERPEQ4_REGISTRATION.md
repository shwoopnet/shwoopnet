# PERPEQ4 registration: ETF perp against the index perp on the same underlying (written 2026-11-06 about 16:20 UTC, before any outcome; shared rules `PERPEQ_COMMON.md`)

Discovery only. No live code. The cleanest possible "same thing, two books" case, so it is the best chance a ratio test has; it is also the cheapest to refute.

## Mechanism and counterparty
SPY and US500 follow the same S&P 500, QQQ and US Tech 100 the same Nasdaq 100, so the log ratio of the two perps should be a constant (a scale plus dividends and funding drift). Counterparty: whoever hit one thin book without checking the other. Honest alternative: the books are quoted by one maker who keeps both in line and any deviation is smaller than the round-trip fee (0.48% for four crossings against a deviation of a few bps).

## Pairs (fixed)
SPY / US500 and QQQ / US Tech 100.

## Rule (fixed, no tuning)
Grid and r as in PERPEQ2 (exchange 1 minute candles at 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 15:55 New York; r = ln(mid ETF perp / mid index perp); a point is skipped if either candle is missing or a spread is over 3 times its cost-map median). Baseline: the last 20 prior grid points of the pair, spanning at least 3 trading dates. Trigger: |z| at least 2.0 AND |r - baseline mean| at least 10 bps (below that no cost can be recovered, so it is not a trade). Trade: sell the rich leg, buy the cheap leg, equal dollar notional, at the close ask and bid. Exit: the first grid point at least 6 hours later and no later than 30 hours. One open trade per pair. Control: the reverse.
Information readout (never scored): the distribution of |r - baseline mean| in bps over all development grid points, and the share above the break-even 48 bps plus recorded spread.

## Numeric prediction
Triggers need a 10 bps deviation: about 2 pairs x 15 dates x 7 points x 0.03 = about 6 trades in development (range 0 to 15). Median |deviation| 3 bps, 95th percentile 15 bps, share above 55 bps under 1%. Mean gross +4 bps, net -50 bps. Probabilities: NOT_ENOUGH_DATA 97%, FALSIFIED 3%. The information readout is the result that matters.

## Kill, bars and cut
As the common file. Development read date **2026-12-01**; held out from 2026-12-01 read once on or after 2026-12-30 after a LEAD only.

## Count
N +4 (pooled rule, control, two per-pair readouts).
