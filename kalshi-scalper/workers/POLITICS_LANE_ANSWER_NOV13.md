# Politics lane: count, re-check, one rule, recorder (Idea Desk B, Nov 13, 2026)

For the Head of R&D, answering the job of Nov 12 20:14Z (the owner: "politics, midterms, elections are all being considered right?"). Research only. No Kalshi request was made for this page; no result and no price level was read, only tickers, events, close times and whether a quote is two-sided and how wide.

## The answer in six lines

1. **Flow.** Short-dated politics is about 43 events and about 250 markets a week in the cadence series, plus mention markets (at least 6 events and 220 word markets a week, quotes never measured). Almost all of it is ladders: one event with 5 to 15 strikes.
2. **Which families can fill a 60 signal block in 21 to 45 days.** Counting independent EVENTS, no single family can at a 25% firing rate. Pooled count ladders can at 50% (about 26 days), and all cadence families pooled can at 25% (about 39 days). Counting sibling MARKETS, activity counts, shipping counts, approval and mentions each can, but strikes of one ladder settle together.
3. **Cannot under either count:** 2028 primaries and nominees, generic ballot (no market since the midterms), runoffs and specials, post-midterm and leadership (a one-time burst), scheduled events (about 1 a week), politics-leg combos (all close in Nov 2027 or Jan 2028).
4. **Re-check.** Everything that closed stays closed, with one exception: POL-i2 reopens under a different exit (hold to settlement, one-way cost).
5. **One rule, registered before data:** POLGAPH, `polgap/POLGAPH_REGISTRATION.md`. Honest prior about 3%. If the Head rules it a version of INPLAYJUMP under section 7g, the answer to part 3 is "none".
6. **Recorder.** The politics recorder is not recording: 7 polls in 26 hours against about 53 intended, and nothing since Nov 12 21:54Z. The cause was sent to Main at 00:47Z. Fix that before anything is added.

**Honest prior for the owner: politics is slow and nothing in it has evidence today.**

## 1. The count

**Files used:** (A) the Testing Desk's cost snapshot of Nov 12 18:51Z: open markets of the 79 Politics series whose frequency is daily, weekly or monthly (`pull/TESTING_LISTS_BUNDLE`, script `polcount/count_polcost.py`); (B) the politics recorder, 4 folders; (C) the census day, markets settled on Nov 10; (D) V2's 60 day sweep counts; (E) the combo files of Nov 11.

Snapshot (A): 79 series asked, 38 with an open market, 233 open markets; 117 markets and 19 events closing within 7 days; 219 markets within 30 days, 198 two-sided, 107 with a spread of 4c or less.

"A week" below adds the daily series back in: a daily series lists one or two days ahead, so a snapshot shows one event where a week holds seven.

| Family | Open now (markets, events) | Settle a week (markets, events) | Two-sided within 14 d / 30 d | Spread 4c or less within 14 d / 30 d | Weeks to 60 signals at 10 / 25 / 50%, by EVENT | By MARKET |
|---|---|---|---|---|---|---|
| Activity counts (orders, posts, acts, visits, judges, pardons, bills): 22 series open of 48 | 143, 23 in 30 d | about 124, 27 (6 weekly ladders and 3 daily series, one of them daily by its name only; the monthly ladders add about 3 events and 20 markets a week) | 36 of 51 / 118 of 135 | 27 / 49 | 22 / 9 / 4.4 | 4.8 / 1.9 / 1.0 |
| Shipping and straits counts, weekly: 7 series | 61, 7 | 52, 6 | 50 of 52 / 59 of 61 | 40 / 41 | 100 / 40 / 20 | 11.5 / 4.6 / 2.3 |
| Approval and favourability: 3 series open of 8 | 18, 3 | about 72, 9 (one daily ladder of 9 strikes, two weekly) | 16 of 18 / 16 of 18 | 15 / 15 | 67 / 27 / 13 | 8.3 / 3.3 / 1.7 |
| Generic ballot: 2 series | 0 | 0 since the midterms (349 markets on 39 dates in the 60 days before) | none | none | never | never |
| Scheduled events and single questions: 6 series open of 14 | 11, 5 in 30 d | about 1, 1 | 1 of 1 / 5 of 5 | 1 / 2 | 600 / 240 / 120 | the same |
| Mentions (what will a speaker say): NOT recorded | not in any held open list | at least 220, at least 6 (three Trump series: 1,879 or more markets on 52 series-dates in 60 days; one Tuesday held 5 political events and 57 word markets) | NOT MEASURED | NOT MEASURED | 100 / 40 / 20 at 6 events; 30 / 12 / 6 if the nightly shows list every weeknight (about 20) | 2.7 / 1.1 / 0.5 |
| Post-midterm settlement and leadership | recount series: no open market | a one-time burst: 45 events and 303 markets on Nov 10, of which leadership 7 events and 41 markets; about 0 a week from here | not applicable | not applicable | never | never |
| Runoffs and specials | not in any held open list | not a weekly flow: 25 one-off series in the part of the series list I hold; 1 settled on the census day | NOT MEASURED | NOT MEASURED | never | never |
| 2028 primaries and nominees | not in any held open list | 0 inside the 30 day cap: 92 one-off or custom series in the part of the series list I hold | not applicable | not applicable | never | never |
| Politics-leg combos | 38 found Nov 11, all two-sided, 4 to 49 legs, 1 to 5 politics legs | 0: all close 2027-11-03 or 2028-01-14 | not applicable | not applicable | never | never |

