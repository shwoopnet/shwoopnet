# REMATCH, the same two e-soccer players meet again within two hours: buy the one who just lost, if his price fell: rule registration

**Registered Nov 12, 2026, before any price of these markets was read and before any result was joined to anything, by anyone on this desk.** Written by Idea Desk B for the owner's Friday deadline (Head of R&D's order of 18:57Z; it grew out of the Head's seed "first-listed against re-listed markets of the same match"). Frozen series, dates and constants: `rematch/REMATCH_SERIES.json`. Counting script (times and tickers only): `rematch/count_listing.py`.

`REMATCH | family: the market's own repricing after one completed result between the same two players, faded; buy the previous loser before the next meeting, hold to settlement | risk class: mid price (20c to 80c), 1 contract, hundreds of matches a day | stage Idea, registered as a rule`

**Nothing here permits an order. Tries: 1.**

## What has been seen so far (the Nov 10 census listing; times, tickers and titles only)

Printed by `rematch/count_listing.py`, no price and no result read:

- E-soccer on that one day: 450 matches between 53 pairs of players. The same two players meet again and again: 397 "next meetings of the same pair".
- 311 of those start 20 to 120 minutes after the earlier meeting's start; in 299 the earlier one had settled 12 minutes or more before the later start; in 297 the later match's market was ALREADY OPEN before the earlier match began.
- So there is no re-listing: what looks like one is a real second match with its own market, and that market is trading while the first match is being played.
- Contract titles carry the club as well as the player ("Flamengo (Hurricane)"), and the clubs often change between meetings. The rule below compares the later market only with ITSELF, so the club is held fixed.
- The listing was cut at a page cap in 23 of 24 hours, so every count is a lower bound.

## The idea in plain words

An e-soccer game lasts about 12 minutes and one result says little about who is better. When the same two players are about to meet again, the later match already has a price from before the earlier one was played. If the loser's price in that later market has dropped 5c or more by the time the later match starts, the rule says the drop is too big for one short game and buys the loser.

**Direction, chosen now: FADE the fall.** The reason is the arithmetic of one noisy game: a sensible rating moves a win chance by 2 to 4 points on one result, so a 5c or larger fall is more than the result carries.

**The named other side:** bettors who chase the last result between the same two players, and a maker's quoting program that moves the next match's price with the last score.

