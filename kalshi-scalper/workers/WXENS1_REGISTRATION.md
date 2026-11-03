# WXENS1 registration (written 2026-11-03, before any ensemble row, Kalshi quote or outcome was recorded for it; forward-only, no historical holdout exists)

Status: REGISTERED. N +2 (the rule and its control are the two tries; the coordinator keeps the total, about 730,090, z bar about 5.27). Research only: no live code, no `functions/`, no L1, no OICORE, no promote verb. Nothing is scored by the recorder. The recorder is on review branch `claude/v2-recorder-wxens`, for the owner to merge.

## 1. Duplicate check (grep of README.md, workers/FAMWX, WXNEW1*, RAINCAL*, AUDIT1_*; there are no TEMPHR* or other WX* files)

What was already run on the Kalshi `KXHIGH*` / `KXLOW*` daily ladders, and why it died:

- **WX1** (2026-10-13 Open-Meteo previous-day forecast: 7 cities, -3.3c, z -2.5; rerun 2026-10-22 with the NWS National Blend of Models, 1,197 trades over 67 days, **-4.70c, day-clustered z -4.17**, both halves negative, 1 of 7 cities positive). A POINT forecast plus a normal error, taker at the ask. Killed assumption: the market lags a public point forecast. It does not: where the forecast and the market differ the market is right, and the spread (4c to 6c) plus the fee is paid on top.
- **WX2** (late-day certainty): by 6 hours before the close no bracket is left in 80c to 98c. **Post-peak**: brackets already 0.99 / 1.00. **WX3** (ladder arbitrage): 1 lock in 2,698 hours. **WXNEW1** (hourly ladders, ASOS nowcast): Miami -4.08c, z -2.16, market Brier 0.086 against 0.159. **FLB1 / scout**: weather -2.80c / -0.38c. **CAL1** is L1, not weather. **RAINCAL** (rain against the NWS PoP) is a registered forward test with its own recorder, read 2027-01-01; it is rain, not temperature.
- **AUDIT1** ranks weather the most volume rich, least tested lane (only 6 families, all falsified, every one on a point forecast).
- **FAMWX** (2026-11-03) named the ensemble spread as the one different input and left it as "recorder-only, not run": no archive of past ensemble runs exists to score 68 days.

**What is different here, and why it is not a reword.** Every earlier test asked "does a point forecast beat the price at the middle of the ladder". This asks a question about the TAILS: the cheap brackets (3c to 30c) are priced by retail from the headline forecast, and an ensemble gives a calibrated probability for the tail the point forecast cannot. The loser in the mechanism is whoever sells a far-from-forecast bracket at 3c to 15c when the model spread says it is worth three times that. Honest alternative (the likely truth): the quote makers already use the ensembles, the tail is priced right, and the ask minus a 1c to 4c fee floor leaves nothing. The test is cheap to run forward and cannot be run backward.

## 2. Universe, fixed now by rule

