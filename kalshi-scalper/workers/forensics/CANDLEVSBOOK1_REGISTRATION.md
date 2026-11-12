# CANDLEVSBOOK1 registration: is the 1 minute candle's ask close the order book's ask at the minute's end? (2026-11-12, committed BEFORE any candle was obtained or anything computed)

Asked for by the Head of R&D (message, Nov 12) for the re-specified CFRTI-K, which would take both prices from Kalshi's 1 minute candles. A measurement: no rule scored, no settlement result loaded, zero tries. This desk makes no Kalshi request: the candles must come from a file another desk already holds or fetches with its own allocation, committed with no result column.

**Constants.** `KXBTC15M`, windows that have an R6 book, closes from 2026-10-29T22:15:00Z up to and including 2026-11-11T23:59:59Z (no outcome is read, so the later days may be used). Candle input needed per candle: ticker, the candle's end time (`end_period_ts`), and the close of the YES bid and the YES ask.

**Primary comparison (the instant the rule would use).** The candle ending 120 seconds before the close. Cheaper side by the candle's own closes (YES ask = ask close; NO ask = 1 minus the bid close), ask c in [0.03, 0.30] (CFRTI's band) and separately [0.05, 0.30]. Book ask of the same side at the last usable R6 poll at or before the candle's end time (no more than 4 s earlier) and at the first poll after it; the bracket measure as in QUOTEVSBOOK1. d = c minus the book ask. Reported: share within 1c; shares with the candle 2c, 4c, 10c or more below and above the book; mean, median, mean absolute; intervals by resampling windows.

**All minutes.** The same for every candle ending 14 to 1 minutes before the close, to see whether any disagreement depends on the time left.

**Time shift.** The disagreement with the book taken k seconds from the candle's end time, k = -20 to +20, to find whether the candle close is the book at the minute's end (k = 0), an earlier state (a delayed copy, k negative), a later one, or something else such as the last trade-time quote. Reported: the k with the smallest mean absolute difference, and the curve.

**Reading rule, fixed now.**
- "The candle close is the book at the minute's end": the best shift is within 2 s of zero and at least 90% of primary rows are within 1c on the bracket measure.
- "The candle is a delayed or advanced copy": the best shift is 3 s or more from zero, with the agreement at that shift stated.
- "The candle close is something else": under 90% within 1c at every shift; say how far off and in which direction.
- Under about 100 windows: "no evidence at n = x".
