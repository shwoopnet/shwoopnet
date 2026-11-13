# PROVEN-BAR read for OICORE, SECOND BUILD: hand case (Testing Desk, Nov 13, 2026), committed BEFORE the code
The Head's task (19:20Z, the owner's priority "prove a strategy, OICORE first"; Refinement runs build 1): from the nightly report's slot rows for strategy OICORE (settled, filled), in fill order, split into 3 equal windows by fill count; cash PF per window from avgFill and avgFee on the fill-booked cash basis (fillCost in functions/kalshiLiveLib.js), unrounded; PROVEN if at least 2 of 3 windows are at 1.3 or better with n of 100 or more, otherwise NOT YET with the figures. INVENTED rows only; no live figure in any file; results go by message only.

## The cash basis as I read fillCost (functions/kalshiLiveLib.js, origin/main)
- side price = avgFill for a YES order, 1 - avgFill for a NO order (Kalshi's averageFillPrice is the YES price); cost = (side price + avgFee) x count. Valid only if 0 < avgFill < 1 and 0 <= avgFee < 1 and count > 0; otherwise fillCost falls back to the limit booking maxCost, which the report row does NOT carry, so such a row is EXCLUDED and COUNTED (it is not guessed).
- settled payout: count x $1 if result equals the side, else 0; cash result = payout - cost. A void is price refunded, fee kept: -(avgFee x count). A result of "exit" (the exit watch sold some contracts: exitProceeds is not in the report row) is EXCLUDED and counted.
- Rows used: strategy exactly "OICORE", count > 0, settledPnl present (settled). Others are excluded and counted by reason.
- Fill order = ascending ts (ISO text), stable for ties. Windows by FILL COUNT = by number of filled orders (rows), window i = rows[i*n // 3 : (i+1)*n // 3] (sizes differ by at most 1). n in "n of 100 or more" = the window's order count.
- PF per window = sum of positive cash results / -(sum of negative cash results), unrounded (no losses: infinity; no wins and no losses: undefined). A window counts as "at 1.3 or better" if PF >= 1.3 - 1e-9 AND its n >= 100. PROVEN if at least 2 of the 3 windows count; otherwise NOT YET with the figures.
- Python version and interpreter path print first (built-in sum is compensated on Python 3.12 and later).

## Invented rows
Every order: count 10, avgFee .02. YES side avgFill .20 (side price .20), NO side avgFill .80 (side price .20): both cost (.20 + .02) x 10 = 2.20. A win pays 10: cash +7.80. A loss: -2.20. A void: -0.20.
PF of a window with w wins and l losses = 7.8 w / (2.2 l).
- Set A (300 rows, ts ascending, sides alternate YES and NO, win when result equals the side): window 1 (rows 1 to 100): 30 wins 70 losses: PF 234 / 154 = **1.5195**; window 2: 25 wins 75 losses: 195 / 165 = **1.1818**; window 3: 28 wins 72 losses: 218.4 / 158.4 = **1.3788**. Two of three at 1.3 or better with n 100 each: **PROVEN**.
- Set B (as A with window 3 at 25 wins): 1.5195, 1.1818, 1.1818: one of three: **NOT YET**.
- Set C (299 rows, windows of 99, 100, 100, window 1 at 30 wins of 99 (PF 234 / 151.8 = 1.5415), window 2 at 30 of 100 (1.5195), window 3 at 25 of 100 (1.1818)): window 1 has n 99, so only window 2 counts: **NOT YET** (n shown).
- Set D (300 rows, windows at 1.5195, 1.5195, 1.1818 but fed in REVERSED row order): the reader sorts by ts: **PROVEN** exactly as in the ordered case.
- Exclusions (added to Set A, none changes a figure): one OICORE row unsettled (settledPnl absent), one with count 0, one strategy "L2X", one with result "exit", one with avgFill 1.2, one with avgFee 1.5, one with avgFill null: each counted in its own exclusion bucket (7 excluded). One void row inside the window it falls in is a -0.20 loss.
- Boundary: a window with PF exactly 1.3 (wins 13 x 7.8 / ... see the test: 100 rows, w = 38, l = 62: 296.4 / 136.4 = 2.17; the exact-1.3 case is built from net values 1.3 and -1.0 repeated: 65 wins of +1.3 and 100 - 65... PF 84.5 / 65 for 65 wins of 1.3 and 65 losses of 1.0 in 130 rows: exactly 1.3) counts as at 1.3 (inside 1e-9); PF 1.2999 does not.
