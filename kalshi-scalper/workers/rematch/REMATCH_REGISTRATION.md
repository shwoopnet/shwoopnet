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

## Amendment 2 (Nov 12, 2026, 19:20Z; before any price was read or any result joined; Head of R&D's ruling of 19:13Z, which accepted the card with these changes)

Where this section and anything above differ, this section is right. Tries unchanged: 1. Direction unchanged: FADE.

1. **When the earlier result may be used (the ESOCTIE rule; replaces rule point 3's "settlement time at or before B's S minus 12 minutes").** Match A's result may set the state only if every market of A has a close time such that close plus 300 seconds is at or before the decision minute, the candle ending at B's S minus 6 minutes. A must have had a winner (not a Tie). Nothing about A that is later than that is used.
2. **The reference minute for "fell 5c" is fixed here and known at the decision:** the candle ending at A's scheduled start minus 2 minutes, in B's market, on the contract of the player who went on to lose A. The fall is that contract's mid at that candle minus its mid at the candle ending at B's S minus 6 minutes.
3. **One bet a match. The placebo buys at the same instant by the same price rule.** One void rule and the one-way cost kill are in Amendment 1.
4. **No cut is computed over the whole development sample.** Every threshold is a constant in this file. The stage 1 lines can close the card; they cannot support it.
5. **z is clustered by UTC day (the verdict's z), and z clustered by player-pair and day is printed beside it,** so the reader sees how much the repeat meetings of the same players matter.
6. **The held-out is closed by default:** the scorer refuses any market closing on or after 2026-10-23 00:00 UTC unless it is started with an explicit held-out switch, which is used once, on the Head's go.
7. **The scorer goes to the Forensics desk for a leak audit before stage 2.**
8. **Stage 1** (counts and cost on the Oct 15 to Oct 23 slice, about 110 candle requests, no bet scored, no try) was approved by the Head, to run once INPLAYJUMP's e-soccer lists have landed. The job is built by `rematch/build_stage1_job.py` from those lists and goes to Main inside the pull limits. Stage 2 waits for the Head's go.

## Amendment 3 (Nov 12, 2026, 19:26Z; before any price was read or any result joined)

Where this section and anything above differ, this section is right. Tries unchanged: 1. Direction unchanged: FADE.

1. **Published evidence and revised odds.** Idea Desk C's reading of the published work (`idea_desk_c/DIRECTION_EVIDENCE_NOV12.md`, commit 338ebbde on `claude/idea-desk-c`; 26 sources, 9 verified from full text): no study of head-to-head recency exists; odds do overreact to a team's recent run against any opponents (20 soccer leagues, 12 seasons), the same direction as this rule, but by a few percent and only at the extremes; in NBA and NHL playoffs the line marks the previous game's winner down by about 1.25 points, which is pricing, not mispricing. No published size is near the 10 points the bar needs at mid prices. **My odds are revised from about 1.5% to about 1% that the development bar is met.** The direction is not changed because of that page.
2. **Standing rule (h), shared held-out windows (Head of R&D, 19:22Z, on a Forensics finding; before any held-out data exists).** REMATCH holds out e-soccer (KXESOCCERGAME) closes from 2026-10-23. The same series and dates are held out by ESOCTIE (History Miner) and by INPLAYJUMP's e-soccer family. No list or candle request may cover a held-out close of these series until every card that holds them out has finished its development read, has its scorer frozen by commit and sha256 on rnd-queue, and has a committed read-once marker; a card that failed development blocks nobody. Then ONE joint held-out pull per shared series, on the Head's go, into a folder whose name starts HELDOUT_, which every scorer refuses by default and which nobody opens, greps, counts or summarises outside an approved read. Development pulls end before the held-out cut by date bounds in the job file, not by a filter after the pull. **Nov 10 is dropped from the held-out:** from REMATCH's held-out window (2026-10-23 to before 2026-11-13) markets closing from 2026-11-10 00:00 UTC to before 2026-11-11 00:00 UTC are left out, because the census listing of that day (which this desk's counting scripts read for times and tickers) already sits in a landed file with its results.
3. **Bounded by date in the job, as rule (h) point 3 asks.** Stage 1: every candle request of `build_stage1_job.py` ends at a later match's scheduled start minus 3 minutes for a match whose market closed before 2026-10-23 00:00 UTC; the builder refuses to write a job in which any request ends at or after that instant, and the lists it reads are INPLAYJUMP's, which carry a close-time ceiling. Stage 2: every list page carries a close-time ceiling of 2026-10-22 23:59:59 UTC and every candle request ends before the cut.
4. **Which time field (asked by the Head on a Forensics note, then settled by Amendment 2).** The time of the earlier match A is the list's `close_time`, the latest over A's markets, plus 300 seconds. `settlement_ts` is not used and no expiration field is ever used. A market of A with no readable `close_time` fails closed: the pair is dropped and counted.
5. **A printed diagnostic, never a filter (Forensics):** up to a fifth of matches may not start at the ticker clock. If match B kicked off early, a "fall" at S minus 6 could be B's own first goal. For matches with a bet the scorer prints the distribution of B's close minus S and the share that closed under 14 minutes after S minus 5. No profit factor is ever computed with those removed.
6. **Labels on the scored line:** the placebo difference is "selected on development" too (its price weights come from the whole sample); the scored line is also shown with the random drop at the miss rate named in the Forensics desk's `HOW_TO_PRICE_A_PAPER_TRADE.md` section 4b, with its caveat that real misses lean toward winners; and "candle freshness measured on Bitcoin 15 minute only, not on sports".

## Amendment 4 (Nov 12, 2026, 19:32Z; before any e-soccer list or candle was pulled; from the Forensics desk's audit of the stage 1 scripts, which it found CLEAN as a reader, 8 of 8 on its leak test)

1. **A missing candle, pinned.** Kalshi leaves out a candle for a period in which nothing changed. At each of the three instants (reference, decision, entry) the quote is the candle ending exactly at that minute, or else the LAST present candle ending before it and no more than 5 minutes earlier. Never a later candle. That is the quote standing at the instant and is known at the decision. If there is no candle in those 5 minutes the pair is dropped. "No candle" and "one-sided" are printed as separate counts, and so is how many instants were read from the exact minute and how many from an earlier one. The stage 1 candle window therefore starts at the earlier match's scheduled start minus 8 minutes.
2. **Held-out folders are refused in the reader itself** (standing rule (h)): any lists, candles or pairs path whose REAL path has a part starting HELDOUT_ is refused, so a link with an innocent name does not get past. The one approved read sets a switch by hand.
3. **No silent drops:** events left out because they do not have exactly two team codes, have no clock in the ticker, or have a market with no close time are printed as three counts.
4. **What the stage 1 candle file holds, said on the page:** one request has one time range for all its tickers, so the landed file also carries minutes after some matches' starts. The stage 1 reader takes only its three instants and never a later candle. Nobody is to look at that file before the stage 2 score, and the stage 2 scorer takes the same three instants only (the Forensics desk tests that).
5. **Added 19:34Z, before any data (Forensics, after its second clean run, 11 of 11):** a carried entry price is the ask of a candle up to 5 minutes old, payable only if a missing candle means the quote did not change. That was measured on hourly politics candles (236 of 236 gaps) and NOT on one-minute candles of a quiet e-soccer market. So stage 1 prints how many entries came from the exact minute, and stage 2 prints the profit factor on exact-minute entries beside the full figure and says on the page that carried entries rest on that assumption. The registered verdict is the full figure.

## Amendment 5 (Nov 12, 2026, 20:35Z; before any price was read or any result joined): the series is younger than this file assumed

**A fact from lists, schedule and tickers only (the History Miner's independent count from the ESOCTIE lists answer, 20:34Z; its counter reproduces this desk's Nov 10 figures exactly):** `KXESOCCERGAME` began on 2026-10-08. Nothing settled from Sep 12 to Oct 7. From Oct 8 to Oct 22 there were 7,120 matches (445 a day) between 250 pairs, and **5,219 qualifying pairs** by this card's schedule test (326 a day, range 274 to 398).

What that changes, all of it before data:
1. **The development sample is 15 days, not 41:** closes from 2026-10-08 to before 2026-10-23, about 5,200 qualifying pairs, not about 12,000. The date constants are unchanged (the window simply holds nothing before Oct 8). The held-out (2026-10-23 to before 2026-11-13, less Nov 10) is about 20 days, about 6,500 pairs.
2. **Bets, restated:** at a 10% firing share about 520 development bets and about 650 held-out; at 5%, about 260 and 325.
3. **The stage 1 projection uses 15 days** (the slice is 8 of them), and **the stage 1 floor is 300 projected development bets, not 600.** Reason: 600 was half of what a 10% share would give on the 12,000 pairs I wrongly expected; 300 is this card's own registered minimum for a verdict, so stage 1 now closes the card exactly when the development read could not give one. The change is made on a count of matches alone.
4. **Stage 2 is smaller:** only Oct 8 to Oct 14 remains to list and pull: about 10 list pages and about 110 candle requests, not about 490.
5. **Plainly:** with about 500 development bets and about 650 held-out at a 10% share, this card can falsify or show a lead, and it reaches about 1,000 bets over both only if the share is near 10% or higher. The day-clustered z has 15 development days to work with.

