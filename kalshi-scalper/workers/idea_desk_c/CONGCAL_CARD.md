# CONGCAL: congressional markets against the official procedural stage (Idea Desk C, Nov 13, 2026)

**Written before any Kalshi price, list, result or congressional record was read.** Only the series NAMES and settlement sources in the Nov 12 census listing (`CENSUS_LISTING`, series metadata) were seen. Examples: "House passage of a Dreamer bill" (Library of Congress), "Brian Johnson confirmed as CFPB director?" (U.S. Senate), "Will the Senate vote on the Clarity Act?" (United States Congress), "Deputy Secretaries confirmed" (U.S. Senate). A card for the Head of R&D's read, not registered; the Verification Analyst scores it. [research]

`CONGCAL | family: an official procedural fact (cloture filed, a bill placed on the weekly floor schedule, a committee report) against a market priced from news and time, on Kalshi's congressional action and confirmation markets; look once a day, hold to settlement | risk class: mid price (20c to 80c), 1 contract | stage Idea | prior about 3%`

## Mechanism, and the other side

- **What Congress tells us ahead of time.** Congress publishes, ahead of the vote, the procedural steps that decide most outcomes:
  - **Cloture filed on a nomination:** under the Senate's simple-majority rules for nominations, a cloture vote follows within about two session days, and confirmation almost always follows. Nominations rarely fail once cloture is filed.
  - **A bill on the House majority leader's weekly floor schedule:** passage is likely that week; bills under "suspension of the rules" need two thirds, and that is stated on the schedule.
  - **No committee report, or no floor time scheduled before a deadline:** the market's "by date X" question cannot resolve YES in time.
- **The other side:** retail traders who price these markets from headlines and the calendar, not from the procedural record. It is a slow, niche family, with little professional attention.
- **Honest counter:**
  - Political insiders and specialist traders read the same calendars.
  - Many congressional markets are thin.
  - Procedural surprises (a vote pulled, a recess) are exactly the losses.
  - The outside record (Le 2026; Burgi, Deng and Whelan) finds politics prices mostly UNDER-confident, which favours the favourite side. This rule bets the mid band in both directions.

## Sources and terms (named before any read)

- **congress.gov API** (`api.congress.gov`; Library of Congress; US government work). Bill and nomination actions with dates. It needs a free api.data.gov key; the key and its terms are an **owner decision** (this desk holds no key).
- **senate.gov:** the Executive Calendar, cloture filings and the floor schedule. **clerk.house.gov:** roll calls (XML). **The majority leader's weekly floor schedule.** All public US government pages, but their terms of use are to be read by Main before any automated read.
- **Kalshi:** public market lists and candles only.

## The rule (proposed, frozen at registration, never before)

