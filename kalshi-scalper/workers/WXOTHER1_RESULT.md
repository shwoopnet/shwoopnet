# WXOTHER1 result (2026-11-04): NOT_RUNNABLE for every non-duplicate family; hourly directional is a DUPLICATE of WXNEW1

Registration `workers/WXOTHER1_REGISTRATION.md` (sha256 1beb6963d35d867bc77fec041686ca2272787a19aacd62cf64b1cda3b744d597, pushed in commit 7985968 before anything else). Census data `workers/WXOTHER1_CENSUS.json`. Owner rule held: cheap side only; no price, candle, forecast or outcome was fetched or joined, so there is no win rate, PF or control result. No favourite-side number exists anywhere in this study.

| Family | Events before the cut | Upper bound on treated | Expected treated (20%) | Reference before the look | Verdict |
|---|---|---|---|---|---|
| hourly directional temperature (10 series) | 12,699 | 23,491 | 4,698 | Open-Meteo hourly forecast exists, but stale next to the live reading | DUPLICATE (WXNEW1), not scored |
| hurricanes and storms | 152 (KXHURCAT 89) | 261 | 52 | NHC archives, not checked | NOT_ENOUGH_DATA |
| rain totals (month, week) | 139 | 273 | 55 | observed-to-date plus historical forecast | NOT_ENOUGH_DATA |
| snowfall (monthly, Christmas, resorts) | 100 | 187 | 37 | observed-to-date plus historical forecast | NOT_ENOUGH_DATA (SCOUT1 WXSNOW1 agrees) |
| monthly/annual temperature rank | 67 | 95 | 19 | none before the look | NOT_ENOUGH_DATA |
| weekly temperature (12 series) | 63 | 95 | 19 | observed-to-date plus historical forecast | NOT_ENOUGH_DATA (8 weekly events a city since 2026-08-18) |
| tornadoes | 39 | 78 | 16 | SPC (source mismatch 38%) | DUPLICATE (COUNT2) |
| degree days / CO2, space weather, sea ice, extreme temperature, water, air quality | 1 to 12 each | 2 to 17 | 0 to 3 | various | NOT_ENOUGH_DATA |
| wind, gust, humidity, heating or cooling degree days (except one Cincinnati series), UV | no series on the public list | | | | NOT_RUNNABLE (nothing to trade) |

Non-hourly total: 613 events, upper bound 1,064, about 210 expected treated, across 12 references (not one test). Nothing is positive, negative or tested.

**Why the one big family is not scored.** The hourly ladders have the events but the mechanism is WXNEW1's (quote makers see the live temperature; WXNEW1's last-30-minute ASOS reading beat the market's Brier 0.159 and still lost at -4.08c in Miami). A forecast made before the look is a worse input on the same ladders. Austin, DC and Boston were not in WXNEW1; they are the same rule on more stations. Cheapest honest test if wanted: Open-Meteo previous-day-1 hourly forecast, Austin and DC ladders (about 3,000 events), one look 3 hours before the close, a new registration with its own N. Today the shared address is out of Open-Meteo's daily quota for the historical-forecast endpoint and Kalshi answers 429 for minutes at a time.

**Forward plan.** No forecast recorder is needed (Kalshi keeps candles; Open-Meteo keeps historical forecasts and observations). Re-run `python -m scalper.wxother1 census CACHE` then `report CACHE` on 2027-04-15; a family becomes runnable at 150 events and 150 expected treated (rain totals about 2027-12, weekly temperature about 2027-09 if the series keep running, snowfall not before winter 2027-28).

**Surprises.** (1) The public list has no wind, gust or humidity series at all; the weather lane is temperature, rain, snow, storms and a few indexes. (2) `KXTEMPAUSH/DCH/CHIH/LAXH/NYCH` have 1,500 to 3,800 events each, more than WXNEW1's ledger reported (it counted 418 from a 120 day window); the "stopped on 2026-09-10" note was about one subset of tickers. (3) The Open-Meteo archive works from the sandbox; the historical-forecast endpoint hit its daily quota.

N +2 (as registered). Code `src/scalper/wxother1.py`, tests `tests/test_wxother1.py`.
