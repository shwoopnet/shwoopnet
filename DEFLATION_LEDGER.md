# Deflation ledger (kept by the Head of R&D from Nov 12, 2026)

One file for the count of tries. Branch `rnd-queue`. Research counts on public data only; no live account figure is in this file. [research]

## Rulings (Head of R&D, Nov 12, 2026)

1. **The shared strict count is about 2.1 million, not 1.1 million.** 1,500,505 (the README and harness ledger on Nov 9, reproduced from the committed ledger files) + 300,000 (GEN12) + 300,000 (GEN13) = 2,100,505, plus about 12,600 hand-registered cells: **about 2,113,000**. The figure "about 1.1 million" that every Nov 11 and Nov 12 registration quotes came from an Oct 29 interim number and left out 1,000,000 tries. It is withdrawn; do not quote it.
2. **The research bar's z is 5.46** (one-sided normal quantile at 1 minus 0.05 / N, N 2,113,000), not 5.34. No verdict changes: nothing was passing at 5.34. One-sided is the convention; a desk that reports two-sided says so.
3. **The "lenient" count (9,009, also quoted as 9,459 to 9,495) has no written definition and is retired as a bar.** The count of hand-registered single-rule cells (about 12,600, z about 4.47) may be reported beside the strict bar as information. No label (PASS, LEAD, FALSIFIED) is taken from it.
4. **A test's own registered bar is not the research bar.** A cell test that registers its own multiplicity (for example W-SPREAD-CELL1: z 3.1 over about 58 cells) can clear ITS bar and become probe-eligible under the owner's popup; that is reported as "cleared its registered bar", never as a research-bar pass.
5. **Counting rules from today.** Every variant, cell or rule that is scored against outcomes counts as one try, including mined rules and pre-registered second lines. Shuffles, null draws and measurements that score no rule count zero. A desk writes its count in the registration before scoring and sends it to the Head of R&D, who adds the row here.
6. **Open gaps** (section 3 below) are not estimated. Where a count was never written down, the row says "not stated" and the total above is a floor.

## Tries added since the compiled table (Nov 12)

