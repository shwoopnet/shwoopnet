# DEC 9 income checkpoint page (2026-11-10, data to 18:59Z; registration in REGISTRATION.md, script calc.py)
Basis: cash, recomputed from avgFill/avgFee, live strategies only (gold L1, OICORE, EVENT830, XRPYES10). Days are US Central.

| Window | n | Cash net | Per week | Blended PF | Bootstrap by day, weekly 5th/50th/95th |
|---|---|---|---|---|---|
| last 14 d | 249 | +$44.23 | +$22.1 | 1.20 | -$23.6 / +$24.7 / +$74.3 (81% of draws positive) |
| last 28 d | 358 | +$61.97 | +$15.5 | 1.24 | -$10.3 / +$14.4 / +$41.1 (83% positive) |
| last 7 d | 142 | -$16.2 | -$16.2 | below 1 | not bootstrapped |

By strategy, 14 d: gold +$19.11 (157 orders, PF 1.14, about 15 contracts, +0.83c per contract, now 17 a order); OICORE +$26.15 (81, PF 1.30, +3.11c per contract, 14 wins of 81, now back at 10 contracts); EVENT830 -$1.30 (10 orders, 0 wins, since Nov 5); XRPYES10 +$0.26 (1 order, Nov 10). The last two are not readable. Last 7 days: gold -$13.36, OICORE -$1.76, so the 14 day figure leans on the week of Oct 27 to Nov 2.

Monthly now: about $96 (14 d) or $67 (28 d), range about -$100 to +$320 a month (14 d, 90%).

Need (blended per contract edge 1.40c on 14 d, 1.56c on 28 d; about 1,580 contracts a week on 14 d):
- $2,000 a month (about $460 a week): 21x the current size on 14 d, 30x on 28 d.
- $5,000: 52x / 74x. $10,000: 104x / 148x.
- By PF instead, at today's size and orders: weekly gross loss is about $110 (14 d) so $460 net needs PF 5.2 (28 d: loss $64, PF 8.2). Nothing in the record is near that; the research bar is 1.5.

Account and caps (base $979.25):
- Cap on one order is 1% ($9.79) and a window or a day 2% ($19.59). The 12% stop is $117.51 and the L1 window cap $53.86. A gold loss at 17 contracts is about $15 to $16, a full OICORE loss at 10 contracts is $5 to $6 (stop 5 x contracts, max 12% of base).
- Everything scales with the base. To hold the same risk shape at 21x to 30x the size you would need a base of about $20k to $29k for $2,000 a month, $51k to $72k for $5,000, $100k to $145k for $10,000. That is arithmetic on today's edge, not a plan or a forecast.
- The code stops well short: L1 order ceiling 50 contracts (gold is at 17, so at most about 3x), OICORE ladder tops at 30 contracts (3x from 10) and needs base $1,350, slot dollar ceilings $20 an order and $40 a window. Even at every ceiling the 14 d rate is about $65 a week, roughly $280 a month, if the edge held at the larger size (book depth at the touch is also unchecked above about 20 contracts).

Honest gap: today is about $70 to $100 a month with a confidence range that includes a loss; $2,000 a month needs 20x to 30x the size or an edge nobody has measured. The last 7 days were negative. Size is not the lever until PF is well above 1.2 with a named counterparty; neither strategy here is at the research bar (OICORE PF 1.30 on 81 orders is the only one with real volume, 14 wins).