- **Universe:** Kalshi series whose rules settle on a congressional action (passage, a vote held, a confirmation) by a date, with an official source (Library of Congress, U.S. Senate, United States Congress, the Clerk). Fixed from the series list before any price.
- **Daily look** at 14:00 ET on each business day while the market is open. Read the procedural stage from the official record as published by then:
  - **Stage A (strong yes):** cloture filed on the nomination or the bill, or the bill on this week's House floor schedule (not under suspension) with the deadline at least 3 session days away. Buy YES if its ask is 20c to 80c.
  - **Stage B (strong no):** the deadline is within 3 calendar days and the item has had no floor action (no cloture filed, not on this week's schedule, not reported from committee where a report is needed). Buy NO if its ask is 20c to 80c.
  - **Otherwise:** no bet.
- **Execution:** spread 4c or less, the ask seen plus the rounded fee, 1 contract, at most one bet per market (the first stage hit), hold to settlement. A void is a fee-only loss, counted as a bet.
- **Fixed now, never fitted:** the stage definitions, the 3 day line, the 14:00 ET look and the band.

## Numeric prediction, kill lines, windows

- **Zero-try count first, before any price:** the number of markets in the universe that reached Stage A or B while open, from the official record and the market lists only. Below 30 in development, it is the slow-family paper screen only, and "no evidence" below 30 bets.
- **Prediction:** about 20 to 60 qualifying markets a year, so a SLOW family and a paper list at most. Stage A wins about 90%, Stage B about 85%, but the market is usually priced above 80c (Stage A) or under 20c (Stage B) by then. Bets are rare, and the development cash PF is 0.8 to 1.5.
- **Kills:**
  - **development:** fewer than 30 bets is "no evidence at n = x"; a cash PF under 1.0 closes it;
  - **slow-family paper screen:** cash PF 1.3 on 30 or more independent events, both halves positive, read once;
  - **main bar:** PF 1.5 in three windows and z 5.46, likely out of reach.
- **Windows (by market close date, constants):**
  - development = closes before 2026-07-01;
  - **held-out = closes 2026-07-01 to before 2027-01-01**, read once on the Head's go.
  - For the Head and Auditor B: W-CAT-POLENT1 holds politics events from a fixed list (not released), and POLGAPH holds politics windows from 2026-11-05. Any overlap with this universe must be checked by series before any read.
- **Held-out line for HELDOUT_REGISTRY.md:** `| CONGCAL | Idea Desk C | idea-desk-c:kalshi-scalper/workers/idea_desk_c/CONGCAL_CARD.md | Kalshi congressional action and confirmation series (fixed list at registration) | Development = closes before 2026-07-01; held-out = closes 2026-07-01 to before 2027-01-01, read once on the Head's go | 2026-07-01; 2027-01-01 | NOT READ | card text | card only, not registered; POLENT1 and POLGAPH overlap to check |`

## Uniqueness checks (lifecycle 7d), self-scored, and the declined list (7e)

1. **Signal: a new source and field.**
   - The official procedural record (cloture, floor schedule, committee action), which no card reads.
   - Closest:
     - **The "nothing happens" politics rule** (NO at 60c to 88c within 14 days): CONGCAL's Stage B differs because it requires a procedural fact (no floor action before a near deadline), not just time, and it bets 20c to 80c.
     - **The politics calibration tests** (POLAPPR1, W-CAT-POLENT1): those use price only.
     - **FOMCTEXT:** another official-text source, but a different family (Fed mentions).
   - Self-score: unique by source and signal, medium confidence. Stage B alone might be ruled a version of nothing-happens; if so, Stage A is the card.
2. **Entry and exit:** a daily look and hold, on markets no live or shadow rule trades.
3. **Correlation:** no shared market with gold L1, OICORE, EVENT830 or CFRTI-K.
4. **Declined list:**
   - not a lock or parity scan, not taker flow, not a cheap-side sweep, not market making, not time-of-day;
   - favourite-and-hold is excluded by the 20c to 80c band;
   - no Polymarket or Yahoo read.
   - The politics hold cap (30 days for singles, POLITICS_RULES) applies to any live probe, not to the research read.

## Amendment 1 (Nov 13, 2026, before any data): the Verification Analyst's ruling

- **Stage A is NEW** (an official procedural stage as the signal, a field no registered test read). **Stage A is the card.**
- **Stage B is a VERSION of the "nothing happens" rule** (POLITICS_RULES section 5). It is removed from this card. It is not counted as research and goes to the paper list only as a version of that rule.
- **Family:** CONGCAL and FEDREGPI are ONE family, "official primary-source status of a government action, traded on Kalshi's government-action markets", counted once under the three-falsified effort stop.
- **Flags before any work:**
  - (i) congress.gov needs an API key. Under the Charter, any key needs the owner's popup; until then only senate.gov and clerk.house.gov can be used, and only after Main has read their terms. A source with unread or ambiguous terms is out.
  - (ii) History is tiny (V2's COUNT1, COUNT2 and GOVCOUNT1 found 1 to 15 settled events in such series), so only the slow-family paper screen (30 independent events, both halves positive, pinned cutoff) is reachable, after a long wait.
  - (iii) No live strategy overlaps, so the correlation check does not apply.
