# Idea Desk B (events and information), Nov 11, 2026: 16 pre-registered Idea cards

Stage of every card: **Idea**. Nothing here was scored. No Kalshi API call was made by this desk (0 requests). No order, no spend, no account, no key. Each card needs its own protocol committed before any outcome is read, the Verification Analyst's score on the four uniqueness checks, and the owner's approval before it can count as "on the shadow list" (`docs/RND_CHARTER.md` section 3).

## What was read first, so nothing is repeated

`docs/RND_CHARTER.md`, `docs/STRATEGY_LIFECYCLE.md` (7c to 7g, the declined list), `docs/POLITICS_RULES.md` (main, and the 30 day version on `claude/politics-30day`), Refinement's `refine_tools/POLITICS_CARDS_NOV11.md`, `POLITICS_CENSUS.md`, `ELECTIONS_CENSUS.md`, `CARDS_NOV11_ROWS_74_93.md`, `CARDS_74_84_REGISTRATION_AND_RESULT.md`, `IDEA_BACKLOG.md` rows 1 to 73, `FIVE_MECHANISMS_NOV11.md`, `LITERATURE_NOTE_NOV11.md`; V2's `workers/IDEA_CARDS_NOV11B.md`, `IDEA_CARDS_NOV11C.md`, `POLITICS_CARDS_V2.md`, `POLITICS_CARDS_V2B.md`, `POLITICS_H_J_RESULT.md`, `POLCOMBO1_CARD.md`, `COMBOPRICE1_DESIGN.md`, `COMBO1_CENSUS.md`, `CLINICAL1_CARDS.md`, `CLINICAL1_TERMS.md`, `BASERATES1_TABLES.md`, `LITSCAN_NOV11.md`, `DOCS_CARDS_RESULT.md`, and the result headers of about 30 V2 tests (COUNT1, COUNT2, GOVCOUNT1, TSA1, NOWCAST1, FEDIMPL1, BARRIER1, EARNPR1, CPIMENT, PHYSCOUNT1, RAINFACT1, CALIB1, USWEEP1 to 3, ECONNEW1 and 2, ECONREL1, WXDEAD1, WXNEW1, WXOTHER1, NEWLIST1, MVE1, PARLAY1, TNOTE1, SOFR1).

**Already tested or carded, so NOT repeated here:** executive order and bill counts from base rates (EXECSUM failed held-out; COUNT1, GOVCOUNT1); mention base rates, persistence and mention combos (MENT1 falsified, card 84 failed PF 0.62 and 0.38, mention combos lose 29c to 37c per dollar); approval and generic ballot calibration (cheap side PF under 1) and poll slope (POL-b1, b2, b3); scheduled votes and deadlines (POL-c1, c2); nothing-happens on dramatic personal events (POL-k1, n 7); news fade, overnight staleness, Wikipedia pageviews, GDELT (POL-i1, i2, n1, n2); exhaustive-set and date-ladder locks (POLPARITY1, ARB2 to ARB5, 0 of 7,628 politics rows); weather forecast prior, ensemble prior (PF 0.76), day-end rounding (0 of 20 priced), dead brackets, rain; CPI gas from EIA, mortgage, Treasury cash, debt, nowcasts, Fed implied, jobless claims, TSA, SOFR, 10 year note; clinical PDUFA, advisory committee, phase base rate, trial status, health counts; quakes, space weather, El Nino; combo price against the PRODUCT of legs (PARLAY1, MVE1); new listings, early close, round cents, category calibration.

Keyword check of the V2 README (1.77 MB) and both workers folders for each card below (TFR, NOTAM, opinion authorship, margin of victory parity, ballot measure, Monthly Treasury Statement, enrolled or presented bills, poll roll-off, infobox edits, unrounded unemployment rate, CPI base effect, weather combo correlation, nested combo legs): **zero prior tests found** for every card; the nearest neighbours are named in each card.

## Common rules for every card

- **Bar:** cash PF 1.5 or better on development AND on the held-out final third (read once), n as stated per card, event-clustered, fee 0.07 x p x (1 - p) per contract unrounded and also rounded up at 3 contracts, slip +0c and +1c. A pass is only "candidate for the shadow list". The live proof bar stays PF 1.3 over 100 fills in 2 of 3 windows.
- **Kill:** PF under 1.0 on development after fees is FALSIFIED; fewer treated events than the stated minimum is NOT_ENOUGH_DATA.
- **Deflation:** each card states how many tries (arms) it adds. This desk adds **N +27** in total if every card ran (it will not; at most 2 tests run at once and one per family).
- **Hold caps (owner, Nov 11):** politics and elections 30 days (at most 5 open beyond 14 days), economics and weather 14 days, clinical 90 days, mixed combos held to settlement by the owner's stated exception. Probe sizes: 3 contracts politics single, 1 contract nothing-happens, $2 per parlay, $40 parlay stop, $200 lifetime for the whole politics and parlay program.
- **Uniqueness (lifecycle 7d), stated per card:** U1 signal, U2 exit, U3 correlation with live strategies (NOT YET MEASURED everywhere; expected near 0 because none of these trades a 15 minute market), U4 declined list. This desk does not score its own cards; the Verification Analyst does.
- **Probability** = this desk's honest chance the card reaches a paper pass at the bar. All are low. Most ideas die at the first count, as the last 100 did.

## Source terms status (hosts these cards would read)

