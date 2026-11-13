# VOIDSNAP: a match that will be voided at a fair price still trades away from it (Idea Desk B)

**Written Nov 13, 2026, 01:05Z. A card with a zero-try MEASUREMENT registered first; no rule is registered yet and no try is spent.** Research and paper only. No Kalshi request was made: every count below comes from lists already landed for other cards (the Nov 10 census listing, and the MAPBREAK lists of run 2026-11-12T1919Z, a card that is now closed). No candle of a voided match has been read by this desk.

`VOIDSNAP | family: settlement by rule (a contract that will settle at a set "fair" price, not 0 or 1), bought under that price, held to settlement | risk class: mid price (15c to 64c), 1 contract | stage Idea, measurement registered, zero tries`

## The fact, from Kalshi's own rules text

Quoted from the rules of a CS2 match market (census listing):

> If the relevant match is postponed and not started within 48 hours of its originally scheduled start time, the market will resolve to the fair market price. If the relevant match is cancelled before play begins, the market will resolve to the fair market price. If the relevant match is forfeited before any play occurs, the market will resolve to the fair market price.

So a no-show, a forfeit before play or a cancellation is NOT a loss for one team and a win for the other. Both contracts settle at a price Kalshi sets, and the two always sum to 1.

## Counts already held (lists only; no price path)

| | CS2 match markets | Dota 2 match markets |
|---|---|---|
| Events closing Sep 12 to Oct 22 | 2,006 | 414 |
| Of those, voided (both contracts settled at a set price) | 195 (9.7%) | 31 (7.5%) |
| Voided events with any trade | 164 | 21 |
| Voided events where a side's LAST TRADE was 10c or more from its settlement | 59 | 8 |
| Hours from the ticker's start time to the void market's close: quartiles | 0.8, 2.8, 6.4 (35 closed before the start) | -10.8, 4.9, 8.2 |
| Both sides settled at exactly 50c | 28 of 195 | 10 of 31 |

- Whole history held: CS2 488 voids in 6,961 events (7.0%), Dota 2 78 in 1,778 (4.4%), Valorant 15 in 1,638 (0.9%), League of Legends 36 in 2,900 (1.2%).
- On the census day alone 714 markets in 69 series settled at a set price. Most are not this idea: ties in "most yards" and "points leader" markets split 50c each, and a basketball player ruled out before the game settles at a fair price that sat within a few cents of the last trade.
- **What the last-trade gap does and does not say.** In 59 CS2 voids somebody's last trade was 10c or more away from the price that side settled at. A last trade is one print; it does not show a book that could be bought, or when.

## The idea in plain words

A void market stays open for hours after its scheduled start (median 2.8 hours). In that time the price can run: a team rumoured not to show is sold as if it will lose, and its opponent is bought as if it will win. Kalshi's rule pays neither view. If the fair price is close to where the market stood before the rumour, the side that was sold snaps back at settlement.

