# GEN4 registration: a strategy generator on SECOND-resolution books in the last 150 seconds (Strategy Research V2, research only)

Written 2026-10-29 by worker GEN4 and pushed BEFORE any result file was read and before any strategy was generated or scored. The only look at `origin/quote-data` before this commit was the file list and the CSV headers (structure, no prices read into any statistic, no `results.csv` row read). Data commit for discovery: `origin/quote-data` at `b7dc9cbe823b2b9f734dc085ea03452a1aec3c1b`. Code: `kalshi-scalper/src/scalper/gen4.py` (written after this file).

## Ledger check (why this is not a reworded tested idea)

Every earlier generator (GEN1, GEN1S, GEN2, GEN3, AUTO1 to AUTO3) used ONE MINUTE candles, entries 840 to 180 s (GEN3: 3,300 to 180 s) before the close, and no book sizes. None could see the last 150 seconds, the size at the touch, or a 5 to 30 second move. The recorder studies on this data were single rules, not a search: RECORD1 (model vs quote lag, registered read not yet due), BTCAVG (fair value from the partly known average, NOT_ENOUGH_DATA, 4 tries), LATECAL (favourite calibration by band, NOT_ENOUGH_DATA), QUOTE1 (passive two-sided quoting), LAG2/LAG2B (spot lead on trade history, FALSIFIED). GEN4's spot features overlap RECORD1 and BTCAVG in spirit (spot vs strike); they are building blocks here, not the rule, and the gates decide. **Owner's ban on L1 and its variants:** buying the favourite at 88c to 97c near the close is excluded by construction: every GEN4 entry has a side ask between 0.03 and 0.85 inclusive (the same cap AUTO3 used), whatever the conditions say.

## Universe (chosen on time and cost only)

Bitcoin `KXBTC15M` and gold `KXGOLD15M`, separately. Every window in the recorder with a `results.csv` row (yes or no). Each window is counted once (the first folder that holds it). Ethereum, Solana, XRP and Dogecoin are in the files and are NOT used.

## Date split, fixed now (UTC, by the window's close time)

- **DISCOVERY:** windows closing before 2026-10-27 00:00.
- **VALIDATION:** windows closing 2026-10-27 00:00 to 2026-10-29 23:59:59. Not built, not read, until the discovery survivor list is frozen and its sha256 committed. Read ONCE, from the then-latest `quote-data` commit (its hash goes in the result).
- **FORWARD:** windows closing at or after 2026-10-30 00:00, scored automatically by the forward ledger (FWDLEDGER) from the candidate files.

