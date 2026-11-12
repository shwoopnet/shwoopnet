# Cards from the untouched-family census (Idea Desk B, Nov 12, 2026)

Asked for by the Head of R&D: ten new cards this week from untouched families with 300 or more independent events a year and enough volume to fill one contract, the first three by 16:00Z on Nov 13, and where a family is simply efficient, "efficient, move on" with the one number that shows it. Fewer than ten is fine; no padding.

**Count so far: pool families examined 12, plus the two rates groups the Head named, plus 12 families the Nov 10 listing added = 26, which is every family in the master table that is not TOUCHED (`FAMILY_TABLE.md`: 62 families, 36 touched, 8 sweep only, 18 never read); cards written 2 (both start with a zero-try cost and price measurement); 5 of the 26 families sit inside the two cards and the other 21 each have a one-line reason below; one question for the Head (hourly temperature). Nothing was scored and no Kalshi request was made for this file.** The pool and its sources are in `FAMILY_CENSUS_NOV12.md`.

## The filter every candidate went through first

1. **The cheap side and crowd biases are out.** V2's pooled calibration (CALIB1, 16,041 cheap-side entries, 3,535 events) loses in every price bucket. And at the research bar a mid-priced bet held to settlement needs the market's price to be wrong by about 9 to 12 points (`IDEA_DESK_B_WAVE3.md`, the table at the top). A bias of 1 to 3 points cannot get there.
2. **In play is a race we lose,** unless play is stopped. A bot that looks once a minute cannot beat people watching the game. The two in-play cards already written (the lag measurement and NHLOT) are the only two shapes that survive this, and the same shape on another sport is a version of them (lifecycle 7g), not a new card.
3. **Score sites are barred,** so for sports the only information is Kalshi's own sibling markets, or a permitted outside fact (weather).
4. **Declined list checked** (lifecycle 7e, read in full on Nov 12). Rows each card was compared with are named in the card.

What is left after the filter is narrow: a contract that the market may price badly for a structural reason (not a taste), in a market type nobody has read.

## Card 18. TIE3: the tie contract in period, quarter and half markets

`TIE3 | family: a listed third outcome priced under its base rate; entry before the game on the Tie contract, hold to the end of the period (under 3 hours) | risk class: mid price (about 20c to 45c), 1 contract, thousands of period-events a year, no link to any live strategy | stage Idea`

