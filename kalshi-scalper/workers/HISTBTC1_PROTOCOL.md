# HISTBTC1 PROTOCOL (registered Nov 8, 2026, before any rule is scored)

Research only. No trading code, no key, no order, no fetching in this task (local sqlite). Real Kalshi candle quotes, so the entry is priced at the ACTUAL ask, not a model.
Caveat on every result: the data is Kalshi's /historical feed (Jun 3 to Aug 5 2026), a quote regime that may differ from today's (Oct to Nov 2026) book. A result here is a lead for the fresh-regime data, never a live figure.

## Question
Do rules on Kalshi's own 1 minute candle features (ask, bid, spread, changes, range, volume, open interest, hour) buy the CHEAP side (ask 3c to 30c) of KXBTC15M at a price below its fair value, after the fee, in each of three windows? Counterparty to name if anything survives: the taker who sells the cheap side after a flow that overprices it; no counterparty is claimed by this screen.

## Data (data/hist15/KXBTC15M.sqlite, ingested by src/scalper/hist15.py)
6,023 settled markets with candles, 65 close dates (2026-06-02 to 2026-08-05; days are 81 to 87 of 96 windows, a few windows have no candle). Development: closes before 2026-07-15 (43 dates, 22,502 cheap-side decision rows, W1/W2/W3 = 7,498 / 7,607 / 7,397 rows, thirds of the dev dates). Held out: closes 2026-07-15 on (2,079 markets, 22 dates), behind `scan.guard_check`, read ONCE. Only row COUNTS were looked at before this registration, no outcome.
Unseen beyond this: Dec 10 2025 to Jun 1 2026 (about 16,000 BTC markets listed, no candles fetched yet) and ETH, XRP, DOGE (not fetched).

## Entry and scoring (the harness, unchanged)
Adapter `hist_btc_cheap` (`scan.HIST_BTC`): look in {840, 780, ..., 180} seconds before the close, one contract, taker at the ask of the side bought (a NO buy at 1 minus the YES bid), ask 3c to 30c only (the `ask_lo`/`ask_hi` filter builds no other row), fee `ceil(0.07 x p x (1-p) x 100 - 1e-9)` cents, stress x1.2, held to settlement. Rule grammar, W1-only quantile cuts, floors (40 trades per window, 150 total, 3 dates per window) and the PF 1.5 in each of W1, W2, W3 bar are the harness's. The bar is the owner's and is not raised.

## Runs and N
3 runs of 10,000 distinct rules (seeds 81101, 81102, 81103), 30,000 rules, N 1,290,505 to about 1,320,505, one-sided Bonferroni z about 5.37. Every run appends to the ledger before scoring. No second dataset, no second try on this data after reading survivors.

## Audits and what happens next
Every survivor: `scan.py freeze` then `audit` (truncation, fee stress, placebo 1,000 permutations, plain-loop recompute, latency shifts, cluster dedupe). Only audited survivors, with deflated or not recorded, are frozen and read once on the held-out. Held-out labels: FALSIFIED (PF under 1.5), NOT_ENOUGH_DATA (under 50 trades or 5 dates), LEAD (holds, not deflated in development), CANDIDATE (holds and deflated).

## Prediction and kill criteria (before scoring)
Expected: ZERO survivors (about 85%): the cheap side's pooled baseline is about -5.5c to -6.2c per contract, and the BINPATH lesson is that cheap-tail results appear only where the price is modelled. If survivors appear they must also hold in a second read on the Oct 2026 fresh data before anything is claimed. Zero survivors closes this family on this data (NOT a statement about other regimes). Two NOT_ENOUGH_DATA in a row from this source closes it.

## What this can and cannot say
It can say whether rules on real Kalshi candle quotes beat the cheap-side price in Jun to Aug 2026. It cannot say anything about the current regime, depth, queue position, or fills larger than one contract. No promote verb.
