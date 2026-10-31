# WXNEW1 step 1: weather ledger check (2026-10-31 Central)

Sources: `README.md` (section names below), `workers/CENSUS_2026-10-30.md` (row "Weather (daily highs and lows)", line 98), `workers/DIRECTOR_2026-10-29.md`. There is no `research/MECHANISMS.md`. Kalshi series data from the public API on 2026-10-31 (`/series?category=Climate and Weather`: 500 listed; 176 are daily, hourly or weekly; settled counts below are markets that closed in the last 120 days, which for daily series is the 68 days Kalshi serves).

## 1. What is already crossed off in weather

| Item | Where | What it tested | Result |
|---|---|---|---|
| WX1 (first, 2026-10-13) | README "Pre-registration: WX1, daily high-temperature markets against a public forecast" | 7 daily-high cities (KXHIGHCHI, NY, MIA, AUS, DEN, LAX, PHIL), Open-Meteo previous-day-1 forecast, walk-forward bias and sigma, 22:00 local the evening before | Registered, listed as tried and failed: weather against public forecasts -3.3c (z -2.5) (README "Tried and failed, as published"; "WX1 ... mechanism" in the Oct 13 notes) |
| WX1 (second, 2026-10-22) | README "Pre-registration: WX1 (2026-10-22), weather daily-high markets against the official blended forecast" and "WX1 result (2026-10-22, run once): FALSIFIED" | Same 7 cities, NBS (National Blend of Models) normal against the market, 12Z run of D-1, price at 20:00 UTC D-1, edge 7c | FALSIFIED: 1,197 trades, mean -4.70c, day-clustered z -4.17, both halves negative, 1 of 7 cities positive. Where the forecast disagrees with the market, the market is right |
| WX2 (never run) | README "Information: why there is no WX2 (late-day weather certainty), 2026-10-13" | Prices only, Chicago: at 8 hours before the close 8 of 351 buckets in 80c to 98c, none at 6, 4, 3, 2 hours | Closed by availability |
| Post-peak certainty | CENSUS line 98 and README "Post-peak weather" (mechanisms list item 4) | Buy the bracket that already holds the day's high | Dead: at 8:35 PM ET NY, MIA, LAX brackets already 0.99 / 1.00 and the rest 0.00 / 0.01. Also WX1 (Oct 22) checked 37 decided LAX cases at 5 times of day, all priced 1.00 |
| WX3 | README "Pre-registration: WX3 ..." and "Result: WX3 (run once on 2026-10-27): FALSIFIED" | Daily-high ladder arbitrage (sum of bucket asks or bids against $1) in 9 cities, 30 days | FALSIFIED: 269 events, 2,698 hours, 1 buy-all lock (1.41c), 0 sell-all |
| DT1 | README "Pre-registration: DT1 ..." | A decision tree on L1 entries | Not weather. Listed on the census weather row by mistake of grouping; it belongs to the closed L1 family (ban of Oct 28) |
| Settlement source | `DIRECTOR_2026-10-29.md` line 9 (grep "Weather Company") | Kalshi's weather series now name The Weather Company as source; Kalshi's settled daily highs vs the NWS climate report (Iowa Mesonet) | Matched on all 67 days for New York and Chicago: "no basis". Only those two cities were compared |
| Rain, daily lows | `DIRECTOR_2026-10-29.md` line 9 | | Called a reword of WX1's mechanism, not run |
| Scout, favourites in the 90c band | README "Market scout result (2026-10-22)" and the scout table (weather 1,289 entries, -0.38c) | Buy the favourite near the top of the book across 76 liquid daily, hourly, weekly series | No edge; weather -0.38c. Also FLB1 (Climate and Weather -2.80c, 58 entries) and the later sweep "weather -4.7c (z -4.2)" which is the WX1 number |
| Census (2026-10-30) | `workers/CENSUS_2026-10-30.md` line 98 | The row for weather | All of the above; "Public: Kalshi candles, NWS, forecast pages; nothing new to record" |

The 15 minute L1 ban of Oct 28 (no favourite-and-hold on 15 minute markets, no filters, exits or sizing) is not about weather and is untouched.

