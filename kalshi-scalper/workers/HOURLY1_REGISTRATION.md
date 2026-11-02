# HOURLY1 registration (Strategy Research V2, written 2026-11-02 BEFORE any Kalshi candle, any spot kline, any result, price or PnL was read or computed; research only)

Owner direction relayed by the main session (approved): new non-L1, non-OICORE families on existing public data. Family HOURLY1 asks whether a spot-based lognormal model beats the quotes of Kalshi's hourly altcoin "above" ladders. Nothing here means trade; there is no promote verb.

## Ledger check (stop-if-duplicate)
`grep -c <ticker> README.md` and `grep -rl <ticker> workers src` before this file: KXSOLD 0, KXXRPD 0, KXDOGED 0, KXHYPED 0 (also KXSOLE, KXDOGE, KXBNBD 0). All four are new. Not tried: the "range" bracket series (KXSOLE, KXXRP, KXDOGE, KXRIPPLE, different payoff, a bracket not an above/below) and KXBNBD (volume 2.5M, under the 5M rule). Excluded by the brief: KXBTCD and KXETHD (DERIBIT-IMPLIED). KXHYPE15M was LAG15's; KXHYPED is the hourly series and is a different market. Not L1, not OICORE.

## Universe (fixed now, chosen on series metadata only)
From the public series list (`/series?include_volume=true`, 15,647 series), frequency "hourly", category Crypto, title "above/below" or "Directional" (one strike per market, strike type "greater"), listed volume above 5,000,000, excluding BTC and ETH: **KXSOLD (SOL Directional, 55.07M), KXXRPD (XRP, 18.20M), KXDOGED (Dogecoin, 5.95M), KXHYPED (Hype Directional, 5.63M).** The universe does not depend on any outcome. Groups (one verdict each): **SOL** (KXSOLD), **XRP** (KXXRPD), **DOGE+HYPE** (KXDOGED + KXHYPED, pooled because each alone is thin).

Disclosure of what was looked at before this file: the series list; the shape of ONE settled KXSOLD market (to read the rules text; it showed result "no" and an expiration value, not used for anything); a count, strike type, first and last close and event count of all settled KXSOLD markets (460,475 markets, 1,586 events, 2026-08-27 to 2026-11-02, 68 dates, strike type "greater" on all). The market listing carries a `result` field; no outcome was tabulated or scored. OKX reachability: one latest candle for SOL, XRP, DOGE and HYPE USDT (format check, not used).

## Settlement reference
KXSOLD rules text: "If the simple average of the sixty seconds of CF Benchmarks' SOLUSD_RTI before 12 PM EST is above $X at 12 PM EST ... then the market resolves to Yes" (strictly above; ties NO). The series list gives CF Benchmarks as settlement source for all four (SOLUSD_RTI, XRPUSD_RTI, DOGEUSD_RTI, and the Crypto terms for HYPE); I read the rules text of KXSOLD only and assume the same 60 second RTI average for the others (stated). The spot proxy is OKX USDT, one venue of the index, so the basis is a stated, unmeasured limit (as LAG15).

## Counterparty, information source, and why the hourly horizon might differ from LAG15
Counterparty: retail takers and thin-book quoters on ladders of 100 to 300 strikes per hour that are repriced from a spot feed by an automated ladder maker, with slower re-quoting on altcoins than on BTC. Information: OKX public 1 minute klines (keyless; Binance.com is blocked from this sandbox). Honest prior that the quote is already on top of spot: high (LAG15: model Brier 0.0764 against the quote mid 0.0287 at a 1 minute look on the 15 minute series; LAG2B on Bitcoin FALSIFIED). What could differ at the hourly horizon: (1) the look is 10 minutes out, so the question is no longer a sub-minute lag but whether the quote's implied volatility is mispriced against a 60 minute realised volatility (a volatility-level gap, which a per-second quoter does not close by watching the price); (2) the realised-vol estimate has 60 returns instead of 5, so the model is far less noisy than LAG15's; (3) a wide ladder gives many strikes per event, with the long-shot tails the usual place retail quoting is loose. Prior of a pass: 3%.

## Model (one estimator, fixed)
At the look `L = close - 600 s` (the last Kalshi 1 minute candle ending at or before L; the last OKX kline used opens at L - 60 and ends at L). `S` = that kline close. `sigma` = root mean square of the 60 one minute log returns of OKX closes over the 3,600 s ending at L (61 closes; any missing minute means no model), divided by sqrt(60), a per-square-root-second figure. Horizon `tau = 570 s` (centre of the final 60 s averaging window). Spot at the settlement average is lognormal with E = S: `P(YES) = 1 - Phi( (ln(K/S) + 0.5 v^2) / v )`, `v = sigma sqrt(tau)`, K = the market's floor_strike, strictly above. No data after L is used and nothing is fitted to outcomes.

