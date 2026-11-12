# SOCDERIV measurement: reader, job builders and scorer (Testing Desk build note, Nov 12, 2026)

**Status: BUILT AGAINST SYNTHETIC DATA ONLY. Not runnable on real data until Desk B's registration text and the frozen cells file exist.** Card 19 in `CENSUS_CARDS_NOV12.md` (`claude/idea-desk-b` 439b3ba); the Head approved a ZERO-TRY measurement. No Kalshi request, no data opened, no job sent to Main, no try added, no outcome read. No live account figure.

## What the code does (`socderiv.py`, `test_socderiv.py`; passes on made-up data)

1. `build-lists <cells>`: one live list per series (winner, total-goals, both-teams-to-score, team totals) per league; closes from 2026-09-12 (the live endpoint) to 2026-11-12 (cap 2026-11-13T00:00Z minus 1 s). **Requests: 1 per series, 4 per league**; for 4 big leagues 16 (at most 96 with paging).
2. `games`: a game is the same suffix after the series prefix in each series' event ticker (ASSUMED, to be verified on the first list answer); it needs all four groups and a derivable kickoff, else it is dropped and COUNTED. No `result` field is kept. Kickoff rule per league in the cells file: ticker local time, a market field minus an offset, or the Head's fixed offset before the market close.
3. `build-candles`: one-minute candles of every leg (winner x3, total ladder strikes named in the cells file, both-teams-to-score, two team totals = about 9 tickers a game) for the 90 minutes up to kickoff minus 30 minutes, packed by time (minutes x tickers at most 9,000). **Requests: about 130 to 200** (about 470 big-league games in the 61-day window at 3 to 4 games a pack, more if kickoffs spread over more than 3 hours a day); exact once the lists are reported.
4. `measure`: per game, the LAST minute at or before kickoff minus 30 minutes (scanning back at most 60 minutes) where EVERY leg has a candle with a two-sided quote; thin, one-sided or missing minutes are counted, not filled. Fits two independent Poisson goal rates by least squares to the winner mids and the total ladder mids (checked: it recovers 1.6 and 1.1 from exact prices), gives implied both-teams-to-score and team-total values, and reports for contracts quoted with a spread of 4c or less the gap (implied minus ask, the cheaper side of YES and NO). Reported with counts first: games seen, with all groups, with every leg two-sided in one minute, priced; contracts quoted; contracts 8c or more under; the gap's quartiles and 90th percentile.

## Verdict rules in the code (Desk B's card plus the Head's 17:16Z ruling)

- **STOPPED: "cannot be measured at minute resolution"** if under **30 percent** of the games have every leg two-sided in one minute (the share the Head suggested; fixed now in `SAME_MINUTE_SHARE`).
- **no evidence at n = x** under 150 priced games.
- **CLOSED, not tradable** if under half of the games have a two-sided quote on the thin contract.
- **CLOSED, efficient, move on** (the one number is the 90th percentile gap) if under 10 percent of quoted contracts show an ask 8c or more under the implied value.
- otherwise SURVIVES the measurement; the registered try is separate (1 try, date constants, read once).
- Output states `tries_added: 0`, `rule_scored: false`, `outcome_read: false`.

## Cutoffs and conditions enforced in code

Date constants `CUTOVER` 2026-09-12 and `HELD_OUT_FROM` 2026-11-13T00:00Z; cells fixed before data (`CELLS_SHA256` None means the code refuses to build a job); prices from minute-end candles only; never a list quote; model note carried in the output (independent Poisson goals understate draws, a gap may be the model's).

## Open items for Desk B (asked at 17:20Z)

The frozen cells file (league, the four series, total strikes, team-total strike, kickoff rule); confirmation that a game shares its ticker suffix across the four series (if not, the key rule changes); which team-total leg is home (I order team legs by ticker; safe only if the ticker suffix begins with the team code); the other venues (NBA, NFL, college basketball quarter and half ladders) are the same card on another market (7g) and are not built.
