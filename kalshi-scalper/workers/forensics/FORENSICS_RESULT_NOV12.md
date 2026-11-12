# Live-Data Forensics Desk: ranked questions and the first two results (2026-11-12)

Research only. Public recorded market data (recorder R6, `book15r6/` on `quote-data`). Zero Kalshi requests. No live account figure is in this file: the bot's own orders were not read, used or reconstructed. Registration: `FORENSICS_REGISTRATION_NOV12.md` (commit 36df325, pushed before any recorded row was opened). Scripts: `r6load.py`, `exitreplay1.py`, `entryreplay1.py`. Raw output: `results/`. Run with `python3 -I <script> <data_root> <D|H|POOLED> <out.json>`.

**Read-once record.** Block D (closes 2026-10-29 to 2026-11-04) read on 2026-11-12 and committed (4d9e54f) before block H (closes 2026-11-05 to 2026-11-08) was opened; H read once on 2026-11-12; no rule changed between them. Nothing closing on or after 2026-11-09T00:00Z was used. One descriptive figure (the paired resting-minus-taker cost) was added to the entry script after both reads; it is arithmetic on the same rows and is marked as such.

**Coverage.** The recorder missed some runs: 3,397 windows are listed for the five series in D plus H (Bitcoin 737 of about 967 possible), 5 dropped for no result, 23 for no look poll. Gold is closed at weekends, so it has 117 synthetic entries in ten days.

**Tries counted: 4** (V1, the counterparty side, maker pessimistic, maker optimistic). Add 4 to the shared count. Nothing here is near any bar and nothing is a pass.

## Summary in five lines

1. **Entry cost (Bitcoin, cheap side, 3 minutes left): a resting buy at the bid saves about 1.5c a contract against a taker buy, and it fills 98.6% of the time.** This is a cost saving for OICORE's entry, not a strategy.
2. **The baseline itself flipped between two adjacent weeks:** buying every cheap Bitcoin side at 3 minutes was PF 1.39 in D and PF 0.61 in H (about 175 trades each). Any cheap-side Bitcoin record of under a few hundred trades has to be read against the same-week baseline, not against zero.
3. **Exit: the gap under the 25c line is the price jumping through the line.** It is not the book (thousands of contracts within 15c) and not the loop's speed (a 2 second watcher does no better).
4. **The stop never fired on a pulled bid** (0 of 103 events), and about a third of triggers were back above 25c within 30 seconds.
5. **Selling against holding after a trigger: no evidence either way** (gold n = 10; all five series +4.6c a contract for holding, interval -3.3c to +14.0c, n = 103). Nothing here proposes holding; the owner has decided that question.

## Ranked forensic questions (8)

| # | Question | Why it is worth the time | Data | Status |
|---|---|---|---|---|
| 1 | Entry execution on the cheap Bitcoin side in OICORE's window: resting against taker | The taker pays the spread and the fee on every entry; this is a mechanical cost, not a filter | Held (R6 books and tape) | **Run (Test 2 below)** |
| 2 | The 25c early sell on the recorded books: what makes the gap under the line, pulled bids, sell against hold, the stop's buyers | The exit is the whole loss side of the favourite rule | Held (R6) | **Run (Test 1 below)** |
| 3 | OICORE's trigger against the SAME-WEEK baseline, and the resting entry on trigger windows only | Result 2 shows the baseline alone swings from PF 1.39 to 0.61 week to week; the trigger's worth is the difference from that, and the resting saving must be checked in the minutes the trigger fires (the price is moving then) | Needs the list of model trigger windows (tickers; derived from public candles, not a live figure). Not in the repo; Refinement holds an open interest cache. Zero Kalshi requests if the list is passed | Next, as its own registration |
| 4 | A public twin beside the live record: which signals the bot took, which it missed and what the missed ones did | Splits a weak stretch into "the rule was weak" and "the execution was weak" | Needs live order rows by message (ticker, side, filled or not, price). Never committed | Waits on the Chief of Staff |
| 5 | Weekly baseline monitor for each live population (cheap Bitcoin at 3 minutes; gold favourite at 6 minutes) | A reading tool: every live result gets its same-week baseline beside it | R6 holds Bitcoin and Ethereum to Nov 20 and gold to Nov 13; after that it needs candles (Kalshi reads) or a recorder decision by the owner | Cheap; scripts exist |
| 6 | Whipsaws of the stop: can a book field at the trigger tell a bounce from a collapse | A third of triggers bounce; a guard would be a version of the exit | Not powered on gold: 10 gold events in ten days, about 60 needed | Parked |
| 7 | EVENT830's entry minute on the non-crypto books: spread and size shown at the release-day look | The probe trades 1 contract in thin markets at one known minute | `nc-data` holds these series only from Nov 11; about ten release windows by Dec 23 | Accruing |
| 8 | Fee rounding by order size (arithmetic only) | A 1 contract order pays a whole cent or two where the unrounded fee is under one; at 10 or more contracts the excess is under 0.1c a contract | None needed | Already read by Refinement (nothing to change); listed so it is not re-run |

