# Politics and parlay rules (owner decisions, Nov 11, 2026)

**Status: recorded from the owner's popup answers of Nov 11, 2026.** It sits under `docs/CHARTER.md` (which only the owner changes) and `docs/RND_CHARTER.md`. Where they differ, the Charter wins.

**Nothing here authorizes a live order.** Every live probe, single or parlay, still needs paper edge first, a written spec, and the owner's own popup for that exact probe. These rules are the limits a probe spec must stay inside, and the research rules for the politics program.

## 1. Research rules

- **Scheduled events first.** Votes, confirmations, shutdowns and deadlines are tested before the other politics families.
- **Forward shadow recording.** The thin politics series are recorded forward (`record-politics.yml`, branch `pol-data`) so history accrues. The recorder's hold cap follows the rule below (30 days since Nov 11, 2026).
- **Hold window (owner, Nov 11, 2026, later popups).** Politics and elections singles and nothing-happens may hold up to **30 days** to settlement (it was 14). Limits: 3 contracts per market, and at most 5 positions open at once that settle beyond 14 days, inside the 10 open total and the $200 lifetime budget. **Economics and weather stay at 14 days.** **Clinical trials and health markets may hold up to 90 days** (to cover late entry in the last 3 months of the typical 99 to 255 day market): 1 contract per market, at most 3 clinical positions open at once, counted inside the $200 budget, and every return figure for that family is quoted **per dollar-year**. The mixed-combo exception below is unchanged. Longer markets go on a "later only" list and are not scored. Each live probe still needs its own owner popup.
- **Mixed combos are an explicit exception to the 14 day cap (owner, Nov 11, 2026: "allow them").** Combos with a politics leg inside Kalshi's cross-category combos (mostly sports legs, closing as late as Nov 2027) are allowed. They stay under every parlay rule: at most 30 legs (see the leg cap below), $2 per parlay, $40 total stop, 10c per dollar paper edge first, and the owner's own popup before any live probe. **Each spec must say plainly that the money is held until settlement, up to Nov 2027.**
- **Parlays are in.** 2 to 30 legs (owner, Nov 11, 2026: up to 30 legs "at small $ amount if you pick and manage"; it was 2 to 5 before). Work is on weather, mentions and sports (NBA, NFL) combos, on Kalshi's own prices only. Politics-leg combos exist inside Kalshi's cross-category collections, mixed with sports legs; a politics-only combo does not, so politics-only parlays are simulation only.
- **Many-leg combos (owner, Nov 11, 2026):** the leg cap is raised from 5 to 30 for small-dollar combos; the $2 per parlay and the $40 total stop are unchanged. The research team PICKS candidates and brings each to the owner as a popup with the exact legs, the price, the estimated win chance and the lock-up. Nothing is placed by the EA or by research; any live placement is by the owner by hand, or by reviewed bot code after the owner's popup. **Each spec must be honest about the win chance of a many-leg combo** (it falls fast with legs) **and about how the 10c per dollar paper edge is estimated when legs are correlated** (an independence product misstates it; say which assumption was used and show the sensitivity).
- **Linked legs are allowed.** The link between legs must be stated in writing before the test runs.
- **"Nothing happens"** (the NO arm of dramatic "will X happen by date" markets) is allowed as a politics family, distinct from the declined favourite-late gold hold (different market, different data). Paper first.
- **Terms rule and host gates** are unchanged: only sources whose terms allow automated reads; new hosts go through the allowlist and its gate.
- **PF 1.5 bar, counted deflation, the uniqueness test and the declined list** are unchanged.

## 2. Limits a live probe must stay inside

These are caps, not permission. A probe starts only after the owner approves its exact spec.

| Item | Rule |
|---|---|
| Single politics probe size | 3 contracts |
| Early live parlay probe size | $2 per parlay |
| Parlay probes stop automatically at | $40 total loss |
| Paper edge before an early live parlay probe | 10c per dollar after fees (the spec must define exactly what is measured and over how many settled trades) |
| Exit | hold to settlement |
| Open positions at once | up to 10 politics or parlay positions |
| Side | either side, whichever the test supports |
| Entry price | 10c to 90c |
| Hold | 30 days at most for politics singles and nothing-happens (at most 5 open beyond 14 days); 14 days for economics and weather; 90 days for clinical trials (1 contract, at most 3 open) |

