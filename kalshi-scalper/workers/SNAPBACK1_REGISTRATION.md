# SNAPBACK1 registration: liquidation-cascade fade on Kalshi perpetuals (written 2026-11-03, before any trigger, return or event count was computed)

Discovery only, approved by the owner (relayed 2026-11-03). Nothing trades from this. The owner's Kalshi account is personal and perps access needs an application; the result only decides whether applying is worth it. No live code, no `functions/`, no L1, no promote verb.

## Data (reachability checked 2026-11-03, no key)
Host `https://external-api.kalshi.com/trade-api/v2`. `GET /margin/markets` (44 markets, status, open interest, funding_cap 0.02, funding_deadband 2e-05, schedule). `GET /margin/markets/{ticker}/candlesticks?period_interval=1|60&start_ts&end_ts` (max 5000 candles per call). `GET /margin/trades?ticker=` (tape, cursor). Candle fields: `price{open,high,low,close,mean,previous}`, `bid{open,high,low,close}`, `ask{...}`, `volume`, `open_interest`, `open_interest_notional_value_dollars`, `end_period_ts`. **Open interest IS in the candles.** No funding-rate or funding-payment endpoint exists (three guessed paths returned 404).
History: BTC, ETH, SOL, XRP hourly from 2026-06-03 15:00 UTC (about 3,650 hourly candles); gold from 2026-09-10. 1 minute candles fetched for **KXBTCPERP and KXETHPERP only** (217,953 and 217,924 minutes, 2026-06-03 to 2026-11-03, about 153 days; 40 and 63 gaps in the minute series; 780 and 3,591 minutes with no trade price, forward filled). Other markets are not tested (their data were not fetched). Prices are in the contract's own units (BTC about 7); only ratios are used. Binance not used.

## Rule (all numbers fixed here)
Per market (KXBTCPERP, KXETHPERP), at every minute t (minute-end timestamps):
- ATR(1h) = mean true range of the last 24 COMPLETED clock-hour bars (bars built from the 1 minute candles: open of first, high, low, close of last; true range with previous hour's close). Needs 25 hours of warm-up.
- Move = close(t) - close(t-60 min). Trigger if |Move| > k x ATR and open interest(t) / open interest(t-60 min) - 1 < -x (OI falling more than x over the same hour). A flat or missing OI minute: use the nearest earlier minute.
- Enter AGAINST the move (Move down: long; up: short) at the OPEN price of the minute after t (price.open; forward-filled previous close if that minute has no trade). Price slippage beyond the fee is not modelled; the 12 bp per side is the whole cost.
- Stop: 0.5 x ATR from entry (ATR frozen at the trigger). Target: T x ATR. Time stop: 6 hours after entry, exit at that minute's close. Fills are checked on 1 minute high/low; if stop and target are both touched in one minute the STOP is taken (pessimistic). A gap through a level fills at the level (no gap model; stated optimism).
- Cooldown: no new entry in the same market within 6 hours of the previous entry, nor while a position is open. The first trigger of a cascade is the one traded. BTC and ETH are treated as separate markets and pooled in one class ("crypto majors").
- Costs: taker fee 12 bp per side (24 bp round trip), no maker assumption. Funding: no funding field exists to fetch, so ASSUMED 1 bp of notional charged AGAINST the position (whatever its sign, conservative) for each 8-hourly funding time (00:00, 08:00, 16:00 UTC, an assumption, not verified) crossed while held.
- Return per trade in bp of notional = side x (exit/entry - 1) x 10,000 - 24 - funding.

## Grid (pre-committed, 8 cells for the crypto class)
k in {2, 3} x x in {2%, 5%} x target T in {2, 3} ATR. Everything else fixed above. **Tries counted: N +8** (running about 729,995 + 8; z bar about 5.27 for the record).

## Window split
Timestamps from the first candle T0 to the last T1. Development = T0 to T0 + 2/3 (T1 - T0), split in two halves at T0 + 1/3 (T1 - T0). The last third is FROZEN and UNREAD: the code computes no trigger, event count or outcome after the cut until a cell passes development, and then reads it once.

## Counterparty
Liquidated traders (and stop-outs) selling or buying at any price into thin books; the fade is paid for providing liquidity into forced flow.

## Numeric prediction (from the owner's research agent, kept as given; mine added)
Win rate about 30%, payoff about 5x (the stop is 0.5 ATR, which is only about 25 bp for BTC, near the 24 bp round-trip fee, so I expect the fee to eat many "wins" and the real payoff well under 5x). Probability it survives 5 to 10%. Events: 20 to 40 in 150 days over all cells combined; I expect the loosest cell (k 2, x 2%) to reach 40 development events pooled over two markets only barely, and the tight cells (k 3, x 5%) to have under 10. Expected verdict: NOT_ENOUGH_DATA for at least 6 of 8 cells, FALSIFIED for the rest. Expected profit factor of cells with data: 0.6 to 1.1.

## Verdict rules (fixed)
- **NOT_ENOUGH_DATA**: fewer than 40 development events (entries after the cooldown) in a cell.
- **FALSIFIED**: development expectancy after fees and funding not above 0 in BOTH development halves, or profit factor under 1.5 in either half or in the whole development window.
- **Survives development** (only then is the frozen third read, once): mean net bp above 0 in both halves, PF at least 1.5 in each half and overall, n at least 40, and a z (mean over standard error, trades treated as independent after the cooldown) of at least 5.27 on development. A survivor is then read on the frozen third; PF under 1.5 there is FALSIFIED, otherwise it is a LEAD only, to be confirmed forward. No cell is promoted by anything here.
- Per-cell reports: n, events per month, win rate, payoff ratio, PF, expectancy in bp, worst loss in ATR and in dollars per $100 notional, longest losing run via `scalper.streaks.empirical_streaks`, months to 40 forward events at the observed rate.

## Read date
Development read once on 2026-11-03 immediately after this commit. Frozen read: same day only if a cell survives; otherwise never read. Forward: 40 events at the observed rate (reported).
