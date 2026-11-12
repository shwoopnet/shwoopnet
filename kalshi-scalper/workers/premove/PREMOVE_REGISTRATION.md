# PREMOVE, follow the last hour's price move before a match starts: rule registration

**Registered Nov 12, 2026, before any price or result of these markets was read by anyone on this desk.** Written by Idea Desk B for the owner's Friday deadline (Head of R&D's order of 18:57Z; the Head's own seed). Frozen families, dates and constants: `premove/PREMOVE_SERIES.json`.

`PREMOVE | family: a match market's own price move in the last hour BEFORE the start, followed; buy the side that rose just before the start, hold to settlement | risk class: mid price (20c to 85c), 1 contract, hundreds of matches a day | stage Idea, registered as a rule`

**Nothing here permits an order. Tries: 4, one for each family.**

## What has been seen so far

Shape, times and volume only (the Nov 10 census listing): these series carry a clock time in the ticker, checked on one market each, and their markets open well before it (e-soccer and e-basketball about two and a half hours before the start, table tennis about twelve, esports days). No price and no result was printed or used.

## The idea in plain words

In the hour before a match, some prices move. In these low-tier games a late move is usually someone acting on something specific: a stand-in, a line-up, who is actually sitting at the controller today. The rule asks whether the price has finished moving by the start, or whether the side that rose is still too cheap.

**Direction, chosen now: FOLLOW.** A late move before the start is information arriving; I can name no reason why it would be an overreaction, so the fade is not registered.

**The named other side:** resting orders and slower bettors who priced the match earlier and have not looked again.

**Why it may well fail, said first:** the best-known result in sports betting is that the closing price is the efficient one. If that holds here, buying the riser at the price it has already reached earns nothing and pays the cost.

## The rule, every number pinned

1. **Scheduled start S:** the clock time in the ticker, US Eastern. The reading is checked once for the whole family (file, `start_rule`), never match by match, so no later time decides which bets exist.
2. **Two instants before the start:** the one-minute candles ending at S minus 65 minutes and at S minus 5 minutes. A contract counts only if it is two-sided (0 < bid < ask < 1) at both.
3. **The move (the state):** a contract's mid at S minus 5 is 6c or more above its mid at S minus 65. That contract is the riser. In e-soccer the Tie is never the riser; if both team contracts rose 6c, no bet.
4. **Entry:** at the close of the candle ending at S minus 4 minutes, if the riser is two-sided, its ask is between 20c and 85c and its spread is 4c or less: buy 1 contract at that ask plus 1c. One bet a match. If the entry fails, no bet (counted).
5. **Fee:** 0.07 x price x (1 minus price), rounded UP to the next whole cent. **Exit:** hold to settlement. The result is read only for matches with a bet.

## Cost kill and placebo

- **Cost:** round trip at the entry minute = spread plus two fees at the mid. A family whose median round trip over its qualifying entries is above 5c is CLOSED on cost and no result of it is read.
- **Placebo (the same entry with no move):** every development match in which NO contract's mid moved 2c or more between the two instants; buy the contract with the higher mid at the same entry minute, same band, same spread line; hold. Grouped by price paid in 10c steps and re-weighted to the rule's own price mix. It is what backing the pre-match leader earns when nothing moved.

## Order of the read (fixed)

1. Per family, no result read: matches listed; the start check; matches two-sided at both instants; matches with a move; entries; the cost line.
2. A family that fails the start check or the cost line stops there.
3. The rule and the placebo are scored for the families that remain.

## Samples (date constants; the same windows as INPLAYJUMP and MAPBREAK, so the same pulls serve)

