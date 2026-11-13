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

## No packet: REMATCH

Its stage 1 read (provisional, one build, Nov 13 00:16Z) prints CLOSED: the later match's market shows no candle around the earlier match's start in about 95% of pairs, and none of the 85 quoted pairs had a spread of 4c or less. Projected development bets: 6 against a floor of 300. **What it would need:** nothing a log can give; the premise (a tradeable price before the earlier match) is not there.

## No packet: MAPBREAK

CS2's count is pending a recount and the other titles are under their minimum until the remaining candles are read; the state must now be observable at the look (Amendments 7 to 10). **What it would need:** the recount and the remaining candles (tonight), a development read not under 1.0, and then the wheel book recorder running: its log (match contracts every 3 seconds through the match, map contracts once a minute, results) records everything the amended rule needs. Signals per 21 days cannot be counted from a log that has not started; from lists it is about 47 best-of-three matches a day across CS2 and Dota 2 before the rule's firing share.

## No packet: INPLAYJUMP

Lists, pilot and validation have not landed. **What it would need:** the cost pilot to pass, then the wheel book recorder's log for the three clock families (e-soccer, table tennis, e-basketball). Tennis is phase 2 of the recorder.

## No packet: a pooled politics place. Is it honest? Not today.

- **The count (from `pol-data`, events not markets, `polcount/count_families.py`):** 17 events close in 7 days across every recorded family together (activity counts 6, shipping counts 6, approval 4 listed, scheduled events 1). No single family reaches 60 signals in 45 days at any firing share; all of them pooled reach it only at about a 50% share.
- **Why a pooled place is not honest now:** a place needs a rule, and there is no politics rule with a mechanism behind it. The one direction with published support near resolution is buying the favourite, which is the banned shape and read flat on our own data (Idea Desk C's page). Pooling families that share no mechanism would pool noise and call it a record.
- **What it would need:** one mechanism that applies to one family with enough events. The only family that looks large enough is mention markets (nightly news shows and speeches: 4 political events with 51 word markets on the one census day), and the politics recorder does not record it. The full answer, with the re-check of every closed politics idea, is due Friday 18:00Z.

## What is left on this desk that could still become a candidate (asked by the Head of R&D, added 00:19Z)

Said plainly: **nothing on this desk has evidence today.** In the order each could next produce a read:

| Item | What is pending | When | My odds |
|---|---|---|---|
| **TIE3** (the Tie in hockey periods, football quarters, soccer first halves) | A price measurement, zero tries: 50 candle requests with the Head's go, scorer with the Testing Desk and Auditor B. If a cell shows the Tie 8c or more under its base rate at a spread of 4c or less, a rule is registered the same hour; it would be the simplest rule on this desk (one quote, one table, a fixed time before a listed start). | Tonight or Friday, when PR 834's pull lands and the scorer is clean | About 15% that a cell survives; about 2% for the research bar |
| **MAPBREAK** (esports map break) | CS2's recount with the 4c comparison fixed; the remaining candles; then the development read under Amendments 7 to 10. With the minimum now on filled bets, Dota 2, League of Legends and Valorant will most likely read "no evidence at n = x". | Tonight or Friday | About 2%; it cannot reach the bar without history |
| **INPLAYJUMP** (five families) | Lists, the 5 request cost pilot, the tennis validation pull, then up to 1,800 candle requests. The third and last look at this idea. | Friday at the earliest | About 1% a family |
| **S3** (combo house side, paper) | Forward snapshots; development read Nov 26, held-out Dec 12. | Nov 26 | Low |
| **Hourly temperature** | A cost and settlement-source measurement, zero tries, last in the pull queue. A card only after it. | Next week | Low; everyone can see the thermometer |
| **SOCDERIV** (soccer legs against each other) | A measurement, paused behind the rest. | Not scheduled | Low |
| **Politics** | The count says no family fills 60 signals in 45 days; the answer with one rule or "none" is due Friday 18:00Z. | Friday 18:00Z | "None" is likely |

**Closed or falling:** REMATCH (stage 1, provisional) and with it its resting-entry variant; PREMOVE (withdrawn unread); NHLOT cannot produce a candidate as built (hindsight window, no live detector). MAPBREAK's resting-target variant waits on MAPBREAK's own read.
