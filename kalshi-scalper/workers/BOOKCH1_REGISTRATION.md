# BOOKCH1 registration: relative order book imbalance (or depth withdrawal) on the CHEAP side, 180 s before the close, Bitcoin and XRP 15 minute markets, recorder R6, FORWARD ONLY (V2 worker, 2026-11-03, research only)

Written and pushed BEFORE any outcome, win rate, PnL, trigger count or price of recorder R6 was computed or opened. What I read to write it: `workers/OICORE_SHAPE_INVENTORY.md`, `workers/DEPTH1_REGISTRATION.md`, `workers/candidates/README.md`, `src/scalper/fwdledger.py` (including `load_r6`), `src/scalper/r6tests.py` (column names and the loader only), `src/scalper/streaks.py`, three lines of `src/scalper/gen4.py` (the `imb` feature), and the README ledger. I opened no R6 `book.csv.gz`, `trades.csv.gz` or `coverage.csv.gz`. Owner brief: more strategies shaped like OICORE (cheap side, ask 0.05 to 0.50, 180 s before the close, about 28% win rate, held to settlement) with a trigger that is neither Bitcoin open interest nor price alone. Nothing here promotes anything; there is no promote verb.

## Ledger check: this exact trigger has not been tested

I grepped the README (about 8,200 lines) and the inventory for `imbalance`, `depth`, `withdraw`, `tertile`, `book15r6` and `BOOKCH`: no result, test or registration uses the order book's SIZES, oriented to the CHEAP side and made RELATIVE to the market's own trailing 24 hours, as the trigger of a held cheap-side trade. Closest two, and how this differs:

- **DEPTH1** (registered 2026-10-30, read from 2026-11-14): favourite side or implied side on EITHER side (the sign of a feature decides which side to buy, ask 0.10 to 0.90), ONE look at 480 s, 10 fixed features with absolute (not trailing-relative) signs and thresholds of zero, gold and Bitcoin, 20 tries. BOOKCH1 buys only the CHEAPER side (ask 0.05 to 0.50), at 180 s, triggers on a rank within the market's own trailing 24 hours, and covers Bitcoin and XRP. DEPTH1's `f1_imb5` is a close cousin of the primary here (it is a monotone transform of a 5 level YES versus NO size ratio) but it picks the side from the sign of the imbalance, at 480 s, so its trades and mine differ in side, time and band. Its `f6_thin_depletion` (the thinner side emptying over 60 s) is a cousin of the alternative here (cheap-side bids pulled over 180 s); not the same variable (thinner side, 60 s, 480 s look, sign-based). The two cards share the R6 data, so they are not independent evidence on the same days; I report the overlap of Bitcoin windows at the read.
- **GEN4** (recorder quotes, last ~150 s): `imb` there is `(bid size - ask size) / (bid size + ask size)` of the TOUCH only (level 1) of the one YES quote, one of nine base features in a grammar of thousands of generated rules, usually combined with spot momentum (Bitcoin), with discovery and validation thresholds fitted on history. BOOKCH1 uses five levels per side from R6 (both YES bids and NO bids), no spot input, no fitted threshold (the cut is a fixed rank of a trailing distribution), one primary definition, forward only.

It is not a rewording of OICORE (open interest) or of OIREL/OIDRIFT (open interest relative). It shares OICORE's trade, not its trigger.

## Family, counterparty, universe

