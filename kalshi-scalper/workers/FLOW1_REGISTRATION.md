# FLOW1 registration: cheap-side taker flow, 180 s before the close, Bitcoin 15 minute markets, on the whole public trade tape (V2 worker, 2026-11-03, research only)

Written and pushed BEFORE any flow, outcome, win rate or PnL of any window was computed. What I read to write it: the brief from the coordinator (lead S-FLOW1 from the refinement chat), `workers/OICORE_SHAPE_INVENTORY.md`, `workers/BOOKCH1_REGISTRATION.md`, `workers/MECH1_REGISTRATION.md` (tape fetch and taker side), `src/scalper/gen6.py`, `candlefield.py`, `api.py`, `rev1.py` (OICORE trigger helpers). Done before this commit, none of it outcome or flow: the date range of the local candle files, a count of how many windows have a cheap side priced 5c to 50c at the -180 s candle with a fill ask of at most 0.50 (candles only, no result column read), the tape endpoints (which dates return trades, one page of 3 raw trades printed to see the field names) and trade counts of 8 random windows (page count only, aborted by a 429). Owner rule (strict): cheap side only, ask 0.05 to 0.50; no favourite-side result is computed or printed anywhere in this card. This is a NEW discovery family approved by the owner (relayed Nov 3); the ban on 15 minute crypto candle triggers is lifted for THIS test only.

## The lead and what is fitted

The refinement chat's S-FLOW1, 146 R6 windows (Oct 29 to Nov 3): Bitcoin cheap side at 180 s, split by taker flow on the cheap side in the 3 minutes before the decision. LOW half (flow <= -0.036): n 76, win 36.8%, PF 2.54, +13.25c a contract; HIGH half PF 0.68; permutation p 0.0026. **The threshold -0.036 was chosen by the refinement chat on those 146 windows: it is a FITTED parameter** (about the median of that sample), not a prior. The refinement chat keeps its own forward read on windows from 2026-11-03: **this card uses NO window closing on or after 2026-11-03 00:00 UTC**, and touches no R6 label.

## Data

- **Prices and outcomes:** the local Kalshi candle files (`scalper.oicorex1.load_series`, the same files gen6 and OICORE use), windows of `KXBTC15M` closing in [2026-08-06 00:00 UTC, 2026-11-03 00:00 UTC). Candles on file begin on 2026-08-06. The tape reaches further back (see the result), but there are no candles before Aug 6 on file and this card does not fetch any.
- **Flow:** Kalshi's PUBLIC trade tape, keyless: `GET /historical/trades` for windows closing before 2026-09-04 (the cutoff `trades_created_ts`), `GET /markets/trades` after, the other endpoint if the first is empty (the cutoff has been seen to leave Sep 5 empty on /historical). Parameters `ticker`, `limit=1000`, `min_ts=close-360`, `max_ts=close-180`, cursor until exhausted, then the rows with `close-360 < created_time <= close-180` are kept. **No deduplication**: every row the endpoint returns is a trade and counts (trade ids are stored and the number of repeated ids is only reported). One polite fetcher (3 s wait on a 429, 0.4 s between pages, 2 threads at most), cache `~/.cache/flow1/tape.sqlite` (outside the repo), tracked per ticker in a `done` table. Fetch order is a seeded random shuffle (seed 36) of the windows listed below, so any partial fetch is a random sample.
- **Which windows are fetched:** exactly those where candles alone give a trade: the -180 s candle exists, the two sides' asks differ, the cheaper side's ask is in [0.05, 0.50], and the next candle (-120 s) exists with a fill ask of at most 0.50. That is 3,940 of 8,437 Bitcoin windows (about 44 a day), decided from candles, before any result is read.

## Definitions (frozen in words, and in `src/scalper/flow1.py`)

