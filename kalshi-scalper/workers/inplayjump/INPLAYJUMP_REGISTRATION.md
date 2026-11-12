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

## AMENDMENT 2, Nov 12, 2026, 19:15Z, before any list or candle has landed (rulings of the Head of R&D at 19:01Z, 19:02Z, 19:03Z, 19:07Z and 19:08Z; findings of the Forensics desk, Auditor B and Desk A)

Where this section and anything above differ, this section is right. Tries unchanged: 5.

1. **Nothing after the decision is used.** No decision input, filter or universe test uses a market's close, its settlement, or anything after the jump minute t (the entry reads the close of t + 1 and nothing later).

2. **No candle window is anchored on the close, in any family.** "First qualifying jump" must mean first.
   - *Clock families:* a match's window STARTS at its ticker clock S and runs forward to the close.
   - *Tennis (ITF, challenger):* a match's window STARTS at the market's open time and runs forward to the close. The sentence "the 300 minutes before the close" is deleted.
   - If a window is too long for one request, the request is split; the window is never shortened from the end.
   - **A cheaper retrieval that gives the same decisions, allowed for tennis (markets are open about 18 hours):** first pull HOURLY candles from the open forward. An hour in which, for each contract, (bid high minus bid low) plus (ask high minus ask low) is under 0.20 cannot hold a 10c one-minute move of the mid, so it cannot hold a qualifying jump. Minute candles are then pulled from 30 minutes before the first hour that is NOT of that kind (or is one-sided or missing), forward to the close, with no further skipping. Every hour skipped is proven empty from data inside that hour, so the first jump found is the first jump. The builder may instead pull every minute from the open; the decisions are the same.

