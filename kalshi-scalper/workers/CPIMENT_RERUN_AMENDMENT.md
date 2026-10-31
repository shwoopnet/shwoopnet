# Amendment to CPI1 and MENT1 (2026-10-31), written and pushed BEFORE any scorer is run

Task CPIMENT-RERUN. Owner decision (relayed by the main session, Oct 30 evening): rerun CPI1 and MENT1 once each, as registered, with the candle parser fixed. The owner's approval lifts the second-run block for these two only.

## Status of the earlier results
Run 1 of CPI1 (NOT_ENOUGH_DATA, 7 trades on 2 releases) and of MENT1 (NOT_ENOUGH_DATA, 71 events) read only `close_dollars` on both candle paths. Historical candles name the field `close`, so every historical market looked quote-less. Both results are VOID, not FALSIFIED. The rerun is the first valid scoring of either rule.

## The exact code change (and nothing else)
1. New helper `src/scalper/candlefield.py`: `quote_close(side)` returns `close_dollars` if present, else `close` (the same logic as `econnew1.pick`); `candle_volume(c)` returns `volume_fp` else `volume`.
2. `src/scalper/cpi1.py` (candle fetch, line ~76) and `src/scalper/ment1.py` (candle fetch, line ~74) call the helper for the yes_bid and yes_ask closes (and CPI1's unused volume) on both the historical and the live path.
3. The run-once guard: each script's result file is renamed (`cpi1_rerun_result.txt`, `ment1_rerun_result.txt`) so run 1's file no longer blocks this single run; the guard stays on the new file, so a third run is still refused. Marked in the code with a comment and the approval date.
4. Because the cached candle files hold the bad extraction, they are set aside and the candles of both rules are fetched again with the fixed parser (data acquisition only, no outcome read).

## Not changed
Rules, thresholds, universe, windows, splits, judging and kill criteria are exactly the README pre-registrations (CPI1 plus its 2026-10-28 amendment: edge 5c, 24 hour lead, at least 25 independent releases, z bar 2.5, PF bar 1.5, both halves above 1; MENT1: word key, prior weight 5, pool at least 15, edge 8c, decision 8 hours before the earliest close, at least 100 events and 100 trades, PF 1.5, z 2.5, PF at fees x1.2 at least 1.2). No new try is added to N: the rules were already counted (running N about 728,688, z bar 5.27 for the whole ledger).

## Before scoring
A parity check that reads no outcome (candles with a bid and an ask under the old and the fixed extraction, markets per window with a quote at the registered look) is run first and recorded in `workers/CPIMENT_RERUN_RESULT.md`. If the fix reveals a second problem (a different parser or join bug), work stops and it is reported, not patched silently. A quote is not a fill: the registered fill rule is applied exactly; the registration does not bound the spread, so a result with a 10c spread cap is reported as an information line, not a second verdict.
