# FILLHAIRCUT1 result: the simulation-to-real-fill haircut for taker rules, Bitcoin 15 minute market (2026-11-12)

Registration: `FILLHAIRCUT1_REGISTRATION.md` (commit f818520, before anything was computed). Script `fillhaircut1.py`, raw output `results/FILLHAIRCUT1.json`. A measurement: no rule scored, no settlement result loaded, zero tries. Public R6 books and tape only, zero Kalshi requests, no live account figure.

**Sample.** `KXBTC15M`, closes 2026-10-29 to 2026-11-08, the span 180 to 120 seconds before the close, cheaper side with its ask from 5c to 30c. 735 windows used of 737 listed; 430 windows had at least one decision instant; **7,587 decision instants** (2 second polls); **502,143 taker trades** that bought the cheaper side. Every bucket has 250 or more windows, so no cell is under the "no evidence" line. Intervals are 95%, from resampling whole windows.

## The haircut, stated first

1. **1 contract and 10 contracts are the same.** The size shown at the ask is 10 or more at 97% of instants (median about 1,500), and the fill shares for 1 and 10 differ by 0.2 points. Size carries no haircut up to 10; this says nothing about hundreds.
2. **Drop fills, do not add cents.** An immediate-or-cancel order with a limit loses the signals whose price ran up and keeps the rest at an average price slightly BELOW the ask seen at the decision.

| Limit | Arrives about 2 s later | about 6 s later | about 10 s later |
|---|---|---|---|
| At the ask seen (a0): share filled | 67% (66 to 69) | 66% (65 to 68) | 67% (64 to 69) |
| At a0: paid against a0, on the filled | -1.2c | -2.4c | -3.6c |
| At a0 + 1c: share filled | **85% (84 to 86)** | 77% (75 to 79) | 74% (72 to 76) |
| At a0 + 1c: paid against a0, on the filled | -0.8c | -2.0c | -3.1c |

3. **The cost is which signals are lost.** For a +1c limit arriving 2 seconds later, the mid of the MISSED orders is 5.4c higher 30 seconds after the decision (3.7c to 7.4c) and the mid of the FILLED ones is 1.0c lower (-1.8c to -0.1c). A limit keeps the signals the market moved against and loses the ones it moved with.
4. **For a decision instant that does not predict the next seconds, a simulation at the seen ask is not biased in price.** The ask moves by -0.06c on average over 2 seconds (-0.13c to +0.01c) and -0.16c over 10 seconds (-0.54c to +0.23c). It is the spread of that move that matters: 75th, 90th and 95th percentile +0.7c, +2.0c, +4.0c at 2 seconds; +1c, +5c, +8c at 6 seconds; +1.4c, +7c, +12.6c at 10 seconds.
5. **So the simulation convention I recommend for a taker rule on this market:**
   - Replay the rule's own decision instants on the books: price each at the first quote at least 2 seconds later, with the limit the probe would really send, and count a miss as NO TRADE. This is the only way to capture a signal that predicts the next seconds (a spot-led or model-edge rule such as CFRTI1-BTC is exactly that kind: its edge is the quote being behind, so its misses are likely to be its best signals).
   - Where only the quote at the decision exists: keep the price at a0, and drop 15% of fills for a +1c limit (33% for a limit at a0) at about 2 seconds, 23% at about 6 seconds. State beside it that the dropped ones are NOT random: as a stress, drop the fills from the signals with the best later outcome first and report both figures.
   - A limit of a0 + 2c fills about 90% at 2 seconds and a0 + 4c about 95% (from the percentiles above; these two were read off the move distribution, not simulated order by order).
6. **What the data cannot answer.** Nothing under about 2 seconds from the books (polls are 2 seconds apart, so the "1 second" row is the next poll, median 2.0 s). The tape (Part 2) is the only sub-poll evidence and agrees. Our own order's effect, and whether the missed signals WIN more, are not measured here (no settlement result was loaded; ENTRYREPLAY1's one read of that on the baseline was not stable).

## Part 1: is the ask still there

Share of instants whose ask is still at or below the ask seen (a0), and at or below a0 + 1c, at the first poll at least h seconds later.

