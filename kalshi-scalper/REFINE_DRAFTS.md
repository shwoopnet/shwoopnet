# Refinement pre-registration DRAFTS, all six (2026-11-06)

Status: DRAFTS ONLY for main and the owner to approve. Nothing is scored, built, registered or live. Combined from two worker files (OICORE drafts first, gold drafts second); every figure is quoted from REFINE_STATUS.md except where a draft says counts were added (fill shares, feasibility). None changes an order, a size, a stop or the exit watch. Adopting any of them is a separate reviewed pull request.

====================================================================
# PART 1: OICORE (S-EDGEFILT, S-NEARTHR, S-NOFILLADV)
====================================================================

# W-REGS-OICORE: three pre-registration DRAFTS (nothing scored, nothing sent, nothing live)

Status: drafts for main and the owner to approve. No outcome was computed for any of them. Every number below is quoted from kalshi-scalper/REFINE_STATUS.md (entries Nov 5 to Nov 6, 2026); I did not recompute any of it. Read only worker; no trading code touched.

Common rules for all three
- [live figure removed, ask Main]
- Try count: REFINE_STATUS says about 385 splits in all (Bonferroni about 0.00013, no survivors) as of its line 678 entry. Each draft below adds the tries it names. Main should restate the current total from the file at registration time; I did not recount.
- [live figure removed, ask Main] A filter can therefore only be adopted on fills placed AFTER its cutoff.
- Every draft is a forward SHADOW COUNT on live fills plus candles. None changes an order. None may be wired into the bot; a promotion is a separate reviewed pull request by main and the owner.
- Cutoffs: each starts the moment main registers it (write the UTC timestamp into the file first). Orders before the cutoff never count.

---------------------------------------------------------------------------------------------

## DRAFT 1: [live figure removed, ask Main]

[live figure removed, ask Main] It has no action line. This draft names the one action it would justify and the bar for it, so that the read and the decision are fixed together before any forward fill. It uses the SAME fills and the same cutoff as S-EDGEFWD, so it adds no new data wait and no new split to the forward arm; the split is already counted there. It adds 1 try (the filter decision itself).

[live figure removed, ask Main] Same definition as w_oicore_edge/e.py and edgefwd_forward.py.

[live figure removed, ask Main] No new Kalshi call beyond what the tracker already makes.

[live figure removed, ask Main]

[live figure removed, ask Main]

[live figure removed, ask Main]

[live figure removed, ask Main] Otherwise nothing.

[live figure removed, ask Main]

[live figure removed, ask Main] It lifts profit factor mainly by removing a handful of small losses. [live figure removed, ask Main]

[live figure removed, ask Main]

---------------------------------------------------------------------------------------------

## DRAFT 2: [live figure removed, ask Main]

[live figure removed, ask Main] I will not scan 90k or 110k).

[live figure removed, ask Main] Rise = open interest at the candle ending 180 s before close minus the candle ending 360 s before close, recomputed from the public candle caches by ticker exactly as risefwd_forward.py does (reuse that code, same candle source).

Data read: report slotOrders (OICORE, filled, settled) plus the candle caches; no new endpoint.

[live figure removed, ask Main]

[live figure removed, ask Main] Proposed action if all hold: one brief to raise oiRiseMin to 100,000. Otherwise nothing. [live figure removed, ask Main]

[live figure removed, ask Main]

[live figure removed, ask Main] Main should weigh that before approving.

[live figure removed, ask Main]

---------------------------------------------------------------------------------------------

## DRAFT 3: S-NOFILLADV, forward measure of no-fill adverse selection (what OICORE's unfilled orders would have made), no filter

Why: it is the one lead with no forward record. [live figure removed, ask Main]

[live figure removed, ask Main] Compare with the filled OICORE orders in the same days: win rate and net per contract.

[live figure removed, ask Main] No private endpoint, no order.

[live figure removed, ask Main] Under 40: print counts, NO READ.

[live figure removed, ask Main]

[live figure removed, ask Main]

[live figure removed, ask Main] It cannot change any order, so even a positive result is a lead for a separate test, not a rule.

[live figure removed, ask Main]

---------------------------------------------------------------------------------------------

[live figure removed, ask Main]


====================================================================
# PART 2: [live figure removed, ask Main]
====================================================================

# W-REGS-GOLD: [live figure removed, ask Main]

