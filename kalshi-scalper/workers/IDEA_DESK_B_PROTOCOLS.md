# Idea Desk B: ready-to-run protocols for the top 3 cards (Nov 11, 2026)

Cards: `workers/IDEA_DESK_B_NOV11.md`. Written BEFORE any price or outcome is read for these three. Nothing is live, nothing was run against Kalshi (0 requests by this desk). Each protocol can be handed to a worker as is once the Chief of Staff gives it a share of the Kalshi budget; the worker commits this file's hash with its first pull.

Shared rules: public GET only, no key; stop at the first 429 and write what was read, no retry inside a run; cash basis; fee 0.07 x p x (1 - p) per contract, reported unrounded and rounded up to the cent at the stated contract count; slips +0c and +1c; one registered run, refused a second time; the held-out part is never pulled until the development result is committed. Deflation count is stated per protocol and goes on the shared ledger.

---

## Protocol 1: NESTCOMBO (card 1)

**Claim under test:** some listed combos have legs that are all implied by one leg, and such a combo can be bought, together with NO on that one leg's single market, for under $1 after fees.

**Prediction, registered now:** fails at the Stage A gate or at the count (the builder blocks nested legs, or the combos have no resting seller). Probability of a pass 4% (lowered from the card's 6% after the two corrections below).

**Two corrections to the card, found while preparing this protocol:**
1. The card said V2 holds combo leg lists for an offline count. It does not. `workers/scan_ledger/kalshi_combo_*.ids.gz` are rule ids from the 15 minute pair scans (COMBO1 to COMBO3), not combo markets, and `POLCOMBO1_CENSUS.json` holds only leg-prefix counts (its read stopped on a 429 after 7 requests). So Stage A needs Kalshi requests; there is no zero-call step.
2. PARLAY1 found that only 30 of 254 open combos had a real resting ask; most combo liquidity is quoted on request. A public read sees only resting asks and past prints. Asking for a quote is an authenticated account action, which research may not take. So Stage B can only find locks against RESTING asks, and Stage C measures past PRINTS as evidence of how quoted combos are priced.

What the census does tell us (`POLCOMBO1_CENSUS.json`, 300 open combos): the commonest leg families are NBA player points (846 legs), NBA game winner (387), rebounds, threes, assists, NBA total (72) and spread (67), college basketball winner, total and spread, tennis matches, NFL touchdowns and game winner. So the nested types that can occur are spread with winner, ordered player-stat strikes, and ordered totals.

### Definitions (frozen)

A combo is **fully nested** when one leg D (the dominant leg) implies every other leg under the contracts' rules. Admitted pair types, each only after its two rules texts are read and the implication is confirmed in writing in the result file (overtime, postponement, void and tie clauses):

| Type | D implies L when | Example leg families |
|---|---|---|
| T1 spread and winner | D = team covers a NEGATIVE spread, L = same team wins the same game | KXNBASPREAD with KXNBAGAME; KXNCAAMBSPREAD with KXNCAAMBGAME |
| T2 ordered player strikes | same player, same stat, same game; D's threshold is higher | KXNBAPTS, KXNBAREB, KXNBAAST, KXNBA3PT |
| T3 ordered totals | same game; D = over the higher line, L = over the lower (or under the lower implies under the higher) | KXNBATOTAL, KXNCAAMBTOTAL |
| T4 futures chain | same team: title implies conference implies playoffs | only if both appear as legs |
| T5 weather strikes | same city and day; D = high above the higher strike | KXCITIESWEATHER legs |

A combo is **contradictory** (arm 2) when two YES legs cannot both happen: both teams to win one game; over a higher line and under a lower line; two winners of one exclusive event.

A combo with nested legs PLUS other legs is **redundant-leg**: reported as a count only, not traded (its fair value is the combo without the implied leg, which may not be listed).

Leg side matters: a NO leg is converted to its YES statement before classifying. Anything the classifier cannot parse is "unclassified" and reported, never guessed.

### Stages and request budget

- **Stage A, structure (no price used):** GET /markets for each combo series (`KXMVENBASINGLEGAME`, `KXMVENFLSINGLEGAME`, `KXMVECROSSCATEGORY` and its shards, the NBA, NFL and sports multi-game series, the weather collections), status open, up to 3 pages of 1,000. Parse `mve_selected_legs`. Classify offline. About 25 requests. **Gate: if fully nested plus contradictory combos number under 30, STOP: CLOSED (the builder does not allow them).**
- **Stage B, resting locks:** the Stage A response already carries each combo's bid and ask. For every fully nested combo read the dominant leg's single market (batched by tickers, about 1 request per 20 combos). A **lock-timestamp** is: combo YES ask a, single YES bid b, both with displayed size of 5 or more, and a + (1 - b) + fee(a) + fee(1 - b) of $0.99 or less at 5 contracts. For arm 2: combo NO ask (1 minus the combo's YES bid) plus its fee of $0.97 or less.
- Stage A and B are repeated at three fixed times a day for 7 days (18:00, 19:30 and 21:00 US Eastern, when NBA combos are busiest): about 30 requests a pass, about 630 in the week, 90 a day. If the budget is smaller, run one pass a day for 7 days (about 210).
- **Stage C, prints (history, descriptive):** for settled fully nested combos with volume, the combo's last trade price against the dominant leg's 1 minute candle at that minute (2 requests each, at most 100 combos). Output: the distribution of print divided by the single's mid. No profit is computed.

### Verdict rules

- **PASS (a count, not a PF):** 20 or more lock-timestamps on at least 5 different games or events in the 7 days. A pass only earns a probe SPEC for the owner (a lock set is about $1 at one contract, inside the $2 per parlay rule; the combo sits on its own shard, so the spec must say where the money has to be).
- **CLOSED:** the Stage A gate, or under 20 lock-timestamps.
- **Lead for the owner, not a pass:** Stage C shows the median print at or below 0.90 of the single's mid on 30 or more combos. That would mean quoted nested combos are sold under the single, and the only way to act on it is a quote request from the owner's account, which is the owner's decision.
- Reported whatever happens: counts by type, the redundant-leg count, unclassified count, the share of combos with any resting ask.

### Known ways this can be wrong

Rule mismatch between the combo and the single on a void (a postponed game may void one and not the other): every admitted type's void clause is quoted in the result. Fee rounding: at 1 contract each leg pays at least 1c, so a lock needs about 3c of room; the test uses 5 contracts. A displayed size can vanish before the second leg fills: a real probe would need both orders sent together and would carry leg risk.

**Tries:** N +2 (lock arm, contradiction arm). No outcome is read at any stage.

---

## Protocol 2: ECONLAG (card 2)

**Claim under test:** in the minutes after a scheduled macro release, thin Kalshi macro markets lag the next-meeting Fed decision market by enough to pay for a round trip.

**Prediction, registered now:** fails, most likely on the spread at entry or on the count. Probability of a pass 8%.

### Universe (frozen before any candle is read)

- **Print events:** CPI, Employment Situation, PCE (8:30 AM Eastern) and the FOMC statement (2:00 PM Eastern), every scheduled date from 2024-10-01 to 2026-10-31, from the BLS, BEA and Federal Reserve calendars (V2's `studies/EVENT_CALENDAR_2026.csv` covers Aug to Dec 2026; earlier dates from the agencies' archived schedules). Rescheduled or cancelled releases (the 2025 shutdown) are dropped by the calendar, not by looking at prices.
- **Fast market F:** in `KXFEDDECISION` for the next scheduled meeting after the print, the single market with the highest YES mid at T-5 minutes.
- **Slow markets:** (S1) `KXFEDDECISION` for the meeting after that; (S2) the meeting after that; (S3) `KXRATECUTCOUNT` for the calendar year; (S4) `KXFED` for the year's last meeting. In each, the ONE market whose YES mid at T-5 is closest to 50c, fixed at T-5. Series names are confirmed from one read of the public series list before anything else; if a name differs, the substitute is chosen by title and logged before any candle is read.

### Rule (frozen)

1. **Trigger:** F's mid changes by 0.08 or more between the candles ending T-5 and T+10 minutes.
2. **Beta:** for each slow market M, the slope of M's daily mid change on F's daily mid change over the 60 trading days before the print, print days excluded. Skip M unless R squared is 0.2 or more and the absolute slope is between 0.2 and 3.
3. **Lag:** implied move = beta x F's move. M qualifies if, at T+10, it has moved less than 25% of the implied move in the implied direction AND the part still owed is 0.04 or more.
4. **Entry:** at the T+10 candle, buy the side the implied move favours at its ask, if the ask is 0.10 to 0.80 and the YES spread is 0.03 or less. 3 contracts. One entry per slow market per print.
5. **Exit:** arm A, sell at the bid of the candle ending T+4 hours; arm B, T+24 hours. If there is no bid in the 30 minutes before the exit time the trade is dropped and counted; over 10% dropped makes the arm DATA_LIMITED.
6. **Cost:** fee on the entry AND on the exit; slips +0c and +1c on both.

### Sample, split and statistics

- Expected about 70 print days and 60 to 140 entries per arm.
- **Split by print date:** development = the first two thirds of print days; held-out = the last third, not pulled until the development result is committed.
- **Minimums:** 60 entries in development and 30 in the held-out part, on at least 20 and 10 print days. Under that: NOT_ENOUGH_DATA, and the forward log takes over (about 3 prints a month).
- **Bar:** cash PF 1.5 or better at +1c in development AND in the held-out part; the 90% interval of mean net per contract, bootstrapped by PRINT DAY (2,000 draws, seed 11), above zero in development.
- **Placebo, scored alongside and never traded:** the same rule at 8:30 AM and 2:00 PM Eastern on the weekday one week before each print. If the placebo shows the same result the effect is not about the print.
- **Kill:** PF under 1.0 on an arm in development (FALSIFIED for that arm); median spread at entry above 3c; the placebo within 0.1 PF of the treated arm.
- Reported whatever happens: entries by slow market, the share of prints that trigger, mean implied move, mean move realised by exit, and the overlap of entry minutes with EVENT830 windows (for the correlation check later).

### Requests

One 1 minute candle read per market per print day (F plus up to 4 slow markets): about 350. Daily candles for the betas: about 20. Series and market lists: about 15. Total about 385, a day and a half at 4 a minute.

**Tries:** N +2 (two exit arms). The placebo is not a try.

---

## Protocol 3: BALLOTNO (card 3)

**Claim under test:** 14 days before the vote, Kalshi overprices passage of citizen initiatives and underprices passage of measures referred by a legislature.

**Prediction, registered now:** NOT_ENOUGH_DATA or a fail. Probability of a paper pass 7%.

**Owner rule this sits under, quoted:** "Nothing happens (NO side of 'will X happen by date'): only markets within the politics hold window ... NO bought at 60c to 88c; 1 contract; at most $5 at risk per market; ONE market per story." Arm N is a favourite-side hold and is PAPER ONLY. Nothing here asks for more than that rule.

### Universe (frozen before any price is read)

- Every settled pass or fail market in `KXSTATEBALLOTMEASURE` (124 settled markets in the Nov 11 elections census) and in any other Elections series whose title contains "ballot measure", "proposition", "amendment", "referendum", "initiative" or "question", from the public series list. Vote-share and margin bracket markets are excluded. The list is written to a file before any candle is requested.
- One market per measure (if a measure has several pass or fail markets, the one with the highest volume).

### Tagging (from Wikipedia through its API, before any price is read)

For each measure, from the year's state ballot measure pages: **type** = citizen initiative; legislatively referred; bond or tax; veto referendum; commission or automatic referral. Also the result, as a cross-check against Kalshi's settlement.

Excluded and logged: veto referendums and any measure where a YES vote keeps the status quo (the polarity is not the one the claim is about); measures not found on Wikipedia; markets whose Kalshi result disagrees with the certified result.

### Rule (frozen)

- **Look:** the daily candle of the day 14 days before election day. If the market opened later, the first day with a two-sided quote, provided it is 3 or more days before the vote; otherwise excluded. The YES spread must be 0.10 or less.
- **Arm N (paper):** type = citizen initiative and YES mid between 0.12 and 0.40. Buy NO at the NO ask (1 minus the YES bid), which must be 0.60 to 0.88. 1 contract.
- **Arm Y:** type = legislatively referred (bond and tax measures excluded) and YES ask between 0.30 and 0.75. Buy YES at the ask. Scored per contract (a probe would be 3).
- Hold to settlement. Fee on entry only.

### Sample, split and statistics

- Expected 25 to 50 entries per arm, on perhaps 6 to 10 election dates.
- **Split:** measures ordered by election date; the first two thirds of DATES are development, the last third held-out, with every measure of a date in the same part.
- **Minimums:** 30 entries per arm in development plus held-out together, at least 20 in development, and at least 3 election dates in development and 2 in the held-out part. Under that: NOT_ENOUGH_DATA.
- **Bar:** cash PF 1.5 or better at +1c in development AND held-out; the 90% interval of mean net per contract, bootstrapped by election date (2,000 draws, seed 11), above zero in development. For arm N the result must also survive removing its single best date.
- **Kill:** PF under 1.0 in development.
- Reported whatever happens (description only): realised pass rate by type and by YES price bucket (0.10 to 0.25, 0.25 to 0.40, 0.40 to 0.60, 0.60 to 0.75, 0.75 to 0.90), with counts and Wilson intervals. That table is the lasting product even if both arms are too thin.

### Requests

Series list 2, markets per series about 4, one daily-candle read per market about 124 to 150, Wikipedia about 10 page reads. Total about 160 Kalshi requests, under an hour at 4 a minute.

### Honest limits

Measures on one date in different states are close to independent, which is why this is better sampled than winner markets; but the same national mood can move several at once, so the bootstrap is by date. After a paper pass the forward test is slow: large ballot dates are rare until November 2027 and 2028.

**Tries:** N +2.

---

## Zero-call work done today: first partial read for card 7 (WXCOMBO-XCITY), part A

Card 7 registered a measurement before any combo is priced: how strongly do NWS forecast errors in nearby cities move together. Read once on Nov 11 from our own recorder files (`quote-data` branch, `wxens/nws` and `wxens/obs`, Nov 4 to 11); error = observed high minus the earliest NWS forecast high for that day.

| Look | City-days with a forecast and an observation | Error sd | Near pairs (under 400 km): pair-days, days | Pooled correlation, near pairs | 400 to 1,500 km | Over 1,500 km |
|---|---|---|---|---|---|---|
| Day-ahead forecast | 48 (14 cities, 2 to 5 days each) | 1.95 F | 15 pair-days on 5 days, 5 pairs | 0.34 | -0.10 (58) | -0.12 (147) |
| Same-day morning forecast | 30 | 1.86 F | 9 pair-days on 4 days | -0.11 | -0.01 (35) | -0.05 (63) |

**Verdict: NOT_ENOUGH_DATA.** Fifteen pair-days on five days cannot tell 0.34 from zero or from the assumed 0.45; nothing is concluded and the assumption in the card stands unmeasured. Two facts worth having:

1. **The recorder yields far fewer usable days than the card assumed:** about 6 day-ahead city-days a day, not 14, and about 2 near pair-days a day. The watch list has only 5 pairs under 400 km (Austin, Dallas and Houston with each other; Las Vegas and Los Angeles; New York and Philadelphia). At this rate 150 near pair-days, the least that gives a usable interval, arrive in late January, not on Dec 3. The card's date is corrected.
2. The far-apart pairs sit near zero or slightly negative (the pooled mean was removed, so a slight negative is expected), which is at least consistent with distance mattering.

This counts as one look at the measurement. The next look is at 150 near pair-days, not before.

---

## Run log and amendments (each written before the read it governs)

**NESTCOMBO Stage A, first run (Nov 11, 22:43Z): stopped at request 2.** Request 1: open markets of series `KXMVENBASINGLEGAME`: HTTP 200, 0 markets. Request 2: `KXMVENFLSINGLEGAME`: HTTP 429, run stopped, not retried. Nothing was classified. Two things learned: (a) open combos are not listed under the single-game series tickers; V2's census found them under three collections (`KXMVECROSSCATEGORY-R`, `KXMVECROSSCATEGORY-SHARD1-R`, `KXMVESPORTSMULTIGAMEEXTENDED-R`, about 146,000 open combos by Refinement's count); (b) V2 already has a worker paging those collections (14 of about 145 pages done).

**NESTCOMBO amendment 1 (Nov 12, before any further read):** Stage A is not re-run by this desk, so the same 146 pages are not pulled twice from one shared budget. Instead the nested-leg classifier of this protocol is run on V2's page output as it lands (V2's committed list keeps `legs(market:side)` per combo). Zero-call result on the 38 combos committed so far (`POLCOMBO1B_CENSUS_PARTIAL.csv`; a biased slice, all with a politics leg, most with 11 or more legs): fully nested 0, nested leg pairs of types T1 to T3 0, contradictory pairs 0; 14 combos have two or more legs on one game, 7 have one player in different statistics (correlated, not nested); 1 of 38 has a nonzero ask. The gate (30 nested or contradictory combos) is judged when the full page set exists; if V2's output keeps only politics-leg combos, this desk asks for a share of pages instead and says so here first.

