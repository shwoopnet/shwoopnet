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

## Build confirmations, Nov 12, 2026, 18:25Z, before any data (asked by the Testing Desk, build 8bdbdbce on `claude/testing-desk`)

1. **Lists job:** 16 requests, at most 100 pages (30 to 45 expected), cap 114. The "about 50 requests" above was a page estimate. Every settled list carries the close-time ceiling, so held-out matches are never listed.
2. **The pre-match minute needs three contracts two-sided together:** the map-1 winner's match contract and BOTH map-1 contracts, in the same minute. One minute serves the model and the placebo, so the gap share and the placebo share are measured on the same matches. It can lower the pre-match fill rate; the reader also counts the matches lost only because the map-1 contracts were never two-sided in the same minute as the match contract, and that count is reported beside each title's result. The rule is not changed after data whatever that count is.
3. **Round trip at the look** is computed per match contract (both teams' contracts, spread plus two fees at that contract's mid), median over contracts, for the cost kill. **On the gap line, "spread 4c or less" means the spread of the contract being bought,** the cheaper side's own match contract.
4. The reader was tested to be blind to the match result and to the results of maps 2 and 3 (every other such result flipped, identical output).

## AMENDMENT 1, Nov 12, 2026, 18:28Z, before any list or candle of these markets has landed: MAPBREAK is registered as a RULE, 1 try

