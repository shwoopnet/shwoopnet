# OIVER-DEPTH build 2: rules as read and expected figures by hand (History Miner, Nov 13, 2026)

Written BEFORE the code, from Desk A's card 3 only: `kalshi-scalper/workers/DESK_A_OICORE_VERSIONS_NOV13.md` at 741092a7 (sha256 e7b918b0), under the Head of R&D's 19:53Z convention for the OIVER builds. Desk A's build was not read. No real row read and no run.

## Rules as built
The parent is OICORE exactly as in OIVER-SPREAD build 2 (quote at the close - 180 decision time, OI rise >= 86,300, rule 18, cheaper ask with a tie to YES, band [0.08, 0.50], ask seen and assumed filled (an upper bound), fee per order at C = 20, void a fee-only loss).
**VERSION:** the parent's trade, kept only if the contracts displayed at the touch the order would meet are at least 2 x the order size = 2 x 20 = 40. That touch is the YES ask size for a YES buy and the YES bid size for a NO buy. Under 40 is counted as depth_thin. A missing, non-numeric or non-finite size is counted as no_size. Both are skipped. No spread or cap condition.
Inputs: the OIVER windows columns plus yes_bid_size and yes_ask_size at the decision time. Per the card these come from R6 books (the YES ask size is the best NO bid's size); that row builder is separate and not written.
Printed as in OIVER-SPREAD, with the same takeover and kill information and "no evidence at n = x" under 60 (the card's own NOT_ENOUGH_DATA line is below 100 signals with a recorded size by 2027-02-26). A held-out read is refused.
**Open readings for the Head:**
- (a) The order size is C = 20, so the need is 40, and a size of exactly 40 is kept.
- (b) The sizes are the book at the same decision time as the quote; the row builder must match them.

## Made-up windows: inv/windows.csv = OIVER-SPREAD's ten plus two size columns
| W | side | touch size used | version | parent net |
|---|---|---|---|---|
| 1 | YES | yes_ask_size 40 | keep (40 >= 40) | +0.7675 |
| 2 | NO | yes_bid_size 39 | depth_thin | -0.315 |
| 3 | NO | yes_bid_size blank | no_size | +0.8725 |
| 8 | YES | yes_ask_size 500 | keep | -0.5075 |
| 9 | NO | yes_bid_size 100 (its yes_ask_size of 5 is not the touch it meets) | keep | -0.325 |
The other windows do not trade.

**Parent:** unchanged, PF 1.429194 over 5, net 0.4925, halves 2.436508 / 1.048048, 41.37 per contract-week.

**Version:** W1, W8 and W9.
- n 3; wins 0.7675; losses 0.8325; PF 0.921922; net -0.065; mean -0.021667.
- Halves: W1 gives inf, and W8 with W9 gives PF 0.0.
- Per contract-week: -0.065 x 84 = -5.46.

**Removed share:** 0.4.

**Counts:** oi_below 1, cheap_skipped 1, no_quote 2, held_out_ignored 1, depth_thin 1, no_size 1.

**Takeover (info):** PF lift no, net per week no, second half no, 60 signals no.
**Kills (info):** removed more than half no, PF below the parent's YES.
**Label:** "no evidence at n = 3".

## Refusals expected
- held mode
- a HELDOUT_ path
- an odd result text
