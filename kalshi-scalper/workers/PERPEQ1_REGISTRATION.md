# PERPEQ1 registration: fade the overnight perp gap of a single stock into the cash open (written 2026-11-06 about 16:20 UTC, before any outcome; shared rules `PERPEQ_COMMON.md`)

Discovery only. No live code. This is the stock-perp version of OVN1 (which had 3 events, all index perps) with a fresh cut and with the real cash open from Yahoo as a second reading; it is not a new idea and is charged as new N.

## Mechanism and counterparty
While the cash market is shut the stock perp is the only place the stock trades, and its price moves on thin overnight and pre-market flow; the cash open auction then sets the price with full liquidity. If the overnight perp gap g_p (perp mid versus the venue's frozen cash reference) overshoots, the perp falls back toward the cash by the open. Counterparty: the overnight taker who pays a wide book (the cost map shows overnight spreads about 3 times the midday ones) for news the cash market has not yet confirmed. Honest alternative: the perp is a fair forecast of the open (g_c = g_p), the gap is already in the price and the 0.24% fee plus the wide book is the whole result.

## Universe
U (see common file) minus the two index perps (their reference is an index, not a stock) minus any perp Yahoo has no regular-session series for (counted). Cash reference prices: Yahoo chart 5 minute bars, range 60 days, keyless. If the Yahoo reads fail on the read date, the Yahoo reading (g_c, beta) is NOT_RUNNABLE and the trade rule still runs on the perp's own rows.

## Rule (fixed, no tuning)
Event = (perp, trading date). Entry sample: the LAST active sample with New York time from 05:00 to 09:25 (hourly rows have 0 to 2 of these a day; a day without one is counted and skipped). g_p = mid / reference_price - 1 at that sample (reference is the venue's frozen last cash value). Trigger: |g_p| at least 30 bps and at least 5 times the sample's own spread in bps. Trade: the perp AGAINST the gap sign (g_p > 0: sell at the bid; g_p < 0: buy at the ask). Exit: the first active sample at or after 09:55 New York and before 12:00 (buy back at the ask, or sell at the bid); no such sample means no trade (counted, and the entry is dropped). Continuation (same entries, opposite direction) is the control. One event per perp and date.
Second reading (information, never scored for the verdict): g_c = open of the first regular 5 minute bar at 09:30 over the previous regular close, minus 1; beta = slope of g_c on g_p through the origin, and the share of events with sign(g_c) = sign(g_p). A beta clearly under 1 is the premise of the fade; a beta of 1 says the gap is already in the cash open.

## Numeric prediction
Events in development: 19 names x 15 dates x P(an entry sample exists, about 0.35) x P(|g_p| >= 30 bps, about 0.4) x P(an exit sample exists, about 0.5) = about 20 trades (range 8 to 40). Mean gross +5 bps (range -10 to +20), mean net about -35 bps (fee 24 plus about 8 spread plus an overnight book), PF 0.1 to 0.6; beta 0.6 to 1.0. Verdict probabilities: NOT_ENOUGH_DATA 85%, FALSIFIED 14%, LEAD 1%.

## Kill, bars and cut
As the common file. NOT_ENOUGH_DATA at the read date reports the date 100 trades would be met at the observed rate (about 5 trades per 3 trading days gives about 2027-03). Development read date **2026-12-01**; held out 2026-12-01 on, read once on or after 2026-12-30 only after a LEAD.

## Count
N +2 (fade, control).
