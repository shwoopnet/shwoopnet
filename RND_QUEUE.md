# R&D queue (Main keeps this; updated at least every hour)

Branch `rnd-queue`, not main. Read it with `git fetch origin rnd-queue && git show origin/rnd-queue:RND_QUEUE.md`. Rules: docs/RND_CHARTER.md section 9 and docs/POLITICS_RULES.md on main.

## Kalshi request budget (shared bucket: 12 requests a minute), re-set 2026-11-11 22:55Z, valid until the next update
| Holder | Share | For |
|---|---|---|
| Refinement (one shared pacer for all its workers) | 6 / min | economics pull (4), weather/finance/indices calibration (2); P4 and sports singles finished |
| V2 | 4 / min | CLINICAL2 first, then POLCOMBO1B core (resume), COMBO1 NBA sample, MENTPERSIST1 last |
| Idea Desk B | 2 / min | NESTCOMBO (about 100 requests), then BALLOTNO (about 124), then ECONLAG (about 350, coordinate with Refinement's economics worker) |
| Idea Desk A | 0 | counts-only work on held data (quote-data, nc-data, pol-data); ask Main for reads |
Total 12. Cause of the 429s earlier: Refinement's economics puller ran at a 3.5 s gap (up to about 17 a minute); fixed at 22:50Z.
A 429 is never retried in a loop. Nobody exceeds a share.

## Ready to test (rank by speed to a verdict)
1. Trump approval and generic ballot calibration, 3 contracts, 10c to 90c, either side, hold within 30 days: Refinement P4, running.
2. Sports singles calibration (Kalshi history only): Refinement, running.
3. Economics releases, overshoot fade plus official components (card 87, counted together): Refinement.
4. Politics scheduled events and nothing-happens (data limited; forward only): Refinement, running as screens.
5. Politics-leg combos, 2 to 30 legs (mixed with sports), simulation plus pricing sample: V2 COMBO1 after 22:15Z.
6. Clinical 90 day sample re-count (merged history) and FDA price vs base rates: V2 after 22:15Z.
7. Weather singles on NWS data, day-end rounding first (card 74 WXDAYEND): waits on NWS recorder data (PR 780), first look about Nov 13.
8. Mentions from Kalshi's own history (card 84 persistence, base rates built): V2/Refinement.
9. Attention signals, both directions (Wikipedia pageviews, GDELT): needs a reviewed host PR for GDELT; one-off pulls inside a worker are fine.
10. News fade at 15 minutes, 1 hour, 4 hours (counted in deflation): Refinement.

## Waiting on data (date it unblocks)
- MMSIM1 held-out read: about Nov 24 (single read, same bar). Owner popups 45 to 48 asked only if it passes.
- CFRTI1-BTC held-out: about Nov 22 at 50 rows.
- NC15 depth tests (NC15DEPTH1): nc-data books, after about 00:15Z Nov 12.
- Politics shadow recorder history (pol-data): accrues from Nov 11.
- Elections forward test: needs registration; no election series closes in the next 14 days.
- App Store and Steam charts: PARKED (needs a Steam key; Apple series ended).

## Idea Desks
- Desk A (structure and cross-market) and Desk B (events and information): started 2026-11-11 about 21:25Z; at least 12 cards each within 4 hours (by about 01:30Z), then the top 3 deepened. Cards land here when pre-registration is complete.

## Alive / closed today (do not retry)
Closed or falsified: cheap-side grammar GEN12/GEN13, REGIME1, SWEEP1, NONCRYPTO1, LEADLAG1, TAPEFLOW1, BFLY2, LADBFLY1 (monotonicity), PIN1, ROUND1, MENTCOMBO1, ANGLES1 (OPENQ1, WINPOS1, TAIL1, PRICECLUSTER1, ACTIVITY1), EARLYCLOSE1, NEWLIST1B, EXECSUM (EOWEEK-D0 failed held-out), external-signal sweep, spot-lead (data limited), weather prior (Open-Meteo, barred source).

## Idea Desk cards (committed 2026-11-11, nothing scored, awaiting uniqueness scoring by the Verification Analyst)
- Desk A: 11 cards, branch claude/idea-desk-a, kalshi-scalper/workers/IDEA_DESK_A_NOV11.md (d899290). Top: EXDIV1 (stock perps on ex-dividend morning; first gate is the perp terms), TIECOND1 (tie settles YES in dead hours; 2 hour count on held tables), RETAILFRAC1 (fractional sizes split retail from API flow; flow family has 2 falsified, a third closes it), CRONCLUSTER1 (cost input: do takers cluster at the start of each minute), ORHARVEST1 (bracket over-round, needs a ruling on MMSIM1 overlap / declined list).
- Desk B: 16 cards (4 combos), branch claude/idea-desk-b, kalshi-scalper/workers/IDEA_DESK_B_NOV11.md (a5dd927). Top: NESTCOMBO (nested-leg combos: combo plus NO on the strongest leg for under $1), ECONLAG (4 hour time exit after CPI, payrolls, Fed), BALLOTNO (ballot measures, status quo; NO on initiatives is paper only under the nothing-happens rule), UNRATEROUND (unrounded unemployment rate vs bracket; thin), WXCOMBO-XCITY (neighbouring cities; measure correlation from wxens by Dec 3).
- Blocked: FAANOTICE (FAA terms unread, 403). Owner flags: tie rule-text conflict ("at least" vs "strictly greater" in FX text); parlay house side (buy-NO-high-and-hold shape) needs the owner's written exception or confirmation that the "either side" rulebook covers it.
- CMD3 (commodity perp roll) relied on Yahoo bars; V2 must amend it to Kalshi's own reference_price or retire it before the Nov 20 December-crude roll.
