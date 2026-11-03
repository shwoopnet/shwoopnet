# CALIB1 registration: a pooled, event-level calibration surface of the CHEAP side (2026-11-03)

Registered before any outcome was aggregated. Discovery only: no live code, no `functions/`, no L1, no OICORE, no promote verb.
**Owner rule (strict): cheap side only, ask 3c to 30c.** No entry above 0.30 is built, counted, scored or printed; the code asserts it (`calib1.py`, `extract` and `score`). No favourite-side (high price) calibration exists anywhere in this study.

## Why
USWEEP1/2/3, NEWLIST1 and the other candle tests found that series-level cells almost never reach n >= 100 outside sports (USWEEP3's lesson: "non-sports need an event-level design"). Meanwhile the candle caches already hold thousands of cheap-side entries with outcomes. CALIB1 pools them and clusters by EVENT (all strikes and markets of one event are one cluster, a stricter unit than the day for these ladders). It fits nothing: no model, no threshold search, no look search.

## Data (cached only; no new Kalshi fetch)
- USWEEP1 cache (`candles.jsonl`, `outcomes.jsonl`, `census.jsonl`): 210 series, development markets only.
- USWEEP2 and USWEEP3 caches (`candles.jsonl`, `census.jsonl`, `census_results.jsonl`): development markets only.
- `data/newlist1.sqlite` (hourly candles, results, category): markets closing before `data/newlist1_cuts.json` t2 only (its frozen third H is dropped by close time and was never read).
- Frozen thirds untouched: checked before registering that 0 cached markets of USWEEP1 (37,690), USWEEP2 (1,200) and USWEEP3 (1,285) fall on a frozen date (`split_dates`, same samples as the original scripts).
- A market appears once per look; the same (market, look) from two caches counts once, first source wins (sweep, us2, us3, newlist1).

## Entry (one per market, look)
Looks are each cache's own (USWEEP: minutes before the anchor by life class H 30/15/5, D 1440/360/60, W 4320/1440/360; NEWLIST1: 1h, 3h, 6h after listing and 3h before close). No look is added or chosen. Quote = latest candle at or before the look (within one candle period) with a two sided quote (0 < bid < ask < 1). The side whose ask is in [0.03, 0.30] is bought at the ask and held to settlement (YES ask, or NO ask = 1 - bid; at most one side qualifies). Fee = 7% x C x p x (1-p) rounded up to the cent, C = 10, per contract. Net = win - price - fee. Recorded per entry: Kalshi category (Elections merged into Politics), life class (anchor - open: H up to 4h, D up to 3d, W longer), look-to-close bucket (<=1h, 1-6h, 6-24h, 1-3d, >3d), ask bucket, outcome, fee, event id (`ticker` without its last `-` part), close time.

## Pre-registered grid: the ONLY claims
Category x ask bucket, at most 8 x 5 = 40 cells. Ask buckets: 3-5c, 5-10c, 10-15c, 15-20c, 20-30c (lower edge in, upper edge out, 0.30 in the last). The 8 categories are the 8 with the most independent events among cheap entries (counts only; no outcome had been aggregated), fixed in `workers/CALIB1_CATEGORIES.json`: Climate and Weather (1,631 events), Economics (854), Sports (702), Financials (134), Commodities (111), Politics (46), Entertainment (31), Crypto (21). Mentions (5 events) is below the cut and is not a claim. Entry counts at registration: 16,041 entries, 3,535 events, 12,479 markets.

Statistic of a cell: mean net per contract after fee, with an event-cluster bootstrap 95% percentile interval (resample EVENTS with replacement within the cell, 2,000 draws, mean = total net / total contracts, seed 20261103).

Split (discovery / validation): within each cell, events sorted by earliest close time (ties by event id); the first half (k // 2 events) and the second half. Each half gets its own interval.

**Decision rule.** A cell is a LEAD only if, in BOTH halves, mean net > 0 and the interval's lower bound > 0 after fees, with >= 30 independent events in each half. A cell with fewer than 30 events in either half is NOT_ENOUGH_DATA. Anything else is NEGATIVE_OR_NO_EDGE. The whole grid is reported, none hidden. **N charged +1 per cell reported (40).**

What a LEAD means: a place to look with a mechanism-bearing registered test on new data, never a trading rule. A 95% interval over 40 cells is far below the ledger's deflated bar (z about 5.27 at N about 730,000), so a LEAD here can easily be luck of the 40; it earns a pre-registered, mechanism-named forward test and nothing else. Entries within one day or one regime are also correlated across events, which the event cluster does not remove; each LEAD is also reported with its number of distinct dates.

## Headline (descriptive, charged nothing, no verdict attached)
The pooled calibration curve: win rate minus price (and net after fee) by ask bucket, by life class (H, D, W) and all together, each with an event-cluster interval; the 8-category grid's per-cell win rate vs price; categories outside the grid and look-to-close buckets as observations. Question answered: where is the cheap side least bad, where most mispriced, and is any lower bound near break-even. Nothing is fitted, selected or tuned on these tables.

## Prediction (before any aggregation)
Pooled net is negative in every ask bucket (cheap side wins less than it costs, as NEWLIST1 and USWEEP3 found), roughly -2c to -6c per contract. Most of the 40 cells are NOT_ENOUGH_DATA or negative; zero or one cell passes the LEAD rule, and if one does it is most likely a Sports or Economics ladder cell with heavy event overlap.

## Kill and stop rules
No kill condition on data: it is read once (`score` refuses a second run; `workers/CALIB1_RESULT.json`). If the extract stage and the grid disagree on entry counts, the result is withdrawn and rerun with a disclosed fix.

Code `src/scalper/calib1.py`, tests `tests/test_calib1.py` (synthetic data only).
