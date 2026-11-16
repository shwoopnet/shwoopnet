# Margin terms at 10, 25 and 50 percent of the maximum leverage (History Miner, Nov 16, 2026; version 3, ASSUMPTIONS flagged)

Max leverage: the PAGE maximum from the owner's list for BTC (15.4x), ETH (10.5x) and XRP (5.4x). For SOL, DOGE and HYPE the owner's list has none, so the API's leverage_estimate from Forensics' PERPS_FULL_CENSUS_NOV16.tsv (column leverage_api_estimate: SOL 3.0828, DOGE 2.9405, HYPE 2.2534) is used and labelled 'API estimate, page max unknown' (the Head, 20:49Z; it is the lower figure, so the conservative choice; the owner's list arriving later is a dated re-hash). ASSUMED, not read from Kalshi's articles: maintenance margin 4.5 percent of notional (gold measured 4.47 percent); fees taker 12 bps and maker 5 bps a side (round trip 24 and 10 bps of notional); funding not included. Adverse move to liquidation = margin on the notional (1 / leverage) minus 4.5 percent.

| market | max leverage | source of the max | share of max | leverage used | margin on the notional | adverse move to liquidation | taker round trip on the margin | maker round trip on the margin |
|---|---|---|---|---|---|---|---|---|
| KXBTCPERP | 15.40x | page max | 10 percent | 1.54x | 65 percent | 60.4 percent | 37 bps | 15 bps |
| KXBTCPERP | 15.40x | page max | 25 percent | 3.85x | 26 percent | 21.5 percent | 92 bps | 38 bps |
| KXBTCPERP | 15.40x | page max | 50 percent | 7.70x | 13 percent | 8.5 percent | 185 bps | 77 bps |
| KXETHPERP | 10.50x | page max | 10 percent | 1.05x | 95 percent | 90.7 percent | 25 bps | 10 bps |
| KXETHPERP | 10.50x | page max | 25 percent | 2.62x | 38 percent | 33.6 percent | 63 bps | 26 bps |
| KXETHPERP | 10.50x | page max | 50 percent | 5.25x | 19 percent | 14.5 percent | 126 bps | 52 bps |
| KXXRPPERP | 5.40x | page max | 10 percent | 0.54x | 185 percent | none on a long; 181 percent up on a short | 13 bps | 5 bps |
| KXXRPPERP | 5.40x | page max | 25 percent | 1.35x | 74 percent | 69.6 percent | 32 bps | 14 bps |
| KXXRPPERP | 5.40x | page max | 50 percent | 2.70x | 37 percent | 32.5 percent | 65 bps | 27 bps |
| KXSOLPERP | 3.08x | API estimate, page max unknown | 10 percent | 0.31x | 324 percent | none on a long; 320 percent up on a short | 7 bps | 3 bps |
| KXSOLPERP | 3.08x | API estimate, page max unknown | 25 percent | 0.77x | 130 percent | none on a long; 125 percent up on a short | 18 bps | 8 bps |
| KXSOLPERP | 3.08x | API estimate, page max unknown | 50 percent | 1.54x | 65 percent | 60.4 percent | 37 bps | 15 bps |
| KXDOGEPERP | 2.94x | API estimate, page max unknown | 10 percent | 0.29x | 340 percent | none on a long; 336 percent up on a short | 7 bps | 3 bps |
| KXDOGEPERP | 2.94x | API estimate, page max unknown | 25 percent | 0.74x | 136 percent | none on a long; 132 percent up on a short | 18 bps | 7 bps |
| KXDOGEPERP | 2.94x | API estimate, page max unknown | 50 percent | 1.47x | 68 percent | 63.5 percent | 35 bps | 15 bps |
| KXHYPEPERP | 2.25x | API estimate, page max unknown | 10 percent | 0.23x | 444 percent | none on a long; 439 percent up on a short | 5 bps | 2 bps |
| KXHYPEPERP | 2.25x | API estimate, page max unknown | 25 percent | 0.56x | 178 percent | none on a long; 173 percent up on a short | 14 bps | 6 bps |
| KXHYPEPERP | 2.25x | API estimate, page max unknown | 50 percent | 1.13x | 89 percent | 84.3 percent | 27 bps | 11 bps |

## What changed from version 2 (hash 114a1de9)
- SOL, DOGE and HYPE are added on the API estimate (labelled), as the Head ruled; the BTC, ETH and XRP rows are unchanged.
