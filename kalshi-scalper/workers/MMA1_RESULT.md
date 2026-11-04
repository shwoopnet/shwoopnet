# MMA1 result (2026-11-04): NOT_ENOUGH_DATA (census only; no candle and no outcome was ever fetched or joined)

Source: row 8 of `workers/SCOUT1_REGISTRATION.md` (KXUFCFIGHT). Not a duplicate: TENNIS1_RESULT.md only wrote "UFC (643 events, a few treated)" as a guess; no census existed. Cheap side only (ask 3c to 30c); no favourite-side figure computed. This file is the registration and the result in one: the census alone decides, so nothing was run that could be fitted.

## Census (listings and close times only)
- Kalshi KXUFCFIGHT settled fights before the cut 2026-10-03T16:00Z: **664 fights, 1,328 markets**, 2025-08-02 to 2026-09-29 (14 months, about 47 fights a month; the last third was never listed beyond the cut).
- ESPN: public site scoreboard API, UFC final bouts 2015 to 2026 (6,812 bouts), keyless, no rating history; Elo would be built walk-forward from these.
- Name match (normalised pair of fighters, event date within 3 days): 518 exact, 75 by last names only, 71 none. 593 of 664 matched (89%). On a random sample of 50: 41 exact, 2 last-name, 7 none (86%).
- Fighters with at least 3 prior ESPN UFC bouts, both: **365 qualified fights** (55% of fights). Under the 500 bar.
- Expected treated = prior 5% of cheap rows. Cheap rows cannot exceed one per qualified fight: at most 365 x 5% = **about 18, realistically 13** (about 70% of fights have a side at 3c to 30c). Under the 150 bar by a factor of 8 to 10.

## Verdict: NOT_ENOUGH_DATA (decided before any candle or outcome)
Stopped without fetching candles. Registered rule left for the record (not run): at the last valid candle at least 120 s before the scheduled start, buy the cheap side when rating probability >= 3 x ask (hard limit 0.30, held, max 1 per fight, cluster = fight); FALSIFIED if mean net after fees not above 0 in both halves or PF under 1.5; NOT_ENOUGH_DATA under 150 trades.

## Forward plan
UFC runs about 52 events a year, about 600 fights; 55% qualified, 70% with a cheap side, 5% treated gives about **12 treated a year**. 150 would take about 12 years. Retire the cell; it is not worth a forward freeze. A bigger universe (boxing, other MMA promotions) has no reachable free results source. Rebuilding the data: `/tmp/mma1/espn.py`, `census.py` (scratch, outside the repo).

N +0 (no rule was scored; coordinator: +2 only if the registration is counted). Cheap side only.