| Bucket (instants / windows) | Still at a0: 2 s | 6 s | 10 s | Within +1c: 2 s | 6 s | 10 s |
|---|---|---|---|---|---|---|
| 5c to 10c (2,806 / 274) | 65.5% | 67.5% | 69.0% | 89.4% | 82.0% | 78.7% |
| 10c to 20c (2,661 / 276) | 71.5% | 69.0% | 68.9% | 86.1% | 77.8% | 75.0% |
| 20c to 30c (2,395 / 252) | 66.3% | 62.6% | 62.1% | 79.1% | 70.9% | 67.8% |
| All (7,587 / 430) | 67.7% | 66.5% | 66.9% | 85.2% | 77.3% | 74.2% |

When the ask at a0 is gone, how far it has moved (mean; 50th, 75th, 90th, 95th percentile):

| Bucket | 2 s | 6 s | 10 s |
|---|---|---|---|
| 5c to 10c | +1.3c (0.5, 1.3, 3.0, 4.9) | +3.2c (1.3, 3.3, 7.4, 11.9) | +4.6c (2.0, 5.1, 10.6, 17.1) |
| 10c to 20c | +2.5c (1, 3, 5, 8) | +4.9c (3, 6, 11, 15) | +7.5c (5, 10, 17, 23) |
| 20c to 30c | +3.3c (2, 4, 7, 10) | +5.7c (3, 7, 13, 18) | +8.2c (5, 12, 20, 24) |
| All | +2.3c (1, 3, 5, 8) | +4.5c (2.1, 5.9, 11, 15) | +6.8c (4, 8.7, 17, 23) |

Size: where the ask is still there, it is there in size (share with 10 or more contracts at or below a0 is within half a point of the share still there, in every cell). Size shown at the touch at the decision: median 823 (5c to 10c), 2,539 (10c to 20c), 1,729 (20c to 30c); 10th percentile 30, 299, 128. Spread: 0.1c under 10c (the book ticks in tenths of a cent there), 1.0c above.

## Part 2: what takers actually paid, and how much of the displayed size trades

Taker buys of the cheaper side against the ask of the last poll at least 2 seconds earlier (so 2 to 4 seconds old).

| Bucket (trades) | Mean per trade | Mean per contract | 50th / 75th / 90th / 95th | Paid above | Paid below | More than 1c above |
|---|---|---|---|---|---|---|
| 5c to 10c (185,760) | +0.19c (-0.15, +0.67) | +0.50c (+0.03, +1.14) | -0.3 / +0.3 / +1.7 / +3.9 | 32.8% | 62.9% | 14.5% |
| 10c to 20c (171,484) | -0.22c (-0.52, +0.15) | +0.20c (-0.31, +0.86) | -1 / +1 / +4 / +7 | 28.7% | 54.8% | 18.7% |
| 20c to 30c (162,541) | -0.28c (-0.68, +0.09) | +0.15c (-0.41, +0.75) | -1 / +2 / +5 / +8 | 35.2% | 51.6% | 25.8% |
| All (502,143) | -0.07c (-0.29, +0.19) | +0.34c (+0.01, +0.72) | -0.5 / +1 / +3.4 / +7 | 32.4% | 56.6% | 19.4% |

By trade size, all buckets, mean per trade: under 2 contracts +0.08c (-0.14, +0.33); 2 to under 20, -0.15c (-0.36, +0.07); 20 or more, -0.10c (-0.35, +0.19). No size effect.

Reading: against a quote 2 to 4 seconds old, real takers paid about the same on average, more often less than more, with a tail: one trade in five paid more than 1c above it and one in twenty about 7c or more above.

Share of the displayed size that trades. Contracts takers bought on the cheaper side at or below a0 after the poll, divided by the size shown at or below a0 at the poll (all buckets):

| Within | Instants with any such trade | Median ratio | Instants where it reaches the whole displayed size |
|---|---|---|---|
| 1 s | 95.8% | 0.52 | 33.7% |
| 2 s | 97.0% | 1.01 | 50.6% |
| 5 s | 98.2% | 2.64 | 74.4% |
| 10 s | 98.8% | 5.59 | 86.2% |

Reading: the displayed ask turns over completely about every 2 seconds and is refilled (two thirds of the time at the same price or better). The size shown at one instant is not a pool an order competes for; it is a flow. That is why a 10 contract order sees no size haircut, and also why "the ask I saw" is a weak description of what an order arriving seconds later meets.

## Part 3: immediate-or-cancel fills by bucket (limit a0 + 1c)

