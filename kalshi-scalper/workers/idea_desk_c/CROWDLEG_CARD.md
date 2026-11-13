# CROWDLEG: combo maker inventory on a crowded leg (Idea Desk C, Nov 13, 2026)

**Written before any combo price, trade or result was read for scoring** (only file names, columns and row counts on `combo-data`). Ruled NEW as a signal by the Verification Analyst on Nov 13. A card for the Head of R&D's read, not registered. Combos are paper only (politics rules). [research]

`CROWDLEG | family: request-for-quote maker inventory on combo legs (flow concentration across combos sharing one leg); a look at each recorder poll, hold to settlement | risk class: cheap-to-mid NO (20c to 50c), 1 contract, paper only | stage Idea | prior about 2%`

## Mechanism, and the other side

- **How the exposure builds.** Kalshi combos are created on request: a maker quotes each combo to one taker.
  - When many takers buy YES on combos that share one leg L within a short time, the maker that filled them is short the joint outcome on L many times over.
  - A maker managing that one-sided inventory has a reason to quote later combos containing L dearer on YES, which makes their NO cheaper.
  - If the skew is larger than the true change in the odds, NO on the next combo containing L is underpriced.
- **The other side:** the maker skewing quotes to manage inventory, a named counterparty with a reason.
- **Honest counter:**
  - Kalshi's combo maker may hedge each leg in the single markets at once, leaving no skew.
  - A crowded leg may also be crowded because the leg is truly likely, in which case NO is correctly priced.
  - The nearest tried class, maker inventory skew on the 15 minute books (MAKER4, MM1, BOOKCH1), found nothing there.

## Data (and what is missing)

- **Recorded now:** `combo-data` quotes (30 minute polls, about 400 rows a run), trades for the 15 most traded combos a run (with the taker side), and the daily settled list.
- **Missing:** legs for every traded combo (leg tickers are kept only on the first 100 quote rows a run), trades for all combos rather than the top 15, and a poll finer than 30 minutes. The recorder change is in the note to the Head; nothing can be scored until it is made.

## The rule (proposed, frozen at registration, never before)

- **Crowding:** at each poll, for each leg L, C(L) is the number of combo trades in the previous 60 minutes whose taker bought YES and whose combo contains L as chosen (same leg ticker and side). This uses trade rows joined to their combo's leg list.
- **Trigger:** C(L) of 10 or more (fixed now, never fitted).
- **Bet:** at that poll, for each listed combo that contains L, was created after the 60 minute window began, and is not one of the counted trades:
  - buy NO if its NO ask is **20c to 50c** and its spread is 4c or less;
  - at most 3 combos per leg per hour, 1 contract each, held to settlement.
  - The band stops at 50c because a NO above about 50c to 65c bought and held is the favourite-and-hold shape. The owner's combo exception covers only NO on high-priced combos, so the band is held under it rather than asking for a new exception.
  - Fill at the ask seen plus the rounded fee. A void is a fee-only loss, counted as a bet.

## Numeric prediction, kill lines, windows

- **Zero-try count first, before any price, once the recorder change has run 14 days:** the number of trigger hours and of qualifying combos. Below 100 qualifying combos, it closes with "no evidence".
- **Prediction:** most crowded legs are crowded because they are likely, so NO is roughly fairly priced. Development cash PF 0.8 to 1.2.
- **Bar:** the parlay rules first: a paper edge of 10c per dollar over 100 settled combos. Then the research bar (PF 1.5 in three windows, z 5.46, clustered by US Central day) before anything else.
- **Kill:** fewer than 100 bets in development, PF under 1.0, or a half under 1.2.
- **Windows (forward only, constants set when the recorder change lands):**
  - development = the first 21 days of the widened recorder;
  - held-out = the next 21 days, read once on the Head's go.
  - The exact dates are written as a dated amendment the day the change goes live, before any row is read.
- **Held-out line for HELDOUT_REGISTRY.md:** `| CROWDLEG | Idea Desk C | idea-desk-c:kalshi-scalper/workers/idea_desk_c/CROWDLEG_CARD.md | Kalshi combos (combo-data, after the recorder change) | Development = first 21 days of the widened recorder; held-out = next 21 days, read once on the Head's go (dates fixed by amendment when the change lands) | to be fixed | NOT READ | card text | card only; needs the recorder change |`

## Uniqueness checks (lifecycle 7d), and the declined list (7e)

1. **Signal: NEW** (the Verification Analyst, Nov 13): crowded-leg flow on the combo tape, a source and tape the taker-flow row does not name (that row covers the 15 minute tape). Closest: MVE1 (price against legs, no flow signal), S3 the combo house side (NO on high-priced combos, no flow signal), and maker inventory skew on the 15 minute books (MAKER4, MM1, BOOKCH1).
2. **Entry and exit:** a poll-time look and hold, on combos no live or shadow rule trades.
3. **Correlation:** no live strategy trades combos.
4. **Declined list:**
   - not a lock or parity scan (no leg prices are used);
   - not 15 minute taker flow, not a cheap-side sweep, not market making, not time-of-day;
   - favourite-and-hold is avoided by the 20c to 50c NO band;
   - no Polymarket or Yahoo read.

## Amendment (Nov 13, 2026, before any data): exit variant, the owner's standing rule (rnd-queue 370169d1)

**No exit variant possible: hold only.**
- **Why:** an exit from a combo means selling it back through Kalshi's request-for-quote system. Kalshi's public Combos help article (help.kalshi.com/en/articles/13823820-combos, read Nov 13) says: "Once a combo is placed and filled, it cannot be canceled or reversed by the user." Neither it nor the RFQ docs (docs.kalshi.com/getting_started/rfqs.md) describe any way to request a quote to SELL a combo already held.
- **So:** no profit target, stop, time exit or in-and-out can be priced from public evidence, and the card stays hold to settlement.
- **If Kalshi confirms** (an owner or Main question, not research) that a held combo can be quoted for sale, an exit variant is registered then, as its own try, before any data.

## Amendment (Nov 13, 2026, before any data): reading the widened recorder

- Trades are read from `trades.csv` and joined to `legs.csv` by combo ticker; a combo in `legs_missing` is dropped and counted, never guessed.
- Successive polls read overlapping tape windows on purpose, so trades are de-duplicated by `trade_id` across polls before any count.
- A poll whose coverage row has `tape_complete` 0 (tape cut at the page cap, a failed read or a stopped run) is counted and reported; its window is a lower bound, never a quiet hour.
- Every result states the share of traded combos dropped for want of legs (`legs_missing` over `combos_traded`, summed over the polls read) and the share of polls with `tape_complete` 0 (Auditor B, Nov 13).

## Amendment (Nov 13, 2026, before any data): the nonstop tape recorder, and rule 17

- The trades and legs now come from the nonstop recorder `record-combo-tape.yml` (`combotape-data`, `tape/`), which replaces the widened-poll plan above; quotes with leg tickers on every row still come from `record-combo.yml`. Its coverage marks each cycle complete, capped (oldest trades of the window lost: a lower bound) or cut (window read again next cycle); a reader de-duplicates by `trade_id` across all files.
- This card reads ONLY rows inside its own development and held-out windows, which are fixed by a dated amendment the day the recorder's first rows land, before any row is read.
- Rule 17: KXMVE markets are also named by MVE1, NEWLIST1, USWEEP1 and USWEEP3 in the held-out registry. Reading this card's rows opens no window of those four cards, and any window of theirs still unread stays unread.
