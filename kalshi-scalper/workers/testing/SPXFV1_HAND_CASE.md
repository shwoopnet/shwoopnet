# SPXFV1 hand case (Testing Desk, Nov 13, 2026): written and committed BEFORE the code is re-frozen on the Head's rulings (16:47Z and 16:49Z)
MADE-UP numbers, worked by hand; `test_spxfv1.py` must reproduce every figure. Nothing here comes from any landed file.

## Rulings in force (printed as constants in every run header)
- GOVERNING fee: 0.07 x C x p x (1 - p), C = 1, rounded UP to the cent per order. Every bar, label, z and kill flag reads this. The unrounded figure prints only as information, labelled so.
- sd: from consecutive one-minute bar pairs, both present AND on F_now's instrument id; at least 6 of the 10; sample (n - 1) sd; times sqrt(119/60).
- Quote: the decision candle's yes_bid and yes_ask closes. Crossed or locked (yes_bid + no_bid >= 1 - 1e-9, no_bid = 1 - yes_ask) is no quote, counted.
- Cheaper side: lower ask, tie to YES; ties are counted (zero expected on the band).
- Thirds: three equal time spans from 2026-12-01T00:00Z to the last traded close at or before READ_DATE (held-out). In development (nothing reaches Dec 1): equal time spans from the first to the last traded CLOSE.
- A void is a fee-only loss. An empty result stops the run. Every comparison carries 1e-9.

## Model arithmetic
a = 0.0005 alternating log changes: sd_1m = a x sqrt(10/9) = 0.00052705; sd = sd_1m x sqrt(119/60) = 0.00074224. z = +1: Phi(1) = 0.841345; z = -1: 0.158655.

## Windows (all closes 2026-11-05 unless stated)
| id | close | z | yes bid / ask | result | outcome |
|---|---|---|---|---|---|
| W1 | 15:00 | +1 | .90 / .91 | no | NO ask .10 (YES ask .91), chance(NO) .158655, edge .0587: TRADE NO, wins. fee .07 x .1 x .9 = .0063 -> 1c. net = 1 - .10 - .01 = **+0.89** |
| W2 | 15:15 | -1 | .09 / .10 | no | YES ask .10, chance .158655, edge .0587: TRADE YES, loses. net = -.10 - .01 = **-0.11** |
| W3 | 15:30 | +1 | .90 / .91 | void | as W1; void: price refunded, fee kept: net **-0.01** |
| W4 | 15:45 | +.5 | .70 / .71 | yes | NO ask .30, chance .3085, edge .0085: no trade (edge under 5c) |
| W5 | 16:00 | +1 | .90 / .91 | no | no F_open bar: dropped |
| W6 | 16:15 | +1 | .90 / .91 | no | F_open on another instrument id: roll, dropped |
| W7 | 16:30 | +1 | .90 / .91 | no | no decision candle: dropped |
| W8 | 16:45 | +1 | .90 / .94 | no | YES spread 4c: no trade |
| W9 | 17:00 | +1 | .49 / .51 | yes | YES ask .51 = NO ask .51: a TIE (counted, goes to YES), ask outside 0.05 to 0.30: no trade |
| W10 | 17:15 | +1 | .91 / .90 | no | crossed (bid above ask): no quote, counted |
| W11 | 2026-12-01 15:00 | +1 | .90 / .91 | no | closes on the held-out start: never opened in dev |
| X1 | other series | | | | ignored entirely |
| W12 | 17:30 | +1 | .90 / .91 | (empty) | empty result: the run STOPS |

## Expected (W1 to W3 traded; W12 run separately)
- traded 3, void 1, ties 1, crossed 1, edge-under-5c 1, spread 1, no F_open 1, roll 1, no decision candle 1, not-in-range-not-read 1, windows listed 11 (X1 not counted).
- GOVERNING (rounded fee): net +0.77, mean +0.25667, PF .89 / .12 = 7.417, win rate 1/3, mean price .10.
- INFORMATION ONLY (unrounded fee): net +0.7811, PF 7.937.
- Thirds in development: first traded close 15:00, last 15:30 (the 2 and 3 are on the 15:15 and 15:30 closes): equal spans of 10 minutes each: W1 in third 1, W2 in third 2, W3 in third 3.
- Label: no evidence at n = 3.

CLOSED UNREAD 2026-11-13, family declined; no value opened
