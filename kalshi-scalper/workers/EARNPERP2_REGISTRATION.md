# EARNPERP2 registration: cost map of the stock perp book around the earnings release (written 2026-11-06 about 23:00 UTC, before any spread of any release window was computed; shared rules `EARNPERP_COMMON.md`)

## Mechanism and counterparty
The PERPEQ cost map shows the overnight book about 3 times wider than the midday one. A release adds an information event on top: market makers should widen quotes and thin the top of the book for some minutes, and that widening is the toll the holder of the cash stock pays to trade at all before 09:30. This is a cost map, not a trade: its use is to say what EARNPERP1 pays and whether a 20 bps screen at L removes the release window.

## Measure (fixed)
For each event (all single-stock perps, the universe is the map itself; event definition without the 20 bps screen and without the |m| trigger): s0 = median close spread (bps of mid) of the candles ending in [R-60 min, R-5 min] (or, if the perp is closed or missing, no event); s1 = median over [R+1, R+15 min]; s2 = median over [R+15, R+60 min] (PRE events: s2 up to 09:25 ET). Control spread c = the median spread over the SAME clock minutes of the SAME ticker on the five previous trading days without an event (the clock effect: the book is wider overnight regardless). r1 = (s1 / c1), r2 = (s2 / c2). Depth: the top sizes in the hourly recorder rows and any 30 second rows that fall inside a window, counted and reported only (the candles carry no sizes; a depth claim needs the recorder in the common file and is NOT made here).

## Numeric prediction
About 55 events with candles in development; median r1 1.6 (range 1.2 to 2.8), median r2 1.2 (1.0 to 1.8); share of events with r1 above 1 about 80%; median s1 in absolute terms about 10 to 20 bps (so the 20 bps screen at L removes about 35% of events, as assumed in EARNPERP1).

## Verdict rules
**MAP_CONFIRMED** (a LEAD in the cost sense, nothing to trade): at least 30 events, median r1 at least 1.5 and a sign test of r1 above 1 with a date-clustered p under 0.001. **FALSIFIED**: at least 30 events and median r1 under 1.15. **NOT_ENOUGH_DATA** under 30 events with candles at both windows or fewer than 20 dates. Read date 2027-03-01 on development; no held-out read is required for a map (held-out events are read once on or after 2027-06-01 only to confirm a MAP_CONFIRMED). Scorable today: zero events (same reason as EARNPERP1).

## Count
N +1.