3. **The placebo is matched to where the rule bets, one for one** (replaces the "first quiet in-play minute" placebo). For each bet of the rule, in match X at elapsed minute e (clock families: minutes from S to the jump minute; tennis: minutes from X's first in-play minute to the jump minute): take the NEXT match of the same family after X (clock families: by scheduled start, then ticker; tennis: by market open time, then ticker) that has not yet served as a placebo. At that match's own elapsed minute e: if the minute exists, is in play, no contract has made a qualifying jump at or before it, and neither contract's mid has moved 5c or more over the previous 5 minutes, then at the close of minute e + 1 buy the contract with the higher mid at its ask plus 1c, if the ask is 20c to 85c and the spread 4c or less; hold. If any condition fails, go to the next match, up to 20 matches; if none, that bet has no placebo (counted). The placebo therefore buys at the same instant after the same elapsed time and by the same price rule as the real bet, and uses nothing later than its own minute e + 1. It is still grouped by price paid in 10c steps and re-weighted to the rule's price mix. The median elapsed minute of the rule and of the placebo are printed side by side.

4. **Cost kill:** the ONE-WAY entry cost at qualifying decision minutes: the median of (ask minus mid) plus the entry fee as charged (0.07 x price x (1 minus price) at the price paid, rounded up to the next cent). Closed on cost if that median is above 4c. Why (Head of R&D's ruling of 19:02Z, on Desk A's flag, changed before any price was read): a rule that buys and holds to settlement pays no second spread and no second fee, and with the one-contract fee rounded up to 2c a side the old round-trip line would have closed every market whose spread is above 1c before one bet was scored. It is a request-saving screen, NOT the bar: the scored profit factor pays the real ask, the 1c slip and the fee.

5. **One void rule (Head of R&D, 19:08Z, the same for every hold-to-settlement card):** a bet that fired and whose market has no yes or no result (a void, a refund, a walkover, an abandoned match, a result missing from the list) is booked as price refunded and fee kept: a fee-only loss. It is COUNTED in n, in the profit factor and in z, in the rule and in the placebo alike, and the number of such bets is printed beside n. Lists are read with status settled and the result field is read as given; no list is filtered on result.

6. **Forensics rules 4b (19:03Z) applied:** every kill line or check computed over the whole development sample (the cost line, the family start check, which titles or families are 'in') is labelled "selected on development": it can close a family, it cannot support a result; only the frozen held-out read can. The same lines are frozen, not recomputed, for the held-out. No haircut is built from a later candle.

7. **Confirmed for the builder (Desk A, 19:01Z):** e-soccer needs two contracts a match, not three (the Tie is never the jumper and never bought). The placebo's timing is point 3 above. Desk A's five-request cost pilot was approved by the Head after this amendment.

8. **Requests, corrected (my estimate; the exact count comes from the lists):** one batched request has one time range for all its tickers and matches start at staggered times, so the earlier "about 610" was low. Clock families from S: about 130 (e-soccer), 170 (table tennis) and 210 (e-basketball) if each family is pulled alone, fewer if matches of different families that start in the same half hour share a request. Tennis by the two-pass retrieval: about 80 hourly requests and about 190 to 250 minute requests in each of the two tennis families; by a plain pull from the open it would be about 850 each. The Head rules on the count when Desk A has it.

## AMENDMENT 3, Nov 12, 2026, 19:17Z, before any list or candle has landed: the hourly skip rule made safe at the hour boundary

Found by me on re-reading Amendment 2, point 2: if an hourly candle's high and low cover only quotes made INSIDE the hour, a move that is the first quote of an hour would show in neither hour's range. So the skip test for hour H includes the level the hour started from: for each contract, take the bid range over {bid high of H, bid low of H, bid close of H minus 1} and the ask range over {ask high of H, ask low of H, ask close of H minus 1}; hour H may be skipped only if bid range plus ask range is under 0.20 for every contract, and hour H minus 1 has a two-sided close. The first hour after the open is never skipped. Nothing else changes.

## AMENDMENT 4, Nov 12, 2026, 19:20Z, before any list or candle has landed (Head of R&D's ruling of 19:17Z on the tennis retrieval; it replaces the hourly skip rule of Amendments 2 and 3)

Where this section and anything above differ, this section is right. Tries unchanged: 5 (or 4, see point 4).

1. **One skip rule, tight enough that the screened retrieval and a full minute pull give the same bets AND the same placebo.** The tennis rule uses three things from minute candles: a 10c one-minute move (the jump), 2c one-minute moves (the in-play test) and a 5c move over five minutes (the placebo's quiet test). The smallest of these is a 2c move of the mid, which needs at least 4c of bid movement plus ask movement inside one minute, and a minute lies inside one hour. So:
   - For each contract and each hourly candle H, take the bid range over {bid high of H, bid low of H, bid open of H, bid close of H minus 1 if there is one} and the ask range the same way.
   - **Hour H may be skipped only if, for every contract of the match, bid range plus ask range is 3c or less and all those values are present.** (Prices are whole cents, so "3c or less" is "under 4c" without a rounding question.)
   - Minute candles are pulled from 30 minutes before the first hour that may NOT be skipped, forward to the close, with no further skipping.
   - Before that first hour no minute can be in play (no 2c step exists), so no jump and no placebo minute can exist there. A move that is the first quote of an hour is caught because the previous hour's close is inside the range. The screen is applied hour by hour; no pair of hours can hide a move, because every one-minute move lies inside one hour whose range includes the level it started from.
2. **The placebo's minutes come from the same pull.** Because the screen keeps every hour that could hold a 2c move, every match's in-play minutes are pulled whether or not it ever jumped, and the placebo is bought from a real minute candle at t + 1 by the same price rule, never from an hourly candle. No separate placebo pull exists; its cost is inside the count.
3. **Before any pull, Auditor B proves equivalence on a synthetic file** (the Head's condition): the screened retrieval and a full minute pull must give the identical set of bets and placebo bets, including a jump in the first minute of an hour, a jump whose bid moves at the end of one hour and whose ask moves at the start of the next, and a never-jumped match used as a placebo. If the proof fails, tennis is pulled minute by minute from the open or dropped under point 4.
4. **Request ceiling (the Head's ruling):** the full candle count for the five families, placebo included, goes from Desk A to the Head after the lists land and the five-request pilot passes the cost line. Over 1,200 it is split by family across runs, clock families first. **Ceiling 1,800 requests for this card. If the count is above that, the more expensive of the two tennis families is dropped before any of its candles are pulled, and the card has 4 tries.** Which family that is depends only on request counts from the lists, never on a price or a result.
5. **Honest cost warning:** a 3c screen skips only truly dead hours. If thin pre-match quotes flicker by a few cents every hour, little is skipped and tennis costs close to the full pull (about 850 requests a family by my estimate). Then point 4 decides.
6. A sixth family (ITF doubles) was asked for and refused by the Head: this is the third and last look at this idea and stays at five families.

## AMENDMENT 5, Nov 12, 2026, 19:26Z, before any list or candle has landed (the Forensics desk's and Auditor B's reads of Amendments 2 to 4, Desk A's build questions, standing rule (h))

Where this section and anything above differ, this section is right. Tries unchanged.

1. **Published evidence and revised odds.** Idea Desk C's reading of the published work (`idea_desk_c/DIRECTION_EVIDENCE_NOV12.md`, commit 338ebbde on `claude/idea-desk-c`; 26 sources, 9 verified from full text): liquid exchange soccer shows no drift after a goal; where continuation exists it is mostly gone within 2 to 6 minutes and the largest published return is 2.8%; thin markets showed 10 to 15 minutes of continuation; surprising events reverse. **My odds are revised from about 2% to about 1% a family that the development bar is met.** FOLLOW stays as registered.
2. **The tennis screen, pinned (replaces the wording of Amendment 4 point 1, same rule):**
   - For each contract and hour H: bid range = max(bid high, bid open, last present bid close before H) minus min(bid low, bid open, last present bid close before H); the ask range the same way. "Last present close" skips over hours with no candle.
   - **Skip H if and only if bid range plus ask range is under 0.04 minus 1e-9 for every contract of the match.** The sentence "prices are whole cents" is deleted (some markets tick in tenths of a cent near the ends); the test is safe at any tick.
   - **An hour with no hourly candle is a dead hour and is skipped.** Kalshi leaves out a candle for a period with no change. The first hour after the open may be skipped like any other (it uses its own open); Amendment 3's "never skipped" is withdrawn, since it would start every pull at the open.
   - Minute candles are pulled from 30 minutes before the first hour that is not skipped, forward to the close, with no further skipping.
3. **Two self-checks on the pulled data, printed per tennis family as counts (Forensics):** (a) minute candles that fall in an hour with no hourly candle; (b) minute closes whose bid or ask lies outside that hour's own low to high. **If either count is above zero, that family's screen is void:** it is pulled in full from the open, or dropped under Amendment 4 point 4. Auditor B's synthetic proof covers the logic; these two cover Kalshi's data.
4. **A missing minute is not carried forward (the strict reading).** A step from minute t minus 1 to t exists only if both minutes have a candle and both are two-sided. A missing or one-sided minute t minus 1 means no step and no jump at t; it also adds nothing to the in-play test's count of 2c steps. The placebo's quiet test is: minute e is present and two-sided, and the highest mid minus the lowest mid over the present two-sided minutes from e minus 5 to e is under 5c, for each contract.
5. **With points 2 to 4 the two-pass retrieval is the definition for tennis** once Auditor B's proof passes and both self-checks are zero. The earlier line "the builder may instead pull every minute from the open" remains true only as the fallback of point 3.
6. **Placebo, confirmed for the builder (Desk A):** no wrap-around at the end of a family's list (a bet near the end may have no placebo, counted); a match has "served" only when a placebo BET was made in it.
7. **Standing rule (h), shared held-out windows (Head of R&D, 19:22Z, on a Forensics finding; before any held-out data exists).** INPLAYJUMP holds out, per family, the block after its development window. E-soccer closes are also held out by ESOCTIE and REMATCH; esports are not in this card. No list or candle request may cover a held-out close of these series until every card that holds them out has finished its development read, has its scorer frozen by commit and sha256 on rnd-queue, and has a committed read-once marker; a card that failed development blocks nobody. Then ONE joint held-out pull per shared series, on the Head's go, into a folder whose name starts HELDOUT_, which every scorer refuses by default and which nobody opens, greps, counts or summarises outside an approved read. Development pulls end before the held-out cut by date bounds in the job file, not by a filter after the pull. **Nov 10 is dropped from the held-out:** from the challenger tennis held-out window (2026-10-23 to before 2026-11-13) and the e-basketball held-out window (2026-10-23 to before 2026-11-11) markets closing from 2026-11-10 00:00 UTC to before 2026-11-11 00:00 UTC are left out, because the census listing of that day (which this desk's counting scripts read for times and tickers) already sits in a landed file with its results. The e-soccer, ITF and table tennis held-out windows end before Nov 10 and are unchanged.
8. PREMOVE was withdrawn by its author (19:26Z), so no window of this card needs to start before S on its account. Clock families start at S (the builder may keep a few minutes before S so that the first in-play minute has its minute t minus 1).
