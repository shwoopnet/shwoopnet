# Review: raising SCALE_STEP from +1 to at most +3 contracts per 3 day review (gold and Dogecoin; Nov 1, 2026, 6:30 PM CT; read only, nothing live)

Requested by main at the owner's direction. Source: nightly report `hours=2160&orders=1` (gold and Dogecoin orders since Oct 7), and `functions/kalshiLiveLib.js` on `origin/main` (`reviewSizing`, `l1Count`, `scaleTarget`). I changed no code. OICORE scaling is not part of this review.

## What the code does today (so the question is clear)

- Order size = `min(cap, 50, floor(cash x 2% / cost per contract))` plus an add-on of at most a quarter of that. `cap` is the ladder: target = floor(balance / $43), it rises at most `SCALE_STEP` per 3 day review and falls to the target within 2 hours of staying below.
- The 2% rule is ALWAYS slightly tighter than the ladder target ($0.93 / 0.02 = $46.5 of cash per contract, against $43). So once the cap reaches the 2% size, the cap stops mattering. At $779 of cash the 2% size is 16 (target 18); at $1,000 it is 21 (target 23). **Raising the step pace cannot make an order bigger than the 2% rule allows. It only makes the cap get there sooner.**

## (1) How fast the size reaches its target, from the live record

What the orders show (base size = ordered contracts minus add-on): gold sat at 4 on Oct 20 to 22, jumped to 11 on Oct 23 (a Stop then Start goes straight to the target), stayed at 10 to 11 through Oct 31 with nothing ordered Oct 24, and became 12 on Nov 1. Dogecoin took gold's size on Oct 30 (11, then 12 on Nov 1).

Two readings, and I cannot tell them apart from the report:
- **A. The sizing base is the $779 main quoted.** Target 18, cap 12. Then the cap was behind and should have stepped on Oct 26, 29 and Nov 1 (to 14). It did not: it stayed at 11 for nine days. That does not fit A unless the review timer was reset (for example by the Oct 23 Start).
- **B. The sizing base is nearer $520 to $555** (target 11 to 12, the cap equal to the target the whole time). That fits the nine flat days and the single step on Nov 1.

Replay under each, from the cap of 12 on Nov 1:
| | +1 per review | +2 | +3 | 2% rule limit |
|---|---|---|---|---|
| A ($779, target 18, 2% size 16): reviews on Nov 4, 7, 10, 13 | 13, 14, 15, **16 on Nov 13** | 14, 16 on **Nov 7** | 15, 16 on **Nov 7** | 16 |
| B ($540, target 12, 2% size 11) | 12, no change | 12 | 12 | 11 |

So under A the larger step reaches the same ceiling (16) six days sooner (Nov 7 against Nov 13), and +2 gets there on the same day as +3. Under B it changes nothing today and only matters after a deposit or a large run of profit: each $43 of new balance adds 1 to the target. The record's profit rate is roughly $3 a day, so +1 per 3 days already tolerates about $14 a day of growth. A deposit is what a faster step would respond to: a $400 deposit adds 9 to the target, which takes 27 days at +1, 9 days at +3.

**What I need to settle A or B:** the values in `kalshiLiveControl/sizing` (cap, base, reviewedAt) and the balance by date. I cannot see them from here and did not guess.

## (2) What one loss costs at each size

Early sells at the 25c line cost, per contract, in the live record's 16 exits: median 74c, worst 88c (range 37c to 88c). A loss held to settlement at 97c costs about 98c with fee. The worst loss so far: -$9.58 (13 contracts, gold, 91.7c).

| Contracts | Typical early sell (74c) | Worst early sell (88c) | Settled loss at 97c | Cost of the order at 97c | Same window, two orders |
|---|---|---|---|---|---|
| 13 | $9.6 | $11.4 | $12.7 | $12.6 | $25.2 |
| 16 | $11.8 | $14.1 | $15.7 | $15.5 | $31.0 |
| 20 | $14.8 | $17.6 | $19.6 | $19.4 | $38.8 |
| 24 | $17.8 | $21.1 | $23.5 | $23.3 | $46.6 |

