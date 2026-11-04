# MECH1S result (run once, 2026-11-04): INTERIOR, NONROUND, PEAK_COLLAPSE all FALSIFIED

Registration `workers/MECH1S_REGISTRATION.md` (sha256 `9cfc51bba827fb8d9411520a5793bcf73091ea1be3e09e93adf4dd817e019965`, commit ea62ec0, pushed before `score`). Data `workers/MECH1S_RESULT.json`, code `src/scalper/mech1_struct.py`, tests `tests/test_mech1_struct.py` (9 pass). Cheap side only (ask 3c to 30c, asserted); no favourite-side figure computed; cached development data, no Kalshi fetch, frozen third untouched. Net per contract after fee (C = 10), taker at the ask, held; event-clustered bootstrap 95% interval; max 2 qualifying rows per event.

| mechanism / arm | part | n | events | win | price paid | net [95%] | PF |
|---|---|---|---|---|---|---|---|
| INTERIOR (treated) | D1 | 1,318 | 776 | 10.24% | 13.81c | -4.40c [-6.23, -2.52] | 0.65 |
| | D2 | 1,311 | 776 | 8.77% | 12.87c | -4.89c [-6.49, -3.17] | 0.59 |
| | TEST | 1,588 | 853 | 6.68% | 13.22c | -7.35c [-8.82, -5.83] | 0.42 |
| | ALL | 4,217 | 2,405 | 8.44% | 13.29c | **-5.66c [-6.61, -4.74]** | 0.54 |
| INTERIOR placebo (end strikes) | ALL | 1,352 | 1,061 | 3.70% | 10.56c | -7.53c [-8.58, -6.39] | 0.28 |
| NONROUND (treated) | D1 / D2 / TEST | 1,906 / 1,855 / 2,039 | | | | -5.51c / -4.55c / -6.87c | 0.55 / 0.61 / 0.46 |
| | ALL | 5,800 | 3,340 | 8.36% | 13.24c | **-5.68c [-6.54, -4.87]** | 0.54 |
| NONROUND placebo (multiples of 5c) | ALL | 2,624 | 1,826 | 7.47% | 14.06c | -7.45c [-8.52, -6.33] | 0.44 |
| PEAK_COLLAPSE (treated) | D1 / D2 / TEST | 1,204 / 1,279 / 897 | | | | -5.65c / -4.72c / -5.30c | 0.48 / 0.53 / 0.52 |
| | ALL | 3,380 | 2,135 | 6.69% | 11.19c | **-5.20c [-6.15, -4.19]** | 0.51 |
| PEAK_COLLAPSE placebo (no collapse) | ALL | 2,205 | 1,423 | 11.97% | 16.62c | -5.62c [-7.17, -3.93] | 0.62 |

## Verdicts
All three **FALSIFIED**: net negative in D1, D2 and the last-third test, intervals entirely below zero, PF 0.42 to 0.65 against 1.5. Predictions held (-4c to -7c). Observation, not a claim: each mechanism ranked the loss in the direction of its story (interior -5.7c vs end strikes -7.5c, +1.9c; non-round -5.7c vs round -7.5c, +1.8c; collapse -5.2c vs no collapse -5.6c, +0.4c, inside the noise) but the best treated arm is still about 5c under break-even, the same size as the pooled cheap side's -6.0c (CALIB1, LIQ1). Structure alone moves the loss by 0 to 2 points; it does not remove it. In INTERIOR the test third (-7.35c) is worse than D1 and D2, so even the ranking is not stable.

## Unscored rows (for later workers; no outcome of these was looked at)
PATH_FALL (score-set rows 1,472), VS_OPEN (2,109), WEEKEND (1,534), SHOULDER (882), SPREADM (817), FEE_WASTE (1,194), VOLRANK (524), OFFHOURS (217, too few), YDAY (175, too few). Definitions, placebo arms and counts are in the registration and `MECH1S_CENSUS.txt`. Given that the best-story mechanisms moved the loss by under 2 points, none of these is expected to clear the 5c gap; a later worker should score them only as one batch with the N charged (+2 each), or not at all.

## Forward plan
None. No LEAD, no forward trade, no candidate file. N +6.

## Caveats
Same sample as CALIB1 and LIQ1 (60 day window, md5 samples per series, Weather and Economics ladders dominate by count). INTERIOR and NONROUND treat 26% and 36% of the pool, so they are mild filters by construction. Rank used the census count x a judged strength, so the top 3 are the most available rows, not the most promising mechanisms. YDAY's census counted eligible rows from earlier events' winning strikes (disclosed in the registration). ID collision: the earlier MECH1 (Bitcoin tape) record is untouched.