**BALLOTNO amendment 1 (Nov 12, after the series list was read and BEFORE any market, price or result was read):** one request listed the Elections series; 46 titles matched the registered title rule (file `universe_series.json`, kept in the run folder). Two exclusions, both by rules already in the protocol, applied now to save requests rather than at tagging:
1. Series that are not pass or fail questions on a measure (turnout, margin, vote share, county splits, "will a referendum be held"): `KXVAREFERENDUMTURNOUT`, `KXPROP50COUNTIES`, `KXCAPROP42V40`, `KXCAWEALTHTAXMOVD`, `KXCANALBERTAREMAIN`, `KXMOVVAREDISTRICT`, `KXALBERTASEPREF`, `KXCABILLIONAIRETAX`, `SCOTREF`, `KXEUREF`.
2. Measures outside the United States, which the protocol's tagging (the year's US state ballot measure pages) cannot type as initiative or legislatively referred: `KXGUINEAREF`, `KXSLOVAKREF`, `KXSWISS10MILLION`, `KXJULYCHARTER26`, `KXJULYCHARTER`, `KXSWISSNOVREF`, `KXTAIWANNUCLEARREF`, `KXTAIWANREF`, `KXFIJIREF`, `KXICELANDREF`, `KXALBERTAREFS`, `KXALBERTAREFYES`, `KXJUDICIALREFORMIT`.
That leaves 23 US series: `KXSTATEBALLOTMEASURE`, `KXCABALLOTMEASURES`, `KXSFBALLOTMEASURES`, `KXDATACENTERMEASURES`, `KXVIRGINIAREDISTRICTING`, `KXCALIREDISTRICTING`, `KXOHDISTRICTS`, `KXMOREDISTREF`, `KXSQ832`, `KXHONOLULUQ4`, `KXBAYAREATRANSIT`, `KXMOPROPA`, `KXKSAMEND`, `KXDCFOIEGRAS`, `KXCAWEALTHTAX`, `KXMOAMD5`, `KXMOAMD4`, `KXFLPROPERTYTAX`, `KXOR120`, `KXCAVOTERID`, `KXMARENTCONTROL`, `KXMDQUESTION3`, `KXLEAGUECITYFLOCK`.
**Request count corrected:** 46 list reads (each series from both the current and the historical endpoint) plus one daily-candle read per development market, so about 150 to 200 in total, not 160. **Held-out rule made mechanical:** close dates are sorted; markets closing on or after the date two thirds of the way through the list of distinct close dates get NO candle read in this run.

