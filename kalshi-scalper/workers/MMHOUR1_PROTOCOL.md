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
