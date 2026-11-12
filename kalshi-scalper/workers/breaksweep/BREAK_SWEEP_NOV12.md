# Break-in-play sweep of the whole listing (Idea Desk B, Nov 12, 2026)

Asked for by the Head of R&D at 18:50Z for the Friday deadline: every family, in any sport or game, with a sibling market that closes MID-EVENT, so that a state can be read from Kalshi alone while play is stopped; one line each; drop those that cannot reach about 1,000 bets at a firing share of 10% to 20%.

**Answer: no further venue can reach about 1,000 bets.** Outside the families already assigned (esports maps here; tennis sets, soccer half time and the e-soccer Tie with the History Miner), every family either has too few events on any history that exists, or lists no mid-event market at all.

## How the sweep was done (zero requests)

`breaksweep/sweep_listing.py` reads the Nov 10 census listing (70,906 settled markets, one Tuesday, a lower bound) and finds every series with a market that closed 10 minutes or more before the last-closing market sharing its event key. Tickers, close times and volume only; no price, no result. Output: `breaksweep/mid_event_series.csv` (141 series; nearly all are the quarter, half, period and prop markets of the NBA, NFL and NHL). Weekend-only families do not appear in a Tuesday listing, so college football and the NFL were also checked against V2's 60 day counts (`census/first_cut_series.csv`).

"Looks" are independent decision points: one a break, so one or two a game or match. "Bets" = looks x the share of looks where a rule fires, at 10% and at 20%.

## Families WITH a mid-event state market

| Family | State market | Looks on the history held (unit) | Contracts a market | Bets at 10% to 20% | Reaches about 1,000? |
|---|---|---|---|---|---|
| Esports maps: CS2, Dota 2, Valorant, League of Legends | the map-1 and map-2 markets | about 6,900 looks from about 4,700 matches in 61 days | 3,000 to 29,000 | 690 to 1,380 | **Yes, at about 15% or more. Registered: MAPBREAK** |
| Tennis sets | the set-winner market | with the History Miner | | | not mine |
| Soccer first half | the first-half markets | with the History Miner | | | not mine |
| Rainbow Six maps | the map market | about 300 matches (5 on Nov 10) | 470 | 30 to 60 | **No.** Also no total-maps market, so a best-of-three cannot be told from a best-of-one |
| NBA quarters and halves | quarter and half winner and spread ladders | about 330 games this season; half time is the only real break (quarter breaks are 130 seconds) | 2,500 to 16,000 | 33 to 66 (100 to 200 with all three breaks) | **No** (dropped by ruling) |
| College basketball first half | the first-half winner | a few hundred games; the season is 10 days old | 7,800 | under 100 | **No.** The margin is readable for 3 of 21 games |
| NHL periods | period winner and "by over 1.5 / 2.5" | about 270 games, 540 intermissions | 1,400 to 11,000 | 54 to 108 | **No** (held: revisit only if last season is in history) |
| NFL quarters and halves | quarter and half winner and spread ladders | about 150 games this season, 450 breaks | 30,000 to 270,000 | 45 to 90 | **No** |
| College football quarters and halves | six series, never read; Saturdays | at most about 850 games in 61 days | 100 or more | 85 to 170 | **No** |
| Golf round leaders | the round-1, round-2 and round-3 leader markets (an overnight break) | about 9 tournaments, 27 looks | 24,000 | under 6 | **No.** The state names only the leader, not the gaps |
| Overtime markets, NBA and college basketball | "game goes to overtime" (the break before overtime) | about 6% of games: about 20 NBA overtimes this season | 300 to 3,000 | under 5 | **No** (hockey's is NHLOT) |

## Families with events but NO mid-event market (only a match winner is listed)

These have the count and cannot be used: Kalshi lists nothing that closes during the event, so the state would have to come from a score feed, which is barred.

| Family | Matches on Nov 10 | Contracts a market |
|---|---|---|
| ITF tennis, singles and doubles | 408 | 91,000 to 113,000 |
| E-soccer | 450 (three-way; the Tie is with the History Miner) | 1,100 |
| Table tennis, Liga Pro | 147 | 3,600 |
| E-basketball | 84 | 4,200 |
| Challenger tennis | 84 | 572,000 |
| Basketball outside the US | 62 events (game, spread, total) | 6,300 |
| Darts | 13 | 850 |
| Cricket: T20, ODI, Test | 9 | 140,000 to 420,000 |
| AHL, KHL, Champions Hockey League | 9 | 5,000 to 10,000 |
| Bowling, chess | 2 | small |

## Not listed at all on Nov 10 or in V2's 60 day counts

Snooker, handball, rugby, volleyball sets (the one volleyball series is a match market), baseball innings (out of season until April), boxing and mixed martial arts rounds (none settled that Tuesday; a round break is one minute in any case).

## Three limits of this sweep

1. One Tuesday. A family that settles only at weekends and was never counted by V2 would be missed; I know of none besides football, which is in the table.
2. The 4,700 esports matches are 78 on one day times 61; weekends run higher, so it is a lower bound.
3. "Soccer totals and both-teams-to-score close mid-event" shows in the raw file because a decided strike closes early. That is a goal being scored during play, not a break, and belongs to the closed in-game lag family.