**BALLOTNO run 1 (Nov 12, about 00:47Z): stopped at request 5 on a 429, not retried.** Read so far: the series list, and the market lists of `KXSTATEBALLOTMEASURE` (current and historical endpoints) and `KXCABALLOTMEASURES` (historical). 124 settled pass or fail markets, all in `KXSTATEBALLOTMEASURE`, in 39 state events. Results only, NO price read: 83 passed, 41 failed. **All 124 belong to ONE election day (Nov 3, 2026)** (close dates Nov 4 to 10 are settlement dates; one Colorado initiative closed Sept 22 when it failed to qualify).

**BALLOTNO amendment 2 (Nov 12, written after the results above and BEFORE any price was read):**
1. **The PF test is NOT_ENOUGH_DATA by the registered minimum, whatever the prices say.** The protocol requires at least 3 election dates in development and 2 in the held-out part; the main series has one. No PF from this night will be called a pass, and the day-clustered interval cannot be computed from one date.
2. **Development = the Nov 3, 2026 night (all 124 markets). Held-out = other election dates:** the 22 smaller US series in amendment 1 (their prices stay unread) and every later election date, forward. The mechanical "last third of close dates" rule of amendment 1 is withdrawn, because close dates here are settlement dates of one election.
3. **What is still read, as description only:** the registered calibration table (realised pass rate by measure type and by YES price bucket 14 days before the vote, with Wilson intervals) and each arm's mean result per contract, labelled descriptive, one night, not a verdict.
4. **Fewer requests:** prices are read with the batch candle endpoint (many markets in one request), about 2 to 4 requests in place of 124. One try each; a 429 stops the run.
5. **Tagging stays before prices:** measure types are taken from Wikipedia and from the ticker's own code (initiative, legislative referral, bond, question) and saved to a file before the first candle request.

