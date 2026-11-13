# Wheel admit packets from logs already recording (Idea Desk B, Nov 13, 2026, 00:18Z)

Asked for by the Head of R&D at 00:00Z: up to 3 packets, due 06:00Z, from the combo recorder, the politics recorder and the wheel book recorder. **Honest count: 1 packet. For the rest the answer is "none, and what it would need".** No outcome was joined to anything here and no threshold was picked from a result.

## Packet 1: S3, combo house side (paper only)

| Line | |
|---|---|
| **Id** | S3 |
| **Mechanism, one sentence** | Buyers of many-leg combos pay more than the legs are worth together, so the NO side of a high-priced combo is bought and held. |
| **Market or series** | Kalshi's cross-category combos (the multi-leg series the combo recorder lists; `exchange_index` 1 in its files). A combo is a one-off ticker, so a seat per market cannot exist: this place is POOLED over the combo series, one fill per combo and per event, ever. |
| **Entry** | Buy NO at the posted NO ask plus 1c when that price is 60c to 90c, with 3 or more contracts resting, volume above zero, 2 to 30 legs, closing 1 hour to 14 days ahead; at the first 30 minute snapshot where the combo qualifies; at most 10 new fills a snapshot. |
| **Exit** | Hold to settlement. No rule (i) variant: there is no book-and-tape reason for one here, and a taker exit would pay a second spread. |
| **Registration** | `S3_COMBO_HOUSE_SIDE_REGISTRATION.md`, registered Nov 12 before any scoring; scorer `combo_s3/s3_score.py`. Entries count from 2026-11-13 00:00 UTC; development read on or after 2026-11-26; held-out read on or after 2026-12-12. One try. |
| **Log folder and stop date** | Branch `combo-data`, `combo/<date>/<HHMM>/` (`quotes`, `books`, `trades`, `coverage`, and the daily `results`), every 30 minutes by design, to 2027-01-31. Everything the signal needs at the decision is in `quotes`. |
| **Expected signals per 21 days, COUNTED from the log, no outcome joined** | The log holds 2 snapshots (Nov 12, 14:35Z and 21:36Z). Each has 400 recorded combos and exactly 1 that meets S3's conditions, a different event each time: **2 qualifying events in 2 snapshots.** That is too little to project. If the recorder keeps pushing 2 or 3 snapshots a day, about 40 to 60 in 21 days; if it reaches its designed 48 a day, more, but one fill per event caps it. I recount on Nov 14 and Nov 16 and send the figure. Also seen: the recorder's list read is cut at 5,000 combos and it records 400, so the log sees a part of the market. |
| **Closest existing mechanism, and why this differs** | Favourite held to settlement (declined, GOLDHOLD row). S3 is the same shape, a high-priced side bought and held, and is allowed ONLY by the owner's written exception of Nov 12 for combos, on paper. It differs in the market (many-leg combos, where a published study of 12,639 Kalshi combos found the combo priced above the product of its legs only from about 7 legs up) and in having no live order. The earlier combo test MVE1 looked at the cheap side of combo prints; this is the other side. |
| **Declined list** | Combo house side is PAPER ONLY under the owner's Nov 12 rule: this place can be a shadow record, never a seat, without the owner's own popup. The ban on 65c to 87c weather NO legs: S3 buys NO on the COMBO, not on a leg, but a combo can be built from weather legs. The registration does not exclude those. The recorder has stored each combo's leg tickers since its second snapshot, so they can be counted; **the Head should rule whether combos with a weather leg are left out of the wheel's record.** I have a dated check of the leg-ticker column on Nov 19. |
| **Does it buy at 88c or above?** | Yes: the band runs to 90c. The 150 signal rule applies. |
| **Honest odds** | Unchanged from the registration: low. The published leg-count result says the overpricing starts at about 7 legs; the 2 qualifiers seen so far have 4 and 5 legs. |

**On the optional extra cut (7 or more legs) the Head allowed for the Nov 26 read:** I do NOT register it now. On the log so far 0 of 2 qualifiers have 7 or more legs although about 70% of the recorded combos do, which says many-leg combos rarely meet the price, size and volume conditions. A cut that is likely empty is a spent try for nothing. I look again on Nov 19 with a week of snapshots and decide before Nov 26.

## No packet: REMATCH (CLOSED, recorded on two builds)

Closed at stage 1 on tradeability and count, no try spent: of 2,404 eligible pairs only 85 had the previous loser's contract two-sided at the reference minute and none of the 85 had a spread of 4c or less; 6 projected development bets against a floor of 300. **What it would need:** nothing a log can give; only a count from the wheel book recorder showing tight early quotes on e-soccer would reopen the ground, as a new card.

## No packet: MAPBREAK (CLOSED at step 1, recorded on two builds)

