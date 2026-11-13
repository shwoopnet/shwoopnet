# ENDNET second build, AMENDED rulings (Head, 15:32Z; Desk B's amendment in cards file e917a3cb): my hand-worked expected output, written BEFORE the scorer is edited or run again. Invented rows. Cents per contract.
Changes from EXPECTED_hand.md (all provisional lines): stage 1 kill reads the median ask over EVERY state with a strike and a two-sided quote before the filters; the mean over the 4-week window decides the weekly test; US Central dates and Monday to Sunday Central weeks; two matching strikes = none taken ("ambiguous strike"); fee per ORDER of 10 contracts rounded up to the cent, divided by 10 (cents per contract = ceil(7 p (100 - p) / 1000) / 10); void = fee-only loss counted; a missing or null result = unsettled, excluded, counted, flagged; halves by the date constant 2026-12-01T00:00Z, a half fails only below 1.0; z day-clustered by Central game day, one-sided, equal-weight clusters (mean of cluster means over stdev / sqrt k), bar 5.46.
## Main set (dev.json, 14 games), decisions unchanged from EXPECTED_hand.md; money lines change by the new fee:
| game | price | fee per contract | result | net |
|---|---|---|---|---|
| G01 | 35 | ceil(15.925) = 16 per 10 -> 1.6 | yes | +63.4 |
| G02 | 21 | ceil(11.613) = 12 -> 1.2 | no | -22.2 |
| G07 | 16 | ceil(9.408) = 10 -> 1.0 | yes | +83.0 |
| G08 | 46 | ceil(17.388) = 18 -> 1.8 | no | -47.8 |
| G12 | 29 | ceil(14.413) = 15 -> 1.5 | void | -1.5 (fee kept) |
| G14 | 30 | ceil(14.7) = 15 -> 1.5 | yes | +68.5 |
- COUNTS: games 14 (outside 0); states 12; entries 6; not entered 6 (no usable quote 2, one-sided 1, ask above the band 1, spread above 4c 1, no strike 1).
- Median ask, stage 1 KILL: over every state with a strike and a two-sided quote (G01 34, G02 20, G06 46, G07 15, G08 45, G09 35, G12 28, G14 29): 31.5c. Information: over the 6 entries 28.5c.
- Entries by US Central close date: Nov 17: 2 (G01, G02), Nov 18: 1 (G07), Nov 21: 1 (G08), Nov 23: 1 (G12), Nov 25: 1 (G14). By Central week (Monday): week of Nov 16: 4, week of Nov 23: 2.
- Week tests: mean over the 4 weeks of the development window 6 / 4 = 1.5 under 6 (DECIDES); every week under 6 (information) true; mean over the weeks with entries 3.0 under 6 (information) true.
- STAGE 1 VERDICT: CLOSED: fewer than 6 qualifying entries a week (the median ask 31.5 is not above 45).
- STAGE 2: n = 6 settled (the void counts), unsettled 0; nets 63.4, -22.2, 83.0, -47.8, -1.5, 68.5: sum +143.4, +23.9c a contract; gains 214.9, losses 71.5, cash PF 3.0056. Halves by the date constant: every game closes before 2026-12-01, so the first half is all 6 (PF 3.0056) and the second half is empty (no entries; it cannot fail).
- z (information, one-sided, day-clustered, Central days): cluster means 20.6 (Nov 17: 63.4 and -22.2), 83.0, -47.8, -1.5, 68.5: mean 24.56, stdev 53.096, se 23.746, z = 1.03 against the bar 5.46.
- STAGE 2 VERDICT: NOT_ENOUGH_DATA at n = 6.
## Amended set (amend_extra.json, 5 games)
| game | what | decision |
|---|---|---|
| X01 | standard 30/34 pay 35 fee 1.6, result null, closes Nov 19 03:30Z = Nov 18 Central | ENTERED, counted, UNSETTLED (excluded from n and PF), flagged |
| X03 | strikes 5.0 and 5.5 both within one goal | state, NOT entered: ambiguous strike |
| X04 | closes Mon Nov 23 05:30Z = Sun Nov 22 Central (week of Nov 16 Central); bid 26 ask 30, pay 31, fee ceil(14.973) = 15 -> 1.5; yes | ENTER, net +67.5 |
| X05 | closes Tue Nov 17 05:30Z = Mon Nov 16 Central; bid 20 ask 22, pay 23, fee ceil(12.397) = 13 -> 1.3; no | ENTER, net -24.3 |
| X06 | closes 2026-11-16T23:00Z, before the development window | outside, counted, not used |
- COUNTS: games 4 in the window, outside 1; states 4; entries 3 (X01, X04, X05); not entered 1 (ambiguous strike 1). Median ask over quoted states with a strike (X01 34, X04 30, X05 22): 30.0c; over entries 30.0c. Entries by Central date: Nov 16: 1 (X05), Nov 18: 1 (X01), Nov 22: 1 (X04); week of Nov 16 Central: 3. Mean over the 4 weeks 0.75 under 6: STAGE 1 CLOSED on the week line.
- STAGE 2: settled n = 2 (X04, X05), unsettled 1 (X01) flagged; nets +67.5, -24.3: sum +43.2, +21.6c a contract, cash PF 67.5 / 24.3 = 2.7778; first half both, second half empty; z: cluster means 67.5, -24.3: mean 21.6, stdev 64.91, se 45.9, z = 0.47. NOT_ENOUGH_DATA at n = 2.
## Held-out: outside.json (a game closing 2026-12-16) still REFUSES the whole run.
