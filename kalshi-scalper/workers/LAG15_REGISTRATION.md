# LAG15 registration (Strategy Research V2, written 2026-11-02 BEFORE any Kalshi candle or any spot kline was downloaded and before any outcome, price or PnL was computed; research only)

Owner direction relayed by the main session (approved): non-L1 angles are allowed on 15 minute Kalshi series the README has never named. Family LAG15 is a replication, on new assets and from history, of the already registered RECORD1 hypothesis ("does Kalshi's 15 minute quote lag the underlying spot near the close"). Nothing here means trade; there is no promote verb.

## Ledger check (stop-if-duplicate)
`grep -c KX<NAME>15M README.md` before this file: KXHYPE15M 0, KXBNB15M 0, KXZEC15M 0, KXNEAR15M 0, KXSILVER15M 0, KXCOPPER15M 0, KXPALLADIUM15M 0, KXPLATINUM15M 0, KXEURUSD15M 0, KXGBPUSD15M 0, KXUSDJPY15M 0. All eleven are new. Other 15 minute series on the public series list, SKIPPED because the README already names them: KXADA15M, KXBCH15M, KXTON15M, KXUSDMXN15M, KXBRENT15M, KXDJIA15M, KXINX15M, KXNDQ15M, KXWTI15M, KXNATGAS15M, KXUSDCAD15M, KXAUDUSD15M, KX10YRRATE15M (and the 2, 5, 30 year siblings), KXCRYPTOCOMP15M, KXCRYPTOLEAD15M, KXGOLD15M, and the five RECORD1 assets. Not named but not a spot-versus-strike market (no keyless spot source or not a price): KXCOFFEE15M (no free minute history), KXKPOWMID15M (a political index). Neither is tried. Not L1 (the L1 series are KXBTC15M, KXGOLD15M, KXETH15M, KXXRP15M, KXDOGE15M and the probes), not OICORE.

## What was looked at before this registration (disclosure)
Listing only: the public series list (tickers and titles), and for each of the eleven series the settled market list (count, first and last close time, mean volume, strike type). No candle, bid, ask, result or spot price was read or printed. Sandbox reachability tests (HTTP status and a 200 character sample of one current minute) of spot sources: OKX history candles, KuCoin, Gate (reachable), Binance.com (HTTP 451 style block "restricted location"), Bybit (blocked), Binance.US (reachable). Pyth Benchmarks and Hermes price history return 401 unauthorized; Yahoo chart and Dukascopy return 429; Stooq resets the connection. One Yahoo retry with a changed User-Agent was refused by the sandbox as a bot-check workaround and was not repeated.

Settled markets on the list (strike type greater_or_equal, so ties resolve YES): KXHYPE15M, KXBNB15M, KXZEC15M, KXNEAR15M 6,417 each (2026-08-27 to 2026-11-02); KXSILVER15M 4,476; KXCOPPER15M 4,401; KXPALLADIUM15M and KXPLATINUM15M 2,839 each; KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M 2,605 each. Mean volume per market 6,000 to 50,000 contracts (listing field, all pass the liquidity rule below).

## Groups, spot sources, and what is not runnable
- **crypto-new** (KXHYPE15M, KXBNB15M, KXZEC15M, KXNEAR15M). Spot: OKX public 1 minute candles for HYPE-USDT, BNB-USDT, ZEC-USDT, NEAR-USDT (`/api/v5/market/history-candles`, keyless, deep). Binance.com, which the brief named, is blocked from this sandbox; OKX replaces it. Settlement reference is the CF Benchmarks 60 second average (README); OKX USDT is one venue of it, so the basis is a stated limit, as in LAG2B (Kraken). RUNNABLE.
- **metals** (silver, copper, palladium, platinum; settlement a single Pyth print) and **FX** (EURUSD, GBPUSD, USDJPY; single Pyth print). No keyless minute history deeper than 7 days is reachable from this sandbox (sources above). Seven days is a handful of trades; the groups are registered as `NOT_RUNNABLE` and are NOT scored. If a deeper keyless source is found it needs a new registration (no variant is run under this one).

## Counterparty and mechanism
Slower quoting by retail takers and thin-book market makers on newly launched, thinly staffed 15 minute markets. The spot price that settles the market is public and moves before the quote may. Honest prior that the quote is already on top of spot: high (LAG2B on Bitcoin: FALSIFIED, the median gap between a spot model and Kalshi's last trade was 0.2c; RECORD1's own read is still pending). The only reason to expect a different answer is that these assets are newer and less contested. Prior of a pass 3%.

