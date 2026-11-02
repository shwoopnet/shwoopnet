# WTIW1 registration (Strategy Research V2, written 2026-11-02 BEFORE any candle was downloaded, any price read or any result computed; research only)

Owner decision relayed by the lead: test new non-L1, non-OICORE families in parallel on existing public data; no further approval needed. Family: Kalshi range and threshold markets on a futures, yield or FX level at a known horizon. Nothing here means trade; there is no promote verb.

## Ledger check (stop-if-duplicate)
`grep -i -E "KXWTIW|KXTNOTEW|weekly range|Treasury 10Y|WTIW|KXUSDJPY" README.md` found nothing. (The README mentions Treasury 15 minute markets and the lead's crude oil rate checks only as different markets.) Not a duplicate. Not L1 (no 15 minute window, held 1 to 7 days), not OICORE.

## What was looked at before this registration (disclosure)
Listing only: Kalshi market listings (historical and live settled) for KXWTIW, KXTNOTEW, KXUSDJPY (and their older prefixes WTIW, TNOTEW, USDJPY), saved to a scratch file under `data/wtiw1/` (not committed). Printed: counts by series, strike type, result and source, event count, open and close times, the `rules_primary` text and the `yes_sub_title` format of one market per type. FRED CSV downloads (DCOILWTICO, DGS10, DEXJPUS) were checked for reachability by printing the line count and last row. No bid, ask, price or candle was downloaded and no model was built. Facts that shape the design:
1. Each event is a ladder of about 15 strikes: one "or above" strike, 13 range ("between") strikes and one "or below" strike, parsed from `yes_sub_title` ("$99.00 to $99.99", "4.67% or above", "161.500 to 161.749"); `floor_strike` is empty for some markets, so the text is the source.
2. History: KXWTIW/WTIW 166 weekly events (2022-09 to 2026-10), KXTNOTEW/TNOTEW 170 weekly events (2023-02 to 2026-06), KXUSDJPY/USDJPY 1,238 daily events (2022-08 to 2026-11). Settlement: WTI daily settlement of the front contract on the Friday, the 10 year par yield on the Friday, the Dollar/Yen price at 10 AM EDT.
3. FRED is reachable with curl (urllib is not needed).
4. The hourly KXWTIH and KXSILVERH were not examined and are not tried.

## Counterparty and mechanism
Who loses: retail traders who price the WIDTH of the distribution (volatility) of a futures, yield or FX level over a known horizon by feel, over-paying for the tails of a ladder or under-paying for the middle. **Honest prior that this is priced in: very high.** These are large markets (about 25M, 10.7M and 10.7M contracts) on instruments whose live level and implied volatility professional makers watch tick by tick; MORTGAGE1 and TSA1 both lost to the market in Brier, and the market at the look already knows the live price while a model built on daily public history knows only the last published daily close. A simple trailing-volatility model is expected to lose to the market mid in Brier. What would make this one different: the look is placed immediately after the market opens (at open plus 4 hours), when the level moved least since the last published daily close and the makers' quotes may be stale or wide; if that is true the model's information disadvantage is smallest here. Prior of a pass: 3% per series.

## Model (ONE volatility estimator, fixed now)
Trailing **20 observation** realised volatility (not EWMA): the sample standard deviation of the last 20 daily changes of the FRED series (log changes for DCOILWTICO and DEXJPUS, level changes in percentage points for DGS10), using observations dated at or before the level date, missing days ('.') skipped. Mean change zero. Fitted on nothing else (no parameter is tuned).
- Level date d0 = the last FRED observation dated on or before the look's UTC date. Level X0 = that observation.
- Horizon h = the number of weekdays from d0 (exclusive) to the market's close date (inclusive). WTIW and TNOTEW: 5 for a market opened after Friday's close; KXUSDJPY: 1.
- Terminal distribution: WTI and USD/JPY lognormal, ln X_T ~ N(ln X0, (sigma sqrt(h))^2); 10 year yield normal, X_T ~ N(X0, (sigma sqrt(h))^2).
- Fair for each strike: the probability of the strike's interval after widening each bound by half the strike's tick (the tick is 10 to the minus number of decimals in the title: 0.01 for WTI and the yield, 0.001 for USD/JPY): "A to B" is [A - tick/2, B + tick/2]; "A or above" is X_T >= A - tick/2; "A or below" is X_T <= A + tick/2.
- An event needs 20 earlier changes, else it is a burn-in and is not traded.

## Universe (cost and metadata only)
Series: KXWTIW + WTIW, KXTNOTEW + TNOTEW, KXUSDJPY + USDJPY, each its own try. Strikes of events with a prediction whose model fair is between 0.10 and 0.90 (no price used). At the look: a valid two-sided quote (0 < bid < ask < 1) in the last hourly candle that ends at or before the look, at most 6 hours old and not before the market opened, and a spread of at most 10c. No quote, no trade. No trade-price fallback.

## Entry rule and time
Look L = open_time + 4 hours (the market's own open timestamp). Nothing published after L is used. (FRED publishes with a lag, so the daily level is not literally downloadable at L; it equals a number already public at L: the prior settle, the noon fix. Disclosed, and this favours the model.)
Buy YES at the ask if fair - ask - 0.07 x ask x (1 - ask) >= 0.08; buy NO at 1 - bid if bid - fair - 0.07 x bid x (1 - bid) >= 0.08. One order of C = 10 contracts per qualifying strike, taker at the quoted ask, held to settlement. Fee 7% x C x p x (1-p) rounded UP to the cent per order; stress line at fees x1.2. Information only (not tried): gaps 0.05 and 0.12. Historical candles use `close` (live `close_dollars`); the shared `pick` reads both. A quote is not a fill; stated.

## Windows and holdout
Per series, events with a prediction sorted by date and cut into three EQUAL thirds by event count: W1, W2, W3. **W3 is the frozen holdout: not scored unless W1 and W2 both pass and the model Brier beats the market's.** The rule is frozen by this file before W1 is scored.

## Numeric prediction (written before scoring)
The brief's claim under test: the model beats the market price in Brier, and buying the side the model says is under-priced by at least 8c after the fee earns profit factor >= 1.5 in each of three time windows with n >= 150 trades. My prediction is the opposite: model Brier WORSE than the market mid on every series (model 0.06 to 0.12 against the mid 0.03 to 0.07 over the traded universe); profit factor in each window 0.3 to 1.1; pooled mean per contract -8c to 0c; weekly series trade counts under 150; USD/JPY (1,238 events) the only series likely to reach 150 trades.

## Kill criteria (per series)
- `FALSIFIED`: profit factor under 1.5 after fees in ANY of the three windows (W3 only if read), or the model Brier no better than the market mid's (same strikes, same look), or not positive at fees x1.2 in any read window, or pooled event-clustered z under the deflated bar 5.27, or pooled mean under +2.0c.
- `NOT_ENOUGH_DATA`: fewer than 150 settled trades pooled over the read windows (PFs reported anyway; the Brier line is still reported).
- `NOT_YET_FALSIFIED`: all of the above pass. It would permit only a forward quote re-read, never a trade.
- `NOT_RUNNABLE`: candles or FRED unreachable. Windows, thresholds, look and universe are not changed after the result; no variant is run.

## Overlap with L1
None. L1 buys 15 minute crypto, gold and similar markets 6 or 10 minutes before the close. These are weekly or daily commodity, yield and FX range markets held 1 to 7 days; different underlying, series, horizon and information source; they cannot be the same position or window. Nothing here touches `functions/`, live code, L1 or OICORE.

## Tries
Three (one per series: WTI weekly, Treasury 10 year weekly, USD/JPY daily). N + 6 at the lead's rate of +2 per series: running count about 728,706 (z bar about 5.27). Gap thresholds shown for information are not tries. Every result is quoted with window, n, cost and N.

## Forward read
Stated in the result file (trades per week times weeks to 150). Candles are retrievable after the fact, so a recorder is not needed unless the result says otherwise.
