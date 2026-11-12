# CANDLEVSBOOK1 result: the 1 minute candle's ask close IS the order book's ask at the minute's end (2026-11-12)

Registration: `CANDLEVSBOOK1_REGISTRATION.md` (commit a15090e) with Amendment 1 (064c7f1), both before any candle was obtained. Script `candlevsbook1.py` (0c565f5, unchanged since), raw output `results/CANDLEVSBOOK1.json`. Candles: Desk A's slice `kalshi-scalper/workers/desk_a_verify/cfrti_candle_slice.csv` on `claude/idea-desk-a` (commit 7fa651b; pull run CFRTI_K_R6SLICE; columns ticker, end time, YES bid close, YES ask close; no result column, and the script refuses a file that has one). A measurement: no rule scored, no settlement result loaded, zero tries. This desk made no Kalshi request. Nothing about the live account.

**Sample.** `KXBTC15M`, closes 2026-10-29 22:15Z to before 2026-11-05. 407 windows with candles and an R6 book; 5,698 two-sided candles ending 14 to 1 minutes before the close. d = the candle's ask close minus the book's ask for the cheaper side; negative means the candle shows a cheaper ask than the book. Intervals 95%, resampling windows.

## Verdict by the registered rule

**"The candle close is the book at the minute's end."** Both conditions are met: the best time shift is 0 seconds, and 95.9% of primary rows are within 1c on the bracket measure (the bar was 90%).

| | Primary: candle ending 120 s before the close, cheaper side 5c to 30c | Same, 3c to 30c | All minutes 14 to 1, 5c to 30c |
|---|---|---|---|
| Rows / windows | 122 / 122 | 145 / 145 | 2,321 / 405 |
| **Within 1c, bracket measure** | **95.9% (91.8 to 99.2)** | 96.6% (93.1 to 99.3) | 98.4% (97.8 to 98.9) |
| Mean d, bracket | -0.02c (-0.12 to +0.08) | -0.02c | 0.00c |
| Mean absolute d, bracket | 0.19c | 0.17c | 0.10c |
| Candle 2c or more BELOW the book, bracket | 2.5% (0 to 5.7) | 2.1% | 0.8% |
| Candle 4c or more below | 0% | 0% | 0.1% |
| Candle 2c or more ABOVE the book | 0.8% | 0.7% | 0.5% |
| Within 1c against the nearest single poll | 85.2% | 87.6% | 92.0% |
| Best shift (smallest mean absolute difference) | 0 s | 0 s | 0 s |

("Bracket" counts the candle as agreeing when its close lies between the book ask at the poll just before the minute's end and the poll just after. R6 polls every 2 seconds, so against one single poll up to 2 seconds away the agreement is lower; that is the book moving between polls, not the candle being off.)

**Time-shift curve, primary rows, 5c to 30c** (mean absolute difference to the nearest poll; share within 1c on the bracket):

| Book taken | -12 s | -6 s | -4 s | -2 s | -1 s | **0** | +1 s | +2 s | +4 s | +6 s | +12 s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Mean absolute difference | 5.3c | 3.4c | 2.7c | 1.7c | 1.1c | **0.6c** | 1.2c | 1.8c | 3.5c | 4.5c | 6.2c |
| Within 1c | 25% | 42% | 63% | 84% | 92% | **96%** | 93% | 84% | 64% | 46% | 20% |

The curve has a sharp minimum at zero and is nearly symmetric. A copy even 2 seconds old would have put the minimum at -2, where agreement is already 12 points lower. The quote recorder's list quote, measured the same way, had its minimum at -5 to -6 seconds and topped out at 76%.

**By minutes left** (all candles, 5c to 30c, bracket within 1c): 99% or better from 14 down to 5 minutes left; 97% at 4; 98% at 3; 96% at 2; **80% at 1 minute left**. In the last minute the book moves several cents within a 2 second gap, so the comparison itself is coarser there; this file cannot say whether the candle is also less exact in the last minute.

## What it means

1. **A 1 minute candle's bid and ask close can be used as "the book at that minute's end" on this series**, to within about a second and about a cent. It is a current source, unlike the market list.
2. **It is one instant per minute.** A rule priced at a candle close can only act at a minute boundary, and the price is the one at that boundary, not a few seconds later. Whether an order sent then still gets that price is the fill haircut already measured on books (FILLHAIRCUT1: at the ask seen, about two thirds fill 2 to 6 s later on the Bitcoin cheap side; with +1c, 76% to 84%). That haircut still applies to any candle-priced figure.
3. **For CFRTI-K**: its re-specified decision price (the market's own 1 minute candle close at close minus 120 s) is a fair price for the development read. The stale-copy problem that voided the quote-recorder figures does not carry over.
4. **For Desk B's sports measurements and other series**: this was measured on one series over six days. The candle endpoint is the same for every market, so the natural expectation is that it holds elsewhere, but it is measured only here; a thin market whose book is often one-sided would need its own check before a seconds-level claim.
5. **For the audit**: candle-based results (FALS3, W-SPOTGOLD1 and 2, the calibration families, the live strategies' research) are not touched by the stale-quote problem, as far as price freshness goes.

## Caveats

Six days, one series, 2 second book polls. The candle's close is compared with the top of book; sizes are not in the candle. Candles with a one-sided book were dropped by the registered filter (ask above bid, both present). The last minute is weaker for the reason given. Not checked by the Verification Analyst.
