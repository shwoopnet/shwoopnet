# FAM2 registration: XLEAD1, macro futures leading the 15 minute Kalshi quotes (written 2026-10-29 before any Yahoo bar is compared with any Kalshi quote or outcome; 4 tries)

Novelty check: `workers/FAM2_CHECK.md` (Family B new; Family A tested as LAD1, not run).

**Disclosed before registering.** Yahoo 1 minute bars were downloaded and only their counts and time ranges read: ES=F 27,294 bars, DX-Y.NYB 26,846, ^TNX 7,977 (cash hours only), all 2026-10-01 13:28 UTC to 2026-10-29 (scratchpad, not committed). Kalshi files' market counts and close ranges were read: `book.sqlite` (Bitcoin, Ethereum, gold to 2026-10-12), `fresh.sqlite` (to 2026-10-27), `five.sqlite` (gold to 2026-10-29). No price, change or outcome was looked at.

**Counterparty.** Kalshi Bitcoin, Ethereum and gold quoters who reprice from the coin's or metal's own feed and not from the macro futures: after a sharp move in the S&P future, the dollar or the 10 year yield they would lag until spot follows, and a taker who reads the macro move first is paid by them. Honest alternative: spot crypto and gold react to these within seconds and the Kalshi quote follows spot within seconds (GOLDFV1, LAG2B), so at minute resolution nothing is left.

**Universe (close time and series only).** Every settled KXBTC15M, KXETH15M and KXGOLD15M market closing from 2026-10-01 14:00 UTC to the last close on file (Bitcoin and Ethereum 2026-10-27 23:45, gold 2026-10-29 15:30), from `book`, `fresh` and `five` (a ticker in two files is taken once, from the later file).

**Signal (fixed).** Decision minute D = end of a Kalshi 1 minute candle, from C - 13 min to C - 4 min (C = close). A Yahoo bar is stamped with its start; only bars with start at or before D - 120 s are read (they ended a full minute before D). r3 = ln(close of the bar starting D - 120) - ln(close of the bar starting D - 300); for ^TNX the same on the yield level. sigma1 = standard deviation of the 1 minute log changes of the 60 bars starting D - 3,660 to D - 120, at least 45 present. **Shock:** both r3 bars present and |r3| at least 2.0 x sigma1 x sqrt(3). The first shock minute of a market is its only signal for that try.

**Side.** V1, V2: Bitcoin and Ethereum, ES=F up -> buy YES, down -> buy NO. V3: gold, DX-Y.NYB up -> buy NO, down -> YES. V4: gold, ^TNX up -> buy NO, down -> YES. Signs fixed from the usual correlations (crypto with stocks, gold against the dollar and real yields), not from this data.

**Entry and exit.** Buy the side at the closing ask of the Kalshi candle ending at D (the YES ask, or 1 minus the YES bid for NO), only if both bid and ask exist, ask not below bid, and the side's price is 0.10 to 0.90. V1, V3, V4: hold to settlement. V2: sell at the side's closing bid of the candle ending D + 180 s; if that candle has no bid, hold to settlement (counted). Conservative check: entry at the next candle's closing ask (ending D + 60). Zero-volume entry candles reported both ways (kept, and dropped as unfillable).

**Fees.** 7% x C x p x (1 - p) rounded up to the cent per order, C = 1 and C = 10, on every buy and sell; fees x1.2 check.

**Windows (by close date, UTC).** W1 2026-10-01 to 10-09, W2 10-10 to 10-18, W3 10-19 to the end. W3 is the holdout, read once and only after the W1 and W2 verdict lines are written.

**Bar (unchanged).** PF at least 1.5 in each window after fees, at least 30 trades a window, positive at fees x1.2, deflated z at the bar for N about 439,000 (z about 5.17), counterparty named above. Kill: PF under 1.0 in W1 or W2 is FALSIFIED without reading W3. Under 30 trades in a window: NOT_ENOUGH_DATA.

**Information, decides nothing.** Lag profile: correlation of the macro bar's 1 minute log change (bar starting t) with the Kalshi YES mid change over the candle ending t + 60 + 60k, k = -2 to +3 (ES with Bitcoin and Ethereum mids between 0.15 and 0.85, DXY and TNX with gold). A lag would show as a positive (or, for DXY and TNX against gold, negative) value at k = 1 or later.

**Prediction.** The lag profile peaks at k = 0 and is near zero from k = 1; all four tries PF under 1.2 in W1 or W2: FALSIFIED. Prior for a pass: under 3%.

**Count.** 4 tries (V1 to V4). Running count about 438,674 plus other workers' tries.