| Test | Desk | N | State |
|---|---|---|---|
| UNRATEROUND version 2 (one trade on every non-January release, paper screen; replaces Desk B's registration, whose 8c rule is reported as a subset) | Testing Desk | 1 (try 2 of the card) | REGISTERED Nov 12 (1af3415e on claude/testing-desk); RETIRED UNREAD the same day (at most 8 admissible events against a floor of 30: January revisions of the seasonal factors); 0 scored |
| V2 perps forward reads: 20 reads, 44 tries already in the compiled count | Testing Desk (owner from Nov 12) | 0 new | 18 RETIRED UNREAD Nov 12 (10 source closed, 8 cannot reach their bar); PERPEQ1 and CASHSPREAD1 part B kept |
| POL-i2 count step (count only; restricted to closes after 2026-09-12) | Testing Desk | 0 | prepared Nov 12 (bd8640a2), not dispatched; dispatched only at 400 requests or fewer |
| Stocks Desk: ten cards (16 tries if all run); prior-tries floor of 8 scored variants from the withdrawn equities and crypto work | Stocks Desk | 0 so far | registered Nov 12 (claude/stocks-desk 65ed5e97), nothing scored; S1, S3, S4, S5, S7 and S2's long-short line RETIRED UNREAD by arithmetic Nov 12 (0 tries spent); S6, S8 and S9 RETIRED UNREAD; S2 long leg SCORED Nov 12 on development (1 try): below the bar, not falsified, held-out never opened, CLOSED (figures in the private repo only); S10 deferred; tries are added here as each is scored |
| In-game lag (INGAMELAG1-M), step 1 measurement and a post-read closing number | Desk B | 0 | CLOSED Nov 12: no lag at one minute resolution (drift under cost in every sport); step 2 not run, its try not spent |
| MAPBREAK (esports break after map 1, and the break before map 3), registered as a rule before data | Desk B, built by the Testing Desk | 2 | REGISTERED Nov 12 (3aaad1c7 on claude/idea-desk-b); unscored; one family with NHLOT |
| CFRTI-K development read (1 specification) | Desk A | counted at registration | READ Nov 12: n 601, PF 1.07, z 0.60 (analyst MATCH; with a cent-rounded band n 610, PF 1.09, z 0.72); the ran-rows line (PF 0.16 to 0.19) is a diagnostic partly driven by selection; no edge near the bar |
| PERPBIN1 development read (2 tries) | Desk A | 2 | READ Nov 12: FALSIFIED on development (n 963 PF 0.91; n 971 PF 0.93); held-out not read |
| W-NO-ARM1 development read (NOSIDE1; arms and families as registered) | Refinement | counted at registration | READ Nov 12: arm A did not clear (approval family n 127 PF 1.03, halves 0.64 and 1.91; all families n 145 PF 0.91); arm B no evidence; held-out not read; CLOSED |
| W-SPREAD-CELL1, line 1 (registered) and line 2 (known-in-advance look) | Refinement | 2 | read once Nov 12 on 1,041 fresh events: FAIL on both lines (n 172 and 173; PF 0.553 and 0.592 by the Verification Analyst, 0.596 and 0.636 as first printed, fee handling differs); reproduced Nov 12 |
| CFRTI1-BTC, Kraken-only, plus two disclosed unregistered looks (Coinbase alone, Bitstamp alone) | Desk A | 3 | development read done Nov 12: no evidence at n = 32 (Kraken); carried to the held-out read |
| CFRTI-K (Kalshi perpetual in place of outside spot) | Desk A | 1 | registered Nov 12 (workers/CFRTI_K_REGISTRATION.md, 9bb9c0f2 on claude/idea-desk-a), one specification, not scored; waits on the perp candle pull |
| EXITREPLAY1 and ENTRYREPLAY1 (the 25c early sell and a resting entry replayed on R6 books) | Live-Data Forensics | 4 | read Nov 12: no new strategy; resting-entry saving is a possible version of OICORE's entry, parked |
| QUOTE2B | Desk A (was V2) | as registered Oct 29, no new try | development read done Nov 12: cash PF 0.00 on 131 hours, FALSIFIED on development (registration asked for 300 hours); held-out Nov 24 |
| Refinement's hand-registered cells of Nov 11 to 12, as itemised by Refinement on Nov 12: W-NO-ARM1 6; W-SPOTLEAD1 16; W-CAT-ECON1 36; W-CAT-SPORTS1 72; weather 36; W-POL-APPR1 240; politics screens 3 | Refinement | 409 | read (news fade: 36 cells registered, not run, not counted yet). Some of these may already sit inside the 12,600 above; the overlap is not resolved, so the total stays "about" |
| ROLLOFF proxy check | Desk B | 0 (a measurement; 30 window candidates fitted on fit days, kill rule read once on check days) | read Nov 12: proxy KILLED (0 of 33 check days within 0.3 points), card closed |
| NC15DEPTH1 pooled cell (11 non-crypto 15 minute series, five-level imbalance 0.50 or more, thin side, look 600 s before close) | Desk A | 1 | registered Nov 12 (c6a97613), forward only from 2026-11-19T00:00Z; bar n 3,400, PF 1.5 pooled and in each third, z 5.46 |
| S3 combo house side (NO at 60c to 90c, one band) | Desk B | 1 | registered Nov 12 (ed6c0bb); paper; development read on or after Nov 26 |
| ECONLAG (4 hour exit after a release, one arm; paper screen only) | Desk B | 1 | cutoff pinned; count-only stages first; not read |
| CFRTI-K lead/lag measurement | Desk A | 0 | registered before the candles are opened |
| CFRTI-B: signal and price from the R6 order book; B3 (three-venue spot) and BK (Kraken-only spot) | Desk A | 2 | approved Nov 12, to be registered before Nov 20; read once in the CFRTI sitting |
| FILLHAIRCUT1, GOLDHAIRCUT1, QUOTEVSBOOK1 (measurements on recorded books and quotes; no outcome loaded) | Live-Data Forensics | 0 | done Nov 12; QUOTEVSBOOK1: the quote recorder's market list is a copy refreshed about every 11 seconds |
| ENTRYREPLAY1_OI (OICORE's model trigger windows against the no-trigger baseline, on R6 books; public data) | Live-Data Forensics | 1 | read Nov 12: no evidence at n = 14; the trigger fires mostly when the cheap side is at 8c or less. A within-bucket cut made after the result (09afa8d) is counted as 1 more try: no evidence at n = 8 |
| RESIL1 (order-flow resilience after a sweep: touch price returns within 6 seconds; taker rule on R6 books and tape) | Desk A | 1 | registered and scripted before any event (4236f81e on claude/idea-desk-a); read once Nov 12: FALSIFIED on development, n 1,061, cash PF 0.90; the order-flow family's third, family closed |
| PERPBIN1 (the Bitcoin perpetual's 15 minute open-interest change, top tercile, as a signal for the 15 minute market; A buys YES, B buys NO at a 40c to 60c ask; the premium arm dropped because the candles carry no reference price) | Desk A | 2 | registered Nov 12 with its script (PERPBIN1_REGISTRATION.md on claude/idea-desk-a); waits on the binary candles and CANDLEVSBOOK1 |
| DEPTH1 (R6 order-book features, gold and Bitcoin; V2, registered Oct 30) | Desk A (was V2) | 20, counted at registration | unread; one read on or after 2026-11-14 |
| RAINCAL (V2, registered Oct 31) | none | 2, counted at registration | RETIRED unread Nov 12 (closed family; recorder coverage about 42 percent) |
| V2's scheduled closing-buy forward reads (the fwd_reads bundle, HOUR3-F, ENTRY2, FLIPS0-F, P6F, P6R, GAS1-F, ABSORB-F, REV1) | none | as counted at each registration | RETIRED UNREAD Nov 12 by the owner's decision (the Oct 28 rule on the closing-buy family stands) |

---

The compiled table follows. It was built read-only from the fetched branches on Nov 12, 2026 and its key lines were spot-checked against the sources (README line 9160; GEN12 and GEN13 registrations).


Scope: every pre-registered research test or search found on the fetched refs, with the number of tries (N) each one counted. Research counts on public data only. No live account figure is in this file. Numbers are quoted as written in the source; where a number is a difference of two stated running counts, or a sum made here, it says so. "Not stated" means no N was found.

Ref short names: **V2** = `origin/claude/epic-ptolemy-0amjd9`, **REF** = `origin/claude/refine-live`, **DA** = `origin/claude/idea-desk-a`, **DB** = `origin/claude/idea-desk-b`, **MAIN** = `origin/main`, **Q** = `origin/rnd-queue`.
Path short names: **R** = `kalshi-scalper/README.md` on V2 (9,229 lines; `R:1234` is line 1234), **W/** = `kalshi-scalper/workers/`, **RT/** = `kalshi-scalper/refine_tools/`.

## 0. The short answer

1. **Three separate ledgers exist, not one.** V2's own status line names them: "Ledger N: Kalshi harness about 1,500,514; single-leg about 5,130; futures 170" (V2:`kalshi-scalper/V2_STATUS.md:276`, Nov 9).
2. **The strict total is not about 1.1 million. The sources support about 2.1 million.** The README and harness ledger stood at **1,500,505** on Nov 9 (R:9160). That figure reproduces from committed files: `prior_n` 730,489 (V2:`W/scan_ledger/PRIOR_N.json`) + 500,000 lines in `W/perpgen_ledger/*.ids.gz` (100 files, counted here) + 270,016 lines in `W/scan_ledger/*.ids.gz` (37 files, counted here) = 1,500,505. GEN12 and GEN13 (300,000 each, Nov 11) are in neither ledger folder. 1,500,505 + 600,000 = **2,100,505**, before the small cell tests (about 12,600 more, section 3).
3. **Where "about 1.1 million" comes from:** V2:`W/GEN12_REGISTRATION.md:16`, "N for the Bonferroni bar = 800,000 (shared README ledger, rounded) + 300,000 = 1,100,000". The 800,000 traces to 800,780, an interim figure in R:7328 that says "GEN1 counted at its 400,000 maximum until it finishes". It leaves out PERPGEN (500,000) and the scan harness (270,016), and GEN13 reused the same 1,100,000 without adding GEN12's 300,000.
4. **The lenient count 9,009 is real arithmetic on a stale base.** 9,009 = 7,731 + 1,064 (REGIME1) + 214 (ANGLES1). 7,731 = 5,319 (V2) + about 900 (Refinement) + 1,512 (a cell count Refinement later corrected to 3,240, giving 9,459). On the corrected base the same two additions give 10,737, and at least 1,434 more V2 cells registered on Nov 11 were never added to it.

## 1. The table

Columns: test or search | date | desk | N counted | running count as stated in the source | verdict | source.

### 1a. Strict ledger: the README running count and the scan harness (V2 branch)

| # | Test or search | Date | Desk | N counted | Running count as stated | Verdict | Source |
|---|---|---|---|---|---|---|---|
| 1 | 60 second scalp, H1 to H7 | to 2026-10-07 | Research (before V2) | 8 | 8 | FALSIFIED | R:675 "Strategy variants tried before this ledger: 8" |
| 2 | L1, L2, L3 and one parameter search | 2026-10-07 | Research | 3 hypotheses + 437 rules | "11 hypotheses ... plus one parameter search of 437 rules" | FALSIFIED | R:773 |
| 3 | L8, L9, second parameter search, M1 with 5 information cuts, 42 strategy search with 2 baseline cuts | to 2026-10-08 | Research | 742 (13 hypotheses + 729 rules) + 1 + 5 + 42 + 2 | 792 | FALSIFIED or NOT_ENOUGH_DATA | R:1307 to 1309 |
| 4 | P1 | 2026-10-08 | Research | 1 | 793 | FALSIFIED | R:36 |
| 5 | Four slot search | 2026-10-08 | Research | 1,760 | 2,553 | FALSIFIED or NOT_ENOUGH_DATA | R:1670 |
| 6 | F6, F7, Q1 to Q3 and two Q1 thresholds, F8, N1, N2, X1 to X7, B1 to B3, F9 | 2026-10-08 | Research | listed items sum to 21; running count moves 29 | 2,582 | FALSIFIED or NOT_ENOUGH_DATA | R:36 to 37, R:1698, R:2301 |
| 7 | T1 to T4 | 2026-10-09 | Research | 4 | 2,586 | FALSIFIED | R:36 |
| 8 | T5, E1, E2, B4; X8 (registered) | 2026-10-10 | Research | 4 + 1 | 2,590, then 2,591 | FALSIFIED; X8 not run | R:36, R:2605 |
| 9 | OW1 (2), OW2 (4), OW3 to OW7 (3) | 2026-10-12 | Research | 9 | 2,600 | OW2 FALSIFIED; OW1 forward | R:2710, R:2745, R:2776 |
| 10 | SS1 | 2026-10-12 | Research | 216 | 2,816 | FALSIFIED | R:2825, R:2827 |
| 11 | SS2 | 2026-10-12 | Research | 1,760 | 4,576 | no survivor (frozen top 10: 1 FALSIFIED, 9 NOT_ENOUGH_DATA) | R:2858, R:2861 to 2864 |
| 12 | E3 (7), E4 (3), WX1, DT1, XM1 (2), SP1, E5 (8), BUYDIP1 (6), PAPER1 (3) and other single tries | 2026-10-13 to 10-20 | Research | 49 by difference of stated counts | about 4,625 | mixed, none passed | R:2933 to R:3845 |
| 13 | FWD5, FWD6, HS1, HS1b, HL1, SL1, EL1, FWD7, EX10, SESS1, SCI1, SIDE1, HOUR1, XLEAD1, DL10, JUMP1b, SQ1, TS1, CW10, FEAT1 to FEAT4, CROWD1, CONC1, CONC2-F, FLAT1 to FLAT3, FLAT-R, STACK1, SIZE1, ENTRY1, WX1 (Oct 22), LOSSCL1, GAS1-F, RECORD1 | 2026-10-21 to 10-22 | Research | 82 by difference (1 to 4 each as stated) | about 4,707 | mixed, none passed | R:4426 to R:5693 |
| 14 | SCAN1 and SCAN2-F | 2026-10-23 | Research | +11 and +1; "the mining over about 4,500 rules is the search itself" and is not counted | about 4,718 | NOT_ENOUGH_DATA | R:5718, R:5720, R:5736 |
| 15 | FLIP1 (1), HOUR2 (1), BTC1 (4), IDEAS20 (20), IDEAS20B (20), HOUR3 (1), IDEAS20C (38), LAG2B (1), IDEAS20D (16) | 2026-10-23 | Research | 102 stated; running count moves 117 | about 4,835 | none passed | R:5789 to R:6071 |
| 16 | IDEAS100 | 2026-10-23 | Research | 200 | about 5,040 | no rule passed | R:6075, R:6081 |
| 17 | SMOOTH20 (40, plus 2 forward), SMOOTH2 (20), COMM1 (26) | 2026-10-23 to 10-24 | Research | 88 | about 5,135 | none passed | R:6101 to R:6163 |
| 18 | Information look, QUIRK1 (36), IV1 (2), TAPE20 (16) | 2026-10-25 | Research | 54 stated; about 65 more not itemized | about 5,260 | none passed | R:6221 "tries about 5,200", R:6236, R:6250, R:6274 |
| 19 | SEARCH5K | 2026-10-25 | Research | 5,000 | about 10,260 | FALSIFIED | R:6286, R:6308, R:6316 |
| 20 | RT1 (2), RT2 (1), BTCBOOK (4) | 2026-10-25 | Research | 7 | about 10,267 | see source | R:6318, R:6348, R:6382 |
| 21 | FACT1 | 2026-10-25 | Research | 4,230 | about 14,500 | NOT_ENOUGH_DATA, none held out | R:6407, R:6426, R:6433 |
| 22 | PROG1 (4), two forward claims (2), P5 (2), P6 (1), P6F (1), P6R (1), LAD1 (6), SC1 (4), F6 and F7 on tennis and totals (2) | 2026-10-25 to 10-26 | Research | 23 | about 14,540 | FALSIFIED or NOT_ENOUGH_DATA | R:6435 to R:6542 |
| 23 | CRYPTO1 | 2026-10-26 | Research | 384 | about 14,930 (the next test resumes at 14,544) | FALSIFIED | R:6565, R:6581, R:6592 |
| 24 | FP1 (4), FP2 (2), FP3 (80 registered; result says "64 + 300-draw null"), HOURS1 (1), HOURS2 (4) | 2026-10-26 to 10-27 | Research | 91 as registered | about 14,635 | FP3 FALSIFIED | R:6598 to R:6665, R:6719 to 6723 |
| 25 | HUNT1 | 2026-10-27 | Research | "576 cells + 200 shuffles" | about 15,211 | FALSIFIED | R:6675, R:6683 |
| 26 | HUNT2 | 2026-10-27 | Research | "about 2,000 cells + 100 shuffles"; result "about 2,000 plus 200 shuffles" | about 17,300, then about 17,500 | FALSIFIED | R:6687, R:6691, R:6695 |
| 27 | WX3 (1), MAKER1 (6), BOUNCE1 (10 + 3) | 2026-10-27 | Research | 20 | about 17,589 | see source | R:6701, R:6725, R:6741 |
| 28 | UNDER1 | 2026-10-27 | Research | "about 2,500 cells + 100 shuffles" | about 20,200 | FALSIFIED | R:6759, R:6763 |
| 29 | REV1 (1), PULL1 (576), SWEEP1 of Oct 27 (24 rules + controls), CAL1 of Oct 27 (7 weekdays x 16 series cells + 100 shuffles), PM1 (1 test x 2 thresholds) | 2026-10-27 | Research | as stated | about 20,915 | PULL1, CAL1 FALSIFIED | R:6769 to R:6815 |
| 30 | PERP3 of Oct 27 | 2026-10-27 | Research | "336 rules + 100 null draws" | about 21,350 | FALSIFIED | R:6835, R:6849 |
| 31 | MAKER2 (2), MAKER3 (2), THROTTLE1 (3 variants + 200 shuffles), FLOW1 of Oct 27 (32 variants), GROW1 (8 rules + 200 bootstrap resamples), CPI1 (2 series x 1 rule), EXIT2 (6 lines), MENT1 of Oct 28 (1 rule) | 2026-10-27 to 10-28 | Research | as stated | about 21,817 | THROTTLE1, FLOW1, GROW1 FALSIFIED | R:6861 to R:6952 |
| 32 | PERPFLOW1 | 2026-10-28 | Research | "288 rules + 100 null draws" | about 22,108 | FALSIFIED | R:6974, R:6984 |
| 33 | QUOTE1 (4), LOCK2 (2), cards CARRY1, PAIRS1, FUNDX1, INDEX1, GOLD2 | 2026-10-28 | Research | 6 stated; cards not stated | about 22,123 | open cards | R:6992 to R:7121 |
| 34 | SCALP1, SCALP2, HIST1 | 2026-10-28 | Research | HIST1 "576 tries"; SCALP1 and SCALP2 not stated | folded into about 199,000 | FALSIFIED | R:7135 to R:7169 |
| 35 | AUTO1, AUTO2, AUTO3 | 2026-10-28 | Research | "176,640 trees" | "about 199,000 including AUTO1 to AUTO3" | 0 admissible holdout passes | R:7201, R:7209 |
| 36 | DAYCUT1 (6), MAKER4 (5 bounds, 1 verdict), SIZE1, SIZE2, ARB2 (2), ARB3 (1), RULES1 (0), FEE1 (6 sizes), ARB4 (1) | 2026-10-28 to 10-29 | Research / V2 | as stated | about 199,018 | all FALSIFIED where scored | R:7229 to R:7295, R:7335 |
| 37 | GEN1 | 2026-10-29 | V2 | 12,056 generated (5,000 distinct) | "N tried 211,074 (GEN1 alone, with prior work)" | NO_WINNER | R:7333 |
| 38 | GEN1S | 2026-10-29 | V2 | 201,762 generated (5,000 distinct) | "800,780 (GEN1 counted at its 400,000 maximum until it finishes)"; later "about 411,000" | NO_WINNER | R:7328, R:7361 |
| 39 | THETA1 (27 cells), ARB5 (1) | 2026-10-29 | V2 | 28 | "about 411,000 + 27" | FALSIFIED | R:7354, R:7361, R:7363, R:7388 |
| 40 | GEN2 | 2026-10-29 | V2 | 14,330 generated (7,500 distinct) | "N tried 425,330" | NO_WINNER | R:7386 |
| 41 | GEN3 | 2026-10-29 | V2 | 13,237 generated (5,000 distinct) | "N tried 438,597" | pass VOID (universe look-ahead); CORR1 then FALSIFIED | R:7405, R:7416, R:7487 |
| 42 | CORR1, LADL1 (8), CONF1 (3), EXIT1 (4), REGIME1 of Oct 29 (5), GOLD1D (1), MM1, LOOK1 (25), BAND1 (20), ROUND1 (1) | 2026-10-29 | V2 | 67 stated; CORR1 and MM1 not stated | about 438,670 | FALSIFIED; MM1 NOT_ENOUGH_DATA | R:7421 to R:7495 |
| 43 | GOLDFV1 (4), LOCK2H (1), CONF2 (1), TIMEX1 and DCAP1 (56), MUT1 (106), MKTTIME1 (70), MKTTIME1-F (1), FALS1 (10), XMAC1 (4), PPW1 (3), DAILY2 (8), INX1 (6), QUOTE2B (6), HOUSE1 (12), HOUSE2 (18), HOUSE3 (40), BAND2 (24), MAKER5 and L1Q1 (18), SIZE3 (17), STRUCT1 (14), BTCAVG (4), LATECAL (33) | 2026-10-29 | V2 | 456 stated; running count moves 523 | about 439,193 | FALSIFIED or NOT_ENOUGH_DATA; forward items open | R:7495 to R:7720 |
| 44 | GEN4 | 2026-10-29 | V2 | "N +36,417" | about 475,577 | broken by FALS3 | V2:`kalshi-scalper/V2_STATUS.md:118` (no N in the README) |
| 45 | FALS3 | 2026-10-29 | V2 | 5 | not stated | GEN4 core BROKEN | R:7724 |
| 46 | GEN5 | 2026-10-29 | V2 | "N +25,592" | about 501,169 | FALSIFIED | V2:`kalshi-scalper/V2_STATUS.md:116` (no N in the README) |
| 47 | GEN6 | 2026-10-29 | V2 | 62,163 | about 563,337 | gold FALSIFIED; Bitcoin 13 NOT_ENOUGH_DATA | R:7730 |
| 48 | FALS4 (23), SLOTEX (504), SLOTEX-ETH (64), EVT1 (480) | 2026-10-29 | V2 | 1,071 | about 592,030 | SLOTEX NOT_YET_FALSIFIED below the bar; EVT1 no evidence | R:7734 to R:7750 |
| 49 | GEN7 | 2026-10-29 | V2 | 27,621 | about 590,982 | gold FALSIFIED; Bitcoin survivors not independent of GEN6 | R:7738 |
| 50 | ESPN1 (4), NEWH1 (9), GOLDFILL (8), MECH1 (2), NEWH2 (4), NEWH3 (4), EXITOI-G (4), NEWH4 (5), NEWH5 (4), NEWH6 (8), NEWH7 (4), NEWH8 (8) | 2026-10-30 | V2 | 64 | about 592,094 | FALSIFIED or NOT_ENOUGH_DATA | R:7754 to R:7798 |
| 51 | GEN8 | 2026-10-30 | V2 | 35,738 | about 627,838 | FALSIFIED | R:7810 |
| 52 | NEWH9 (7), LADFADE (1), NEWH10 (6), NEWH11 (4) | 2026-10-30 | V2 | 18 | about 627,856 | no survivor | R:7814 to R:7844 |
| 53 | GEN9 | 2026-10-30 | V2 | "51,067 (51,055 draws plus 12 information looks)" | about 678,923 | no survivor | R:7860 |
| 54 | NEWH12 (6), FALS5 (12) | 2026-10-30 | V2 | 18 | about 700,166 | see source | R:7879, R:7905 |
| 55 | GEN10 | 2026-10-30 | V2 | 21,225 | about 700,154 | no survivor | R:7883 |
| 56 | GEN11 | 2026-10-30 | V2 | 28,450 | about 728,623 | no survivor | R:7935 |
| 57 | DEPTH1 (20 at the read), NEWH15 (3), FXUSD (4), SPORTCONS1 (3), LADLONG1 (4), OICOREX1 (8), ECONNEW1 (3), ECONNEW2 (2), WXNEW1 (2), DERIBIT-IMPLIED, SPORTS-PRE, RAINCAL, CHART1, EQUAKE1, TSA1, MORTGAGE1, SPOTD1 (2 each), WTIW1 (3), ESPORT1 (2), LAG15 (6), HOURLY1 (6), XMET1, XCRY1, XOI1, BOOKCH1, QSTALE1 (2 each), OEXIT1 (3), FAMSPORTS (2), FAMXV (2), EVENT1 (8), VOLGAP1 (6), EVENT830 (1) | 2026-10-30 to 11-03 | V2 | 114 stated; running count moves 117 | about 728,740 | FALSIFIED or NOT_ENOUGH_DATA; forward items open | R:7983 to R:8316 |
| 58 | IDXFUT1 (N +8), TODSEAS1 (N +22), SPIKE1 (+4), SETTLE1 (+10), VOLSLOT1 (+6), SNAPBACK1 (+8), SWING1 (+2), OIHR1 (+4), PERPOI1 (+4), HRSEAS1 (+18), NOWCAST1 (+2), XLADDER1 (+4), BARRIER1 (+4), FEDIMPL1 (+4); USWEEP1 "N added is kept at 6 x 210 = 1,260"; NEWLIST1 and STRADDLE1 not stated | 2026-11-03 | V2 | 1,360 stated | about 730,044 | FALSIFIED or NOT_ENOUGH_DATA | R:8318 to R:8426, R:8363 |
| 59 | MAKERTAIL1 (+4), GAS2 (+2), BOOKIMB1 (+2), XETH1 (+2), SLOWSTAT1 (+2), ESPORTM1 (+2), RECORD1B (+2), LADCOH1 (+3), RAINFACT1 (+2), plus BOOKS1, BOOKS2, BOOKNCAA1, SOCCER1 and others in the same span | 2026-11-03 to 11-05 | V2 | 21 stated here; running count moves 399 | about 730,443 | FALSIFIED or NOT_ENOUGH_DATA | R:8450 to R:8915 |
| 60 | Perps cards: FUNDP1, CARRY1, BASIS1 (+3), RV1 to RV3 (+16), EVM1 to EVM4 (+3), CASHSPREAD1 group (+4), OVN1 to OVN4 (+8), CPREM1 group (+4), PBOOK1 to PBOOK3 (+3), PERPEQ1 to PERPEQ4 (+15), LL1, XS1, RO1 (+3), PSET1 to PSET3 (+3), SEASON1 (+1), MVE1 (+2), FLOWX1 (+2), XV2 (+1), DIGMET1 (+1) | 2026-11-06 | V2 | 69 stated | about 730,491; `PRIOR_N.json` freezes 730,489 | NOT_ENOUGH_DATA, NOT_RUNNABLE or FALSIFIED | R:8918 to R:9009; V2:`W/scan_ledger/PRIOR_N.json` |
| 61 | PERPGEN, NONCRYPTO slice | 2026-11-06 | V2 | "N +100,000 exact" | not stated | 0 discovery survivors | R:8984 to 8985 |
| 62 | PERPGEN, CRYPTOPRICE slice | 2026-11-06 | V2 | "N +200,000 exact" | not stated | 0 of 200,000 | R:8987 to 8988 |
| 63 | PERPGEN, CRYPTOCTX slice | 2026-11-06 | V2 | "N +200,000 exact" | "about 730,491 plus 500,000" | 3 discovery survivors of 200,000, none promoted | R:8990 to 8991, R:9003 |
| 64 | CMD1 to CMD4 (+21), CASHOPEN2 group (+8), EARNPERP1 to 3 (+5), STOCKPERP1 to 6 (+14), SOFR1 (+1), CRICT20 (+2), VIRT1 (+3), NPBKBO1 (+1) | 2026-11-06 to 11-07 | V2 | 55 | about 1,230,543 | NOT_ENOUGH_DATA (CMD later retired) | R:9011 to R:9071 |
| 65 | BINPATH | 2026-11-07 | V2 | "N +60,016" (60,000 rules plus 16 baseline lines) | "N 1,290,505" | model result only, not an edge | R:9074, R:9077 |
| 66 | HISTBTC1 | 2026-11-08 | V2 | 30,000 | "N 1,320,505" | FALSIFIED, zero survivors | R:9083 |
| 67 | HISTETH1 | 2026-11-08 | V2 | 30,000 | "N 1,350,505" | FALSIFIED, zero survivors | R:9089 |
| 68 | COINRACE1 | 2026-11-08 | V2 | 30,000 | "N 1,380,505" | FALSIFIED, zero survivors | R:9098 |
| 69 | COMBO1 of Nov 8 (metal pairs) | 2026-11-08 | V2 | 30,000 | "N 1,410,505" | FALSIFIED, zero survivors | R:9104 |
| 70 | COMBO2 and COMBO3 | 2026-11-08 | V2 | 2 x 20,000 | "N 1,450,505" | FALSIFIED, zero survivors | R:9110 |
| 71 | NFLPC1 | 2026-11-09 | V2 | 20,000 | "N 1,470,505" | 0 deflated survivors | R:9157 to 9158 |
| 72 | HISTLAD1 | 2026-11-09 | V2 | 30,000 | "N 1,500,505, bar z 5.400" | FALSIFIED on development | R:9160 to 9161 |

Check made here: `W/perpgen_ledger` holds 500,000 lines and `W/scan_ledger` holds 270,016 lines (binpath 60,016; histbtc 30,000; histeth 30,000; coinrace 30,000; combo metals 30,000; combo crypto 20,000; combo cross 20,000; ladder 30,000; NFL pairs 20,000). 730,489 + 500,000 + 270,016 = 1,500,505, equal to R:9160.

### 1b. Strict additions that sit outside the harness ledger (V2 branch)

| # | Test or search | Date | Desk | N counted | Total as stated | Verdict | Source |
|---|---|---|---|---|---|---|---|
| 73 | GEN12 | 2026-11-11 | V2 | 300,000 drawn and scored | "800,000 (shared README ledger, rounded) + 300,000 = 1,100,000" | FALSIFIED, 0 survivors, held-out unread | V2:`W/GEN12_REGISTRATION.md:16`, `W/GEN12_RESULT.md:5` |
| 74 | GEN13 | 2026-11-11 | V2 | 300,000 drawn and scored | "1,100,000 (800,000 shared ledger + 300,000 this sweep)" | FALSIFIED, 0 survivors, held-out unread | V2:`W/GEN13_REGISTRATION.md:17`, `W/GEN13_RESULT.md:5` |

### 1c. The small-count ("lenient") ledger, V2 side

| # | Test or search | Date | Desk | N counted | Running count as stated | Verdict | Source |
|---|---|---|---|---|---|---|---|
| 75 | FUT1, FUT2 (50 variants), FUT3 | 2026-11-09 | V2 | futures ledger N 60, then 160, then 170 | separate futures ledger | zero survivors | R:9135, R:9141, R:9169 |
| 76 | SINGLELEG1 | 2026-11-09 | V2 | "N 600" (440 potential cells) | 600 | FALSIFIED on development | R:9148 to 9149 |
| 77 | SINGLELEG2 | 2026-11-09 | V2 | "cumulative N up to 2,360" | 2,360 | zero shortlisted | R:9151 |
| 78 | SINGLELEG3 | 2026-11-09 | V2 | 2,080 potential cells; "N 4,440 registered (printed 4,600 with the 160 prior counted again)" | 4,440 | FALSIFIED on development | R:9154 to 9155 |
| 79 | ROUND1L (N 4,500), NEWSER1 (200 cells, N 4,700), LADDOW1 (N 4,920), COMSEAS1 (N 218, own count), LADCONV1 (1 try), SERIESLAG1, NFLCOMBO1, OICORE x L1 filter, REGIME1 of Nov 9 (10 cuts) | 2026-11-09 | V2 | as stated; several not stated | "single-leg about 5,130" | no shortlist | R:9130 to R:9186; V2:`kalshi-scalper/V2_STATUS.md:276` |
| 80 | OPEN1H (24), CHEAPEXIT1 (8), AAAGAS1 (2), MENT1 of Nov 10 (12), WING1 (12), AAASPREAD1 (not stated), SOFR1 (1), TNOTE1 (not stated) | 2026-11-10 | V2 | 59 stated | "N 5,187" | FALSIFIED or NOT_ENOUGH_DATA | V2:`W/OPEN1H_PROTOCOL.md:6`, `W/CHEAPEXIT1_PROTOCOL.md:6`, `W/AAAGAS1_PROTOCOL.md:8`, `W/MENT1_PROTOCOL.md:5`, `W/WING1_PROTOCOL.md:4`, `W/SOFR1_PROTOCOL.md:6`; R:9229 |
| 81 | HLAD2 (1 + 12, parked), OI1 (+6), CFRTI1 (1) | 2026-11-10 to 11-11 | V2 | 20 | "about 5,207 after this try" | OI1 FALSIFIED; CFRTI1 pooled bar not met; HLAD2 parked | V2:`W/HLAD2_PROTOCOL.md:7`, `W/OI1_PROTOCOL.md:6`, `W/CFRTI1_PROTOCOL.md:8` |
| 82 | SWEEP1 of Nov 11 | 2026-11-11 | V2 | "112 tests"; result "0 survivors of 110 tests" | "N after = 5,207 + 112 = 5,319" | 0 survivors | V2:`W/SWEEP1_PROTOCOL.md:8`, `:12` |
| 83 | MMSIM1 (1), MMSIM2 (18) | 2026-11-11 | V2 | 19 | "ledger about 5,190 + 1 + 18" | MMSIM1 NOT_YET_FALSIFIED on development, held-out read open; MMSIM2 no variant at the bar | V2:`W/MMSIM1_PROTOCOL.md:12`, `W/MMSIM2_PROTOCOL.md:15` |
| 84 | NONCRYPTO1 | 2026-11-11 | V2 | 127 | "about 7,731 (V2 + Refinement)"; not added to it | 0 survivors of 127 | V2:`W/NONCRYPTO1_PROTOCOL.md:6`, `:10` |
| 85 | REGIME1 of Nov 11 | 2026-11-11 | V2 | 1,064 | "7,731 (V2 + Refinement ledger) + 1,064 = 8,795" | 0 survivors | V2:`W/REGIME1_PROTOCOL.md:13`, `:18` |
| 86 | LEADLAG1 | 2026-11-11 | V2 | "1026 cells, all counted into N" | quotes 8,795 without adding | 0 of 1,026 pass | V2:`W/LEADLAG1_PROTOCOL.md:18` |
| 87 | MMHOUR1 | 2026-11-11 | V2 | "N added = 92" | "5,209 before; about 8,795 after the idea cards registered so far" | NOT_ENOUGH_DATA | V2:`W/MMHOUR1_PROTOCOL.md:13` |
| 88 | ANGLES1 | 2026-11-11 | V2 | 214 (140 + 16 + 18 + 16 + 24) | "8,795 (+214 = 9,009)"; "1,100,000 + 214 = 1,100,214" | 0 survivors of 214 | V2:`W/ANGLES1_PROTOCOL.md:23`, `:27` |
| 89 | TAPEFLOW1 (3), BFLY2 (1), LADBFLY1 and XSER1 (2), EXECSUM (4) | 2026-11-11 | V2 | 10 | each quotes "1,100,000 plus" its own count | FALSIFIED, closed, or failed development | V2:`W/TAPEFLOW1_PROTOCOL.md:22`, `W/BFLY2_PROTOCOL.md:27`, `W/LADBFLY1_XSER1_PROTOCOL.md:2`, `W/EXECSUM_PROTOCOL.md:28` |
| 90 | PIN1, ROUND1, AVG1 (32), STALE1 (80), EARLYCLOSE1 (18), CAL1 and NEWLIST1B (20 registered) | 2026-11-11 | V2 | 150 | each quotes "about 1,100,000 +" its own count | no survivor; AVG1 and CAL1 NOT_ENOUGH_DATA; AVG1, STALE1, EARLYCLOSE1 later retired | V2:`W/PIN1_ROUND1_AVG1_PROTOCOL.md:9`, `W/STALE1_PROTOCOL.md:9`, `W/EARLYCLOSE1_PROTOCOL.md:7`, `W/CAL1_NEWLIST1_PROTOCOL.md:27` |
| 91 | MENTCOMBO1 (not stated), MENTPERSIST1 (2), CLINICAL2 (4), COMBO1 of Nov 11 (1 census + 2), POLCOMBO1B (at most 29, census only), TIECOND1 (1) | 2026-11-11 to 11-12 | V2 | 10 stated, plus at most 29 | each quotes "about 1,100,000 +" its own count | MENTCOMBO1 FALSIFIED on development; the rest NOT_ENOUGH_DATA, closed or retired | V2:`W/MENTCOMBO1_PROTOCOL.md:11`, `W/MENTPERSIST1_PROTOCOL.md:27`, `W/CLINICAL2_PROTOCOL.md:32`, `W/COMBO1_PROTOCOL.md`, `W/POLCOMBO1B_PROTOCOL.md:32`, `W/TIECOND1_REGISTRATION.md:22` |
| 92 | THREELEG1 ("N 0"), EXDIV1, RETAILFRAC1 and CRONCLUSTER1 stage A (adds 0), ORHARVEST1 stage 1 ("0 new"), MMMAP1 ("0 new"), POWER2 ("N tried: 0") | 2026-11-11 to 11-12 | V2 | 0 | unchanged | retired or closed without a try | V2:`W/THREELEG1_FEASIBILITY.md`, `W/RETAILFRAC1_CRONCLUSTER1_REGISTRATION.md:21`, `W/ORHARVEST1_STAGE1_REGISTRATION.md:21`, `W/MMMAP1_REGISTRATION.md`, `W/POWER2_QUEUE.md:2` |

### 1d. Refinement desk (REF branch)

| # | Test or search | Date | Desk | N counted | Total as stated | Verdict | Source |
|---|---|---|---|---|---|---|---|
| 93 | Earlier Refinement tries, not itemized | to 2026-11-09 | Refinement | "about 540 earlier" | about 540 | not stated | REF:`RT/SHADOW_REGISTRATIONS_WEEK1.md:3` |
| 94 | W-HUNT1 | 2026-11-09 | Refinement | 121 cells | "about 670" | shadow candidates only, never a pass | REF:`RT/SHADOW_REGISTRATIONS_WEEK1.md:3` |
| 95 | Shadow batch 2 | 2026-11-10 | Refinement | "best of 120 cells" | "N about 760"; "about 770" | shadow candidates only | REF:`RT/SHADOW_REGISTRATIONS_WEEK1.md:33`, `RT/ONDECK.md:3` |
| 96 | Rows 62 and 71 | 2026-11-11 | Refinement | 2 | "N tried so far about 900; this adds 2" | shadow candidates only | REF:`RT/ROW62_71_REGISTRATION_AND_RESULT.md:2` |
| 97 | W-SWEEP-EXT1 | 2026-11-11 | Refinement | registered 6,480 cells, then 1,512 and 1,728, scored 3,240 | "5,319 + 900 + 3,240 = 9,459" | 0 at the bar | REF:`RT/SWEEP_EXTERNAL_SIGNAL_REGISTRATION.md:2`, `:13`; `RT/SWEEP_EXT1_PLAN.md:6` |
| 98 | Category calibration (economics, weather, finance, indices, politics, entertainment) | 2026-11-11 to 11-12 | Refinement | grid "160 cells"; added as "222"; handoff says "216 + 74"; weather part "108 cells in my scope"; economics part "36 cells" | "about 7,731 plus 222 = about 7,950" | no shortlist | REF:`RT/CATEGORY_CALIBRATION_REGISTRATION.md:2`, `:5`; `kalshi-scalper/REFINE_HANDOFF.md:79`; `RT/WEATHER_FIN_IDX_CAL_PLAN_AND_RESULT.md:11`, `:18`; `RT/ECON_CAL_REGISTRATION.md:6`, `:13` |
| 99 | Politics approval calibration | 2026-11-11 | Refinement | 240 cells | "about 7,950 tries; with these it is about 8,190" | UNDERPOWERED | REF:`RT/POLITICS_APPROVAL_CAL_REGISTRATION.md:21`; `RT/POLITICS_APPROVAL_CAL_RESULT.txt:9` |
| 100 | Politics step 2 (about 12 cells), cards 74 and 84 (not stated), sports calibration (72 cells) | 2026-11-11 | Refinement | about 12 + 72; cards not stated | quote "about 7,950" | sports: shortlist pass 0 | REF:`RT/POLITICS_STEP2_PLAN.md:2`, `RT/CARDS_74_84_REGISTRATION_AND_RESULT.md:2`, `RT/SPORTS_CAL_REGISTRATION.md:2`, `RT/SPORTS_CAL_RESULT.txt:1` |
| 101 | NO arm approval | 2026-11-12 | Refinement | 6 cells | "N before this test 9,459 ... N = 9,465" | see source | REF:`RT/NO_ARM_APPROVAL_REGISTRATION.md:36` |
| 102 | Sports spread cell | 2026-11-12 | Refinement | 1 | "9,465 + 1 cell" | open | REF:`RT/SPORTS_SPREAD_CELL_REGISTRATION.md:10` |
| 103 | Row 75 WXREVISE | 2026-11-12 | Refinement | 4 cells registered; "no cell was scored" | "9465 shared + 4 cells registered = 9469" | NOT_ENOUGH_DATA (nothing scored) | REF:`RT/ROW75_WXREVISE_REGISTRATION_AND_RESULT.md:13`, `:27` |
| 104 | News fade | 2026-11-12 | Refinement | 36 cells | "about 9,459 ... Adding 36: N = 9,495" | open (forward) | REF:`RT/NEWS_FADE_REGISTRATION.md:54`, `:56` |
| 105 | W-SPOTLEAD1 (8 variants x 2 assets), Deribit ladder (2), MAKERREPLAY1 (1), WXPRIOR (1; "5 variants counted for the family") | 2026-11-11 to 11-12 | Refinement | 16 + 2 + 1 + 1 | "added to the project's try count"; no total given | open | REF:`RT/SPOTLEAD1_REGISTRATION_AND_RESULT.md:17`, `RT/DERIBIT_LADDER_REGISTRATION.md:7`, `RT/MAKERREPLAY1_REGISTRATION.md:2`, `RT/WXPRIOR_REGISTRATION.md:16` |
| 106 | Diagnostics marked "try count 0": W-OIBASE1, W-OIGAP1 and descriptive reads in the status file | 2026-11 | Refinement | 0 | unchanged | descriptive, no verdict | REF:`RT/OIBASE1_REGISTRATION_AND_RESULT.md:1`, `RT/OIGAP_REGISTRATION_AND_RESULT.md:1` |

### 1e. Idea desks

| # | Test or search | Date | Desk | N counted | Total as stated | Verdict | Source |
|---|---|---|---|---|---|---|---|
| 107 | Idea Desk A, 11 cards (CRONCLUSTER1, TIECOND1, EXDIV1, ORHARVEST1, RACEMAKE1, RESIL1, RETAILFRAC1, BASEFX1, PERPBIN1, TWINLOCK1, AUCTION1) | 2026-11-11 to 11-12 | Desk A | "0 tries" for cards 1, 2, 3; others not run | "about 1,100,000" and "lenient bar (N 8,795)" | closed, held or retired without a try | DA:`W/IDEA_DESK_A_NOV11.md:9` to `:17`; `W/IDEA_DESK_A_PROTOCOLS.md:5` |
| 108 | Idea Desk A batch 2: WXDAYEND (no new test), POL-n1 (2 tries), ECONFADE (2 tries) | 2026-11-12 | Desk A | 4 registered, none run | shared count, no number | open | DA:`W/IDEA_DESK_A_PROTOCOLS2.md:30`, `:81` |
| 109 | Idea Desk B, 16 cards, +1 or +2 each (one card "+0") | 2026-11-11 | Desk B | "N +27 in total if every card ran" | not stated | 12 of 16 closed or retired without a try | DB:`W/IDEA_DESK_B_NOV11.md:5`, `:35` |
| 110 | Idea Desk B, BALLOTNO (the only card read) | 2026-11-12 | Desk B | "N +2" | not stated | NOT_ENOUGH_DATA for the registered test; reported as a description of one election night, then parked | DB:`W/IDEA_DESK_B_PROTOCOLS.md:143`, `:204` |

## 2. Running totals and whether the quoted figures hold

### 2a. Strict total

| Step | N | Basis |
|---|---|---|
| README running tally before the ledger folders | 730,489 | V2:`W/scan_ledger/PRIOR_N.json` ("prior_n": 730489, as of 2026-11-07) |
| PERPGEN ledger | + 500,000 | 100 files, 500,000 lines, counted here; R:8984, R:8987, R:8990 |
| Scan harness ledger | + 270,016 | 37 files, 270,016 lines, counted here |
| **Harness total, Nov 9** | **1,500,505** | R:9160 "N 1,500,505, bar z 5.400" |
| GEN12 and GEN13 | + 600,000 | V2:`W/GEN12_RESULT.md:5`, `W/GEN13_RESULT.md:5` |
| **Strict total from stated counts** | **2,100,505** | sum made here |
| Small cell tests on all desks (section 2b) | about + 12,600 | sum made here, approximate |
| **Strict total, everything found** | **about 2.11 million** | one-sided Bonferroni z about 5.46 (computed here; 5.34 is the bar at 1,100,000) |

**Does the record support "shared N about 1.1 million, z 5.34"? No.** The z of 5.34 is correct for N 1,100,000, but 1,100,000 is not the count. It is 800,000 plus GEN12 alone. The project's own README ledger was already at 1,500,505 two days before GEN12, and MAIN says "After 1.5 million rules tried" (MAIN:`docs/STRATEGY_LIFECYCLE.md:7`). The strict count from stated sources is about 2.1 million, and the bar at that N is about 5.46.

A few tries sit in the README but not in the harness sum (rows 64: 55 tries after the 730,489 freeze), so the README's own figure before BINPATH is 1,230,543 while the harness base is 1,230,489. The gap is 54 and moves no bar.

### 2b. Lenient count

**Definition found.** No file defines the word "lenient". It first appears as "the lenient bar" for N 8,795 (V2:`W/PIN1_ROUND1_AVG1_PROTOCOL.md:9`, `W/RETAILFRAC1_CRONCLUSTER1_REGISTRATION.md:21`). The same number is called "the V2 + Refinement ledger" (V2:`W/GEN13_REGISTRATION.md:17`, `W/REGIME1_PROTOCOL.md:13`), "the smaller ledger" (V2:`W/ANGLES1_PROTOCOL.md:23`) and "the small-count bar" (V2:`W/CLINICAL2_PROTOCOL.md:32`). Its content, traced: V2's single-leg ledger, opened at SINGLELEG1 on Nov 9 with N 600 and carried to 5,319 at SWEEP1 (V2:`W/SWEEP1_PROTOCOL.md:8`), plus Refinement's own count of about 900, plus the W-SWEEP-EXT1 cells (REF:`RT/SWEEP_EXT1_PLAN.md:6`: "V2 5,319 + Refinement about 900 + 3,240 = 9,459"). It counts hand-registered cell tests since Nov 9 only. It leaves out every generator sweep and every try before Nov 9.

| Step | N | Basis |
|---|---|---|
| V2 single-leg ledger at SWEEP1 | 5,319 | V2:`W/SWEEP1_PROTOCOL.md:8` |
| Refinement | about 900 | REF:`RT/SWEEP_EXTERNAL_SIGNAL_REGISTRATION.md:2` |
| W-SWEEP-EXT1 as first registered | 1,512 | REF:`RT/SWEEP_EXT1_PLAN.md:6` |
| V2's base | 7,731 | 5,319 + 900 + 1,512 (sum made here; V2 quotes 7,731 without a breakdown) |
| REGIME1 | + 1,064 = 8,795 | V2:`W/REGIME1_PROTOCOL.md:13` |
| ANGLES1 | + 214 = **9,009** | V2:`W/ANGLES1_PROTOCOL.md:23` |
| Same chain on Refinement's corrected base (3,240 cells, 9,459) | 10,737 | 9,459 + 1,064 + 214, sum made here |
| V2 cells registered Nov 11 to 12 and never added (rows 83, 84, 86, 87, 89, 90, 91) | + 1,434 = 12,171 | sum made here |
| Refinement cells added on other bases (222 + 240 + 6 + 1) | + 469 = about 12,640 | sum made here; overlap with "about 900" cannot be ruled out |

**Does the record support "lenient N 9,009, z 4.39"? Only as arithmetic.** 9,009 = 7,731 + 1,064 + 214 is stated, and z 4.39 is the one-sided bar at that N. But the 7,731 base uses a cell count that Refinement corrected upward by 1,728 on Nov 11, and V2's own later cell tests were charged to the 1.1 million figure and not to this one. A lenient count built from every stated cell count is about 12,600 (one-sided z about 4.47, two-sided about 4.61, computed here).

### 2c. Conflicts between files (both quotes given)

1. **Strict total.** V2:`kalshi-scalper/V2_HANDOFF_NOV12.md:3` "shared ledger about 1.1M, z bar 5.34" against R:9160 "N 1,500,505, bar z 5.400" (Nov 9, before GEN12), V2:`kalshi-scalper/V2_STATUS.md:276` "Kalshi harness about 1,500,514", MAIN:`docs/STRATEGY_LIFECYCLE.md:7` "After 1.5 million rules tried", MAIN:`CLAUDE.md:928` "a deflated z of 5.4 at N 1.5 million", and DB:`W/IDEA_DESK_B_POWER.md:7` "N about 1.1 to 1.5 million tries".
2. **GEN13 does not count GEN12.** V2:`W/GEN12_REGISTRATION.md:16` "800,000 (shared README ledger, rounded) + 300,000 = 1,100,000" against V2:`W/GEN13_REGISTRATION.md:17` "1,100,000 (800,000 shared ledger + 300,000 this sweep)". MAIN:`docs/STRATEGY_LIFECYCLE.md:176` counts both: "GEN12 and GEN13 (600,000 strategies ...)".
3. **What "the README ledger, 800,000" is.** V2:`W/REGIME1_PROTOCOL.md:13` "800,780 + 1,064 = 801,844 (README ledger)" against R:7328 "N tried for deflation 800,780 (GEN1 counted at its 400,000 maximum until it finishes)", R:7333 "N tried 211,074 (GEN1 alone, with prior work)" and R:7386 "N tried 425,330". MAIN:`CLAUDE.md:603` also says "about 425,000 (425,330 after GEN2)". The 800,780 was an interim overcount on Oct 29, not the README total on Nov 11.
4. **Lenient base.** V2:`W/REGIME1_PROTOCOL.md:13` "7,731 (V2 + Refinement ledger)" against REF:`RT/SWEEP_EXTERNAL_SIGNAL_REGISTRATION.md:13` "N tried = 5,319 + 900 + 3,240 = 9,459 ... (z 4.52 at the registered 7,947 ...)".
5. **Lenient total today.** V2: "lenient N 9,009" (V2:`kalshi-scalper/V2_HANDOFF_NOV12.md:3`, `W/POWER2_QUEUE.md:4`) against Refinement: "9,459" (REF:`RT/POWER_TABLE_NOV12.md:10`), "9,465" (REF:`RT/NO_ARM_APPROVAL_REGISTRATION.md:36`), "9469" (REF:`RT/ROW75_WXREVISE_REGISTRATION_AND_RESULT.md:27`) and "9,495" (REF:`RT/NEWS_FADE_REGISTRATION.md:56`). Neither chain holds the other desk's additions.
6. **Lenient z convention.** V2 uses one-sided: "z about 4.39" at 8,795 and 9,009. Refinement uses two-sided: "Bonferroni z 4.55" at 9,459 (REF:`RT/NO_ARM_APPROVAL_REGISTRATION.md:36` "two-sided 0.05/9,465 gives 4.553; one-sided 4.41"). The same N gives two bars depending on the desk.
7. **Refinement's own stale quotes.** REF:`RT/AUDIT_NOV11_FAILS.md:48` "the sweep corrected itself to 9,459 (z 4.55). The politics, sports and cards files still quote 7,950 to 8,190". The 9,459 figure also drops the 222 and 240 calibration cells that the 7,950 and 8,190 figures had added.
8. **Category calibration count.** REF:`kalshi-scalper/REFINE_HANDOFF.md:79` "7,731 + 216 + 74 = about 7,950" against REF:`RT/CATEGORY_CALIBRATION_REGISTRATION.md:5` "about 7,731 plus 222 = about 7,950". 216 + 74 is 290, and 7,731 + 290 is 8,021.
9. **W-SWEEP-EXT1 grid.** REF:`RT/SWEEP_EXTERNAL_SIGNAL_REGISTRATION.md:2` "6,480 cells ... about 7,380" against `RT/SWEEP_EXT1_PLAN.md:6` "14 features = 1,512 cells ... 15 features = 3,240 cells ... arithmetic slip".
10. **V2 single-leg ledger before SWEEP1.** V2:`W/CFRTI1_PROTOCOL.md:8` "N about 5,207 after this try" against V2:`W/MMSIM2_PROTOCOL.md:15` "ledger about 5,190 + 1 + 18" (5,209). MMSIM1 and MMSIM2 are not in the 5,319.
11. **TIECOND1.** V2:`W/TIECOND1_REGISTRATION.md:22` "Adds 1 test (the kill gate). Deflation N 1,100,001" against DA:`W/IDEA_DESK_A_NOV11.md:10` "CLOSED by V2, 0 tries".
12. **SWEEP1 of Nov 11.** V2:`W/SWEEP1_PROTOCOL.md:8` "112 tests" against `:12` "0 survivors of 110 tests".
13. **SINGLELEG3.** R:9154 "N 4,440 registered (printed 4,600 with the 160 prior counted again)".
14. **FUT2.** V2:`W/fut_ledger/FUT2_DEV_RESULT.txt:1` "futures ledger N = 160 (60 prior + 50)". 60 + 50 is 110.
15. **README running count is not monotone.** R:6565 "384 tries, running count about 14,930" then R:6598 "4 tries, running count about 14,544" (CRYPTO1's 384 drop out of every later figure). R:8049 "running count about 592,085" inside a run of 728,6xx entries. R:7584 "about 130 tries ... about 438,860" then R:7596 "Tries +106 (running count about 438,834)". R:6687 "about 2,000 cells + 100 shuffles ... about 17,300" then R:6695 "about 2,000 plus 200 shuffles; running count about 17,500".
16. **Older snapshots still quoted as current.** REF:`RT/FORWARD_LOGGERS_PACKET.md:32` "N tried (about 425,000, z bar about 5.2 ...)"; REF:`kalshi-scalper/REFINE_STATUS.md:2120` "the shared N across all candidates stays about 728,683"; V2:`kalshi-scalper/HANDOFF_V2.md:9` "z about 5.17 at N about 438,700"; DA:`W/IDEA_DESK_A_NOV11.md:24` "about 730,000 rules tried".

## 3. Gaps: tests clearly run with no stated N, or counts that cannot be traced

1. **MENTCOMBO1** (V2, Nov 11, FALSIFIED on development): the protocol says "plus this count" and never gives the count.
2. **GEN4 and GEN5**: N +36,417 and N +25,592 appear only in `V2_STATUS.md`. The README has no result section with an N for either; it jumps from about 439,193 to about 563,337.
3. **SCAN1** (Oct 23): "about 4,500 rules" were mined and only 11 were counted.
4. **SCALP1, SCALP2, SIZE1, SIZE2, CORR1, MM1, GEN3-F1, NEWLIST1 (Nov 3), STRADDLE1, AAASPREAD1, TNOTE1, SERIESLAG1, NFLCOMBO1, the OICORE x L1 filter read, XVENUE1, PARLAY1**: run or registered, no own N found.
5. **Unitemized spans in the README**: 8 tries between 2,553 and 2,582 beyond the listed items; about 65 tries between about 5,135 and about 5,200; 67 tries in the Oct 29 batch (row 43); about 378 in Nov 3 to Nov 5 (row 59). R:8323 says of one worker's tries "running count not totalled here (lead keeps it)".
6. **Shuffles and null draws** (HUNT1, HUNT2, UNDER1, CAL1, PERP3, THROTTLE1, GROW1, PERPFLOW1, FP3): the running count rises by cells plus shuffles in some rows and by cells only in others. No rule is written down.
7. **Refinement's "about 540 earlier" and "about 900"**: no itemized list exists for either.
8. **Refinement cells with no clear place in any total**: sports calibration 72, economics calibration 36, weather 108, cards 74 and 84, politics step 2 "about 12", W-SPOTLEAD1 16.
9. **The single-leg ledger's start**: N 600 at SINGLELEG1 is 440 cells plus 160 carried from the futures ledger; nothing says whether earlier tries were meant to be excluded for good.
10. **POLCOMBO1B**: "at most 29"; only the census ran, and the number actually spent is not stated.
11. **Idea desks**: Desk B states +27 if all 16 ran; only BALLOTNO was read. Desk A states counts for 3 of 11 cards. No desk total is written on the shared figure.
12. **No ledger file exists on any fetched ref.** Q:`RND_QUEUE.md:66` says "One file, DEFLATION_LEDGER.md on this branch (being compiled ...)". It is not on `origin/rnd-queue` or any other fetched ref.

## 4. Method notes

- Read only: `git show`, `git grep`, `git ls-tree` on fetched refs. No checkout, commit, push or network call.
- The ledger line counts were made by reading the committed `.ids.gz` blobs with `git show` and counting lines.
- z values marked "computed here" use the one-sided normal quantile at 1 minus 0.05 / N unless marked two-sided.
- Verdict words are the sources' own. "No survivor" is used where a search closed with nothing frozen and the source gives no single verdict word.
