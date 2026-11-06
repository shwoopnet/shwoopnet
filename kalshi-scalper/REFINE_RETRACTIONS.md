# W-RETRACT1: claims in REFINE_STATUS.md corrected, withdrawn or tempered by a later entry (Nov 5 to Nov 6, 2026)

Source: /home/user/shwoopnet/kalshi-scalper/REFINE_STATUS.md (read only). Times CT. Format: original entry (date) -> correcting entry -> truth now.

## Corrected or withdrawn

1. Original: W-GQH-COST1 "about $25 not earned, 0 losses avoided", W-GQH-NEXT1 "block 26 of 26 won, review not readable yet", W-GQH-PROG1 projection (Nov 6 10:40 to 10:52).
   Chain: OPEN CONFLICT (W-GQH-PROG1) (Nov 6 11:06) -> CORRECTION W-GQH-LIVE1 "went live on the Nov 6 16:33Z deploy, not Oct 29" (11:07) -> CORRECTION OF THE CORRECTION (11:07) -> W-DEPLOYTIME1 (11:08).
   Truth now: gold's quiet hours block is NOT live; QUIET_HOURS_CT is empty (lifted by the owner Oct 30, #669). W-GQH-LIVE1, the "$25 not earned", the Nov 26 100-entry review and the projections are all withdrawn. Plain history that stands: candle block 26 of 26 wins; live fills at those hours Nov 1 to 5, 16 settled, 2 losses, -$10.13 (live and candle method disagree).

2. Original: W-GOLDEXIT180-PESS1 "close-180 rule with a pessimistic sale" (Nov 6 11:01; its "survives pessimism" reading).
   Corrected by: CORRECTION W-GOLDEXIT180-AUDIT1 (Nov 6 11:01).
   Truth now: pess() was never applied to the close-180 rule (a bug), so the run was identical to the ideal one. With realistic slippage the rule's edge over hold (1.19c) is gone at about 0.05 slippage (1.25c at -0.03, 0.89c at -0.07).

3. Original: W-GOLDEXIT180-1 (Nov 6 10:49, selling gold at close-180 beats hold by 0.33c).
   Tempered by: W-GOLDEXIT180-AUDIT1 (and W-GOLDEXIT-DEPTH1 Nov 6 10:59, exits sold a median 7c below trigger).
   Truth now: the 0.33c edge assumes a sale at the c-180 bid; it does not survive realistic fills. Not adoptable.

4. Original: W-GOLDEXIT1 "gold's live 25c exits against holding" (Nov 6 10:41), and the ideal 25c exit figure in history (+0.15c over hold).
   Tempered by: W-GOLDEXIT-REAL1 (Nov 6 11:00), W-GOLDEXIT-DEPTH1 (10:59).
   Truth now: with a pessimistic exit price the 25c exit is a wash to about 0.06c below hold; 15 of 16 live exits sold below 25c (median about 0.18), 11% extra loss ($15.63 of $140.05).

5. Original: W-LIVEBUCKET1 (Nov 6 10:21; B5 and floor rows, "longest 12", "10 B5 forward fills all losses").
   Corrected by: W-AUDIT1 (Nov 6 10:24).
   Truth now: that table used the mixed slot stream (OICORE 47 + EVENT830 5 + FLOW1 1). OICORE alone: 47 fills, 10 wins, +41.79, PF 2.17, longest loss streak 11 (not 12), B5 30 fills +2.81c PF 1.43, B10 15 fills +15.49c. Tracker figures stand.

6. Original: W-OICORE-HIST1 "OICORE sim by price bucket beside live: live sits cheaper than the sim" (Nov 6 10:45).
   Corrected by: W-OICORE-SKEW1 (Nov 6 10:46).
   Truth now: the sim price split depends on which candle is used (29/45/27% at c-180, 53/16/31% at c-120 vs live 51/30/19%), so the skew is not established.

7. Original: earlier descriptions of S-SDIR1 as a YES versus NO split (before Nov 5 10:45).
   Corrected by: W-SDIREXP1 (Nov 5 10:45).
   Truth now: S-SDIR1 is the bought side's YES mid change from close-360 to close-180 (sign flipped for NO), kept when sdir is at least -0.09; not a YES vs NO split.

8. Original: the earlier d.order.status guess for where the create-order response puts status (and the line sent to main), before W-POSTSTATUS1 (Nov 5).
   Corrected by: W-POSTSTATUS1 (Nov 5 10:42).
   Truth now: the POST response is flat with no status field, so kalshiStatus can never be written from it; the no-fill reason would need an inference or a follow-up GET (trading code, for main to decide).

9. Original: the reconcile table in the OICORE no-order work (before W-NOORDER1, Nov 5).
   Corrected by: W-NOORDER1 (Nov 5 10:25).
   Truth now: 9 trigger-with-no-fill windows, not 8; 8 no-order windows with no pattern, reasons not stored.

