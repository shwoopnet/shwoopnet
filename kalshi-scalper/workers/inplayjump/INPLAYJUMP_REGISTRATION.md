# INPLAYJUMP, follow a match market's own in-play jump and hold: rule registration

**Registered Nov 12, 2026, before any price or result of these markets was read by anyone on this desk.** Written by Idea Desk B on the Head of R&D's order of 18:53Z for the owner's Friday deadline; built by Desk A on the Testing Desk's engine. Frozen families, series, dates and constants: `inplayjump/INPLAYJUMP_SERIES.json`.

`INPLAYJUMP | family: a single market's own in-play price jump, followed; buy the side that jumped one minute later, hold to settlement | risk class: mid price (20c to 85c), 1 contract, hundreds of matches a day | stage Idea, registered as a rule`

**Nothing here permits an order. It is a rule registered for one development read and, on the Head's go, one held-out read. Tries: 5, one for each family.**

## What has been seen so far

Shape, times and volume only, from the Nov 10 census listing: these families list a match-winner market and nothing that closes during the match; contracts a market; and, for three of them, a clock time in the ticker that matched the market's close minus the length of a game. No price and no result of these series was printed or used.

## Why these families, and the one state Kalshi gives

They are where the events are (matches on Nov 10: e-soccer 450, ITF tennis 302, table tennis 147, challenger tennis 92, e-basketball 84), and Kalshi lists no set, map or half market for them. With score sites barred, the only state is the match market's own price path. A one-minute jump in that price says something just happened in the match.

## The direction is chosen now: FOLLOW. One direction, one try a family.

**Rule in one sentence:** when a team's or player's match contract jumps 10c or more in one minute during play, buy that same contract at its ask one minute later and hold it to the end.

**Why follow and not fade:**
1. The fade has been run. V2's SWING1 bought the side that had just DROPPED 25c in play and held: FALSIFIED (302 trades, cash PF 0.99 and 1.06). I do not register a direction that has already failed.
2. V2's SC1 ran both directions on tennis with a time exit of 2 or 5 minutes: FALSIFIED, four rules, 62,747 events, about -4.3c a trade, which is about one round trip. A time exit pays the spread twice. Holding to settlement pays it once.
3. **The named other side:** resting limit orders placed before the point or the goal by people who are not watching, in low-tier markets where there are hundreds of matches a day and few makers on each. If those orders are still being filled a minute after the jump, the jumper's price is still too low.

**Why it may well fail, said first:** a market that has just jumped has usually been moved by the people who know the score. One minute later the price is theirs, not the stale orders'. SWING1's result for the faller (about fair, less costs) implies about the same for the riser. This is the mirror image of a falsified test, and I expect it to lose the cost.

## The rule, every number pinned

1. **Candles:** one-minute candles of the match-winner contracts; a minute counts only if 0 < bid < ask < 1 at its close (two-sided). Mid = (bid + ask) / 2.
2. **In play** (file, `in_play_rules`):
   - *Clock families* (e-soccer, table tennis, e-basketball): the ticker carries the scheduled start S as a clock time, read as US Eastern. A minute is in play if its candle ends at or after S + 60 seconds. Guard: the market closed 4 to 90 minutes after S, else the match is dropped and counted.
   - *Tennis* (ITF, challenger): no start time can be read. A minute t is in play if at least 3 of the 20 one-minute steps ending at t - 1 moved the mid 2c or more. Backward-looking only. **The close time is never used to decide what is in play:** conditioning on "the match ended soon after the jump" would select the jumps that held, which is a look-ahead I found while writing this and have kept out.
3. **The jump (the state):** at an in-play minute t, a contract's mid is 10c or more above its mid at minute t - 1, both minutes two-sided, the candle of minute t shows volume above zero, and its mid at t - 1 was between 15c and 75c. In e-soccer the Tie contract is never the jumper.
4. **One decision a match:** the FIRST minute at which a contract qualifies. If two contracts qualify in the same minute, no bet (it cannot happen in a two-way market; in e-soccer it is dropped and counted).
5. **Entry:** at the close of minute t + 1, if the jumper is two-sided there, its ask is between 20c and 85c and its spread is 4c or less: buy 1 contract at that ask plus 1c. If not, the match gives no bet and is counted; there is no second chance later in the match.
6. **Fee:** 0.07 x price x (1 minus price), rounded UP to the next whole cent.
7. **Exit:** hold to settlement. Result: the market's own result, read only for matches where a bet was made.

