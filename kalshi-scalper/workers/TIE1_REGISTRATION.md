# TIE1 registration: two-leg soccer "to advance" markets, cheap side split by the aggregate deficit after leg 1 (written 2026-11-05, before any candle, price or outcome of this study was read; research only)

Strategy Research V2 worker, discovery only. Touches no live code. Cheap side only (ask 3c to 30c, hard limit 0.30, taker at the ask, held to settlement, fee 7% x C x p x (1-p) rounded up with C = 10, fees x1.2 shown). Not a favourite-and-hold test, not a 15 minute trigger.

## Duplicate check (README and workers/, searched before choosing)
No entry for UECL, "to advance", two-leg ties or aggregate. SP1 / SOCCER1 / XI1 / BOOKS1 / SPORTCONS1 / FAMSPORTS / SCOUT1 are single-match markets (winner, goalscorer, totals). Nothing here overlaps ladder coherence, weather siblings, stale quotes, MWIDE1 or government releases.

## Census (counts only, 2026-11-05; settled-events endpoint, no price, no result of any tie used)
Settled events per sports series with at least one event (183 candidate series): KXUECLADVANCE 139 (Conference League ties: 75 in July 2026 qualifying, 54 in August playoff and qualifying rounds, 10 knockout ties in Mar to May), KXSVKCUPADVANCE 110 (single match, equals the game winner, excluded), KXNCAAFWINS 73, KXSERIECCUPADVANCE 45, KXNFLDRAFTPICK 20, KXNBADRAFTPICK 19, everything else 12 or fewer. Season-long futures (win totals, playoff qualification, MVP and award markets, touch ladders) have 1 to 2 settled events a series, i.e. one season each: NOT_ENOUGH_DATA by count, no price fetched. Only KXUECLADVANCE has at least 100 settled events with a keyless fact source (ESPN `uefa.europa.conf_qual` and `uefa.europa.conf` scoreboards carry both legs' scores). KXUELADVANCE and KXUELADVANCE-like series were not counted as a second family (Europa League knockout ties are a few dozen at most) and are not in the universe.

Disclosure of what was seen before registering: the event titles and tickers of KXUECLADVANCE and KXSVKCUPADVANCE (first and last of the list), ONE market object (Partizan Belgrade vs Getafe, 2026-08-27, result no for Partizan: seen by accident in the metadata printout; it is in the universe and is not selected on), and two ESPN scoreboard days (2026-08-20 and 2026-08-27, qualifying round scores) while checking the source works. No quote or candle was read.

## Counterparty and mechanism
Longshot buyers in two-leg ties. A cheap "to advance" quote mixes two different things: a team that is level or one goal behind with a leg at home or away still to play (a live chance priced at 15c to 30c) and a team two or more goals behind (almost dead, priced 3c to 10c). The favourite-longshot bias says dead longshots are overpaid more than live ones, so the cheap side should lose least where the aggregate deficit after leg 1 is 0 or 1 goal. This is the one claim: an outside FACT (the leg 1 score, public on ESPN) splits one cheap-side pool into two, and the treated arm should be no worse than fair price.

## Universe, chosen before any outcome
Every KXUECLADVANCE event with settled status whose second leg date is before the cut 2026-10-03T16:00Z (all of them), two markets each (one per team), via `/historical/markets?event_ticker=` (closes before the 2026-09-04 historical cut) or the live market list. Leg 2 is the later ESPN match of the two teams inside the 21 days before the event's `occurrence_datetime` date; leg 1 is the earlier one in the same window; teams matched by normalised name (lower case, ASCII, tokens of at least 3 letters, both teams' token sets must overlap the ESPN team's). A tie with no unique leg 1 and leg 2 match is DROPPED and counted (single-leg or unmatched), never guessed. Kickoff of leg 2 is the ESPN event time.

## Look and trigger
Look = the last 1 minute candle of the market whose period ends at or before kickoff of leg 2 minus 300 seconds, within the 4 hours before (historical candle endpoint or live, by the 2026-09-04 cut), needing a real two sided quote (bid and ask present, spread at most 10c). Candidate = the market of the tie with the lower yes ask if that ask is 0.03 to 0.30 (at most one per tie; none if no side qualifies). Arms, fixed now:
- **TREATED**: the candidate team's aggregate deficit after leg 1 is 0 or 1 goal (goals against minus goals for in leg 1, at most 1).
- **CONTROL**: every candidate (treated or not), the cheap-side baseline.
- Information only (not a try): deficit 2 or more, and the home / away split.

## Numeric prediction (before any score)
Candidates 90 to 130 of the 139 ties (about 3 in 4 have a usable look); treated 55 to 100. Treated win rate 0.8x to 1.0x of price, mean net -6c to -1c per contract, PF 0.3 to 0.9; control -7c to -3c. Treated beats control by 1c to 4c. FALSIFIED 40%, NOT_ENOUGH_DATA 58% (treated under 150), pass under 2%.

## Kill criteria and tries
FALSIFIED: treated mean net after fee not above 0 in BOTH halves (D1, D2 = events cut at the median second leg date), or PF under 1.5, or tie-clustered z under the deflated bar 5.27 (one trade per tie so the unit is the tie). NOT_ENOUGH_DATA: fewer than 150 treated trades (then a dated forward accrual figure: ties per season, about 140 a year, so about 1.5 seasons for 150 treated). NOT_RUNNABLE: ESPN or the candle endpoint unavailable for under 50 usable ties. N tried this study: **+2** (TREATED, CONTROL), running count about 730,447, z bar about 5.27. One read, no reruns, no variants. Frozen last third (cut 2026-10-03T16:00Z): no event of this universe is after it; no market after the cut is fetched.

## Data and size of the fetch
ESPN day scoreboards (keyless) for the days around each second leg; Kalshi: one listing call per event, one candle call per market (at most 278). The shared Kalshi limit answers 429 often, so the fetch is resumable and cached; a tie whose candle cannot be fetched after 8 retries is counted dropped, not guessed.
