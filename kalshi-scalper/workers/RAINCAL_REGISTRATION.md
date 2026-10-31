# RAINCAL registration (written 2026-10-31, about 3:00 PM CT, BEFORE any recorded row exists, before any NWS forecast was compared with any outcome and before any rain outcome was read)

Owner approved the proposal at 2:45 PM CT on 2026-10-31 (relayed by the main session). The numbers below are the proposal's, unchanged. Two tries; running count about 728,698 after them (728,696 after SPORTS-PRE), z bar about 5.27.

## The question

Are Kalshi's daily "Will it rain in <city>?" markets (`KXRAIN`, 35 US cities) wrong where the National Weather Service's own probability of precipitation (PoP) can see it?

**Loser (counterparty):** casual weather-app bettors who price "will it rain" off a headline icon or a feeling, and thin market makers who pad one side. **Honest prior:** WX1 (the temperature version) found the market BEATS the public forecast; a pass is unlikely. PoP is natively a probability, so no error distribution is modelled (WX1 modelled a temperature error and lost 4.70c). The gap tested is PoP against the station-defined settlement.

## Ledger check (grep of `kalshi-scalper/README.md` on 2026-10-31 for WX1, WX2, WX3, post-peak, WXNEW1, FLB1, THETA1)

NOT repeated, and why this is not one of them:

- **WX1** (daily-high temperature, Oct 13 and the Oct 22 National Blend rerun: FALSIFIED, 1,197 trades, -4.70c, z -4.17, 1 of 7 cities positive). Different variable (temperature, with a modelled error), different series. README line ~3151 says "weather lows, rain and the other cities are not tried: the same calibration gap would apply". That was a statement of expectation, not a run; no rain market was ever downloaded or scored.
- **WX2** (late-day certainty: by 6 hours before the close no quote is left inside 80c to 98c) and **post-peak certainty** (dead, brackets 0.99 / 1.00): both are about information that arrives DURING the day. RAINCAL decides once at 7:00 AM, before the day's weather, and uses a forecast, not an observation.
- **WX3** (ladder arbitrage on the daily-high ladders): rain has one binary market per city, no ladder.
- **WXNEW1** (hourly temperature nowcast from airport readings, and four angles closed in its ledger check): its ledger check (`workers/WXNEW1_LEDGER_CHECK.md` line 55) calls daily rain "REWORD of WX1's mechanism ... NOT_RUNNABLE (not examined further)", citing the Director's Oct 29 note. Rain was never examined. This proposal examines it with a different edge (a probability, not a point forecast).
- **FLB1** (favourites in long-dated, non-sports markets; its weather cell at 72 h was -2.80c on 58 entries) and **THETA1** (favourite drift sold before settlement, 27 cells, all FALSIFIED): both are price-only rules with no outside information; RAINCAL trades only when the price disagrees with an outside forecast, and holds to settlement. Not re-run.

## What was looked at before writing this (disclosure; no outcome was used for any number below)

1. The series list (`/series?category=Climate and Weather`): which series have RAIN in the ticker, their frequency, and, per series, the count of settled markets and total volume. `KXRAIN` (daily) has 1,899 settled markets from 2026-08-25 to 2026-10-31 and 63.4M contracts of volume; split yes 423, no 1,476. That split is a base rate across all cities and days; it was read as a count only and was NOT compared with any forecast. The city-specific daily series (`KXRAINDNYC`, `KXRAINDCHI` and about 25 more) are almost empty: `KXRAINDNYC` has one settled market (2026-09-19, no) and two live ones (2026-10-31, 2026-11-01); the rest hold only far-dated placeholders quoted 0.01 / 0.99 with no volume. They are IGNORED. The monthly, weekly and "custom" rain series are ignored.
2. The 70 open `KXRAIN` markets on 2026-10-31 at about 2 PM CT (events `KXRAIN-26OCT31` and `KXRAIN-26NOV01`, 35 cities each): tickers, close times, rules text, bid, ask, sizes and volumes. A few quotes seen: Miami and Tampa for Oct 31 at 0.99 / 1.00 (rain evidently already fallen), West Palm Beach for Nov 1 at 0.90 / 0.92, most northern cities at 0.00 / 0.01 for Oct 31. These are quotes, not outcomes.
3. The NWS gridpoint response for New York (structure only: `updateTime`, `validTimes`, `probabilityOfPrecipitation.values` with 6 hour `validTime` periods and a long first period), and the station and grid lookup for the 35 airports. The PoP numbers visible for New York on the days after Nov 3 were seen in passing and were not compared with anything.
4. No settled `KXRAIN` market was scored against a forecast; no spread statistic was computed.

## The market, exactly (read from live rules text, 2026-10-31)

