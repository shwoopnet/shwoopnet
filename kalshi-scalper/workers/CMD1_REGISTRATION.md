# CMD1 registration: perp versus futures at one minute, who leads and does the basis revert (2026-11-06, before any score)

Shared rules, data, convention, cut, costs and bars: `workers/CMD_COMMON.md`. 6 tries (N +6).

**Mechanism.** The perp copies the CME futures through a few makers. If the perp lags the futures by one or more minutes, a one minute futures move not yet in the perp mid is information and a basis spike should revert. Counterparty: the slower perp maker or resting perp liquidity.

**Information (no try): lag profile.** Pearson correlation of one minute log returns of perp mid and futures at lags -3..+3 minutes per pair (D1 and D2), plus ^GSPC and ^NDX versus the perp in cash hours (09:30 to 16:00 ET) only. LEAD statistic: corr(fut return at T-1, perp return at T) minus corr(perp return at T-1, fut return at T) at least 0.03 in at least 4 of 6 pairs in both halves.

**Rule R1, basis reversion.** At each minute T (scanning in order, at most one open position per pair): d_T at least +10 bp (perp rich) sell the perp, d_T at most -10 bp buy it; exit at T+H, H = 5, 15 and 30 minutes (three tries, **primary H = 15**). Next entry only after exit. Skip if |d_T| is above 100 bp (a bad pair, counted).

**Rule R2, follow the futures.** Futures one minute log return at T (bar T-60 to T) with |return| at least 5 bp and the perp mid change over the same minute less than 50 percent of the futures change, same sign: trade the perp in the futures' direction at T, exit at T+H, H = 1, 5, 15 (three tries, **primary H = 5**).

**Numeric prediction (written before running).** Lag 0 correlation at least 0.5 for all six pairs; futures lead by the statistic in at least 4 of 6; R1 primary gross (after the recorded spread, before fee) +0 to +4 bp a trade, break-even fee 0 to 2 bp a side, net at 12 bp about -22 to -26 bp; R2 primary gross +0 to +3 bp, net about -22 to -25 bp. Expect fewer than 60 trades and 3 clusters: NOT_ENOUGH_DATA. A positive net at 12 bp is not expected.

**Kill / verdict:** as in the shared file (LEAD, FALSIFIED, NOT_ENOUGH_DATA). The pooled primary R1 (H=15) and R2 (H=5) carry the verdict; other holds are information.
