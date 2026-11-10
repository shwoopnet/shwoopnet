# OPEN1H (registered Nov 10, 2026, 12:30 AM CT, before any first-hour candle is fetched): first-hour pricing of newly listed markets
Research only, public data, no key, no order. Cheap side only (ask 4c to 30c). Not favourite-and-hold, not a long hold of an expensive entry.
Question: is a market's quote in its first hour after listing miscalibrated on the cheap side (makers not yet set, retail first)? Mechanism and counterparty: a fresh listing is quoted by a maker with no flow yet; the loser is whoever sells the cheap side too low, or buys it too high, before the book matures.
Data: the open_ts column already held in `data/newser1.sqlite`, `data/nflpc1.sqlite`, `data/sports1.sqlite`, `data/sports.sqlite`. The history endpoint is retroactive, so nothing has to be collected going forward: pull hourly candles from open_ts to open_ts + 3 h for a sample of 300 markets per source chosen by md5 of ticker (same rule as NEWSER1), cache in `data/open1h.sqlite`.
Test: decision quote = last candle ending within 1 hour of open_ts; both sides quoted, spread <= 5c; buy the cheap side (ask 0.04 to 0.30) in bands 0.04-0.12, 0.12-0.20, 0.20-0.30; fee ceil(0.07*C*p*(1-p)*100), C = 10; cells = source group x side x band; first two thirds by close time development, last third read once for the shortlist; event-clustered z; shortlist needs 100 dev markets in 30 events, net >= 2c, z at or above the bar.
Potential cells: 4 sources x 2 sides x 3 bands = 24. Single-leg ledger N about 5,130, so N about 5,154, z bar about 4.30. Count 24.
Prediction (honest, before running): fails. Earlier single-leg calibrations (SINGLELEG1 to 3, NEWSER1) found nothing, and the first-hour spread filter will drop most markets, as in NEWSER1. Prior of a shortlist: 5%.
Cost: about 1,200 historical candle requests, at the same slow rate as NEWSER1 (about 40 minutes per 800).

## Amendment 1 (Nov 10, 2026, before any candle was fetched)
`sports.sqlite` has no open_ts column, so it is dropped: 3 sources (newser1, nflpc1, sports1), 900 markets, cells 3 x 2 x 3 = 18, N about 5,148, z bar about 4.30. Count 18, not 24. Requests about 900.
