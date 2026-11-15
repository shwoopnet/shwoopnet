# ADJWIN1 registration (Desk A, Nov 15, 2026). Written before any data is read. First read, lighter gate.

**Question:** after a 15 minute window in which the market moved a lot, is the next window's first quote (near 50c) priced off its true win frequency?

**Data (only this):** the NC15 1 minute candle history (NC15_CANDLE_HISTORY_REGISTRATION.md; 11 series, 2026-06-01 to 2026-11-13T23:59Z) with market results from its settled lists. NOT the crypto and gold archive: its third 3 is spent, so a read there would be information only. Readers open candles only through heldout_guard_v2 and apply this card's cut. Whether any open card holds dates inside this range is for Auditor B's reading of HELDOUT_REGISTRY.md; I read nothing until the answer.

**Cut (by the window's CLOSE date, frozen now):** development 2026-06-01 to 2026-08-31; validation 2026-09-01 to 2026-10-15; held-out 2026-10-16 to 2026-11-13, read once on the Head's go and only for a rule that passed development and validation.

**Definitions (frozen):**
- Window W of series S closes at t. Previous window P closes at t-900 s, same series. Both must have a candle at their first and last minute and at W's first minute, else W is skipped (counted).
- drift(P) = YES mid at P's last candle minus YES mid at P's first candle (mid = (bid+ask)/2, candle close prices). Signal: |drift(P)| >= 0.30.
- Entry at W's first candle at or after its open: the ask of the chosen side, only if that ask is 0.40 to 0.60. Held to settlement. One entry per window.
- Arm R (reversal): buy the side AGAINST drift(P) (drift up: buy NO). Arm M (momentum): buy the side WITH drift(P). Each series x arm is one try (22 tries).
- Cost: per-order rounded fee fee_up_order(p,10) and the 2c haircut on entry (C11, NC15 series; 1c shown for information). The ask is already the price paid, so the haircut adds to it.
- Stats: per series and arm, n, PF at 1c and 2c, halves floor(n/2) by close time, day-clustered z. "No evidence at n under 100". No pooled pass.

**Prediction (numeric):** at least 3 of the 11 series show an arm with 2c PF of 1.3 or more on development AND validation with n of 100 or more on each. **Kill:** no series and arm at 2c PF 1.0 or more on both, or fewer than 100 signals on a series.

**Uniqueness:** 7e rows compared: all the favourite and price-band rows (no, entry at 40c to 60c), lead-lag (no outside reference), OI (none), maker rows (no resting order). Closest: SEARCH1 (price level against frequency, failed) and CALIB3; this conditions on the previous window's path. Mechanism guess for the VA, not a claim: anchoring on the last window. No counterparty is named.

**Plan:** hand case with invented candles first, then the reader (closed by default), Auditor B's quick check, then the Testing Desk input list, then one run committed blind.
