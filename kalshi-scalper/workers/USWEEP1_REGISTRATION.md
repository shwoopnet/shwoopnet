# USWEEP1 registration: universe sweep of every non-15-minute Kalshi series (written 2026-11-03, before any outcome of any rule was read)

Name note: first drafted as SWEEP1, which already belongs to the retired Oct 27 Bitcoin big-print study (`src/scalper/sweep1.py`, untouched). This study is **USWEEP1**; code `src/scalper/usweep1.py`.

Worker for "Strategy Research V2". Research only: public keyless data, no order, no live code, no promote verb.

## Already covered (carry the verdict, do not re-score)
- All 15 minute series (crypto, gold, forex, commodities, `fifteen_min`): excluded entirely. Cheap side and favourite there are C1 to C3, TAIL1, UNDER1, BOUNCE1, E3, E3C, COMM1, L1 and its whole family. FALSIFIED, or the live strategy.
- Favourites in long-dated non-sports non-price markets: FLB1 (28,005 markets, 24/72/168 h, all FALSIFIED, 72 h -1.83c z -2.43). Sports game-winner favourites: SP1 (-4.19c, z -2.79). Sports consistency locks: SPORTCONS1, ARB5. Locks across events: ARB1 to ARB4. Fee rounding: FEE1 (size reveals no edge). Lock rules: RULES1 (traps).
- The scout (Oct 22): generic L1 favourite at 60% of life on 76 hourly/daily/weekly series, no LEAD (pooled +0.16c); weather -0.38c to -4.7c (WX1, WX2, WX3 dead); gas ladders GAS1-F (read 2026-11-22); Brent daily too thin.
- Calibration scan (information): win rate equals ask within about 1c at every price.
USWEEP1 differs from these by (a) every series that clears the history rule, not a hand-picked family, (b) both tails, (c) fixed times to expiry per life class, (d) per-series walk-forward.
Prediction: the market is calibrated; about 25% of series x rule x look cells will be positive in both halves by luck alone, none will clear the deflated bar. Prior of a bar-clearing cell: 2%.

## Universe
Every series in Kalshi `/series` (15,663 on 2026-11-03). Skipped before counting: 16 `KXMVE*` parlay collections (combinatorial, no stable resolution) and the 38 `fifteen_min` series. For the rest the census lists settled markets closing in the last 60 days (the live `/markets` cutoff; older markets are in `/historical`, not used), at most 2 pages of 1000. Census records resolution frequency (median anchor minus open), volume per market and market count; results are NOT stored in the census file. Time budget caveat: the census reads recurring series (hourly, daily, weekly, monthly, quarterly) first, then custom, one_off and annual in list order, under the shared API limit; the report states how many of the 15,609 were reached.
Local data reachable and noted but not used for scoring (different windows and looks): `data/*.sqlite` (flb1, sports, weather, e3b, ladders, fresh, ...), `quote-data` branch (15 minute and BTC ladders only).

## Eligible series (fixed by structure, no outcome)
At least **300 settled markets** and **20 distinct close dates** in the 60 days, median life above zero. At most the 600 most recent markets of a series are used. Life class by median (anchor - open): H up to 4 h, D up to 3 days, W longer. Anchor = `expected_expiration_time` when present else `close_time`; a market already closed (or not yet open) at the look is not tradeable and is dropped.

## Rule grid
Looks T before the anchor: H {30, 15, 5} minutes (1 minute candles); D {24 h, 6 h, 1 h}; W {72 h, 24 h, 6 h} (hourly candles). The decision quote is the last candle ending at or before the look and no more than one candle period earlier, two-sided and valid (0 < bid < ask < 1). Taker at the ask (YES at yes_ask, NO at 1 - yes_bid), held to settlement.
- **tail**: the side whose ask is in 0.05 to 0.15 (the cheaper if both).
- **fav**: the side whose ask is in 0.85 to 0.97 (the dearer if both).
Fee 7% x C x p x (1 - p) rounded up to the cent at C = 10, per contract. Stress: fee x1.2.
Cells per series: 3 looks x 2 rules = 6. **N added = 6 x (number of eligible series), recorded in the series file `workers/USWEEP1_SERIES.json` before candles or results are fetched.** Running N before: about 728,735. Deflated bar = one-sided z at 0.05 / N_total (5.27 at 728,702); also quoted: the sweep-only bar at 0.05 / (6 x series).

## Walk-forward
Per series the sorted distinct anchor dates of its sampled markets are split: first two thirds development, **last third frozen: never downloaded as candles or results and never scored here**. Development is cut by date into halves A and B. Frozen markets stay for a later forward read only.

## Readout and kill rules (fixed now)
A cell is a LEAD only if: n >= 100 in development, n >= 40 in each half, net per contract after fee > 0 in BOTH halves, positive at fee x1.2, day-clustered z (pooled development) >= 2.0, and positive on the subset whose decision candle traded (volume > 0). Ranked by min(half nets) then z. A LEAD is a reason to run a forward probe, never evidence of an edge. Verdict words: a cell reaches NOT_YET_FALSIFIED only with deflated z at or above the running bar; otherwise leads are NOT_ENOUGH_DATA (clear the half and fee screens but not the bar) and the sweep is FALSIFIED as a family if no cell clears the bar. Flag separately any LEAD with a stated mechanism (named counterparty). Run once; the series file and rule grid are not changed after the first outcome.
Candidate JSON (top 5 leads): forward-only, `stage: discovery`, frozen-third dates unread, 1 contract capped probe, kill at 40 fills with PF under 1.0, worst day stated.

## Amendment 1 (2026-11-03 14:05 UTC, before any outcome of any rule): census cap
The shared API limit (429s, other workers) gives about 25 series a minute, so reading all 15,609 would take about 10 hours. Rule: the census reads tier 0 first (hourly, daily, weekly, monthly, quarterly series, sorted by ticker), then the rest in ticker order; it is **stopped at 14:50 UTC or when it finishes, whichever is first**, and the series reached by then are the universe actually swept. Not-reached series are reported as NOT TESTED (cause: API rate limit, not any outcome). The selection, thresholds, looks, rules and fee are unchanged. N added = 6 x eligible series, written to `workers/USWEEP1_SERIES.json` (committed before any candle or result is fetched). Local resume: `USWEEP1_CACHE=<scratchpad>/sweep python3 -m scalper.usweep1 census` (resumable), then `select`, `fetch`, `score`.
