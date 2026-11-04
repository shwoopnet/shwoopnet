# MECH2S registration (second batch of the MECH1S structural mechanisms; 2026-11-04)

Registered BEFORE any outcome (win, loss, result, net) was joined to any treated or placebo row of any mechanism below. Cheap side only (ask 3c to 30c, hard limit 0.30 asserted in code); no favourite-side result computed or printed; no 15 minute crypto or gold candle trigger. No new Kalshi fetch; no live code, no functions/, no L1, no OICORE; no promote verb.

## Question
Do any of the seven remaining MECH1S mechanisms with enough rows pick cheap-side rows that win more than they cost after the fee? Prior: each LEAD under 3%. MECH1S scored the top 3 of the same family at -5.2c to -5.7c, intervals below zero; the pooled cheap side is about -5.5c to -6.2c (CALIB1, LIQ1), so a filter has to move the loss by 6c or more.

## Data
Exactly the MECH1S pool: `src/scalper/mech1_struct.py extract` rows (16,201 cheap rows, 3,558 events, 12,530 markets; the LIQ1 pool from USWEEP1/2/3 caches and newlist1 cut at t2; frozen third excluded). Rows file rebuilt count-checked (16,201). No new fetch. Entry taker at the ask, held to settlement, fee 7% x C x p x (1-p) rounded up, C = 10.

## Eligibility (from the MECH1S census, features only, workers/MECH1S_CENSUS.txt; capped rows, 2 per event)
Needs at least 150 eligible treated rows in each of D1, D2 and TEST:
- PATH_FALL 613 / 859 / 1,281 ; VS_OPEN 998 / 1,111 / 760 ; WEEKEND 920 / 614 / 741 ; SHOULDER 387 / 495 / 916 ; SPREADM 414 / 403 / 408 ; FEE_WASTE 612 / 582 / 984 ; VOLRANK 232 / 292 / 252. All seven qualify: **scored**.
- OFFHOURS (D2 88, test 74) and YDAY (D2 79, test 65) do NOT qualify: **not scored**, no verdict, no N charged.

## Fixed definitions (unchanged from MECH1S_REGISTRATION.md; code `mech1_struct.py` MECH table, nothing refit)
| id | treated | placebo (opposite arm) |
|---|---|---|
| PATH_FALL | ask <= 0.8 x price about an hour earlier (candle 30 to 90 min before the look nearest 60) and >= 2c lower | ask >= 1.25 x and >= 2c higher |
| VS_OPEN | >= 2 earlier candles and first quoted price >= 2 x ask | ask >= first quoted price |
| WEEKEND | look on Saturday or Sunday (US Eastern) | Tuesday to Thursday |
| SHOULDER | adjacent rungs' max price (same side) >= 0.30, >= 4 sibling quotes, numeric ladder >= 5 | adjacent rungs all <= 0.10 |
| SPREADM | spread <= 1c and ask >= 10c | spread >= 5c and ask >= 10c |
| FEE_WASTE | rounded fee minus exact fee <= 0.02c a contract | >= 0.08c |
| VOLRANK | candle volume > 0 and lowest among siblings with volume > 0 (>= 3) | the highest |

## Scoring, ONCE
Split as MECH1S: events by earliest close time; first two thirds = D1 (first half) and D2 (second half); last third = TEST. Cap 2 qualifying rows per event (md5 order). Net per contract after fee; event-clustered bootstrap 95% interval (2,000 resamples, seed 20261104) of the mean; ALL = D1 + D2 + TEST (development only). Placebo arm reported beside each, not separately counted.
**LEAD only if** net > 0 in D1 AND D2 AND TEST, the ALL event-clustered lower bound > 0, at least 150 trades in ALL and at least 30 in each part. Otherwise FALSIFIED, or NOT_ENOUGH_DATA if too few. A LEAD is not a trade; only a forward pre-registered read after 2026-11-04 could promote it, and no promote verb exists here.

## Predictions (before the join)
All seven FALSIFIED at -4c to -7c. Best guesses: SPREADM -4c to -5c (tight books, modest), SHOULDER -4c to -6c, VS_OPEN -4c to -6c, PATH_FALL -5c to -6c, WEEKEND -5c to -7c, FEE_WASTE -5c to -6c (a cost filter, moves little), VOLRANK -5c to -7c (small n, wide interval). P(any LEAD) about 8% across the seven, mostly the multiple-comparison chance on VOLRANK or SPREADM in a small sample; none would survive the z bar 5.27.

## N accounting
+2 per mechanism scored: 7 scored = **N +14**. OFFHOURS and YDAY add 0. Coordinator total before this worker about 730,425; z bar 5.27.

## Disclosure
Pool, features, cap, split and net are MECH1S's code; this worker adds only `src/scalper/mech2_struct.py` (a scorer that imports it). No outcome of any of the seven mechanisms was looked at before this file is committed; the only outcome-adjacent numbers seen are MECH1S's results for its own three mechanisms and the pooled cheap baseline.
