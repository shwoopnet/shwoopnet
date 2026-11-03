# FXREF1 registration: 15 minute FX / energy markets priced against an outside spot reference, cheap side only (Strategy Research V2, discovery lane, research only)

Written 2026-11-03 BEFORE any outcome was joined and before any reference price was fetched. Only quote counts at the look (ask level, no result column) were read for the census. No live code, no `functions/`, no L1, no OICORE, no promote verb. Nothing here means trade.

## 1. Duplicate check (said first)
- **H7** (README 623, FALSIFIED) and **L2/N1/N2**: distance-to-strike in realised-vol units, with the outside reference being spot, but on **Bitcoin 15 minute only**, both sides, any price. **CMD1** (README 3903, FALSIFIED -7.28c, n 1,054): the same mechanism on commodity DAILY ladders (futures as spot), both sides. **NOWCAST1/CPI1**: macro nowcasts, not this. **E5/E5B** (README 3636): L1 (favourite buyer) on WTI and natural gas; **FXUSD**, **AUD1/PAPER1/FLAT2**: USD direction, L1 rule, flat shape on the FX pairs. **BARRIER1**: touch markets.
- **Not tested before:** the distance-to-strike nowcast with an outside spot reference on the **15 minute FX (EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD), WTI and natural gas** markets, **cheap side only** (ask 3c to 30c, model probability at least 3 times the ask). H7/CMD1 are the closest relatives; the mechanism is a relative of a falsified one and is disclosed as such (prior of a pass under 3%).
- Verdict: **not a duplicate in cell, a near relative in mechanism**. Proceed to the census.

## 2. Mechanism and counterparty
Thin 15 minute FX and energy books (median 1,600 contracts a market for AUD/USD and USD/CAD) may be anchored on a stale reference or ignore the volatility regime. Counterparty: the seller of a tail side priced below its distance-implied chance. Contrary evidence: the ordinary longshot bias (a cheap ask wins less than its price), H7 (price well calibrated to distance on Bitcoin), CMD1 (-7c).

## 3. Universe, cut and data
- Series: `KXEURUSD15M KXGBPUSD15M KXUSDJPY15M KXAUDUSD15M KXUSDCAD15M KXWTI15M KXNATGAS15M`. Index 15 minute series (Dow, S&P 500, Nasdaq 100) and Brent have **0 settled markets** in the census (README 3820): excluded, not traded.
- Reference (fixed now): Yahoo chart `EURUSD=X GBPUSD=X JPY=X AUDUSD=X CAD=X CL=F NG=F`, minute closes. Strike K from the market's own `strike` field. Look: the Kalshi candle ending 600 s before the close; spot S = the last reference close at or before that second; vol = standard deviation of the previous 60 one minute log returns (at least 40 present), zero drift, time left 10 minutes: `P(YES) = Phi(ln(S/K) / (sigma * sqrt(10)))`. Ties settle YES (FXUSD), not modelled.
- Frozen cut: markets closing from 2026-10-03T16:00Z are never fetched or joined by this worker. Pre-cut census (stored Kalshi prices, no result, no reference): WTI 4,146 markets (2026-08-06 to 10-03), natural gas 2,606 (08-27 to 10-03), EUR/USD 649, GBP/USD 649, USD/JPY 649 (09-23 to 10-02); **AUD/USD and USD/CAD have 0 pre-cut markets** (start 2026-10-07). Markets with a cheap-side ask (3c to 30c) at the look: WTI 1,919, gas 1,062, EUR 271, GBP 256, JPY 283 (about 3,800 quotes).
- **Reference availability gate (fixed now):** a minute reference must exist for the look hour of at least 90% of the pre-cut markets. Yahoo 1 minute covers about 7 days (all after the cut, forbidden) and 5 minute about 60 days (from about 2026-09-04: no coverage of WTI before then, gas before then, FX is 09-23 on, but it is 5 minutes, not minutes, and the shared host answers HTTP 429 now). Stooq and Dukascopy are unreachable from this host (connection reset by the proxy). Below the gate the result is `NOT_RUNNABLE` and the forward plan (section 6) applies. I did not work around the 429.

## 4. Trade rule (if runnable)
At the look, cheap side = the side with the lower ask; trade if its ask is in 0.03 to 0.30 (hard limit 0.30), model probability of that side at least 3 times the ask, held to settlement, at most 1 per market, 1 contract, fee `ceil(0.07*C*p*(1-p)*100)/100/C` with C=10 and fees x1.2 stress. Control: the same markets' cheap-side asks at the same prices with no model filter (win vs price).

## 5. Numeric prediction and kill rules
Prediction: treated trades 0 to 60 pre-cut (under the 150 bar); if run, win rate at or below the mean ask paid (the cheap side wins about 1 to 2 points less than its price), PF 0.6 to 0.95, mean net -1c to -4c. Prior of a pass under 3%.
Kill rules: `NOT_RUNNABLE` if the reference gate fails or fewer than about 150 expected treated trades; `NOT_ENOUGH_DATA` under 150 trades with months to go; `FALSIFIED` if mean net after fees is not above 0 in both halves (by date) or PF is under 1.5. A result better than predicted is an audit trigger first (reference timestamp after the look, basis offset between Yahoo and Kalshi's source, ties).

## 6. Forward plan if not runnable
A keyless daily job (GitHub Actions, public Yahoo chart `range=5d&interval=1m` for the seven symbols, minute closes saved gzipped to the `quote-data` branch, no key, no order) accumulates the reference; Kalshi's candles for the same days are re-fetched later from the public API, so only the reference needs recording. All of it falls after the frozen cut, so it is the single frozen read, run once on or after 2026-12-15 (about 30 trading days: WTI and gas about 25 treated per week if the pre-cut rate of cheap quotes holds, before the 3x filter), with this file's rules unchanged. Not built here (research only, no workflow changes by this worker).

N: +2.
