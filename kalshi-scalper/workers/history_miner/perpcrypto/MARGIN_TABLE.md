# Margin terms at 10, 25 and 50 percent of the maximum leverage (History Miner, Nov 16, 2026; ASSUMPTIONS flagged)

Max leverage is Kalshi's `leverage_estimate` (one over the margin rate) from perps-lev-2026-11-16.csv at 20:00Z, the latest print, one value per market (the file does not say it is size specific: it moves by about 0.1 percent an hour; if Kalshi's margin article gives tiers by size, the table is redone). ASSUMED, not read from Kalshi's articles: maintenance margin is half of the initial margin; fees taker 12 bps and maker 5 bps a side (round trip 24 and 10 bps of notional); funding not included. Adverse move to liquidation = margin on the notional minus maintenance margin. Where leverage is under 1x the position is fully funded and a long cannot be liquidated.

| market | max leverage | share of max | leverage used | margin on the notional | adverse move to liquidation | taker round trip on the margin | maker round trip on the margin |
|---|---|---|---|---|---|---|---|
| KXBTCPERP | 6.38x | 10 percent | 0.64x | 157 percent | none on a long; 149 percent up on a short | 15 bps | 6 bps |
| KXBTCPERP | 6.38x | 25 percent | 1.59x | 63 percent | 54.9 percent | 38 bps | 16 bps |
| KXBTCPERP | 6.38x | 50 percent | 3.19x | 31 percent | 23.5 percent | 77 bps | 32 bps |
| KXETHPERP | 4.37x | 10 percent | 0.44x | 229 percent | none on a long; 217 percent up on a short | 10 bps | 4 bps |
| KXETHPERP | 4.37x | 25 percent | 1.09x | 92 percent | 80.1 percent | 26 bps | 11 bps |
| KXETHPERP | 4.37x | 50 percent | 2.19x | 46 percent | 34.3 percent | 52 bps | 22 bps |
| KXSOLPERP | 3.08x | 10 percent | 0.31x | 324 percent | none on a long; 308 percent up on a short | 7 bps | 3 bps |
| KXSOLPERP | 3.08x | 25 percent | 0.77x | 130 percent | none on a long; 113 percent up on a short | 19 bps | 8 bps |
| KXSOLPERP | 3.08x | 50 percent | 1.54x | 65 percent | 48.6 percent | 37 bps | 15 bps |
| KXDOGEPERP | 2.95x | 10 percent | 0.29x | 339 percent | none on a long; 322 percent up on a short | 7 bps | 3 bps |
| KXDOGEPERP | 2.95x | 25 percent | 0.74x | 136 percent | none on a long; 119 percent up on a short | 18 bps | 7 bps |
| KXDOGEPERP | 2.95x | 50 percent | 1.47x | 68 percent | 50.9 percent | 35 bps | 15 bps |
| KXXRPPERP | 2.88x | 10 percent | 0.29x | 347 percent | none on a long; 330 percent up on a short | 7 bps | 3 bps |
| KXXRPPERP | 2.88x | 25 percent | 0.72x | 139 percent | none on a long; 121 percent up on a short | 17 bps | 7 bps |
| KXXRPPERP | 2.88x | 50 percent | 1.44x | 69 percent | 52.1 percent | 35 bps | 14 bps |
| KXHYPEPERP | 2.31x | 10 percent | 0.23x | 433 percent | none on a long; 412 percent up on a short | 6 bps | 2 bps |
| KXHYPEPERP | 2.31x | 25 percent | 0.58x | 173 percent | none on a long; 152 percent up on a short | 14 bps | 6 bps |
| KXHYPEPERP | 2.31x | 50 percent | 1.15x | 87 percent | 65.0 percent | 28 bps | 12 bps |
