# XCRY1 registration (Strategy Research V2, written 2026-11-03 BEFORE any Kalshi candle, any OKX kline or any outcome was downloaded or computed; research only)

Brief (main session, for the owner): more strategies in the OICORE shape (cheap side or underdog, ask 5c to 50c, held to settlement, low win rate, large payoff per win, trigger from public data published before the quote reprices). Family XCRY1: a cross-series price lead. Nothing here means trade; there is no promote verb. Code `src/scalper/xcry1.py` and `tests/test_xcry1.py` (synthetic data, all pass) are committed with this file; no data has been fetched.

## Ledger check (stop-if-duplicate): NOT a duplicate
`grep -n -i "xcry\|KXHYPE\|KXNEAR\|KXZEC\|KXBNB" README.md workers/*.md`: no XCRY1 anywhere. Closest prior work, each different: NEWH15 (Coin Race, `KXCRYPTOLEAD15M`, a different market, Bitcoin price at 10 minutes left); NEWH12 (XLAG, one KALSHI BOOK lags another's 2 minute move, Bitcoin/Ethereum/Dogecoin, 20c to 80c; all FALSIFIED, the control equalled the hypothesis); XLEAD1 (a Bitcoin L1 win or loss in the PREVIOUS window, followers include HYPE/NEAR/BNB/ZEC; NOT_ENOUGH_DATA); LAG15 (alt spot model against its OWN quote at 60 s; FALSIFIED). None trades the cheap side of an altcoin 15 minute market on the SAME-window Bitcoin SPOT return of the last 3 minutes. The pair (Bitcoin spot return 360 s to 180 s before the close, cheap side same direction, HYPE/NEAR/Zcash/BNB, held) has not been run.

## What was looked at before this registration (disclosure)
Text only: README tail and ledger, `workers/OICORE_SHAPE_INVENTORY.md`, `LAG15_REGISTRATION.md`, `LAG15_RESULT.md`, `ECONNEW2_REGISTRATION.md`, `src/scalper/lag15.py`, `streaks.py`, `oirel.py`. LAG15's printed numbers (six-thousand markets per asset, listed volume) are known from its result. No new Kalshi or OKX data was requested for XCRY1 and no outcome of any XCRY1 trade has been seen.

## Counterparty and mechanism
Who is on the other side: the sellers of the cheap side of an altcoin 15 minute market, whose quote is built from that altcoin's own flow and book. Bitcoin leads crypto: when it has moved by 1 sigma over 3 minutes, alts tend to follow with a beta above 1, and the settlement is a 60 second average of the CF Benchmarks index that is still ahead (60 s average, so a move that continues after the look shifts the average). The underdog buyer wins when the alt follows Bitcoin after the look and the quote has not yet moved by enough. **Honest prior against:** LAG15 showed the quote beats a spot model built on the alt's OWN spot (model Brier 0.0764 against 0.0287); a cross-asset lead is a weaker signal than the alt's own spot, which the quote already tracks. Market makers on Kalshi alt books see Bitcoin too (NEWH12/BK1 to BK7: cross-series leads are priced inside a minute). What could still make it work: the settlement average (the last 60 s average is not yet formed at 180 s, so there is 120 s of drift to come), the beta of alts to Bitcoin in the last 3 minutes, and thin alt books (listed volume 6,000 to 50,000 contracts a market). Probability of a pass: about 3%.

## Data sources (keyless, public)
Kalshi: settled markets of `KXHYPE15M`, `KXNEAR15M`, `KXZEC15M`, `KXBNB15M` (listing: close time, result, volume; no strike is needed) and the 1 minute candlestick batch endpoint (bid close, ask close, volume), keeping only candles ending in (close - 900, close - 180]. Bitcoin spot: OKX `BTC-USDT` public 1 minute klines (`/api/v5/market/history-candles`, the fetcher from `lag15.py`; Binance is blocked here). OKX is one venue, not the CF index (basis unmeasured, stated). Nothing at or after the look is used.

## Universe (fixed now, before any outcome)
- Series: exactly the four above. **Never Bitcoin, Ethereum, Dogecoin or gold** (L1 buys the favourite there; a cheap-side trade in the same market and window would hedge L1; `test_xcry1.py` asserts none is in `ASSETS`). XRP, SOL and the others are not used.
- Minimum quoted volume rule: an asset is in only if it has at least 1,000 settled markets and a mean listed volume of at least 1,000 contracts (all four passed this on LAG15's listing); a market is eligible only if the sum of its candle volume over the 5 minutes ending at the look is at least 10 contracts and its two sided quote (0 < bid < ask < 1, not older than 120 s) has a spread of at most 0.10.
- History: all settled markets on the list at fetch time (about 2026-08-27 to 2026-11-03, about 68 dates); the Bitcoin window needs 25 hours of earlier klines.

## Exact trigger and trade rule (frozen by this file)
Look = 180 s before the close. `end(t)` = close of the OKX 1 minute kline that ENDS at t.
1. **Trigger:** `ret = ln(end(look) / end(look - 180 s))` (that is the Bitcoin return from 360 s to 180 s before the close). `sigma` = root mean square of the 3 minute log returns `ln(end(t) / end(t - 180))` for t = look, look - 60 s, ... over the 1,440 minutes ending at the look (at least 1,000 valid returns, else no signal). Fires when `|ret| >= 1.0 x sigma`. The multiple 1.0 is fixed now and is not tuned.
2. **Trade (follow):** up move (ret > 0): buy YES at the ask if the YES ask is in 0.05 to 0.50, else nothing. Down move: buy NO at `1 - bid` if that price is in 0.05 to 0.50, else nothing. One order of C = 10 contracts per market, taker at the quoted ask (a quote is not a fill; stated), held to settlement. Every market with a trigger and a cheap side in the direction is a trade; four assets can trade in one window (they share Bitcoin's move, so they are correlated; statistics are clustered by date).
3. **Control (reported only, not a try to trade):** same trigger, the cheaper side AGAINST the Bitcoin move (up move: NO if its price is 0.05 to 0.50), same costs and windows.
4. **Cost:** fee 7% x C x p x (1-p) rounded up to the cent per order (`lag15.fee`), plus a stress at fee x1.2. Win pays 100c.
5. No look-ahead: the Bitcoin signal uses klines ending at or before the look; the quote is the latest two sided candle ending at or before the look.

## Windows and frozen holdout
Eligible dates sorted and split into three EQUAL thirds by number of dates: W1 earliest, W2 middle, W3 the last third, a **frozen holdout read only if W1 and W2 both reach profit factor 1.5** (control also read only then). The rule, trigger multiple, band and universe are frozen by this file; no variant is run; any change made after registration is disclosed in the result.

## Numeric prediction (written before scoring)
Win rate **27%** (range 24% to 31%; the mean entry price is about 0.30 and the market is roughly fair on the cheap side); payoff ratio (average win in cents / average loss in cents) **2.2** (range 1.9 to 2.6; win about +68c, loss about -32c); profit factor **0.85** (range 0.6 to 1.1) in each window; pooled mean about -2c a contract; the control within 0.15 of the follow profit factor (the signal carries no direction information the quote lacks). Trades: about 2,000 to 5,000 (the trigger fires in roughly a third of windows, the cheap side matches the direction about half the time). Probability of FALSIFIED: about 95%.
**Streak report (at the predicted win rate 27%, `src/scalper/streaks.py`, exact):** in 100 trades the longest losing run has mean 11.8, 95th percentile 19, 99th percentile 24 (at 28%: mean 11.4, 95th 18, 99th 23); the chance of at least one 10-loss run in 100 trades is 0.71 (0.67 at 28%). A 10-loss run is normal at this win rate, not a sign of a broken rule. The result file repeats the report with the OBSERVED win rate and the empirical longest losing run.

## Kill rules
- `FALSIFIED`: profit factor under 1.5 after fees in any window read (W1, W2, and W3 if read), or not positive at fees x1.2 in any window read.
- `NOT_ENOUGH_DATA`: fewer than 150 settled follow trades pooled over the windows read (the profit factors are printed anyway).
- `NOT_YET_FALSIFIED`: all windows read have profit factor 1.5 or better and are positive at x1.2. A pooled event-clustered (date) z under the deflated bar of about 5.27 (running N about 728,704) or a pooled mean under +2.0c is **not a pass**; it stays NOT_YET_FALSIFIED and permits only a forward re-read. It never permits a trade.
- Information only, no verdict: the control, per asset lines, the Brier-free comparison of follow against control.

## Overlap with OICORE (reported, not a rule)
OICORE is Bitcoin only (the cheap side 180 s before the close after open interest jumped), so XCRY1 shares no market with it, but both look at the same 180 s moment. Reported: (a) the share of XCRY1 trades whose 15 minute window also holds an OICORE trade (the OIREL research rule `oirel.decide` over the forward ledger windows, 2026-08-06 to 2026-10-27, the span where Bitcoin open interest is stored), and (b) the correlation of the daily sum of XCRY1 PnL with the daily sum of OICORE PnL over days present in both. Both are computed after the verdict and cannot change it.

## Tries
N + 2 (the follow rule counts; the control and the per-asset lines are information). Running count about 728,704 (z bar about 5.27). Every result is quoted with window, n, cost and N.

## Forward read and recorder (not built)
The Kalshi candles and OKX klines are retrievable after the fact, so no recorder is needed. A fresh read needs 30 new days after the history end (2026-11-03): earliest **2026-12-03**, and only if the history result is not FALSIFIED (a FALSIFIED result plans none). The forward read would also want size at the ask (R6-style book sizes do not exist for these four markets; candles do not show fill size) and a Bitcoin spot feed finer than one minute; neither exists, so a pass here would first need a recorder of the four books plus Bitcoin per second, not built.