## 2. Weather series on Kalshi today (daily, hourly, weekly; settled in the last 120 days; volume in contracts)

Top of the list by volume. Frequencies: daily 143, custom 141, annual 76, monthly 71, one_off 36, weekly 19, hourly 14 among the 500 listed. 73 of the 176 daily, hourly and weekly series have settled markets in the window; the other 103 (all the international daily highs and lows such as Tokyo, London, Paris, Dubai, plus most "Daily Rain" cities) are listed and idle in the settled history.

| Series | Freq | Settled markets / events | Contracts | Since | Settlement source | Already tested |
|---|---|---|---|---|---|---|
| KXRAIN (daily rain, multi-city) | daily | 1,885 / 68 | 63.2M | 2026-08-24 | The Weather Company | No |
| KXHIGHLAX | daily | 408 / 68 | 33.6M | 2026-08-24 | TWC | WX1, WX3 |
| KXTEMPMIAH (Miami hourly) | hourly | 16,070 / 1,607 | 22.5M | 2026-08-23 | Synoptic Data | No (new: WXNEW1) |
| KXHIGHNY, KXHIGHMIA, KXHIGHCHI | daily | 408 / 68 each | 12.1M, 11.5M, 7.0M | 2026-08-24 | TWC | WX1, WX3 |
| KXTEMPNYCHS (NYC hourly) | hourly | 11,740 / 1,174 | 6.6M | 2026-09-10 | Synoptic Data | No (new) |
| KXHIGHAUS, KXHIGHTPHX, KXHIGHTSFO, KXHIGHTATL, KXHIGHTDAL, KXHIGHDEN, KXHIGHTSEA, KXHIGHPHIL, KXHIGHTHOU, KXHIGHTMIN, KXHIGHTLV, KXHIGHTOKC, KXHIGHTBOS, KXHIGHTDC, KXHIGHTNOLA, KXHIGHTSATX, and 6 smaller (SAN, TTN, EWR, SDF) daily highs | daily | 378 to 408 / 63 to 68 each | 0.15M to 4.7M each | 2026-08-24 | TWC | AUS, DEN, PHIL by WX1 and WX3; MIA, NY, LAX, CHI also; HOU, TDC, TSEA, TATL by WX3 only; the rest not tested, a reword of WX1 |
| KXTEMPCHIHS (Chicago metro hourly) | hourly | 11,930 / 1,193 | 4.6M | 2026-09-10 | Kalshi index / Synoptic | No (new) |
| KXTEMPLAXHS (coastal LA hourly) | hourly | 11,900 / 1,190 | 4.4M | 2026-09-10 | Synoptic Data | No (new) |
| KXLOWT* daily lows (NYC, MIA, DEN, AUS, LAX, PHX, CHI, OKC, DAL, ATL, MIN, HOU, PHIL, DC, LV, NOLA, BOS, SFO, SATX, SEA, SAN, EWR, TTN, SDF) | daily | 390 to 408 / 65 to 68 each | 0.15M to 1.5M each | 2026-08-24 | TWC | No; a reword of WX1 (forecast against the market) and of post-peak certainty (a day's low is known by mid morning) |
| KXRAINWKND (rain this weekend) | weekly | 237 / 10 | 1.4M | 2026-08-24 | TWC | No |
| KXTEMPNYCH, KXTEMPCHIH, KXTEMPLAXH, KXTEMPAUSH, KXTEMPDCH (TWC station hourly) | hourly | 4,204 to 4,282 / 418 each | 0.10M to 0.83M | 2026-08-23 to 2026-09-10 only (19 days; the series stopped) | TWC at KNYC, KORD, KLAX, KAUS, KDCA | No (new: WXNEW1) |
| KXAVGTK* weekly average temperature (12 cities: OKC, AUS, IAH, SAN, DFW, SAT, MSY, PHX, LAS, DEN, ATL) | weekly | 40 / 8 each (ATL 5 / 1) | 0.01M to 0.15M each | 2026-08-24 | TWC | No |
| KXBIGGESTQUAKE | daily | 558 / 58 | 0.66M | 2026-09-02 | USGS | Not weather in the sense of this task |
| KXRAINNYCW, KXRAINDNYC | weekly, daily | 4 / 1, 1 / 1 | under 0.05M | October | TWC | No |

Not listed in the table because they have no settled market in the window or no frequency that repeats: monthly series (rain, snowfall, minimum temperature: about 2 settled months each at most), annual (ski area openings, annual lows, Christmas snow) and custom (hurricanes, named storms). Machine-readable survey of all 176 daily, hourly and weekly series: not committed (data/ rule); the counts above are from it.

## 3. Candidate angles: decision

| Angle | NEW / REWORD | RUNNABLE? | Evidence |
|---|---|---|---|
| (a) Settlement-source mismatch on daily highs (TWC vs NWS) | REWORD of the Director's Oct 29 check, which found no mismatch in 67 days for NY and Chicago | NOT_RUNNABLE as a trade | The mismatch rate is zero where measured, so there is nothing to trade; TWC history for other cities is only the settled bracket itself, and there is no price to compare it with unless the mismatch exists. The question is measured instead inside the hourly TWC-station series (WXH-TWC) as an information line |
| (a') Settlement-source mismatch on the TWC hourly station series (rounded ASOS vs the TWC reading) | NEW | RUNNABLE, small | KXTEMPNYCH, CHIH, LAXH, AUSH, DCH settle on TWC "for coordinates" of an ASOS station; IEM one-minute ASOS for NYC, ORD, LAX, AUS, DCA is public and keyless; the settled value is in `expiration_value`. But only 19 days exist (the series stopped on 2026-09-10); registered as part of WXNEW1 (try WXH-TWC) with its trade counts as a bar, so it may end NOT_ENOUGH_DATA |
| (b) Forecast-update lag (price vs the latest NWS / NDFD / model revision) | REWORD of WX1 (same forecast against the same price; WX1 found the market right, -4.70c, z -4.17, with the 12Z run) | RUNNABLE in principle (IEM NBS archive and Open-Meteo previous-runs serve past runs), not run | A revision-timing variant is the same forecast against the same price at another hour; WX1 already shows the market is at least as informed as the NBS point forecast. Not counted as a try |
| (c) End-of-day bracket vs running observed maximum (fixed look times) | REWORD of post-peak certainty (dead: 0.99 / 1.00) and WX2 (no quote left in 80c to 98c by 6 hours before the close) | NOT_RUNNABLE | No quote left to buy by the time the maximum is observed. International highs, where the market might be slower, have no settled market in the window (Tokyo, London, Paris, Dubai and others: 0 settled markets), so there is nothing to test |
| (c') Intraday nowcast of the HOURLY temperature ladders (last 30 minutes before the close, public one-minute ASOS) | NEW (not crossed off; not post-peak certainty, because the ladder has ten strikes a degree apart and the prices are 5c to 95c at the look time, not 0.99 / 1.00) | RUNNABLE | Settled history: Chicago 52 days, Miami 69 days, NYC and coastal LA 52 days (Synoptic), plus 19 days of five TWC cities; the quotes are 4c to 6c wide, which is the cost this has to beat. Registered as WXNEW1 (2 tries) |
| (d) Monthly or cumulative markets (monthly rain, snowfall, minimum temperature, weekly average temperature) | NEW for weekly average temperature; monthly ones are NEW | NOT_RUNNABLE | Monthly series have about two settled months each; KXAVGTK* have 8 weekly events per city in 68 days (about 40 events across ten cities, correlated, with a week of one weather regime) against bars of 100 / 50 / 30 trades; NOT_ENOUGH_DATA, and could only be met after roughly 25 more weeks (about 2027-04) |
| (e) Daily rain (KXRAIN, 63M contracts) | REWORD of WX1's mechanism (a forecast or observation against the price) per the Director's Oct 29 note; observed rain makes it certain (post-peak shape) | NOT_RUNNABLE | No archived precipitation forecast probability is retrievable for past dates without a key (NBS has a probability of precipitation field, but the settlement is TWC's multi-city rule); not counted |

Verdict of step 1: one NEW and RUNNABLE family (the hourly temperature ladders), registered as two tries in `workers/WXNEW1_REGISTRATION.md` before scoring. Zero new tries are spent on the others.
