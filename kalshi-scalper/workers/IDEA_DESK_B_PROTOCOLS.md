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

**BALLOTNO price read, single-market fallback (Nov 12, 01:03Z to 01:30Z): stopped at the cap of 5 refusals.** 15 requests, 10 markets read (daily candles Oct 1 to Nov 3), 5 refused with 429, 113 markets left. Nothing was scored: 10 of 123 is not a description of anything. The read is resumable from the saved file. Requests by this desk so far: 25, of which 10 refused. At this refusal rate the remaining 113 markets would take about four hours and about forty more refusals, so this desk has STOPPED reading and waits for either a quiet limit or the separate pull route the Chief of Staff has asked the owner about. ECONLAG (about 390 requests) is not started for the same reason.

**BALLOTNO price read, quiet window (Nov 12, 08:01Z to 10:07Z): finished.** One market per request, 61 seconds apart, as allowed by the Chief of Staff for 08:00Z to 11:00Z. 115 requests, 2 refused with 429 (each waited 5 minutes and resumed), 113 markets read. The first run was cut off by the session's 2 hour task limit at 116 markets held and was restarted once for the last 7. All 123 markets of the Nov 3, 2026 development night are now held (daily candles Oct 1 to Nov 3). Requests by this desk in total: 140 public GETs, of which 12 refused. The held-out set (the 22 other US series and future dates) is still unread.

**BALLOTNO result: a DESCRIPTION of one election night, not a verdict (amendment 2).** The registered PF test is NOT_ENOUGH_DATA: one election date is one cluster. Public market data and public results only.

Scored: 107 markets at the 14 day look (15 dropped for a spread over 10c, 1 with no two-sided quote, 1 excluded before the read), 121 at the 1 day look. "Gap" is the realised pass rate minus the mean YES mid; the bracket is a 90% Wilson interval on the pass rate.

| Type | Look | n | Mean YES mid | Passed | 90% interval | Gap | Brier |
|---|---|---|---|---|---|---|---|
| Citizen initiative | 14 day | 27 | 0.594 | 0.556 | 0.40 to 0.70 | -3.9c | 0.238 |
| Citizen initiative | 1 day | 36 | 0.623 | 0.528 | 0.39 to 0.66 | -9.5c | 0.154 |
| Legislative referral | 14 day | 73 | 0.696 | 0.726 | 0.63 to 0.80 | +3.0c | 0.116 |
| Legislative referral | 1 day | 75 | 0.700 | 0.733 | 0.64 to 0.81 | +3.4c | 0.110 |
| Bond | 14 day | 7 | 0.876 | 1.000 | 0.72 to 1.00 | +12.4c | 0.017 |
| Bond | 1 day | 9 | 0.882 | 0.889 | 0.62 to 0.97 | +0.7c | 0.116 |
| All | 14 day | 107 | 0.682 | 0.701 | 0.62 to 0.77 | +1.9c | 0.140 |
| All | 1 day | 121 | 0.692 | 0.686 | 0.61 to 0.75 | -0.6c | 0.123 |

All measures by price bucket at the 14 day look (n, mean mid, passed): 0.10 to 0.25: 6, 0.18, 0.00. 0.25 to 0.40: 5, 0.35, 0.40. 0.40 to 0.60: 19, 0.51, 0.47. 0.60 to 0.75: 26, 0.68, 0.65. 0.75 to 0.90: 36, 0.83, 0.92. 0.90 and up: 14, 0.93, 1.00.

The two registered arms at the 14 day look, fee 0.07 x p x (1 - p), held to the result:

| Arm | Slip | n | Wins | Mean per contract | Cash PF |
|---|---|---|---|---|---|
| N: citizen initiative, YES mid 0.12 to 0.40, buy NO at 0.60 to 0.88 | +0c | 3 | 2 | -6.7c | 0.70 |
| N | +1c | 3 | 2 | -7.7c | 0.67 |
| Y: legislative referral, YES ask 0.30 to 0.75, buy YES | +0c | 31 | 17 | -9.8c | 0.63 |
| Y | +1c | 31 | 17 | -10.8c | 0.60 |

What it says, plainly:

1. **The market was close to calibrated on this night.** Over all measures the mean price and the pass rate differ by 2c at 14 days and under 1c the day before.
2. **The type gaps point the way the card guessed (initiatives a little rich, referrals a little cheap) but every one sits inside its interval.** With 27 to 75 measures from ONE night, sharing one electorate mood, none of it is evidence.
3. **The arms as registered lost on this night.** Arm N found 3 trades, far too few to mean anything. Arm Y lost about 10c a contract over 31 trades: referrals priced 0.40 to 0.60 passed only 3 of 12, so the cheap referrals were cheap for a reason. The referral gap is all above 0.75, where buying is a favourite hold, which is close to a declined family and is NOT proposed.
4. **No new cell is proposed from this table.** Picking the best bucket after the read would be chasing one cell of about thirty on one cluster.

**Status: PARKED, as decided in the power analysis.** The next cluster of any size is November 2028 (under 20 measures in 2027). Nothing further is read for this card; the held-out set stays unread so it is still clean if the card is ever reopened. The frozen tags are in `workers/ballotno/BALLOTNO_TAGS_2026-11-03.csv`.

## Protocol 4: ROLLOFF proxy check (registered Nov 12, 2026, before the settled history is opened)

`ROLLOFF | family: outside composition arithmetic, entry the day before resolution, hold | risk class: mid price, 3 contracts, daily events, group D | stage Idea`. Card 13. Main bar, not the slow-family screen (about 365 events a year).

**What is tested now.** Only the feasibility gate on the card: can a simple window average rebuilt from the Wikipedia poll table reproduce the value Kalshi settles the daily approval market (`KXTRUMPAPPROVE`) on? No price is read and no trade is scored at this stage.

**Step 0, the settlement source, read first.** The pull `ROLLOFF_PROXY` (12 public reads, dispatched by Main through kalshi-pull, branch `kalshi-pull-data` under `pull/ROLLOFF_PROXY/`) holds the series' rules text. The rules text is read before any settled value. **If the source is a weighted or model average (pollster ratings, recency or sample weights, house-effect adjustment, a trend line) and not a simple average of recent polls, the card dies on that fact alone** and the scorer is not run for a verdict. If the rules text does not say how the average is built, that is reported as "source method not stated" and the scorer decides. The source's own site is not read (barred).

**Scorer.** `workers/rolloff/rolloff_proxy.py`, committed with this text. Inputs: the Wikipedia poll table as read on Nov 12, 2026 (Wikimedia API, permitted), and one settled value per day from the pull. The quantity (approve share, disapprove share or net) is the one the rules text names.

**Pinned constants (the script carries the same values).**

| Item | Value |
|---|---|
| Settled days used | event dates 2026-09-01 to 2026-11-11 inclusive |
| Fit days (the proxy's window is chosen here) | 2026-09-01 to 2026-10-09 |
| Check days (the kill rule is read here, once) | 2026-10-10 to 2026-11-11 |
| Candidate proxies | window 7, 10, 14, 21 or 30 days by field end date; latest poll per pollster or every poll; a poll usable 0, 1 or 2 days after its field end: 30 candidates, the one with the lowest mean absolute error on the FIT days is used |
| Fewer than 3 polls in the window | no proxy for that day, counted as a miss |
| Offset or scaling | none is fitted |
| **Kill rule (as on the card)** | **KILLED if the proxy is within 0.3 points of the settled value on fewer than 80% of the check days** |
| Minimum | 20 check days, otherwise NOT_ENOUGH_DATA |

**Read once.** The check days are read one time. The marker is the result line added to this file in the same commit as the result.

**Honest limits, stated before the read.**

1. The poll table is the table as it stands on Nov 12, not as it stood on each day. A poll released late is in our window for a day on which the source could not have had it. This favours the proxy, so a KILL is solid and a SURVIVE is optimistic. If the proxy survives, the forward shadow uses the table as read each day, which removes this.
2. The sources that publish these averages choose which pollsters to include. Wikipedia's table is a wider list. No pollster filter is fitted here.
3. Thirty candidates are fitted on the fit days; the check days are untouched by that choice. This is a fit of a measuring tool, not a trade rule, and it adds no try to the deflation count; the trade test, if it is ever reached, is the card's one try.
4. Seen before this registration: ONE settled value (the Nov 11 event, from one politics recorder snapshot, while checking that the recorder carries the field). Nothing else of the settled history has been read.

**If the proxy survives.** ROLLOFF's forward shadow is registered as a read-time join on `pol-data` (one row a day: the proxy for tomorrow's value from that day's table, and the recorder's quotes), with its bar, in a separate registration before any forward row is scored. It stays on the main bar.

