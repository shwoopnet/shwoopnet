# SPXSCALP: expected figures on a made-up fixture, written BEFORE the scorer

MADE-UP numbers (not Databento, not Kalshi). Two windows, one entry each. Arms covered here: B25 HEADLINE and B25 HOLD at 1c and 2c. NOT covered yet (a second expected file will be committed before the scorer): the half-at-2x arm, the B30 band, a window with no two-sided exit, missing ES bars, and the rule 18 cases. Fees: 7% x p x (1-p) per order, rounded UP to the cent, on 1 contract. Minutes are candle ends O+60m, m = 1..15; close = O + 15 min; looks m = 1..5; time exit candle m = 10. Threshold = 0.0005 x ES(O) = 3.5 points on ES(O) = 7000.

## Window A (closes first)
ES close by m: m1 7002 (move +2, under threshold), m2 7005 (+5, YES favoured). YES ask close at m2 0.22 (in band). YES bid closes after entry: m3 .30, m4 .40, m5 .47, m6 .50. Result: yes.
- 1c: fill 0.23, target 0.46, first bid >= 0.46 is m5 (.47), exit at .47 - .01 = 0.46. Entry fee .02, exit fee .02. Net 0.19.
- 2c: fill 0.24, target 0.48, first bid >= 0.48 is m6 (.50), exit at .50 - .02 = 0.48. Fees .02 and .02. Net 0.20.
- HOLD (settles yes): 1c 1 - .23 - .02 = 0.75; 2c 1 - .24 - .02 = 0.74.

## Window B
ES m1 6990 (move -10, NO favoured). YES bid close at m1 0.80, so NO ask = 1 - 0.80 = 0.20 (in band, inclusive). NO bid = 1 - YES ask; YES ask at m10 = 0.85, so NO bid .15; no earlier bid reaches the 2x target. Result: yes (the NO side loses).
- 1c: fill 0.21, time exit at m10: .15 - .01 = 0.14. Fees .02 and .01. Net -0.10.
- 2c: fill 0.22, exit .15 - .02 = 0.13. Fees .02 and .01. Net -0.12.
- HOLD: 1c -.21 - .02 = -0.23; 2c -.22 - .02 = -0.24.

## Aggregates (n = 2; entries under 100 so the label is FALSIFIED by precedence, with --min-entries lowered the figures below hold)
| arm | read | entries | net sum | gross wins | gross losses | PF | half 1 (A) PF | half 2 (B) PF |
|---|---|---|---|---|---|---|---|---|
| B25 HEADLINE | 1c | 2 | 0.09 | 0.19 | 0.10 | 1.9000 | no losses | 0.0000 |
| B25 HEADLINE | 2c | 2 | 0.08 | 0.20 | 0.12 | 1.6667 | no losses | 0.0000 |
| B25 HOLD | 1c | 2 | 0.52 | 0.75 | 0.23 | 3.2609 | no losses | 0.0000 |
| B25 HOLD | 2c | 2 | 0.50 | 0.74 | 0.24 | 3.0833 | no losses | 0.0000 |
Halves = the first floor(2/2) = 1 entry by close time (A) and the rest (B). Verdict for every arm above: FALSIFIED (a half PF under 1.0 at 1c, and also fewer than 100 entries), "upper bound, not fill-checked". Tolerance 0.0001 on PF and 0.001 on sums.