- **Counterparty, named:** traders who price a forfeit or a no-show before play as a result.
- **What must be true for a rule:** (1) the fair price can be known, near enough, at the time of the bet; (2) a book exists at 10c or more under it; (3) something on Kalshi's own screen says "this match has not started" well enough.
- **Closest existing:** PREMOVE (withdrawn unread; it FOLLOWED the last hour's move before any match) and MAPBREAK (a state break inside a played match; closed). The politics rulebook says rule edge cases are flagged to the owner with the rule text and are never automatic; this is a settlement rule in sports, not politics, and the text is quoted above so the owner sees it. Whether that rulebook line reaches it is the Head's call.
- **Not a favourite hold:** bets would be taken at 15c to 64c only.

## Stage 1, registered now: a hindsight measurement (zero tries)

Every line it prints ends: "[hindsight sample: events chosen by their void result; an upper bound, not a live rule]".

- **Sample (fixed):** the 195 voided CS2 match events closing 2026-09-12 to 2026-10-22 in the landed MAPBREAK lists, and for each the played event of the same series whose ticker start time is nearest (ties: alphabetical; each played event used once). Nothing closing after Oct 22 is listed or pulled. Dota 2 is not pulled at this stage.
- **Candles:** 1-minute, both contracts, from 180 minutes before the ticker start S to the market's close or S plus 480 minutes, whichever is first. Events sharing a start time are batched. My estimate is 250 requests; ceiling 300; the exact count goes to the Head before any request.
- **Question 1, the fair price.** For each void: how far the settlement value is from the mid at S minus 180, at S minus 60, at S, and from the last two-sided mid. Printed: the share within 1c and within 3c for each reference.
- **Question 2, the window.** For each void: the minutes with a two-sided book in which a side's ask is 10c or more under that side's settlement value at a spread of 4c or less; the first such minute against S; the longest run. The one-way cost by the standing template.
- **Question 3, a detector.** Three, fixed now, each read at a stated minute from candles at or before it:
  - D1, frozen after the start: at S plus 60 the first-named team's mid has stayed within 2c of its mid at S (a missing minute is an unchanged minute).
  - D2, no trade after the start: under 10 contracts traded in both contracts together from S to S plus 60.
  - D3, ran before the start: at S one side's mid is 10c or more under its mid at S minus 180.
  For each: the share of voids it flags, the share of matched played events it flags, and the implied share of voids among flagged events at the 9.7% base rate.
- **Lines fixed before data. "Worth a rule" needs all three; anything else closes the card with no try spent:**
  1. for one detector, at least 40 of the 195 voids show a side buyable 10c or more under its settlement, at a spread of 4c or less, for 5 minutes in a row starting at or after that detector's minute;
  2. for the same detector, the implied share of voids among flagged events is 30% or more;
  3. the settlement value is within 3c of a reference known at that detector's minute in 70% or more of voids.
- Empty-book candles (0.00 and 1.00) are not quotes; comparisons carry a 1e-9 tolerance; voids are counted, never filtered.

## What would follow, and what would not

- If stage 1 says "worth a rule", ONE rule is registered before any other data is read: one detector, buy the side under the reference at 15c to 64c, hold. Because stage 1 chose its sample by the result, it can design the rule but cannot support it. The rule's first score would be on the 293 voids and their neighbours BEFORE Sep 12 (never opened for prices), and its held-out on closes from Oct 23, under rule (h).
- **Speed, honestly:** about 33 CS2 voids a week in the window and about 10 a week with a 10c last-trade gap. A rule firing on those reaches 60 signals in six to twelve weeks. It is above the slow-family line and well short of a fast family.
- **Odds:** that stage 1 says "worth a rule", about 20%; that a rule then clears profit factor 1.5 on development and held-out, about 5% overall. The likeliest ending is that no book stands at the stale price.

## A sibling fact, noted and NOT registered: ITF tennis walkovers pay 50c to both sides

Quoted from an ITF match market: "If the match does not occur (signaled by a ball being played) due to a player injury, walkover, forfeiture, or any other cancellation (all before the match starts), all markets will resolve to $0.50." (A challenger or tour match settles at a fair price instead, and a retirement after the first ball is a loss for the player who retires.)

- Census day: 12 walkovers in 408 ITF events, every side at exactly 50c: doubles 7 of 106 (6.6%), singles 5 of 302 (1.7%). In 4 of the 7 doubles walkovers a player of one team had finished a singles match in the same tournament 3 to 10 hours earlier.
- A bookmaker returns the stake on a walkover; Kalshi pays 50c. So an underdog bought at 15c gains 35c on a walkover and a favourite held at 85c loses 35c. A price copied from a bookmaker's odds ignores that.
- **Why it is not a card:** the arithmetic. At a 6.6% walkover rate the underdog is underpriced by 1c to 3c, which is the size of a taker's cost. A taker needs a subset with a walkover rate near 25% to reach profit factor 1.5. The only candidate seen, "a team member played singles earlier that day", is 4 events on one day. What it would need: settled lists of the four ITF series for six weeks (about 70 requests) to count walkover rates by that subset. I do not ask for them now.

## AMENDMENT 1, Nov 13, 2026, 01:12Z: stage 1 frozen in full, on the Head of R&D's rulings of 01:06Z, before any candle of any of these markets was requested or read

The Head accepted the card as a measurement, put it first, and set conditions. This section is the text a second builder builds from. Where it is more exact than the section "Stage 1, registered now", this section is right. The three questions and the three lines are the ones already stated; nothing is added to them and no fourth detector will be.

**The clause, verbatim, with its source.** Field `rules_secondary` of market `KXCS2GAME-26OCT221715SHINIMP-SHIN` in the landed lists `pull/MAPBREAK_LISTS/2026-11-12T1919Z_43289005222` (request `live_KXCS2GAME`); the same four sentences stand in the market quoted above from the census listing `pull/CENSUS_LISTING/2026-11-12T1703Z_43265329747`:

> If the relevant match is postponed and not started within 48 hours of its originally scheduled start time, the market will resolve to the fair market price.
> If the relevant match is cancelled before play begins, the market will resolve to the fair market price.
> If the relevant match is forfeited before any play occurs, the market will resolve to the fair market price.
> If the relevant match begins and is subsequently forfeited, the market will resolve according to the official result published by the governing body or tournament organizer.

"Fair market price" is Kalshi's to set; the text gives no formula. **Before any rule is registered from this card the Head sends the owner this text and stage 1's lines.** A measurement places nothing.

**Every figure stage 1 prints is labelled "hindsight measurement, not a rule".**

### The sample, named before any price

1. **Source:** the answers to request `live_KXCS2GAME` only, in the lists run above (closes 2026-09-12 00:00:00Z to 2026-10-22 23:59:59Z). The `hist_` answers in that run are never opened by this card.
2. **An event** is one event ticker with exactly two contracts, both with a close time, and a clock in the ticker (date and four digits, US Eastern): the scheduled start S. Events without these are dropped and counted.
3. **Void:** neither contract's result is yes or no. **Played:** one contract's result is yes and the other's is no. Anything else is dropped and counted. An event's close is the later of its two close times.
4. **The match:** voids are walked in order of S, then event ticker. Each takes the played event, not yet taken, whose S is nearest its own; on a tie the earlier S, then the event ticker first in alphabetical order.
5. **The held-out set:** every CS2 match event closing before 2026-09-12 (488 voids in the whole history less this window's, 293). No ticker of theirs is in the sample, the job or any request, and no price of theirs is pulled or opened in stage 1. The scorer refuses a sample holding an event that closes outside the window.

### Candles and quotes

6. **Window of an event:** 1-minute candles of both contracts from S minus 185 minutes to the earlier of its close and S plus 480 minutes. An event whose close is at or before S minus 185 minutes has no window; it is counted and stays in every denominator.
7. **The quote at a minute:** the candle ending exactly at that minute; if there is none, the last candle ending before it inside the event's window (Kalshi omits a minute in which nothing changed, and these markets sit unchanged for long stretches, so a short carry would throw away exactly the standing books this card asks about). If that candle shows 0.00 and 1.00 or has one side missing, there is no quote; the search does not go further back. A quote set before the window opened and never changed is not seen at all, which can only undercount. Two more versions of every figure are printed beside the registered one, information only: a carry of at most 60 minutes, and no carry at all. If the three versions disagree on the reading, the page says so in its last line.
8. **The first-named contract** of an event is the one whose ticker comes first in alphabetical order. Its settlement value is v; the other contract's is its own listed value.

### Question 1: can the fair price be known at the time

9. For each void, the first-named contract's mid at S minus 180, S minus 60 and S, each by rule 7, and the last two-sided mid of a present candle in the window. Printed for each: how many voids have it, and how many are within 1c and within 3c of v.
10. **Line 3 (unchanged):** for a detector, the settlement value is within 3c of a reference known at that detector's minute in 70% or more of voids. The references allowed are the mids at S minus 180, S minus 60 and S for D1 and D2, and at S minus 180 and S minus 60 for D3. The best single reference is used, and the page says it was the best of two or three. The denominator is every sampled void; a void without that reference is a miss.

### Question 2: does a book stand under it

11. A side is **buyable at a minute** if it has a quote by rule 7, its spread is 4c or less, and its ask is 10c or more under that side's own settlement value. A **run** is consecutive minutes in which the SAME side is buyable. Printed: voids with a run of 5 minutes or more, the first minute of the first such run against S, the median shortfall of the ask under the settlement value over buyable minutes, and the one-way cost by the standing template: the median of (ask minus mid) plus the fee as charged at the ask plus 1c, over buyable minutes.
12. **Line 1 (unchanged):** for a detector, at least 40 sampled voids are flagged by it AND show a run of 5 minutes or more that STARTS at or after that detector's minute. Read exactly: five consecutive minutes in which the same side is buyable, all at or after that minute, whether or not the side was already buyable before it. Beside it, information only: the same count with the ask also held to 15c to 64c in each of those minutes.

### Question 3: a detector, from Kalshi's own screen

Each uses only candles ending at or before its minute. An event whose market has closed at or before that minute is not flagged.

13. **D1, frozen after the start (minute S plus 60):** the first-named contract has a quote at S by rule 7, and every candle ending after S and at or before S plus 60 shows a two-sided quote whose mid is within 2c of the mid at S. A missing minute is an unchanged minute.
14. **D2, no trade after the start (minute S plus 60):** the volume of both contracts together, over candles ending after S and at or before S plus 60, is under 10 contracts.
15. **D3, ran before the start (minute S):** for either contract, the mid at S is 10c or more under its mid at S minus 180, both by rule 7.
16. Printed for each detector: voids flagged of all sampled voids, matched played events flagged of all sampled played events, and the implied share of voids among flagged events at the window's own base rate b (voids over voids plus played, counted on every event of rule 2, not only the sample): share = (f_void x b) / (f_void x b + f_played x (1 minus b)).
17. **Line 2 (unchanged):** that implied share is 30% or more.

### The reading

18. **"Worth a rule"** only if ONE detector meets lines 1, 2 and 3 together. Otherwise the card is CLOSED with no try spent, and the page says which line failed for each detector.
19. Every "or more", "or less", "within" and "under" is compared with a tolerance of 1e-9. Voids are counted, never filtered. The held-out folder guard runs on every path.
20. **Requests:** one batched candle request covers tickers whose windows fit one time range within 100 tickers and 8,500 candles. Ceiling 300. If the sample needs more, no job is written and the count goes to the Head; the sample is not cut.
21. **Order:** scorer frozen by commit and sha256, Auditor B CLEAN, a second build from this text by another desk, then the pull.

## AMENDMENT 2, Nov 13, 2026, 01:18Z: the Head of R&D's ruling on the carry (01:15Z), written before any candle of these markets was requested or read

1. **The registered carry stands** (rule 7: no age limit inside the event's window; a non-quote candle stops the search).
2. **The reading (replaces rule 18).** Stage 1 says "worth a rule" ONLY IF all three of its lines pass on the registered carry AND none of them fails on the 60 minute carry or on no carry. If the carries disagree, stage 1's verdict is "depends on the carry: not decided", no rule is registered, and the next step is a zero-try check of what a missing candle means on these markets against the wheel book recorder's 3 second books (KXCS2GAME is one of its polled series), not a choice of carry.
   Read exactly, for the builder: a detector is "worth a rule" if its three lines pass under all three carries; it "fails" if under every carry at least one of its lines fails; anything else is "mixed". The verdict is "worth a rule" if any detector is worth a rule; else "depends on the carry: not decided" if any detector is mixed; else CLOSED, no try spent.
3. **A stated limit of every figure built on a carried quote.** A carried ask is a quote last SEEN, not a quote that can be paid. So stage 1 measures whether the price stood, not whether an order would have filled, and any later rule is scored only on fills that the recorder's books can confirm or on exact-minute quotes. That is the lesson of REMATCH and of MAPBREAK's quarter of orders that did not fill.
4. Nobody chooses a carry after seeing the lines.
