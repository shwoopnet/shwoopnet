# COMBO1 census (Nov 11, 2026; GET /markets on api.elections.kalshi.com, spacing 2 s then 4 s then 10 s; 429 hit repeatedly, shared budget, stopped each time, no workaround)
| collection series | settled | open | legs | notes |
|---|---|---|---|---|
| KXMVENBASINGLEGAME | 569 (live /markets) | 0 | 553 two-leg, 16 three-leg | close 2026-10-05 to 2026-10-08 only (3 days); older NOT read (/historical/markets unread); no entry quotes kept (settled quotes 0/1), only last price and volume |
| KXMVENFLSINGLEGAME | 0 | 0 | | |
| KXMVENBAMULTIGAMEEXTENDED | 0 | 0 | | |
| KXMVENFLMULTIGAMEEXTENDED | 0 | 0 | | |
| KXMVESPORTSMULTIGAMEEXTENDED | 0 | 37 stale (closes Aug 9 to 23, no result) | 2:7, 3:8, 4:11, 5:4, 6+:7 | |
| KXMVEMENTIONSSINGLE, weather MVE, KXMVECROSSCATEGORY | NOT READ (429) | NOT READ | | |
Median spread and volume on combo markets: not computed (open combos with a real quote: none seen in the read series). Raw rows: not committed (scratch).
Verdict so far: NOT_ENOUGH_DATA. Only NBA same-game combos have any settled history on the live endpoint (569, 3 days), and a settled combo has no entry quote, so pricing needs per-combo candlestick reads (about 1 + legs each) that the request budget has not allowed. Data would suffice for the n >= 100 gate per rule once candles for about 300 NBA combos are read (about 900 reads), the earliest next try after the 429 window clears. No PF computed, no outcome rule read.
