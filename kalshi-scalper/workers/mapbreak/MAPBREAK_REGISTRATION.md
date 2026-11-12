# MAPBREAK, the break after map 1 of an esports best-of-three: gap measurement registration

**Registered Nov 12, 2026, before any price or result of these markets was read by anyone on this desk.** Written by Idea Desk B on the Head of R&D's go of 18:18Z; the reader, the pull jobs and the scoring are built by the Testing Desk from this text. Frozen titles and series: `mapbreak/MAPBREAK_SERIES.json`.

`MAPBREAK | family: a change of game state read from a sibling market while play is stopped; buy the side priced under what the state implies, hold to the end of the match (about an hour) | risk class: mid price, 1 contract, about 78 matches a day, no link to any live strategy | stage Idea, measurement only`

**This stage is a ZERO-TRY gap and cost measurement. No rule is scored, the result of a match is never read, nothing is traded, and nothing here permits an order.**

## Rulings it rests on (Head of R&D, Nov 12, 18:18Z)

1. **It is the same mechanism as NHLOT** (card 17): a state change while play is stopped, bought and held. It is a second VENUE of that family, not a new family. **For the owner's count, NHLOT and MAPBREAK are ONE candidate.** It is run because it has the events NHLOT lacks.
2. Zero tries at this stage. A rule scored afterwards is 1 try and needs a new go.
3. Prices come from minute-end candles at the stated instant, two-sided quotes only. Every output carries: "candle freshness measured on Bitcoin 15 minute only, not on esports".
4. **Wherever this card is quoted, my probability that it reaches the research bar is quoted beside it: 2%.**

## What has been seen so far

Only shape, times and volume, from the Nov 10 census listing: the tickers of one CS2 match and its maps, their open, close and settlement times, and contracts a market (about 3,000 to 8,000). In that one match the map-1 market closed 45 minutes before the match market did. No price field and no result field of any of these series was printed or used.

## The idea in plain words

A best-of-three match is won by the first team to take two maps. When map 1 ends, Kalshi's own map-1 market closes and settles within about three minutes. Play then stops for a break. At that moment the match price should jump to what "one map up" is worth. The measurement asks whether, two minutes into the break, either team's match contract can be bought for clearly less than that.

**Who is on the other side:** resting orders left from before the map ended, and bettors anchored on the team that was the favourite before the match. **Why they might not lose:** esports traders watch the stream, the result of a map is known to them the second it ends, and two minutes is a long time.

## The state, the instants and the prices (all pinned)

1. **Best-of-three only.** A match is in the sample only if its total-maps event has a market at 2.5 and none higher, and map markets 1 and 2 exist for its key (file). Others are dropped and counted.
2. **The state** is the map-1 market: its `close_time` is when map 1 ended, and its `result` says which team is one map up. That result is read, because it is the state. **The result of the match market, of map 2 and of map 3 is never read; the reader must enforce that in code.** No outside site is used for anything.
3. **Scheduled start S:** the date and four-digit time at the front of the ticker key, read as US Eastern time. (Seen once: a key reading 13:00 belonged to a match whose first map ended at 18:44 UTC.) **Guard:** map 1 must have ended between 15 and 150 minutes after S. If not, the match is dropped and counted under "start not derivable". If the time zone reading is wrong, this guard will drop nearly everything and the measurement will say so.
4. **Pre-match instant:** the one-minute candle ending at S minus 10 minutes. If it is not two-sided on the needed contracts, step back a minute at a time to S minus 40; if none, the match is "not filled" and counted.
5. **The look:** the one-minute candle ending at the first whole minute at or after (map-1 close + 120 seconds). If the two match contracts are not both two-sided there, step FORWARD one minute at a time to map-1 close + 5 minutes; if none, "not filled" and counted. **Guard:** the map-2 market must close at least 15 minutes after map 1 closed; otherwise the break cannot be told from play and the match is dropped and counted.
6. Two-sided means 0 < bid < ask < 1 at the candle's close. Nothing is filled in from another minute.

## The model (one line, and its known leans)

- p = the mid, at the pre-match instant, of the match contract of the team that went on to win map 1.
- q = that team's chance of winning one map, solved from **p = q x q x (3 minus 2q)** (the chance of taking two maps of three at q a map, maps treated as independent).
- **Value one map up: V = 1 minus (1 minus q) squared.** The other team's value is 1 minus V.
- **Gap** for a team = its value minus the ask of its own match contract at the look. The side with the larger gap is "the cheaper side".