- **Signal candle** ends at close-180. Ask(YES) = its yes_ask close; ask(NO) = 1 - its yes_bid close. **Cheap side** = the side with the lower ask; equal asks, no trade. Signal ask must lie in [0.05, 0.50].
- **Entry:** buy the cheap side at the NEXT candle's ask (the candle ending close-120), **HARD LIMIT 0.50**: a fill ask above 0.50 means no trade (counted as a skipped window, not a loss). Held to settlement, no exit. Fee 7% x C x p x (1-p) rounded UP to the cent per order, C = 10 (per-contract cost = fee/10), `gen6.fee`. Also shown at C = 1 and at fees x1.2.
- **Flow.** Trades in (close-360, close-180]. For each trade, `taker_outcome_side` is the side the taker is LONG. With the cheap side identity `c` in {yes, no}: BOUGHT = sum of `count_fp` of trades with taker_outcome_side == c; SOLD = sum of `count_fp` of trades with taker_outcome_side != c (a taker buying the other side is a taker selling the cheap side, the same exposure). TOTAL = BOUGHT + SOLD (all contracts). **flow = (BOUGHT - SOLD) / TOTAL.** Antisymmetric under swapping the cheap side. If `taker_outcome_side` is missing the row falls back to `taker_side`; a row with neither is counted as unknown and is in TOTAL but in neither BOUGHT nor SOLD (reported if any). TOTAL = 0 (no trades): NoData, the window is not traded and not counted as evaluated.
- **LOW half:** flow <= -0.036 (takers net selling the cheap side). **HIGH half:** flow > -0.036. The threshold is FIXED and is not re-estimated on anything.
- **Mapping test:** `tests/test_flow1.py` builds synthetic trades for a YES-cheap and a NO-cheap window and checks that a taker "no" is a buy of the cheap side when the cheap side is NO and a sell when it is YES, that flipping the cheap side flips the sign, and that duplicate rows are all counted.

## Dates and windows rule

Range [2026-08-06 00:00, 2026-11-03 00:00) UTC, 89 days, cut in three equal thirds by CLOSE TIME: **D1** = first third (to 2026-09-04 16:00 UTC), **D2** = second third (to 2026-10-04 08:00 UTC), **HOLDOUT** = last third (to 2026-11-03 00:00). The exact integer cuts are `CUT1 = 1785974400 + 89*86400/3` and `CUT2 = 1785974400 + 2*89*86400/3` (start `1785974400`, end `1793664000`). D1 and D2 are the discovery halves for the kill rules. **The HOLDOUT is read ONCE, and only if the kill rules below do not fire on D1 and D2** (stricter than "both halves positive"; if they fire the verdict is FALSIFIED and the holdout stays unread). **R6 flag:** the lead came from R6 windows (Oct 29 to Nov 2). Every window closing on or after 2026-10-29 00:00 UTC is flagged; every table is shown with and without them (they sit inside the HOLDOUT). **Pass needs the holdout positive WITHOUT the R6 windows too.** Windows closing in the last day of D data are not special.

## Replication (separate, never pooled)

`KXETH15M` and `KXGOLD15M`, same fixed threshold -0.036, same definitions, same range, same cuts. The windows are selected the same way from their own candles (ETH 3,692, gold 3,285 fillable). They are fetched after Bitcoin; their fetch has a time box of 3 hours each, scored on the random prefix that is in. A replication is described, not thresholded: it is "SUPPORTS" if its low-half PF is above 1.0 and above its high-half PF in the pooled range and in both halves of a split at the midpoint, and otherwise "DOES_NOT_SUPPORT". Gold and Ethereum are series where L1 buys the favourite; this card buys only the cheap side and is research only.

## Numeric prediction (written before any flow was computed)

Given the fitted threshold, I expect shrinkage, a lot of it: the 146-window sample picked the cut that looked best.