## 3. Kill and return

- **Kill (single politics probe):** net under -$15 after 20 fills, or 5 losses in a row. The probe stops and stays stopped.
- **Kill (parlay probes):** $40 total loss.
- **Return after a kill:** a 14 day cool-off, then a shadow PF of 1.3 or better, then the owner approves. Nothing resumes on a date alone.
- **Scheduled events:** trading around a scheduled event is allowed only if the strategy was built and tested for that window.

## 4. Further rules (owner popups 17 to 28, Nov 11, 2026)

- **Weather combos:** same city, linked days or brackets first.
- **Mention combos:** words in the same speech or call first.
- **Sports combos:** price consistency only, against Kalshi's own single markets. No outside sports data.
- **Conflicts:** the first strategy in holds the market; the other skips it.
- **Poll sources:** only those whose terms were read and allow it. Today that is the Wikipedia polling tables via its API.
- **Attention signals (Wikipedia pageviews, GDELT):** test both directions, pre-registered.
- **Trump approval and generic ballot:** run the calibration test on both now (the fastest real politics verdict).
- **Foreign politics:** only markets settling within the politics hold window (30 days).
- **Activity counts (executive orders, bills signed):** base rates plus the count so far this week, via GovInfo.
- **Mention base rates:** Kalshi's own settled mention history.
- **Resolution-rule edge cases:** flagged to the owner with the rule text, never automatic.
- **News fade:** pre-register three delays (15 minutes, 1 hour, 4 hours), all counted in the deflation.

## 5. Nothing happens, budget and proof (owner popups 29 to 40, Nov 11, 2026)

- **Nothing happens (NO side of "will X happen by date"):** only markets within the politics hold window (30 days; it was 14); NO bought at 60c to 88c; 1 contract; at most $5 at risk per market; ONE market per story.
- **Budget:** politics and parlay probes may use up to **$200 lifetime in total** (the owner chose this over the recommended $60). Each live probe still needs its own owner popup.
- **Shard:** confirm which Kalshi shard politics singles use and the smallest amount to move there. The owner moves the money themselves; the page and the bot cannot.
- **Reporting:** politics and parlays are reported only on a real result or a decision.
- **Proof:** the same bar as everything else, PF 1.3 or better over 100 fills in 2 of 3 windows.
- **Economics releases:** in as their own family. Run both the overshoot fade and the official-components idea, counted together in the deflation.
- **EVENT830:** left to its own kill rule.
- **Weather singles:** yes, on NWS data, the day-end rounding idea first.

## 6. Other families (owner popups 41 to 44, Nov 11, 2026)

- **Sports singles:** calibration only, on Kalshi's own settled markets. No outside sports data.
- **Market making:** stays on zero-fee series, not sports. The questions on first-live details (popups 45 to 48) were not answered; they are asked only if the Nov 24 read passes.
- **Entertainment:** Kalshi's own history only. Awards combos by price consistency.
- **App Store and Steam charts:** yes, a small test on the permitted official APIs.
- **Clinical trials (new family, owner, Nov 11):** a census of Kalshi's FDA approval, drug and trial readout, PDUFA and health markets first; any source (ClinicalTrials.gov, openFDA, FDA advisory calendar, Drugs@FDA) has its terms read before any automated read.

## 7. What is not decided

- No code places any politics or parlay order, and the second slot registry (`functions/kalshiSlotLib.js`) holds none. Admitting one is a separate reviewed pull request and the owner's own popup.
- The exact meaning of "10c per dollar after fees" is left to each probe spec to define and the owner to approve.
- How a parlay would be placed if Kalshi offers no politics combo market is undecided; today it would be a simulation only.

## 7. Three owner decisions (Nov 12, 2026)

- **Combo house side (owner exception).** MEASURE ON PAPER: buy NO on high-priced combos and hold to settlement. This is a written owner exception to the Charter's buy-high-and-hold ban, for combos only; it covers no single market and no other strategy. Small $2 live probes are allowed ONLY IF paper shows an edge, and then only under the parlay rules in section 1 ($2 each, $40 total stop, 10c per dollar paper edge first). Each live probe needs its own owner popup with the exact spec. The spec must say plainly that the money is held until settlement.
- **Weather brackets (ORHARVEST1).** Allowed on paper with YES priced 35c to 88c ONLY (the NO side 12c to 65c). The 65c to 87c NO legs stay under the ban. The protocol stays behind the MMSIM1 read.
- **Combo book recorder.** Approved to build: public Kalshi data, no key, no orders, the same safety pattern as the other recorders, with a security pass. It is tracked as a separate pull request.

