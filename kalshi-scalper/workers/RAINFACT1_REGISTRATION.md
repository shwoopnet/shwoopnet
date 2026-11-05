# RAINFACT1 registration (Strategy Research V2 worker, written 2026-11-05 BEFORE any KXRAIN candle, any ASOS precipitation observation or any KXRAIN result was downloaded or scored by this study; discovery only)

Research only: public keyless data, no order, no live code, no promote verb. Code `src/scalper/rainfact1.py`, tests `tests/test_rainfact1.py` (written after this file is pushed).

## Family and idea
Settlement rules and stale quotes on a non-15-minute series. Kalshi's daily `KXRAIN` market ("Will it rain in <city>?") resolves YES if the NWS climate-report daily precipitation at the airport behind the CLI code is **strictly greater than 0 inches** (trace counts as 0), for a market day that runs midnight to midnight LOCAL STANDARD time (so 1 am to 1 am clock time in daylight time). Once the airport gauge has measured at least 0.01 inch in the market day, the daily total can only grow, so the market is **already decided YES by a published, timestamped fact** (the station's hourly METAR precipitation group). This is a structurally riskless buy if, and only if, a quote is still below about 95c after the fact is public. This design is NOT a forecast and NOT an outside-model-vs-quote nowcast: it needs no model. It tests one thing: how fast the quote follows a public observation that settles the contract, and whether the airport observation and the settlement source can disagree.

## Duplicate check (README, workers/*.md grep for KXRAIN, p01i, rain, post-peak, WX2, FAMWX, RAINCAL, CHART1, SPOTD1, EVENT830, NOWCAST1, MENT1 on 2026-11-05)
- **RAINCAL** (forward, one read 2027-01-01): decides once at 7 am from the NWS probability of precipitation; its own text says it "cannot see rain already fallen at the look" and does not trade a market after rain. RAINFACT1 trades only AFTER an observation, with no forecast. Different input, different time.
- **WX2 / post-peak certainty / FAMWX** (temperature): bucket holding the day's high is already 0.99/1.00 hours after the peak, so "observed so far" is priced for TEMPERATURE. That says nothing about rain, a thin market with 35 cities, many of them quoted wide. Not repeated: no temperature market is touched. Prior carried: the temperature version is dead, so this prior is against a pass.
- **CHART1, SPOTD1, EVENT830, NOWCAST1, MENT1**: chart ranks, Spotify, 8:30 releases, macro nowcasts, earnings-call words. None uses KXRAIN or an airport gauge. No overlap.
- Nothing in the ledger scores KXRAIN outcomes against any observation (README "Surprise recorded before data" in RAINCAL and the SCOUT1 note that city rain series are near empty).

## Counterparty
Whoever leaves a resting YES offer (or a stale ask) in a thin daily rain market after rain has been measured at the airport, and the retail buyer who needs a seller at 60c to 95c to hold a decided contract. Why it may not exist: market makers read the same METAR, the market "can close early if the event occurs" (the quote may go to 0.99 within a minute), and the airport gauge is the settlement gauge, so rain observed is rain settled. A thin market with no maker may not update for minutes. The result decides which.