**Why it may well fail, said first:** the market has been the better forecaster every time the research team tested a results-based view against it (ESPORT1 twice, VIRT1's signs). The fall may simply be right: a player having a bad session, or the result may have been a rout that says more than a coin flip does. And one earlier fade of a price fall held to settlement (SWING1, in-play, cheap side, American sports) found the fallen side fairly priced.

## The rule, every number pinned

1. **Scheduled start S:** the clock in the ticker, US Eastern, checked once for the whole family (file, `start_rule`), never match by match.
2. **The pair:** an earlier match A and a later match B of the same series between the same two player codes (either order), B being the NEXT meeting of that pair after A, with B's scheduled start 20 to 120 minutes after A's.
3. **Known before the bet:** every market of A has a settlement time at or before B's S minus 12 minutes, and A had a winner (not a Tie). L is the player who lost A.
4. **The state:** in B's market, L's contract is two-sided (0 < bid < ask < 1) at the candle ending at A's S minus 2 minutes (before A was played) and at the candle ending at B's S minus 6 minutes, and its mid fell by 5c or more between the two.
5. **Entry:** at the close of the candle ending at B's S minus 5 minutes, if L's contract is two-sided, its ask is between 20c and 80c and its spread is 4c or less: buy 1 contract at that ask plus 1c. One bet a match B. If the entry fails, no bet (counted).
6. **Fee:** 0.07 x price x (1 minus price), rounded UP to the next whole cent. **Exit:** hold to settlement. B's result is read only for matches with a bet.

No time that is known only after the bet decides which bets exist: the conditions use scheduled starts, A's settlement time (which must already be in the past at the decision) and candles that ended before the entry.

## Cost kill and placebo

- **Cost:** round trip at the entry minute = spread plus two fees at the mid. Median over qualifying entries above 5c: CLOSED on cost, nothing scored.
- **Placebo (the same bet with no fall):** pairs that meet every condition except the state, where L's contract moved less than 2c either way between the two instants; buy L's contract at the same minute, same band, same spread line; hold. Grouped by price paid in 10c steps and re-weighted to the rule's price mix. It is what backing the previous loser earns when the market did not react.

## Two stages (the first reads no bet's result)

**Stage 1, counts and cost only, on the slice already being listed for INPLAYJUMP (closes 2026-10-15 to before 2026-10-23):** pairs that qualify, the share in which the state is true, entries, the median round trip, the start check. A's results are used only to name L. No bet is scored.

- Closed at stage 1 with no try spent if the median round trip is above 5c, or if (share with an entry) x (pairs expected in the whole development window) is under 600 bets.

**Stage 2, on the Head's go:** the rest of the development window is listed and pulled, and the rule and placebo are scored once.

## Samples (date constants)

| | Market closes |
|---|---|
| Stage 1 slice | 2026-10-15 to before 2026-10-23 |
| Development | 2026-09-12 to before 2026-10-23 |
| Held-out (not listed, not pulled until the Head's go) | 2026-10-23 to before 2026-11-13 |

## Reported, and the verdict (fixed now)

Counts first, then: bets, wins, mean price paid, cash profit factor, net cents a contract, both halves by date, the largest share of net carried by one day and by one player, z with the DAY as the cluster (the same players meet many times a day, so a match is not an independent event; the day is the coarsest cluster and is the one used), the placebo's net at the same price mix and the difference with its standard error.

- Under 300 bets: NOT_ENOUGH_DATA at n = x.
- 300 or more and cash PF under 1.0, overall or in either half: FALSIFIED.
- Cash PF 1.5 or better, both halves above 1.0, AND net above the placebo's by two standard errors or more: "development bar met"; the held-out is asked for the same hour.
- Else "bar not met".
- **Research bar:** cash PF 1.5 or better on development AND held-out, one-sided z of 5.46 or more on the two together. Nothing short of it is a pass.

## Declined list and earlier tests, written out

- **Not favourite-late:** before the start, ask capped at 80c. **Not a cheap-side sweep:** one rule, band from 20c. **Not order flow, not in-game lag, not a lock, not market making, not a forecast.**
- **Nearest earlier tests:** SWING1 (fade a 25c in-play fall on the cheap side in college football and baseball, held: FALSIFIED, the fallen side was fairly priced). REMATCH differs in the cause (a finished result between the same two players, not a scoreboard event), the time (before the start, not in play) and the price (mid, not cheap). VIRT1 and ESPORT1 set a rating built from results against the price; REMATCH uses no rating, only the market's own move, and bets the opposite way to a results-follower. The scalp-exit fades on the 15 minute series (SCALP2, LADFADE, GEN8, GEN9) share the word "fade" and nothing else.
- **Against this desk's PREMOVE:** PREMOVE follows a late pre-match rise; REMATCH fades a fall with a known cause. So that no match is ever bet both ways, PREMOVE's Amendment 1 (same commit) leaves out any e-soccer match in which REMATCH's state is true. The two cards split the matches; they do not overlap.

## Events and requests, said plainly

- **Events:** 297 qualifying pairs on the one day seen (a lower bound). Development (41 days) about 12,000; held-out (21 days) about 6,200. What share shows a 5c fall is unknown: at 10%, about 1,200 development bets and 620 held-out; at 5%, 600 and 310. **But the true count of independent events is nearer the number of days and player-sessions than the number of matches, because the same few dozen players play all day; that is why the z is clustered by day and why a high profit factor on many matches may still miss z 5.46.**
- **Requests.** Stage 1: no list of its own (INPLAYJUMP's e-soccer lists serve); candles for two team contracts of each later match from A's S minus 3 to B's S minus 4, about 22 matches a request because one request has one time range for all its tickers: my estimate 110 requests. Stage 2: about 50 list pages and about 440 candle requests. Held-out: about half of stage 2.

## Honest limits

1. Candle freshness was measured on the Bitcoin 15 minute series only. Every output carries that line.
2. A candle has no size: a two-sided quote may have one contract behind it.
3. Between the two instants either player may have played somebody else; the rule does not care why the price fell, only that it fell after a loss to this opponent. The placebo is the check.
4. **My odds: about 1.5% that the development bar is met; under 1% for the research bar.**

## Amendment 1 (Nov 12, 2026, 19:15Z; before any price was read or any result joined; tonight's rulings of the Head of R&D applied from the start)

Where this section and anything above differ, this section is right. Tries unchanged: 1.

1. **Cost kill:** the ONE-WAY entry cost at qualifying decision minutes: the median of (ask minus mid) plus the entry fee as charged (0.07 x price x (1 minus price) at the price paid, rounded up to the next cent). Closed on cost if that median is above 4c. Why (Head of R&D's ruling of 19:02Z, on Desk A's flag, changed before any price was read): a rule that buys and holds to settlement pays no second spread and no second fee, and with the one-contract fee rounded up to 2c a side the old round-trip line would have closed every market whose spread is above 1c before one bet was scored. It is a request-saving screen, NOT the bar: the scored profit factor pays the real ask, the 1c slip and the fee.
2. **Tradeability is counted first:** before any bet is scored, the number of qualifying pairs in which the previous loser's contract is two-sided with a spread of 4c or less at the "before" instant. If, scaled from the stage 1 slice to the whole development window, it is under 300, the card CLOSES ON TRADEABILITY, unread.
3. **The decision uses candles up to and including the one ending at B's S minus 6 minutes;** the entry is the next candle's ask plus 1c. The placebo buys at the same instant by the same price rule.
4. **One void rule (Head of R&D, 19:08Z, the same for every hold-to-settlement card):** a bet that fired and whose market has no yes or no result (a void, a refund, a walkover, an abandoned match, a result missing from the list) is booked as price refunded and fee kept: a fee-only loss. It is COUNTED in n, in the profit factor and in z, in the rule and in the placebo alike, and the number of such bets is printed beside n. Lists are read with status settled and the result field is read as given; no list is filtered on result.
5. **Forensics rules 4b (19:03Z) applied:** every kill line or check computed over the whole development sample (the cost line, the family start check, which titles or families are 'in') is labelled "selected on development": it can close a family, it cannot support a result; only the frozen held-out read can. The same lines are frozen, not recomputed, for the held-out. No haircut is built from a later candle. The stage 1 "under 600 projected bets" line is such a kill line.
