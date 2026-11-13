# FEDREGPI: executive-action markets against the Federal Register's public inspection list (Idea Desk C, Nov 13, 2026)

**Written before any Kalshi price, list, result or Federal Register document was read.** Only series NAMES and settlement sources in the Nov 12 census listing were seen. Examples: "50% tariffs on Canadian autos and steel" (Federal Register), "Tariffs on copper in effect before date" (White House), "Crypto executive order" (ABC), "Trump's Executive Order 14418" (AP). A card for the Head of R&D's read, not registered; the Verification Analyst scores it. [research]

`FEDREGPI | family: an official early-release channel (the Federal Register's public inspection desk, where signed executive documents appear about a business day before publication) against markets priced from news; look each business day, hold to settlement | risk class: mid price (20c to 80c), 1 contract | stage Idea | prior about 2%`

## Mechanism, and the other side

- **What is published early.** Presidential documents (executive orders, proclamations such as tariff actions) and agency rules are filed for PUBLIC INSPECTION at the Office of the Federal Register, usually the business day before they are published. The public inspection list is public, on federalregister.gov and its API. A market asking "will an order or tariff of kind X be signed, published or take effect by date D" can therefore be partly answered a day early from an official record. That includes the effective date written in the document.
- **The other side:** traders who price these markets from news reports, and who react only when the press reports the signing or the publication.
- **Honest counter:**
  - Professional trade, legal and policy watchers read the public inspection list daily, and news wires often report signings first. The lead may be minutes, not a day.
  - Many of these markets are one-off and thin.
  - Some settle on a news source (ABC, AP) rather than the Federal Register, so publication there is not the settling fact.

## Sources and terms (named before any read)

- **The Federal Register API** (`www.federalregister.gov/api/v1`, public inspection documents and published documents; no key). It is run by the Office of the Federal Register (National Archives) and the GPO, and its content is US government work. Its terms page is to be read by Main before any automated read, and its developer pages state any rate limits.
- **Kalshi:** public market lists and candles only.

## The rule (proposed, frozen at registration, never before)

- **Universe:** Kalshi markets whose rules settle on a signed, published or effective executive document (an executive order, proclamation, tariff action or Federal Register rule) by a date. The list is fixed from the series rules text before any price.
- **Daily look** at 17:00 ET each business day. Read the public inspection list (documents filed that day, with their titles, types and effective dates):
  - if a filed document satisfies the market's YES condition (matched by the market's own named subject and type, by two blind passes, as in FOMCTEXT Clarification 4), buy YES if its ask is 20c to 80c;
  - if the market's deadline is the next business day and no matching document is on the list, buy NO if its ask is 20c to 80c.
- **Execution:** spread 4c or less, the ask seen plus the rounded fee, 1 contract, at most one bet per market, hold to settlement. A void is a fee-only loss, counted as a bet.
- **Settling source:** markets whose settling source is a news outlet are kept, but reported as a separate descriptive row.

## Numeric prediction, kill lines, windows

- **Zero-try count first, before any price:** the number of markets in the universe that had a matching public inspection document, or a next-day deadline with none, while open. Below 30 in development, it is the slow-family paper screen only.
- **Prediction:** about 20 to 80 qualifying markets a year (executive-action markets cluster in active policy periods), a SLOW family and a paper list at most. Most matching documents are already priced above 80c by the public inspection time, so bets are rare. Development cash PF 0.8 to 1.4.
- **Kills:**
  - **development:** fewer than 30 bets is "no evidence at n = x"; a cash PF under 1.0 closes it;
  - **paper screen:** PF 1.3 on 30 or more events, both halves positive, read once.
- **Windows (by market close date, constants):**
  - development = closes before 2026-07-01;
  - **held-out = closes 2026-07-01 to before 2027-01-01**, read once on the Head's go.
  - W-CAT-POLENT1's fixed list and POLGAPH's politics windows must be checked for overlap by series first.
- **Held-out line for HELDOUT_REGISTRY.md:** `| FEDREGPI | Idea Desk C | idea-desk-c:kalshi-scalper/workers/idea_desk_c/FEDREGPI_CARD.md | Kalshi executive-action series settling on a signed, published or effective document (fixed list at registration) | Development = closes before 2026-07-01; held-out = closes 2026-07-01 to before 2027-01-01, read once on the Head's go | 2026-07-01; 2027-01-01 | NOT READ | card text | card only, not registered; POLENT1 and POLGAPH overlap to check |`

## Uniqueness checks (lifecycle 7d), self-scored, and the declined list (7e)

1. **Signal: a new source and field.**
   - The Federal Register's public inspection list, an official early-release channel no card reads.
   - Closest:
     - **CONGCAL** (this desk, the congressional procedural record): a different branch, a different source, and a document already decided rather than a procedural stage;
     - **the "nothing happens" rule:** the NO arm here needs an official absence one business day before the deadline;
     - **the rule-edge-case flag:** this card is about the settling fact, not about how the rules text is worded.
   - Self-score: unique, medium confidence. CONGCAL and FEDREGPI may be ruled one "official government calendar" family, in which case this is its second card, not a new family.
2. **Entry and exit:** a daily look and hold, on markets no live or shadow rule trades.
3. **Correlation:** no shared market with any live strategy.
4. **Declined list:**
   - not a lock or parity scan, taker flow, a cheap-side sweep, market making or time-of-day;
   - the 20c to 80c band excludes favourite-and-hold;
   - no Polymarket or Yahoo read.

## Amendment 1 (Nov 13, 2026, before any data): the Verification Analyst's ruling

- **The YES arm is NEW:** a decided-fact lag from an official list. **The YES arm is the card.**
- **The NO arm is a VERSION of the "nothing happens" rule.** It is removed, and goes to the paper list only as that version.
- **One family with CONGCAL,** counted once.
- **The universe is narrowed to answer the VA's risk.** V2's GOVCOUNT1 found that Federal Register publication lags SIGNING by 3 to 7 days, so for a market that settles on signing, the news has already carried the fact before the public inspection list shows it. So the universe is ONLY markets whose settling fact is the document's Federal Register publication or its EFFECTIVE date (for example tariffs taking effect on a date, or a rule in effect). Markets that settle on a signing or an announcement, or on a news outlet's report, are left out.
- **No key is needed;** the content is public domain. Main reads the site's terms. It is a slow family: the paper list only.
