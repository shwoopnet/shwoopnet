# ADJWIN1 registration (Desk A, Nov 15, 2026). Written before any data is read. First read, lighter gate.

**Question:** after a 15 minute window in which the market moved a lot, is the next window's first quote (near 50c) priced off its true win frequency?

**Data (only this):** the NC15 1 minute candle history (NC15_CANDLE_HISTORY_REGISTRATION.md; 11 series, 2026-06-01 to 2026-11-13T23:59Z) with market results from its settled lists. NOT the crypto and gold archive: its third 3 is spent, so a read there would be information only. Readers open candles only through heldout_guard_v2 and apply this card's cut (Auditor B cleared the cut below).

**Cut (amended Nov 15 after Auditor B's pre-read answer; by the window's CLOSE time, one cut for all 11 series):** development 2026-06-01 to 2026-08-31; validation 2026-09-01 to 2026-10-03T15:59:59Z. Rows with close_time at or after 2026-10-03T16:00Z (epoch 1791043200) are dropped on load, by close_time before any other field is read: every one of the 11 series has a protected window from that date (FXREF1, the W3 cuts, FXUSD, NEWH2, the crypto-new cards). ADJWIN1 therefore has NO in-history held-out. A pass goes to a forward read only: windows closing from 2026-11-14T00:00Z (after the history end 2026-11-13), read once on the Head's go. NC15DEPTH1's scoring starts 2026-11-19 and is a forward count, not a held-out; this read uses other rules and does not consume its windows.

**Definitions (frozen):**
- Window W of series S closes at t. Previous window P closes at t-900 s, same series. Both must have a candle at their first and last minute and at W's first minute, else W is skipped (counted).
- drift(P) = YES mid at P's last candle ENDING AT LEAST 60 s BEFORE P's close minus YES mid at P's first candle (mid = (bid+ask)/2, candle close prices). This is a quote path, not P's result: a candle ending at the close can carry the settled 0.99 or 0.01 and is not used. Signal: |drift(P)| >= 0.30.
- Entry at the close ask of W's first candle that ENDS AFTER W's open (a candle ending exactly at the open is P's last candle): the ask of the chosen side, only if that ask is 0.40 to 0.60. Held to settlement. One entry per window.
- Arm R (reversal): buy the side AGAINST drift(P) (drift up: buy NO). Arm M (momentum): buy the side WITH drift(P). Each series x arm is one try (22 tries).
- Two-sided quotes required: 0 < bid < ask < 1 on both mids and on the entry side; otherwise skip and count. Candles after close are dropped on load (C8). Results are read only after the cut check. Label: upper bound, not fill-checked.
- Cost: per-order rounded fee fee_up_order(p,10) and the 2c haircut on entry (C11, NC15 series; 1c shown for information). The ask is already the price paid, so the haircut adds to it.
- Stats: per series and arm, n, PF at 1c and 2c, halves floor(n/2) by close time, day-clustered z. "No evidence at n under 100". No pooled pass.

**Prediction (numeric):** at least 3 of the 11 series show an arm with 2c PF of 1.3 or more on development AND validation (validation is Sep 1 to Oct 3) with n of 100 or more on each. **Kill:** no series and arm at 2c PF 1.0 or more on both, or fewer than 100 signals on a series.

**Uniqueness:** 7e rows compared: all the favourite and price-band rows (no, entry at 40c to 60c), lead-lag (no outside reference), OI (none), maker rows (no resting order). Closest: SEARCH1 (price level against frequency, failed) and CALIB3; this conditions on the previous window's path. Mechanism guess for the VA, not a claim: anchoring on the last window. No counterparty is named.

**Plan:** hand case with invented candles first, then the reader (closed by default), Auditor B's quick check, then the Testing Desk input list, then one run committed blind.

**Rule hash:** the reader's sha256 is committed before the first read; each series x arm is one try (22).

## Dated note, 2026-11-15 (appended; no frozen text changed)
A kept market whose result is void, a scalar or missing is dropped by the loader and counted per series ("no result (dropped): SERIES"); its neighbouring windows then show as "not adjacent" skips. A void would refund the price and keep the fee, so dropping voids is a small optimistic bias, and the result line must say so with the per series counts.

## Result, 2026-11-16 (appended; no frozen text changed)
One blind run, print sha256 27f3eb59d3250011f2c599a2073c90a6e7fa17296da6f78dfd5c57932673af9f (ADJWIN1_PRINT_SHA_NOV16.txt, committed before reading). 22 tries, 0 passed. **The development window (June to August) had NO data in these runs (n = 0 for every series and arm), so only validation (Sep 1 to Oct 3) was informative; this is missing data, not a development window that failed.** On validation at the 2c haircut the best arm was HYPE reversal (PF 1.021, n 798, z 0.30) and every other arm was at or below 1.0 (silver reversal 0.989; momentum arms 0.63 to 0.95). The registered bar needs both windows, so it could not be met; the kill rule fires. CLOSED, no candidate.