## Fact and timestamp
Iowa Environmental Mesonet ASOS archive (keyless): https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py with `data=p01i` (one hour precipitation in inches, trace set to 0), `tz=UTC`, `report_type=3` and `4`. Each row has a station valid time (the METAR time, usually minute 51 or 53). Mapping is fixed now (RAINCAL's station list, ICAO to IEM id by dropping the K): ABQ ATL AUS BOS ORD CLL CMH DFW DCA DEN DTW EWR HOU IND LAX LEX LAS MIA MSP MKE MSY NYC (Central Park, IEM id NYC) OKC PHL PHX PIT PVD SAT SEA SFO SGF STL TPA TTN, and WPB = PBI (an assumption, RAINCAL flagged it). Kalshi suffix to station: ABQ ABQ, ATL ATL, AUS AUS, BOS BOS, CHI ORD, CLL CLL, CMH CMH, DAL DFW, DC DCA, DEN DEN, DTW DTW, EWR EWR, HOU HOU, IND IND, LAX LAX, LEX LEX, LV LAS, MIA MIA, MIN MSP, MKE MKE, NOLA MSY, NYC NYC, OKC OKC, PHIL PHL, PHX PHX, PIT PIT, PVD PVD, SATX SAT, SEA SEA, SFO SFO, SGF SGF, STL STL, TPA TPA, TTN TTN, WPB PBI. A city whose station has no p01i values at all in the window is dropped (data availability, decided before any outcome is read) and listed.

## Universe (chosen before any outcome)
Every settled `KXRAIN` market whose `close_time` is **before 2026-10-03T16:00:00Z (epoch 1791043200)**, in the cities above, from the series start (2026-08-25). **Frozen last third (close_time at or after the cut) is never listed, fetched or scored**: the code passes `max_close_ts` = cut minus 1 to the listing, and a guard raises if any ticker in memory closes at or after the cut. Halves: D1 = first half of the distinct close dates, D2 = second half. Market day = [close_time minus 24 h, close_time).

## Rule (one parameter set, fixed now)
1. Hourly bucket: per station and UTC clock hour, take the MAX `p01i` among the rows in that hour (a special report repeats the hour's amount, so no double count). Cumulative precipitation for the market day = sum of the bucket values in the day's hours.
2. **t_fact** = the valid time of the first row whose bucket pushes the cumulative sum to at least 0.01 inch. A market-day with no such row has no trigger (it is never traded and never needs a candle).
3. **Decision time** T_d = t_fact + 10 minutes (METAR publication and the IEM ingest are assumed to take at most 10 minutes; later is only more conservative against the idea).
4. **Entry**: the first Kalshi 1 minute candle with `end_ts` greater than T_d + 60 seconds. Price = that candle's `yes_ask` close, taker at the ask, buy YES, 1 contract in the P/L. Needs 0 < bid and ask < 1 (a quote must exist). No quote in the following 120 minutes, or the market already closed/settled before the entry candle = "no quote", counted, not traded. **Trade if ask is at most 0.95** (above that the win is at most 5c and the fee takes about 0.3c to 1c: no room, counted as "already priced").
5. Fee: 7% x C x p x (1 - p), C = 10, rounded up to the cent, divided by 10 (per contract). Stress lines: fees x1.2, and +1c slippage.
6. Outcome: Kalshi `result` for the market (read at scoring only). Net = (1 if yes else 0) - ask - fee.
7. Information only (not part of any verdict): the YES ask at 1, 5, 15, 30 and 60 minutes after t_fact (last candle at or before each), the minutes from t_fact to the first candle with ask at least 0.97, and the count of trigger days in which the market had volume 0 in the 2 hours before t_fact.
8. **Cheap-side compliance**: the standing cheap-side rule is ask 3c to 30c. Stated honestly: the riskless design buys at high prices (up to 0.95); it is a "structurally riskless" design, explicitly justified by the fact above, and is reported in three price groups: A = ask at most 0.30 (the cheap-side-compliant subset: a decided contract still quoted at 30c or less), B = 0.30 to 0.95, C = above 0.95 (already priced, not traded). A and B pooled is the headline set; A is also reported alone.

## Fill realism
Candles carry no depth. Required for any LEAD: ask size at least 10 on a live order book snapshot of the same kind of market today (information only). Historical size is NOT measurable; the volume of the entry minute is reported as a weak proxy. A taker at the ask is assumed fillable for 1 contract only if the candle shows a two-sided valid quote.

## Fetch rule (Kalshi rate limit)
Candles are fetched ONLY for triggered market-days (rule 2), one market at a time over [t_fact minus 5 min, t_fact + 130 min]. No control markets are fetched: the claim is determined by the fact, not by a comparison. A fetch failure after retries is a "not fetched" row, counted and reported, never imputed.

## Pass and kill (fixed now)
- Triggered = market-days with a t_fact. Trades = headline set (A and B pooled).
- **FALSIFIED (quotes follow the fact)** if triggered days are at least 100 and fewer than 30 of them are trades (ask at most 0.95 at entry). Reading: the market is already priced when the observation is public.
- **FALSIFIED (not riskless)** if trades are at least 30 and either the win rate is under 97%, or the mean net after fee is not above +3c in BOTH D1 and D2, or the mean net with fees x1.2 and +1c slippage is not above 0.
- **NOT_ENOUGH_DATA** if triggered days are under 100 (or trades between 10 and 29 with no kill above); states the date count and how many more days of KXRAIN history would be needed. Listed history is what Kalshi serves, so more days arrive only forward; a forward freeze is then named.
- **LEAD** only if trades are at least 30 on at least 8 dates, D1 and D2 both have at least 10 trades and a mean above +3c, win rate at least 97%, and the exact Poisson-binomial probability of that many wins when each trade wins with probability equal to its own ask (the null "price is fair") is at most 6e-8 (z about 5.27, the deflated bar at N about 730,442). A LEAD is a lead, never permission to trade: it would need a forward test with fills.
- The frozen third is opened only if a LEAD stands, and by a separate registered read.

## Numeric prediction (before any outcome)
Trigger days (dev): 200 to 340 of about 1,300 market-days. Entry ask at least 0.97 or no quote in 85% or more of them; trades (ask at most 0.95): 8 to 40; group A (ask at most 0.30): 0 to 3 (those would be cases where the TWC settlement and the airport gauge disagree or where nobody was quoting); win rate of trades 93% to 100%; mean net of trades between 0c and +6c. Median minutes from t_fact to ask at least 0.97: 3 to 20. Verdict: FALSIFIED (quotes follow the fact) about 55%, NOT_ENOUGH_DATA about 35%, LEAD about 10%. **If any trade group has a mean above +10c, or if group A has wins, it is an audit trigger first** (a candle quote that is stale because no one traded, with no fill behind it, is the first suspect; the second is an observation timestamp that lags the real time of the rain by more than 10 minutes).

## N
Two tries (headline set A+B; cheap-compliant subset A scored as its own counted view). Running count about 730,440 -> about 730,442. Deflated z bar about 5.27.

## Limits stated now
- Airport hourly gauge vs the CLI total: both come from the same gauge, but the climate report is quality controlled and could differ (a missing hour, a frozen-precipitation melt). A trigger day that resolves NO is the kill for "riskless" and is listed with its station and hour.
- Rain before the market opened (about 09:10 UTC the day before) cannot matter: the market day starts at close minus 24 h and the market is open all day.
- No data after 2026-10-03T16:00Z is read. The recorder data on the quote-data branch has no KXRAIN rows and is not used.