Nothing here authorizes a live order.

## 8. Slow-family paper screen (Nov 12, 2026, owner decision relayed by the EA)

**Why.** Idea Desk B's power file showed the main research bar (about 900 to 1,350 independent events at a true profit factor of 1.5, deflated for the number tried) cannot be reached for years by a family that produces a dozen events a year. Refinement's power table found the same for the forward-only ideas. The owner's decision: slow families get a SEPARATE, LOWER screen that decides one thing only, whether an idea goes on a PAPER LIST. It is not the main bar, it replaces nothing in it, and it proves nothing.

### What counts as a slow family

Both of these, stated in the registration before the first read:

1. **Fewer than about 52 independent events a year** (owner, Nov 12, 2026: the line was first drawn at about 26 and moved to about 52 the same day, so weekly families may use the screen). The unit is an independent event (a monthly release, a court term, an election night, a trial readout), not a market and not a contract. Many markets on one event are one event.
2. **It cannot reach the main bar within 26 weeks** at the rate it produces events (the arithmetic in the Desk B and Refinement power files; the main bar is the z score that clears the deflation count, or PF 1.5 in three windows).

Monthly, weekly, seasonal and calendar-bound families (economics releases, court terms, elections, clinical readouts, storms and quakes) are the intended cases. A daily family (ROLLOFF, about 365 a year) is NOT slow; it stays on the main bar.

### The screen

All of these, registered before any result is read:

- **Cash profit factor of 1.3 or better** on at least **30 independent events**: gross cash won divided by gross cash lost, 1 contract, fill price plus fee, hold to the stated exit, one trade per event.
- **Both halves positive.** Split the events by event date at the median; each half has net cash above zero.
- **Pinned cutoff, read once.** The cutoff is a date constant in the script, the same constant is in the registration, and the read-once marker is a line committed to the repo (`docs/RND_CHARTER.md` section 6, item 7). Events after the cutoff are the only ones a later read may add.
- **The number tried is counted and stated** next to the result (see the multiplicity note).
- **Labels.** Fewer than 30 independent events: **"no evidence at n = x"** (x is the actual count), never PASS and never FALSIFIED, and the idea is not scored. 30 or more and the screen is met: **"on the paper list (unproven)"**. 30 or more and the screen is not met: **"off the list (failed the screen)"**. The word PASS is not used for this screen anywhere.

### What it permits

- A **paper list** entry: the rule's trades are logged forward on paper, with the registered exit, and every line carries the label **unproven**.
- A written forward kill criterion in the registration (research charter section 6), checked on the forward paper trades only.
- Nothing else. A listing is not approval, not a shadow-list entry, not a promotion and not a reason to skip any step in `docs/STRATEGY_LIFECYCLE.md`.

### What it does NOT permit

- **No live order of any kind.** Being on the paper list is not enough for one.
- **Any live probe** needs the owner's own popup for that exact probe with its exact spec, and then stays inside every limit in section 2 (3 contracts for a single politics probe, $2 per parlay, $40 total parlay stop, 10c to 90c entry, hold to settlement) and the $200 lifetime budget; a probe off this list is small, at most $2 of risk, and labelled **unproven** in the spec, the popup and every report.
- **The existing bans stay.** No favourite-and-hold except the owner's combos exception (section 7). The declined list (`docs/STRATEGY_LIFECYCLE.md` 7e), the uniqueness test and the terms rule apply unchanged. A source whose terms were not read or are ambiguous is blocked here too.
- It does not reopen a card that was closed or retired on evidence or by the owner. Reopening is a separate decision.

### Multiplicity: the lower bar lets false positives through

A rule with NO edge passes this screen far more often than it passes the main bar. Computed exactly (binomial, every outcome enumerated; scratch script not kept in the repo): n = 30 independent bets, 15 in each half, one contract bought at price p, fee 0.07 x p x (1 - p), the zero-edge rule winning with probability equal to its price (a calibrated market), pass = cash PF at least 1.3 AND net cash above zero in both halves.

