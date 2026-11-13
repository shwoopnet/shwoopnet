HISTORY (Nov 13, 2026, owner ruling): this note predates the privacy scrub; lines marked "[live figure removed, ask Main]" are blank on purpose. Read it as history, not as a current rule.

# W-RETRACT1: claims in REFINE_STATUS.md corrected, withdrawn or tempered by a later entry (Nov 5 to Nov 6, 2026)

Source: /home/user/shwoopnet/kalshi-scalper/REFINE_STATUS.md (read only). Times CT. Format: original entry (date) -> correcting entry -> truth now.

## Corrected or withdrawn

1. [live figure removed, ask Main]
   [live figure removed, ask Main] Truth now: gold's quiet hours block is NOT live; QUIET_HOURS_CT is empty (lifted by the owner Oct 30, #669). W-GQH-LIVE1, the "$25 not earned", the Nov 26 100-entry review and the projections are all withdrawn. [live figure removed, ask Main]

2. Original: W-GOLDEXIT180-PESS1 "close-180 rule with a pessimistic sale" (Nov 6 11:01; its "survives pessimism" reading).
   Corrected by: CORRECTION W-GOLDEXIT180-AUDIT1 (Nov 6 11:01). Truth now: pess() was never applied to the close-180 rule (a bug), so the run was identical to the ideal one. With realistic slippage the rule's edge over hold (1.19c) is gone at about 0.05 slippage (1.25c at -0.03, 0.89c at -0.07).

3. [live figure removed, ask Main]
   [live figure removed, ask Main] [live figure removed, ask Main] Not adoptable.

4. [live figure removed, ask Main]
   Tempered by: W-GOLDEXIT-REAL1 (Nov 6 11:00), W-GOLDEXIT-DEPTH1 (10:59). [live figure removed, ask Main] [live figure removed, ask Main]

5. Original: W-LIVEBUCKET1 (Nov 6 10:21; [live figure removed, ask Main]
   Corrected by: W-AUDIT1 (Nov 6 10:24). [live figure removed, ask Main] Tracker figures stand.

6. [live figure removed, ask Main]
   [live figure removed, ask Main]

7. Original: earlier descriptions of S-SDIR1 as a YES versus NO split (before Nov 5 10:45).
   Corrected by: W-SDIREXP1 (Nov 5 10:45). Truth now: S-SDIR1 is the bought side's YES mid change from close-360 to close-180 (sign flipped for NO), kept when sdir is at least -0.09; not a YES vs NO split.

8. [live figure removed, ask Main]
   Corrected by: W-POSTSTATUS1 (Nov 5 10:42). Truth now: the POST response is flat with no status field, so kalshiStatus can never be written from it; the no-fill reason would need an inference or a follow-up GET (trading code, for main to decide).

9. [live figure removed, ask Main]
   Corrected by: W-NOORDER1 (Nov 5 10:25). [live figure removed, ask Main]

10. [live figure removed, ask Main]
   Tempered by: W-AVGFILL1 (Nov 6 10:31) and W-COSTGAP1 (10:56). [live figure removed, ask Main]

11. [live figure removed, ask Main]
   Clarified by: W-DAYLOSS1 follow up (Nov 6 10:12). Truth now: the disagreement was scope (the shadow report applies rules to all settled markets together, mostly cutting Dogecoin and Bitcoin loss days); the gold-only replay (FALSIFIED) stands.

12. [live figure removed, ask Main]
   Tempered by: W-EV830AUDIT1 (Nov 5 10:38). Truth now: the slice was picked after EVENT1's pooled verdict was FALSIFIED; same windows chose and scored it, try count understated. Not evidence, cannot count toward adoption. [live figure removed, ask Main]

13. [live figure removed, ask Main]
   Corrected by: W-REGISTRY1 (Nov 5 10:29) and W-DOCS1 (Nov 5 10:35). [live figure removed, ask Main]

14. [live figure removed, ask Main]
   [live figure removed, ask Main]

15. [live figure removed, ask Main]
   Tempered by: W-C9RESTATE1. Truth now: [live figure removed, ask Main] Not a kill, read stays at 200 windows.

## Still marked provisional, open or not settled (as of Nov 6 11:09)

- [live figure removed, ask Main] Open, no review date.
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- W-GOLDEXIT-RATE1 and W-GOLDSIZE1/2: descriptive, "size sensitivity, arithmetic not a forecast".
- W-COSTGAP1 and W-FILLGOLD1: gap sizes are bounds until avgFill is populated (#729 merged, not deployed; re-run once avgFill and avgFee appear).
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main]

Count: 15 claims corrected, withdrawn or tempered; 11 items still provisional or open.

16. [live figure removed, ask Main] Fixed in lim_review.py Nov 8.

17. [live figure removed, ask Main] [live figure removed, ask Main] Lesson: recompute wins and losses from avgFill and avgFee in every script (goldtrip.py and the fixed scorer.py do).

18. [live figure removed, ask Main] BTCHI6 candle 0.76 became 0.93 (+1c) or 1.16 (+0c). The 'none qualify' verdicts of the on-deck grids are being rerun (W-FEEFIX). Live numbers are unaffected. Lesson: check a model's fee against live avgFee before quoting a candle PF.