**Pooled.** All cadence families: about 43 events and about 250 markets a week. By event: 14 / 5.6 / 2.8 weeks. The tight part only (weekly activity ladders, shipping, approval; about 21 events a week): 29 / 11 / 5.7 weeks.

**What the count does not show.**
- Sibling strikes are not independent signals. A block of 60 market signals from 20 events is 20 pieces of evidence.
- The three daily activity series are thin (median spreads 4.5c to 10c in the cost table), so most of the "27 events a week" in the first row cannot be traded at a sane cost. The liquid part of that family is the 6 weekly ladders.
- "Series I hold" is 3,973 of the public series list; the pull cut it at 5 MB. Counts from it are lower bounds.
- Mentions, runoffs and primaries were never quoted in any file held. One list request a series would settle each; none was made.

## 2. The re-check, under exits, limit entries and pooled seats

| What closed | Verdict now | Why |
|---|---|---|
| POL-i2, overnight gap follow, 24 hour exit | Taker form STAYS CLOSED on cost. A resting form CANNOT BE SCORED. **Reopened in one form: hold to settlement.** | Round trip 9.4c (list quotes) and 6.3c (recorder) against a 5c line. Both legs resting at the mid leaves about 3.4c of fees, but that is a floor: a resting buy in the gap's direction fills mostly when the price comes back, and there is no book or tape to score it. Holding pays one way only (about 2.5c to 3c on the ladders with a 1c to 2c spread) and these ladders settle within days. That is POLGAPH, a new try. |
| Approval and generic ballot NO side | STAYS CLOSED | Read, did not clear: arm A pooled n 127, PF 1.03 at +1c, halves 0.64 and 1.91; all families pooled n 145, PF 0.91. It is the favourite side, so it also needs the owner's exception. Generic ballot has no market. A limit entry saves 1c to 2c on a mean of +0.4c: not a different result. The cheap arm has n 15 and makes about 30 a year. |
| POL-n1, Wikipedia attention spike | STAYS CLOSED | Ten people is ten clusters. Its markets ("out as", "leaves", "fired") are long-dated: a 7 day exit pays a round trip at spreads of about 7c, and a hold breaks the 30 day cap. Pooled seats do not add people. |
| Mention base rates | STAY CLOSED | Negative evidence twice (MENT1 on 71 events; card 84 at PF 0.62 and 0.38), and buyers of mention combos lose 29c to 37c a dollar. A limit entry does not repair a signal that points the wrong way. The family is the largest flow in politics and has no cost row at all: a measurement, not a rule, is the next step (part 4). |
| Nothing happens | STAYS CLOSED for now | POL-k1 NO arm: 7 events with an entry, pooled n 4, PF 0.09. Inside 30 days there are 5 single-question events open, about 1 a week, so the slow-family paper screen (30 independent events) is 30 weeks away. Exits and limits do not change the count. |
| News fade (POL-i1) | STAYS CLOSED on count | Never registered (`POLI1_POWER_COUNT_NOV12.md`): 4 single-question mid-priced markets with volume, 0 jumps of 15c in the one night held, likely under 100 events a year. The owner's three delays (15 minutes, 1 hour, 4 hours) need minute data around a jump, which nothing records. |
| Rule edge cases | NOT A WHEEL RULE | By the owner's rule these are flagged to the owner with the rule text, never automatic. Nothing new to flag today. |

## 3. One rule: POLGAPH