**If it is killed.** Card 13 is closed, and POL-b2's use of the same table as a level model is flagged to the Head of R&D.

**ROLLOFF proxy check: READ ONCE on Nov 12, 2026 (about 15:10Z). Verdict: PROXY KILLED. Card 13 is CLOSED.**

- **Step 0, the source.** The rules text names it: the "Approve" column of the "RCP Average" row of the table "President Trump Job Approval", at 1:00 PM ET on the day. The rules text does not say how that average is built, so the card did not die on the source alone and the scorer decided.
- **Inputs.** Settled values: the pull `ROLLOFF_PROXY` (7 answer files, complete), 71 daily events, 2026-09-02 to 2026-11-11, one settled value each. Poll table: "Opinion polling on the second Trump presidency", revision of 2026-11-10 22:29Z, read once through the Wikimedia REST API (the action API refused three requests with a rate-limit answer; none was retried in a loop). The parser `workers/rolloff/wiki_polls.py` read 168 polls and could not read 10 rows.
- **Result on the check days (2026-10-10 to 2026-11-11, 33 days): within 0.3 points on 0 of 33 (0%).** The bar was 80%. Mean error -2.29 points (our average is lower than the settled value), mean absolute error 2.29, worst 4.51. The best of the 30 candidate windows on the fit days had a mean absolute error of 6.13 there. On 18 check days where the settled value moved, the proxy moved the same way on 6.
- **One correction to the mechanical step, disclosed.** The first run used 64 of the 71 days: my extraction dropped 7 days whose value carries a percent sign (6 fit days, 1 check day). That run read 0 of 32 check days within 0.3. The figures above are the re-run with all 71. The verdict is the same either way.
- **Why it failed (description).** The Wikipedia table is not the source's poll list. It has no poll ending in August 2026, 12 in September, 32 in October and 5 in November, and its mix of pollsters runs 2 to 4 points lower than the settled average through mid October. A window average of it cannot stand in for the settled value, in level or in day to day direction.
- **What follows.** ROLLOFF needed our table to reproduce the settled value; it does not, so there is no forward shadow to register. Any other card that uses the Wikipedia poll table as a LEVEL model of this average (Refinement's POL-b2) has the same problem and is flagged to the Head of R&D. A rule that uses only Kalshi's own prices on these markets (Refinement's S1) is not affected.
- **Requests:** 0 Kalshi reads by this desk (the pull was run by Main through kalshi-pull, 7 answers). Wikimedia: 4 requests, 3 refused.

## ECONLAG amendment 2 (Nov 12, 2026, before any ECONLAG read): pinned cutoff, the slow-family screen, staged spend

Asked for by the Head of R&D. ECONLAG is the first card to be read against the slow-family paper screen (`docs/POLITICS_RULES.md` section 8). It will be **try number 1** against that screen. Protocol 2 and amendment 1 stand except where this changes them. No ECONLAG request has been made.

**1. The cutoff is a date constant.** The universe is every scheduled print (CPI, Employment Situation, PCE, FOMC statement) with a print time from **2024-10-01 00:00 UTC to 2026-10-31 23:59 UTC**. "The last third of print days" is withdrawn: it is not a constant. Nothing after 2026-10-31 is requested. Prints after that date are the only events a later read may add.

**2. What is claimed, and what is not.** The read is against the paper screen only: cash profit factor 1.3 or better on at least 30 independent events, both halves positive, read once. **No main-bar claim (profit factor 1.5 on development and held-out, deflated) will be made from this read**; the power analysis showed the card cannot reach that bar for years, and the development and held-out split of protocol 2 is withdrawn with it.

**3. One event, one trade.** The independent event is the print DAY (two prints on one day are one event). On each print day at most ONE trade counts: among the slow markets that qualify under rules 1 to 4 of protocol 2, the one with the largest part of the implied move still owed (ties go to S1, then S2, S3, S4). Its result is the net cash of 1 contract, entry at the ask of the T+10 minute candle, **exit arm A only: the bid of the candle ending T+4 hours**, fee on both legs, **+1c slip on both legs**. Arm B (T+24 hours), the other qualifying markets and the placebo are reported as description and are not tries.

**4. The screen, as it will be read.**

| Item | Value |
|---|---|
| Events counted | print days in the pinned range with a trade under item 3 |
| Fewer than 30 | label "no evidence at n = x", not scored further |
| 30 or more | profit factor = gross cash won on winning days / gross cash lost on losing days; listed "on the paper list (unproven)" only if it is 1.3 or better AND each half is net positive (halves split at the median print date); otherwise "off the list (failed the screen)" |
| Dropped trades (no bid in the 30 minutes before the exit) | counted; over 10% of trades makes the label "no evidence (data limited)" |
| Tries | 1, stated beside any listing with the running count in `workers/PAPER_LIST.md` |

**5. Two changes that only save reads (made now, before any read).**

- F and the slow markets are chosen from the **daily candle of the day before the print** (highest YES mid for F; nearest 50c for each slow market), not from the minute five minutes before it. That needs one daily read per market, which the beta calculation needs anyway, in place of a minute read of every market in every series on every print day.
- Slow markets are only read on print days where F's trigger fired.

**6. Staged spend and stop rules (at most 390 requests in all).**

| Stage | Job file (`workers/desk_b_jobs/`) | Requests | What it settles |
|---|---|---|---|
| 1 | `ECONLAG_CALENDAR.json` (complete, passes the pull script's own check) | 10 | the print calendar from Kalshi's own event close times (amendment 1), the count of print days, and that the series names `KXRATECUTCOUNT` and `KXFED` exist |
| 2 | part A of `ECONLAG_CANDLES.json` | at most 90 | daily candles of the Fed decision markets: which market is F on each print day |
| 3 | part B | at most 75 | one 1 minute read around each print for F: on how many print days the trigger (a move of 0.08 or more from T-5 to T+10) fired |
| 4 | part C | the rest | daily and 1 minute candles of the slow markets, on trigger days only |

- **Stop after stage 1** if the calendar holds fewer than 30 print days in the range: label "no evidence at n = x".
- **Stop after stage 3** if fewer than 30 print days show the trigger. A day without the trigger cannot have a trade, so the screen could not be reached; nothing more is asked and the label is "no evidence at n = x" with x the number of trigger days. Worst case spent by then: 175 requests.
- If stage 4 cannot cover four slow markets on every trigger day inside the cap, S4 is dropped first, then S3, for every day alike.
- `ECONLAG_CANDLES.json` is NOT RUNNABLE as committed: its tickers are not known before stage 1. Each part is built from the answers before it and reviewed before it runs.

**7. What I expect, said in advance.** The trigger asks the next-meeting Fed market to move 8c within fifteen minutes of a print. That is a large move. My guess is that it fires on fewer than 30 of about 70 print days, so the most likely outcome of this read is "no evidence at n = x" after stage 3. The stop rule is there so that answer costs at most 175 requests, not 390. Probability that the card is listed: 5%.

**8. Forward kill, if it is ever listed.** Paper trades after 2026-10-31 are logged with the same rule. The listing is removed if the forward paper net is below zero after 10 forward trades, or if 3 forward trades in a row are dropped for having no bid.

Sources: Kalshi's public market data only (the print calendar is taken from Kalshi's own event close times). No outside host.

**ECONLAG scripts committed before the calendar pull (Nov 12, about 16:10Z).** `workers/econlag/econlag.py` holds every stage: `calendar` (print calendar, count of print days, builds the part A job), `build-b` (chooses F for each print from the day-before daily candle, builds the part B job), `scan` (the trigger scan, a count that reads no outcome, with the stop rule) and `score` (the one read against the paper screen, with a read-once marker file). `workers/econlag/test_synthetic.py` runs the whole chain on made-up data: a world with late-following slow markets ends "on the paper list (unproven)", a world with no jumps is stopped by the scan, and a second `score` is refused.

**Two details fixed now, before any read:**

1. **Part B's cap is 100 requests, not 75.** Twenty-five months hold about 75 monthly releases plus about 17 Fed meetings, about 92 prints, one request each. "About 70 print days" in protocol 2 was low. Worst case spent by the end of the scan: 10 + 90 + 100 = 200 requests (it was stated as 175).
2. **The beta needs at least 20 paired daily changes** inside the 60 trading days before the print; with fewer, the slow market is skipped for that print. Protocol 2 named the 60 days and not a minimum.

**Not built yet, on purpose:** the part C job builder (slow markets on trigger days). It is only needed if the scan clears 30 trigger days, and the Head of R&D has ruled that nothing is pulled past the scan otherwise. `score` already takes any plan of slow markets, and was tested with one. **Not computed in the first read:** the placebo (the same rule a week earlier), which needs its own candles; it is asked for only if the card is listed.

## ECONFADE count, on ECONLAG's own pull (registered Nov 12, 2026, before any ECONLAG or ECONFADE read; zero tries)

Rank 1 of the re-open ranking (`workers/REOPEN_RANKING_NOV12.md`). The card is Refinement's (row 87 of its Nov 11 cards); the protocol is Desk A's (`IDEA_DESK_A_PROTOCOLS2.md`, Q3 on `claude/idea-desk-a`), which fixed every open detail and wrote a count step with a stop rule. Neither was run: the count needed about 70 requests and there was no read budget. ECONLAG's part B already asks for one-minute candles around the same prints, so the count is taken from the same pull.

`ECONFADE | family: overshoot fade after a scheduled print, entry at minute 20, hold or six hour exit | risk class: mid price (10c to 60c), 1 contract, about 24 events a year | stage Idea`

**What is done now: step 0 only, a count. No entry is priced, no outcome is read, no try is spent.** Constants are Desk A's, copied into `workers/econlag/econlag.py` (`fade-count`):

| Item | Value |
|---|---|
| Events | CPI and Employment Situation releases with a print time from 2024-10-01 to 2026-10-31 (ECONLAG's pinned range and calendar) |
| Market | of the next scheduled Fed meeting after the print, the one whose YES mid was nearest 50c at the previous day's daily close (Desk A's choice; ECONLAG's F is the highest mid, so the two can differ and both are asked for) |
| Reference | the last one-minute candle ending at or before the release second; its mid must be 10c to 90c |
| Shock | among candles ending 1 to 10 minutes after the release, the largest move of the mid from the reference in one direction is 15c or more |
| Retrace | at the candle ending 20 minutes after the release, the mid is 4c or more back from the extreme toward the reference |
| **Stop rule (Desk A's, unchanged)** | **fewer than 40 events with a confirmed retrace: NOT_ENOUGH_DATA, the card ends before any outcome is read** |

**Two differences from Desk A's text, stated:** the range starts at 2024-10-01 and not at "as far back as Kalshi serves candles, at most 2024-01", because it rides on ECONLAG's range (about 50 CPI and jobs prints, not about 70); and only the Fed decision series is used, not the rate-level series (`KXFED`), whose market list is not in ECONLAG's pull. Both can only lower the count. If the count is under 40 here it would also have had to find 40 minus the count in the fifteen earlier prints and the second series, which Desk A itself did not expect ("well under 40"). If it lands between 25 and 39 I will say so and the Head of R&D decides whether the wider count is worth about 40 more requests.

**Cost:** no extra pull. Part B's window on CPI and jobs prints becomes T minus 30 to T plus 25 minutes, and the nearest-50c market is asked for when it is not F: at most about 50 extra requests in part B, whose cap moves from 100 to 150. Worst case spent by the end of the scan: 10 + 90 + 150 = 250.

**If the count clears 40:** nothing is scored by this desk without a new word from the Head of R&D; step 2 is Desk A's protocol (two tries, development and held-out by release date).

## ECONLAG amendment 3 (Nov 12, before any read): the print time is the scheduled minute, checked against the market's close

Amendment 1 took the print time T as the close time of the Kalshi event that resolves on the print. A market can close a few minutes BEFORE its release, and a T that is five minutes early would move both scans. So T is now the scheduled release minute in US Eastern time on the day the market closed (8:30 for CPI, the Employment Situation and PCE; 2:00 PM for the Fed statement), and an event whose market closed more than one hour from that minute is dropped and counted, not guessed. This also drops a release that was moved to another time of day. The cross-check against V2's 2026 calendar file is replaced by this rule, which needs no outside file.