| Bucket | Filled in full, 2 s | 6 s | 10 s | Paid against a0 on the filled, 2 s | 6 s | 10 s |
|---|---|---|---|---|---|---|
| 5c to 10c | 89.3% (87.9 to 90.7) | 81.9% | 78.6% | -0.4c | -1.1c | -1.7c |
| 10c to 20c | 86.1% (84.7 to 87.5) | 77.6% | 75.0% | -0.9c | -2.2c | -3.3c |
| 20c to 30c | 79.0% (76.8 to 81.2) | 70.8% | 67.7% | -1.3c | -3.1c | -5.0c |
| All | 85.1% (84.0 to 86.3) | 77.2% | 74.1% | -0.8c | -2.0c | -3.1c |

With the limit at a0 itself: 65.1%, 71.5%, 66.3% filled at 2 seconds for the three buckets (all: 67.5%). Figures for 10 contracts are the same to within 0.3 points in every cell.

Mid 30 seconds after the decision, filled against missed (limit a0 + 1c, 2 seconds): 5c to 10c, -0.3c against +6.6c; 10c to 20c, -0.7c against +4.6c; 20c to 30c, -2.0c against +5.3c; all, -1.0c against +5.4c.

## Notes for the CFRTI1-BTC read and for probe specs

- CFRTI1's look is 120 seconds before the close; this span is 180 to 120 seconds. The 20c to 30c bucket, the closest to the close in behaviour, has the lowest fill share and the largest moves; expect the 120 second look to be at least that jumpy.
- CFRTI1 buys when a spot-built model is above the quote. If the quote is simply behind spot, it will move in the seconds after the signal, and the misses will be the model's best rows. The unconditional 15% here is therefore a floor for that rule, not an estimate. The honest figure needs CFRTI1's own signal rows (time, ticker, side, ask seen) replayed on the books at +2 seconds; that reads no outcome and I can run it on the development rows if they are passed.
- Disclosure: this desk's ENTRYREPLAY1 read the settlement outcome of the cheap-side Bitcoin BASELINE (no model, 178 seconds, 8c to 50c) for closes Nov 5 to 8, which overlaps the first days of CFRTI1's held-out period. CFRTI1's rule is frozen and none of its rows were formed or scored here, but whoever reads its held-out result should know the baseline figure for those days is already public in `FORENSICS_RESULT_NOV12.md`.
- Ten days, one regime, recorder gaps (735 of about 967 possible windows). Bitcoin only: the other four 15 minute series are far thinner and would need their own run (the data is held).

## Amendment 1 result (2026-11-12): the full grid, with a +2c limit and closes to Nov 11

Registered first (commit 1786f56). Period A = closes Oct 29 to Nov 8 (the tables above; raw `results/FILLHAIRCUT1_A.json`, and the first cut kept as `results/FILLHAIRCUT1_first_cut.json`). Period B = closes Nov 9 to 11 (`_B.json`: 217 windows used, 114 with instants, 1,940 instants, 141,006 taker trades). Both = `_AB.json` (952 windows used, 544 with instants, 9,527 instants, 643,149 taker trades). No settlement result loaded for any close.

**How to read the delay columns.** Polls are 2 seconds apart. "1 s" is the next poll (median 2.0 s). "2 s" is the first poll at least 2.0 s later, a mix of 2 and 4 seconds (median 2.07 s). "5 s" is median 6.0 s and "10 s" is median 10.06 s. The bot's orders leave several seconds after the minute, so the 5 and 10 second columns are where a live order lives.

**Share of immediate-or-cancel buys filled in full, both periods (the MISS rate is 100 minus this).** 1 contract; the 10 contract figure is the same to within 0.3 points in every cell.

| Bucket (instants / windows) | Limit | 1 s | 2 s | 5 s | 10 s |
|---|---|---|---|---|---|
| All (9,527 / 544) | ask seen | 67.1% (66.0 to 68.3) | 66.4% | 65.5% (63.8 to 67.0) | 65.8% (63.7 to 67.8) |
| | +1c | 84.2% (83.2 to 85.2) | 81.7% | **75.9% (74.3 to 77.5)** | **72.8% (70.8 to 74.9)** |
| | +2c | 90.5% (89.6 to 91.3) | 88.0% | **81.8% (80.3 to 83.2)** | **77.5% (75.8 to 79.4)** |
| 5c to 10c (3,565 / 353) | ask seen | 64.8% | 65.6% | 66.0% | 67.4% |
| | +1c | 88.4% | 86.5% | 80.2% | 76.8% |
| | +2c | 94.2% | 92.5% | 86.5% | 82.9% |
| 10c to 20c (3,372 / 356) | ask seen | 70.8% | 69.3% | 68.1% | 68.0% |
| | +1c | 84.8% | 81.7% | 76.6% | 73.8% |
| | +2c | 90.7% | 88.0% | 82.0% | 77.5% |
| 20c to 30c (2,941 / 317) | ask seen | 66.1% | 64.1% | 61.7% | 61.2% |
| | +1c | 78.5% | 75.7% | 69.6% | 66.6% |
| | +2c | 85.5% | 82.5% | 75.8% | 70.7% |