- Recorded (14 US cities, the 7 of WX1 plus the 7 next most liquid by the README's own census): New York `KXHIGHNY`, Los Angeles `KXHIGHLAX`, Miami `KXHIGHMIA`, Chicago `KXHIGHCHI`, Austin `KXHIGHAUS`, Denver `KXHIGHDEN`, Philadelphia `KXHIGHPHIL`, San Francisco `KXHIGHTSFO`, Phoenix `KXHIGHTPHX`, Seattle `KXHIGHTSEA`, Dallas `KXHIGHTDAL`, Atlanta `KXHIGHTATL`, Houston `KXHIGHTHOU`, Las Vegas `KXHIGHTLV`. Daily lows (`KXLOW*`) are NOT part of the test (same shape as WX1 plus post-peak; the low is observed by mid morning); not recorded.
- **Tested city set (the rule):** the 8 recorded cities with the highest MEDIAN per-bracket `volume_fp` at the primary look over the first 7 recorded days that have a primary look (ties: alphabetical by series). Chosen on volume alone, before any outcome is read; frozen at that read (`python -m scalper.wxens1 cities`). Trades before the freeze are kept for those 8 cities. Liquidity is what lets a 3c to 30c quote be filled at all.
- Unit: a city-day = one `event_ticker` (one settlement date).

## 3. The look (ONE primary)

**Primary look: 10:00 local STANDARD time on the day BEFORE the settlement date** (the daily market opens at 10:00 ET the day before: the `KXHIGHNY-26NOV04` event opened 2026-11-03T15:00Z). The entry quote is the first recorded poll at or after the look and before 12:00 local standard time; no poll in that window means no trade (counted as NoData, not a price). Standard time is used all year (the market day is a standard-time day). Information only, never a try: 07:00 on the day before (`L1_07`) and 07:00 on the settlement day (`L0_07`) are recorded with the same fields but are not scored for the verdict.

## 4. The probability model (all constants fixed here, nothing tuned on outcomes)

- Inputs at the look: every member of the Open-Meteo ensemble API daily maximum temperature (`temperature_2m_max`, Fahrenheit, local calendar day of the target date) from three models: `gfs_seamless` (GFS ensemble), `ecmwf_ifs025`, `icon_seamless`. Models are weighted equally; within a model every member is weighted equally. A model with no members that run is left out (weights renormalise); fewer than 2 models means no trade for that city-day.
- Bias correction: per city, the mean of (official settled maximum minus the model-pooled ensemble mean) over the trailing 14 settled target dates whose result was recorded BEFORE the look, at the same primary look. Applied only with at least 5 such days; otherwise 0. It is a plain mean, no weights, no refit, no other correction.
- Smoothing: each member value v (after the bias shift) becomes a normal kernel with sd **1.5 F**, fixed. P(bracket) = the model-weighted mean over members of the kernel probability that the whole-degree maximum falls in the bracket: `greater` strike K means maximum at least K+1 (kernel mass above K+0.5); `less` strike K means at most K-1 (mass below K-0.5); `between` floor..cap inclusive (mass between floor-0.5 and cap+0.5). The 1.5 F value is the registered smoothing for under-dispersion and is never changed after the first outcome. Probabilities are not floored or capped.
- Official observed maximum: the settled market's `expiration_value` and result are the settlement truth; the IEM daily summary (`max_tmpf`) is recorded as a cross-check only, never used to score.

## 5. The trade (fixed)

At the primary look, for each city-day: a bracket is **cheap** if its YES ask is between 0.03 and 0.30 inclusive. A cheap bracket is a **candidate** if `p_model >= 3 x ask`. Buy YES at the quoted ask, 1 contract per bracket in the unit-price accounting, **hard limit 0.30**, held to settlement (no exit order, no resting order), at most **2 brackets per city-day** (largest `p_model / ask` first, ties to the lower ask, then alphabetical ticker). Fee: 7% x C x p x (1 - p) rounded up to the cent per order at C = 10, divided by 10; a fees x 1.2 line is reported. Net per contract = payout (1 or 0) minus ask minus fee. **Not tested:** the NO side and any favourite (YES or NO above 0.70) and hold: the owner banned favourite-and-hold research on 2026-10-28. No order of any kind is sent.

**Control = all cheap brackets** (every bracket with ask 0.03 to 0.30 at the same look, no model), same fee, same settlement. The model's job is only to beat its control: information, not part of the verdict, but the selected set must also be above the control's mean net.

## 6. Numeric prediction (before any outcome)

- Take-up: **0.5 trades per city-day** (range 0.2 to 1.0), so about 4 trades a day over the 8 cities (range 1.6 to 8) and **150 trades in about 38 days (range 19 to 94) from the first look**, 300 in about 75 days (range 38 to 188).
- Win rate versus price paid: the realised win rate is **1 to 4 points BELOW the mean price paid** (the market already knows the tails; the ensemble over-states them). Mean price paid about 0.10 to 0.15, win rate about 8% to 12%.
- **PF about 0.75 (0.5 to 1.2); mean net about -2c per contract (-5c to +1c).** Prior that this passes all bars: under 3%.
- Calibration information: the model's Brier on all brackets at the look against Kalshi's mid Brier; predicted: the model is worse in the middle brackets and no better in the tails.

## 7. Bars and verdicts (fixed)

The sample is split BY DATE (settlement date) into two halves with equal counts of trades (the earlier half is the first ceil(n/2) trades in date order, whole days kept together). One read, when the selected set has **300 trades** or on **2027-02-28 23:59 UTC**, whichever comes first, run once with `python -m scalper.wxens1 run`; a second run is refused unless the result file is deleted for a crash fix only.

- `NOT_ENOUGH_DATA` if under **150 trades** at the read; the message prints trades so far, trades per day, and the date 150 would be reached.
- `FALSIFIED` if the mean net after fees is not above zero in BOTH halves, or the profit factor is under 1.5 (sum of net wins over sum of net losses), at 300 trades (or at the stop date with 150 to 299 trades, the same rule).
- Otherwise `NOT_YET_FALSIFIED`, which is a forward candidate only, not a result: it additionally needs the day-clustered z (`calibration.cluster_mean_z`, cluster = settlement date) to be reported against the deflated bar of about 5.27 and the fees x 1.2 line to stay above zero; it permits a second, longer forward test, never a live order. Power rule: the run prints the minimum detectable mean (2.8 x clustered se); if it is above 2c, a `FALSIFIED` is reported as "not shown at this sample size".
- Before the read the only permitted looks are trade COUNTS (`python -m scalper.wxens1 count`), which use the quotes and the model and no outcome. Nobody reads results, win rates or means early.

## 8. Limits (stated before data)

Quotes are asks, not fills; cheap brackets are thin and a 1 contract fill at 3c to 6c may not be there. Forward only: about 8 cities x 1 day, and weather days are correlated across cities (hence the date-clustered z). Open-Meteo's free ensemble API has a daily call limit per IP that a shared runner can hit: a refused call is recorded as a gap and the city-day is dropped (counted), never filled. Station identity (CLINYC versus the airport) is taken from each event's rules text, recorded once per event. Ensembles are 25 to 31 km (GFS) and 9 km (ECMWF, ICON-EPS) grids: a point temperature at a city with a marine or mountain site (Denver, San Francisco, Los Angeles) is biased, which the 14 day correction partly removes.

## 9. Disclosure

Read before writing this: the Kalshi series list; one open `KXHIGHNY` listing (strike layout, ticker form, opening time, no outcome used); the NWS `points` response shape; one IEM daily summary shape. The Open-Meteo ensemble API answered 429 (daily limit) from the research sandbox, so its response shape is taken from its documentation and the parser is written to accept any `member` key naming. No ensemble value, no settlement and no price for a past day was looked at.
