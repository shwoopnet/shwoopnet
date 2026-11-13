# POLGAPH: follow an overnight gap in a short-dated politics market and HOLD to settlement (Idea Desk B)

**What this is, in one line (the Head of R&D's ruling of 00:51Z): POLGAPH is the ONE permitted rule (i) variant of POL-i2: the same overnight gap, held to settlement instead of the 24 hour taker exit that closed on cost, for the stated mechanical reason that holding pays one way only (about 2.5c to 3c against the 4c line). It uses up POL-i2's one variant; there is no second. It is not a version of INPLAYJUMP (ruled). 1 try, on the ledger. Honest prior that it clears the bar: 3%.**

**Registered Nov 13, 2026, 00:47Z, before any price path or result of a gap morning was read by this desk.** Research and paper only. Nothing here places, changes or cancels an order, and nothing here asks for a live probe. No Kalshi request was made to write it.

`POLGAPH | family: follow an overnight price gap at the US morning, taker entry, hold to settlement | risk class: mid price (10c to 64c), 1 contract in the score (3 on a politics single by the rulebook), one-way cost | stage Idea, registered, unscored | tries 1`

## Where it comes from, said plainly

- **Parent:** POL-i2 (Refinement's card of Nov 11; the Testing Desk's count registration is the one of record, `claude/testing-desk`). POL-i2 buys the direction of an overnight gap at 07:00 ET and sells 24 hours later at the bid. It was CLOSED ON COST before any gap was counted: the round trip measured 9.4c (list quotes, 29 series) and 6.3c (recorder sample) against a 5c line. No gap was ever scored, so the parent has no evidence for or against its direction.
- **What is new here:** the EXIT. Under standing rule (i) a different exit on a registered rule is a new try, registered before data. Holding to settlement pays one way only. The markets in question are weekly, daily and monthly ladders that settle within days, so the hold stays inside the politics hold cap of 30 days (`docs/POLITICS_RULES.md`).
- **Closest existing, for the uniqueness check:** POL-i2 (same signal, different exit) and INPLAYJUMP (follow a jump and hold, inside a live sports match, minutes). It differs from INPLAYJUMP in the clock (a fixed wall-clock look after the US night, not an in-play state change) and the market kind. **Whether section 7g makes it a version of INPLAYJUMP is the Head of R&D's ruling; I flag it and do not argue it.**
- **Outside evidence, both ways (Idea Desk C's page, `claude/idea-desk-c` 616dc686):** Kalshi politics prices are underconfident (a recalibration slope of 1.3 to 1.8), which supports buying a side that has moved above 50c, weakly, and argues AGAINST buying a side still under 50c. A second study finds the politics slope not significant. Nothing published tests an overnight gap.
- **Honest prior that it clears profit factor 1.5 on development and held-out: about 3%.** It is registered because it is the one politics shape with a reachable count, a cost under the line, a score possible on candles that exist, and no negative evidence. On count ladders an overnight move is usually the count arriving, which is news, not staleness.

## Universe (fixed now)

The 69 series in `POLGAPH_SERIES.json` (this folder): the 79 daily, weekly or monthly Politics series of the POL-i2 universe minus the 10 approval, favourability and generic ballot series (other cards hold those out, and their NO side read is closed). Every market of those series. No market is chosen by a price or a result.

**Windows, by the market's CLOSE time (so a bet's result is always inside its own window):**
- **Development:** markets closing from 2026-09-12 00:00Z to 2026-11-12 23:59:59Z. Halves by the gap morning's Eastern date: before 2026-10-13, and from 2026-10-13.
- **Held-out:** markets closing from 2026-11-13 00:00Z to 2026-12-17 23:59:59Z. Not pulled. Standing rule (h) applies: no list or candle request covers a held-out close until the scorer is frozen by commit and sha256, a read-once marker is committed, and every other card holding out these series is at the same point; then one joint pull into a `HELDOUT_` folder.

## The rule (every number fixed now)

Clock: America/New_York. For a market and a morning D, three hourly candles are used: the ones ENDING at 22:00 on D-1, at 06:00 on D and at 07:00 on D.

1. **Three candles present and two-sided.** Each of the three candles exists and shows 0 < bid < ask < 1 for YES. A candle showing a bid of 0.00 and an ask of 1.00 is an empty book, not a quote. A missing candle is "no look", counted, never filled in from an older one.
2. **Gap.** YES mid at 07:00 minus YES mid at 22:00 is 5c or more in size. Up means the bought side is YES; down means NO (NO ask = 1 minus YES bid, NO bid = 1 minus YES ask).
3. **Steady.** The bought side's ask at 07:00 is within 1c of its ask at 06:00.
4. **Band.** The bought side's ask at 07:00 is from 10c to 64c. (65c and above is the buy-high-and-hold shape the owner bans; the 65c line is the one already used for the weather bracket ruling.)
5. **Spread.** The bought side's spread at 07:00 is 4c or less.
6. **Liquid.** The market traded 200 contracts or more in the 7 days ending 22:00 on D-1, summed from its hourly candles' own volume.
7. **One bet per event and morning,** and no new bet on an event while an earlier POLGAPH bet on that event is unsettled. Among an event's qualifying markets the one whose bought-side ask is nearest 50c is taken; ties go to the ticker first in alphabetical order.
8. **Entry and fill.** A limit at the 07:00 ask plus 1c. The 1-minute candle ending 07:01 decides the fill: absent (Kalshi omits a minute in which nothing changed) or showing the bought side's ask at or under the limit means FILLED, paying the limit; showing an ask above the limit means NOT FILLED, counted, no bet. The two kinds of fill are counted apart, and the profit factor is also printed for the fills with a present candle only. The figure with every decision booked at the limit is printed beside it, labelled "optimistic, same-candle fill", information only.
9. **Exit.** None. Hold to settlement.
10. **Money.** 1 contract. Fee 0.07 x price x (1 minus price) at the limit, rounded up to the next cent. Win pays 1 minus limit minus fee; loss pays limit plus fee. A void refunds the price and keeps the fee, a fee-only loss, COUNTED in n and in the profit factor.

Every "or more", "or less", "within" and band edge is compared with a tolerance of 1e-9. Lists are read with status settled and the result as given, never filtered.

## What is printed, counts first

1. Series asked, series with any settled market in the window, markets, markets with any hourly candle.
2. Market-mornings with three two-sided candles; with a gap of 5c or more; then the count left after each of steps 3 to 7 in order; fired; filled on a present candle; filled on an unchanged minute; not filled.
3. Distinct events, distinct series and distinct mornings among filled bets, per half. The largest number of bets open at once (the rulebook allows 10).
4. The one-way cost line (below).
5. Only then: cash profit factor, n, wins, mean per bet, for development and for each half, with the event-clustered z. The same for the present-candle fills only, and the optimistic figure.
6. A price-matched baseline, information only: market-mornings that pass steps 1 and 3 to 6 with a gap under 2c in size, buying the side whose ask is in the band and nearest 50c, one per event and morning. It answers one question: does the gap add anything beyond the price.
7. Every output carries: "candle freshness measured on Bitcoin 15 minute only, not on these markets".

## Lines fixed before data

- **Count:** fewer than 150 filled bets in development, or fewer than 40 in either half, reads "no evidence at n = x". Not falsified, not a pass.
- **Cost (the standing one-way template):** the median of (the 07:00 ask of the gap side minus its mid) plus the fee as charged at the limit, over every market-morning that passes steps 1 and 2. Above 4c the card is CLOSED on cost and no result is read. The limit-based figure is printed beside it, information only.
- **Profit factor:** with the count met and the cost under the line, development cash profit factor of 1.5 or more with each half at 1.0 or more reads "survives development"; anything else reads FALSIFIED.
- **Held-out:** read once, only if development survives, same lines.
- **The shared bar:** the deflated bar (one-sided z 5.46 at about 2,113,000 tries) will not be reached at this n. A survival here is a candidate for a wheel shadow place, never a pass of the research bar.
- These lines are set before data; any line later chosen from the development data would be labelled "selected on development" and could only falsify.

## Data and requests (nothing is asked for yet)

- **Lists:** `desk_b_jobs/POLGAPH_LISTS.json`, settled markets of the 69 series bounded by close time in the job file (2026-09-12 to 2026-11-12), 69 requests, cap 110 with paging.
- **Hourly candles:** built from the lists answer by a builder still to be written, batched by close week so that no request passes 10,000 candles. My estimate is 120 to 200 requests; the exact count goes to the Head before any candle request.
- **Minute candles for the fill:** one batched request per development morning that has a fired decision, the minute ending 07:01 only, at most 61 requests.
- **Ceiling for the whole card: 380 requests.** Over that, the monthly ladders are dropped first (stated now, by frequency, not by any result).
- **Order of work:** the scorer and the two builders are committed and frozen by sha256, audited by Auditor B, before the lists pull is dispatched. A verdict is recorded only when an independent second build prints the same figures on the same landed file (rule 16b).

## What it cannot show

- Hourly candles cannot show that a quote "had not yet followed". Step 3 says only that the price was steady for the last hour.
- A fill on an unchanged minute rests on Kalshi omitting unchanged minutes, measured so far on one Bitcoin series.
- No book and no tape exist for these markets, so no resting entry and no resting target is scored here. Each would be a further variant and a further try, only after a book-and-tape recorder exists.
- The sibling strikes of one ladder settle together. The rule takes one bet per event and morning for that reason, and the z is clustered by event.
- Live, a seat would need the bot's long-hold order path, the rulebook's limits (3 contracts, 10 open, the $200 lifetime budget, the kill at net under -$15 after 20 fills or 5 losses in a row) and the owner's own popup. None of that is asked for here.

## AMENDMENT 1, Nov 13, 2026, 01:06Z: the Head of R&D's rulings of 00:51Z, written before any list, candle, price path or result of this card was requested or read

1. **Identity.** The line now at the top of this page. The section "Where it comes from" asked whether section 7g applied; the Head ruled it does not: the information is an overnight repricing over nine hours in politics count and event markets, not a state change inside a live game within minutes, and the market family, clock and counterparty differ.
2. **Pooling is allowed for this research card on three conditions, fixed now:**
   - one bet per independent event and morning (rule step 7, unchanged);
   - **every figure is printed by family beside the pooled line.** The three families are fixed in `POLGAPH_SERIES.json` under `families`: activity counts (48 series), shipping counts (7), single questions (14);
   - **a pooled pass does not count if one family supplies more than half of the pooled net.** Then the card is read as that family's alone, against the same minimums (150 filled bets, 40 in each half) and the same lines. "Net" is the sum of cash results over filled development bets.
3. **A wheel place is not decided here.** Whether a pooled series can hold one is the Head's to take to the owner, and only if the development read is not under 1.0.
4. **Process, no shortcuts:** the scorer and builders frozen by commit and sha256; a 1e-9 tolerance on every registered comparison; the held-out folder guard; Auditor B CLEAN; and a second build from this text by another desk, BEFORE the lists job is dispatched. Cost by the template of rule (d). Development dates bounded in the job file; held-out from Nov 13. It queues behind Friday's reads.
5. **Three pins the builder needs, clarifying, no rule changed:**
   - "Unsettled" in step 7 means the earlier FILLED bet's market has a close time later than the look. An order that did not fill blocks nothing.
   - A fill can be judged only where the minute request for that market and morning was answered. A decision whose minute request is missing or failed is "no fill data": counted, not a bet, never treated as filled.
   - A market that settles at a set price (result neither yes nor no) is a void under the money rule. The count is printed, and beside it, information only, the figure with the settlement value paid instead.
