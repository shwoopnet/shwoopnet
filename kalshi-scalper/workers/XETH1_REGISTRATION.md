# XETH1 registration (Strategy Research V2, written 2026-11-03 BEFORE any KXETHD candle, any OKX kline or any outcome was downloaded or computed; research only, discovery)

Brief (coordinator, for the owner): cross-market consistency with an outside price, cheap side held to settlement, NOT 15 minute. Hourly Ethereum ladder `KXETHD` against the Bitcoin move over the last minutes. Nothing here means trade; there is no promote verb. OWNER RULE (strict): cheap side only; no favourite-side result is computed or printed anywhere in this study (the code has no favourite-side function).

## Ledger check (stop-if-duplicate): NOT a duplicate
`grep -il KXETHD workers/*.md`: HOURLY1 (spot-lognormal level model on SOL/XRP/DOGE/HYPE hourly ladders, ETH excluded), HRSEAS1 and OIHR1 (Bitcoin ladder; KXETHD noted as only 14 days, not run), LADLONG1 (Bitcoin wings), NEWH12 (cross-asset lead and lag among the 15 MINUTE crypto books; an Ethereum copy of LADLEAN declined), OICORE_SHAPE_INVENTORY. Closest, each different: XM1 (README ~3070, the 15 minute market against its coincident ladder), NEWH12 (Kalshi book lags Kalshi book at 15 minutes), XCRY1 (Bitcoin spot leading HYPE/NEAR/ZEC/BNB 15 minute books, a different market and horizon), LAG15 (one asset's own spot), VOLGAP1 (ladder-implied sigma vs own realised vol, ratio trigger). None uses Bitcoin's move as the trigger for the hourly KXETHD ladder with ETH's own lack of movement as the second condition.

## What was looked at before this registration (disclosure)
Text only (README tail, XCRY1/LAG15 registrations and code, HRSEAS1 code for the ladder fetch shape). Metadata only from the Kalshi API: ONE listing of currently OPEN KXETHD markets (strike spacing is $5 near the money in the 19:00 style event with 260 strikes, $40 in the 17:00 style event with 40 strikes; ETH about $2,290). One OKX call returned the last 2 ETH-USDT klines (reachability). No settled market, candle, result or outcome has been read.

## Counterparty and mechanism
The seller of the cheap side of a KXETHD strike, whose quoter reprices from ETH's own price and may be slower to reprice a Bitcoin-led move (KXETHD volume is about an eighth of KXBTCD's). Bitcoin leads; ETH follows with beta above 1; if ETH has not yet moved, the strike on the Bitcoin side is cheaper than it should be. Contrary view held in advance: the quoter sees both markets (HOURLY1 and XM1 found Kalshi's books price from spot), so the cheap side is priced fairly or worse, as every unconditional hourly tail was (LADLONG1 PF 0.64 / 0.72).

## Data sources (keyless, public)
- Kalshi: settled `KXETHD` markets by close time from the listing (ticker, event_ticker, close_time, strike, result), and 1 minute bid/ask candles via the batch endpoint, 8 markets per request (as `usweep2.py`), 1 to 2 threads, backoff, cache outside the repo (`XETH1_CACHE`, default `/tmp/xeth1_cache`), resumable, tracked background fetch.
- Spot: OKX `BTC-USDT` and `ETH-USDT` public 1 minute klines (`/api/v5/market/history-candles`, fetcher from `lag15.py`). OKX is one venue, not the CF index (basis unmeasured, stated). `end(t)` = close of the kline that ENDS at t.
- History: all settled KXETHD markets whose close lies in the last 62 days at fetch time. Candle availability beyond that is not assumed.

## Windows and frozen holdout
Events (distinct close times) sorted by date; the dates split into three EQUAL thirds by number of dates. The LAST third by close time is the frozen holdout: its markets are dropped at the listing and no candle is fetched and no result stored for them. The first two thirds are the DEVELOPMENT period; its dates are split into two equal HALVES (H1 earliest, H2 later). Nothing about the holdout is read by this file.

## Exact trigger and trade rule (frozen by this file)
Look = 1500 s (25 minutes) before the event's close.
1. **Spot:** `rb = ln(BTCend(look) / BTCend(look - 600))`, `re = ln(ETHend(look) / ETHend(look - 600))`. `sb` and `se` = root mean square of the 10 minute log returns `ln(end(t)/end(t-600))` for t = look, look-60, ... over the 1,440 minutes ending at the look (at least 1,000 valid returns each, else no signal).
2. **Trigger UP:** `rb > 2 sb` and `re < 1 se`. **Trigger DOWN:** `rb < -2 sb` and `re > -1 se`. (ETH "has not moved with it": ETH's 10 minute move in the BTC direction is under 1 sd, including a move the other way.) 2 and 1 are fixed, not tuned.
3. **Strikes:** ETH spot `S = ETHend(look)`. On the move side only: UP uses strikes above S (YES is the cheap side), DOWN uses strikes below S (NO is the cheap side). Take the 6 strikes of that event nearest to S in that direction (chosen from the strike and S alone, before any quote or outcome). Among them keep those whose cheap-side price at the look candle is in 0.03 to 0.30 (YES: the ask; NO: 1 minus the YES bid; a valid two sided quote, 0 < bid < ask < 1), and take the 2 with the HIGHEST price (nearest the money). Fill: taker at the ask of the candle ENDING one minute after the look (YES ask, or NO at 1 minus the YES bid); no fill if that price is above the hard limit 0.30 or below 0.01 or the quote is missing. C = 10 contracts, held to settlement. A trade per (event, strike).
4. **Cost:** fee 7% x C x p x (1-p) rounded up to the cent per order (`hrseas1.fee` form), stress at fee x1.2. Win pays 100c.
5. **Control (no trigger; same rule and cost, deterministic sample):** events with neither trigger and `md5(event_ticker)` hex integer mod 4 equals 0 (a quarter of the events); side = sign of `rb` (UP if rb > 0 else DOWN; rb = 0 skipped); the same 6-strike and 2-highest-price picks. The control is the same ETH cheap tails with no trigger.
6. **Information only (no verdict):** group F = `|rb| > 2 sb` and ETH DID follow (`re >= 1 se` for UP, `re <= -1 se` for DOWN), all events, same trade rule; the sample counts per group.

No look-ahead: spot uses klines ending at or before the look; the quote is the candle ending at the look; the fill candle is the one after, as in HRSEAS1.

## Numeric prediction (written before scoring)
Trigger rate about 0.2 events a day (range 0.1 to 0.6; roughly 1% of hourly closes), so about 10 trigger events and 15 to 25 trades in the development period: `NOT_ENOUGH_DATA` is the likely verdict. If it fills: win 12% (range 8% to 18%) against about 17% paid, PF 0.6 (range 0.4 to 0.9), mean about -4c a contract; control PF 0.7 (range 0.55 to 0.85, matching the unconditional hourly tail record), trigger-minus-control about zero or negative. A trigger PF of 1.5 or better would be an audit trigger first (check the klines used end at or before the look).

## Kill rules
- `NOT_ENOUGH_DATA`: fewer than 150 filled trigger trades pooled over the development period (the PFs are printed anyway, with the days-to-go: forward days = 150 / observed trades per day).
- `FALSIFIED` (150 or more trades): profit factor under 1.5 after fees in either development half, or not positive at fees x1.2 in either half, or (trigger mean minus control mean) not positive in both halves.
- `NOT_YET_FALSIFIED`: all of the above clear. A pooled day-clustered z under the deflated bar of 5.27 (running N about 730,230) or a pooled mean under +2.0c is not a pass; it permits only a forward re-read, never a trade.
- The frozen last third is read only if both development halves pass; a FALSIFIED or NOT_ENOUGH_DATA result never reads it.

## Probe spec if both halves are positive (written now)
Forward only: the same trigger recorded live from the recorder branch or a poll, no order; `KXETHD` cheap side, 1 contract, would be a separate reviewed slot that cannot hold a position at the same time as L1 (it is not a 15 minute series, so it cannot). Nothing is built.

## Tries
N + 2 (one rule). Control and group F are information. Running count about 730,232 (z bar about 5.27).
