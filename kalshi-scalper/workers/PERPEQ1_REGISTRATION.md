# PERPEQ1 registration: fade the overnight perp gap of a single stock into the cash open (written 2026-11-06 about 16:20 UTC, before any outcome; shared rules `PERPEQ_COMMON.md`)

Discovery only. No live code. This is the stock-perp version of OVN1 (which had 3 events, all index perps) with a fresh cut and with the real cash open from Yahoo as a second reading; it is not a new idea and is charged as new N.

## Mechanism and counterparty
While the cash market is shut the stock perp is the only place the stock trades, and its price moves on thin overnight and pre-market flow; the cash open auction then sets the price with full liquidity. If the overnight perp gap g_p (perp mid versus the venue's frozen cash reference) overshoots, the perp falls back toward the cash by the open. Counterparty: the overnight taker who pays a wide book (the cost map shows overnight spreads about 3 times the midday ones) for news the cash market has not yet confirmed. Honest alternative: the perp is a fair forecast of the open (g_c = g_p), the gap is already in the price and the 0.24% fee plus the wide book is the whole result.

## Universe
U (see common file) minus the two index perps (their cash reference is an index, not a stock). Quotes are the exchange 1 minute candles (close bid and close ask, `PERPEQ_COMMON.md`); no recorder row is needed. Yahoo is used only for the second reading below; if the Yahoo reads fail, that reading is NOT_RUNNABLE and the trade rule is unaffected.

## Rule (fixed, no tuning)
Event = (perp, trading date). Entry: the candle ending at 08:55 New York. g_p = mid(08:55) / mid(16:00 New York of the PREVIOUS trading day) - 1, where mid = (close bid + close ask) / 2 of those candles (the perp's own move through the night, and through the weekend on a Monday; it needs no reference price). A missing candle at either end skips the event (counted). Trigger: |g_p| at least 30 bps and at least 5 times the entry candle's own spread in bps, and the entry spread at most 3 times the perp's cost-map median (defect screen, counted). Trade: the perp AGAINST the gap sign (g_p > 0: sell at the close bid; g_p < 0: buy at the close ask). Exit: the candle ending at 10:00 New York (buy back at the close ask or sell at the close bid); a missing exit candle means no trade (counted). One event per perp and date. Continuation (same entries, opposite direction) is the control.
Second reading (information, never scored for the verdict): g_c = open of the 09:30 regular 5 minute bar (Yahoo) over the previous regular close, minus 1; beta = slope of g_c on g_p through the origin and the share of events with the same sign. A beta clearly under 1 is the premise of the fade.

## Numeric prediction
Trades in development: 19 names x 15 dates x P(both candles present, about 0.95) x P(|g_p| >= 30 bps and the 5 times spread test, about 0.45) = about 125 (range 70 to 180), on about 15 clusters (one per date; the 30 cluster bar is NOT met by 15 dates, so the verdict at the read date is NOT_ENOUGH_DATA on clusters even if trades exceed 100, and the trade count is reported). Mean gross +5 bps (range -15 to +25), mean net about -35 bps (24 bps fee plus about 8 bps of entry and exit spread), PF 0.1 to 0.6; beta 0.6 to 1.0. Verdict probabilities at 2026-12-01: NOT_ENOUGH_DATA 90% (cluster bar), FALSIFIED 9%, LEAD 1%. The 30 cluster bar is met on about 2026-12-21 (30 trading dates from 2026-11-09), at which date the verdict can be rerun on the same frozen rule with the dates in between folded in; the held-out start then moves ONLY by a new registration.

## Kill, bars and cut
As the common file. NOT_ENOUGH_DATA at the read date reports the date the 100 trade and 30 cluster bars are both met (the cluster bar, about 2026-12-21). Development read date **2026-12-01**; held out 2026-12-01 on, read once on or after 2026-12-30 only after a LEAD.

## Count
N +2 (fade, control).
