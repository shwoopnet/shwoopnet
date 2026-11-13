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
