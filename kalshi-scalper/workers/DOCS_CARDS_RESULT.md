# DOCS_CARDS_RESULT (2026-11-11): REBATE1, FEEROUND1, RULES1. Docs reading and cost arithmetic; 0 strategies scored, N unchanged.

Fetch notes: kalshi.com/docs/kalshi-fee-schedule.pdf and kalshi.com/fee-schedule returned HTTP 429 (not worked around). Guessed contract-terms PDF URLs returned 404, so no terms PDF was read first-hand. Read: docs.kalshi.com/getting_started/fee_rounding, help.kalshi.com/trading/fees and maker-fees article. About 14 fetches.

## REBATE1: CLOSED (no rebate program for us; maker coefficient is 0, not 0.0175)
- Help Center fees: "Maker fees are charged for orders placed that are not immediately matched ... only charged when a trade is ultimately executed"; "Maker fees apply in some markets". No maker rebate, market-maker program or interest on balances found on any page read (the interest and incentive article URLs I tried were other articles; nothing about interest anywhere). So: no published maker rebate, no balance interest found (not proven absent).
- Only program found earlier (INCENT1, `GET /incentive_programs`): liquidity incentive pools on non-15-minute markets, under $1 per program unpaid, most US individuals qualify, depth already 13k+ per side. Not on KXBTCD or the 15 minute series. See INCENT1_RESULT.md.
- Fee type (COST1, live API): KXBTCD and the 15 minute series are plain `quadratic`, maker multiplier 0. The 0.0175 x p(1-p) rate exists only on about 160 sports and futures series.
- MMSIM1 rerun (cost recomputation of the registered test, same rule, books before 2026-11-08 only; files and rows on or after the cutoff not loaded): 176 events, 1,151 strikes. Maker coef 0: PF 1.45, +0.82c per strike, +5.38c per event. Coef 0.0175: PF 1.32, +0.62c. (Protocol's 171-event split: 1.41 and 1.28.) The true coefficient is 0, so the bar's bound (0.0175) was conservative by about 0.13 PF. The bar was PF 1.3 at 0.0175 AND n 300 AND each third positive AND gold correlation under 0.3; the fee does not change the other conditions. Fills are still a queue model with no real fill seen. Verdict on the bound: moves it to the 1.4 end, not a new test.

## FEEROUND1: LEAD for sizing only (a cost refinement, not a strategy; basis cash model)
Rounding page: trade fee = model fee rounded up to $0.000001, plus a rounding fee to the account's precision (cent for non-direct), minus a per-order accumulator rebate in cent steps, net never below 0. Rebate only recovers overpayment across several fills of one order. Model used: order fee = ceil to cent of 0.07 x C x p(1-p) (COST1; not verified on real fills). Mean cents per contract (unrounded in brackets):
| C | 3c-30c [0.92] | 30c-88c [1.49] | 88c-97c [0.48] |
|---|---|---|---|
| 1 | 1.46 | 1.90 | 1.00 |
| 3 | 1.08 | 1.67 | 0.63 |
| 6 | 1.00 | 1.57 | 0.57 |
| 10 | 0.97 | 1.54 | 0.53 |
| 15 | 0.96 | 1.53 | 0.51 |
| 18 | 0.95 | 1.52 | 0.51 |
| 30 | 0.94 | 1.51 | 0.50 |
| 100 | 0.92 | 1.50 | 0.48 |
Cost falls monotonically toward the formula, with ripples. Lowest sizes by band: 3c-30c, 12 or more (4% over formula at 12, 2% at 20+); 30c-88c, 12 or 20 (4 and 8 are the local dips); 88c-97c, 20+ (5% over at 20), and exact fits per price, e.g. 94c: 5 contracts costs 0.40c each, 3 contracts 0.67c. L1 check: in the 88c-97c band a 1-lot pays 1.0c against 0.2c to 0.74c formula (2x to 5x at 93c to 97c); 3 contracts pays 0.33c to 0.67c per contract; gold at 15 to 18 sits near the floor (0.27c to 0.8c). So the capped crypto 1-lots are BAD sizes (1c is 20% of the 5c a 95c entry wins), and 3 contracts for XRP, Dogecoin are middling; gold's 15 to 18 is good. Single-contract cost cannot be cut without ordering more, which L1's caps forbid; do not raise size for this alone.

## RULES1: NOT_ENOUGH_DATA for ties (basis: counts, no cash model)
Rules text held (RULES1_META, `KXGOLDD`): "close price of the 1-minute candlestick ... is above 4065 USD/t.oz, then Yes" (strictly above, so a tie resolves No); "rounded to 2 decimal places"; "If no data is published by the specified source agency ... the most recently available published data will be used". The 15 minute and BTC ladder terms PDFs were not read (404/429), so "at or above" wording, halts and revision rules for them are unconfirmed here. Earlier RULES1B (RULES1_RESULT.md) already falsified the 8 rules-text features and found 42 EXACT cases, 0 wins.
Held tables (market: ticker, close, result, strike; no final value stored): every result is yes or no only (no void or scalar), hist15 KXBTC15M 6,185 / KXETH15M 6,267 / KXGOLD15M 285 / KXBTCD 14,270, alts2 19,139, alts3 32,314, alts4 5,442, fresh 35,519 markets; null strike: 8, 8, 0, 0, 3, 47, 17, 0. Because the final index value is not stored, the count of strike-equals-final and of results inconsistent with a naive reading is NOT computable from these tables (would need spot history; `quote-data` spot.csv covers Oct 22 on only). Kill: not enough data, no forward recorder worth building (ties at 2-decimal precision on BTC are rare).
