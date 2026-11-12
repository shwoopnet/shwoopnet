# TIE3, the Tie contract in period, quarter and half markets: measurement registration

**Registered Nov 12, 2026, before any price or result of these series was read by anyone.** Written by Idea Desk B; the reader, the pull jobs and the scoring are built by the Testing Desk from this text. Card: `CENSUS_CARDS_NOV12.md`, card 18. Frozen series and cells: `tie3/TIE3_SERIES.json`.

`TIE3 | family: a listed third outcome priced under its base rate; entry before the game on the Tie contract, hold to the end of the period | risk class: mid price, 1 contract | stage Idea, measurement only`

**This stage is a ZERO-TRY cost and price measurement. No rule is scored, no result of a priced game is read, nothing is traded, and nothing here permits an order.**

## What has been seen so far (so the reader of a result knows)

Only shape and volume, from the Nov 10 census listing (`FAMILY_CENSUS_NOV12.md`): these series list three markets an event, one ending in -TIE; contracts a market that day. Their time fields were looked at for five games to set the start rule below. No price field and no result field of any of these series was printed or used.

## Plain statement required by the Head of R&D

**This IS a base-rate rule, a crowd-bias rule, the kind this desk's own note on CALIB1 warns about.** It is allowed to be measured because CALIB1 covered the cheap tails of two-way markets, not a mid-priced third outcome, and because the named other side is bettors who pick a team and leave the Tie to whoever quotes it. A bias of 1 to 3 points cannot reach the research bar; this needs 8c or more, and the measurement exists to show quickly that it is not there.

## Rulings it rests on (Head of R&D, Nov 12, 17:15Z)

1. TIE3 is OUTSIDE the declined row "Conditional tie premium on the non-crypto 15 minute markets" (a different contract, market type and reason).
2. The base rate for any bet uses only settlements dated strictly before that bet's day.
3. Prices come from candles or books at a stated instant, never a list quote. Every output carries the line: "candle freshness measured on Bitcoin 15 minute only, not on sports".
4. Cutoffs are date constants, cells are fixed before data, and tries equal the number of cells written here.
5. The lists job is approved. The candle stage waits for the Head's go after the lists are reported.

## Cells, fixed now (6)

| Cell | Series | What "level" means | Base rate I expect (memory, not data) |
|---|---|---|---|
| NHL_P1 | KXNHL1P | the Tie market of period 1 settles YES | about 40% |
| NHL_P2 | KXNHL2P | same, period 2 | about 38% |
| NHL_P3 | KXNHL3P | same, period 3 | about 38% |
| NHL_REG | KXNHLOT | "game goes to overtime" settles YES | about 22% |
| NFL_Q | KXNFL1Q, 2Q, 3Q, 4Q, pooled | the quarter's Tie market settles YES; the base rate is kept per quarter | about 20% |
| SOC_1H | twelve soccer first-half series (file), pooled | the first half's Tie market settles YES; the base rate is kept per series | about 43% |

Left out on purpose and said so: college football quarters, every basketball period, NFL halves (their Tie is a cheap-tail contract), and soccer second halves. A soccer ticker in the file that returns no market is counted as "no such series" and dropped.

## Date constants

- **Base block:** events whose market closes before **2026-10-27 00:00 UTC**, including anything the history endpoint holds for the same series. Results ARE read here, for one count only: how often the period was level.
- **Price block:** events closing from 2026-10-27 00:00 UTC to before 2026-11-13 00:00 UTC. Prices only. **No result field of a price-block market is read; the reader must enforce that in code,** not by habit.
- **Held-out:** events closing from **2026-11-13 00:00 UTC** on. Not pulled at this stage.
- (The card said Oct 20 for the block line. It is moved to Oct 27 here, before any data, because the NHL season is three weeks old on Oct 27 and one week younger would leave each NHL cell under its 150 base events if the history endpoint holds nothing.)

## The instant

1. **Scheduled start** of a game = the market's `occurrence_datetime` minus 180 minutes. (In the five games looked at, hockey, football and basketball period markets all carry this field and it sat 3 hours after the listed start.)
2. **Check, per game:** the game's first-period market (file: `first_period_series`) must have closed between 20 and 120 minutes after that start. If not, or if the field is missing, the game is dropped and counted under "start not derivable". This catches a wrong offset, a postponement and a market left open.
3. **T = start minus 30 minutes.** The price is the one-minute candle ending at T: YES ask and YES bid at the candle's close.
4. If that minute is missing or one-sided, step back one minute at a time to T minus 30 minutes and take the first two-sided minute. If none, the game is "not two-sided" and counted. Nothing is filled in.
5. A live rule could use the same instant: the field is known before the game.

## What is reported, per cell (counts first)

