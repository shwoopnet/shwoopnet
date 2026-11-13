# VOIDSNAP stage 2: the rule, written BEFORE stage 1 is read (Idea Desk B)

**Written Nov 13, 2026, 01:51Z, on the Head of R&D's order of 01:49Z. No candle of any CS2 match market has been requested or read by this desk; stage 1's job (79 requests) is not dispatched yet.** So nothing here can be shaped by stage 1's numbers. Text only.

**This is not a registration yet and it spends no try.** It becomes the registered rule, with its one try, only if stage 1 reads "worth a rule" (`VOIDSNAP_CARD.md`, Amendments 1 to 3) AND the owner has been sent the settlement clause and stage 1's lines by the Head. Research and paper only; nothing here places an order.

`VOIDSNAP-R | family: settlement by rule: a match that is not being played, whose market stands away from where it stood before; buy the side that fell, hold to settlement | risk class: mid price (15c to 64c), 1 contract | stage Idea, text frozen before data, unregistered | tries 0 now, 1 if armed`

## 1. What arms it, fixed now

1. Stage 1's verdict is "worth a rule".
2. **The detector:** of the detectors that stage 1 finds worth a rule (their three lines pass under all three carries), the one with the highest implied share of voids among flagged events under the registered carry (stage 1's line 2 figure). On a tie: the earlier minute (D3 before D1 and D2), then D1 before D2. No other detector is ever used and none is added.
3. **The reference minute:** the one stage 1's line 3 names as the best allowed reference for that detector under the registered carry (S minus 180, S minus 60 or S; for D3 only the first two).
4. If stage 1 reads "depends on the carry: not decided" or CLOSED, this page stays unregistered. If the missing-candle check later shows that a missing candle is an unchanged standing quote, arming it on the registered-carry lines is the Head's decision; the text below does not change.

## 2. The rule

Universe: every CS2 match event (`KXCS2GAME`) with exactly two contracts and a clock in its ticker (the scheduled start S, US Eastern). M is the armed detector's minute (S for D3; S plus 60 for D1 and D2).

1. **The detector fires at M**, exactly as stage 1 defines it, on candles ending at or before M and by stage 1's registered quote rule. The market must still be open at M.
2. **The side.** For each contract: its mid at the reference minute is R (stage 1's quote rule), and its quote at M gives a bid and an ask. A contract qualifies if R minus its ask is 10c or more, its spread is 4c or less, and its ask is from 15c to 64c. If both qualify, the one with the larger R minus ask is taken; on an exact tie, the ticker first in alphabetical order. If none qualifies there is no bet.
3. **One bet per event,** at M only. No second look.
4. **The order and the fill.** A limit at the ask plus 1c. Because a carried ask is a quote last seen and not a quote that can be paid (the Head's ruling of 01:15Z), a fill needs evidence from an exact minute: the first 1-minute candle that EXISTS ending from M plus 1 to M plus 5 decides. Its ask for that side at or under the limit: FILLED, paying the limit. Its ask above the limit, no ask, or an empty book: not filled. No candle in those five minutes: "no fill evidence", counted, NOT a bet. Where the wheel book recorder holds books for the market, a book within 5 seconds after M offering 1 contract at or under the limit is used in place of the candle, and the page says which was used.
5. **Exit:** none. Hold to settlement.
6. **Money. A stated exception to the standing void rule, which needs the Head's say before registration.** The subject of this card is the void settlement itself, so a contract that settles at a set price pays its listed settlement value: cash = settlement value minus the limit minus the fee. A contract that settles yes or no pays 1 or 0. 1 contract; fee 0.07 x limit x (1 minus limit), rounded up to the next cent. (Under the standing rule, "price refunded, fee kept", every void would be a fee-only loss and the card could not be read.)
7. Every comparison carries a 1e-9 tolerance. A candle showing 0.00 and 1.00 is not a quote. Lists are read with status settled and the result as given, never filtered.

## 3. Samples, with fixed date bounds

- **First score (development):** every event of the universe closing from 2026-03-01 00:00:00Z to 2026-09-11 23:59:59Z. This is the block that holds the 293 earlier voids; stage 1 never opens a price of it. Halves by close time: before 2026-06-10 00:00:00Z, and from it.
- **Held-out:** events closing from 2026-10-23 00:00:00Z to 2026-11-30 23:59:59Z. Not listed and not pulled until development survives, the scorer is frozen with a read-once marker, and rule (h)'s joint pull applies (MAPBREAK and INPLAYJUMP hold out the same series from Oct 23).
- **Never scored for the rule:** closes 2026-09-12 to 2026-10-22, stage 1's window. Its voids chose the detector and the reference, so any figure of the rule on it would be "selected on development".
- The rule is scored on EVERY event of a sample, voids and played alike. It never knows which is which.

## 4. What is printed, counts first

1. Events; events with any candle; detector fired; no qualifying side; decisions; filled on a candle; filled on a recorder book; not filled; no fill evidence.
2. Among filled bets: how many settled as voids, how many as wins, how many as losses, per half.
3. The one-way cost by the standing template: the median of (ask at M minus mid at M) plus the fee as charged at the limit, over every event where the detector fired and the taken or best side had a two-sided quote at M.
4. Only then: cash profit factor, n, wins, mean, the event-clustered z, for the sample and each half. Beside it, information only: the same for bets that settled as voids alone and for bets that settled by result alone, and the figure with every decision booked at its limit ("optimistic, no fill test").
5. Every line of a first-score page carries "candle freshness measured on Bitcoin 15 minute only, not on esports".

## 5. Lines fixed before data

- **Count:** fewer than 150 filled bets in the first score, or fewer than 40 in either half, reads "no evidence at n = x".
- **Cost:** a median one-way cost above 4c closes the card on cost before any result is read.
- **Profit factor:** with count and cost met, a cash profit factor of 1.5 or more with each half at 1.0 or more reads "survives development"; anything else reads FALSIFIED.
- **Held-out:** read once, only if development survives, same lines with the count at 60 filled bets (a five week block).
- The shared deflated bar (one-sided z 5.46) is not claimed by a survival; it would make the rule a candidate for a wheel shadow place.

## 6. What it costs, and what I do not know

- **Requests.** The first score needs 1-minute candles of both contracts of every event in its block, from S minus 185 minutes to M plus 5. The block is about 4,950 events. If the batched candle call serves markets that old, my estimate is 700 to 1,000 requests; if they must be asked one contract at a time, as MAPBREAK's history note says, it is about 9,900. **I do not know which, and no request has tested it.** The exact count, from a builder run on tickers and times only, goes to the Head before anything is asked for. If it is over the ceiling the Head sets, the block is shortened from its OLD end by a date fixed then, before any candle, never by a result.
- **The fill rule is strict on purpose.** A quiet market gives no candle in the five minutes after M and so no bet. If most decisions end as "no fill evidence", the honest reading is that history cannot score this rule and only the recorder's books can; the page will say so plainly.
- **Odds, unchanged:** about 5% that this rule clears profit factor 1.5 on its first score and its held-out.
- **A variant under rule (i),** one at most and only after this rule has a read: a resting bid at the reference price less a fixed margin, scored only on the recorder's books and tape. Not written now.

## Dated lines, Nov 13, 2026, 01:53Z: the Head of R&D's say on the two open points (01:51Z), written before stage 1 is read and before any candle of these markets was requested

1. **The money rule (section 2, point 6): ACCEPTED as a stated exception, for this card only.** A bet whose market settles at a set price is paid its listed settlement value, the cash Kalshi actually paid, not "price refunded, fee kept". Reason: standing rule (g) is a conservative convention for a void that interrupts some other bet; here the void settlement IS the outcome under test and the settlement value is the real cash result. Two conditions: the value is read from the market's own settled record in the lists (never inferred from a last trade or a candle); and a bet whose settlement value is missing is booked as a fee-only loss and counted.
2. **The cost of the first score (section 6): the ceiling is 1,000 requests.** Whether to spend it is not decided until stage 1 says "worth a rule". Whether the batched candle call serves markets that old is tested by the Chief of Staff with a request that returns no candle to any desk, only if we get that far.
3. **If old markets must be asked one at a time, the first score runs on a SUBSAMPLE OF ALL EVENTS, chosen by a rule fixed here, before any price:** take the sha256 of the event ticker (its text as listed), read it as a whole number, and keep the event if that number modulo 1,000 is below a cut K. K is the largest value for which the builder's request count for the kept events is at or under 1,000; the builder works from tickers and times only and K is written into the registration before any candle is asked for. Voids are never chosen for the sample and played events are never matched to them: that case-control shape, with voids at half the sample instead of a tenth, would inflate any detector's hit rate and the profit factor with it. Stage 1 may use it because it measures; this rule may not.
4. The minimums do not move with the subsample: fewer than 150 filled bets, or fewer than 40 in either half, still reads "no evidence at n = x". If the subsample cannot reach them on any plausible firing rate, the page says so before the pull, and the Head decides whether the first score is worth its requests.
5. Before this rule is registered the owner gets Kalshi's clause and stage 1's lines from the Head through the EA.