**Known leans, both stated before data, pulling opposite ways:**
1. *Map picks.* In CS2 and Valorant each team usually picks one of the first two maps. A team that won map 1 on its own pick now plays the other team's pick. The model ignores that and so OVERVALUES the team that is up. Dota 2 and League of Legends have no map pick, so they are the cleaner cells.
2. *Learning.* Winning map 1 is itself evidence the team is better than the pre-match price said. The model keeps q fixed and so UNDERVALUES the team that is up.
Kalshi's data does not say whose pick a map was, so neither lean can be corrected. A gap can be the model. That is what the placebo is for.

## The placebo (what model error alone looks like)

At the pre-match instant no state has changed, and the map-1 market prices the very number the model derives: one team's chance of winning a single map. So: q from the match price, compared with the ask of that team's MAP-1 contract at the same minute (and 1 minus q with the other team's). Its gap is model error plus quote noise and nothing else. The same statistics are reported for it as for the look.

## Cells, fixed now (4)

CS2, Dota 2, Valorant, League of Legends. A pooled line is printed for information; the kill is read per title.

## Date constants

- **Measurement sample:** matches whose match market closed from 2026-09-12 to before **2026-10-23 00:00 UTC**; the 1,500 most recently closed best-of-three matches among them, all titles together, never extended.
- **Held-out:** matches closing from **2026-10-23 00:00 UTC** on, about the most recent third of the 61 days held. **Not pulled:** the lists job asks only for markets closing before that instant.

## What is reported, per title and pooled (counts first)

1. Matches listed; best-of-three; start derivable; filled at the pre-match instant; filled at the look.
2. At the look: median spread of the match contracts; **median round trip** = spread plus two fees of 0.07 x price x (1 minus price).
3. The gap on the cheaper side: median, quartiles, 90th percentile, and **the share of filled matches with a gap of 8c or more and a spread of 4c or less**; how that share splits between "the team that is up" and "the team that is down".
4. The same four numbers for the placebo.
5. How far the look was from the map-1 close, in minutes (2 to 5).

## Minimums and the kill rule, fixed now

- A title needs **150 matches filled at the look**; under that it is "no evidence at n = x".
- **A title is CLOSED on cost** if its median round trip at the look is above 5c.
- **A title is CLOSED with "efficient, move on"**, the 90th percentile gap as the one number, unless the share with a gap of 8c or more (spread 4c or less) is **10% or more AND at least twice the placebo's share** at the same line.
- The card is closed if every title is closed or "no evidence".

## If a title survives

A separate registration and a new go from the Head, before any match result is read: buy the cheaper side at the look when its gap is 8c or more and its spread 4c or less, 1 contract, hold to the end of the match; the measurement sample's match results as development, read once; the held-out from 2026-10-23, read once; **1 try for the card** (titles pooled into the one rule, each title reported). Research bar: cash PF 1.5 on development and held-out at the shared count (z 5.46). Near 50c that is about 950 bets for a true PF of 1.5 and about 320 for a true PF of 2.

## Requests

- **Lists job:** for each of the 12 series (match, map and total-maps for four titles) the markets settled from 2026-09-12 to before 2026-10-23, plus 4 fee-field reads. About 30 to 45 pages: **about 50 requests.** To run right after `NHLOT_LISTS`.
- **Candle stage (on the Head's go after the lists are scored):** per match the two match contracts and the two map-1 contracts, from S minus 40 minutes to map-1 close plus 5; matches with the same scheduled start share a request. **150 to 250 requests,** one or two runs.

## Honest limits

1. The closest earlier tests are priors against: V2's SERIESLAG1 ran this idea on playoff series with a fixed coin-flip model (44 trades, PF 0.21, not enough data), and ESPORT1 (a rating before the match) was FALSIFIED twice.
2. The time zone of the ticker's clock was read from one match. The guard catches a wrong reading; it cannot fix it.
3. A candle is one instant a minute and carries no size. An ask two minutes into a break may be one contract deep.
4. Candle freshness was measured on the Bitcoin 15 minute series only.
5. **My probability that a title survives the measurement: about 15%. That the card then reaches the research bar: 2% overall.**