Against the limits (scenario A base $779 / scenario B base $540):
- **12% stop:** $93.5 / $64.8. Typical early sells needed to reach it: at 13 contracts 9.7 / 6.7; at 16, 7.9 / 5.5; at 20, 6.3 / 4.4; at 24, 5.3 / 3.6. Open orders count as lost, so a bad window plus a few settled losses gets there sooner than the table says.
- **5.5% window cap:** $42.8 / $29.7. Two orders in one window (gold and Dogecoin now share it): the second is cut once the pair costs more than the cap, which starts at about 22 contracts each under A, and at 15 each under B.
- **Reachability:** 20 and 24 contracts need a cash balance of about $930 and $1,100 or more (2% rule 20 and 24). At $779 the base cannot pass 16 (20 with a full add-on), whatever the step.

## (3) Does the record show loss rate or no-fill share changing with size?

Orders by ordered contracts (all history, gold; Dogecoin only 1 to 5 and 11 to 15 exist):
| | Orders | No-fill share (95% range) | Settled fills | Losses (rate, 95% range) |
|---|---|---|---|---|
| Gold 1 to 5 | 88 | 41% (31 to 51) | 52 | 3 (5.8%, 2 to 16) |
| Gold 6 to 10 | 145 | 28% (22 to 36) | 104 | 3 (2.9%, 1 to 8) |
| Gold 11 to 15 | 86 | 42% (32 to 52) | 50 | 4 (8.0%, 3 to 19) |
| Gold 16 and up | 16 | 44% (23 to 67) | 9 | 0 (0 to 30) |
| Dogecoin 1 to 5 | 199 | 29% (23 to 35) | 142 | 7 (4.9%, 2 to 10) |
| Dogecoin 11 to 15 | 53 | 36% (24 to 49) | 34 | 1 (2.9%, 0.5 to 15) |

Reading: gold's no-fill share is higher at 11 to 15 than at 6 to 10 (42% against 28%, two sided p 0.043) and its loss rate is higher too (8.0% against 2.9%, p 0.22), but the buckets come from different weeks, prices and balances, six comparisons were looked at, and the loss counts are 3 and 4 events. Dogecoin at ladder size shows no loss increase (1 of 34, p 1.0) and a no-fill share of 36% against 29% (p 0.32). **No size effect on loss rate can be proved or ruled out with 17 losses in the whole record, and nothing at all is known above 16 contracts** (9 settled fills, no losses, range 0 to 30%).

## (4) Recommendation

**Keep +1.** My reasons, in order:
1. At today's balance the step pace is not what limits size. Under reading A the cap catches the 2% size (16) in 12 days at +1; under B the cap is already at the target. The extra pace buys about six days of 3 or 4 more contracts under A, and nothing under B.
2. The record has nothing above 16 contracts to say a larger size is safe, and the only cut that moves (gold's no-fill share at 11 to 15) points the wrong way.
3. The cost of a mistake is lopsided: one more contract is about 74c to 98c of loss against about 3c to 6c of win, so each extra contract needs about 12 to 30 wins to pay for one loss.
4. A faster ladder matters mainly after a deposit, and the owner can already do that deliberately (a Stop then Start jumps straight to the target).

If the owner still wants a faster ladder: **+2, not +3.** Under A it reaches the same ceiling on the same day, and it halves the largest single-review jump (2 contracts is about 1.5 to 2 dollars of extra loss per order, 3 is about 2.2 to 3).

**Kill rule to register with any faster step (gold and Dogecoin pooled, scored on orders placed after the change):** go back to +1 if the last 100 settled orders at the larger size lose more than 8%, or net under +0.5c a contract, or any single US Central day is down more than 2% of the sizing base, or the no-fill share of the last 100 orders at the new size is above 45% (so size is outrunning the book). 100 settled orders is about 8 to 10 days at the current rate. Doge's existing review (250 settled, 8% / +0.5c at the last 100) stays as it is.

## Count for deflation
This review looked at 6 bucket comparisons and 2 scenarios: about 8 tries, N about 728,691. Nothing here is a finding about edge; it is arithmetic on the sizing rules plus a descriptive table.
