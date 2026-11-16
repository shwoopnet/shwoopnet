# Margin terms at 10, 25 and 50 percent of the page maximum leverage (History Miner, Nov 16, 2026; version 2, ASSUMPTIONS flagged)

Max leverage = the PAGE maximum from the owner's pasted list (Forensics' PERPS_FULL_CENSUS_NOV16.tsv column page_max_owner_pasted: BTC 15.4x, ETH 10.5x; XRP 5.4x as the Head wrote it, the TSV cell is blank). SOL, DOGE and HYPE are NOT in this table: their page-max cell in the TSV is blank, so I will not guess them; they need the value. ASSUMED, not read from Kalshi's articles: maintenance margin 4.5 percent of notional (gold measured 4.47 percent, the Head); fees taker 12 bps and maker 5 bps a side (round trip 24 and 10 bps of notional); funding not included. Adverse move to liquidation = margin on the notional (1 / leverage) minus the 4.5 percent maintenance margin.

| market | page max leverage | share of max | leverage used | margin on the notional | adverse move to liquidation | taker round trip on the margin | maker round trip on the margin |
|---|---|---|---|---|---|---|---|
| KXBTCPERP | 15.4x | 10 percent | 1.54x | 65 percent | 60.4 percent | 37 bps | 15 bps |
| KXBTCPERP | 15.4x | 25 percent | 3.85x | 26 percent | 21.5 percent | 92 bps | 38 bps |
| KXBTCPERP | 15.4x | 50 percent | 7.70x | 13 percent | 8.5 percent | 185 bps | 77 bps |
| KXETHPERP | 10.5x | 10 percent | 1.05x | 95 percent | 90.7 percent | 25 bps | 10 bps |
| KXETHPERP | 10.5x | 25 percent | 2.62x | 38 percent | 33.6 percent | 63 bps | 26 bps |
| KXETHPERP | 10.5x | 50 percent | 5.25x | 19 percent | 14.5 percent | 126 bps | 52 bps |
| KXXRPPERP | 5.4x | 10 percent | 0.54x | 185 percent | none on a long; 181 percent up on a short | 13 bps | 5 bps |
| KXXRPPERP | 5.4x | 25 percent | 1.35x | 74 percent | 69.6 percent | 32 bps | 14 bps |
| KXXRPPERP | 5.4x | 50 percent | 2.70x | 37 percent | 32.5 percent | 65 bps | 27 bps |

## What changed from version 1 (hash 0ab80ba2)
- Max leverage: the API's leverage_estimate (BTC 6.4x, ETH 4.4x, XRP 2.9x) is replaced by the page maximum (15.4x, 10.5x, 5.4x). The API estimate stays in the TSV as `leverage_api_estimate`, with size-specific figures at 1,000 and 1,000,000 dollars of notional (BTC long 6.8x and 6.2x at those sizes), so it is a different quantity from the page maximum.
- Maintenance margin: 4.5 percent of notional (assumed, gold measured 4.47 percent) replaces half of the initial margin, so the adverse move to liquidation is smaller at every share of the maximum.
- SOL, DOGE and HYPE are dropped from this table until their page maximum is supplied.