Status: DRAFTS ONLY. Nothing here is scored, built, registered or live. Written from kalshi-scalper/REFINE_STATUS.md entries since Nov 5 (no new data read). Every shadow below reads forward fills only, never changes an order, a size, a stop or the exit watch.

SIZING IS THE OWNER'S DECISION. Draft B touches the idea of size. It is a shadow what-if on recorded fills; it never sends, caps or resizes an order. [live figure removed, ask Main] Adopting any of these is a separate reviewed pull request the owner asks for.

[live figure removed, ask Main]

Shared rules for all three:
- Cutoff: first gold fill whose order time is after the registration commit time (hard coded in the script, as goldfwd did). Nothing before it counts, including the fills that suggested the idea.
- [live figure removed, ask Main]
- Unit: cents per contract (settledPnl over count) and loss rate. [live figure removed, ask Main]
- Interim reads are information only. The only flag is the one written below, printed by wake.sh, sent to main, never acted on by the shadow.
- [live figure removed, ask Main] A forward read inside this stretch is a read of the stretch.

---------------------------------------------------------------------------
## Draft A: [live figure removed, ask Main]

[live figure removed, ask Main] [live figure removed, ask Main]

[live figure removed, ask Main] A price is the order price field (limit) until avgFill is in the report.

Data it reads: forward gold orders, price, count, settledPnl, exit flag.

[live figure removed, ask Main]

[live figure removed, ask Main]

[live figure removed, ask Main] Then the idea is closed.

[live figure removed, ask Main]

Tries already spent: the 0.92 cut was chosen after seeing W-GOLDBAND1's four buckets. [live figure removed, ask Main]

[live figure removed, ask Main] Only fills priced after the cutoff, taken at the real counts, can say what the cheap bucket does now.

---------------------------------------------------------------------------
## Draft B: [live figure removed, ask Main]

[live figure removed, ask Main] [live figure removed, ask Main] The question this draft isolates: is the extra size on cheap fills paying for its risk.

[live figure removed, ask Main] The shadow is NOT a proposal to change `l1Count`, `L1_ORDER_CEILING` or the ladder.

[live figure removed, ask Main]

[live figure removed, ask Main] [live figure removed, ask Main]

[live figure removed, ask Main] (b) the dollars of gain given up on winning days; (c) a loss-to-gain ratio. [live figure removed, ask Main] Fail: either side. Since dollars scale linearly with count, (a) and (b) will always move in proportion; the shadow's only information is whether the cheap fills' cents per contract is lower than the rest. So the verdict must be written as a cents per contract comparison (cheap bucket vs rest) with the dollar what-if shown beside it, and the owner decides the size.

[live figure removed, ask Main]

Tries already spent: 1 cap value (8) and 1 price cut (0.92). [live figure removed, ask Main]

[live figure removed, ask Main] SIZING IS THE OWNER'S DECISION: this prints a what-if and stops.

---------------------------------------------------------------------------
## Draft C: [live figure removed, ask Main]

[live figure removed, ask Main]

The exact rule (shadow only): for each forward gold order that the live exit watch sells (exit flag true, result exit), find the sale time T. [live figure removed, ask Main] [live figure removed, ask Main] No entry, size or other rule changes.

Data it reads: forward gold orders with an exit, exit time, market result. The close time comes from the ticker's Eastern time (`kalshiCloseFromTicker`).

[live figure removed, ask Main] Candle coverage of the exit sample and the share inside 120 seconds: [live figure removed, ask Main] [live figure removed, ask Main] Read once at 15, nothing between.

[live figure removed, ask Main] [live figure removed, ask Main]

[live figure removed, ask Main] Then the idea is closed.

[live figure removed, ask Main]

[live figure removed, ask Main] The exit watch is the safety feature (it only ever reduces exposure); a change to it is the owner's and a separate reviewed pull request; this draft changes nothing in it.

--------------------------------------------------------------------------- Next, if the owner approves: write each as a `README.md#S-...` entry with the cutoff, a read only script on the model of `goldfwd_forward.py` with a synthetic test, and one wake.sh section. Nothing in `functions/` or `index.html` is touched by any of them.

## Open discrepancy on S-GHOLD120 (Nov 6 2026)
The two workers' feasibility counts disagreed ([live figure removed, ask Main]); they use different readings of the same proxy. Treat the feasibility as unsettled and the idea as slow either way; nothing is started.

## Update on S-GHOLD120 feasibility (Nov 6 2026, later)
[live figure removed, ask Main]