## Cost kill, and the placebo

- **Cost:** at the entry minute, round trip = spread plus two fees at the mid. **A family whose median round trip over its qualifying entries is above 5c is CLOSED on cost and no result of it is read.**
- **Placebo (the same entry at a matched no-jump minute):** in every development match of the family, the first in-play minute at which neither contract's mid has moved 5c or more over the previous 5 minutes; at that minute "buy" the contract with the higher mid at its ask plus 1c if the ask is 20c to 85c and the spread 4c or less; hold. That is what holding the current leader earns when nothing has just happened. Its results are grouped by the price paid (20 to 30c, 30 to 40c, and so on to 80 to 85c) and re-weighted to the rule's own mix of prices, so the two are compared at the same price level.

## Order of the read (fixed)

1. Per family, no result read: matches listed; in-play definable; matches with a jump; entries that pass step 5; the cost line.
2. A family closed on cost stops there.
3. The rule and the placebo are scored for the families that remain.

## Samples (date constants, per family; file)

Windows are sized so each family has about 3,000 development matches. Held-out is the block straight after, about half as long, **not pulled** until the Head's go.

| Family | Development: market closes | Held-out: market closes |
|---|---|---|
| E-soccer | 2026-10-15 to before 2026-10-23 | 2026-10-23 to before 2026-10-27 |
| ITF tennis, singles | 2026-10-10 to before 2026-10-23 | 2026-10-23 to before 2026-10-30 |
| Table tennis, Liga Pro | 2026-10-01 to before 2026-10-23 | 2026-10-23 to before 2026-11-03 |
| Challenger tennis | 2026-09-12 to before 2026-10-23 | 2026-10-23 to before 2026-11-13 |
| E-basketball | 2026-09-15 to before 2026-10-23 | 2026-10-23 to before 2026-11-11 |

Every match in a window is used; nothing is sampled or capped. If a series did not exist for all of its window, the family has what it has.

## What is reported, per family (counts first)

Bets; wins; mean price paid; cash profit factor; net cents a contract; both halves of development by date; the share of bets paid 70c to 85c; the largest share of the net carried by one day; z with days as the cluster; the placebo's net cents a contract at the same price mix, and the difference with its standard error.

## Verdict on development, fixed now, per family

- Under 300 bets: NOT_ENOUGH_DATA at n = x.
- 300 or more bets and cash PF under 1.0, overall or in either half: FALSIFIED.
- Cash PF 1.5 or better, both halves above 1.0, AND the rule's net above the placebo's by two standard errors or more: "development bar met"; the held-out is asked for the same hour.
- Anything else: "bar not met".
- **The research bar:** cash PF 1.5 or better on development AND held-out, and a one-sided z of 5.46 or more on the two together (shared count about 2,113,000 tries). Nothing short of that is reported as a pass. A family that only matches its placebo has no jump effect, whatever its profit factor.

## Declined list and earlier tests, written out