| Price paid | Zero edge before the fee | Zero edge after the fee (true win chance = price + fee) |
|---|---|---|
| 0.20 | 12.4% | 15.5% |
| 0.50 | 15.1% | 20.0% |
| 0.75 | 16.2% | 20.4% |
| 0.90 | 30.1% | 34.0% |

**Headline: about 1 in 7 (roughly 15%) of rules with no edge pass this screen at n = 30 for prices of 20c to 75c, up to about 1 in 5, and about 3 in 10 for 90c favourites (the outcomes are lumpy at n = 30, so these wobble by a point or two).** Requiring more events helps slowly: at n = 100 the same table reads 7%, 4% (0.50, before fee), 8% and 15%. The PF alone, without the halves rule, would pass 18% to 41%, so the halves rule roughly halves the false positives and is kept for that reason.

What follows from it:

1. **A listing means "survived a weak filter", not "has an edge".** About 1 in 7 listings from a pile of no-edge ideas would be there by luck.
2. **Tries add up.** With 15% per try, the chance that at least one of k zero-edge rules is listed is 1 - 0.85^k: 5 tries give about 56%, 10 tries about 80%. Every idea read against this screen counts as a try, passing or not, and the running count is stated beside any listing.
3. **Correlated events inflate it.** The numbers assume independent events; if the registration's events share a driver, the true false-positive share is higher.
4. **More cards are eligible since the line moved to about 52, so the tries pile up faster.** Three cards (UNRATEROUND, POL-b3, ECONLAG) can be read now: if all three had no edge, the chance that at least one is listed is 1 - 0.85^3, about 39%. At least 25 named slow cards are eligible in the table above as their events accrue: if all 25 were read and none had an edge, the chance that at least one is listed is 1 - 0.85^25, about 98%. Plainly: a listing from a long run of cards is expected even if none has an edge, so the count of cards read is stated next to every listing and a single listing is weak evidence.
5. This is the reason the screen leads only to paper trades, and why a live probe stays tiny, unproven and a separate owner decision.

### Re-screen of the slow-family cards (Nov 12, 2026; nothing was run)

Sources: Desk B's `IDEA_DESK_B_POWER.md` (branch `claude/idea-desk-b`), Refinement's `POWER_TABLE_NOV12.md` (branch `claude/refine-live`), V2's `POWER2_QUEUE.md` (branch `claude/epic-ptolemy-0amjd9`). "n" is the independent events held now, as those files state it. "Qualifies" means: it is a slow family under the definition AND holds at least 30 independent events, so it could be read against the screen at a pinned cutoff once its registration is complete. Any other slow card gets the label "no evidence at n = x" and a rough date to 30 events at its stated rate. Only three cards qualify.

