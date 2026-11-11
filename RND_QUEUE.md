# R&D queue (Main keeps this; updated at least every hour)

Branch `rnd-queue`, not main. Read it with `git fetch origin rnd-queue && git show origin/rnd-queue:RND_QUEUE.md`. Rules: docs/RND_CHARTER.md section 9 and docs/POLITICS_RULES.md on main.

## Kalshi request budget (shared bucket: 12 requests a minute), set 2026-11-11 21:45Z, valid until the next update
| Holder | Share | For |
|---|---|---|
| Refinement P4 | 4 / min | Trump approval and generic ballot calibration on merged historical candles (fastest real politics verdict) |
| Refinement, all other pullers together | 4 / min | sports singles calibration, politics step 2, economics, entertainment, mention base rates |
| V2 | 4 / min from 22:15Z (0 before) | COMBO1 census and pricing, politics-leg combos, clinical 90 day re-run |
| Idea Desk A, Idea Desk B | 0 | (ask Main with the exact reads) |
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