`kalshi-scalper/workers/polgap/POLGAPH_REGISTRATION.md`, with its fixed series list and a lists job that passes the static check (`desk_b_jobs/POLGAPH_LISTS.json`, 69 requests, not to be dispatched yet).

- **Rule in two sentences.** At 07:00 Eastern, in a liquid short-dated politics market whose YES mid moved 5c or more since 22:00 and whose price was steady for the last hour, buy the side the gap points to if its ask is 10c to 64c and its spread is 4c or less, one bet per event and morning. Hold to settlement.
- **Why this one.** It is the only politics shape with a reachable count (pooled count ladders and single questions, 69 series), a one-way cost under the 4c line on the tight ladders, a score possible on candles that exist, and no negative evidence.
- **Against it.** No evidence for it either. On count ladders an overnight move is usually the count arriving. The published calibration work supports a side above 50c only weakly and argues against a side under 50c. Prior about 3%.
- **Two rulings it needs from the Head.** (a) Whether section 7g makes it a version of INPLAYJUMP; if so, part 3 is "none". (b) The lane rule that a politics place may pool sibling markets of one family: this card pools two families (activity counts and shipping counts) and the single questions, with approval left out.
- **What it costs.** One try. A ceiling of 380 requests (lists 69, hourly candles 120 to 200, fill minutes at most 61), none before the scorer is frozen and audited, and none ahead of Friday's queue. Held-out from Nov 13 under rule (h).
- **What the count says about its speed.** In the one night held (Nov 11 to 12), 29 of 62 mid-priced markets with volume moved 5c or more (approval markets included, which this card leaves out). After the band, steadiness, spread and liquidity steps and one bet per event, my guess is 20 to 40 fired bets a week, so a 60 signal block in two to three weeks. That guess is the first thing the count stage replaces.

## 4. The recorder

1. **It is not recording.** 5 runs since Nov 11, 3 of them scheduled; 4 folders and 7 polls on `pol-data` in 26 hours against about 53 intended; none since Nov 12 21:54Z. The self-chain died at its first link (the successor was dispatched 6 minutes after the run started, found a fresh poll, skipped, and a skipped run does not chain). Likely cause and two fixes went to Main at 00:47Z.
2. **Mention series to add to the quote recorder,** for a cost row and a count before any rule: KXTRUMPMENTION (26 dates in 60 days, about 3 events a week), KXTRUMPMENTIONB (16 dates, about 2 a week), KXTRUMPSAY (10 dates, about 1 a week); and three nightly shows seen on the census day only, events a week not measured: KXWORLDNEWSMENTION, KXTHEWEEKNIGHTMENTION, KXLASTWORDMENTION. Six series, about 6 more requests a poll. Other speakers get a one-off series each (Hegseth on Nov 10), which a fixed list cannot follow.
3. **A book-and-tape recorder, if one is built:** the eight tight weekly ladders, about 75 markets open at once: KXTRUTHSOCIAL, KXTRUMPACT, KXEOWEEK, KXBABELMANDEBWEEKLY, KXHORMUZWEEKLY, KXHORMUZPEAK, KXHORMUZMAX, KXPANAMAWEEKLY. One batched book read covers them all. Every 60 seconds all day (1 request a minute), every 5 seconds from 06:00 to 08:00 Eastern (12 a minute for two hours), the tape after each close (about 65 markets a week, about 150 requests), 8 list reads an hour. About 2 requests a minute on average, 13 at the peak, on a runner's own address, not the shared research budget.
4. **My recommendation: do not build it yet.** POLGAPH's count and cost lines need only candles. A book recorder earns its minutes only if those lines survive, because the resting variants are what it would score.

## Scripts and files

- `polcount/count_polcost.py` (new, with the held-out folder guard), `polcount/count_families.py`, `polcount/count_polrec.py`.
- `polgap/POLGAPH_REGISTRATION.md`, `polgap/POLGAPH_SERIES.json`, `desk_b_jobs/POLGAPH_LISTS.json`.
- Sources read: Refinement's `NOSIDE1_READ_OUTPUT.txt`, `POLITICS_STEP2_RESULTS.txt`, `POLITICS_CARDS_NOV11.md`; the Testing Desk's `POLCOST_TABLE_NOV12.csv` and `COST_CLOSED_SURVEY_NOV12.md`; Idea Desk C's `POLITICS_NEAR_RESOLUTION_EVIDENCE_NOV12.md`; `docs/POLITICS_RULES.md`.
