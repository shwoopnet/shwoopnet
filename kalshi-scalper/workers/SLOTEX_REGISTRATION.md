# SLOTEX registration (2026-10-30, written and pushed before any scoring)

Worker SLOTEX, Strategy Research V2. Research only, information only, no promote verb.

## What is scored
GEN6's PURE open interest core on Bitcoin (`KXBTC15M`), reusing `src/scalper/fals4.py` (which reproduces GEN6: disc n 222 PF 2.28, val n 333 PF 1.85, hold, next-candle ask fill), under exits the second slot's guard rails allow (every exit before settlement).

- Signal: candle ending 180 s before the close. Cheap side = first of YES, NO whose ask is 5c to 50c at the signal candle. Condition: oi(-180 candle) minus oi(-360 candle) > 86,300 (`THRESH` in fals4). No other condition.
- Entry fill: (N) next candle's closing ask (candle ending -120 s), the default; (S) the signal candle's own ask (-180 s).
- Exits (sell at a candle's closing bid of the side held):
  1. HOLD: settlement baseline (reference only, not slot-legal).
  2. X60: sell at the bid of the candle ending 60 s before the close.
  3. TP5: first candle after the entry candle with bid >= entry + 5c, sold at that bid; else X60.
  4. TP8: same with +8c.
  5. TP5/SL2, 6. TP5/SL3, 7. TP5/SL4: TP5 plus a stop (first candle after entry with bid <= entry - stop, sold at that bid; if TP and stop both touch in one candle, the stop counts); else X60.
- Candles scanned for TP/stop run from the candle after the entry candle up to and including -60. **Stated in advance:** with fill (N) the only such candle is -60 itself, so TP5, TP8 and the stops collapse to X60 exactly for (N); they differ only for (S) (candles -120 and -60). Candle bid is a 1 minute close snapshot; intra-minute touches are not seen.
- Fees: 7% x C x p x (1-p) rounded up to the cent per order, C = 10, on the entry AND on each sell; settlement no fee. A sell-point bid of 0 or missing is a total loss of the stake (no sale, no sell fee).
- Cost checks per exit and fill: base, fees x1.2 (both legs), entry fill +2c.
- Stages: discovery 2026-08-06 to 2026-09-20, validation 2026-09-21 to 2026-10-27. No window closing on or after 2026-10-28 is touched. No holdout read here (that belongs to GEN6's own forward registration).

## Counterparty
As GEN6: late takers piling into the favourite as open interest jumps, who overpay for the near-certain side and leave the cheap side underpriced. Exiting at 60 s instead of holding only captures that if the cheap side's bid rises before the close; otherwise the edge lives in the settlement payoff and an early exit gives it back.

## Prediction (numeric, before scoring)
X60 with fill N: PF below 1.2 in validation (most cheap-side value is in the settlement payoff; a 60 s bid on a 5c to 50c side that has not yet moved is near the entry less the spread, and two fees are paid). Share of entries with a nonzero bid at 60 s: 70% to 95%. TP variants with fill S: PF within 0.3 of X60.

## Kill criteria
Any slot-legal variant (2 to 7) with PF < 1.5 in either stage at the base cost, or <= 1.0 at fees x1.2 or at fill +2c, is FALSIFIED as a slot exit. A variant at PF >= 1.5 in both stages and > 1.0 on both cost checks is only NOT_YET_FALSIFIED (it needs a forward test registration; two windows here, not three).

## Variant count
7 exits x 2 entry fills x 3 cost settings = 42 variants, x 2 stages = **84 cells. N added = 84.**
(Of these, the (N) rows of TP5, TP8 and the three stops are identical to X60 by construction; they are counted anyway.)

Code: `src/scalper/slotex.py`. Result: `workers/SLOTEX_RESULT.md`.

## Amendment 1 (2026-10-30, lead's addendum; pushed before any of these cells is scored)

The C = 10 table was already scored (commit eb64780). Added, not yet scored:

- **Contract count:** every one of the 42 variants (7 exits x 2 fills x 3 costs) also at C = 1 and C = 5 (fees rounded up per order, so 1 contract pays at least 1c each way). 42 x 2 new sizes x 2 stages = **168 new cells**.
- **Entry price buckets:** at base cost, for every exit x fill x C (7 x 2 x 3), entries split by the raw entry fill (under 10c, 10c to 20c, over 20c): n, PF, mean fee per contract (entry plus sell fees, divided by C). 42 x 3 buckets x 2 stages = **252 new cells**.
- Same stages, same rules, same kill rule (applied to the C = 1 and 5 rows as to C = 10; buckets are descriptive only, no verdict per bucket).

**N added for SLOTEX now = 84 + 168 + 252 = 504.**