**Price paid against the ask seen, on the filled contracts, both periods (negative = cheaper than the ask seen).**

| Bucket | Limit | 1 s | 2 s | 5 s | 10 s |
|---|---|---|---|---|---|
| All | ask seen | -1.2c | -1.6c | -2.5c | -3.7c |
| | +1c | -0.8c | -1.1c | -2.1c | -3.2c |
| | +2c | -0.7c | -0.9c | -1.8c | -2.9c |
| 5c to 10c | +1c / +2c | -0.4c / -0.3c | -0.6c / -0.5c | -1.1c / -1.0c | -1.8c / -1.5c |
| 10c to 20c | +1c / +2c | -0.9c / -0.7c | -1.3c / -1.0c | -2.3c / -2.0c | -3.5c / -3.2c |
| 20c to 30c | +1c / +2c | -1.3c / -1.1c | -1.8c / -1.5c | -3.3c / -2.8c | -5.1c / -4.7c |

**Which signals a limit loses** (mid 30 seconds after the decision, both periods, 10 contracts): +1c limit at 5 s, filled -2.1c, missed +7.9c (6.4 to 9.6); at 10 s, filled -3.3c, missed +10.0c (8.4 to 11.6). +2c limit at 5 s, filled -1.8c, missed +9.6c (7.8 to 11.3); at 10 s, filled -2.9c, missed +11.4c (9.7 to 13.1).

**The two periods beside each other (all buckets, share filled in full, 1 contract).**

| Limit | Period | 1 s | 2 s | 5 s | 10 s |
|---|---|---|---|---|---|
| ask seen | A (Oct 29 to Nov 8) | 67.5% | 66.9% | 66.4% | 66.8% |
| | B (Nov 9 to 11) | 65.8% | 64.7% | 61.6% | 61.8% |
| +1c | A | 85.1% | 82.7% | 77.2% | 74.1% |
| | B | 80.8% | 78.1% | 70.9% (67.5 to 74.2) | 67.7% (63.7 to 71.8) |
| +2c | A | 91.2% | 89.0% | 83.2% | 78.8% |
| | B | 87.6% | 84.0% | 76.4% (73.4 to 79.5) | 72.5% (68.7 to 76.3) |

Period B filled 4 to 7 points less at every limit and delay, so the miss rate is not a constant: it moves with how fast the market is. Period B's buckets have 65 to 80 windows each, under the 100 line: by bucket, B alone is "no evidence at n = 65 to 80 windows"; pooled over buckets (114 windows) it is usable.

**The haircut to carry, restated for a live-like delay of 5 to 10 seconds.**

| Limit | Drop this share of simulated fills | Price on the rest |
|---|---|---|
| ask seen | about 34% (period B: 38%) | keep the ask seen (the fills are cheaper on average, by 2.5c to 3.7c) |
| +1c | 24% to 27% (period B: 29% to 32%) | keep the ask seen |
| +2c | 18% to 23% (period B: 24% to 28%) | keep the ask seen |

- 1 and 10 contracts: the same row.
- The dropped ones are the signals the market moved WITH: the mid of a missed order is 8c to 11c higher half a minute later, the mid of a filled one 2c to 3c lower. Dropping fills at random understates the cost for any rule whose signal predicts the next seconds. For such a rule the replay on its own instants is the only honest figure.
- The first cut's "+2c fills about 90% at 2 seconds" (read off the move distribution) is confirmed by the order-by-order figure, 90.5% at the next poll and 88.0% at 2 to 4 seconds. Its "+4c fills about 95%" was not simulated and stays an estimate.
- A wider limit buys back less than it seems at live delays: going from +1c to +2c recovers about 5 to 6 points of fills at 5 to 10 seconds, and the ones still missed have moved the most.
