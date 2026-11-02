# SPOTD1 registration (Strategy Research V2, written 2026-11-02 BEFORE any candle was downloaded, any price read or any result computed; research only)

Owner decision relayed by the lead: test new non-L1, non-OICORE families in parallel on existing public data; no further approval needed. Family: Kalshi DAILY US Spotify chart markets, using only Kalshi's own previously settled results as the information source. Nothing here means trade; there is no promote verb.

## Ledger check (stop-if-duplicate)
`grep -i -E "KXSPOTIFY|spotify" README.md` finds only CHART1 (weekly Netflix, "and Billboard/Spotify if runnable", result NOT_RUNNABLE because the outside daily rank history is not archived). KXSPOTIFYD itself was never priced or scored. Not a duplicate. Not L1 (daily, no 15 minute window), not OICORE.

## What was looked at before this registration (disclosure)
Listing only: Kalshi market listings (`/historical/markets`, `/markets` settled) for KXSPOTIFYD, KXSPOTIFYGLOBALD, KXSPOTIFYARTISTD, KXSPOTIFYW, KXSPOTIFY, KXTOPSONGSPOTIFY, KXSPOTIFYTOP, saved to a scratch cache. Printed: counts by series and status, event range, strikes per event, total volume, open and close hours, `settlement_ts` of one market, and `expiration_value` (the chart's number one title) and title text of 2 to 4 sample markets per series. No bid, ask, price or candle was downloaded, no outcome was tabulated, and no model was built.
Findings that shape the design (they depart from the brief, disclosed):
1. **The market is "Top USA Song on Spotify on <date>", a multi-outcome winner market (about 15 titles per event, one YES), not a rank threshold.** The brief's "above/below a rank threshold" is therefore not available. The only chart fact each settled event carries is which title was number one (`result = yes` on exactly one strike; `expiration_value` is the title). The model below is a persistence model of the number one title, not of rank.
2. KXSPOTIFYD: 8,769 markets, 592 events (2024-12 on), volume about 21.8M; KXSPOTIFYGLOBALD (global song): 7,872 markets, 510 events, 2.8M; KXSPOTIFYARTISTD (top artist): 6,752 markets, 449 events, 0.7M. All status finalized, listed under `/historical/markets`. Weekly KXSPOTIFYW and the one-off Wrapped and monthly-listener series are NOT in the universe (weekly has far fewer events; the others are not daily chart persistence).
3. **Settlement lags the chart date.** The market for chart date D opens D-1 about 21:00 UTC, closes D+1 03:59 UTC, and settles around D+1 20:00 UTC (sample `settlement_ts` 2026-07-02 20:36Z for D = 2026-07-01). So at any look on day D the market for D-1 is NOT yet settled in Kalshi's own record. The model therefore sees only events whose `settlement_ts` is at or before the look (in practice chart dates up to D-2). This is stricter than the brief's "last 3 days".

## Counterparty and mechanism
Who loses: retail takers on a winner market who overweight the buzzier new release or the favourite-longshot style long shots, or who underweight how often the same title stays number one. Honest prior that the book already prices persistence: high (it is the obvious statistic, and the market sees the day's early stream counts that the model cannot). Prior of a pass 3%.

## Model (fixed now)
For chart date D with look L: let T = settled number one titles of chart dates d with `settlement_ts` <= L, most recent first; take the first three distinct titles (a1, a2, a3) among the last three settled dates (fewer if repeated). Title key = lowercase, letters and digits only, of the `yes_sub_title` of the strike with result yes (fallback `expiration_value`).
Rates fitted expanding on EARLIER events only (events whose own settlement is at or before L): r_j = (count of earlier events whose number one equalled the j-th distinct title of its own last three settled tops + 0.5) / (earlier events + 1), j = 1..3. Fair(YES) of a strike whose title key equals a_j is r_j. Strikes of other titles are not in the universe. At least 60 earlier events needed (burn-in), else no prediction.

## Universe (cost, liquidity and metadata only)
Try A: series KXSPOTIFYD. Try B: KXSPOTIFYGLOBALD and KXSPOTIFYARTISTD pooled, same rule. Strikes are those whose title key equals a_1, a_2 or a_3 of a predicted event, listed before the look. At the look: a valid two-sided quote (0 < bid < ask < 1) in the last hourly candle ending at or before the look, at most 6 hours old, spread at most 10c. No quote, no trade. No trade-price fallback. (KXSPOTIFYD's volume is the cost/liquidity reason A is first; the other two are the siblings the brief named.)

## Entry rule and time
Look L = 00:00 UTC of chart date D (after the market opens at about 21:00 UTC the day before; before the day's streams exist; the hourly candle used is the one ending at or before L). Buy YES at the ask if fair - ask - 0.07 x ask x (1 - ask) >= 0.08; buy NO at 1 - bid if bid - fair - 0.07 x bid x (1 - bid) >= 0.08. One order of C = 10 contracts per qualifying strike, taker at the quoted ask, held to settlement. Fee 7% x C x p x (1-p) rounded UP to the cent per order; stress line at fees x1.2. Historical candles name fields `close` (live `close_dollars`); the shared `pick` reads both. A quote is not a fill; stated. Information only: gaps 0.05 and 0.12.

## Windows and holdout
Predicted events of each try, sorted by chart date, cut into three EQUAL thirds by event count: W1, W2, W3. **W3 (the last third) is the frozen holdout: not scored unless W1 and W2 both pass**, and the rule is frozen by this file.

## Numeric prediction (written before scoring)
The brief's claim under test: the persistence model beats the market mid in Brier on quotes at the look, and buying the side the model says is underpriced by 8c after fee earns profit factor >= 1.5 in each of three windows with n >= 150 trades. **My prediction is the opposite:** the model's Brier is WORSE than the market mid's (the market at 00:00 UTC already prices the favourite and the new releases), profit factor 0.4 to 1.1 in each window, pooled mean -8c to +1c, fewer than 150 trades in window reads (NOT_ENOUGH_DATA about 55%, FALSIFIED about 42%).

## Kill criteria
- `FALSIFIED`: profit factor under 1.5 after fees in ANY of the read windows, or model Brier no better than the market mid (same strikes, same look), or not positive at fees x1.2, or pooled event-clustered z under the deflated bar 5.27, or pooled mean under +2.0c. Judged per try; the family is falsified if both tries are.
- `NOT_ENOUGH_DATA`: fewer than 150 settled trades pooled over the read windows of a try (PFs reported anyway; the Brier line is still a kill line).
- `NOT_YET_FALSIFIED`: all pass; would permit only a forward quote re-read.
- `NOT_RUNNABLE`: candles unreachable. Windows, thresholds, look and universe are not changed after the result; no variant is run.

## Overlap with L1
None. L1 buys 15 minute crypto, gold and similar markets 6 or 10 minutes before the close. These are daily Spotify chart markets held about a day, a different underlying, series, horizon and information source; they cannot be the same position or window. Nothing here touches `functions/`, live code, L1 or OICORE.

## Tries
Two (A: KXSPOTIFYD; B: the two siblings pooled). N + 2: running count about 728,702 (z bar about 5.27). Every result is quoted with window, n, cost and N.

## Forward read (stated in the result)
New daily events settle every day, and the hourly candles are retrievable after the fact, so no recorder is needed; the date depends on the qualifying-trade pace (in the result).
