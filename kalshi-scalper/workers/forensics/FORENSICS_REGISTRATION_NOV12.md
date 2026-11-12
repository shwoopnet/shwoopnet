# Live-Data Forensics Desk: registration (2026-11-12, written and pushed BEFORE any recorded row was opened)

Research only. Public recorded market data only (recorder R6, `book15r6/` on the `quote-data` branch). Zero Kalshi requests. No live account figure of any kind is in this file or any file of this desk: the bot's own orders are not read, used or reconstructed. Nothing here changes an order, a rule or a size, and nothing is promoted.

What I read before writing this: `CLAUDE.md`, `docs/RND_CHARTER.md`, `docs/STRATEGY_LIFECYCLE.md` (7b to 7g, the declined list), the queue on `rnd-queue`, V2's `POWER2_QUEUE.md`, `V2_HANDOFF_NOV12.md` and the DEPTH1, BOOKCH1, QSTALE1, MAKERTAIL1, CFRTI1 files, Desk A's `DESK_A_HELD_DATA_NOV12.md`, Refinement's registrations (MAKERREPLAY1, holdvssell, esfeat, SPOTLEAD1, R6 final read note), `functions/kalshiLiveLib.js` (`runExitWatch`, `exitBody`, `EXIT_THRESHOLD`, `EXIT_SLIPPAGE`), `scripts/record_15m_book.py` (column names). I opened no `book.csv.gz`, `trades.csv.gz` or `coverage.csv.gz`.

## Date constants (fixed; not computed from the data)