- **Source of the fact (first, as ruled):** Kalshi's own markets only. The base rate comes from Kalshi's own earlier settlements of the same series; the price is the Tie contract's own quote. No outside host, no score site.
- **Mechanism in one line.** Period, quarter and half "winner" markets are three-way: team A, team B, Tie. A hockey period ends level about 4 times in 10 and a soccer first half more often than that. If buyers come for a team and the Tie contract is left to whoever quotes it, the Tie may sit under its base rate by more than the fee.
- **Seen in the Nov 10 listing (added 17:15Z; shape and volume only, no price or result read).** Each of these lists three markets an event, one with a ticker ending in TIE: NHL periods 1 to 3, NFL quarters and first half, NBA quarters and halves, college basketball first half, a soccer first half. Contracts a market that day: NHL period winner about 2,700 to 6,200; NBA first quarter 27,400; NFL first quarter about 100,000 (one game); college basketball first half 7,800. One contract fills. The NHL "will the game go to overtime" market (5,500 contracts a market) is the same idea over a whole game, a level score after regulation with a base rate near 22%, and joins the card as one more cell. NBA and college basketball Ties are cheap-tail contracts and stay out.
- **How I knew the markets are three-way before the listing.** V2's Nov 3 counts: the NFL first-half and each NFL quarter series settled exactly 363 markets on 33 dates, which is 3 a game for 121 games; MLS first half 501 against 167 games; NBA first half 519 against 173 games. The NHL period and college quarter series were never read; the listing will show whether they have the same shape. If they do not, they drop out of this card.
- **Who is on the other side, and why they might lose.** Team buyers, and a maker who prices the two team contracts off the full-game line and leaves the third wide. Honest counter: sportsbooks have priced "60 minute" and period three-way lines for decades, and any maker here can copy them. I expect the Tie to be priced within a few cents of its base rate where there is a real maker, and to have no usable quote where there is none.
- **Base rates I am assuming (general knowledge, NOT measured; the test replaces them):** NHL period level about 40%; soccer first half level about 43%; NFL quarter level about 20%; college quarter about 15%; NFL half about 7%; NBA half about 2%. The NBA and NFL half Ties are cheap-tail contracts and are NOT part of this card (filter 1).
- **Rule a one-minute bot could follow (proposed, not registered).** Before the game, at one fixed minute set by rule from the event's listed start: buy YES on Tie at the ask if the ask is at least 10c under that league and period's base rate (base rate fixed from an earlier block of games) and the spread is 4c or less. One contract, one entry a period, hold to settlement.
- **Uniqueness check (7d).** Signal: a different market TYPE (three-way sports period markets; nothing live or shadow is in one), read against a base rate from Kalshi's own earlier settlements. Exit: hold to settlement, with different entry rules and no shared market with any live strategy. Correlation with live strategies: not measured; no shared market or clock. Declined list: see next line.
- **Declined list, compared row by row.** (a) "Conditional tie premium on the non-crypto 15 minute markets" (TIECOND1; names it must not return under: "TIECOND1, tie or frozen-source YES rules"). That row is about 15 minute PRICE markets where an unchanged price settles YES, a rare settlement edge case, closed by census at a best lower bound of 1.96% against 6% needed. This card is about a LISTED Tie contract in sports period markets, an outcome that happens 20% to 45% of the time. Different market, different contract, different reason. **But the word "tie" is in that row, so I am not ruling on my own card: the Head of R&D rules before any pull.** (b) "Favourite-and-hold": not a favourite; the Tie is bought at 20c to 45c. (c) "Cheap-side price, regime and grammar rules on the 15 minute series": not that series and not a sweep. (d) "Lock and parity scans": not a lock; it can lose.
- **Closest existing tests.** USWEEP2 read seven NFL period series and three NBA and MLS half series with one rule, the cheap tail at 5c to 15c: 548 entries over 117 cells, no lead, almost every cell under 20 entries. It never looked at a mid-priced Tie. SPORTCONS1 looked for locks between the game and first-half totals and found none. TIE1 was a two-leg soccer "to advance" rule, a different contract.
- **Data and terms.** Kalshi's own public data only, through kalshi-pull. No outside host.
- **Cheapest test: a price measurement, zero tries.** Pull the settled lists of the period series the listing confirms as three-way (expected: three NHL periods, four college quarters and a half, four NFL quarters, MLS and smaller-league first halves), then one pre-game minute candle of each Tie contract. Split the games by close date at a pinned date: the OLDER 60% give the base rate of a level period per league and period (results are read there, for that count only); the NEWER 40% give prices only, and no result of theirs is read. Reported per league and period: the median and quartiles of (base rate minus Tie ask), the share of games with a two-sided quote, and the standard error of the base rate.
- **Requests:** about 25 for the lists and about 80 to 150 for the candles, one run, under the 200 MB cap. Exact count after the listing shows the series.
- **Kill rule, fixed now.** A league-and-period cell needs at least 150 period-events in the base block and 40 priced games in the newer block, else it is "no evidence". The card is CLOSED, with the words "efficient, move on" and the median gap as the one number, unless at least one cell shows a median (base rate minus Tie ask) of 8c or more with a spread of 4c or less. Also closed if under half of the games in every cell have a two-sided Tie quote before the game (nothing to buy). The direction is fixed: if the Tie turns out OVERPRICED, the card closes; it is not turned round.
- **If it survives: 1 try,** on date constants, development and held-out split by close date, the base rate always from games earlier than the bet.
- **Power line.** NHL alone gives 1,312 games and 3,936 period-events a year. At an entry near 30c the bar (true cash PF 1.5 at z 5.46, 80% power) needs about 1,200 bets, so one NHL season could decide it, and soccer first halves would add to that. This is the first card of mine where the event count is not the problem.
- **Time to settlement:** under 3 hours. **Time to a verdict:** two days for the measurement after the pull. **Probability:** 4% that it reaches the bar; about 80% that the measurement closes it.
- **Families from the pool it covers:** NHL periods, college football periods, NBA and MLS halves (first halves in soccer only), and the first-half series inside the small-league soccer group.

**The card in the Head's required lines (added Nov 12 after the 16:58Z rulings):**