- **Family.** Resting-order imbalance (primary) and cheap-side depth withdrawal (alternative) on the cheaper side of Kalshi's 15 minute markets at the 180 s look, held to settlement.
- **Counterparty hypothesis (stated before data, "none named" is allowed if the data does not support it).** Market makers who quote the cheap side withdraw their bids when they expect the cheap side to lose, and leave them when informed flow is about to hit the other side; the resting lottery-ticket bids that remain are a retail crowd. The two definitions point in opposite directions on purpose: the PRIMARY says heavy resting bids on the cheap side (relative to the other side) mark informed accumulation of the underdog by someone who knows the late move is coming (the trade is WITH that size); the ALTERNATIVE says a collapse in cheap-side bids marks an informed seller of the favourite and the cheap side is bought AFTER the makers leave (the trade is on the side the makers abandoned: weaker story, a contrarian read of the same data). The data can support the primary story only if the win rate on triggered entries exceeds the cheap side's ask by a margin larger than the fee in both halves. If it does not, the result file says **no counterparty named**.
- **Universe (fixed now on cost, liquidity and the L1-free rule only, no returns seen).** `KXBTC15M` (Bitcoin; OICORE's market and the cheaper side is the side OICORE would buy, so there is no hedge; overlap reported) and `KXXRP15M` (L1 has XRP paused in code). NOT Ethereum, Dogecoin or gold: L1 buys the favourite there and a cheap-side order in the same window could hedge an L1 position.

## Data source

Recorder R6 on `origin/quote-data`, `book15r6/<run>/`: `book.csv.gz` (columns `t_send_ms, t_recv_ms, server_date_header, ticker, series, close_time`, `yes_bid_px_1..5`, `yes_bid_sz_1..5`, `no_bid_px_1..5`, `no_bid_sz_1..5`, about every 2 s), `trades.csv.gz` (not used), `coverage.csv.gz`. Read through `scalper.fwdledger.load_r6` (source `r6`), exchange time by the R6T clock rule (offset from the Date header). The recorder ends 2026-11-13 23:59 UTC and is not extended by this card (the owner decides).

## The trigger (one primary, one alternative, both frozen in words and in `src/scalper/bookch1.py`)

Definitions at a window's look poll L = the last book poll at or before T-180 s that is no more than 10 s earlier than that (T = close time):

- YES ask = 1 - best NO bid; NO ask = 1 - best YES bid. The **cheaper side** is the one with the lower ask; equal asks or a missing best bid on either side means no trade. A bid on a side is a resting offer to BUY that side: YES bids are the YES side's bids, NO bids are the NO side's bids.
- **S5(side)** = sum of the recorded sizes of that side's bids over the (up to) 5 levels.

**PRIMARY (BOOKCH1): ratio R = S5(cheaper side) / S5(other side).** The window triggers when R is strictly above the 2/3 quantile (linear interpolation, the usual "type 7") of R over that market's windows that closed in the 24 hours before this window's look (close times from T-86,400 s to T-900 s, each window's R computed the same way at its own look, with its own cheaper side). It needs at least 48 such windows (half a full day); fewer means NoData, not a no-trade. S5(other side) = 0 gives no R and the window is left out of the history and not traded.

**ALTERNATIVE (BOOKCH1B, a separately counted second try): change D = (S5(cheaper side) at the look - S5 of the SAME side at the poll at or before T-360 s (no more than 10 s earlier)) / S5 at T-360 s.** The window triggers when D < 0 and D is strictly below the 10th quantile of D over the same trailing 24 hours of windows (same rule, same minimum of 48; the side is the cheaper side at the 180 s look in both polls; S5 at T-360 s must be above 0).

## The trade (both)

If the window triggers and the cheaper side's ask at the look is in [0.05, 0.50]: buy that side, 1 decision priced at 1 and 10 contracts, at the **first ask at or after look + 1.0 s** (R6T's "an order is live 1 s later" rule), within 20 s of that time. The fill ask must also be in [0.05, 0.50] and the displayed size at that ask must be at least 10 contracts (best opposite-side bid size: the YES ask size is the best NO bid size, the NO ask size is the best YES bid size); otherwise no trade. Held to settlement; no exit, no resting order. Fee 7% x C x p x (1-p), rounded UP to the cent per order, entry only, C = 1 and 10 (plus the ledger's x1.2 stress), the same as every ledger row. Missing look poll, missing fill poll, or too little history: NoData (the window is not counted as evaluated).

## Numeric prediction (written before any trigger count was seen)

All figures are for the PRIMARY, pooled over Bitcoin and XRP, per market where noted. Honest: these are estimates from structure, not from R6 data.

- **Eligible windows.** 96 windows a day per market, about 64% recorder coverage (DEPTH1's estimate), about 65% of recorded windows with the cheaper side's ask inside 0.05 to 0.50 and 10 contracts displayed; a tertile cut triggers about one third of eligible windows. Expected **about 13 triggered trades a day per market, about 20 to 26 a day pooled** (range 12 to 30). The ALTERNATIVE triggers about one tenth of eligible windows: **about 4 a day per market, 6 to 8 pooled**, so it will almost certainly be NOT_ENOUGH_DATA before the recorder ends.
- **Win rate 29%** (range 24% to 34%), mean entry ask about 0.27. **Payoff ratio (average win / average loss in cents) about 2.5** (average win about +71.6c, average loss about -28.4c at C = 10, fee included). **Profit factor about 1.05** (range 0.8 to 1.4), expected **FALSIFIED**; I put about 7% on PF 1.5 or better in both halves, and about 1% on clearing the deflated z bar. A flat result (PF about 1.0) is the modal outcome: the cheap side's price already tracks its chance, and R6 is the only data this was ever going to be tested on.
- **Streaks** (`scalper.streaks`, independent trades, a floor): at a 29% win rate in 100 trades the longest losing run has mean 11.0, median 10, **95th percentile 18, 99th percentile 22**; the chance of at least one run of 10 straight losses in 100 trades is **62%** (of 15 or more: 14%). A 10-loss run is ordinary here and is not a signal.
- **Worst single loss** (premium at the 0.50 cap plus fee, rounded up): **5 contracts $2.59** (250c + ceil(8.75c) = 9c), **10 contracts $5.18** (500c + ceil(17.5c) = 18c). Typical loss at an ask of 0.27, 10 contracts, is $2.84.
- **Overlap with OICORE** (OICORE: Bitcoin cheaper side after a 3 minute open interest jump above the threshold at 180 s). OICORE enters roughly 6% of Bitcoin windows (555 history entries, 23 forward windows evaluated in the first four days); if independent of the book ratio, about 6% of BOOKCH1's Bitcoin entries and about 3% of pooled entries are also OICORE entries. OICORE windows are busier with a cheaper cheap side, so the true share is probably higher: **expected 8% to 15% of Bitcoin entries, 4% to 8% of pooled**. It is measured at the read from the REF_GEN6_OICORE trades in the forward ledger (same ticker, same side) and reported with and without those windows. It never changes the verdict; a pass that is only the OICORE windows is called **paper only (overlaps OICORE)**.

## Freeze, windows, expected read

- **Freeze time: 2026-11-04T00:00:00Z** (the next UTC midnight after this commit, which is on 2026-11-03). Only windows closing strictly after it count (`close_ts > freeze`); the trailing 24 hour history may use R6 windows from before the freeze (they are only used to set the cut, never traded or scored). The candidate files are written and pushed only AFTER this registration is pushed, and are never edited after (a changed rule is a new id with a new freeze).
- **Expected read date: about 2026-11-12** (150 pooled primary trades at 20 to 26 a day needs 6 to 8 days after the freeze, and at least 7 trade days). The recorder ends 2026-11-13 23:59 UTC, so the last allowed read is 2026-11-14 00:00 UTC. If the recorder is stalled (GitHub skipped scheduled runs for hours on 2026-10-30) the primary may only reach about 100 trades: that reads NOT_ENOUGH_DATA, and the owner decides whether to extend R6.

## Kill rules (frozen)

On the PRIMARY, Bitcoin and XRP pooled (per-market rows are descriptive; the verdict is pooled; the alternative has its own verdict on its own pooled trades), at C = 10 and fee included:

- **NOT_ENOUGH_DATA:** fewer than 150 pooled trades at the read, or fewer than 7 trade days. Nothing is called.
- **FALSIFIED:** forward PF below 1.0 after 150 trades, OR PF below 1.5 in either of two equal halves (equal trade count, in time order), OR (at 1 contract) mean net per trade not above 0, OR PF at fees x1.2 below 1.0.
- **NOT_YET_FALSIFIED** only if none of the above and PF is 1.5 or better in both halves. Even then a result under the deflated bar is **not a pass**: the date-clustered z must reach about **5.27** (Bonferroni on N about 728,724, one sided, alpha 0.05) for anything stronger, and a result under it stays NOT_YET_FALSIFIED. A pass earns only a falsifier read (shuffled-trigger control, look-ahead audit, OICORE overlap) and a new registration, never a live order.
- **Frozen holdout rule:** the last third of the forward period by close time (the verdict cutoff is the read date) is the holdout; it is read once, at the verdict, together with the other two thirds, and counts only if its own PF is above 1.0. The ledger prints running numbers hourly, so the holdout is NOT blind: the rule binds the verdict only, and anyone who adjusts anything after seeing the running table invalidates the card.

## N accounting

Running N about 728,722 before this card (README, after XMET1). This card adds **2 tries** (the primary and the alternative; each is evaluated on Bitcoin and XRP together, and the per-market rows are not separate tries), so N about 728,724 at the read and the z bar stays about 5.27. Not tries: the trailing quantile choice (fixed, 2/3 and 10th), the 48 window minimum, the OICORE overlap split, the half/holdout splits.

## Code

`src/scalper/bookch1.py` (`look_stats`, `trailing_cut`, `decide`, `forward_eval`, evaluator `scalper.bookch1:forward_eval`) and `tests/test_bookch1.py` (synthetic data only). Candidates (written after this push): `workers/candidates/BOOKCH1_BTC.json`, `BOOKCH1_XRP.json` (primary), `BOOKCH1B_BTC.json`, `BOOKCH1B_XRP.json` (alternative). No R6 outcome was computed to write any of this.
