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

## Dated line, 2026-11-13 21:17Z: the governing card is Desk A's 23b5bd9b (sha256 ae1f1ee6...), with its 21:13Z and 21:14Z lines; reworked by hand before the code
- **Replay set:** the comparison is the parent's trades that HAVE an R6 decision poll against the version on that same set. A parent trade with no poll is left out of both, counted as no_poll. The input gains a column r6_poll (1 or 0), which the R6 builder writes.
- **Open reading:** a poll whose touch size is blank or non-finite stays in the replay set, and the version skips it as no_size.
- **Keep:** the touch holds >= 40 (inclusive), unchanged.
- **Range:** a development row outside [2026-10-29T00:00Z, 2026-11-09T00:00Z), DEPTH's intersection of the candle and R6 ranges, STOPS the run. Held-out rows (on or after Dec 1) are ignored and counted.
- no_quote is renamed not_two_sided.
- **Weeks** are taken over the REPLAY SET's parent trades, at least one week, with the same divisor for both.

### Reworked made-up data
inv/windows.csv gains r6_poll: W3 = 0 (it had a blank bid size; it is now a trade with no poll); every other row = 1. The sizes are unchanged.
- **Replay parent:** W1, W2, W8, W9; nets +0.7675, -0.315, -0.5075, -0.325.
  - wins 0.7675, losses 1.1475, PF 0.668845, net -0.38, mean -0.095;
  - halves (first 2): W1 and W2 give PF 2.436508, W8 and W9 give PF 0.0;
  - weeks: W1 to W9 is under a week, so the divisor is 1 and the parent is -0.38 per contract-week.
- **Version:** W1 (ask size 40, kept), W2 (bid size 39, depth_thin), W8 and W9 kept.
  - PF 0.921922, net -0.065, mean -0.021667, halves inf / 0.0, per contract-week -0.065.
- **Removed share:** 1 - 3/4 = 0.25.
- **Counts:** oi_below 1, cheap_skipped 1, not_two_sided 2, held_out_ignored 1, no_poll 1, depth_thin 1.
- **Takeover (info):**
  - PF lift: yes (0.921922 >= 0.668845 + 0.10 = 0.768845).
  - Net per week not lower: yes (-0.065 >= -0.38).
  - Second half not worse: yes (0.0 >= 0.0).
  - 60 signals: no.
- **Kills (info):** removed more than half no; PF below the parent's no.
- **Label:** "no evidence at n = 3".
- The full parent (with W3) is not this comparison and is not printed for DEPTH.

## Dated line, 2026-11-13 21:30Z: the counter name (the Head's ruling of 21:19Z; Desk A card c356ca2d)
A poll with a blank or unreadable touch size stays in the replay set and the version skips it. This was already built that way; the counter is renamed from no_size to size_unknown. No figure changes. The made-up set has no such row, so the count is absent there.

## Dated line, 2026-11-13 21:30Z: voids (Auditor B's 16b finding of 21:28Z; Desk A's sheet v2 G5; the Head's ruling of 21:29Z), reworked by hand before the code
- Results "yes" and "no" are scored.
- "void" or blank on a development row is DROPPED: it is not a bet, not in n, not in the PF. It is counted as void_dropped, at the point where the parent would have traded. This means after every signal test (and, for DEPTH, after the replay-set test), before the trade is booked.
- Any other text still STOPS.
- Before this line a void was booked as a fee-only loss and a blank stopped the run; both are withdrawn.
- **Base figures:** unchanged, since the made-up development rows carry no void or blank.
- **New variant test:** the base windows plus two rows, W11 and W12, closing 1794009000 and 1794009900, both inside the range. The variant must give every base figure unchanged, plus counts void_dropped 2.
  - W11: a copy of W1 (r6_poll 1, ask size 40), result "void".
  - W12: a copy of W9 (r6_poll 1, NO buy, bid size 100), result blank.