**Why (Head of R&D, 18:26Z, on the owner's Friday deadline):** the deadline is a read against the bar, not a measurement. So the first pull's output is BOTH the measurement and the development read. The held-out third is pulled and read once, only on the Head's go. Everything above stands except where this section says otherwise; where they differ, this section is right.

**Tries: 1** for the card (the titles that pass their kill lines are pooled into the one rule). It is added to the shared count (about 2,113,000 tries; bar: one-sided z 5.46).

### The rule

At the look (the first whole minute at or after map-1 close + 120 seconds, forward to + 5 minutes if not two-sided), take the cheaper side as defined above. **If its gap is 8c or more and the spread of its own match contract is 4c or less: buy 1 contract.** One bet a match. Hold to the end of the match.

- **Price paid:** the ask at the look plus 1c (a limit one cent through the ask, booked as filled there; the Forensics desk measured a 59% to 73% fill at the price seen and 76% to 86% with one more cent on other markets, nothing on esports).
- **Fee:** 0.07 x price x (1 minus price), rounded UP to the next whole cent, as one contract pays it.
- **Result:** the match market's own result, read ONLY for matches where the rule fired. Win pays 1 minus the price paid minus the fee; loss costs the price paid plus the fee.

### Order of the read (fixed, so there is no choosing after the fact)

1. Per title, with no match result read: the counts, the cost line, the gap share and the placebo share, exactly as registered above.
2. **A title is OUT of the rule** if it has under 150 matches filled at the look, or its median round trip is above 5c, or its gap share is under 10%, or its gap share is under twice the placebo's. These are the kill conditions. If every title is out, the card is CLOSED and no match result is read at all.
3. The rule is scored on the titles that are in, pooled, each title also shown alone.

### Samples (date constants)

- **Development:** every best-of-three match whose match market closed from 2026-09-12 to before 2026-10-23 00:00 UTC. **The cap of 1,500 matches is REMOVED** (it was there to save requests on a measurement; bets are now what count).
- **Held-out:** closes from 2026-10-23 00:00 UTC to before 2026-11-13 00:00 UTC. Not pulled until the Head's go; read once.

### What is reported for the rule (counts first)

Bets; wins; mean price paid; cash profit factor; net cents a contract; the same for each half of development by date and for each title; the largest share of the net carried by one day; a one-sided z with days as the cluster.

### Verdict on development, fixed now

- Under 100 bets: NOT_ENOUGH_DATA at n = x.
- 100 or more bets and cash PF under 1.0, overall or in either half: FALSIFIED.
- Cash PF 1.5 or better with both halves above 1.0: "development bar met"; I ask the Head for the held-out pull the same hour.
- Anything else: "bar not met".
- **The research bar itself:** cash PF 1.5 or better on development AND on the held-out, and a one-sided z of 5.46 or more on the two together. Nothing short of that is reported as a pass.

### Can it reach about 1,000 bets? Said plainly

About 78 matches a day on the one day I have seen (a Tuesday, a lower bound): about 3,200 in development and about 1,600 in the held-out. If the rule fires on 10% of matches that is about 320 and 160 bets; at 20%, about 640 and 320. **So on the 61 days the live endpoint holds, it reaches about 1,000 bets only if it fires on about one match in five. At one in ten it does not, and the read would then be "not enough to meet the bar" however good the profit factor looks.** The only way to more events is the history endpoint (matches before 2026-09-12), which needs its own list read first and one candle request a contract; that is a separate amendment on the Head's word, not part of this one.

### Requests after this amendment

Lists: unchanged (16 requests, at most 100 pages). Candles for development: about 3,200 matches at four contracts each; matches sharing a scheduled start share a request: my estimate 250 to 450 requests, one run. The exact count comes from the lists. Held-out candles: about half that, on the Head's go.

## AMENDMENT 2, Nov 12, 2026, 18:32Z, before any list or candle of these markets has landed: a second look, the break before map 3

**Why:** the deadline needs bets. A best-of-three that stands at one map each has a second stopped-play break, before the deciding map, and the same pre-match price values it with no extra input. It adds about 45% more looks from the same matches and the same pull (my estimate of how often a best-of-three goes to a third map; not measured).

**The second look.** When the map-2 market closes and the match market does NOT close within 10 minutes of it, the match stands at one map each (a team that wins map 2 after winning map 1 ends the match, and then the match market closes with it). No result of map 2 is read: the state is taken from the two close times alone. The look is the first whole minute at or after (map-2 close + 120 seconds), forward to + 5 minutes if not two-sided, as for the first look. **Guard:** the match market must close at least 15 minutes after map 2 closed; if it closes between 10 and 15 minutes after, the match is dropped from the second look and counted.

**Value at the second look:** the match is now one map. For the team that won map 1, the value is **q**, its per-map chance from the pre-match price (the same q as above); for the other team, 1 minus q. Gap, cheaper side, the 8c and 4c lines, price paid, fee and result are exactly as in Amendment 1.

**Known leans at this look:** the deciding map is usually picked by neither team, so the map-pick lean is smaller here than at the first look. The learning lean remains (one map each says the teams are closer than the pre-match price said, so the model OVERVALUES the pre-match favourite here). The placebo is unchanged: it measures the model against the map-1 market before the match.

**How it joins the rule.** One bet per look, so a match can give two bets (after map 1, and before map 3), never two at the same look. The kill lines are computed per title for each look separately (150 filled, cost, 10% gap share, twice the placebo); a title can be in at one look and out at the other. The rule's read pools all bets from the looks and titles that are in, and shows each look and each title alone.

**Tries: 2 for the card** (one for each look), counted that way to be safe; the Head may rule it one.

**Events, said plainly:** about 3,200 development matches give about 3,200 first looks and about 1,400 second looks, 4,600 in all; the held-out about 2,300. At a firing share of 10% that is about 460 development bets and 230 held-out; at 15%, about 690 and 345, **which reaches about 1,000 bets over the two samples together.** At 10% it does not.

**Requests:** the lists are unchanged (map-2 close times are already in the map list). The candle window of a match that went to a third map runs to map-2 close + 5 minutes, about 60 more candles on each of two contracts; the request count rises by perhaps a fifth.

## AMENDMENT 3, Nov 12, 2026, 18:32Z, before any list or candle has landed (Head of R&D's rulings of 18:30Z)

1. **Amendments 1 and 2 are accepted as written. The card counts 2 tries.**
2. **Reporting:** the two looks are shown as separate lines and pooled. One trade per match and look. **Two looks from one match are not independent: the standard error and the z are computed with the MATCH as the cluster, and also with the day as the cluster; the verdict uses the smaller z of the two.**
3. **Four history list calls are added to the lists job** (`/historical/markets` for the four match series; the job is now 20 requests). They only count how many best-of-three matches exist before 2026-09-12. If there are thousands, I send the Head the candle request count for a history stage and the Head rules.
4. **Any older matches join DEVELOPMENT only.** The held-out block stays the matches closing from 2026-10-23 to before 2026-11-13 and is not enlarged.
5. For a history stage the same rules apply unchanged (best-of-three from the total-maps market, start from the ticker's clock with its guard, the pre-match minute, both looks). If the history endpoint does not hold the map or total-maps markets of older matches, those matches cannot be used and are counted as such; nothing is guessed.

## AMENDMENT 4, Nov 12, 2026, 19:00Z, before any list or candle has landed: two look-ahead defects removed (found by the Forensics desk's audit)

The Forensics desk audited the venue code before the read and found two places where a close time known only AFTER the look decided which bets exist. Both were in my registration text, not in the build. Both are removed here. Where this section and anything above differ, this section is right.

1. **First look: no guard on a later time.** The sentence "the map-2 market must close at least 15 minutes after map 1 closed; otherwise the match is dropped" is DELETED for the first look. A very short map 2 is a stomp or a forfeit and is tied to who wins; the look is 2 to 5 minutes after map 1 and cannot know it. Every best-of-three match with a derivable start gets a first look. (How many had a map 2 that closed under 15 minutes after map 1 is printed as a count and changes nothing.)

2. **Second look: the state comes from the map-2 market's own result, not from the match market's close.** Amendment 2 read "one map each" from the match market staying open more than 10 minutes after map 2. That is a time after the look, and an inexact stand-in. It is replaced: **the match stands at one map each when the map-2 market's result names the team that LOST map 1.** That result is public at the map-2 close exactly as map 1's is at its own close, and it is the state, so it is read. The 10 to 15 minute band and every use of the match market's close time are DELETED. The match result and map 3's result are still never read before scoring.

3. **A check of the assumption the card rests on, added as a count from data known at the look:** for each look, whether the winning team's own map contract had a bid of 0.90 or more in its last two-sided candle before that map market closed. If the map market's close is when the map ended, that share should be near all. It is printed per title and look. Kalshi posts a map's result about three minutes after its close, a minute or so after the look; a live bot would read the winner from that last quote, and this count says how often it could.

4. **On the result page:** the number of bets AND the number of distinct matches they come from. Two looks of one match are two bets in n and in the profit factor and one cluster in z (Amendment 3).

Nothing else changes: the look times, the model, the placebo, the kill lines, the samples, the tries (2).

## AMENDMENT 5, Nov 12, 2026, 19:15Z, before any list or candle has landed (rulings of the Head of R&D at 18:58Z, 19:02Z and 19:08Z)

Where this section and anything above differ, this section is right. Tries unchanged: 2.

1. **Amendment 4 stands as the Head ordered it, restated in the Head's words.** (a) The first look is taken for every best-of-three whose map 1 has closed; nothing later can remove it. (b) "One map each" is read from the map-1 and map-2 markets' own RESULTS; the second look is the first whole minute at or after map-2 close plus 120 seconds, stepping forward to plus 5 minutes if not two-sided; nothing later decides whether the look exists. This replaces Amendment 2's sentence "the state is taken from the two close times alone" and its 10 and 15 minute bands.
2. **Cost kill, per title and per look:** the ONE-WAY entry cost at qualifying decision minutes: the median of (ask minus mid) plus the entry fee as charged (0.07 x price x (1 minus price) at the price paid, rounded up to the next cent). Closed on cost if that median is above 4c. The price paid is the ask plus 1c. Why (Head of R&D's ruling of 19:02Z, on Desk A's flag, changed before any price was read): a rule that buys and holds to settlement pays no second spread and no second fee, and with the one-contract fee rounded up to 2c a side the old round-trip line would have closed every market whose spread is above 1c before one bet was scored. It is a request-saving screen, NOT the bar: the scored profit factor pays the real ask, the 1c slip and the fee.
3. **One void rule (Head of R&D, 19:08Z, the same for every hold-to-settlement card):** a bet that fired and whose market has no yes or no result (a void, a refund, a walkover, an abandoned match, a result missing from the list) is booked as price refunded and fee kept: a fee-only loss. It is COUNTED in n, in the profit factor and in z, in the rule and in the placebo alike, and the number of such bets is printed beside n. Lists are read with status settled and the result field is read as given; no list is filtered on result.
4. **Forensics rules 4b (19:03Z) applied:** every kill line or check computed over the whole development sample (the cost line, the family start check, which titles or families are 'in') is labelled "selected on development": it can close a family, it cannot support a result; only the frozen held-out read can. The same lines are frozen, not recomputed, for the held-out. No haircut is built from a later candle.

## AMENDMENT 6, Nov 12, 2026, 19:26Z, before any candle has landed (standing rule (h); published evidence)

1. **Standing rule (h), shared held-out windows (Head of R&D, 19:22Z, on a Forensics finding; before any held-out data exists).** MAPBREAK holds out the four esports titles' closes from 2026-10-23. PREMOVE, the other card on these series, was withdrawn unread by its author, so MAPBREAK is the only card holding them out today. No list or candle request may cover a held-out close of these series until every card that holds them out has finished its development read, has its scorer frozen by commit and sha256 on rnd-queue, and has a committed read-once marker; a card that failed development blocks nobody. Then ONE joint held-out pull per shared series, on the Head's go, into a folder whose name starts HELDOUT_, which every scorer refuses by default and which nobody opens, greps, counts or summarises outside an approved read. Development pulls end before the held-out cut by date bounds in the job file, not by a filter after the pull. **Nov 10 is dropped from the held-out:** from MAPBREAK's held-out window (2026-10-23 to before 2026-11-13) markets closing from 2026-11-10 00:00 UTC to before 2026-11-11 00:00 UTC are left out, because the census listing of that day (which this desk's counting scripts read for times and tickers) already sits in a landed file with its results.
2. **Published evidence:** Idea Desk C's reading of the published work (`idea_desk_c/DIRECTION_EVIDENCE_NOV12.md`, commit 338ebbde on `claude/idea-desk-c`; 26 sources, 9 verified from full text) found nothing published on map or period breaks. My odds are unchanged (about 2% that the rule reaches the development bar), and they rest on the measurement alone.
3. PREMOVE's wider window (S minus 70 minutes on the match contracts) is no longer needed; the candle window is the registered one (from S minus 40).

## AMENDMENT 7, Nov 13, 2026, 00:04Z, BEFORE any match result is read (Head of R&D's ruling of 00:04Z; to be coded by the Testing Desk and re-hashed for Auditor B): the map state must be OBSERVABLE at the look

**Why.** Step 1 (counts only, no match result) showed that the winner's map contract had a bid of 0.90 or more in its last two-sided candle before the map market closed in only 42% to 60% of looks, by title. Kalshi posts a map's result about three minutes after its close, which is after the first minute a look can fall on. So a live bot, or a replay from the recorder's log, cannot always know who won the map at the look, and the scorer so far took the state from the result field. That is a state the trader may not have had.

**One definition, the same for the scorer, a live build and the recorder's log.** At a look (the registered minute: the first whole minute at or after the map market's close plus 120 seconds at which both match contracts are two-sided, forward to plus 5 minutes), take for each of the two contracts of THAT MAP its last candle ending at or before the look minute, two-sided or one-sided.
- Team X is the OBSERVED winner of the map if X's map contract shows a YES bid of 0.90 or more in that candle, or the other team's map contract shows a YES ask of 0.10 or less in that candle.
- If exactly one team is observed as the winner, the state is observable and that team is the map's winner for every later step of the rule.
- If neither team or both teams qualify, or a contract has no candle at all, the look is counted as **"state not observable at the look" and is NOT a bet.**

