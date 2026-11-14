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

## Dated note (Nov 14, 2026, 02:40Z): the nonstop tape recorder failed as merged; a fix spec for the owner (NOT built)

**What happened.** PR 921's recorder (`record-combo-tape.yml`) was sized from one quiet Sunday half hour, which was this desk's error. Main read its first hour (Friday evening, `tape/2026-11-14/0120-1`, from coverage, end.txt and file sizes only):
- All 59 cycles were capped, so the tape was incomplete.
- About 9,000 to 10,000 raw trades a minute, about 2,400 of them combos.
- About 84,000 distinct combos in the hour.
- No legs at all: the look-ups never fired and the queue sat at its cap.
- About 150 MB a day gzipped.
The Head and this desk asked Main to disable it.

**Fix spec, for the owner's decision. Nothing is built.** The freeze stands, and the Head recommends a cap of 4 requests a minute if it is approved.
- **Legs from creation, not by look-up.** `GET /markets?mve_filter=only&min_created_ts=<the last read>` lists newly created combos with `mve_selected_legs`, 1,000 a page. At an estimated 1,400 new combos a minute that is about 1.5 to 2 pages a minute. It gives every combo's legs once, traded or not, and replaces the per-ticker look-ups, which would need about 2,100 requests an hour.
- **Sampled complete tape minutes.** Read one whole minute of tape at a time, about 10 to 12 pages for a Friday-evening minute. Each sampled minute is complete or flagged.
- **Narrowed storage, joined in the recorder from the creation listing, with the join rule fixed in a hand case before any data:**
  - raw rows only for NO-taker combo trades, for NOTAKER;
  - for YES-taker trades, per 5 minute counts per leg (leg ticker and side): trades and contracts, for CROWDLEG's C(L).

**Request rate and what each card loses:**

| Cap | Legs (creation) | Tape | Share of minutes read whole | Requests a minute |
|---|---|---|---|---|
| 8 a minute (this desk's first proposal) | about 2 a minute | one whole minute in 2 | 50% | about 8 |
| 4 a minute (the Head's recommended cap) | about 2 a minute | one whole minute in 5 | 20% | about 4 |

- **At the 4 a minute cap:**
  - CROWDLEG's 60 minute C(L) becomes a count over 12 sampled minutes. The threshold of 10 must be re-registered (about 2 over the sampled minutes) by a dated amendment before any row is read, and its signal is noisier.
  - NOTAKER sees about 20% of NO-taker prints.
- **At a busier minute than 12 pages:** the sampled minute is flagged incomplete and counted, never read as quiet.

**Size, an estimate to be re-measured:**
- Raw NO-taker rows plus 5 minute leg counts plus the creation listing's legs: about 5 to 15 MB a day gzipped at either cap.
- The creation listing's leg strings dominate, at about 1,400 combos a minute.
- At 15 MB a day the cards' 42 days are about 0.6 GB, under the 1.2 GB stop.

**Feasibility, which may decide it before any build.** Forensics' inventory (`claude/forensics-desk` 1794f5ca, `DATA_INVENTORY_TABLE_NOV14.md`) finds only **2.3% of combo quote rows two-sided**. CROWDLEG's and NOTAKER's bet needs a NO ask of 20c to 50c with a spread of 4c or less on a listed combo containing the leg. If two-sided combos are that rare, the bets may never reach 100 in 21 days at any recorder rate.

So before any build this desk proposes a counts-only feasibility line on the existing `combo-data` quotes, with no result and no price beyond the two-sided flag and the spread band:
- how many listed combos per day are two-sided with a NO ask in 20c to 50c and a spread of 4c or less;
- how many of those carry `leg_tickers`.

If that is under about 5 a day, the recorder fix is not worth the owner's requests, and both cards close as "no evidence: combos cannot be priced".

## Closed for want of evidence (Nov 14, 2026, 02:41Z, on the Head of R&D's fixed rule): **no evidence: combos cannot be priced.**

- The feasibility count (counts only; reader audited CLEAN before the run; hand case first at a06cfe15) was run once on combo-data fedfd5e4. It found 0 qualifying combos (two-sided under rule 18, NO ask 20c to 50c, spread 4c or less) on the one complete day 2026-11-13 (45 polls, 18,000 sampled quotes, 455 two-sided), and 0 on the partial days.
- The average is 0.0, against the threshold of 5 fixed before the run. Auditor B's independent recount was equal (rule 16b). Their aggregate sanity check: 500 of 502 two-sided combos have a NO ask above 0.50; 2 are in the band, and neither has a spread of 4c or less.
- It reads as "no qualifying combo in 18,000 sampled quotes of one complete day": each poll lists 400 different combos.
- Print: `crowdleg/feasibility/FEASIBILITY_PRINT_2026-11-14.json` (ae8591b3). No result, volume or size was read, and no try was counted.