- Series `KXRAIN`, one event per day (`KXRAIN-26NOV01` is the market day Nov 1, 2026), one binary market per city (`KXRAIN-26NOV01-WPB`). Ticker suffix = city (ABQ, ATL, AUS, BOS, CHI, CLL, CMH, DAL, DC, DEN, DTW, EWR, HOU, IND, LAX, LEX, LV, MIA, MIN, MKE, NOLA, NYC, OKC, PHIL, PHX, PIT, PVD, SATX, SEA, SFO, SGF, STL, TPA, TTN, WPB).
- **Rule text:** "If the total precipitation at CLI<xxx> in <city> in <date> is strictly greater than 0 inches, then the market resolves to Yes." `CLI<xxx>` is the NWS climate-report site code (CLINYC, CLIORD, CLIDFW, CLIMSP, ...). Source: The Weather Company (weather.com/kalshi) daily report. "Trace amounts (T) and missing daily precipitation values are counted as 0 inches." `strike_type: greater`, `floor_strike: 0`. Directional; can close early if the event occurs.
- **Market day:** the market opens about 09:10 UTC the day before and closes at **midnight local STANDARD time**: close_time 05:00Z (Eastern), 06:00Z (Central), 07:00Z (Mountain and Phoenix), 08:00Z (Pacific). So the market day is the half-open interval **[close_time minus 24 h, close_time)**. On daylight-saving days that is 1:00 AM to 1:00 AM local clock time (the climate day is in standard time all year). From Nov 1, 2026 civil and standard time are the same.
- **Station:** the airport behind the CLI code. Fixed map (ICAO identifier used for the NWS lookup): ABQ KABQ, ATL KATL, AUS KAUS, BOS KBOS, CHI KORD, CLL KCLL, CMH KCMH, DAL KDFW, DC KDCA, DEN KDEN, DTW KDTW, EWR KEWR, HOU KHOU, IND KIND, LAX KLAX, LEX KLEX, LV KLAS, MIA KMIA, MIN KMSP, MKE KMKE, NOLA KMSY, NYC KNYC (Central Park), OKC KOKC, PHIL KPHL, PHX KPHX, PIT KPIT, PVD KPVD, SATX KSAT, SEA KSEA, SFO KSFO, SGF KSGF, STL KSTL, TPA KTPA, TTN KTTN, WPB **assumed Palm Beach International (KPBI), coordinates 26.6832, -80.0956**, because the rule's code CLIDJT is not an airport identifier I could resolve (flagged; NWS has no KPBI station record, so its coordinates are fixed by hand).

## PoP to settlement mapping (fixed now)

- NWS PoP (gridpoint `probabilityOfPrecipitation`) is the probability of measurable precipitation (0.01 inch or more) at a point in the grid cell during the valid period. The market's station reading is a daily gauge total, where a trace counts as 0 and the gauge reads in hundredths. So "greater than 0" equals "0.01 inch or more": the same event, up to the difference between a grid-cell probability and one gauge. That residual mismatch is part of what is tested, not corrected.
- Gridpoint periods are mostly 6 hours (`PT6H`), the first is often long (for example `P3DT23H`). A period `[start, start + duration)` is **in the day** if it overlaps `[look, close_time)`, where look is defined below, so periods already over at the look are excluded.
- **PoP_day = the MAXIMUM of the in-day period values** (a lower bound on the probability of rain at any time that day, with no assumption about independence between periods; the independence union 1 minus product of (1 minus p) is an upper bound and is recorded as information only, not used for the rule). The max biases toward buying NO and away from YES; that is stated here so it cannot be argued after the result.
- Known blind spot, stated now: PoP at the look cannot see rain that fell between the day's start and the look. If rain has been recorded, the market may already be closed or quoted near 0.99; a market that is not `active` at the look is not traded.
- Forecast timestamp: each PoP series carries the gridpoint `updateTime` (the issuance). A poll uses only the forecast that was returned at the poll time; the issuance timestamp is stored beside it so look-ahead can be checked.

## The look, the universe and the data