Closed at both looks with both tries unspent; not falsified. The gap is real but rare and about a quarter of orders do not fill a minute later, so the largest title yields about 70 filled bets in six weeks against a minimum of 150. **What it would need:** a book and a tape for map and match markets (the wheel book recorder's phase 1 covers CS2 and Dota 2), and then a new registration counted forward.

## No packet: INPLAYJUMP

Lists, pilot and validation have not landed. **What it would need:** the cost pilot to pass, then the wheel book recorder's log for the three clock families (e-soccer, table tennis, e-basketball). Tennis is phase 2 of the recorder.

## No packet: politics (answered in full on Nov 13)

`POLITICS_LANE_ANSWER_NOV13.md`: about 43 events and 250 markets a week in the short-dated cadence series, nearly all ladders; everything that closed stays closed except POL-i2 under a hold exit, registered as POLGAPH (one try, about 3% odds, scorer audited and matched by a second build, nothing requested yet). It is a research card, not a wheel place: whether a pooled series can hold a place is the Head's to take to the owner, and only if its development read is not under 1.0. **What a politics place would need beyond that:** a politics recorder that records (its chain was fixed on Nov 13) and the mention series added to it.

## No packet yet: VOIDSNAP (new on Nov 13)

A zero-try hindsight measurement on CS2 matches voided at Kalshi's "fair market price" (195 of 2,006 match events in six weeks). Scorer audited, second build matched, 79 requests waiting for the owner's merge of the job file. Its stage 2 rule is written before stage 1 is read and is unregistered. **What a place would need:** stage 1 to read "worth a rule" under all three quote-carry readings, the owner to have seen Kalshi's clause, and then fills the wheel book recorder's books can confirm.

## What is left on this desk that could still become a candidate (asked by the Head of R&D; rewritten Nov 13, 00:51Z, after the night's reads)

Said plainly: **nothing on this desk has evidence today, and three cards closed overnight.**

**Closed, each recorded by the Head of R&D on two builds printing the same figures:**
- **REMATCH:** closed at stage 1 on tradeability and count, no try spent (of 2,404 eligible pairs only 85 were two-sided at the reference minute and none of the 85 had a spread of 4c or less; 6 projected bets against a floor of 300). Its resting-entry variant falls with it.
- **MAPBREAK:** closed at step 1 at both looks, both tries unspent. The gap is real but rare and about a quarter of orders do not fill a minute later, so the largest title yields about 70 filled bets in six weeks; the card cannot reach a verdict on Kalshi's history and is closed, not falsified. Its resting-target variant and both wheel places fall with it.
- **TIE3:** closed, "efficient, move on". No cell shows the Tie 8c or more under its base rate; the best is +0.8c, and in NHL periods the Tie is priced above its base rate.
- **PREMOVE:** withdrawn unread by its author. **NHLOT:** cannot produce a candidate as built (hindsight window, no live detector); its price measurement is still owed when its candles land.

**Still open, in the order each could next produce a read:**

| Item | What is pending | When | My odds |
|---|---|---|---|
| **VOIDSNAP** (a CS2 match voided at Kalshi's "fair market price" still trades away from it) | A zero-try hindsight measurement, first in the Head's order. Sample named (195 voids, 195 matched played matches), scorer frozen, 79 candle requests built; waits for the auditor and a second build. No rule and no try until it says "worth a rule"; the Head sends the owner the rule text first. | As soon as the audit and second build are done | 20% that stage 1 passes; about 5% overall |
| **POLGAPH** (politics: follow an overnight gap, hold to settlement) | Registered Nov 13 before data as the one permitted variant of POL-i2; ruled not a version of INPLAYJUMP; 1 try. Scorer frozen and with the auditor; a second build is asked for; then at most 380 requests. | After VOIDSNAP and Friday's reads | About 3% |
| **INPLAYJUMP** (five families) | Lists, the 5 request cost pilot, the tennis validation pull, then up to 1,800 candle requests. The third and last look at this idea. | Friday at the earliest | About 1% a family |
| **S3** (combo house side, paper) | Forward snapshots; development read Nov 26, held-out Dec 12. | Nov 26 | Low |
| **Hourly temperature** | A cost and settlement-source measurement, zero tries, last in the pull queue. A card only after it. | Next week | Low; everyone can see the thermometer |
| **SOCDERIV** (soccer legs against each other) | A measurement, paused behind the rest. | Not scheduled | Low |
| **Politics lane** | Answered Nov 13 (`POLITICS_LANE_ANSWER_NOV13.md`): about 43 events and 250 markets a week in the cadence series; everything that closed stays closed except POL-i2 under a hold exit, which is POLGAPH. | Done | Politics is slow and nothing in it has evidence |