## Entry rule (fixed now, frozen by this file)
Per event (hourly close), consider the strikes with |ln(K/S)| <= 2% (a spot-only filter, also used to limit fetching). A strike is eligible when its Kalshi candle quote at L (latest two sided quote 0 < bid < ask < 1 ending at or before L and not older than 120 s) has spread <= 0.10 and candle volume over the 5 minutes ending at L is at least 10 contracts. Buy YES at the ask if `P - ask - 0.07 ask (1 - ask) >= 0.08`; buy NO at `1 - bid` if `(1 - P) - (1 - bid) - 0.07 (1 - bid) bid >= 0.08` (gap of 8 cents after the fee). **At most one trade per event: the eligible strike with the largest after-fee gap** (chosen without any outcome; lower strike on a tie), because strikes of one hour are one bet. C = 10 contracts, taker at the quoted ask (a quote is not a fill; stated), held to settlement. Scored fee: 7% x C x p x (1-p) rounded up to the cent per order (the shared `lag15.fee`), and x1.2 as a stress. Information-only Try B: gap 0.12 (separately counted). Only one look value (10 minutes) is registered.
**Bans, in advance:** no entry price under 0.20 (no cheap-side-late; the count skipped is printed). **OVERLAPS_L1:** for each asset, if 50% or more of its qualifying trades (counted from entry PRICES alone, before any outcome is used) are priced 0.88 to 0.97, the asset is reported `OVERLAPS_L1` and its outcomes and PnL are NOT computed. The share is reported for every asset. No buy-the-favourite-and-hold rule is intended.

## Windows, Brier and the frozen holdout
Eligible dates sorted, three EQUAL thirds by number of dates: W1 earliest, W2 middle, W3 the frozen holdout (the last third), not read unless W1 and W2 both pass and the Brier line passes. Brier: model P against the outcome and the market mid `(bid + ask) / 2` against the outcome, over all eligible strikes of the group (not only the traded ones). Statistics: date-clustered z (the shared `calibration.cluster_mean_z`).

## Numeric prediction (written before scoring)
The model's Brier is WORSE than the quote mid's in every group (about 0.03 to 0.08 against 0.02 to 0.04); profit factor in each window 0.5 to 1.2; pooled mean per contract -6c to +1c; trades per group 200 to 1,500 over 68 days (about 1 per event at most). The registered claim under test is the opposite: the model beats the quote in Brier at the look and the rule earns profit factor >= 1.5 in each of three time windows with n >= 150 trades. Probability of FALSIFIED or OVERLAPS_L1: about 95%.

## Kill criteria
- `FALSIFIED`: the model Brier no better than the market mid's (pooled), or profit factor under 1.5 after fees in ANY window read (W3 only read if W1 and W2 pass), or not positive at fees x1.2 in any window read, or pooled mean under +2.0c, or date-clustered pooled z under the deflated bar 5.27.
- `NOT_ENOUGH_DATA`: fewer than 150 settled trades pooled for the group (PFs printed anyway; a failed Brier line still falsifies).
- `NOT_YET_FALSIFIED`: all of the above pass. It would permit a forward re-read only, never a trade.
- `NOT_RUNNABLE`: spot or Kalshi candles unreachable. `OVERLAPS_L1`: per asset, above.
Windows, thresholds, look, universe and bans are not changed after the result; no variant is run.

## Overlap with L1
None by construction: hourly markets on SOL, XRP, DOGE and HYPE (none is an L1 series; L1 is KXBTC15M, KXGOLD15M, KXETH15M, KXXRP15M, KXDOGE15M), a spot-model information source, held to hourly settlement, and the 0.88 to 0.97 share test above. It places no order and touches no code in `functions/`, L1 or OICORE.

## Tries
N + 2 per series group (Try A the verdict, Try B information only): SOL, XRP, DOGE+HYPE = +6. Running count about 728,714 + 6 = about 728,720 (deflated z bar about 5.27, unchanged at this precision). Every result is quoted with window, n, cost and N.

## Forward read (not built)
Kalshi hourly candles and OKX klines are retrievable after the fact, so no recorder is needed for a model read at the 10 minute look. History end is 2026-11-02; 30 fresh days give a forward read on or after **2026-12-02**, and only if the history result is not FALSIFIED. A recorder would be needed only to test sub-minute or order book questions (RECORD1 and the book recorder cover those).