| Host | Status | Note |
|---|---|---|
| Kalshi public API | PERMITTED, but this desk has 0 budget | each card states the requests it needs from the shared 12 a minute |
| GovInfo bulk data (BILLSTATUS, Federal Register, Congressional Record) | PERMITTED (already used by BASERATES1) | bulk XML, no key |
| BLS public API (api.bls.gov) | PERMITTED (on the desk's permitted list) | v1 needs no key; 25 queries a day keyless |
| NWS API (api.weather.gov) | PERMITTED | already recorded by `record-wxens.yml` |
| Wikipedia and Wikimedia APIs | PERMITTED | the Wikimedia User-Agent policy asks for a contact in the agent string; the repo rule is "no personal details", so the contact is an owner choice (flagged by Refinement too) |
| Treasury Fiscal Data API (api.fiscaldata.treasury.gov) | PERMITTED per Refinement's row 79 read (Daily Treasury Statement); NOT re-read by this desk | no key |
| FAA (tfr.faa.gov list of temporary flight restrictions) | **UNREAD, so BARRED for now.** This desk's one read of the FAA web policies page on Nov 11 was refused (HTTP 403 to an automated reader, no text returned); it was not retried and tfr.faa.gov itself was never fetched | NEW host. A person must read the policy page in a browser and record the verdict; a 403 to an automated client is itself a caution. Only then the signal logger allowlist edit (a code edit and the owner) |
| supremecourt.gov | AMBIGUOUS (V2: policy page errored) | NOT used; card 6 uses Wikipedia instead |
| RCP, Silver Bulletin, VoteHub, X, Reddit, Polymarket, Yahoo, ESPN and the other gated hosts | BARRED | never read; where a market settles on one of them, the number is seen only through Kalshi's own settled result |

---

## The cards

### 1. NESTCOMBO (combo): a combo whose legs are logically nested is worth its strongest leg, not the product

**STATUS (Nov 12): CLOSED, untestable from public data (Chief of Staff's call, on V2's COMBO1 finding).** Combos carry no posted asks: in all 34 sampled combos with candles the ask closes at 1.00 and the bid at 0.00, because combos are quoted on request. So "combo plus NO on the strongest leg for under $1" cannot be priced from the public book whatever the nested count is. This desk's own structure count stopped at its second request (a 429) and found no nested or contradictory legs in the 38 combos V2 had committed. Reopen only if a recorder of the live combo book shows real asks, which is the owner's decision and is not proposed.

`NESTCOMBO | family: structural dominance, combo leg plus the single's NO bought together, held to settlement (paired within its own position) | risk class: no outcome risk if the nesting is real; loss shape = a leg not filled or a rule read wrong; about $1 per set | stage Idea`

- **Mechanism (one line):** when every leg of a listed combo is implied by one leg (team wins the title implies it wins the conference; covers -5.5 implies wins; over 220.5 implies over 215.5; high above 60 implies high above 55), the combo pays exactly when that one leg pays, so combo ask must not sit below that single's bid; when it does, buy the combo and buy NO on the single for under $1 in total.
- **Leg-correlation assumption, stated in advance:** correlation is 1 by logic, not by estimate. Joint probability = the minimum leg (the Frechet upper bound in `COMBOPRICE1_DESIGN.md`). No statistical input at all. The only risk is rule reading: the nesting must hold under both contracts' rules text (overtime, void, postponement and tie clauses read for every pair type before it is admitted).
- **Second arm (contradictory legs):** a combo whose legs cannot all happen (two teams both winning the same title) is worth 0; if its NO is offered under 97c that is $1 for under $1. Registered separately; it is a capital lock-up question, not an edge claim, and it is quoted per dollar-year.
- **Who is on the other side and why they lose:** the combo quote comes from a pricing engine or a resting order that applies a capped correlation between legs. PARLAY1 and MVE1 measured combos only against the PRODUCT of the legs (median print over product 1.12, so combos are priced a little above independence). For nested legs the fair price is far above the product, so "a little above the product" would be very cheap. Sportsbooks block nested same-game legs for this reason; it is unknown whether Kalshi's builder does.
- **Closest existing:** PARLAY1, MVE1 (price against the product), POLPARITY1 and ARB2 to ARB5 (locks inside one event). Differs: a lock between a combo and a single, on the upper Frechet bound, never scanned.
- **U1** different market type (combo) and different field (leg structure). **U2** paired within its own position, hold. **U3** not measured, expected 0. **U4** not on the list; not a favourite hold (the pair pays $1 in every state).
- **Data and terms:** Kalshi public API only (combo market objects carry `mve_selected_legs` and the combo's bid and ask; the legs' single markets). Owner rule for sports combos is met: price consistency only, against Kalshi's own singles, no outside sports data.
- **Cheapest test:** a census, no outcome needed. **Corrected the same day:** there is no offline step. The combo files V2 holds are rule ids from the 15 minute pair scans, not combo leg lists, and `POLCOMBO1_CENSUS.json` has only leg-prefix counts. Step 1 (about 25 requests): list open combos and count those whose legs are nested by ticker rule (same team or player stem, ordered strikes; same city ordered temperature strikes). Step 2: for the nested ones, read the strongest leg's quote. **Second correction:** PARLAY1 found only 30 of 254 open combos with a real resting ask; most combos are quoted on request, and asking for a quote is an account action research may not take. So the public test sees only resting asks and past prints. Full protocol: `workers/IDEA_DESK_B_PROTOCOLS.md`. **Sample:** every nested combo found; the bar is a COUNT: at least 20 combo-timestamps with combo ask + single NO ask + both fees under $0.99 and displayed size of 5 or more on both. Under 20 in 14 days = CLOSED.
- **Time to settlement:** same day (NBA, weather) to Nov 2027 (futures legs; the owner's mixed-combo exception applies and the spec must say the money is held). **Time to verdict:** the structure count in an hour of budget (about 25 requests); the 7 day lock count about 210 to 630 requests.
- **Tries:** N +2. **Probability:** 4% that 20 real resting locks exist (lowered from 6% after the corrections); 12% that at least one does.

### 2. ECONLAG: after a scheduled print, the slow macro markets lag the fast one

`ECONLAG | family: related-market lag, entry on the lagging market, TIME EXIT (4 hours) | risk class: mid price 10c to 80c, about even win and loss size, $2.40 per order at 3 contracts, group E (macro release days, about 3 a month) | stage Idea`

- **Mechanism:** on CPI, payrolls, PCE and FOMC statement days, the next-meeting Fed decision market reprices within a minute or two; the markets that depend on the same news but trade thinly (number of rate cuts this year, later meetings, the year-end rate level) can sit on stale resting orders for longer. Buy the side of the slow market that the fast market's move implies, exit on the clock.
- **Entry (frozen before any read):** print time T from the BLS, BEA and Fed calendars. If the next-meeting KXFEDDECISION favourite bracket's mid moved 8c or more between T-5 and T+10 minutes, then at T+10 for each linked market (the fixed list: KXRATECUTCOUNT, the next two later KXFEDDECISION meetings, KXFED year-end) compute the implied move = beta x fast move, beta from a regression of DAILY changes on non-print days in the prior 90 days (no look-ahead). If the slow market has moved less than 25% of its implied move and the side to buy costs 10c to 80c with a spread of 3c or less, buy 3 contracts. One order per linked market per print.
- **Exit:** sell at the bid at T+4 hours (arm A) or T+24 hours (arm B). Never held past a day. This is the first card on the list with a pure time exit, which lifecycle 7d item 7 names as a gap.
- **Who loses:** owners of resting orders in long-dated macro books who are not watching the print; makers who refresh the front meeting first.
- **Closest existing:** ECONFADE row 87 (a fade inside the SAME market), EVENT830 (15 minute longshot before the print), EVM1 to EVM4 (perp against ladder, minute lag FALSIFIED), INGAMELAG1 (sports, forward). Differs: macro, a cross-series lag after a scheduled public number, time exit. The Fed paper finding that Kalshi macro prices are accurate (LITERATURE_NOTE item 5) is about levels at the close, not about the minutes after a print in the thin books.
- **U1** different market type and a different field (another series' move). **U2** time exit. **U3** not measured (EVENT830 trades the same mornings but different markets and it is at 1 contract; report the overlap share). **U4** not on the list.
- **Data and terms:** Kalshi 1 minute candles from the public history endpoints; the release calendar (V2's `studies/EVENT_CALENDAR_2026.csv` plus BLS and Fed calendars, permitted). No outside price.
- **Cheapest test and sample:** about 70 print days since late 2024 x up to 4 linked markets, expected 60 to 140 qualifying entries; **minimum 40 per half**. About 350 candle requests (one per market per print day), a day and a half at 4 a minute.
- **Kill:** PF under 1.0 on either arm, or median spread at entry above 3c, or fewer than 40 entries per half (then forward log on the 3 prints a month).
- **Time to settlement:** 4 or 24 hours. **Time to verdict:** 3 days after a budget is given. **Tries:** N +2. **Probability:** 8%.

### 3. BALLOTNO: ballot measures and the status-quo vote

`BALLOTNO | family: calibration by measure type, entry 14 days out, hold to settlement | risk class: arm N high win rate with a large loss (inside the owner's nothing-happens rule), arm Y mid price; 1 contract arm N, 3 contracts arm Y; group D (politics) | stage Idea`

- **Mechanism:** voters who are unsure vote no on ballot questions, so support in polls falls by election day; citizen initiatives pass much less often than measures a legislature refers. If Kalshi prices follow the polls and the headlines, the YES of an initiative is too dear and the YES of a referred measure can be too cheap.
- **Entry (frozen):** at the daily candle 14 days before the election. Type of each measure (citizen initiative, legislatively referred, bond or tax, constitutional or statutory) tagged from Wikipedia's ballot measure lists BEFORE any price is read. **Arm N:** an initiative whose YES is 12c to 40c: buy NO at 60c to 88c, 1 contract, at most $5 at risk, one market per measure (exactly the owner's nothing-happens limits, POLITICS_RULES section 5). **Arm Y:** a legislatively referred measure whose YES ask is 30c to 75c: buy YES, 3 contracts. Hold to settlement.
- **FLAG, quoted so nobody is surprised:** arm N buys a 60c to 88c favourite and holds. The Charter bans favourite-and-hold for new live strategies; the owner's Nov 11 rule allows "nothing happens" as a politics family ("distinct from the declined favourite-late gold hold (different market, different data). Paper first."). Arm N stays paper until the owner's own popup; this card does not ask for an exception beyond that rule.
- **Who loses:** bettors pricing a measure from its poll lead or from how loudly it is covered.
- **Closest existing:** POL-k1 (nothing-happens on resignations and firings, n 7, PF 0.09 pooled on 4). Differs: a different market type with a known, repeated base rate, and outcomes in different states are close to independent, which the election census says winner markets on one night are not.
- **U1** different market type plus an outside fact (measure type). **U2** hold, with different entry rules, no interference. **U3** not measured. **U4** favourite-and-hold row: covered only by the nothing-happens rule quoted above.
- **Data and terms:** Kalshi history (KXSTATEBALLOTMEASURE, 124 settled markets per the elections census; other measure series to be listed from the public series list); Wikipedia API for type and result (PERMITTED).
- **Cheapest test and sample:** about 124 daily-candle requests plus one Wikipedia read per election date. Expected 25 to 50 entries per arm; **minimum 30 per arm with at least 3 election dates in each half**, clustered by state-date.
- **Honest limit:** the next large ballot dates are few until November 2027 and 2028, so a pass on paper would be followed by a slow forward test. **Time to settlement:** 14 days. **Time to verdict:** 2 to 3 days. **Tries:** N +2. **Probability:** 7%.

### 4. UNRATEROUND: the unrounded unemployment rate

`UNRATEROUND | family: official arithmetic prior, entry 3 days before the release, hold to settlement | risk class: mid price, 3 contracts, one event a month, group E | stage Idea`

- **Mechanism:** the headline rate is rounded to one decimal, but BLS publishes the unemployed and labour force levels, so last month's unrounded rate is known (4.349 and 4.251 both print as 4.3). The chance that next month's HEADLINE moves a tenth depends on which edge of the bracket the unrounded rate sits at. A bettor who anchors on "4.3 last month" misses that.
- **Entry (frozen):** u0 = unemployed / labour force from the last release (BLS series LNS13000000 and LNS11000000). Model: next unrounded rate = u0 + 0 drift + normal error, sd from monthly changes 2010 to 2019 and 2022 to 2025, frozen. Three days before the Employment Situation release, buy the threshold or bracket side whose ask is 8c or more under the model, price 10c to 80c, 3 contracts, one per event. January releases are excluded (annual population controls break the series).
- **Who loses:** bettors who price from the rounded headline and the rounded consensus.
- **Closest existing:** row 43 (bracket within one consensus sigma), ECONREL1 (not runnable, a structural reference), NOWCAST1, FEDIMPL1. Differs: no forecast and no consensus, only the rounding position of an already published official number.
- **Honest counter:** street economists print the unrounded rate in every preview, and the Fed paper found Kalshi's unemployment market about as accurate as consensus. The edge, if any, is in which side of the consensus the rounding risk lies.
- **U1** outside official data, different market type. **U2** hold with different entry rules. **U3** not measured. **U4** not on the list.
- **Data and terms:** BLS API (PERMITTED); Kalshi history for the unemployment series (about 40 requests).
- **Cheapest test and sample:** about 30 to 36 monthly events, expected 15 to 25 entries: under any PF bar. So the registered first read is DESCRIPTIVE: Brier score of the model against the Kalshi mid three days out, and the mean result of the 8c rule with its interval. **Minimum for a PF claim: 40 entries**, which needs about 2 more years, so the honest label is NOT_ENOUGH_DATA with a forward log (one BLS read and one Kalshi quote a month).
- **Time to settlement:** 3 days. **Time to verdict:** 2 days for the descriptive read; a bar-level verdict is not reachable before 2028. **Tries:** N +1. **Probability:** 7% that the descriptive read beats the market's Brier; 3% that it ever clears the bar.

### 5. FAANOTICE: FAA flight restrictions as the official early notice of presidential travel and of launches

`FAANOTICE | family: official precursor notice, entry on the cheap or mid side when the notice publishes, hold to settlement (1 to 5 days) | risk class: mid price, 3 contracts, a few events a month, group D | stage Idea`

- **Mechanism:** the FAA publishes a "VIP Movement" temporary flight restriction, with place and times, one to five days before the President travels, and a "Space Operations" restriction before a launch attempt. A Kalshi market on whether he attends an event, visits a place, or whether a rocket launches by a date can still be priced on rumour when the notice is already public.
- **Entry (frozen):** for each open market on a fixed list (attendance and visit markets: KXTRUMPUFC, KXTRUMPATTEND, KXWHVISIT, KXATTENDSOTU style; launch-by-date markets if listed; the list is fixed from the public series list before any price), when a restriction is published whose area covers the venue and whose time window covers the event, buy YES if its ask is 10c to 70c, 3 contracts, one per market. Control arm, scored only: no restriction published 24 hours before the event start (that is a NO at a high price, a nothing-happens shape, never traded from this card).
- **Who loses:** bettors pricing attendance from news and social chatter. Honest counter: flight-restriction watchers post these notices publicly within hours, so a sharp trader may already use them; the test is whether the Kalshi YES is still under 70c an hour after publication.
- **Closest existing:** rows 72 and 73 (a determined fact or a live reference number against a stale bracket), POL-n1 and n2 (attention spikes). Differs: an official notice issued BEFORE the event by a third agency, not a count and not attention.
- **U1** new outside source. **U2** hold with different entry rules. **U3** not measured. **U4** not on the list (YES at 10c to 70c is not a favourite hold).
- **Data and terms:** FAA TFR list. **Terms: UNREAD, so the source is BARRED for now.** The one policy page read this desk tried on Nov 11 was refused (HTTP 403, no text); it was not retried and the TFR site was never fetched. Nothing is read from the FAA until a person reads the policy page in a browser and the verdict is PERMITTED. After that, recording still needs a signal-logger registry entry AND an allowlist edit (code review and the owner). No public archive of expired restrictions is known to this desk (UNVERIFIED), so the test is forward only. **This card is blocked at step 0 until the terms are read.**
- **Cheapest test and sample:** an EXISTENCE check first: for the next 5 settled attendance or visit events, log the publication time of the covering restriction and the Kalshi YES ask at that time and one hour later (the politics recorder already quotes KXWHVISIT every 30 minutes). Dead if the ask is above 85c within the hour in 4 of 5. A PF claim needs **40 entries**, at an estimated 2 to 4 events a month: about a year.
- **Time to settlement:** 1 to 5 days. **Time to verdict:** 3 to 4 weeks for existence; about 12 months for a bar-level read. **Tries:** N +1. **Probability:** 35% that a priced window exists at all; 5% that it reaches a paper pass.

### 6. SCOTUSAUTH: who is left to write the opinion

`SCOTUSAUTH | family: official process arithmetic, entry in the last 30 days of the term, hold to settlement | risk class: mid price, 3 contracts, about 10 events a year in one month, group D | stage Idea`

- **Mechanism:** the Court spreads majority opinions almost evenly across the nine justices within each argument sitting. Late in the term, the justices who have not yet written for a sitting are the likely authors of that sitting's undecided cases, and the author is strong evidence of the direction of the ruling. Court watchers do this arithmetic by hand every June; a casual bettor does not.
- **Entry (frozen):** from June 1, on each opinion day, for each Kalshi case-outcome market still open: the candidate author set = justices with no majority opinion yet from that case's sitting. Model probability of the outcome = the frozen table P(outcome side | author bloc) built from the five terms before the test window (Wikipedia term tables only). Buy the side whose ask is 10c or more under the model, price 10c to 90c, 3 contracts, one per case. Decisions arrive by about July 1, so the hold is inside 30 days.
- **Who loses:** bettors anchored on the oral argument headlines from months earlier.
- **Closest existing:** COURTTIME (V2: the DATE of a ruling against the calendar; not enough data). Differs: the outcome, from the assignment pattern.
- **U1** new outside information. **U2** hold with different entry rules. **U3** not measured. **U4** not on the list.
- **Data and terms:** Wikipedia term opinion tables through the MediaWiki API (PERMITTED). supremecourt.gov is AMBIGUOUS and is not read. A second arm (which side was asked more questions at argument) needs the official transcripts and stays BLOCKED until that host's terms are read.
- **Cheapest test and sample:** the two terms with Kalshi case markets: count cases with a market still open on June 1 and a two-sided quote. Expected 8 to 15 a term, so 15 to 30 in total: **under the 40 minimum; NOT_ENOUGH_DATA is the expected first verdict.** The value is a prepared forward log for June 2027.
- **Time to settlement:** up to 30 days. **Time to verdict:** 2 days for the count; a real read in July 2027. **Tries:** N +1 (the question-count arm would add 1). **Probability:** 5%.

### 7. WXCOMBO-XCITY (combo): neighbouring cities miss the forecast together

`WXCOMBO-XCITY | family: combo priced against a stated correlation, buy the same-direction combo, hold to settlement (same day) | risk class: low to mid win rate, loss = the combo price, $2 per parlay, $40 total stop; group W (weather) | stage Idea`

- **Mechanism:** when the day's forecast high is too low in New York it is usually too low in Philadelphia too, because one air mass and one model error cover both. A combo of "warmer than the threshold" legs in neighbouring cities (or all "cooler than") therefore wins together more often than the product of the legs says.
- **Leg-correlation assumption, stated in advance:** what matters is the correlation of the forecast ERRORS, not of the temperatures. Assumed error correlation for station pairs under 400 km apart: **0.45 (range 0.30 to 0.60)**; 400 to 1,500 km: 0.20 (0.05 to 0.35); beyond: 0.05. For two legs near 50c that is a joint of about 0.32 against a product of 0.25. Mixed-direction combos (one warmer, one cooler) are worth LESS than the product and are never bought. The assumption is replaced by a measured value, frozen, before any combo is scored (see the test).
- **Entry (frozen after the measurement):** at the 10:00 local look, for listed KXCITIESWEATHER combos of 2 or 3 same-direction legs in cities under 400 km apart, each leg's single mid between 20c and 80c: fair = one-factor copula joint at the measured correlation's LOWER 90% bound (`combo_price.py` has the function). Buy when (fair - ask - fee) / (ask + fee) is 10c per dollar or more (the owner's paper-edge bar), $2 a combo, one per city pair per day.
- **Who loses:** a combo pricer that treats cities as independent or applies one generic correlation. PARLAY1 and MVE1 found combos priced near the product on average.
- **Closest existing:** WXPRIOR and WXENS1 (single brackets against a forecast, FAIL direction, PF 0.76), MVE1 (cheap combos against the product, n 11). Differs: it takes NO view on any leg's probability (the legs' own Kalshi prices are the marginals); the only claim is the dependence between legs. The owner's combo rule asks for "same city, linked days or brackets first"; this is cross-city, so it is the second in line behind card 8 unless the census shows only cross-city collections exist.
- **U1** combo market, dependence as the signal. **U2** hold, different entry rules. **U3** not measured. **U4** not on the list.
- **Data and terms:** our own `quote-data` branch `wxens/` (NWS forecast high and observed high for 14 cities since Nov 3; PERMITTED NWS data already recorded) for the correlation; Kalshi combo and leg quotes for the price.
- **Cheapest test and sample:** Part A, zero Kalshi calls: measure the error correlation by pair from the recorder. **First partial read, Nov 11: NOT_ENOUGH_DATA** (15 near pair-days on 5 days, pooled 0.34, not distinguishable from zero or from 0.45; the recorder gives about 2 near pair-days a day on only 5 near pairs, so 150 pair-days arrive in late January, not Dec 3; table in `workers/IDEA_DESK_B_PROTOCOLS.md`). Part B: a census of what the 35 KXCITIESWEATHER collections allow and 10 days of combo quotes (about 60 requests a day at 2 looks). **Minimum 60 combo-days per half, clustered by day.**
- **Kill:** measured near-pair error correlation under 0.15, or the median combo ask already at or above the copula fair value, or PF under 1.0.
- **Time to settlement:** same day. **Time to verdict:** Part A in late January at the recorder's present yield; Part B about 30 trading days after the census. **Tries:** N +2 (2 leg and 3 leg). **Probability:** 5%.

### 8. WXCOMBO-PERSIST (combo): the same city on linked days

`WXCOMBO-PERSIST | family: combo priced against a stated correlation, same city on consecutive days, hold to settlement (2 days) | risk class: as card 7 | stage Idea`

- **Mechanism:** a forecast that runs too cool today tends to run too cool tomorrow under the same weather pattern. A two-day combo of same-direction legs in one city wins together more often than the product.
- **Leg-correlation assumption, stated in advance:** lag-one correlation of the day-ahead forecast error at one station: **0.25 (range 0.10 to 0.40)**. Weaker than card 7's, so the expected edge is smaller: two 50c legs give a joint of about 0.29 against 0.25.
- **Entry, who loses, data:** as card 7 with "consecutive days" for "neighbouring cities". This is the owner's stated first priority for weather combos ("same city, linked days or brackets first").
- **Blocker, stated plainly:** it is UNVERIFIED that Kalshi lists a combo across two different days of one city; the collections are called "cities weather". If none exists this card is simulation only and gives the correlation number for a future spec.
- **Cheapest test:** the same Part A measurement as card 7 (zero Kalshi calls; the lag-one error correlation per city from the recorder), then the census. **Minimum 60 combo-days per half.**
- **Time to verdict:** late January for the measurement (same recorder yield as card 7). **Tries:** N +1. **Probability:** 3% (smaller correlation, and the product may not exist).

### 9. MOVPARITY: the winner market against the margin ladder of the same race

`MOVPARITY | family: cross-series parity, arm A a paired lock held to settlement, arm B a lag entry with a 30 minute time exit | risk class: arm A no outcome risk if the ladder is exhaustive; arm B mid price; 3 contracts | stage Idea`

- **Mechanism:** "A wins" is the same event as "the margin lands in one of A's brackets". So the winner price for A must equal the sum of A's margin brackets. **Arm A:** when A-wins YES plus every B-side margin bracket YES costs under $1 after fees, buy them all; exactly one pays. **Arm B:** on election night, when the winner market moves 10c or more in 5 minutes and the ladder's implied win chance trails by 6c or more two minutes later, buy the trailing side's nearest bracket and exit after 30 minutes.
- **Who loses:** makers quoting hundreds of races at once on one night; the ladder is the thinner book.
- **Closest existing:** POLPARITY1 (exhaustive sets inside ONE event: 0 of 7,628 live rows, one unconfirmed historical lead), XSER1 (15 minute crypto against the hourly ladder), INGAMELAG1. Differs: two different series on one race, and the timing is the count itself.
- **U1** different market type and field. **U2** paired within its own position (arm A), time exit (arm B). **U3** not measured. **U4** not on the list.
- **Data and terms:** Kalshi history only: KXMIDTERMMOV (729 settled markets, 10 dates), KXPRIMARYMOV (636, 32 dates), KXGENERALMOV, with the matching winner series. The rules text of each ladder must be read first to confirm the brackets are exhaustive (ties, recount clauses).
- **Cheapest test and sample:** a sample of 100 races (the two highest-volume per date), 1 minute candles for the night: about 800 requests, two days of a 4 a minute share. **Arm A bar is a count: 20 lock-timestamps with size; arm B needs 40 entries per half, clustered by NIGHT** (and the nights are few: this is the honest weak point).
- **Time to settlement:** hours to days. **Time to verdict:** 3 to 5 days. **Tries:** N +2. **Probability:** 4% (every lock scan so far found nothing).

### 10. PRESENTQ: the bills already on the President's desk

`PRESENTQ | family: official pipeline queue, entry with 3 to 10 days left in the period, hold to settlement | risk class: mid price, 3 contracts, 1 to 2 events a month, group D | stage Idea`

- **Mechanism:** a bill presented to the President becomes law within ten days, Sundays excepted, unless vetoed. The presented-but-unsigned bills and their dates are in the official bill status data. So the number of laws in the rest of the month is partly already fixed, which a base rate cannot see.
- **Entry (frozen):** with 3 to 10 days left, model count = laws so far + presented bills whose ten-day clock ends inside the period (counted as certain, less the frozen veto rate) + presented bills whose clock ends after it (weighted by the frozen signing-delay distribution of the 115th to 119th Congresses) + a small base-rate term for bills not yet presented. Buy the KXBILLSCOUNT or KXBILLSSIGNED bracket whose ask is 10c or more under the model, price 10c to 80c, 3 contracts, one per period.
- **Who loses:** bettors using pace and headlines.
- **Closest existing:** EXECSUM (base rates; FAILED held-out), BASERATES1 tables A3 and A4 (count so far), GOVCOUNT1. Differs: a deterministic forward queue, a different field of the same official source. **Family note:** this is the activity-count family, which already has one falsified test; a second failure here would leave one try before the family is declined for good.
- **Known problems:** Kalshi's own count differed from public laws in 2 of 10 months (BASERATES1 A5); the update lag of the bulk status files is unverified.
- **U1** a different field with different logic. **U2** hold, different entry rules. **U3** not measured. **U4** not on the list.
- **Data and terms:** GovInfo BILLSTATUS bulk XML (PERMITTED), `workers/baserates1/plaw_list.csv` (held).
- **Cheapest test and sample:** offline, zero Kalshi calls: replay 21 months of the 119th Congress and score how often the queue model, 7 days before month end, names the final count bracket against the base-rate model. Only if it wins clearly: about 25 Kalshi history requests for prices. **A PF claim needs 40 periods; about 11 settled months exist. NOT_ENOUGH_DATA is the expected trade verdict.**
- **Time to settlement:** 3 to 10 days. **Time to verdict:** 1 day for model accuracy; over a year for a bar-level read. **Tries:** N +1. **Probability:** 8% that the model beats the base rate by a useful margin; 3% bar.

### 11. TARIFFDTS: the daily Treasury statement adds up to the monthly one

`TARIFFDTS | family: official components nowcast (a sum identity), entry on the first business day of the month, hold to the monthly statement (about 8 business days) | risk class: mid price, 3 contracts, one event a month, group E | stage Idea`

- **Mechanism:** the Monthly Treasury Statement's customs duties, receipts and deficit are close to the sum of the month's Daily Treasury Statement lines, which are complete about a week before the monthly figure is published.
- **Existence is UNVERIFIED:** this desk made no Kalshi call and no held file names a tariff revenue, receipts or monthly deficit series. Step 0 is one read of the public Economics series list.
- **Entry (frozen):** model = a + b x (sum of the daily "customs and certain excise taxes" deposits), fitted on the 36 months before the test window; error sd from the fit. On the first business day after month end buy the bracket whose ask is 10c or more under the model, 10c to 80c, 3 contracts.
- **Who loses:** bettors extrapolating last month's headline.
- **Closest existing:** row 79 (the Treasury cash BALANCE projected from the same statement), row 77 (CPI gasoline from EIA). **Honest family note:** this is the "official components" economics family the owner approved; it queues with row 77 under the one-test-per-family limit and shares its deflation count. It is new only in the market and the identity.
- **Data and terms:** Treasury Fiscal Data API (PERMITTED per Refinement's row 79; not re-read here).
- **Cheapest test and sample:** one day: 10 years of daily and monthly statements, out-of-sample error of the sum model. Trade read: monthly, so **NOT_ENOUGH_DATA for at least a year.**
- **Time to settlement:** about 10 days. **Tries:** N +1. **Probability:** 50% that a listed market with volume exists; 4% bar overall.

### 12. CPIARITH: two CPI ladders that must agree

`CPIARITH | family: cross-ladder official arithmetic, cheap leg of the thinner ladder (or both legs, closed together at settlement), hold | risk class: mid price, 3 contracts, one event a month, group E | stage Idea`

- **Mechanism:** the year-on-year CPI rate is fixed by this month's index and the index twelve months ago, which is known. So each year-on-year bracket is a precise interval of the month-on-month change, given BLS's published seasonal factors. The month-on-month ladder and the year-on-year ladder therefore imply each other; where they disagree by more than fees, the thinner one is wrong.
- **Entry (frozen):** the day before the release, map the month-on-month ladder's mids to a distribution (linear inside brackets), transform it to the year-on-year brackets with the index arithmetic and the rounding rule (index to 3 decimals, rates to 1), and buy a year-on-year bracket whose ask is 8c or more under the transformed value, 10c to 80c, 3 contracts, at most 2 per event.
- **Who loses:** bettors pricing the year-on-year number from the news.
- **Closest existing:** CPI1 (a nowcast, FALSIFIED), rows 43, 69, 81. Differs: no forecast of inflation at all; one Kalshi ladder prices the other.
- **Honest limit:** V2's volume note lists KXCPIYOY at about $80 to $200 a day, so fills are small and the spread may eat the edge.
- **Data and terms:** BLS API (index levels, seasonal factors; PERMITTED), Kalshi history (about 60 requests).
- **Cheapest test and sample:** about 28 monthly events; expected 20 to 40 entries. **Minimum 40; expect NOT_ENOUGH_DATA or a thin read.** Kill: median spread on the bought bracket above 4c.
- **Time to settlement:** 1 day. **Time to verdict:** 3 days. **Tries:** N +1. **Probability:** 5%.

### 13. ROLLOFF: which polls leave the average tomorrow

`ROLLOFF | family: outside composition arithmetic, entry the day before resolution, hold | risk class: mid price, 3 contracts, daily events, group D | stage Idea`

- **Mechanism:** a polling average over a fixed window changes when an old poll drops out, on a date known in advance. If an outlier leaves tomorrow, the average moves tomorrow whatever the new polls say.
- **Entry (frozen):** rebuild the window from the Wikipedia poll table (field dates), compute tomorrow's average from the polls that remain, and buy the side whose ask is 10c or more under the implied chance, 10c to 80c.
- **Honest duplicate flag:** same source and same markets as POL-b2 (the slope of the last 10 polls). This is a different MODEL on an untested Idea, so it is proposed as the model POL-b2 uses, **not a second slot**. It also only works where the settlement average is a simple window average; a weighted model average does not roll off cleanly. The settlement source of each approval series must be read from its rules text first, and the sources themselves are barred, so our table is a proxy.
- **Kill before any trade test:** the proxy fails to reproduce Kalshi's settled value within 0.3 points on 80% of settled days.
- **Sample:** KXTRUMPAPPROVE 68 daily events, KXAPRPOTUS 9 weekly. **Minimum 40 per half; reachable by about January on the daily series.**
- **Time to settlement:** 1 to 7 days. **Time to verdict:** 2 days for the proxy check. **Tries:** N +1. **Probability:** 5%.

### 14. IMPLY1: one market that implies another, across series

`IMPLY1 | family: cross-series implication lock, A NO plus B YES bought together, hold (paired within its own position) | risk class: no outcome risk if the implication is exact; capital lock-up | stage Idea`

- **Mechanism:** if A can only happen when B happens (a shutdown lasting 30 days implies a shutdown; "confirmed as chair" implies "nominated"; "out by March" implies "out by June"), then A's bid may never exceed B's ask. When it does, A NO plus B YES costs under $1 and pays at least $1.
- **Closest existing:** ARB3 (7,396 politics deadline rows, same stem, 0 positive), POLPARITY1. Differs: pairs in DIFFERENT series, which no scan covered.
- **Honest limits:** most implication partners are long-dated and sit on the recorder's `later_only` list, outside the 30 day hold; those are counted as simulation only and quoted per dollar-year. Prior scans of every lock shape found nothing.
- **Cheapest test and sample:** zero new requests for pairs inside the 32 recorded series (`pol-data`, every 30 minutes since Nov 11): after 14 days count pair-snapshots with bid(A) above ask(B) plus fees and size 10 or more. **Bar: 20 such snapshots on at least 3 pairs; else CLOSED.** The pair list is written and reviewed for exactness before the count.
- **Time to verdict:** Nov 25. **Tries:** N +1. **Probability:** 3%.

### 15. WIKIEDIT: the infobox changes before the price does

`WIKIEDIT | family: outside first-notice signal, cheap YES entry, 7 day time exit | risk class: low win rate, small loss, 3 contracts, rare events | stage Idea`

- **Mechanism:** when an office holder leaves, their Wikipedia infobox (term end, successor) is edited within minutes. A structured edit that survives five minutes without a revert is a first notice for "out as" markets.
- **Honest duplicate flag:** same family as POL-n1 (pageviews): outside Wikipedia signal, cheap YES, time exit. Different field (edits to named infobox parameters, not view counts). Under one test per family it is an ARM of POL-n1, not a separate slot.
- **Cheapest test:** existence only: for the 20 to 30 settled "out as" events, the minutes between the first surviving edit (revision history, PERMITTED) and Kalshi's YES crossing 90c (about 30 candle requests). Dead if the median lead is under 2 minutes or vandalism false positives exceed real events.
- **Time to verdict:** 2 days. **Tries:** N +1. **Probability:** 3%.

### 16. SWEEPSIM (combo, simulation only): same-night races break the same way

`SWEEPSIM | family: combo pricing input, no position | risk class: none | stage Idea (a measurement, not a strategy)`

- **What it is:** Kalshi lists no politics-only combo, so by the owner's rule a politics parlay is simulation only. This card measures the one number a future politics combo spec needs: how much more often same-party toss-up races on one night all go the same way than the product of their prices says.
- **Leg-correlation assumption, stated in advance:** one common factor (the national polling miss), **correlation 0.5 (range 0.3 to 0.7)** for same-party general-election legs priced 20c to 80c the day before; 0 for primaries (no party swing inside a primary).
- **Honest limit:** Kalshi's own history has two or three general-election nights with volume, so its own estimate will have a very wide interval; the card reports the interval and does not pretend otherwise. **A rolling parlay built from single markets has no edge of its own:** it multiplies whatever edge the legs have and pays the fee on every leg, so this desk does not propose one.
- **Cheapest test:** day-before prices and results for the Nov 2025 and Nov 2026 general-election winner markets (about 150 requests). Output: the measured joint frequency against the product, with a 90% interval, fed to `combo_price.py`.
- **Tries:** N +0 (no rule is scored). **Probability it becomes a tradable strategy:** 2%, and only if Kalshi lists combos with two politics legs.

---

## Ranking

By speed to a first honest verdict, then by how different the card is from what failed today (the failures were single-market "model against price, cheap side, hold" tests and combos against the product).

| Rank | Card | First verdict | Needs from the shared Kalshi budget | Different from the failures because | Probability |
|---|---|---|---|---|---|
| closed | 1 NESTCOMBO | CLOSED Nov 12: untestable from the public book (combos have no posted asks) | 2 used | no model: a logical bound between a combo and a single | 0% as a public test |
| 2 | 2 ECONLAG | 3 days | about 385 | time exit; one Kalshi market prices another; n about 100 | 8% |
| 3 | 3 BALLOTNO | 2 to 3 days | about 160 | independent events with a known base rate; inside the nothing-happens rule | 7% |
| 4 | 4 UNRATEROUND | 2 days (descriptive) | about 40 | rounding position of a published number, no forecast | 7% / 3% |
| 5 | 7 WXCOMBO-XCITY | late January (part A, zero calls; first partial read Nov 11 was NOT_ENOUGH_DATA) | 0, then about 60 a day | takes the legs' prices as given; only the dependence is claimed | 5% |
| 6 | 10 PRESENTQ | 1 day (offline) | 0, then about 25 | a forward queue, not a base rate | 8% / 3% |
| 7 | 12 CPIARITH | 3 days | about 60 | ladder against ladder | 5% |
| 8 | 13 ROLLOFF | 2 days (proxy check) | about 70 | model for POL-b2, not a new slot | 5% |
| 9 | 9 MOVPARITY | 3 to 5 days | about 800 | cross-series parity on election night | 4% |
| 10 | 15 WIKIEDIT | 2 days (existence) | about 30 | arm of POL-n1 | 3% |
| 11 | 14 IMPLY1 | Nov 25 | 0 | cross-series lock | 3% |
| 12 | 11 TARIFFDTS | 1 day model, a year for trades | 1 | queues with row 77 | 4% |
| 13 | 5 FAANOTICE | BLOCKED until a person reads the FAA terms; then 3 to 4 weeks (existence) | 0 (recorder already quotes) | most unusual source on the list | 5% |
| 14 | 8 WXCOMBO-PERSIST | late January | 0, then a census | product may not exist | 3% |
| 15 | 6 SCOTUSAUTH | July 2027 | about 30 | seasonal, n-limited | 5% |
| 16 | 16 SWEEPSIM | 2 days | about 150 | a measurement only | 2% |

**Top 5:** NESTCOMBO, ECONLAG, BALLOTNO, UNRATEROUND, WXCOMBO-XCITY. Ready-to-run protocols for the first three: `workers/IDEA_DESK_B_PROTOCOLS.md`. **Most unusual:** FAANOTICE and SCOTUSAUTH (both slow).

**Combos (4):** cards 1, 7, 8 and 16, each with its leg-correlation assumption written above before any price is read: 1.0 by logic; 0.45 (0.30 to 0.60) forecast-error correlation for near city pairs; 0.25 (0.10 to 0.40) lag-one; 0.5 (0.3 to 0.7) national swing.

## Considered and NOT carded (said plainly, not padded)

- **Regulation "by date" markets against the official pipeline** (review office listing, public inspection, publication): the same mechanism as POL-c2 (deadline against the official calendar) on another process. A version, not a new card.
- **Trump speech mention base rates** (10,521 settled markets held): a third test in a mention base-rate family that failed twice (MENT1, card 84). Same logic on another speaker is a version.
- **The NO side of mention combos** (buyers lose 29c to 37c per dollar, so the seller wins): a taker cannot get that side; it needs answering quote requests as a maker. What it would take: a reviewed maker for combo quote requests, and the owner's rule today keeps market making on zero-fee series only.
- **A rolling politics parlay from single markets:** no edge beyond its legs, more fees (see card 16).
- **Strait and canal traffic weekly brackets** (KXHORMUZWEEKLY and siblings, high volume): a running-total nowcast, the TSA1 mechanism on another series (TSA1: PF 1.12 and 1.27, under the bar, Brier worse than the market). A version. Its settlement source's terms are also unread.
- **Awards sweep combos** (one film winning several categories): one ceremony is one cluster, so the bar can never be met; the owner also limited entertainment to Kalshi's own history.
- **Company filings as a first notice** for executive departure markets: rare events, and the filing system's access policy asks for a contact in the agent string.
- **Following top traders:** not feasible (positions are private; LEADERBOARD1).

## What this desk could not do

No Kalshi call was made, so every Kalshi count above is taken from the censuses of Nov 11 (which their authors mark as undercounts for settled markets before 2026-09-12) or is marked UNVERIFIED. No card's outcome was read. Probabilities are judgement, not measurement.
