# Settlement mechanics: gold and Bitcoin 15 minute markets (V2, 2026-10-29, read from Kalshi's own market and series objects)

## Gold, KXGOLD15M (source: Pyth, "Metal.Index.1OZGOLD/USD")
- **Rule (rules_primary):** YES if the close price of the 1 minute candlestick for Gold at the close time is at least the strike (`floor_strike`, e.g. 4013.70; `strike_type: greater_or_equal`).
- **Which price:** the candle stamped one minute before the close, whose close is the price AT the close instant (rules_secondary: "the candlestick timestamped 4:59 PM ... closes at 5:00:00 PM"). One price, one instant, rounded to 2 decimals. No averaging.
- **When it becomes public:** at the close instant; until then, the outcome depends on the last tick before it. If Pyth publishes nothing for that time, the most recent published value is used.
- **Consequences for design:** the whole outcome can turn in the final seconds; a favourite near the strike carries full point risk to the last tick (unlike Bitcoin). Pyth aggregates many publishers; the COMEX future leads or tracks it within the minute (GOLDFV1). Pyth's history needs a key; live Pyth prices are public (Hermes, keyless for latest).

## Bitcoin, KXBTC15M (source: CF Benchmarks BRTI)
- **Rule:** YES if the simple average of the 60 seconds of BRTI before the close is at least the simple average of the 60 seconds of BRTI before the open. The strike (`floor_strike`) IS that opening average.
- **When information becomes public:** BRTI is a once-a-second index over constituent exchanges (Coinbase, Kraken, Bitstamp, Gemini, itBit, LMAX and others; check CF's methodology for the current list). In the final 60 seconds the settlement value is partly fixed: with s seconds left, (60 - s)/60 of the average is already observed. At 30 s left half of it is known; the remaining uncertainty shrinks with roughly the square root of s times s/60.
- **Consequences for design:** a favourite in the last minute is safer than its distance from the strike suggests, if the market prices the point price instead of the average (L9 tested this on minute candles and was FALSIFIED; nothing tested it at second resolution). The averaging also means the price at the close instant does not settle it, unlike gold.

## What has and has not been tested against these mechanics
- Tested on minute data: L8 (averaged strike at the open), L9 (final-minute averaging), IV1, H7 (fair value with realised or implied volatility), GOLDFV1 and XMAC1 (outside prices, minute bars).
- NOT tested: anything at second resolution in the last 60 to 150 seconds, where both mechanics bite. Data for it: the quote recorder (Kalshi quotes about every 0.6 s in the last 150 s, Bitcoin with Coinbase, Kraken and Bitstamp trades, gold since Oct 28), and recorder R6 (whole-window books every 2 s and every trade, from Oct 29 22:03 UTC).
