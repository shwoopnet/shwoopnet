# EQUAKE1 registration (Strategy Research V2, written 2026-11-02 BEFORE any earthquake outcome, USGS catalog row or price candle was read; research only)

Owner direction relayed by the main session: test new non-L1, non-OICORE families in parallel on existing public data; no new approval needed. Nothing here means trade. Code `src/scalper/equake1.py` is written after this file is pushed.

## Ledger check (stop-if-duplicate)
`grep -i -E "earthquake|usgs|equake" README.md` found nothing before this entry. Not a duplicate.

## What was looked at before this registration (disclosure)
Metadata only. The public series list (tickers, titles, frequency, settlement source) and the settled-market listings of the earthquake series: counts, tickers, open and close times, titles, rules text, strike values, volume. The listing also carries `result` for every market; it was NOT printed and not used. One live candle request (KXBIGGESTQUAKE-10OCT26-5.8, 159 candles returned) was made to see the field names and printed no price. USGS: one count query (268 events, M6+ since 2025-01-01) to confirm the endpoint is reachable. No model was fitted and nothing was scored.
Series found: KXBIGGESTQUAKE (daily, USGS worldwide maximum magnitude in a UTC day, strikes 5.2 to 7.0 in 0.2 steps, "greater or equal", 578 settled markets on 61 days from 2026-09-02, can close early once USGS has finalised the day), KXEARTHQUAKEM (monthly "at least M worldwide before the first of next month", 16 settled markets), KXBIGGESTQUAKEH, KXEARTHQUAKE, KXEARTHQUAKEJAPAN, KXEARTHQUAKECALIFORNIA, KXEARTHQUAKELA, KXEARTHQUAKEM7, EARTHQUAKE, KXEARTHQUAKEJAPANTATSUKI (no settled markets: untestable). **The daily series is only 61 days old, so a result with 150 trades is unlikely; the prediction below says so.**

## Counterparty and mechanism
Who loses: retail traders who price a rare-event tail by feel. Daily world maximum magnitude is close to a Poisson maximum of Gutenberg-Richter events, so P(max >= K) = 1 - exp(-lambda(K)) is knowable to anyone who reads the catalog. Honest prior: the strikes are quoted by market makers who can compute this, so the mispricing, if any, is in the tails and around clustering (aftershock days) which the base rate does not know about. Prior of a pass: 3%.

## Information source and model (fixed now; fitted only on events before each day)
Source: USGS FDSN event service (`https://earthquake.usgs.gov/fdsnws/event/1/query`, keyless CSV), final catalog values, magnitude at least 4.5, worldwide. Model for a UTC day D (Angle A): using only events with origin time before D 00:00 UTC, over the trailing 730 days: lambda45 = count / 730 per day; b = Aki maximum likelihood with the bin correction, b = log10(e) / (mean(M) - (4.5 - 0.05)), magnitudes rounded to 0.1; fair P(max >= K) = 1 - exp(-lambda45 x 10^(-b (K - 4.45))) (the 4.45 is the lower edge of the 4.5 bin, so a 4.5 reading counts). Refit for every day; no other parameter. Known weaknesses, stated now: final-catalog magnitudes can differ from the first USGS values a market sees; the Poisson form ignores clustering (a big quake raises the next days' rate); the market settles on USGS "reported" values at finalisation.

## Angle A rule (KXBIGGESTQUAKE, all fixed now)
1. Eligible day: a settled day with at least 2 strikes listed, with 730 trailing days of catalog.
2. Universe: strikes with model fair between 0.05 and 0.95 (model and strike only, no price, no outcome).
3. Entry time T0 = D 00:00 UTC (the start of the measured period; the market opens about 4 hours earlier). Quote = the first one-minute candle at or after T0, and not later than T0 + 30 minutes, with a valid two-sided quote (0 < bid < ask < 1); no quote means no trade. Spread at most 10c. Candles from the live endpoint use `close_dollars`, historical ones `close` (read through `candlefield.quote_close`, the CPIMENT fix).
4. Edge after the fee: fee per contract f(p) = ceil_to_cent(0.07 x C x p x (1-p)) / C with C = 10. Buy YES at the ask if fair - ask - f(ask) >= 0.08; buy NO at 1 - bid if bid - fair - f(1 - bid) >= 0.08. One order of 10 contracts per qualifying strike, held to settlement. Fees 7% x C x p x (1-p) rounded up per order; stress fees x1.2.
5. No look-ahead: the model sees only events before T0; the entry is the first price at or after T0. The close time of the market is never used (an early close reveals the outcome).
6. Windows by quake date: the eligible days sorted by date, cut into three equal parts (first third DISCOVERY, middle third VALIDATION, last third HOLDOUT, the remainder day going to the last). The HOLDOUT is frozen untouched (no trade list, no PF) until discovery and validation both pass.

## Angle B rule (KXEARTHQUAKEM, monthly; fixed now)
Fair = 1 - exp(-lambda45 x 10^(-b (M - 4.45)) x days) with the same trailing fit at the market's open time and days = open to close in days; entry = first valid two-sided candle at or after the market's open time (within 6 hours), spread at most 10c, same edge 0.08 after fee, YES at the ask or NO at 1 - bid, C = 10, held. Window: all 16 markets pooled as one set (no split is possible). **Expected NOT_ENOUGH_DATA; registered so it cannot be looked at afterwards as a free try.**

## Judging and kill criteria (verdict words only)
Profit factor (PF) first; n is independent days (z clustered by day with `calibration.cluster_mean_z`), not strikes.
- `FALSIFIED` if any of: PF under 1.5 after fees in discovery or in validation (each with at least 50 trades, see below) or, if both pass and the holdout is read, in the holdout; not positive at fees x1.2; Brier of the model no better than the Brier of the market mid at entry; pooled day-clustered z under the deflated bar 5.27; pooled mean under +2.0c.
- `NOT_ENOUGH_DATA` if the pooled trade count is under 150 (the registered minimum), or discovery has under 50 trades, or validation under 50. The PFs are reported anyway but decide nothing.
- `NOT_YET_FALSIFIED` only if every line passes in all three windows; it permits a forward re-read, never a trade, and there is no promote verb.
- `NOT_RUNNABLE` if the data cannot be reached from the sandbox.
Windows, edge, spread cut, entry time, model window and universe are not changed after the result.

## Numeric prediction (written before scoring)
The base-rate probability beats the market price in Brier score, and a rule that buys the side the model says is under-priced by at least 8c after the fee earns PF >= 1.5 in each of three windows. My own forecast, stated against the owner's: Brier of the model within 0.01 of the market's and probably worse (market 0.5 to 0.7 of the time right on the tails); 30 to 120 trades on 61 days, so `NOT_ENOUGH_DATA` (about 70%) or `FALSIFIED` (about 27%); pass 3%.

## Holdout, overlap with L1, tries
Holdout: the last third of eligible days, frozen as in rule 6. Overlap: none; earthquakes are not a 15 minute series and no L1 or OICORE market is touched. Tries: two (Angle A, Angle B), one rule each; N + 2, running count about 728,700, deflated z bar about 5.27. The information thresholds (5c, 12c) and the fees x1.2 line are shown, not tried. Quote every result with window, n, cost and N.

## Forward read
Needs 150 settled trades; the daily series yields about 1 new day per day at about 10 strikes. The trades per day will be known from the result; at that rate, the forward date is written into the result file. No recorder is needed if the historical candle endpoint keeps the finished days (Kalshi retains settled-market candles); if it does not, a recorder of the first quote at 00:00 UTC for each strike would be about five lines.
