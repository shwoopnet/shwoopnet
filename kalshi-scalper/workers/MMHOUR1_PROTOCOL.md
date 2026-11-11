# MMHOUR1 (registered Nov 11, 2026, before any cell is scored): MMSIM1 split by hour of day, quoted spread and touch depth, development events only
Research only, simulation only, no live change, no network call except git on this repo. Card MMHOUR1 in `workers/IDEA_CARDS_NOV11B.md`. Base rule = MMSIM1 exactly (`workers/MMSIM1_PROTOCOL.md`, `src/scalper/mmsim1.py`; MMSIM2's BASE reproduces it): post one contract at the best bid of each side of each of the 7 recorded strikes at the first book poll from T-50 minutes, join the back of the queue, fill by cumulative taker contracts at the price reaching queue ahead + 1, cancels ignored, flatten at T-15 (a pair is held to settlement and pays 1; a single sells at the best bid with taker fee 0.07 p(1-p)), cash basis, unrounded fees.
DEVELOPMENT ONLY. Development = the 171 events (168 quotable) closing before the Nov 8 cutoff, the first 171 events by close time exactly as MMSIM2. The script drops every later event before simulating (reuse of `mmsim2.load`). NO event closing on or after the cutoff is read into a score. The parent reads the held-out events once, on or after 2026-11-17.

## Fixed splits (a strike-quote is assigned to ONE cell at posting time; nothing is tuned)
- Hour block = US Central hour of the posting time (first poll in the window), `America/Chicago`: 0 to 6, 6 to 12, 12 to 18, 18 to 24 (4 blocks).
- Spread at posting = 100 x (1 - yes_bid - no_bid) at the first poll: 1c, 2c, 3c or more (3 labels: "1c", "2c", "3c+"). Note up front: MMSIM2 found EVERY recorded book in the quoted window had a 1c spread, so the 2c and 3c+ cells are expected to be EMPTY. They stay in the registration and count in N; an empty cell is reported as empty, not dropped.
- Depth at the touch = yes_bid_sz_1 + no_bid_sz_1 at posting (the two sizes we would queue behind). Terciles by this depth over ALL development strike-quotes, cut points fixed at the 1/3 and 2/3 quantiles of that one set (low, mid, high). The cut points are computed once from posting-time book rows only, not from any P&L.
- Cell P&L per event = the sum of the P&L of the strike-quotes of that event that fall in the cell (one contract per side per strike). n events = events with at least one strike-quote in the cell.
- Fee bounds: maker 0 and 0.0175 x p(1-p); taker exit 0.07 p(1-p); cash basis, as MMSIM1.

## Tests counted
Full cross: 4 blocks x 3 spreads x 3 depth terciles x 2 fee bounds = 72. Pooled marginals (the plan below): 4 blocks + 3 spreads + 3 depth terciles = 10 cells x 2 bounds = 20. N added = 92 on top of the ledger (about 5,190 + 1 + 18 = 5,209 before; about 8,795 after the idea cards registered so far per the parent; bar z about 4.39 at N 8,795, about 5.34 at N 1.1M). Day-clustered z of a pooled cell is judged against the same bar. No cell is selected for a live version on development alone.

## Honest note on power
168 development events cannot reach the n >= 300 events bar in ANY cell, split or pooled (n <= 168 even with no split), and the 72 full-cross cells will average under 5 events each, with strike-quotes spread over about 10 UTC days. So every full-cross cell is NOT_ENOUGH_DATA by construction. Pooled-blocks plan: because the full cross is too thin, the reportable reads are the pooled marginals (blocks alone, spreads alone, depth terciles alone). A marginal cell with n >= 60 events and cash PF at 0.0175 above MMSIM1's 1.28 is "worth the held-out read", never a pass. Because the unsplit base is only 168 events with per-event sd about 42c, differences between cells are expected to be within noise; with 92 tests, the best cell is biased upward.

## Bar (per cell, at the 0.0175 bound)
Cash PF >= 1.5 on per-event P&L over >= 300 events, day-clustered z above the multiple-testing bar, and a positive mean in each third of the cell's events. Verdict words: FALSIFIED only if a registered pooled marginal with n >= 60 events has PF at 0.0175 below 1.0 AND no marginal beats base; NOT_YET_FALSIFIED if some marginal with n >= 60 beats 1.28 with positive thirds; otherwise NOT_ENOUGH_DATA.

## Prediction before running
No marginal separates from the base's 1.28 by more than noise; the spread split is degenerate (all 1c); hour blocks overnight (Central 0 to 6) may look better (wider queues, fewer informed takers) but it will be inside noise. Script `src/scalper/mmhour1.py`, run with `python3 -I`.

## Result (Nov 11, 2026, development events only; held-out NOT read)
Script `src/scalper/mmhour1.py` (python3 -I). 171 development events (168 quotable), cutoff 2026-11-07T15:00Z, 1,113 strike-quotes, 10 UTC days. Depth cut points (YES plus NO touch size): 1,962.6 and 4,426.6 (371 quotes per tercile). Correction to MMSIM2's note: 1,100 quotes had a 1c spread and 13 had 2c; none had 3c or more, so the 3c+ cells are empty and the 2c cells hold 1 to 3 events. Fills/day is cell fills over 10 days. Cash, unrounded, maker bound 0.0175 (the PF at bound 0 is higher by 0.1 to 0.4 in every row; full output in the script run). z is day-clustered. Bar for multiple tests: z about 4.39 (N 8,795).

| cell (0.0175) | n events | fills/day | cash PF | mean/event | day z | thirds (c) | pos thirds |
|---|---|---|---|---|---|---|---|
| ALL (= MMSIM1) | 168 | 79.1 | 1.28 | +3.71c | 1.60 | +9.6/-6.0/+7.6 | 2 |
| block 0-6 CT | 38 | 14.9 | 1.67 | +7.35c | 1.35 | +4.3/+3.2/+14.3 | 3 |
| block 6-12 CT | 34 | 15.8 | 0.56 | -8.76c | -1.36 | -11.1/-17.1/+1.0 | 1 |
| block 12-18 CT | 46 | 24.7 | 2.59 | +12.42c | 3.28 | +25.2/+1.1/+11.1 | 3 |
| block 18-24 CT | 50 | 23.7 | 1.10 | +1.43c | 0.25 | +7.8/-19.3/+16.1 | 2 |
| spread 1c | 168 | 77.9 | 1.34 | +4.27c | 1.78 | +10.8/-6.0/+8.0 | 2 |
| spread 2c | 12 | 1.2 | 0.04 | -7.74c | -1.34 | all negative | 0 |
| spread 3c+ | empty | | | | | | |
| depth low | 151 | 35.7 | 1.07 | +0.69c | 0.40 | +3.6/-2.0/+0.5 | 2 |
| depth mid | 152 | 25.8 | 1.10 | +0.89c | 0.43 | +4.0/-5.3/+4.0 | 2 |
| depth high | 142 | 17.6 | 2.11 | +2.71c | 2.02 | +1.5/-0.2/+6.7 | 2 |
| 12-18 CT, 1c, high depth | 43 | 7.3 | 6.78 | +7.53c | 3.20 | +5.6/+3.5/+13.1 | 3 |
| 0-6 CT, 1c, high depth | 35 | 3.2 | 5.36 | +2.83c | 2.45 | +3.5/+0.7/+4.3 | 3 |
| 12-18 CT, 1c, low depth | 38 | 8.9 | 1.50 | +4.16c | 0.87 | +12.9/-13.6/+13.9 | 2 |

The other full-cross cells (36 of 72 non-empty) are all n under 50 and mixed; 6-12 CT with 1c and high depth is PF 0.30 and with low depth 0.67.
Reading:
- No cell reaches n >= 300 events or the z 4.39 bar. All full-cross cells are NOT_ENOUGH_DATA (at most 46 events, at most 122 strike-quotes). The best z is 3.28 (block 12 to 18 CT) and 3.20 (the cell inside it), both under the bar and chosen as the best of 92 looks.
- Marginals with n >= 60 that beat MMSIM1's 1.28: depth high (n 142, PF 2.11, z 2.02, 2 of 3 thirds positive, 17.6 fills/day) and spread 1c (n 168, PF 1.34, essentially the base because 98.8% of quotes are 1c). The hour blocks have n 34 to 50, under 60.
- Pattern: the edge sits in 12 to 18 CT and 0 to 6 CT; 6 to 12 CT loses (PF 0.56). High touch depth (a long queue ahead, so fewer and later fills) is better than thin depth. Both are plausible but within noise for 168 events and 92 looks; the middle third of events is negative for most cells, as in MMSIM1 and MMSIM2.
- Verdict: NOT_ENOUGH_DATA. Not falsified (high depth and the 12 to 18 CT block stay positive), not a pass. Worth carrying to the parent's one held-out read on or after 2026-11-17: block 12 to 18 CT and depth high, as registered here before the held-out events are read. N added 92. No live change.
