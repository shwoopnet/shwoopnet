# LAG2 log-only request for the build session (DRAFT: send ONLY if LAG2 reads NOT_YET_FALSIFIED)

Status: not sent. LAG2 (README, "Pre-registration: LAG2") has not run when this is written. If it fails, delete this file's request and send nothing.

## What is asked
Add logging only, on the existing Bitcoin 15 minute decision path. **No order, no size change, no new setting, nothing on the page.** The record is what LAG2 would have done, so forward days accumulate with no money at risk.

## What to log, once per Bitcoin market at 120, 90 and 60 seconds before the close (three rows per market)
- `spot`: the latest Kraken XBT/USD trade price (public endpoint, no key), carried forward at most 5 seconds; missing if older.
- `strike`: the market's strike.
- `sigma`: standard deviation of the log returns of spot sampled every 10 seconds over the previous 900 seconds, divided by sqrt(10).
- `p_yes = Phi( ln(spot / strike) / (sigma * sqrt(max(left - 40, 1))) )`, left = seconds to the close. (The settlement is the mean of the last 60 seconds, so its variance is sigma^2 * (left - 40).)
- `ref`: the yes price of the latest Kalshi trade in the previous 15 seconds (missing if none).
- `signal`: `yes` if `p_yes - (ref + 0.01) >= 0.07`; `no` if `(1 - p_yes) - ((1 - ref) + 0.01) >= 0.07`; else none.
- `yesBid`, `yesAsk`, `bidSize`, `askSize` at that moment (for the later quote-level read).
Parity: `studies/lag2_parity_vectors_2026-10-23.json` gives six inputs and the exact `p_yes` outputs; the implementation must reproduce them to six decimals before any row is trusted.

## Safety
Read-only public data; a failed Kraken call logs `missing` and nothing else; the logging must never delay or block the order path. Nothing here may place, size or cancel an order.

## What I do with it
Score the rows after the market settles (the result is already in the bot's data) on days LAG2 has not seen, at the quote level (buy at the logged ask), and read it once on the registered date. A live rule would be a separate, reviewed change the owner asks for.