| Card | Slow family? | n held now | Events a year | Qualifies? | Why / next |
|---|---|---|---|---|---|
| Desk B UNRATEROUND (unemployment rate rounding) | yes | about 33 (months) | 11 | **Yes, marginal** | n of about 33 is just over 30, so it could be read once with a pinned cutoff; its source terms are not recorded in the power file and must be read first; retired on the main bar, so a Main/owner call to re-enter |
| Refinement POL-b3 (elections against polls) | yes (seasonal, even-year autumn) | about 60 to 90 usable nights (history holds 152; Refinement's estimate, not verified) | none open before 2027 | **Yes, on history only** | the unit is an election night, not a market; needs the registration and a pinned cutoff; no forward events until 2027 |
| Desk B ECONLAG (economics release lag) | yes (about 36 a year, under 52) | about 70 print days | 36 | **Yes** | enough events for a read with a pinned cutoff; Desk B demoted it on the main bar, so re-entering is a Main/owner call, and its source terms must be on record |
| Desk B CPIARITH | yes | about 28 (months) | 12 | No: "no evidence at n = 28" | 30 is about two releases away |
| Desk B SCOTUSAUTH | yes | 15 to 30 cases | 12 | No: "no evidence at n = 15 to 30" | at most about 15 months to 30; retired on the main bar |
| Desk B PRESENTQ | yes | about 11 (months) | 12 | No: "no evidence at n = 11" | about 19 months to 30 |
| Desk B WIKIEDIT | yes | 20 to 30 | about 10 | No: "no evidence at n = 20 to 30" | up to about 12 months to 30 |
| Desk B BALLOTNO | yes | 1 election date | under 20 measures in 2027, about 150 in Nov 2028 | No: "no evidence at n = 1" | parked until 2028 (the one-night description was done) |
| Desk B FAANOTICE | yes (about 36 a year) | 0 | 36 | No: "no evidence at n = 0" | forward only (about 10 months to 30) and the source terms are unread (blocked) |
| Desk B TARIFFDTS | yes | 0 to 12 | 12 | No: "no evidence at n = 0 to 12" | also blocked: the Treasury source terms are ambiguous |
| Desk B MOVPARITY arm B | yes (races) | 10 to 40 nights | few until 2028 | No: "no evidence at n = 10 to 40" | the count is too loose to rely on; arm A is a lock scan with its own count bar, not this screen |
| Desk B SWEEPSIM | yes | 2 to 3 nights | under 1 | No: "no evidence at n = 2 to 3" | no instrument exists |
| Desk B ROLLOFF | no, about 365 a year | 68 daily events | 365 | No (not slow) | main bar is reachable in months; stays on it |
| Desk B IMPLY1, NESTCOMBO, WXCOMBO-XCITY, WXCOMBO-PERSIST | not applicable | n/a | n/a | No | closed or retired on evidence (no posted combo asks, no lock found) |
| Refinement ECONFADE (row 87) | yes | 1 shock in 26 print days | about 8 | No: "no evidence at n = 1" | about 5 years to 40 at its own rate |
| Refinement QUAKE-M7 (row 89) | yes | 5 settled | 12 | No: "no evidence at n = 5" | about 25 months to 30 |
| Refinement GSTORM-KP (row 90) | yes | 9 settled | at most 12 | No: "no evidence at n = 9" | about 21 months to 30 |
| Refinement ENSO-CPC (row 91) | yes | not stated | 12 | No: "no evidence", count not stated | about 30 months if it started at zero |
| Refinement CPIGAS-EIA (row 77) | yes | 16 settled | 12 | No: "no evidence at n = 16" | about 14 months to 30 |
| Refinement LMARENA-HIGH (row 93) | unknown rate | 2 settled | unknown | No: "no evidence at n = 2" | parked on terms |
| Refinement SNOWRUN (row 76) | yes (seasonal, about Dec to Mar) | 0 (forward log) | independent storms unknown, at most about 100 correlated brackets a winter | No: "no evidence at n = 0" | one winter will not reach 30 independent storms; count storms, not brackets |
| Refinement POL-c2 (deadline markets) | yes | a handful per decade | about 0.5 | No: "no evidence", n tiny | near certain to stay below 30 for years |
| Refinement NO-arm approval | yes (weekly approval series, about 52 a year) | no cell reached 30 in both thirds (8 of 263 events had candles for one series, 0 of 143 for the other) | about 52 | No: "no evidence at n under 30 per cell" | the limit is the candle pull, not the calendar; a larger pull is needed first |
| Refinement MORT30-FRED (row 78) | yes (weekly) | 11 settled | about 52 | No: "no evidence at n = 11" | about 19 weeks to 30 |
| Refinement TGA-DTS (row 79) | yes (weekly) | 5 settled | about 52 | No: "no evidence at n = 5" | about 25 weeks to 30; the Treasury source terms need a person to read them first |
| Refinement OPENROUTER-SHARE (row 92) | yes (weekly) | 3 settled | about 52 | No: "no evidence at n = 3" | about 27 weeks to 30 |
| Refinement POL-b2 (approval up or down) | yes (weekly) | settled count unverified | about 52 | No: "no evidence", count unverified | count it before any screen |
| Refinement POL-c1 votes, POL-n1, POL-n2, POL-i2, DEBTPENNY | probably | counts unverified | unknown | No: "no evidence", count unknown | count them before any screen |
| V2 queue (`POWER2_QUEUE.md`) | none slow | n/a | n/a | No | every queued card runs on 15 minute, hourly or daily series; its one monthly card, CLINICAL2 (17 held, 12 a year, about 13 months to 30), was CLOSED Nov 11 and the screen does not reopen it |

**The line moved (owner popup, Nov 12, 2026).** It was first drawn at about 26 events a year; the owner moved it to about 52 so weekly families (MORT30-FRED, TGA-DTS, OPENROUTER-SHARE, POL-b2, ECONLAG and similar) may use the screen. ROLLOFF (about 365 a year) stays on the main bar.

Nothing in this section authorizes a live order.
