# NOTAKER: follow the rare NO taker on a combo leg (Idea Desk C, Nov 13, 2026)

**Written before any combo price, trade or result was read for scoring.** The Verification Analyst ruled it NEW as a signal on Nov 13: the same family as CROWDLEG (combo-tape flow joined to legs) but a separate try. A card for the Head of R&D's read, not registered. Combos are paper only. [research]

`NOTAKER | family: combo-tape flow joined to legs (with CROWDLEG); the informed-side print; a look at each recorder poll, hold to settlement | risk class: NO at 20c to 50c, 1 contract, paper only | stage Idea | prior about 1%`

## Mechanism, and the other side

- **Who buys NO.** On Kalshi combos the taker almost always buys YES: combos are lottery demand. A taker who BUYS NO is rare, and may know something about one leg, such as a late injury, a lineup or a weather call.
- **The bet:** after a NO-taker print, other listed combos that contain the same leg (same ticker and side) may still be quoted as if nothing changed.
- **The other side:** the maker that has not yet updated that leg in its other quotes.
- **Honest counter (the Verification Analyst's flag):** the premise, that makers are slow to update a changed leg, is the lag claim INGAMELAG1-M tested and closed on Nov 12. It found no lag at one minute resolution, and the drift was under cost in every sport. At the recorder's 30 minute poll, with leg tickers on only the first 100 quote rows a run, the premise cannot even be resolved yet. The prior is low for that reason.

## Data (and what is missing)

The same gap as CROWDLEG: legs for every traded combo, all combo trades (not the top 15), and a finer poll. Nothing can be scored until the recorder change is sized (Main's trial, `jobs/CROWDLEG_TAPE_TRIAL.json`) and made.

## The rule (proposed, frozen at registration, never before)

- **Trigger:** a combo trade whose taker side is NO (from `taker_outcome_side`), joined to that combo's legs.
- **Bet:** at the first poll after the print, for each listed combo created before the print that contains at least one of the printed combo's legs as chosen:
  - buy NO if its NO ask is 20c to 50c and its spread is 4c or less;
  - at most 3 combos per print, 1 contract each, held to settlement;
  - fill at the ask seen plus the rounded fee; a void is a fee-only loss, counted as a bet.
- **The band is inside the owner's combo exception** and is not favourite-and-hold (the Verification Analyst).

## Numeric prediction, kill lines, windows

- **Zero-try count first, once the recorder change has run 14 days:** NO-taker prints and qualifying combos. Below 100 qualifying combos, it closes with "no evidence".
- **Prediction:** NO-taker prints are a few a day at most. Most are hedges, not information. Development cash PF 0.7 to 1.2.
- **Bar:** the parlay rules first (10c per dollar of paper edge over 100 settled combos), then the research bar (PF 1.5 in three windows, z 5.46, clustered by US Central day).
- **Kill:** fewer than 100 bets, PF under 1.0, or a half under 1.2.
- **Windows:** forward, the same as CROWDLEG: development = the first 21 days of the widened recorder; held-out = the next 21 days. The dates are written by a dated amendment the day the change lands.
- **Held-out line for HELDOUT_REGISTRY.md:** `| NOTAKER | Idea Desk C | idea-desk-c:kalshi-scalper/workers/idea_desk_c/NOTAKER_CARD.md | Kalshi combos (combo-data, after the recorder change) | Development = first 21 days of the widened recorder; held-out = next 21 days, read once on the Head's go (dates fixed by amendment) | to be fixed | NOT READ | card text | card only; same family as CROWDLEG; needs the recorder change |`

## Uniqueness checks (lifecycle 7d), and the declined list (7e)

1. **Signal: NEW** (the Verification Analyst): the informed-side print on the combo tape. It is one family with CROWDLEG, a separate try.
   - Closest: CROWDLEG (volume concentration), INGAMELAG1-M (the lag premise, closed), and taker flow on the 15 minute tape (declined; a different tape).
2. **Entry and exit:** a poll-time look and hold, on combos no live or shadow rule trades.
3. **Correlation:** none with any live strategy.
4. **Declined list:**
   - not a lock, parity, cheap-side sweep, market making or time-of-day;
   - 15 minute taker flow is another tape;
   - the band is within the combo exception;
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

## Closed for want of evidence (Nov 14, 2026, 02:41Z, on the Head of R&D's fixed rule): **no evidence: combos cannot be priced.**

- The feasibility count (counts only; reader audited CLEAN before the run; hand case first at a06cfe15) was run once on combo-data fedfd5e4. It found 0 qualifying combos (two-sided under rule 18, NO ask 20c to 50c, spread 4c or less) on the one complete day 2026-11-13 (45 polls, 18,000 sampled quotes, 455 two-sided), and 0 on the partial days.
- The average is 0.0, against the threshold of 5 fixed before the run. Auditor B's independent recount was equal (rule 16b). Their aggregate sanity check: 500 of 502 two-sided combos have a NO ask above 0.50; 2 are in the band, and neither has a spread of 4c or less.
- It reads as "no qualifying combo in 18,000 sampled quotes of one complete day": each poll lists 400 different combos.
- Print: `crowdleg/feasibility/FEASIBILITY_PRINT_2026-11-14.json` (ae8591b3). No result, volume or size was read, and no try was counted.
