# SPXSCALP: expected figures, fixture 2 (all arms, both bands, rule 18, missing ES bar), written BEFORE the scorer

MADE-UP numbers (not Databento, not Kalshi). Cards at 6d35a82b (SPXSCALP Amendments 1 to 5). Supersedes `EXPECTED_SPXSCALP_fixture.md` (which covered B25 HEADLINE and HOLD on windows A and B only; A and B below are the same windows with the extra minutes the half arm needs). Fees 7% x p x (1-p) per order, rounded UP to the cent; the half arm enters as ONE order of 2 contracts (fee on 2) and exits as two orders of 1. ES(O) = 7000, threshold 3.5 points. Minutes m = candle ends O+60m. Looks m = 1..5; time exit m = 10. YES ask = YES bid + 0.02 unless stated. NO ask = 1 - YES bid; NO bid = 1 - YES ask. Window closes (UTC): A 15:00, B 15:15, C 15:30, D 15:45, E 16:00 on 2026-11-06 (halves = first floor(5/2) = 2 entries by close, A and B, then C, D, E).

## Windows (only listed minutes exist; a missing minute has no candle)
- A: ES m1 7002, m2 7005. YES m2 bid .20 ask .22; m3 .30; m4 .40; m5 .47; m6 .50; m10 .45 (ask .47). Result yes.
- B: ES m1 6990. YES m1 bid .80 ask .82; m10 bid .83 ask .85. Result yes (the NO side loses).
- C: ES m1 7000, m2 7005, m3 7005. YES m2 bid .26 ask .28; m3 bid .22 ask .24; m4 .35; m5 .52; m6 .60; m7 .70; m8 .82. Result yes. (B25 skips m2, ask .28 is outside .20 to .25, and enters at m3; B30 enters at m2.)
- D: ES m1 7006. YES m1 bid .21 ask .23; m2 .30 (ask .32); m9 .30 (ask .32); m10 bid .30 ask .30 (locked, not two-sided); m11 bid .28 ask .31. Result no. Time exit moves to m11 (rule 18).
- E: ES m1 MISSING (look skipped, counted), m2 7006. YES m2 bid .20 ask .22; m3 .60 (ask .62); m4 .85 (ask .87). Result yes.

## Per-window net per contract-entry (1c, 2c), cash, after per-order fees
| window | HEADLINE | HALF2X (2 contracts) | HOLD |
|---|---|---|---|
| A (both bands) | .19, .20 | .37, .36 | .75, .74 |
| B (both bands) | -.10, -.12 | -.19, -.23 | -.23, -.24 |
| C, B25 (enters m3, ask .24) | .22, .20 | .75, .71 | .73, .72 |
| C, B30 (enters m2, ask .28) | .26, .24 | .75, .71 | .69, .68 |
| D (both bands) | -.01, -.03 | -.01, -.05 | -.26, -.27 |
| E (both bands) | .32, .30 | .91, .87 | .75, .74 |
Check of one cell by hand (C, B25, 1c, HEADLINE): fill .24+.01 = .25, target .50, first bid >= .50 after m3 is m5 (.52), exit .52-.01 = .51; fees .02 and .02; net .51-.25-.04 = .22. HALF2X same cell: contract 1 .51-.25-.02 = .24; contract 2 sold at m8 (.82 >= .80), .81-.25-.02 = .54; entry fee on 2 contracts .03; total .78-.03 = .75. HOLD: 1-.25-.02 = .73.

## Aggregates (n = 5 per arm; entries under 100, so every label is FALSIFIED by precedence; counts below hold with --min-entries lowered to 5)
| arm | read | n | net sum | PF | half 1 PF (A,B) | half 2 PF (C,D,E) |
|---|---|---|---|---|---|---|
| B25 HEADLINE | 1c | 5 | 0.62 | 6.6364 | 1.9000 | 54.0000 |
| B25 HEADLINE | 2c | 5 | 0.55 | 4.6667 | 1.6667 | 16.6667 |
| B25 HALF2X | 1c | 5 | 1.83 | 10.1500 | 1.9474 | 166.0000 |
| B25 HALF2X | 2c | 5 | 1.66 | 6.9286 | 1.5652 | 31.6000 |
| B25 HOLD | 1c | 5 | 1.74 | 4.5510 | 3.2609 | 5.6923 |
| B25 HOLD | 2c | 5 | 1.69 | 4.3137 | 3.0833 | 5.4074 |
| B30 HEADLINE | 1c | 5 | 0.66 | 7.0000 | 1.9000 | 58.0000 |
| B30 HEADLINE | 2c | 5 | 0.59 | 4.9333 | 1.6667 | 18.0000 |
| B30 HALF2X | 1c | 5 | 1.83 | 10.1500 | 1.9474 | 166.0000 |
| B30 HALF2X | 2c | 5 | 1.66 | 6.9286 | 1.5652 | 31.6000 |
| B30 HOLD | 1c | 5 | 1.70 | 4.4694 | 3.2609 | 5.5385 |
| B30 HOLD | 2c | 5 | 1.65 | 4.2353 | 3.0833 | 5.2593 |
Drops (per band scan): look_es_missing = 1 (window E, look m1); exit candle not two-sided = 1 entry (window D, moved to m11, so no entry dropped); no window dropped. Verdict for every arm with --min-entries 5: all halves and PFs are at or above the 1.0 line and PF >= 1.3 at 1c and 2c PF >= 1.0, so the label is "counts" on this fixture (an artefact of made-up data), "upper bound, not fill-checked". Tolerance 0.0001 on PF, 0.001 on sums.
