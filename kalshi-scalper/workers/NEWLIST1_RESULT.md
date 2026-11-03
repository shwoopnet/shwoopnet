# NEWLIST1 result (scored ONCE, 2026-11-03 23:04 UTC; registration fface1c, Amendment 1 f26dd24, Amendment 2 in 30b the same day)

Verdict: FALSIFIED for the cheap side (Try A). New listings are NOT cheaper than the same families later in life: the cheap side wins LESS than its price at every look, in both development windows. N +4 (as registered; the favourite Try B is dropped, see Disclosure).

Sample: stratified md5-rank prefix of 1,370 markets (10 per family, 137 families, rank 0..9 complete), looks at 1, 3 and 6 hours of life and the late control (3 hours before the close). Frozen third H unread (counts only). Cheap side = ask 5c to 30c, taker at the ask, hard limit 0.30, held to settlement, fee 7% x C x p x (1-p) rounded up, C=10.

ALL families pooled, Try A (win rate vs price paid, PF), D = development, V = validation:
| look | D n | D win vs price | D PF | V n | V win vs price | V PF |
|---|---|---|---|---|---|---|
| 1 h | 344 | 9.0% vs 15.7c | 0.48 | 225 | 8.4% vs 15.6c | 0.45 |
| 3 h | 310 | 11.0% vs 14.8c | 0.64 | 289 | 9.0% vs 14.6c | 0.52 |
| 6 h | 297 | 10.4% vs 14.9c | 0.60 | 303 | 6.9% vs 15.8c | 0.36 |
| late control | 106 | 9.4% vs 14.8c | 0.55 | 155 | 3.2% vs 15.2c | 0.16 |
Per family: 131 families with cells; NONE has n >= 20 and PF > 1 in both D and V at any look. Early minus late gap (the registered claim) is not positive in both windows. Kill rule hit (PF under 1.5 in D and V at every look). Prediction held (gap -1 to -3 points, PF 0.70-0.95): the actual PF is lower (0.36-0.64).

## Disclosure
1. The first `score` run crashed on a sort bug (keys mixed ints and the string 'late') before writing any output or the run-once file; the fix is the sort key only (`sorted(set(rows), key=lambda k: (k[0], str(k[1])))`), no rule, band, look or threshold changed; the second run wrote data/newlist1_score.json.
2. NEWLIST1's registration included Try B (favourite 85c-97c, held). The owner's strict ruling of 2026-11-03 (no buy-the-favourite-and-hold research on any underlying) came after NEWLIST1 was registered and the coordinator did not amend Try B out of the scorer, so the scorer computed it and the coordinator printed the pooled B cells once while checking the output (all negative: PF 0.06-0.41, win 48-86% vs 92-94c paid). Try B is not reported, not used, and is withdrawn here; the counted N for it (+2) stays charged. The frozen third H was not read.
