# Live-against-shadow harness: hand case (Testing Desk, Nov 13, 2026), committed BEFORE the harness and its test
Task from the Head (18:49Z): for each live order of a trial seat find the shadow decision the registered rule would have made in the same window; report the agreement rate, the fill gap against the touch seen on the recorded book, and the disagreeing windows with reason codes. Tools only, INVENTED rows only, no live figure in any file; the live orders arrive later from the nightly report through Main.

## Definitions as built
- Window = one ticker. Live attempt = orderedCount > 0 or count > 0 for that ticker; live side = the order's side. Several live orders in one window: sides are collected; both sides = LIVE_BOTH_SIDES.
- Shadow decision per window, supplied by the card's rule as ("trade", side, price) or ("no_trade", reason) when the rule itself says no, or ("no_data", reason) when data is missing (a data gap is not a rule decision).
- Touch seen: the last recorded book poll at or before the order's send time (sentAtMs, else tickStartMs) and no more than 4 s before it. YES touch = 1 - best NO bid; NO touch = 1 - best YES bid (R6 shape from scorekit.r6_book; NC15 polls must be given in the same shape). No poll in that span = no touch.
- Fill gap (cents) = live fill - touch seen; positive = the live fill was WORSE than the touch.
- Agreement universe = windows where the live seat attempted OR the shadow traded. Agree = same window, same side, both decided to trade (a live attempt that did not fill still agrees: AGREE_LIVE_NOFILL).
- Reason codes: AGREE, AGREE_LIVE_NOFILL, SIDE_MISMATCH, LIVE_ONLY_SHADOW_NO_TRADE (+ the shadow's reason), LIVE_ONLY_SHADOW_NO_DATA (+ its reason), SHADOW_ONLY, LIVE_BOTH_SIDES.
- Output: aggregates plus the disagreeing windows with codes; no dollar figure of the account.

## Invented windows (all prices dollars; send times in seconds on the book's clock)
| id | live | shadow | book at the send time | expectation |
|---|---|---|---|---|
| W1 | NO, ordered 3, filled 3 at .10 | trade NO | poll 1 s before, YES bids [(.90, 5)] -> NO touch .10 | AGREE, gap 0c |
| W2 | YES, ordered 2, filled 2 at .15 | trade YES | poll 2 s before, NO bids [(.87, 4)] -> YES touch .13 | AGREE, gap +2c (worse) |
| W3 | YES, filled 1 at .20 | trade NO | poll 1 s before, NO bids [(.78, 3)] -> YES touch .22 | SIDE_MISMATCH, gap -2c |
| W4 | NO, filled 1 at .30 | no_trade "edge under 5c" | poll 3 s before, YES bids [(.68, 5)] -> NO touch .32 | LIVE_ONLY_SHADOW_NO_TRADE, gap -2c |
| W5 | none | trade YES | | SHADOW_ONLY |
| W6 | YES, filled 2 at .10 | no_data "no decision candle" | poll 0.5 s before, NO bids [(.90, 9)] -> YES touch .10 | LIVE_ONLY_SHADOW_NO_DATA, gap 0c |
| W7 | YES, filled 1 at .11 | trade YES | newest poll 5 s before (too old) | AGREE, no touch |
| W8 | NO, ordered 2, filled 0 | trade NO | | AGREE_LIVE_NOFILL, no fill gap |
| W9 | YES filled 1 at .50 and NO filled 1 at .50 | trade YES | no book | LIVE_BOTH_SIDES, two fills with no touch |
| W10 | none | no_trade "spread above 3c" | | not in the agreement universe |

## Expected output
- windows considered 10; live orders 10 (W1 to W4, W6, W7, W8, W9 twice); filled live orders 9; agreement universe 9 (W1 to W9).
- agree 4 (W1, W2, W7, W8), rate 4 / 9 = 0.4444. Codes: AGREE 3, AGREE_LIVE_NOFILL 1, SIDE_MISMATCH 1, LIVE_ONLY_SHADOW_NO_TRADE 1, LIVE_ONLY_SHADOW_NO_DATA 1, SHADOW_ONLY 1, LIVE_BOTH_SIDES 1.
- fill gap: orders with a touch 5 (W1, W2, W3, W4, W6): gaps 0, +2, -2, -2, 0 cents: median 0, mean -0.4, worse-than-touch share 1 / 5 = 0.2, max +2, min -2; filled orders with no touch 3 (W7 and the two W9 orders); the unfilled order (W8) is excluded.
- Disagreements listed: W3 SIDE_MISMATCH, W4 LIVE_ONLY_SHADOW_NO_TRADE (edge under 5c), W5 SHADOW_ONLY, W6 LIVE_ONLY_SHADOW_NO_DATA (no decision candle), W9 LIVE_BOTH_SIDES.