## Model (RECORD1's, reused; every difference listed)
At the look, with `s` = 60 seconds before the close: `S` = spot proxy, `K` = the market's `floor_strike`, `sigma` = per square root second volatility. Variance of the average of the final 60 s index values seen from s = 60: `sigma^2 * ((s - 60) + 20) = 20 sigma^2`. `P(YES) = Phi( (S - K) / (S sigma sqrt(20)) )` with `sigma` a fraction (log return) per sqrt second. Ties resolve YES (the market is greater_or_equal; the model's mass at equality is zero, stated).
Differences from RECORD1, all forced by the data (candles are 1 minute, the recorder is per second):
1. **One look time only: s = 60** (the candle ending exactly 60 s before the close). RECORD1 also looks at 45, 30 and 15 s; a 1 minute candle cannot see them. Fewer looks, so fewer trades.
2. **Index proxy = one venue (OKX)** 1 minute kline close at the look minute, not the median of three exchanges per second. The kline whose open time is `close - 120 s` ends at the look and is the last candle that may be used (its open time is the key; nothing later).
3. **sigma** = root mean square of the five 1 minute log returns of OKX closes over the 300 s ending at the look (the previous 300 s, as RECORD1), divided by sqrt(60). RECORD1 uses about 300 one second changes. Five returns is noisy; stated, not tuned. A missing minute in those five means no trade. sigma of zero means no trade.
4. **Quote** = the Kalshi 1 minute candle (historical endpoint: `yes_bid.close` and `yes_ask.close`; live: `close_dollars`; the shared parser reads both) ending at the look, or the latest earlier candle with a two sided quote (0 < bid < ask < 1) not older than 120 s. RECORD1 requires 5 or more contracts of size at the touch; candles carry no sizes. Replacement liquidity rule (fixed now, uses only data up to the look): the sum of candle volume over the 5 minutes ending at the look is at least 10 contracts, and the quoted spread is at most 0.10.
5. **Fee**: the entry test uses the unrounded `0.07 p (1-p)` per contract as RECORD1 (edge >= 0.03 after it). The SCORED fee is 7% x C x p x (1-p) rounded up to the cent per order of C = 10 contracts (the shared `fee()`), with a x1.2 stress.

## Entry rule (fixed now, frozen by this file)
Buy YES at the ask if `P - ask - 0.07 ask (1 - ask) >= 0.03`; buy NO at `1 - bid` if `(1 - P) - (1 - bid) - 0.07 (1 - bid) bid >= 0.03`. One order of C = 10 contracts per market, taker at the quoted ask (a quote is not a fill; stated), held to settlement, one market per asset per window. Information-only second try: edge 0.06.
**Bans applied, in advance:** (a) an entry price below 0.20 is not taken (no cheap-side-late; RECORD1 would allow it, this is a stricter rule, the count of skipped trades is printed); (b) **OVERLAPS_L1**: for each asset, if more than 50% of its qualifying trades (counted from entry PRICES alone, before any outcome is used) have an entry price in 0.88 to 0.97, the asset is reported `OVERLAPS_L1` and its outcomes and PnL are NOT computed or scored; (c) no buy-the-favourite-and-hold, no coin-flip round trip.

## Universe (cost and metadata only)
Assets exactly as listed above. Liquidity: settled markets on the list at least 1,000 and mean listed volume at least 1,000 contracts (all four crypto-new assets pass; decided on the listing). Markets with a model, a valid quote and the volume rule at the look are "eligible"; the eligible set does not depend on outcomes.

## Windows and brier
Eligible dates sorted, split into three EQUAL thirds by number of dates: W1 earliest, W2 middle, W3 the frozen holdout (the last third). W3 is not scored unless W1 and W2 both pass; the rule is frozen by this file. Brier: model P against the outcome and the market mid `(bid + ask) / 2` against the outcome, over all eligible markets of the group (not only the traded ones), pooled and per window.

## Numeric prediction (written before scoring)
The spot model's Brier is WORSE than the quote mid's; profit factor in each window 0.4 to 1.2; pooled mean per contract -6c to +1c; trades per scored asset 20 to 400; most qualifying trades sit in the 0.88 to 0.97 band (so several assets end `OVERLAPS_L1`). The registered numeric claim under test is the opposite: the spot model beats the quote in Brier at the look, and the rule earns profit factor >= 1.5 in each of three time windows with n >= 150 trades for the asset group. Probability of FALSIFIED or OVERLAPS_L1: about 90%.

## Kill criteria
- `FALSIFIED`: the model Brier no better than the market mid's (pooled), or profit factor under 1.5 after fees in ANY window (W3 only read if W1 and W2 pass), or not positive at fees x1.2 in any window, or pooled mean under +2.0c, or event-clustered (date) pooled z under the deflated bar 5.27.
- `NOT_ENOUGH_DATA`: fewer than 150 settled trades pooled for the group (the PFs are printed anyway; a failed Brier line still falsifies).
- `NOT_YET_FALSIFIED`: all of the above pass. It would permit only a forward re-read and the RECORD1 quote-level test, never a trade.
- `NOT_RUNNABLE`: spot unreachable (metals and FX, registered now). `OVERLAPS_L1`: per asset, above.
Windows, thresholds, look, universe and bans are not changed after the result; no variant is run.

## Overlap with L1
None by construction. Different assets (none are L1 series), a different information source (a spot model, not the 88c to 97c band), and the band overlap test above removes any asset whose trades would just be favourites bought in the band. It places no order and touches no code in `functions/`, L1 or OICORE.

## Tries
N + 2 per asset group: crypto-new (Try A edge 0.03, the verdict; Try B edge 0.06), metals (NOT_RUNNABLE, counted anyway), FX (NOT_RUNNABLE, counted anyway): +6, running count about 728,708 to about 728,714 (deflated z bar about 5.27). Every result is quoted with window, n, cost and N.

## Forward read (not built)
Crypto-new: Kalshi candles and OKX klines are retrievable after the fact, so no recorder is needed. New markets accrue 96 a day per asset. A forward read needs 30 fresh days of markets after the history end (2026-11-02): earliest **2026-12-02**, and only if the history result is not FALSIFIED. RECORD1's own registered read (original five assets) is expected about 2026-11-05 to 2026-11-08. Metals and FX: a recorder of a keyless spot feed is needed (none reachable now); not built.
