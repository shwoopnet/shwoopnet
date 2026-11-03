# USWEEP2 registration: a faster, broader universe sweep (Strategy Research V2, research only; written 2026-11-03 before any candle was downloaded and before any outcome of any rule was read or computed)

Code `src/scalper/usweep2.py`, tests `tests/test_usweep2.py` (reuses `usweep1` functions, which are not edited). No live code, `functions/`, L1 or OICORE; no promote verb.

## Disclosure
Read so far: listing structure only (ticker, event, open, close, expected expiration, volume, early-close flag) from the bulk `/markets` endpoint. `result` is not stored by the crawl. Nothing scored. The exact per-series census (stage B) stores results in a separate file (`census_results.jsonl`) that `select()` never reads; it runs only after this file is pushed.

## Step 1 enumeration (measured)
Per-series census (USWEEP1) reached 1,753 of 15,663 series at about 21 a minute. Bulk `/markets?status=settled&min_close_ts&max_close_ts&limit=1000&mve_filter=exclude` needs no series list; a series ticker is the event ticker before the first "-". `/historical/cutoff` is 2026-09-04, so the live endpoint holds everything of interest. Measured: 1,000 markets a page, 4 to 10 pages per hourly window, about 5 to 7 pages a minute under the shared 429s (about 5,000 to 7,000 markets a minute), so 60 days of all markets is not reachable (about 7 million markets). Rule: **stage A** crawl the last **72 contiguous hourly windows (3 days)**, non-parlay; **stage B** one exact 60-day settled listing (one page of 1000) for each series with at least 15 markets and 2 close dates in stage A (15,609 series are in scope; the rest are not reached and the count is reported). A series that closes less often than about every 3 days is not found; it could not reach 20 close dates in 60 days anyway.

## Eligible set (by rule, structure only)
In stage B: at least **300 settled markets and 20 close dates in 60 days**, median life above zero, **median volume per market at least 100 contracts** (no dead books), not in `USWEEP1_SERIES.json`, not KXMVE, not `fifteen_min`, not 15 minute crypto or gold. Life class H up to 4 h, D up to 3 days, W longer (as USWEEP1).

## Sample, sized to the rate limit
Candle fetches run at only a few calls a minute, so: per series at most **30 markets with the smallest md5(ticker)**; anchor dates sorted, last third frozen (never fetched), first two thirds development, halves A and B by date. If eligible series x development markets exceed **1,200 candle requests**, series are taken in descending median volume until the budget is used; the rest are reported as NOT TESTED (cause: candle budget, not any outcome). One candle request per market covers all three looks.

## Rule grid, readout and kill rules
Identical to USWEEP1: looks H {30,15,5} min, D {24 h, 6 h, 1 h}, W {72 h, 24 h, 6 h}; tail = side ask 0.05 to 0.15; fav = side ask 0.85 to 0.97; taker at the ask, held to settlement, fee 7% x C x p x (1-p) rounded up, C = 10, stress fee x1.2. Quote = last candle ending at or before the look, at most one period earlier, two sided.
**LEAD** only if n >= 100 in development, n >= 40 in each half, net per contract > 0 in both halves and at fee x1.2, day-clustered z >= 2.0, and positive on the traded subset. A claim of an edge needs z at the deflated bar (one-sided 0.05 / N_total, about 5.27); otherwise leads are NOT_ENOUGH_DATA, and the sweep is FALSIFIED as a family if no cell clears the bar. Cells positive in both halves with n >= 40 per half are listed (top 5 as watch-only JSON, no promote); a mechanism-bearing cluster is an observation, not a lead. Run once; series file, rules and sample are not changed after the first outcome.

## N rule
N added = **6 x (series actually tested)**, written in `workers/USWEEP2_SERIES.json` before candles or results are fetched; the coordinator keeps the running total (about 730,013 before this).

## Numeric prediction
Market calibrated: pooled favourite net -1c to -3c, tail -0.5c to -1c; about 25% of cells positive in both halves by luck; at most a handful with n >= 40 per half; no cell reaches the deflated bar (prior of a bar-clearing cell 2%).

## Amendment 1 (2026-11-03, owner decision relayed by the coordinator; before any candle was downloaded and before any outcome was read, computed or printed)
**The favourite half (ask 85 to 97c) of the rule grid is DROPPED.** The Oct 28 rule is held strictly: no buy-the-favourite-and-hold research on any underlying. USWEEP2 is **tail only** (side ask 0.05 to 0.15, three looks per life class, taker at the ask, held, same fee). `usweep2.entries_for` is a tail-only copy of the USWEEP1 function (usweep1.py and its `fav` rule untouched); no favourite entry is built, no favourite candle look is scored, and no favourite result is computed or printed. **I have not scored or printed any favourite result (nothing has been scored at all).** The LEAD rule, thresholds, sample, budget and N rule are otherwise unchanged. **N added = 3 x (series actually tested)** (3 looks x 1 rule), not 6 x. Census note (structure only): stage B was slow (about 7 to 10 series a minute), so it counts candidate series busiest first by their stage A count and is stopped by count or time; series not counted are reported NOT TESTED (rate limit, not any outcome).