- Block D (first read): windows whose `close_time` is from 2026-10-29T00:00:00Z up to and including 2026-11-04T23:59:59Z.
- Block H (second read, read ONCE, after D's output is committed, with no rule changed in between): `close_time` from 2026-11-05T00:00:00Z up to and including 2026-11-08T23:59:59Z.
- Nothing closing on or after 2026-11-09T00:00:00Z is used (that block is frozen for V2's DEPTH1; a row for a later close found in a run file is dropped on its `close_time` before anything is computed).
- No rule below has a tunable parameter chosen on D. D and H are two periods of one pre-specified measurement; results are reported for D, H and pooled. If any rule is changed after D is seen, H is void for that rule and the report says so.
- READ-ONCE MARKER (replaced by a committed line after each read): `EXITREPLAY1 D: READ ON 2026-11-12 (results/EXITREPLAY1_D.json)`, `EXITREPLAY1 H: READ ON 2026-11-12 (results/EXITREPLAY1_H.json, after commit 4d9e54f)`, `ENTRYREPLAY1 D: READ ON 2026-11-12 (results/ENTRYREPLAY1_D.json; one run died on a data-type bug before printing anything, fixed, no rule changed)`, `ENTRYREPLAY1 H: READ ON 2026-11-12 (results/ENTRYREPLAY1_H.json, after commit 4d9e54f)`.

## Common data rules

- Book rows: `t_recv_ms` is the poll time; the book is `yes_bid_px_1..5`, `yes_bid_sz_1..5`, `no_bid_px_1..5`, `no_bid_sz_1..5`. YES ask = 1 - best NO bid; NO ask = 1 - best YES bid. A poll is usable only when both best bids are present and YES bid < YES ask.
- Result: the `result` column of `coverage.csv.gz` (`yes` or `no`). A window with no result, with `max_gap_ms` over 15,000, or with no usable look poll is dropped and counted.
- Tape: `created_time`, `yes_price_dollars`, `count_fp`, `taker_outcome_side` (the side the taker BOUGHT).
- Fees: taker 0.07 x p x (1 - p) per contract, unrounded (primary), and rounded up to the cent on a 10 or 15 contract order (shown). Settlement has no fee. Maker fee 0 on these series (stated assumption; a 25% of taker sensitivity is shown).
- Cash basis, per contract. PF = gross wins / gross losses. Intervals by resampling whole windows (seed 20261112, 2,000 draws); for pooled series, by resampling close times so that markets closing together move together.
- Labels: under about 100 trades the label is "no evidence at n = x"; FALSIFIED only at about 100 or more.

## Test 1: EXITREPLAY1, the 25c early sell replayed on the recorded books

**Question.** L1's exit sells when its side's bid is at or below 25c, with an immediate-or-cancel order that may go 15c below the bid it saw, from a loop that looks about every 10 seconds. Refinement measured on the live record that early sells filled below their trigger. On the public books: how much of that gap is the 10 second loop, how much is the book, is the trigger sometimes a pulled bid rather than a repriced market, and does selling fetch more or less than holding, on a larger public sample than the live record?

**Population (a public twin of L1's entries, not the bot's orders).** One synthetic entry per window: the look poll is the last usable poll received at or before close - 360 s and no more than 10 s before that. If one side's ASK is in [0.88, 0.97], that side is bought at that ask (a fill is assumed: an upper bound). Primary series `KXGOLD15M`. Secondary, for mechanics only: `KXBTC15M`, `KXETH15M`, `KXXRP15M`, `KXDOGE15M`, shown per series and pooled as "crypto" (L1 does not trade them; the exit code is the same).

**Trigger event.** The first usable poll after the entry, before the close, at which the bought side's best bid is above 0 and at or below 0.25.

**Measurements (descriptive, 0 tries).**
1. Count of entries, count and share of trigger events, seconds left at the trigger.
2. Live-like sale: detection on a 10 second grid (five phases 0, 2, 4, 6, 8 s from the window's first poll, averaged), detected at the first grid time at or after which a usable poll shows the bid at or below 0.25 (the poll at or just before that grid time); the sale executes on the first usable poll at least 1.0 s after the detection poll, walking that poll's bid levels 1 to 5 down to a limit of (detected bid - 0.15), for 1 and for 15 contracts. Reported: detected bid, sale price, filled share, and the gap split into (0.25 - detected bid) and (detected bid - sale price).
3. Instant sale: the same with detection at the trigger poll itself (a 2 second watcher).
4. Hold counterfactual on the same events: the settlement value of the side (1 or 0) against the live-like sale less the taker fee. Statistic: mean of (hold - sell) per contract over events, with its interval. This repeats, on books, a question the owner has already decided (GOLDHOLD is on the declined list): it is reported as the cost of the exit's mechanics only, and nothing here proposes holding.
5. Pulled-bid share: events where, at the trigger poll, the same side's ask is 0.40 or more (a spread of 15c or more), and events whose bid is back above 0.25 at the first usable poll at least 10 s and at least 30 s later.
6. The twin's cash PF per contract over all entries (entry at the ask plus the taker fee) under: the live-like exit, hold, and the variant below. Shown for D, H, pooled. Favourite-late: diagnostic only, never a candidate.

**Variant V1 (1 try): the two-sided confirm.** The trigger additionally needs the same side's ASK to be at or below 0.35 at that poll (so the other side's bid is 0.65 or more: the market has repriced, the bid was not merely pulled). Everything else as the live-like sale. A version of Gold L1's exit, not a strategy (lifecycle 7g): it needs no uniqueness check, it is not on the declined list (it is not a hold, a price floor, a resting entry or a size rule), and its parent is Gold L1.
- Bar (information only): on gold, mean cash per trigger event under V1 better than the live-like exit by 1.0c or more with the 95% interval above 0, on 60 or more events. Fewer than 60 gold events: "no evidence at n = x" (the crypto series are shown beside it and cannot rescue it).
- Prediction: gold events in D plus H about 15 to 40; pulled-bid share under 15%; V1 difference inside noise. Chance of meeting the bar: under 5%.

**Counterparty side (1 try, counted for honesty; NOT a candidate).** On each trigger event, the first usable poll at least 2.0 s after the trigger poll: buy the same (collapsed) side at its ask if that ask is at or below 0.35, hold to settlement, taker fee. Cash PF, n, mean per contract, gold alone and all five series pooled. This is the buyer's side of the stop: it says whether the people who buy what the stop sells are paid for it. It is a cheap-side price-path rule, a family closed by evidence (lifecycle 7e), so whatever it shows it is reported as a measurement of the exit and goes to the Chief of Staff for a ruling; it is not put forward as a strategy by this desk.
- Prediction: pooled PF 0.85 to 1.10.

## Test 2: ENTRYREPLAY1, cheap-side entry execution on Bitcoin in OICORE's entry window (no open interest condition)

**Question.** OICORE buys the cheaper Bitcoin side as a taker (fee plus a limit 1c above the touch). At the recorded books, would a resting (maker, zero fee) buy at the bid have filled, at what saving, and which fills does it get? Also: how often does a taker limit miss at realistic delays, and what do the missed windows do?

**Population.** `KXBTC15M` only. Look poll L: the first usable poll received at or after close - 178 s and no more than 10 s after that. Cheaper side = the side with the lower ask (equal asks: no trade). In band if that ask is in [0.08, 0.50]. This is OICORE's price band and time WITHOUT its open interest trigger (open interest is not in the held files), so it is the baseline population, not OICORE.

**Taker comparators (descriptive, 0 tries).** T0: buy at the ask at L. T1 and T5: an immediate-or-cancel limit of (ask at L + 0.01) arriving at the first usable poll at least 1.0 s (T1) or 5.0 s (T5) after L; it fills at that poll's ask if that ask is at or below the limit and the size shown there is 10 or more, else no fill. Reported: fill rate, price paid, cash PF of the filled set, and the win rate against price of the unfilled set.

**Maker rule M (2 tries: pessimistic and optimistic queue).** At the first usable poll at least 1.0 s after L (time t0), rest a buy of 10 contracts on the cheaper side at that side's best bid P at that poll, until close - 60 s, then cancel. Queue ahead Q0 = the size shown at that bid at t0.
- A tape trade after t0 and before close - 60 s in which the taker bought the OTHER side at our price level (for a YES bid at P: `taker_outcome_side` = `no` and `yes_price_dollars` = P; for a NO bid at P: `taker_outcome_side` = `yes` and `yes_price_dollars` = 1 - P) consumes the queue at our level. A trade of that kind THROUGH our level (YES bid: `yes_price_dollars` < P; NO bid: `yes_price_dollars` > 1 - P) fills us in full.
- PESSIMISTIC (the verdict): nobody ahead ever cancels; filled contracts = min(10, max(0, volume at our level - Q0)), or 10 on a trade through.
- OPTIMISTIC (information): Q0 = 0.
- Filled contracts are held to settlement; cash per contract = result - P (maker fee 0). The order's result is the sum over its filled contracts.
- Reported: share of orders with any fill, contracts filled, win rate against price paid, cash PF (contract-weighted), mean cents per resting order and per filled contract, D, H, pooled, and the T1 taker result on the same windows.
- Bar (pessimistic): PF 1.3 or better on 100 or more filled orders pooled, D and H each 1.0 or better, and mean per filled contract above the T1 taker's on the same windows. Under 100 filled orders: "no evidence at n = x". PF under 1.0 at 100 or more: FALSIFIED. Otherwise NOT_YET_FALSIFIED, a lead only: any use would be a version of OICORE's entry (parent OICORE) or a liquidity-provision card, and either needs its own registration, the Verification Analyst and the owner.
- Prediction: pessimistic fill rate 40% to 70%; pessimistic PF 0.75 to 1.05; T1 taker PF 0.85 to 1.00; a resting buy is filled when the price is falling (the MAKERTAIL1 and MAKERREPLAY1 shape). Chance of meeting the bar: about 10%.
- Ledger check: MAKERREPLAY1 (Refinement) was gold favourites, closed; MAKERTAIL1 (V2) was hourly-ladder tails at 15c or less; MMMAP1 (Desk A) measured one-minute markouts, not held outcomes with a queue. No test has replayed a resting cheap-side entry on the 15 minute Bitcoin book with the tape as the fill model.

## Deflation

Tries added by this registration: 4 (V1, the counterparty side, M pessimistic, M optimistic). The shared count is about 1.1 million (z bar 5.34); nothing here can reach that bar on ten days of data, so the best possible outcome of either test is a lead or a cost figure, never a pass.

## Classification cards

`EXITREPLAY1-V1 | version of Gold L1 (exit execution guard; parent Gold L1) | n/a (changes no entry, size or stop level) | Idea (version)`

`ENTRYREPLAY1-M | resting cheap-side buy at the bid, hold to settlement (closest existing: OICORE's entry; MAKERTAIL1) | low win rate, loss = price paid, 10 contracts | Idea (measurement of the baseline population)`
