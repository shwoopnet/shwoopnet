# FLIPS_0 log-only request for the build session (the owner said "go" on 2026-10-23)

Add logging only. **No order, size, entry-time or cap changes; nothing on the page.** The aim is forward evidence for a shape rule from real live windows, with no money at risk.

## Rule being logged (README, "IDEAS100 result" and "FLIPS0-X result")
At the decision candle of each market (the 1 minute candle the bot already reads at its entry time; log it for Bitcoin and Ethereum at their 6 minute decision, and for every other live series at the entry time it uses):
1. `path`: the favourite side's mid for every 1 minute candle of the market from its first candle up to and including the decision candle, oldest first. The favourite side is the side the bot would buy at that tick (the one whose ask is inside its entry band); if no side qualifies, log nothing. Side mid is (yesBid + yesAsk) / 2 for YES and 1 minus that for NO.
2. `flips`: ignore minute changes of 0.004 or less; then count the sign changes between consecutive remaining changes.
3. `flips0`: true when there are at least 4 earlier candles (the path has at least 5 points) AND `flips` is 0.
4. Log `ticker`, `series`, `side`, `askAtDecision`, `earlierCandles`, `flips`, `flips0` with each order record (and for each candidate the bot considers but does not take, if that is already logged for `rise3`).
Parity: `studies/flips0_parity_vectors_2026-10-23.json` has six paths with the exact `flips` and `flips0`; the implementation must reproduce them before any record is trusted.

## What I do with it
Score the records after settlement on days FLIPS0-F has not seen, and compare the flips0 orders with the others of the same series (each against its own series average). The registered forward read of the same rule on public candles is 2026-11-12. A live use (an extra order only on a flip-free climb, in its own lane) would be a separate, reviewed change the owner asks for.
