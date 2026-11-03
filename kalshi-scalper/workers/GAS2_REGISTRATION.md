# GAS2 registration: cheap-side AAA gas strikes against a persistence model (written 2026-11-03, before any candle, market listing or outcome of any KXAAAGASD* series was downloaded by this study)

Worker GAS2 for "Strategy Research V2". Research only: public keyless data, no order, no live code, no promote verb. Code `src/scalper/gas2.py`, test `tests/test_gas2.py`.

## Duplicate check (done first, verdicts carried, nothing re-scored)
- **GAS1** (README 2026-10-21, national `KXAAAGASD`): persistence model, bought the model's FAVOURITE side. 184 entries, -7.50c, z -2.27, Brier model 0.2351 vs market 0.0826: FALSIFIED. Lesson carried: a naive persistence model is much worse calibrated than the quotes. GAS2 differs in side (cheap side only, the owner banned favourite-and-hold), in universe (17 series, not one), in the model (a pooled AR(1) on changes with day-of-week effects and an empirical residual shape, not a normal), and in the requirement (model probability at least 3 x the ask).
- **GAS1-F** (forward, favourites in the L1 band, read 2026-11-22) and the 67-day information look (2026-10-22): favourites at ask 0.88 to 0.97 won 86.6% against 0.931 paid. The same look found longshots quoted 3c to 14c winning only 0.8% to 3.8% (the cheap side is OVERPRICED on average). No test was registered on it; GAS2 is that cheap side, but only where a model says the day's distribution puts real mass.
- **USWEEP1** (workers/USWEEP1_RESULT.md): state gas ladder favourites have 85c to 97c asks over bids of 10c or less (stale quoting); carried: fill realism must be checked.
- **COMM1 / CMD1** (commodity daily ladders from spot): FALSIFIED. **FLB1** (long-dated non-price favourites): FALSIFIED. **OICORE_SHAPE_INVENTORY**: no gas row on the cheap side. Weekly `KXAAAGASW` with an RBOB term (econ-new A, README): NOT_ENOUGH_DATA, PF 0.07 and 0.27, so the market at the look already sees the daily AAA print; carried as a warning that the model's information is no better than the quote's.
- No registered test of the cheap strike with an empirical daily-change model on the state ladders exists.

## Universe (by rule, before outcomes)
`KXAAAGASD*` series (national and states) whose entry in `data/scout_census.json` shows at least 40 distinct close dates (a structural count, no outcome): the 17 tickers in `workers/GAS2_SERIES.json` (written before any download). At fetch a series is dropped if it has fewer than 40 distinct close dates, and a market-day is dropped at the look if the decision candle has no two-sided valid quote (0 < bid < ask < 1).

## Daily average reconstruction (the AAA series from Kalshi's own settled ladders)
For each series and close date, the event's settled value is the `expiration_value` carried by its settled markets (GAS1 established this is the published AAA number). If a market lacks it, the value is bracketed by the ladder: the largest strike that settled "yes" (value above it) and the smallest that settled "no" (value at or below it); the value is the bracket midpoint and a bracket wider than 0.003 is not used. Markets are "greater than K"; the settled value V is above K iff result is yes. A day whose previous event did not close 24 hours earlier (plus or minus 1.5 hours) has no change for the model.

## Walk-forward, frozen third
The distinct close dates of the universe are sorted; the FIRST TWO THIRDS (floor) are development, the last third is frozen. **Rows for frozen dates are dropped inside the fetch function before anything is written to disk: no candle, no result, no value of a frozen date is stored or scored.** (The market listing returns results with it, so the only way to keep it unread is to discard at fetch; the code does this and prints only the count of dropped rows.) Development is cut by date into halves A (first half of scored dates) and B.

## Model (fixed now, nothing else is fitted)
Change d_t = V_t - V_{t-1} for a series. For scored date t (needs at least 14 earlier dates with a change available across the universe), fit on dates strictly before t, pooled over all universe series: d_t = a + b d_{t-1} + dow_t (OLS, 6 day-of-week dummies for the date's weekday in US Eastern, Monday base). Residuals r are scaled per series: s_series is the population sd of that series' residuals on the fitting dates, floor 0.0010. The pooled standardised residuals e = r / s_series are the empirical shape (at least 200 needed, else the day is not scored). Prediction: V_t = V_{t-1} + a + b d_{t-1} + dow_t + s_series e_j for every pooled e_j; P(V_t > K) is the share of those that exceed K. Nothing is smoothed. The probability for the NO side is 1 minus it.

## Look and rule (fixed now)
Look: 8 hours before the market close (the evening before settlement, afternoon US Eastern): the last hourly candle ending at or before close minus 8 h and not older than one candle, with yes_bid and yes_ask closes both valid. Entry is taker at the ask of that candle (YES: yes_ask; NO: 1 - yes_bid), 1 contract in the P/L, held to settlement. Cheap side: a side whose ask is in 0.03 to 0.30 (HARD LIMIT 0.30, never above). Take it if the model probability for that side is at least 3 x the ask. At most 2 entries per series-day (highest probability / ask ratio first). **Control**: every cheap-side market in the band 0.03 to 0.30 at the look (no model), one per market, same fee, same halves.
Fee: 7% x C x p x (1 - p), rounded up to the cent, C = 10, divided by 10 (per contract), stress x1.2. Clustering: by close date (all gas series move together, so the effective sample is days, not trades).

## Size and fill realism
Candlesticks carry no depth. Required: ask size at least 10 contracts. Historical: **not measurable** from candles; the decision candle's volume > 0 is reported as a weak proxy (subset result). Current: one snapshot of the live order book (`/markets/{ticker}/orderbook`, 1 request per series, the nearest open ladder) gives size at the ask and bid-ask spread today; information only. A taker at the ask with 1 contract is assumed fillable only if the candle shows it quoted (two-sided valid).

## Pass / kill (fixed now)
- Needs n >= 150 model trades on development. Under 150: **NOT_ENOUGH_DATA**, stating the days to go (the scored dates and trades per scored date give the date when 150 is reached) and a dated forward freeze: the frozen third plus new dates are read once, on or after the date stated in the result (candles stay about 69 days).
- **FALSIFIED** if n >= 150 and the mean net after fees is not above 0 in BOTH halves, or profit factor (sum of wins over sum of losses, after fee) is under 1.5.
- Otherwise NOT_YET_FALSIFIED: permission to propose a capped probe (1 contract, ask <= 0.30, stop after 40 fills with PF under 1.0, worst-day dollars stated), never evidence of an edge. A positive claim must also clear the deflated bar (z about 5.27 at N about 730,100) to be called more than a lead.
- Also reported (information): win rate against mean price paid for model trades and control, by ask bucket (0.03-0.10, 0.10-0.20, 0.20-0.30); model Brier against market mid on the scored markets; trades by series and side.

## Numeric prediction (before any outcome)
Control mean net per contract between -2.5c and -0.5c (the cheap side wins less often than its price, as the 67-day look suggested). Model trades: 60 to 400 on development; mean net between -4c and +2c; PF below 1.0. Verdict: FALSIFIED about 55%, NOT_ENOUGH_DATA about 40%, NOT_YET_FALSIFIED about 5%. The model has the same information as the quote (yesterday's price), so a 3x ratio mostly selects the model's tail over-dispersion.

N: +2 (one rule; running count about 730,100 to 730,102).
