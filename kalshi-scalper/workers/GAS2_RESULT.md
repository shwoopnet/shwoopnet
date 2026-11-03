# GAS2 result: cheap-side AAA gas strikes vs a persistence model (run once, 2026-11-03; registration `workers/GAS2_REGISTRATION.md`, sha256 begins 35a92bd5e2351b52)

**Verdict: FALSIFIED.** Raw output: `workers/GAS2_RESULT_raw.txt`. Nothing in the rules was changed after seeing data; one deviation is listed below.

## Data
17 series (all passed the 40-date rule), 67 distinct close dates, development through 2026-10-09 (44 dates); 7,556 frozen-date market rows were dropped inside the fetch before any write and never scored; 12,785 development markets, hourly look candle at close minus 8 h. Daily AAA series rebuilt from `expiration_value` of each event's settled markets. The model needs 14 earlier dates, so scored dates are 24 (2026-09-16 to 2026-10-09); 5,314 markets had a valid two-sided look quote, 2,604 did not (no candle or invalid).

## Numbers
| | n | days | win rate | mean price | net/contract | z (day-clustered) | PF | halves A / B | x1.2 fee |
|---|---|---|---|---|---|---|---|---|---|
| Control, every cheap strike 0.03-0.30 | 2,310 | 24 | 2.5% | 13.6c | -11.90c | -13.46 | 0.15 | -10.42c / -13.27c | -12.05c |
| Model (p >= 3 x ask, <= 2 per series-day) | 393 | 24 | 2.0% | 7.5c | -5.98c | -5.72 | 0.23 | -3.70c / -8.90c | -6.05c |
Model by ask bucket (win vs price): 0.03-0.10 1.0% vs 4.5% (n 294); 0.10-0.20 5.5% vs 14.1% (73); 0.20-0.30 3.8% vs 22.5% (26). YES side 259 trades -5.96c; NO side 134 trades -6.01c. Model Brier 0.1705 against the market mid 0.0805 (the model knows less than the quote, as GAS1 found: 0.235 vs 0.083). Volume>0 subset of model trades: 88, -7.00c. Spread was not a screen; the loss is the price level itself.

## Reading
The cheap strike is overpriced everywhere: control wins 2.5% at 13.6c average, and the model's 3x filter selects tails the model over-disperses (its draws are wider than reality), so it picks the worst-priced ones. Prediction check: control -2.5c to -0.5c was wrong (actual -11.9c, much worse, because the ask in the hourly candle carries through hours with no trade, so the posted ask is a stale quote that nobody trades against); model -4c to +2c narrowly missed (-5.98c); PF below 1 and FALSIFIED were right (my 55% on FALSIFIED over NOT_ENOUGH_DATA; the 150 count was passed, 393).

## Size realism
Not measurable from candles (no depth). Only 88 of 393 model trades and 351 of 2,310 control entries had candle volume above zero in the look hour, i.e. most cheap asks are posted, untraded quotes (consistent with USWEEP1 and FLB1). The live order book snapshot (`book` command) was not run: with a FALSIFIED result a depth check cannot change the verdict.

## Duplicate check outcome
GAS1/GAS1-F/USWEEP1 carried; GAS2 adds the one thing not tested before: the cheap side against an empirical model. Same direction as every prior gas test: the quotes know more than a persistence model.

## Forward plan and probe
None. No probe spec: a mean of -6c to -12c with PF 0.15 to 0.23 in both halves has no mechanism pointing the other way for a taker. The frozen last third (2026-10-10 to 2026-10-22, 23 dates, candles still available until about 2026-12-20) stays unread; reading it could only be justified if someone registers a different model that changes the sign, and a model with Brier worse than the market's cannot. Not NOT_ENOUGH_DATA, so no dated freeze.
The only observation worth a separate registration (not done, no try added): the favourite side of these ladders at the same look, which GAS1-F already reads on 2026-11-22. Selling the cheap side is not available to a taker.

## Deviations
Dates are keyed by US Eastern close date and the "previous event 24 hours earlier" rule is implemented as the previous Eastern date (identical except around DST changes, none in the window). Series dropped for the 40-date rule: none. N: +2 (running count about 730,102).
