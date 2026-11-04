# WXOTHER1 registration: weather and climate families other than daily highs, daily lows and daily rain, cheap side only (written 2026-11-04, before any price, candle, forecast or outcome of these families was read; 2 tries, running count about 730,345 before, +2 after, z bar about 5.27)

Research only. Nothing places an order. No live code, no `functions/`, no L1, no OICORE, no promote verb. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE, DUPLICATE. **Owner rule (strict): cheap side only (ask 3c to 30c). No favourite-side result is computed or printed. No 15 minute crypto or gold candle is used.**

## 1. Duplicate check (README.md and workers/ searched for WX1, WX2, WX3, WXNEW1, WXENS1, WXLOW1, WXLOCK1, RAINCAL, FAMWX, OVERROUND1, CALIB1, USWEEP1/2/3, COUNT2, EQUAKE1, SCOUT1, SLOWSTAT1)
Covered and excluded by name (daily highs `KXHIGH*`, daily lows `KXLOW*`, daily rain `KXRAIN`, `KXRAIND*`): WX1 twice (point forecast, -3.3c then -4.70c z -4.17), WX2, WX3, post-peak, WXENS1 (forward-only ensemble), WXLOW1, WXLOCK1 (observed-high lock, zero trades), RAINCAL (daily rain vs the NWS PoP, read 2027-01-01), FAMWX, OVERROUND1 (weather temperature events by overround, FALSIFIED), CALIB1 (Weather negative in every ask bucket, 1,631 events). Remaining families, with the nearest tested item:

| Family (series) | Nearest tested item | Why it is or is not a duplicate |
|---|---|---|
| Hourly directional temperature (`KXTEMP*H`, `KXTEMP*HS`: NYC, Chicago, Chicago metro, LA, coastal LA, Miami, Austin, DC, Boston) | **WXNEW1** (ASOS nowcast, last 30 minutes, same ladders, Miami -4.08c, z -2.16, market Brier 0.086 against 0.159) | the same ladders priced against a better, later reference; a forecast made before the look is stale next to a quote maker who sees the live temperature. **DUPLICATE in mechanism**, not scored (see section 5) |
| Weekly temperature (`KXAVGTK*` 11 cities, `KXAVGTATL`, `KXHEATAPHX`, `KXWEEKHT*`) | WXNEW1 ledger check (d), SCOUT1 hypothesis WXAVGT1 (listed, never run), WX1 (daily forecast vs market) | new input (a week's running average), never scored |
| Monthly snowfall (`KX*SNOWM`, 24 series incl. Christmas, ski-resort and storm series) | SCOUT1 WXSNOW1 (listed, never run: "fails the census") | never scored |
| Monthly and weekly rain totals (`KXRAIN*M`, `KXRAINNYCW`, `KXRAINWKND`) | RAINCAL (daily, not monthly), SCOUT1 (KXRAINNYCM line) | cumulative totals, never scored |
| Monthly tornado count (`KXTORNADO`) | **COUNT2** (NOT_ENOUGH_DATA, SOURCE_MISMATCH: the SPC daily sum did not match the settled value 38% of the time) | **DUPLICATE** |
| Monthly and annual temperature rank (`KXHMONTH`, `KXHMONTHRANGE`, `KXGTEMP`, `KXAVGTEMP`, `KXTEMPMON`, `KXHOTYEAR`, `KXTEMP`) | none | never scored |
| Monthly or annual extreme temperature (`KXMINNYC`, `KXHOLIDAYT*`, `KXMONTHLOWMSN`, `KXYEARLOW*`, ...) | none | never scored |
| Hurricanes and named storms (`KXHUR*`, `KXTROPSTORM`, `KXNAMEDSTORM`, 36 series with a settled market) | none | never scored; most are one-off landfall questions |
| Air quality `KXAQICITY`, sea ice, Lake Mead / Michigan temperature, CO2, geomagnetic storm and flare | none (earthquakes are EQUAKE1, left out) | never scored |
| Wind speed or gust, humidity, heating degree days (other than one Cincinnati series `KXHDDCVG`), UV, wildfire | none | **no such series exists** on the public series list: the full list (15,687 series, all categories) was searched by title for wind, gust, humid, degree day, heating, snow, hurricane, tornado, air quality, sea ice, anomaly, storm, weather, fire, flood; every hit is political, sports or commodity or is a series below |

## 2. Census (listings and close times only: no price, no candle, no result was read; frozen cut 2026-10-03T16:00Z)
Method: `/series?category=Climate and Weather` (501 series) plus title hits in category World (`KXSEAICE`, `KXGSTORM`, `KXXFLARE`), minus the covered and non-weather names (`COVERED`, `NOT_WEATHER` in `src/scalper/wxother1.py`): 252 candidate series; settled markets closing before the cut from `/historical/markets` and `/markets?status=settled`. Counts are events (an `event_ticker`), settled markets, events with at least one market of 20 or more contracts traded, and the **upper bound on treated trades** (per event at most 2 markets that traded 20 or more contracts). Expected treated is taken as 20% of that upper bound (an assumption, generous: the 3x model ratio on a cheap side is rarely met; TENNIS1 used 2%). Machine-readable: `workers/WXOTHER1_CENSUS.json`.

| Family | Series with markets | Events | Traded events | Upper bound | Expected treated (20%) | Close dates |
|---|---|---|---|---|---|---|
| hourly directional temperature | 10 | 12,699 | 12,036 | 23,491 | 4,698 | 2026-03-11 to 2026-10-03 |
| hurricanes and storms | 36 | 152 | 144 | 261 | 52 | 2021-08 to 2026-10 |
| rain totals (month, week) | 13 | 139 | 139 | 273 | 55 | 2024-03 to 2026-10 |
| snowfall | 24 | 100 | 99 | 187 | 37 | 2021-12 to 2026-04 |
| monthly/annual temperature rank | 7 | 67 | 66 | 95 | 19 | 2021-11 to 2026-09 |
| weekly temperature | 12 | 63 | 53 | 95 | 19 | 2026-08-18 to 2026-09-28 |
| tornadoes (COUNT2) | 1 | 39 | 39 | 78 | 16 | 2023-08 to 2026-10 |
| degree days / CO2 | 1 | 12 | 12 | 13 | 3 | 2021-07 to 2022-07 |
| space weather | 2 | 12 | 12 | 14 | 3 | 2021-11 to 2025-11 |
| sea ice | 4 | 10 | 10 | 17 | 3 | 2021-10 to 2026-10 |
| monthly/annual extreme temperature | 3 | 9 | 9 | 14 | 3 | 2021-12 to 2026-07 |
| water temperature / level | 3 | 9 | 9 | 15 | 3 | 2021-11 to 2026-07 |
| air quality | 1 | 1 | 1 | 2 | 0 | 2026-07-19 |

All the non-hourly families together: **613 events, upper bound 1,064, expected treated about 210**, spread over 12 different references; that sum is not one test (no common reference, error model or look) and each family alone is under 150 events and under 60 expected treated. Largest single families: rain totals 139 events (the biggest series KXRAINNYCM 32), hurricanes 152 (KXHURCAT alone 89, one-off storm questions), snowfall 100 (KXSNOWNYM 17), tornadoes 39.

Reference with a forecast made before the look (all free, keyless, reachable from this sandbox on 2026-11-04):
- Weekly temperature, monthly snowfall, monthly rain, extreme and rank series: Open-Meteo `historical-forecast-api` keeps past model runs (and `archive-api` gives the observed-to-date part, reachable now; the historical-forecast endpoint answered "daily limit exceeded" from this shared address today). A running total or running average to date is a fact; only the rest of the period needs a forecast. **Exists.**
- Hurricanes and storms: NHC HURDAT2 for outcomes, NHC archived advisories for forecasts: reachable in principle, heavy, not checked. Tornadoes: SPC (COUNT2: source mismatch). Sea ice: NSIDC daily extent, no forecast before the look. Rank series: NOAA/NASA/Copernicus monthly anomalies, published after the month: **no forecast before the look.** Space weather: SWPC Kp, no archived forecast checked. Air quality: AirNow needs a key. Water level or temperature: USGS/USBR, no forecast.

## 3. Rule (fixed now; scored only if the census said RUNNABLE, which it does not for a non-duplicate family)
Per family, one fixed look (24 hours before the close for weekly and monthly periods, using the part of the period already observed). Reference: the observed-to-date value from `archive-api` plus the Open-Meteo `historical-forecast-api` value for the rest of the period, a normal error with bias and sd fitted on the FIRST TWO THIRDS of the family's events by close time only. Trade: the side with ask in [0.03, 0.30] whose model probability is at least 3 x the ask, hard limit 0.30, 10 contracts, at most 2 markets per event, held to settlement, fee 7% x C x p x (1-p) rounded up per order (`fee()`; x1.2 stress line). **No favourite side is ever considered** (`pick()` only returns a side with ask at most 0.30). Control: every cheap strike of the same series at the same look. Event-level cluster; halves split at the median close time of treated events. Frozen last third (from 2026-10-03T16:00Z) never fetched or joined.

## 4. Numeric prediction (before any join)
The census shows no family reaching 150 events, so the registered verdict is NOT_RUNNABLE for each, and NOT_ENOUGH_DATA with a forward date. If a family were scored, the prediction would be CALIB1's: win rate 0.4 to 0.65 of the price, mean net -2c to -6c, PF 0.4 to 0.9, prior of a pass under 2%.

## 5. Kill rules and the hourly family
FALSIFIED if (n >= 150 treated) the mean net after fees is not above 0 in BOTH halves or PF is under 1.5. NOT_ENOUGH_DATA under 150 treated trades or 150 events. NOT_YET_FALSIFIED only if both halves positive, PF >= 1.5 and event-cluster z >= 5.27 (a forward test, never a trade). **Hourly directional temperature** is the only family with the events (12,699) and is NOT scored here: it is a DUPLICATE of WXNEW1 in mechanism (the same ladders; WXNEW1's reference, the live ASOS reading in the last 30 minutes, strictly dominates a forecast made before the look). Its untested stations (Austin, DC, Boston) are the same rule on more stations. If the coordinator wants it anyway, the cheapest honest test is the Open-Meteo previous-day-1 hourly forecast against the Austin and DC ladders (about 3,000 events, one look 3 hours before the close, one candle request per event), which needs tomorrow's Open-Meteo quota and a free Kalshi limit; it would be a new registration with its own N.

## 6. Forward plan
No recorder of forecasts is needed: Kalshi keeps settled candles and Open-Meteo keeps historical forecasts and observations. Re-run `python -m scalper.wxother1 census CACHE` and `report CACHE` on 2027-04-15 (after the snow season; rain, weekly temperature and rank series keep adding). Expected by then: snowfall about 190 events if the 24 series reopen each winter month, weekly temperature about 12 events a week of the season, rain totals about 80 a year. A family becomes runnable only at 150 events with an expected 150 treated, which is rain totals about 2027-12, weekly temperature about 2027-09 (if the series keep running), snowfall not before winter 2027-28.

## 7. Count
Two tries (one rule across the non-duplicate families, one hourly-family duplicate declaration); no outcome is joined. Registered N +2.

Code `src/scalper/wxother1.py` (census, report, fee, model probability, cheap side picker), tests `tests/test_wxother1.py` (synthetic, passing before this commit).
