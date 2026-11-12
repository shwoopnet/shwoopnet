# Gap audit: sibling market types in the six families already over 1,200 events (History Miner, Nov 12, 2026, zero requests)

Sources: the Nov 10 census listing (`CENSUS_LISTING` on `kalshi-pull-data`; one Tuesday, a lower bound; series names and settled-event counts only, no price, no result), the census series list, and Desk B's `breaksweep/BREAK_SWEEP_NOV12.md` (claude/idea-desk-b) for which series close mid-event. Numbers in brackets are settled events on Nov 10. Research only. [research]

| Family | Sibling type beside the winner | Status | If untouched: state while play is stopped? events |
|---|---|---|---|
| ITF and Challenger tennis | match winner (ITF 161 + 141 women, Challenger 84 + 8 women) | INPLAYJUMP (Desk B, registered tonight); TENNIS1 ratings not enough data; SC1 in-play FALSIFIED (tour) | |
| | doubles winner (ITF 59 + 47, Challenger 7) | a separate event, not a sibling; no type beside its own winner | no mid-event market (Desk B sweep) |
| | set, games, exact score | NOT LISTED at these tiers (set winner exists only at tour level, about 10 matches a day) | |
| Virtual sports | e-soccer three-way winner (450) | INPLAYJUMP; VIRT1 ratings, every sign negative | |
| | e-soccer listed Tie | ESOCTIE (registered tonight) | |
| | e-soccer same pair meeting again | REMATCH (Desk B, card) | |
| | e-basketball winner (84), Liga Pro table tennis winner (147) | INPLAYJUMP; VIRT1 | |
| | anything else (half, total, spread) | NOT LISTED | |
| Esports (CS2, Dota 2, Valorant, LoL, R6, CoD, Rocket League) | match winner, map winner, total maps | MAPBREAK (Desk B, registered); ESPORT1 FALSIFIED; ESPORTM1 not enough data | |
| | map handicap (CS2SPREAD 5, VALORANTSPREAD, RLSPREAD) | UNTOUCHED | settles at match end; the break state is MAPBREAK's map market, so a handicap rule at the break is a VERSION of MAPBREAK, not a new card. About 5 events a day |
| | LoL in-game props (first blood, first dragon, first baron, kills, long or short game) | UNTOUCHED | close DURING play when the event happens (not a stopped-play state: the in-game lag family, closed); LoL GAME had 2 events on Nov 10 |
| | Dota 2 three-way, R6 total maps | UNTOUCHED | 0 settled on Nov 10; under 100 events in the window |
| Small-league soccer | three-way game winner with a listed full-time Tie | Tie: UNTOUCHED as a base-rate bet. Winner: SOCCER1 and SOCCERELO1 (cheap side, FALSIFIED or not enough data) | no stopped-play state (pre-game only). It is the TIE3/ESOCTIE mechanism on a third venue, so a VERSION, not a new card. Development (closes Sep 12 to Oct 22) holds about 1,500 small-league and big-league games: at a 3% to 10% firing share, 45 to 150 bets. Fails the 1,200 line |
| | totals, spreads, both teams to score, team totals, corners | SOCDERIV (Desk B card 19, measurement registered) | pre-game only |
| | first half winner, total, BTTS | TIE3 soccer cell (big leagues); soccer half time DROPPED (half time not derivable; too few games) | |
| T20, ODI and Test cricket | match winner (T20 3 + 3 women, ODI 2) | CRICT20 not enough data (10 treated) | |
| | first 6, 10, 15 overs runs; fours, sixes (T20 and IPL) | UNTOUCHED | the 6-over market closes after the powerplay, during play (no stop); the innings break is real but nothing settles at it. About 1,500 matches a year at most, under 1,200 in any window |
| Foreign basketball (EuroCup, EuroLeague, FIBA, Australia, Turkey, Korea, Brazil, VTB and others) | game, spread, total (EuroCup 8, FIBA Champions 4, Brazil 4, others 0 to 1 on Nov 10) | game: never read; spread and total ladders: a SOCDERIV venue (Desk B card 19, "other venues") | no half, quarter or period market listed: no stopped-play state. Pre-game ladder consistency is SOCDERIV's mechanism. About 25 games a day in the 7 Nov 10 series with events; about 1,000 in development; bets far under 1,200 |

**Answer: none.** Every untouched sibling type is either a version of a card already registered tonight (esports handicap: MAPBREAK; soccer full-time Tie: TIE3 and ESOCTIE), a market that closes during play (the closed in-game lag family), or too thin to give 1,200 development bets. No card is written.
