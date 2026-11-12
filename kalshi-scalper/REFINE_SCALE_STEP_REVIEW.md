# Review: [live figure removed, ask Main]

Requested by main at the owner's direction. [live figure removed, ask Main] I changed no code. OICORE scaling is not part of this review.

## What the code does today (so the question is clear)

- [live figure removed, ask Main]
- [live figure removed, ask Main] So once the cap reaches the 2% size, the cap stops mattering. [live figure removed, ask Main] It only makes the cap get there sooner.**

## (1) How fast the size reaches its target, from the live record

[live figure removed, ask Main]

Two readings, and I cannot tell them apart from the report:
- **A. [live figure removed, ask Main] It did not: it stayed at 11 for nine days. That does not fit A unless the review timer was reset (for example by the Oct 23 Start).
- **B. [live figure removed, ask Main]

Replay under each, from the cap of 12 on Nov 1:
| | +1 per review | +2 | +3 | 2% rule limit |
|---|---|---|---|---|
| A ($779, target 18, 2% size 16): reviews on Nov 4, 7, 10, 13 | 13, 14, 15, **16 on Nov 13** | 14, 16 on **Nov 7** | 15, 16 on **Nov 7** | 16 |
| B ($540, target 12, 2% size 11) | 12, no change | 12 | 12 | 11 |

So under A the larger step reaches the same ceiling (16) six days sooner (Nov 7 against Nov 13), and +2 gets there on the same day as +3. [live figure removed, ask Main] A deposit is what a faster step would respond to: a $400 deposit adds 9 to the target, which takes 27 days at +1, 9 days at +3.

**What I need to settle A or B:** the values in `kalshiLiveControl/sizing` (cap, base, reviewedAt) and the balance by date. I cannot see them from here and did not guess.

## (2) What one loss costs at each size

[live figure removed, ask Main] [live figure removed, ask Main]

| Contracts | [live figure removed, ask Main] |
|---|---|---|---|---|---|
| 13 | $9.6 | $11.4 | $12.7 | $12.6 | $25.2 |
| 16 | $11.8 | $14.1 | $15.7 | $15.5 | $31.0 |
| 20 | $14.8 | $17.6 | $19.6 | $19.4 | $38.8 |
| 24 | $17.8 | $21.1 | $23.5 | $23.3 | $46.6 |

[live figure removed, ask Main]
- [live figure removed, ask Main] Open orders count as lost, so a bad window plus a few settled losses gets there sooner than the table says.
- **5.5% window cap:** $42.8 / $29.7. [live figure removed, ask Main]
- [live figure removed, ask Main]

## (3) Does the record show loss rate or no-fill share changing with size?

Orders by ordered contracts (all history, gold; [live figure removed, ask Main]
| | Orders | No-fill share (95% range) | Settled fills | Losses (rate, 95% range) |
|---|---|---|---|---|
| Gold 1 to 5 | [live figure removed, ask Main] |
| Gold 6 to 10 | [live figure removed, ask Main] |
| Gold 11 to 15 | [live figure removed, ask Main] |
| Gold 16 and up | [live figure removed, ask Main] |
| Dogecoin 1 to 5 | [live figure removed, ask Main] |
| Dogecoin 11 to 15 | [live figure removed, ask Main] |

[live figure removed, ask Main]

## (4) Recommendation

[live figure removed, ask Main]
1. At today's balance the step pace is not what limits size. Under reading A the cap catches the 2% size (16) in 12 days at +1; under B the cap is already at the target. [live figure removed, ask Main]
2. [live figure removed, ask Main]
3. [live figure removed, ask Main]
4. A faster ladder matters mainly after a deposit, and the owner can already do that deliberately (a Stop then Start jumps straight to the target).

[live figure removed, ask Main]

[live figure removed, ask Main] [live figure removed, ask Main]

## Count for deflation
This review looked at 6 bucket comparisons and 2 scenarios: about 8 tries, N about 728,691. Nothing here is a finding about edge; it is arithmetic on the sizing rules plus a descriptive table.
