# TIECOND1 stages 0 and 1: registration (written before any count)

Source protocol: `origin/claude/idea-desk-a:kalshi-scalper/workers/IDEA_DESK_A_PROTOCOLS.md`, P2, followed as written. Counts only. Zero Kalshi API calls. No P&L, no price, no candle is read.

## Data and cut
- Files (read-only sqlite, table `market`: ticker, series, open_ts, close_ts, result, strike): `alts2`, `alts3`, `alts4`, `rep`, `fxusd/candles`, `l1b`, `book`, `five`, `hist15/KXGOLD15M`; first file wins on duplicate ticker. `fresh.sqlite` is entirely frozen (F1) and is NOT opened.
- Frozen key F1: rows closing on or after 2026-10-05 00:00Z (1791158400) are never loaded for stage 0 or stage 1. Development = close_ts before that. The held-out third is not read here (stage 2 only, survivors only).
- Exception, existence only: the "windows during breaks, weekends, holidays" fact is counted from tickers and close_ts alone (no strike or result read), including Columbus Day Oct 12, which is frozen.
- Series: non-crypto only. FX (EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD), metals (SILVER, COPPER, PLATINUM, PALLADIUM, GOLD), energy (WTI, NATGAS, BRENT), rates (any rates series in `rep`; found by exclusion of the above and crypto). Crypto series are excluded.

## Stage 0
Per series, order by close_ts. Consecutive pair = close_ts(t+1) - close_ts(t) = 900 s and open_ts(t+1) = close_ts(t) (no gap). d = strike(t+1) - strike(t). Check result(t)=='yes' iff d >= 0. Report agreement rate per series; under 99.5% drops the series. If any tie (d == 0) has result 'no', STOP and flag (rule-text conflict, lie 4); do not flip a side.

## Stage 1
- tie(t) = (d == 0), on pairs that survive stage 0. tick = smallest positive |d| in the series' first 500 windows.
- Predictors known at the open of t: q8 = median |d| in ticks over the previous 8 contiguous windows (needs 8 contiguous prior pairs, d(t-1) uses strike(t) which is posted at the open of t); ties4 = ties in the previous 4 contiguous windows (needs 4); hour (UTC) and first_after_gap (no window in the previous 30 min) are defined and counted as descriptive only.
- Cells: group (FX, metals, energy, rates) x q8 tercile (cut points from the first third of each series' dates, development only; terciles pooled within group by each series' own cuts) = up to 12 cells; and group x ties4 (0, 1, 2 or more) = up to 12 cells. Windows with a gap behind them lack the predictor and are in no cell.
- Interval: Wilson 95% two-sided (z = 1.96) on tie rate per cell. Kill: CLOSED if no cell with n >= 300 windows has a Wilson lower bound >= 6%. One try. The best cell is reported either way. If any cell passes, STOP; stage 2 needs its own registration.
- Fact for the Chief of Staff: count of listed windows inside the daily break, on weekends (UTC Sat/Sun), Labor Day Sep 7 and Columbus Day Oct 12, per group. Break = windows whose open falls 21:00 to 22:00 UTC (CME hour; approximate and stated as such).

## Ledger
Adds 1 test (the kill gate). Deflation N 1,100,001 (z about 5.34) and 8,796 (z about 4.39). Nothing here claims an edge.

## Result (run after the push of this registration)
Script `workers/tiecond1_run.py`, tables `workers/TIECOND1_RESULT.json`. Deviation: the rates series (KX2YR/5YR/10YR/30YRRATE15M, in `rep`) close only on or after 10-05 so they have zero development windows; rates group is empty. Stage 0: agreement 99.98% (silver) to 100% on all 10 series, 0 ties settle NO, none dropped. Stage 1: 13 cells with n >= 300; best by lower bound: energy, q8 lowest tercile, n 1,984, tie rate 2.57%, Wilson lower 1.96%. Highest rate: FX ties4 = 2 or more, 18.2% (2 of 11, lower 5.1%), n under 300. No cell reaches the 6% lower bound: **CLOSED** (1 try). Existence counts (listed windows): break hour 21 UTC FX 423, metals 422, energy 336; weekend FX 231, metals 590, energy 400; Sep 7 metals 288, energy 192 (FX not listed yet); Oct 12 FX 480, metals 441, energy 192. So windows exist during holidays and breaks: arm B has something to test.

## RETIRED (Nov 12, 2026, POWER2 + main): TIECOND1 arm B retired (arm B is not registered anywhere; read as the tie rate in break, weekend and holiday windows): 300 to 600 windows are held but power is 0.00 unless the true tie rate is 8%. Stage 0/1 stay CLOSED. Reasons in workers/POWER2_QUEUE.md.