- **Take-up:** 44 fillable windows a day; flow defined in about 97% of them; LOW half about 50% of those (the threshold is near the median, so the share could be 45% to 60%): **about 21 low-half trades a day (range 17 to 27), about 1,800 over the 89 days** (so NOT_ENOUGH_DATA is very unlikely on count).
- **Low half:** mean price paid about 0.27; **win rate about 30% (range 26% to 35%) against a price of 0.27 plus 1.5c fee**, i.e. net about **+1.5c a contract** (range -3c to +6c) and **profit factor about 1.2 (range 0.85 to 1.6)** in D1+D2 and **about 1.1 (0.7 to 1.5)** in the holdout. The lead's win rate 36.8% and +13.25c should shrink by about 85% of the gap to zero.
- **High half:** PF about 0.95 (range 0.7 to 1.2). **Low minus high** mean net about +3c (range -4c to +10c); permutation p (within-day shuffle) about 0.12, range 0.0005 to 0.9.
- Probability the kill rules do NOT fire on D1 and D2 (low-half PF at least 1.5 in both halves and low minus high positive in both): **about 10%**. Probability of clearing the deflated bar (z about 5.27): **under 1%**: a low-half net of +3c on 1,000 trades with per-trade sd about 0.45 gives z about 2 at best.
- **OICORE overlap:** OICORE (Bitcoin doi > 86,299.56 fixed) fires in about 40% of windows lately (the fixed threshold has drifted below the median) and about 6% to 10% over the whole period; I expect **8% to 15% of low-half trades to be OICORE windows** (OICORE windows are busier, so a bit more selling of the cheap side), and low-half PF to be higher inside them than outside.

## Kill rules (frozen)

On the LOW half, Bitcoin, C = 10, fees included, **D1 and D2 scored separately**:

- **FALSIFIED:** low-half PF below 1.5 in either D1 or D2, OR (low minus high mean net per contract) not positive in both D1 and D2, OR the pooled low-half mean net per contract not above 0 at C = 1, OR PF at fees x1.2 below 1.0 (D1+D2 pooled). Holdout unread.
- **NOT_ENOUGH_DATA:** fewer than 150 low-half trades in D1+D2 together (with the number of months to go stated), or fewer than 15 trade days in either half. Nothing is called.
- **NOT_YET_FALSIFIED:** none of the above; then the holdout is read once: its low-half PF must be above 1.0 and low minus high positive, with and without the R6 windows. Even then the deflated bar (date-clustered z of the low half about **5.27**, Bonferroni, N about 730,210 + this card) is separate: under it the status stays NOT_YET_FALSIFIED, never "pass" by itself. A pass at the deflated bar plus the holdout earns the capped probe spec below, nothing else; there is no promote verb.
- Reporting regardless of verdict: n, win rate against the price paid, PF, net per contract, by D1/D2, by calendar month and by R6 flag; windows a day; the HIGH half; the permutation p (one sided, the statistic is mean net low minus mean net high, 10,000 shuffles of the low/high label WITHIN each close date, seed 36); the date-clustered z (`calibration.cluster_mean_z`); the overlap with OICORE (fixed 86,299.56 and trailing 24 h p90 as in `rev1.trailing_p90`) and the low-half PF inside and outside OICORE windows; empty-tape windows; tape depth.

## Capped probe spec (only if D1, D2 and the holdout all pass, also without R6 windows)

Cheap side only, low-flow windows only, one contract, hard limit 0.50 on the fill, hold to settlement, entry at the candle ending 180 s before the close; kill rules, worst day and fills a day stated in the result from the data; handed to the coordinator for main. Nothing in this repo sends it.

## N accounting

Running N about 730,210 (coordinator). This card adds **+6**: the Bitcoin rule (+2), the Ethereum replication (+2), the gold replication (+2). Not tries: the D1/D2/holdout cuts, the R6 split, the OICORE overlap, the threshold (fixed from the lead; it is a fitted parameter of the refinement chat, said so above), fees x1.2 and C = 1 views.

## Code

`src/scalper/flow1.py` (candidate windows from candles, `fetch`, `flow`, `entries`, `score`; `score` refuses to read the holdout twice and refuses to run the verdict twice) and `tests/test_flow1.py` (synthetic only). Results: README.md and `workers/FLOW1_RESULT.md`.