**What follows.**
1. **The bet uses the OBSERVED state, never the result field.** The map market's result is read only to print one count: looks where the observed winner differs from the posted result. Those looks stay bets exactly as observed, because a live trader would have made them.
2. **Second look:** "one map each" means the observed winner of map 2 is the team that was the observed loser of map 1. If map 1's state was not observable at the first look, it is taken again at the second look from the map-1 contracts' last candles; if either map's state is not observable then, there is no second-look bet (counted).
3. **The 150 minimum, the cost line, the gap share and the placebo share apply to the looks that are left** after "state not observable" is removed, per title and per look.
4. **The constants 0.90 and 0.10 are fixed here** and were not chosen from any match result; 0.90 is the figure this registration already used for its count in Amendment 4.
5. **Step 1 as already run stands as a count:** CS2 is OUT at both looks on its registered gap-share line (6.8% and 8.3% against 10%), as the Head recorded at 00:04Z. This amendment cannot bring it back: it only removes looks.
6. The live spec sheet and the recorder spec use this same definition (the recorder already keeps the map contracts' books once a minute until each map market closes).

## AMENDMENT 8, Nov 13, 2026, 00:06Z: made after step 1 counts on 165 of 282 candle requests, BEFORE any match result was read (the Testing Desk's two questions; Auditor B's findings F1 and F2)

Where this section and Amendment 7 differ, this section is right. It is the ONE definition the Testing Desk codes.

1. **The observed winner of a map, simplified to a single observable.** At a look, take each of that map's two contracts' LAST candle ending at or before the look minute (one-sided allowed). **Team X is the observed winner if and only if X's own map contract shows a YES best bid of 0.90 or more in that candle and the other team's does not.** Amendment 7's alternative ("or the other team's ask is 0.10 or less") is dropped. Reason, said plainly: the recorder's five-level books give the best bid directly, and the Testing Desk's count (no match result) found a best bid present in 90% to 99% of maps against 52% to 82% for a last trade; the earlier 42% to 60% used the last TWO-sided candle and so measured the book thinning. The choice of observable was informed by those counts of what can be seen; no match result was read and 0.90 was already this registration's figure.
2. **Which contract carries the state:** always the map's WINNER's own map contract, whichever team the rule then buys. For the second look both maps are read this way (Amendment 7, point 2).
3. Neither or both teams at 0.90, or no candle: **"state not observable at the look", not a bet,** counted and printed. The 150 minimum applies to the looks that are left; under it the title reads "no evidence at n = x".
4. **Auditor B's F1** (the state came from a result posted about three minutes after the close, after the look) is closed by points 1 to 3: the bet uses the observed state, never the result field. The result is read only to count looks where the observed winner was wrong; those stay bets.
5. **Auditor B's F2, the price: the decision and the price are no longer the same candle.** The decision is taken on the look minute L exactly as registered (state observable, gap 8c or more against the ask at L, spread 4c or less at L). **The price paid is the NEXT minute's ask plus 1c:** at the candle ending one minute after L the bought contract must be two-sided with a spread of 4c or less AND its gap against that minute's ask must still be 8c or more; then the bet is made at that ask plus 1c. Otherwise it is "not filled", counted, and there is no bet. The fee is charged on the price paid. The one-way cost line is computed on those entry minutes.
6. Nothing else changes: the look times, the model, the placebo, the samples, the tries (2), CS2's step 1 verdict.

## AMENDMENT 9, Nov 13, 2026, 00:07Z: made after step 1 counts on 165 of 282 requests and after Auditor B's findings, BEFORE any match result was read (Head of R&D's mandatory fixes of 00:05Z)

The Head's ruling reached me after Amendment 8 was written. It agrees with Amendment 8 on the state (F1) and sets a different, mandatory rule for the fill (F2). **Where Amendments 7 and 8 and this section differ, this section is right; with Amendment 8's points 1 to 4 it is the ONE definition.**

1. **F1, the state (as Amendment 8, points 1 to 4, restated in the Head's words):** the team taken is named ONLY by Kalshi's own quote in a candle ending at or before the look: the map's winner is the team whose own map contract shows a best bid of 0.90 or more (one-sided books allowed) while the other team's does not. If neither shows it, the match is "state not observable at the look": counted, printed, not a bet. The result field never names the team.
2. **F2, the fill (replaces Amendment 8, point 5):** the decision is taken on the look candle exactly as registered (state observable, gap 8c or more against that candle's ask, spread 4c or less). The order is **a limit at the look candle's ask plus 1c. It is FILLED only if the next minute's candle shows an ask at or under that limit, and it pays the limit.** Otherwise it is "not filled": counted, printed, not a bet. There is no second gap test on the next minute.
3. **The old figure is printed beside the new one, labelled "optimistic, same-candle fill"** (every decision booked at the look candle's ask plus 1c as before). It is information only; the registered verdict is the filled figure.
4. **The 150 minimum applies to FILLED bets,** per title and look. Under it the title reads "no evidence at n = x".
5. CS2 stays OUT as registered. Step 1 is re-run on the whole set after the remaining requests land. Tries stay at 2. The one-way cost line is computed on the filled entries (ask at the look minus mid, plus the 1c, plus the fee on the limit).
6. The live spec sheet takes the same two definitions.