| Line | TIE3 |
|---|---|
| Counterparty | Team buyers, and a maker who prices the two team contracts off the game line and leaves the third wide. Named, not shown: the measurement does not identify who quotes |
| Entry | Before the game, YES on Tie at the ask when the ask is 10c or more under the base rate, spread 4c or less |
| Exit | Hold to settlement (the end of the period, quarter or half) |
| Cost from data | **No cost row exists** for any period, quarter or half market (Forensics, `FAMILY_COSTS_NOV12.md`). Nearest rows: NHL moneyline spread 2c, round trip 5.5c, 800 contracts a market; NHL spread and total 3c to 4c wide and flagged too costly. So I expect the NHL cells to fail on the spread condition and the NFL and MLS cells (median volume 8,000 to 15,000 in V2's count) to be the ones that can be measured. Stage 1 below IS the zero-try cost measurement: it reports the spread and the share of two-sided quotes before any price gap. Held to settlement, the cost is half the spread plus one fee (about 1.5c at these prices), not a round trip |
| Events a year | NHL 3,936 period-events; NFL 1,140 quarter-events; college football about 3,600 quarter-events; MLS and small-league first halves, count from the listing |
| Events needed at z 5.46 | about 1,200 bets near 30c for a true PF of 1.5; about 400 for a true PF of 2 |
| Date constants | Base block: closes before 2026-10-20 00:00 UTC. Price block (measurement, prices only): closes 2026-10-20 to 2026-11-12. Held-out for the one try: closes from 2026-11-13 00:00 UTC on, never read before the development read is filed |
| Requests | about 25 for lists, 80 to 150 for candles, one run |
| Tries it adds | 0 for the measurement; 1 if it survives |

## Card 19. SOCDERIV: soccer extras against their own sibling markets

`SOCDERIV | family: a derived contract priced away from what its liquid siblings imply, by a model that can be wrong; entry before kickoff, hold to settlement (2 hours) | risk class: mid price (about 35c to 65c), 1 contract, about 2,800 big-league games a year, no link to any live strategy | stage Idea`

- **Source of the fact (first, as ruled):** Kalshi's own related markets only: the same game's winner prices and total-goals ladder are the state. No outside host, no score site, no sportsbook line.
- **Mechanism in one line.** "Both teams to score" and "team total over 1.5" are functions of the two teams' expected goals. The same game's winner prices and total-goals ladder, which trade 10 to 100 times more, already pin those two numbers down. If the thin contract is quoted by someone who does not tie it to the siblings, it can drift from what they imply.
- **Who is on the other side.** A casual maker or a resting order on a contract with a median volume near 1,600, in a game whose main markets trade 20,000 to 180,000. Honest counter: sportsbooks price these from exactly this arithmetic, and a maker who copies a sportsbook has done the work already. Where the gap looks large it may be MY model that is wrong, not the market.
- **The sibling-implied value, written out.** Fit two goal rates (home, away) to the game's three winner prices and its total-goals ladder by least squares, goals treated as independent counts. Then both-teams-to-score is (1 minus the chance home scores none) times (1 minus the chance away scores none), and a team total follows from that team's rate alone. Known weakness: real scores have slightly more draws and low scores than independent counts give, which moves both-teams-to-score by about a point. Corners are NOT covered: nothing in the siblings implies them.
- **Rule a one-minute bot could follow (proposed, not registered).** At the last two-sided minute at least 30 minutes before kickoff: buy the side (YES or NO) whose ask is at least 8c under the sibling-implied value, spread 4c or less, 1 contract, one entry a game per contract, hold to settlement.
- **Uniqueness check (7d).** Signal: sibling-market prices of the same game put through a model, on a market type nothing live touches. Exit: hold to settlement, different entry rules, no shared market. Correlation: not measured; no shared market or clock. Declined list: next line.
- **Declined list, compared row by row.** "Lock and parity scans (riskless or implication-bound sets across Kalshi markets)", names: "any monotonicity, full-set, deadline, bracket or cross-series dominance scan". This card is not riskless and not bound by implication: the relation holds only on average, through a model, and every trade can lose. It is nearer to COMBOPRICE1 (a combo's price against its own legs), which is an open design and not on the list. **It is still a relative-value idea next to a closed row, so the Head rules before any pull.** No other row is close.
- **Closest existing tests.** SPORTCONS1 (locks only, none found). SOCCER1 and SOCCERELO1 (winner prices against sportsbook odds and a rating; gap median +0.12c). XI1 (starting line-ups against goalscorer rungs). None priced one Kalshi soccer contract off its siblings.
- **Data and terms.** Kalshi's own public data only, through kalshi-pull.
- **Cheapest test: a gap measurement, zero tries, no result read.** For this season's settled big-league games: the lists of the both-teams-to-score and team-total series and of the game's winner and total series, then one pre-kickoff minute candle of each. Reported: the share of contracts with a two-sided quote, and the distribution of (implied value minus ask) on the cheaper side.
- **Requests:** about 40 for the lists and about 100 to 200 for the candles (four market groups a game), one or two runs. Exact count after the listing.
- **Kill rule, fixed now.** CLOSED with "efficient, move on" and the 90th percentile gap as the one number if fewer than 10% of quoted contracts show an ask 8c or more under the implied value. CLOSED as "not tradable" if under half of the games have a two-sided quote on the thin contract. Under 150 priced games is "no evidence".
- **If it survives: 1 try,** date constants, read once.
- **Power line.** About 2,800 big-league games a year. If one game in ten qualifies, that is about 280 bets a year near 50c. The bar needs about 950 bets at a true PF of 1.5 and about 320 at a true PF of 2. So within a year it is reachable only if the true PF is 2 or better. Small leagues would add games only if their extras are listed, which the listing will show.
- **Time to settlement:** about 2 hours. **Time to a verdict:** two to three days for the measurement. **Probability:** 2% that it reaches the bar; about 85% that the measurement closes it.
- **Families from the pool it covers:** soccer extras (team totals and both-teams-to-score).
- **Why it is not a lock scan under a new name (the Head's rule 2c).** A lock scan looks for a set of contracts that cannot lose together. This rule buys ONE contract that loses about half the time; the siblings only say what it is worth on average, through a model with a stated weakness. If the measurement finds no gap, there is no trade; it never looks for a riskless set.

**The card in the Head's required lines (added Nov 12 after the 16:58Z rulings):**

| Line | SOCDERIV |
|---|---|
| Counterparty | A casual maker or resting order on the thin contract. Named, not shown |
| Entry | At least 30 minutes before kickoff, the side whose ask is 8c or more under the sibling-implied value, spread 4c or less |
| Exit | Hold to settlement (about 2 hours) |
| Cost from data | **No cost row exists** for any soccer market (Forensics holds no soccer recorder). V2's count gives a median volume near 1,600 for the one extras series it read, against 22,000 for big-league totals. Stage 1 IS the zero-try cost measurement: spread and share of two-sided quotes come first, the gap second. Cost when held: half the spread plus about 1.7c of fee near 50c |
| Events a year | about 2,800 big-league games; about 280 bets if one game in ten qualifies |
| Events needed at z 5.46 | about 950 bets near 50c for a true PF of 1.5; about 320 for a true PF of 2 |
| Date constants | Measurement: games closing 2026-09-12 to 2026-11-12 (the live endpoint's range), prices only. Development for the one try: the same games' results, read once. Held-out: closes from 2026-11-13 00:00 UTC on |
| Requests | about 40 for lists, 100 to 200 for candles, one or two runs |
| Other venues, same card | The Nov 10 listing shows quarter and half spread and total ladders for the NBA (2,500 to 9,500 contracts a market), the NFL and college basketball. The same measurement applies there with a different sibling model (a quarter's line as a fixed share of the game line, the share taken from Kalshi's own earlier settlements). Under lifecycle 7g that is this card on another market, not a new card; it is counted once and the soccer measurement runs first |
| Tries it adds | 0 for the measurement; 1 if it survives |

## Pool families with no card, and why

| Pool family | Why there is no card | The one number, where one exists |
|---|---|---|
| Small-league soccer totals and spreads (30 series never read) | Before the game these are two-way prices with no outside fact we may read; any rule is a calibration rule (filter 1). In play they are a venue for the lag card, which is a version of it, not a new card. Their first-half Tie contracts are inside TIE3 | CALIB1: sports cheap side at 5c to 10c, +1.8c, interval -2.1c to +6.2c, 186 events; pooled cheap side negative in every bucket |
| Foreign basketball totals and spreads (10 series) | Same: two-way, no permitted fact, no third outcome | none of its own; never read |
| Minor hockey, AHL and KHL winners (2 series) | Same. A rest-and-travel rule from the schedule is worth about 3 points of win chance in the big leagues, far under the 9 to 12 needed | none of its own; never read |
| College volleyball match (1 series) | Same, and seasonal | none of its own; never read |
| College football props (2 series) | The only outside fact that moves football props and may be read is wind (NWS). About 1 game in 8 outdoors is windy: about 100 games a year across the NFL and college. Under the 300 line on events that the rule would trade, and the best known weather effect in football betting. Considered and dropped, not carded | none |
| Texas power daily peak (source terms NOT read; none needed, since no card names it). Nov 10 listing: 39 contracts a market, too thin whatever the mechanism | A public forecast or a running peak against a bracket is the weather mechanism again (forecast against market: closed, three falsified; already-decided fact: WXDEAD1 and RAINFACT1 FALSIFIED). The same logic on a new market is a version of a closed family | USWEEP3: no lead. WXDEAD1: 612 of 612 events, quotes follow the fact |
| Truflation daily index (source terms NOT read; none needed, since no card names it). Nov 10 listing: 84 contracts a market, too thin | A slow daily index against a ladder is the persistence mechanism | GAS2 control PF 0.15 (n 2,310); TNOTE1: no bracket was ever quoted cheap enough to trade; SOFR1: 1 trade in 44 days |
| Daily top music video | Yesterday's number one against today's ladder is favourite-and-hold, and the chart sources are barred or unread | SPOTD1 (the song version): model worse than the market |
| Daily Treasury yields (the Head asked for one card here if a mechanism exists) | **Too costly, move on.** Not in the 300 pool (about 250 days), and the cost closes it before any mechanism | Forensics: spread 8c to 18c, round trip 9.7c to 20c, volume 100 to 510 a market |
| Daily SOFR (same request) | No card. SOFR1 already tested the last print plus calendar effects, and its own result says why nothing can trade: about 2 strikes a day near the last rate, 1 qualifying trade in 44 days. The one mechanism I can name that is not SOFR1 (month-end and tax-date jumps bought at a mid price) IS SOFR1's calendar term at another price. About 250 days a year with a two-sided quote on 31% of reads leaves under 80 tradable days against about 950 needed | Forensics: round trip 2.1c, two-sided on 31% of quotes. SOFR1: 1 trade in 44 days |

### Families the Nov 10 listing added to the pool (added 17:15Z)

| New never-read family | Events that day (lower bound) | Card or reason |
|---|---|---|
| NBA quarters and halves: winner, spread, total | 124 from 6 to 8 games | The Tie contracts are cheap-tail (out). The spread and total ladders are a venue of card 19, not a new card |
| College basketball spread, total, first half | 168 | Two-way lines with no permitted outside fact; the first-half ladders are a venue of card 19. Early-season ratings are the obvious idea and every ratings site is barred or unread |
| ITF tennis | 408 matches | The most traded never-read family (about 76,000 contracts a market). Before the match it is a rating against the market, which needs an error of 9 to 12 points to reach the bar and was falsified twice on esports from Kalshi's own results; in play it is a race against people at the court. No card |
| Tennis set winner and exact score | 28 | Derived from the match price by a standard model; a venue of card 19 at most. No card |
| Overtime markets (NBA, NHL, college basketball) | 12 | The NHL one joins card 18 as a cell. The others are cheap-tail contracts |
| Hourly city temperature (4 cities) | 87 | The only large never-run family outside sports (about 32,000 events a year, 800 contracts a market). Any rule I can write is a public forecast or the latest reading against a bracket: the first is the closed weather mechanism on a new clock, the second is the already-decided-fact mechanism (WXDEAD1 and RAINFACT1 FALSIFIED) and a race against everyone polling the same government feed. The declined row names daily highs, lows and rain, not hourly readings, so this is my reading of the rule, not the rule's words: **the Head may want to rule on whether hourly temperature is inside the closed family** |
| Index intraday up or down | 24 | A price ladder; the grammar is closed without a new data source |
| NBA race to a score, winning margin, team total | 37 | Derived from the game's spread and total; a venue of card 19 at most. No card |
| Darts, chess, bowling | 18 | 360 contracts a market; two-way winners with no permitted outside fact. No card |
| Hourly commodity ladders | 92 | 59 contracts a market: too thin whatever the mechanism, and a price ladder |
| Hourly Treasury rate ladders | 83 | 8 contracts a market: dead |
| NASCAR; open-weights AI share; Shiba ladders (sweep only in the master table) | 0 to 1 | Not fast or not traded: 38 races a year, a one-off, and a ladder with zero volume. No card |
| NHL period totals and spreads | 25 | A venue of card 19 if NHL spreads are not too wide; Forensics already flags NHL game spreads and totals as too costly |

## What I would not claim

- Two cards from twelve families is the honest number today. Both are measurements first, both expect to close, and neither is a find.
- The base rates in TIE3 are from memory of the sports, not from data. They are there to size the idea; the measurement replaces them.
- "Never read" families have no number of their own. "Efficient, move on" for them rests on the pooled calibration and on the arithmetic of the bar, not on a read of that family. A read would cost about 30 requests a family and would only confirm a calibration result that cannot reach the bar either way, so I have not asked for it.