| Family | Development: market closes | Held-out: market closes (not pulled until the Head's go) |
|---|---|---|
| Esports: CS2, Dota 2, Valorant, League of Legends, every match format | 2026-09-12 to before 2026-10-23 | 2026-10-23 to before 2026-11-13 |
| E-soccer | 2026-10-15 to before 2026-10-23 | 2026-10-23 to before 2026-10-27 |
| Table tennis, Liga Pro | 2026-10-01 to before 2026-10-23 | 2026-10-23 to before 2026-11-03 |
| E-basketball | 2026-09-15 to before 2026-10-23 | 2026-10-23 to before 2026-11-11 |

Every match in a window is used.

## Reported, and the verdict (per family, fixed now)

Counts first, then: bets, wins, mean price paid, cash profit factor, net cents a contract, both halves by date, the share of bets paid 70c to 85c, the largest share of net carried by one day, z with the day as the cluster, the placebo's net at the same price mix and the difference with its standard error.

- Under 300 bets: NOT_ENOUGH_DATA at n = x.
- 300 or more and cash PF under 1.0, overall or in either half: FALSIFIED.
- Cash PF 1.5 or better, both halves above 1.0, AND net above the placebo's by two standard errors or more: "development bar met"; the held-out is asked for the same hour.
- Else "bar not met".
- **Research bar:** cash PF 1.5 or better on development AND held-out, one-sided z of 5.46 or more on the two together. Nothing short of it is reported as a pass.

## Declined list and earlier tests, written out

- **Not favourite-late:** it is before the start, not the last minutes of a window, and the ask is capped at 85c, so no entry is above 88c. The share paid 70c to 85c is reported.
- **Not a cheap-side sweep:** one rule, a stated band of 20c to 85c, not a grammar over price and time.
- **Not taker order flow:** it uses the quoted price at two instants; no trade tape and no signed volume.
- **Not in-game lag, not a lock, not market making, not a forecast.**
- **Nearest earlier tests:** ESPORT1 (a rating built from Kalshi's own results against the price before the match: FALSIFIED twice) and NEWLIST1 (the first hours of a new market: FALSIFIED). Neither used the market's own late move. INPLAYJUMP is the same idea during play; this one is before play and shares no bet with it.

## Events and requests, said plainly

- **Events (matches in development; a lower bound from one Tuesday):** esports about 3,200; e-soccer about 3,600; table tennis about 3,200; e-basketball about 3,200. What share shows a 6c move in the last hour is not known; at 10% each family has about 320 development bets, at 30% about 960. **Whether a family reaches about 1,000 bets over development and held-out depends on that share; a family that does not reads NOT_ENOUGH_DATA and is not stretched.**
- **Requests: none of its own if two planned pulls widen their candle windows before they are built.** MAPBREAK's candles for the two match contracts start at S minus 70 minutes in place of S minus 40; INPLAYJUMP's clock families start at S minus 70 in place of a window measured back from the close. Esports matches that are not best-of-three are not in MAPBREAK's pull and would need their own candles: my estimate 60 to 100 requests. Lists: none of its own (both jobs already list these series; the esports match lists must be kept whole, not only best-of-three).

## Honest limits

1. Candle freshness was measured on the Bitcoin 15 minute series only. Every output carries that line.
2. Thin markets may show a two-sided quote with one contract behind it; a candle has no size.
3. In e-soccer and e-basketball the market opens only about two hours before the start, so S minus 65 can fall in a market's first hour, when quotes are wide; those matches drop out at the two-sided condition and are counted.
4. **My odds: about 2% a family that the development bar is met; about 1% a family for the research bar; about 3% that any of the four passes.**

## Amendment 1 (Nov 12, 2026, 19:12 UTC; before any price or result was read)

1. **E-soccer matches in which REMATCH's state is true are left out** (`rematch/REMATCH_REGISTRATION.md`, rule points 2 to 4: the previous loser's contract fell 5c or more after a meeting of the same two players 20 to 120 minutes earlier). That state is known a minute before PREMOVE's entry. Reason: REMATCH buys the faller in those matches and PREMOVE would buy the riser, and this desk does not bet one match both ways. The number left out is printed.
2. **A plain fact found after registration, from listing times only:** in e-soccer and e-basketball the next match's market is already open while the players' previous match is played (297 of 299 qualifying e-soccer pairs on Nov 10). So in those two families a late move is mostly the market reacting to results that have just come in, not to line-up news. The rule is unchanged; the reader should know what it is testing there.
3. **The request line is corrected.** One batched candle request has ONE time range for all its tickers, and matches start at staggered times, so a wider window costs requests. My estimate for PREMOVE's own cost is now about 400 to 500 requests on top of INPLAYJUMP's and MAPBREAK's pulls, not none. The exact count comes from the lists.