- **Not the in-game lag card** (closed Nov 12): that was one market lagging ANOTHER market, with a time exit. This is one market's own move, bought and held.
- **Not a cheap-side sweep** ("Cheap-side price, regime and grammar rules on the 15 minute series"): not those series, one rule and not a grammar, and it buys at any price in a stated band, 20c to 85c.
- **Not a favourite rule** ("Favourite-and-hold"): the ask is capped at 85c, so the share of entries above 88c is zero by construction; the share at 70c to 85c is reported. It is still a contract that has just become MORE likely, and I say so: if most bets turn out to be paid above 70c, the Head should read it as close to that row.
- **Not a lock.** Every bet can lose.
- **Earlier tests of this entry mechanism (the market's own in-play jump):** SC1 (follow and fade, time exit, tennis: FALSIFIED four times) and SWING1 (fade, hold: FALSIFIED). INPLAYJUMP is the one combination neither ran: follow, hold. If the Head counts "own in-play jump" as one family, this is a third and last look at it, on lower-tier markets than either earlier test.

## Can it reach about 1,000 bets? Yes, in every family, if the markets are quoted at all

One decision a match, and a 10c one-minute move happens in most tennis matches (a break of serve) and most e-soccer games (a goal). If half the development matches give a bet, that is about 1,500 bets a family in development and about 750 held-out. The count is not the constraint here; the cost line and the price are.

## Requests

- **Lists:** settled markets of 7 series inside the development windows only (close-time floor and ceiling on every call, so held-out markets are never listed), plus 5 fee-field reads. E-soccer about 11 pages, ITF about 8, table tennis about 7, challenger about 8, e-basketball about 7: **about 45 requests.**
- **Development candles:** one batched call holds 100 contracts and 10,000 candles. E-soccer (3 contracts, 40 minutes): about 33 matches a call, about 110 calls. ITF and challenger tennis (2 contracts, the 300 minutes before the close): about 16 matches a call, about 190 calls each. Table tennis (2 contracts, 70 minutes) and e-basketball (2 contracts, 60 minutes): about 50 matches a call, about 60 calls each. **About 610 requests, one run.**
- Held-out candles: about half that, on the Head's go.

## Honest limits

1. Candle freshness was measured on the Bitcoin 15 minute series only. Every output carries: "candle freshness measured on Bitcoin 15 minute only, not on these markets".
2. A candle is one instant a minute. "The ask one minute later" is the ask at the next minute's close, 60 to 120 seconds after whatever happened. A real order would not fill at that ask every time; Forensics measured 59% to 73% at the price seen on other markets, and these are thinner.
3. For tennis, "in play" is inferred from the price being alive. A news move before a match (a withdrawal) could be counted; such markets are usually voided, and the count of bets made more than 6 hours before the close is reported so it can be seen.
4. The Eastern reading of the ticker clock was checked on three families, one market each. The guard drops matches where it fails.
5. E-soccer and e-basketball are people playing video games for a few minutes; table tennis and ITF tennis are low-tier sport. Whoever moves these prices may know more than a score.
6. **My odds: about 2% that any one family meets the development bar (with over a thousand bets, luck alone will not produce a profit factor of 1.5); about 1% a family that it passes the research bar; about 4% that any of the five does. The likely result is FALSIFIED in most families, near the cost.**

## AMENDMENT 1, Nov 12, 2026, 19:05Z, before any list or candle has landed: the clock guard no longer drops single matches

The Forensics desk's audit of another registration of mine (MAPBREAK) found conditions where a time known only after the bet decided which bets exist. The same kind of condition was in this file: "Guard: the market closed 4 to 90 minutes after S, else the match is dropped and counted." A game that ends early or late could be tied to who wins. It is replaced:

- **No match is dropped because of when its market closed.** In the clock families every match is in play from S + 60 seconds, as read from its ticker.
- **The Eastern reading of the ticker clock is checked once for the whole family, not match by match:** the share of the family's development matches whose market closed 4 to 90 minutes after S is printed. If that share is under 80%, the reading is wrong for that family, the family is reported as "start not derivable" and no result of it is read. A family-level check cannot select bets by their outcome.
- The file `INPLAYJUMP_SERIES.json` carries the old wording in its `in_play_rules` text; this amendment overrides it.

Also confirmed for the builder (Desk A's questions of 18:56Z), none of it new: the bought contract is the JUMPER's own contract, bought as YES at its own ask (never a NO of the other contract); the jump is 10c on the two-sided minute-end mid with volume above zero in that minute; there is no cooldown because there is one decision a match (the first qualifying jump, no second chance); the direction is FOLLOW; the placebo is the one registered above (the first quiet in-play minute, the contract with the higher mid, re-weighted to the rule's price mix), NOT a matched minute of the same contract in the same match, because the nearest minute at the same price is usually just after the jump and would be the same bet a few minutes later.