- **Look (fixed):** 7:00 AM **local standard time**, which is `close_time minus 17 hours` in UTC (12:00Z Eastern, 13:00Z Central, 14:00Z Mountain, 15:00Z Pacific). The decision uses the **first recorded poll at or after the look** with an active quote and a PoP series, and only if that poll is no later than 8:00 AM local (`close_time minus 16 hours`). The recorder polls every city whose local standard time is between 6:00 and 8:00 AM, about every 20 minutes (delays of scheduled jobs are accepted and logged). No poll in the window means no trade for that city and day.
- **Spread window (fixed):** the first 14 recorded UTC days. For each city, the **spread** is yes_ask minus yes_bid at that day's look poll, counted only when both sides are quoted (bid at least 0.01 and ask at most 0.99). **Universe = every city whose median spread over those days is at most 3 cents, with at least 7 such days.** (The 7-day minimum is a detail the proposal left open; it is fixed here, before any data, so a city with almost no two-sided quotes cannot enter on two lucky days.) Chosen on cost alone, before any outcome; applied in analysis, not in the recorder. The universe is applied to ALL days (including the first 14), since no outcome entered its choice.
- **Recorded (every poll in the 6:00 to 8:00 window, all 35 cities from day 1):** poll time and the server Date header, ticker, city, status, yes bid and ask and their sizes, last price, volume, open interest; the NWS station coordinates and grid used, the forecast `updateTime`, `generatedAt` (blank when NWS omits it), `validTimes`, and every PoP period that overlaps the market day with its start, end and value; the station's latest observation (information only, never used by the rule); per-pass request counts and failures. Results (`yes` or `no`, close time, expiration value) are copied from Kalshi's public settled markets by a daily results pass and again by the analysis from the public API; the public API is the record, the copy is a convenience.
- **Stop date (built into the script and the workflow):** nothing is recorded from **2026-12-31 23:59 UTC**. The results pass runs until **2027-01-03 23:59 UTC** so the last days settle. About 60 days of recording remain if the recorder is merged by about Nov 1.
- **Read date (one read, fixed now):** **2027-01-01, after 18:00 UTC (12:00 PM CT)**, the day after the stop date. Markets still unsettled at the read are listed and excluded, not guessed.

## The rule (2 tries, nothing else varies)

At the look, for each city in the universe with an active market, PoP_day = p, YES ask = a, YES bid = b (all in dollars):

- Buy **YES** at the ask if p minus a is **at least 0.08** (a in 0.01..0.99).
- Buy **NO** at the NO ask (1 minus b) if b minus p is **at least 0.08** (b in 0.01..0.99).
- Held to settlement. Fill at the quoted ask at the look, whatever the quoted size (a size under 10 is reported as information, and the result without those trades is printed). One trade per city and day at most.
- **Tries:** the proposal counts this rule as **2 tries** for the deflation (N +2) and does not itemise them. Nothing is invented here: the rule above is the only rule that will be scored, with no variant. The count of 2 is kept for the deflated bar.
- Fees: Kalshi's taker formula 7% x C x p x (1 - p), rounded up to the cent per order at C = 10 contracts, and a second line at fees x 1.2. Net per contract = payout minus price paid minus fee / 10.

## Prediction and kill (fixed before any run)

- **Prediction:** profit factor about **1.05** (range 0.90 to 1.20) on **250 to 450 trades in 60 days** at the 0.08 threshold. Honest read: this is a thin-edge guess; the base rate for a pass is low.
- **NOT_ENOUGH_DATA** if fewer than **150 trades** at the read.
- **FALSIFIED** if any of: profit factor **under 1.2 in either 30-day half** (the halves split the days with a look at the date midpoint, first look to last look); **Kalshi's mid Brier at or below the PoP Brier** (over every city-day in the universe that has a look, outcome 1 for rain; mid = (bid + ask) / 2; PoP_day as defined); **day-clustered z under 3** (clusters = UTC days, because cities share weather); the z not reaching the **deflated bar** at the read (running N about 728,698, two more tries for this family, z bar about 5.27; recomputed from the count at the read).
- `NOT_YET_FALSIFIED` only if every bar holds. A pass permits considering a small capped slot, nothing more; L1 overlap: different tickers, daily settlement, no 15 minute exposure.

## Information, not part of the verdict

Spread by city; share of city-days with a look; trades per city; mean price paid; PoP calibration (reliability table by PoP decile against outcomes); the independence-union PoP used in place of the max; PoP from the earliest forecast of the day versus the one at the look; the share of trades with ask size under 10; Brier of PoP versus mid; outcomes in the markets that were not `active` at the look.

## Limits (stated now)

Quotes are asks at a moment, not fills; a thin book may not fill 10 contracts. The NWS grid cell is not the airport gauge. PoP cannot see rain already fallen at the look. The universe shrinks the sample (a spread of 3 cents or less may hold only a few cities). The 35 cities are not independent days (frontal rain covers many at once), hence the day-clustered z. Rain base rates differ by season: the sample is Nov 1 to Dec 31 only.

## The recorder (research only; its own review branch, not merged by the research session)

`scripts/record_rain.py` and `.github/workflows/record-rain.yml` on branch `claude/v2-recorder-raincal` (review branch for the owner to merge). Public keyless endpoints only: Kalshi's public market data (`external-api.kalshi.com`) and `api.weather.gov`. NWS requires a descriptive `User-Agent` header; that is an identification header, NOT an authentication header, and no key, token or secret is used anywhere. Pushes gzipped files to the `quote-data` branch under `raincal/`, never to main. Nothing places an order.