1. Base events, the base rate and its standard error (for NFL_Q and SOC_1H also per quarter and per series).
2. Price-block games; how many had a derivable start; how many were two-sided at the instant; the share.
3. Median spread (ask minus bid).
4. Median and quartiles of (base rate minus Tie ask), using the base rate of that game's own quarter or series.
5. The share of two-sided games where the ask is 10c or more under the base rate and the spread is 4c or less (how often the proposed rule would fire).
6. Events with fewer than three settled markets (one for NHL_REG): dropped and counted.

## Minimums and the kill rule, fixed now

- A cell is read only with **150 or more base events and 40 or more two-sided price-block games.** Under either it is "no evidence at n = x".
- **The card is CLOSED with the words "efficient, move on" and the median gap of the best cell as the one number, unless at least one cell shows a median (base rate minus Tie ask) of 8c or more with a median spread of 4c or less.**
- Closed as "nothing to buy" if under half of the price-block games are two-sided in every cell.
- The direction is fixed. If the Tie is OVERPRICED the card closes; it is not turned round.

## If a cell survives

A separate registration, before any result of the price block is read: the rule of the card (ask 10c or more under the base rate, spread 4c or less, 1 contract, hold), the price block as development read once, the held-out from 2026-11-13 read once, and **tries = the number of surviving cells, at most 6.** The research bar is cash PF 1.5 on development and held-out at the shared count (about 2,113,000 tries, one-sided z 5.46). At an entry near 30c that needs about 1,200 bets for a true PF of 1.5.

## Requests

- **Lists job (approved):** for each of the 20 series, its settled markets on the live endpoint; for the 8 NHL and NFL series also the history endpoint; one fee-field read for 4 series (file). **32 requests, about 50 pages.** The Head approved "about 25": the extra 7 are the soccer first-half tickers, which can only be found by asking for each league's ticker because the Sports series list is over the 5 MB answer cap. If that is too many, drop the last six soccer tickers in the file.
- **Candle stage (after the Head's go):** the Tie contract only, the 31 minutes ending at T, batched by start time. About 730 contracts; 80 to 150 requests.

## Honest limits

1. Candle freshness was measured on the Bitcoin 15 minute series only. A thin sports market may show a one-sided or stale close; those minutes are counted, not used.
2. The base rate from three weeks of one season has a standard error near 4 points in an NHL cell (about 155 games). The 8c kill line is about two of those. If the history endpoint holds last season, the error falls to about 1.4 points.
3. The ask at one instant is not a fill. Forensics measured a 59% to 73% fill at the price seen on the 15 minute series; nothing is measured for sports.
4. Forensics flags NHL spreads and totals as too costly (3c to 4c wide). The NHL cells may fail on the spread line alone; that is a result, not a fault.
5. My probability that any cell survives: about 20%. That a surviving cell then reaches the bar: about 1 in 5.

## Note, Nov 12, 2026, 19:05Z, before any data (after the Forensics audit of another registration)

The start check in "The instant", step 2, uses the close of the game's first-period market, a time AFTER the entry instant. At this stage no result of a priced game is read, so it cannot bias a result: it only removes games whose start cannot be trusted (a postponement, a market left open). **If a cell survives and a rule is registered, that check becomes a family-level check** (the share of games passing it is printed and a cell under 80% is "start not derivable"), so that no later time decides which bets exist.

## Dated amendment, Nov 12, 2026, 19:15Z, before any candle of these markets was requested (Head of R&D, 18:58Z, on the Forensics desk's finding)

**The start check's lower bound is raised from 20 to 30 minutes.** "The instant", step 2, now reads: the game's first-period market must have closed between **30** and 120 minutes after the derived start. Reason: Forensics showed that with the 20 minute bound the pricing instant could fall into play in games whose derived start is late. This is still a zero-try measurement that reads no result of a priced game; the note of 19:05Z stands (in any rule registration this becomes a family-level check).

Lists result, as given by the Head (not counted by this desk): 821 priced events in the price block (NHL periods 1, 2, 3 and regulation 114 each, NFL quarters 120, soccer first halves 245); base block 2,036; the ticker-suffix assumption held.

## Dated note, Nov 12, 2026, 19:26Z: published evidence and odds

Idea Desk C's reading of the published work (`idea_desk_c/DIRECTION_EVIDENCE_NOV12.md`, commit 338ebbde on `claude/idea-desk-c`; 26 sources, 9 verified from full text): the full-time soccer draw is fair on average on exchanges and books (three large samples), with weak evidence of a small underpricing; UK books' NHL regulation-tie prices imply 22% to 33% against 22.4% observed, so the tie is if anything overpriced there; nothing published exists for periods, quarters or halves. No size near the 8c line was found. **My odds that TIE3 reaches the research bar are revised from 4% to about 2%;** that a cell survives the measurement, from about 20% to about 15%. Nothing in the registration changes. The held-out (closes from 2026-11-13) starts after the census day and falls under standing rule (h) like every other card.