**Gold has no discovery rows under this split** (gold's 15 minute market is recorded from the 2026-10-28 15:45 UTC job on), so gold is `NOT_RUNNABLE` in this run. The same grammar and gates are registered now for a later gold run on its own split, not read in this job: GOLD-DISCOVERY = gold windows closing 2026-10-28 15:45 to 2026-11-03 23:59, GOLD-VALIDATION = 2026-11-04 00:00 to 2026-11-06 23:59, GOLD-FORWARD after. (Gold days on 10-28 and 10-29 were already seen by LATECAL and GOLDFILL; disclosed.)

## Grammar (every strategy is exactly one of these)

- **Side:** YES, NO, FAV (the side whose mid is above 0.5 at the poll), DOG (the side whose mid is below 0.5). Side-relative quantities: YES ask = `yes_ask` with size `ask_size`; NO ask = 1 - `yes_bid` with size `bid_size`; YES bid = `yes_bid` (size `bid_size`); NO bid = 1 - `yes_ask` (size `ask_size`).
- **Entry window** [hi, lo] of seconds left, hi > lo, both from {150, 120, 90, 60, 45, 30, 20, 10}.
- **1 to 3 conditions**, each `feature >= q` or `feature <= q`, q a decile (10th to 90th) of that feature over all eligible DISCOVERY poll rows of the market (features only, no outcome). Features, all known at the poll and computed only from polls and spot ticks received at or before it:
  - `ask`, `bid` (side), `spread` (yes_ask - yes_bid), `lsz_ask`, `lsz_bid` (log1p of the size at the side's ask and bid), `imb` ((size at side bid - size at side ask) / sum),
  - `dm5`, `dm15`, `dm30`: change of the side's mid since the last poll at or before t - 5, 15, 30 s,
  - Bitcoin only, from the spot proxy (median of the last Coinbase, Kraken and Bitstamp trade prices received within 5 s, per second, as BTCAVG): `sp5`, `sp15`, `sp30` (log return in bp over 5, 15, 30 s, signed toward the side: + for YES, - for NO), `zd` ((proxy - strike) / (sigma x proxy x sqrt(seconds left)), signed toward the side, sigma the standard deviation of 1 s log returns over the previous 120 s, at least 60 of them), `edge` (Phi(zd) - side ask), `vol` (that sigma, in bp per sqrt second).
  A missing feature fails its condition.
- **Eligibility of a poll:** status active, 0 < yes_bid <= yes_ask < 1, side ask in [0.03, 0.85], at least 1 contract at the side ask, seconds left in [lo, hi].
- **Entry:** the FIRST eligible poll in the window where every condition holds; at most one entry per window per strategy. **Fill:** at that poll's side ask (the quote is received at or after the signal; no earlier quote is ever used). **Latency variant:** filled instead at the NEXT poll of that market (received strictly later, before the close) at its side ask with at least 1 contract there, whatever the price; no fill if there is none.
- **Exit:** HOLD to settlement, or SELL at the side's bid at a fixed X seconds left, X in {90, 60, 30, 15, 5} and X < lo: at the first poll received at or after close - X (within 5 s); a bid of 0 or under 1 contract or no such poll means the contract is held to settlement (counted and reported).
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order, on the entry and on a sale (settlement has no fee). Scored at C = 1 (the screen) and C = 10 (min(10, size at the ask) bought; min(that, size at the bid) sold, the rest held), and at fees x1.2.

## Generation and counting

Seeded random draws (seed 4) from the grammar until **5,000 distinct** Bitcoin strategies or 300,000 generated, whichever is first. Distinct = at least 20 discovery trades and an entry set (window, side) whose Jaccard with every kept strategy that has the same exit is at most 0.9. **N added = 2 x generated** (each strategy is read with two fill models), all counted whether distinct or not.

## Screens (gold and Bitcoin separately)

- **DISCOVERY pass:** PF at C = 1 at least 1.5, at least 40 trades on at least 4 dates, net at fees x1.2 above 0. Survivors frozen (`studies/gen4_survivors_FROZEN_2026-10-29.json`, sha256 in the commit message and in the result) and pushed before validation is built.
- **VALIDATION pass (read once):** PF at C = 1 at least 1.3 on at least 20 trades on at least 2 dates, net at fees x1.2 above 0, and the latency variant PF at least 1.0.
- **Family control (registered kill rule):** the validation pass rate of discovery FAILURES with at least 40 discovery trades is the control. If the survivors' validation pass rate is not at least 5 points above the control, discovery carried no information and the family is reported `FALSIFIED` as a whole (the individual validation passes still go to the forward ledger, labelled so).
- **RULES bar (information):** PF 1.5 in each of three windows after fees, positive at x1.2, deflated z about 5.17 for N about 439,000 + GEN4's. With about 150 discovery and 110 validation windows no single rule here can show that z; every survivor is at best `NOT_ENOUGH_DATA` against the RULES bar until FORWARD adds windows. Nothing here is a candidate in the owner's sense; the falsifier comes later.

## Counterparty (who would pay, if anything passes)

Late-window quoters on Kalshi who refresh more slowly than the spot price moves (spot and distance features), and takers who cross a thin book in the last two minutes (size and imbalance features), selling a contract below what the next 5 to 150 seconds make it worth. The book is one-sided 72% of the time at 30 s left (BTCAVG), so most late entries are not available at all.

## Numeric prediction (before the run)

Bitcoin: 150 to 300 strategies pass discovery out of 5,000 (with 40 to 150 trades a PF of 1.5 arises by chance often); 20% to 35% of survivors pass validation, within 5 points of the control rate, so the family is `FALSIFIED` by the control rule (prior about 75%). The best validation PF above 2 on fewer than 40 trades. Forward will shrink every survivor toward PF 1.0. Gold: `NOT_RUNNABLE` in this run.

## Kill criteria

Fewer than 100 Bitcoin discovery windows = `NOT_ENOUGH_DATA` for the run. A strategy failing a gate is `FALSIFIED` at that gate. The family control rule above. Rules, thresholds and splits are not changed after any outcome is read.