Not on the list because it is already closed: resting entries on gold (MAKERREPLAY1), the gold price floor, holding gold to settlement (declined by the owner), second-of-minute send timing (CRONCLUSTER1), book imbalance as a signal (DEPTH1 and BOOKCH1 are V2's registered tests), spot lead and settlement-index replication (SPOTLEAD1, CFRTI1).

## Test 1: EXITREPLAY1 (the 25c early sell replayed on the books)

A synthetic favourite entry per window (ask 0.88 to 0.97 at 6 minutes), then the exit as the code sends it: trigger when the side's bid is at or below 25c, seen by a 10 second loop, sold one second later into the book down to 15c below the bid seen. Cents per contract. Intervals 95%, resampling close times.

| | Gold | Four crypto series | All five |
|---|---|---|---|
| Synthetic entries (D + H) | 117 | 878 | 995 |
| Favourite won | 94.9% | 91.8% | 92.2% |
| Trigger events (share of entries) | 10 (8.5%) | 93 (10.6%) | 103 (10.4%) |
| Median seconds left at the trigger | 88 | 117 | 106 |
| Bid at the first 2 second poll under the line | 21.8c | 21.2c | 21.2c |
| Ask at that poll | 22.9c | 22.8c | 22.8c |
| Bid the 10 second loop sees | 19.1c | 17.5c | 17.7c |
| Sale price, 15 contracts | 20.0c | 17.8c | 18.0c |
| Seen bid minus sale price | -0.9c | -0.2c | -0.3c |
| Median contracts bid within 15c at the trigger | 3,922 | 2,190 | 2,285 |
| Events with a pulled bid (ask 40c or more) | 0 | 0 | 0 |
| Back above 25c after 10 s / 30 s | 20% / 33% | 36% / 36% | 34% / 35% |
| Side won after the trigger | 40% | 22.6% | 24.3% |
| Hold minus sell, per event | +15.7 (-8.4, +43.1) | +3.4 (-4.7, +12.4) | +4.6 (-3.3, +14.0) |
| 2 second watcher minus 10 second loop, per event | -4.0 (-15.5, +3.1) | -0.2 (-2.7, +2.1) | -0.5 (-3.2, +1.7) |
| V1 (two-sided confirm) minus the live exit | 0.0 | 0.0 | 0.0 |

**Reading.**
- **The gap under the line is a jump, not a cost that code can remove.** At the first poll under 25c the bid is already about 21c to 22c, and the 10 second loop sees about 18c to 19c. The sale then gets the seen bid or slightly better: the book is deep, 15 contracts never walk it, and the one second of delay costs nothing measurable. Order size is not the cause.
- **A faster loop does not help.** A 2 second watcher sells at a higher price (about 20c to 21c) but also sells more of the bounces that the slower loop sometimes misses; net it is level or worse. No evidence for spending compute on a faster exit watch.
- **V1 is closed.** The trigger never fired on a pulled bid: in every one of 103 events the ask was about 1.5c above the bid. V1 changed no outcome. The registered bar could not be read on gold (n = 10, "no evidence at n = 10"), but a guard that changes nothing in 103 events across five series is not worth a version test.
- **Sell against hold: no evidence at these counts.** Gold: n = 10. All five: holding was better by 4.6c a contract per event, interval -3.3c to +14.0c. With about one entry in ten triggering, that point estimate is about half a cent per entry. The sign agrees with EXIT1 (candles); the size is not established. The owner has declined holding gold; this is recorded as the measured cost of the exit and nothing more.
- **Public twin, cash PF per contract** (entry at the ask plus the fee, a fill assumed, so an upper bound): gold with the exit 1.09 (0.62 to 2.55), gold held 1.39 (0.72 to 4.44), n = 117: no call possible. The four crypto series with the exit 0.79 (0.60 to 1.08), held 0.83 (0.62 to 1.17), n = 878: the favourite rule lost after fees on them in these ten days, which is in line with their being paused. Favourite-late: diagnostic only, never a candidate.

**Counterparty side (1 try; a measurement of the exit, not a candidate).** Buying the collapsed side at its ask two seconds after the trigger and holding: gold n = 10, no evidence; all five PF 1.11 (0.59 to 1.90), n = 97, mean +1.8c (-7.4c to +12.2c); D 0.85 and H 1.59. No evidence that the stop's buyers are paid for it. It is a cheap-side price-path rule in a family closed by evidence; this desk does not put it forward.

## Test 2: ENTRYREPLAY1 (cheap-side entry on Bitcoin at 3 minutes, no open interest condition)

The baseline population of OICORE's price band and time (cheaper side, ask 0.08 to 0.50, look at 178 seconds left), Bitcoin only. Cents per contract; cash PF.

| | D (Oct 29 to Nov 4) | H (Nov 5 to 8) | Pooled |
|---|---|---|---|
| Windows in band | 178 | 171 | 349 |
| Mean ask at the look / spread | 25.5c / 0.9c | 27.4c / 0.9c | 26.4c / 0.9c |
| Cheaper side won | 33.1% | 19.9% | 26.6% |
| Taker at the look ask (T0): PF | 1.39 (0.99 to 1.90) | 0.61 (0.40 to 0.87) | 0.95 (0.73 to 1.21) |
| Taker, limit +1c, 1 s later (T1): filled / PF | 80.9% / 1.43 | 75.4% / 0.52 | 78.2% / 0.91 |
| Taker, limit +1c, 5 s later (T5): filled / PF | 74.7% / 1.53 | 70.8% / 0.76 | 72.8% / 1.11 |
| Resting buy at the bid, pessimistic queue: orders filled | 98.3% | 98.8% | 98.6% (344 of 349) |
| Resting, pessimistic: PF | 1.55 (1.09 to 2.13) | 0.65 (0.42 to 0.92) | 1.03 (0.79 to 1.32) |
| Resting, optimistic: PF | 1.54 | 0.68 | 1.05 |
| Resting minus taker T0, same windows, per contract | +1.6 (+0.4, +2.6) | +1.4 (-0.1, +2.6) | **+1.5 (+0.6, +2.3)** |

**Verdict on rule M by the registered bar: NOT MET** (pooled PF 1.03 against 1.3; H is under 1.0). It is not under 1.0 pooled on 344 filled orders, so the registered label is NOT_YET_FALSIFIED, but read it plainly: as a strategy it is the cheap-side baseline with a cheaper entry, and the baseline is about 1.0. **It is a cost saving, not a strategy.**

**What is solid.**
- **The bid gets traded through.** In 98% of windows a trade printed THROUGH the best bid of the cheaper side within the two minutes after the look, so a resting buy fills in full even with the whole displayed queue ahead of it (median 2,020 contracts). Queue position is not the constraint in this market at this time; price movement is.
- **The saving is about 1.5c a contract** on a contract of about 26c: 2.25c of spread and fee saved on the fills, less 0.73c given up on the 1.4% of orders that never filled (4 of those 5 won: the misses are runaway winners). The same sign in both blocks. In PF terms on this population it is about +0.08, which is under the 0.10 margin a version needs to take over (lifecycle 7g). A 25% maker fee would take 0.3c of it.
- **The taker limit misses a fifth to a quarter of signals** at a 1 to 5 second delay. Whether the missed ones are better is not stable: at 1 second they won more than their price (36.8% at 29.9c), at 5 seconds they did not.

**What it means for OICORE (honest limits).** This is the baseline, not OICORE: open interest is not in the held files, so the trigger windows could not be picked out. Two things follow. First, the baseline alone swung from PF 1.39 to 0.61 between adjacent weeks, so a short OICORE record says little unless it is set beside the baseline of the same days (question 3). Second, the resting saving has to be re-measured on trigger windows before anyone builds on it: when open interest is jumping the price is moving, and the cost of the missed runaway winners may be larger there.

## What could become a live probe, and what is only a cost saving

- **New strategy for a live probe: none.** Nothing in either test is a strategy. The baseline is about 1.0, the exit variants change nothing, and the stop's buyers show no premium.
- **Cost saving, real but modest: a resting entry for OICORE** (rest at the bid for up to two minutes instead of an immediate order at the ask plus 1c). About 1.5c a contract on the baseline. It is a VERSION of OICORE (parent OICORE), so it needs: question 3 first (trigger windows only), then a version test beside the parent, then the owner. It also needs a kind of order the bot does not send today (a resting order with a cancel), which is an engineering and safety change in its own right, not a parameter.
- **No change indicated for the exit.** Not the loop's speed, not a guard, not the order size.
- **A reading rule worth adopting at no cost:** quote every cheap-side Bitcoin result beside the same-week baseline (question 5).

## Caveats

Ten days, one regime, with gaps in the recording. The twin assumes a fill at the ask. The resting model fills in full on any trade through the level and assumes the order was in the book one second after the look; it ignores the engine's own rules (the slot does not enter under 120 seconds). The live-like exit model uses the last 2 second poll before each 10 second grid time and averages five phases; unsold contracts are held. Sub-cent prices near the extremes are compared with a tolerance. Maker fee 0 is the stated assumption for this series. Nothing here was checked by the Verification Analyst.