**BALLOTNO tagging, frozen before any price read (Nov 12):** file `workers/ballotno/BALLOTNO_TAGS_2026-11-03.csv` (124 rows: ticker, type, how it was tagged, Kalshi's public result). Source: one read of the Wikipedia page "2026 United States ballot measures" through its API (the Origin column), 72 matched by measure name; the other 52 by rules written in the file's `how_tagged` column (every Nov 3 row of that state has one origin; legislative resolution codes; Colorado's numbering rule for one amendment with no page row). Bond rule fixed now: a legislative measure whose name contains "bond" is type BOND and is in neither arm. Counts: legislative referral 76, citizen initiative 36, bond 8 (plus 1 bond issue listed as OTHER), advisory question 1, veto referendum 1, did not qualify 1 (excluded).

**Results by type on this one night (public settlement results, no price involved):** legislative referrals passed 55 of 76 (72%); citizen initiatives passed 19 of 36 (53%); bonds passed 7 of 8. One election day, so this is a description, not a base rate.

**BALLOTNO price read, try 1 (Nov 12, about 00:52Z): refused.** The first batched candle request got HTTP 429 and the run stopped; no price has been read. Requests by this desk so far, all public GETs: 8 in total (NESTCOMBO 2, BALLOTNO 6), of which 3 were refused with 429. The shared limit was saturated each time, so the 2 a minute share was not usable in practice at these hours.

**NESTCOMBO closed (Nov 12):** untestable from public data. V2's COMBO1 found no posted asks on sampled combos (ask 1.00, bid 0.00 on all 34 with candles; combos are quoted on request), so the lock cannot be priced from the public book. Amendment 1's plan to classify V2's page output is dropped; no further request is made for this card. Verdict: NOT_ENOUGH_DATA, closed. Requests used: 2. Reopening needs a recorder of the live combo book, an owner decision that is not proposed here.

**ECONLAG coordination (Nov 12):** Refinement's economics worker (card 87) pulled hourly candles on other series (no Fed decision, rate cut count or year-end rate series, nothing keyed to print days), so there is no overlap and no shared calendar. ECONLAG uses its own print-day calendar from the agencies' schedules, as registered, and still counts with the economics-release family in the deflation.

**ECONLAG amendment 1 (Nov 12, before any ECONLAG read):** the print-day calendar is taken from Kalshi's own public event list, not from agency web pages: print time T = the close time of the settled event that resolves on that print, for `KXCPI` (CPI), `KXPAYROLLS` (Employment Situation), `KXPCECORE` (PCE) and the meeting events of `KXFEDDECISION` (the statement). One listing request per series, both the current and the historical endpoint (about 8 requests). This gives the actual release time, including releases moved by the 2025 shutdown, with no outside host. Cross-check, no price involved: the Aug to Dec 2026 rows must match V2's `studies/EVENT_CALENDAR_2026.csv` (5 CPI, 5 jobs, 5 PCE, 3 FOMC rows) to the minute; any mismatch is listed and that print day is dropped. Everything else in protocol 2 is unchanged. The name of the rate cut count series is still unverified and is confirmed from the series list in the same pass.

**BALLOTNO price read, tries 2 and 3 (Nov 12, 00:52Z and 00:58Z): both refused (429)**, the first inside a window when the other research pullers were paused, the second with a batch of 10 markets. So the batch candle endpoint is treated as unusable for now and the read falls back to one market per request (31 seconds apart; after a refusal it waits 5 minutes and resumes; it stops for good at 5 refusals). Requests by this desk so far: 10, of which 5 refused. Still no price read.