10. Original: W-FILLGOLD1 and W-FILLPRICE1 "bound, not a measurement" (Nov 6 10:30) and the understatement bounds (OICORE 0 to 4.36, gold 0 to 9.83), plus the claim that settledPnl books cost at the limit (W-DAYLOSS2 side finding, freshness entry 10:26).
   Tempered by: W-AVGFILL1 (Nov 6 10:31) and W-COSTGAP1 (10:56).
   Truth now: avgFill is null only because of a report field-name mismatch (the real fill is stored); the bounds can be settled exactly from a Copy all orders export or the fixed report (#729, merged, not yet deployed). Measured cost gap: gold 0.33c, OICORE 0.62c per contract (a third to a half of gold's history margin).

11. Original: W-DAYLOSS1 (Nov 6 10:11, shadow report's daily-loss gain) and the report that disagreed.
   Clarified by: W-DAYLOSS1 follow up (Nov 6 10:12).
   Truth now: the disagreement was scope (the shadow report applies rules to all settled markets together, mostly cutting Dogecoin and Bitcoin loss days); the gold-only replay (FALSIFIED) stands.

12. Original: W-EVENT830-REG1 / EVENT830 history figures (PF 2.47 on 21 trades, 1.71 on 28) as support (before Nov 5 10:38).
   Tempered by: W-EV830AUDIT1 (Nov 5 10:38).
   Truth now: the slice was picked after EVENT1's pooled verdict was FALSIFIED; same windows chose and scored it, try count understated. Not evidence, cannot count toward adoption. Later: W-EVENT830-PACE1 says the Dec 7 40-fill read is not reachable.

13. Original: the worker notes that only OICORE and gold were live (my own notes, before W-REGISTRY1, Nov 5 10:29).
   Corrected by: W-REGISTRY1 (Nov 5 10:29) and W-DOCS1 (Nov 5 10:35).
   Truth now: EVENT830 is a second live slot strategy (added #704); FLOW1 was added and removed. CLAUDE.md and README lines about the registry being exactly OICORE with 5 contracts are stale (six stale doc lines).

14. Original: W-OICORE-MATCH1 / W-MISSING1 explanation of live vs sim trigger gaps as "rounding and timing" (Nov 5 to Nov 6 10:38).
   Tempered by: W-OICORE-NOFILL1 (10:48), W-OICORE-0812 (Nov 6 11:04), W-OICORE-SKIP1 (11:05).
   Truth now: some sim triggers have no order and no no-fill record (9 of 15 in 08-12 CT); look time does not explain them; skip reasons are not logged (PR 726 merged, not live).

15. Original: C9 "-2.71c" read as a possible kill (before W-C9RESTATE1, Nov 6 10:26).
   Tempered by: W-C9RESTATE1.
   Truth now: -2.71c over 97 windows has a bootstrap interval of -8.95 to +2.53 (spans 0); not a kill, read stays at 200 windows.

## Still marked provisional, open or not settled (as of Nov 6 11:09)

- Gold quiet hours block: whether it has any effect (block is lifted; the live 20-24 CT fills do worse than the candle method said). Open, no review date.
- W-GOLDVOLUME1: value of gold's 35 missed windows, "sign not settled" (-$6 to +$6).
- W-OICORE-NOFILL2 / W-OICORE-ADVERSE1: unfilled OICORE orders winning more, "suggestive, not significant".
- W-OICORE-SLIP1: the slip result flips with the pricing assumption.
- W-OICORE-SKIP1 and W-OICORE-0812: cause of skipped sim triggers unidentifiable until skip reasons are logged (deploy of PR 726 needed).
- W-GOLDEXIT-RATE1 and W-GOLDSIZE1/2: descriptive, "size sensitivity, arithmetic not a forecast".
- W-COSTGAP1 and W-FILLGOLD1: gap sizes are bounds until avgFill is populated (#729 merged, not deployed; re-run once avgFill and avgFee appear).
- W-OICORE-STREAK1 / NOV13PREP1: the 18-loss streak kill is a live risk (14.5% by Nov 13, 44% by Nov 30); decision aid only.
- W-EVENT830-NEXT1 / PACE1 / NOFILL1: 5 fills, 0 wins; Dec 7 read not reachable; reachability does not separate no-fills.
- W-C2DOGE1: C2 projected 40th fill about Nov 26, noisy.
- S-LIM1-LIVE and W-INVENTORY1: retire proposals for trackers (S-FLOW1, S-FLOW2, S-FLOWL1, C8) still proposals.
- Freshness check (Nov 6 10:26): four stale doc lines remain, EVENT830 scale understated.

Count: 15 claims corrected, withdrawn or tempered; 11 items still provisional or open.
