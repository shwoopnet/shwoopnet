# RETAILFRAC1 stage A and CRONCLUSTER1 stage A: registration (Nov 12, 2026)

Written and committed BEFORE any tape, book or coverage file was loaded. Source protocol: `IDEA_DESK_A_PROTOCOLS.md` P3 and P4 (branch `claude/idea-desk-a`), followed as written. Zero Kalshi API calls; held data only (`origin/quote-data:book15r6/`, every date and HHMM folder present at run time, extracted into a scratch dir, never committed).

Frozen-window key (`DATA_INVENTORY.md`): F11 says windows closing after 2026-10-30 00:00Z are the GEN5 forward set, read automatically through the candidate file. Stage A loads NO outcome column, no price path to settlement and no P&L; it is a flow-composition and timing census, so it does not read the forward result. The `result` column of coverage is used only as a presence flag (non-empty or not) to apply the protocol's window filter, and is dropped immediately; its value is never tabulated.

## P3 stage A rules (verbatim in substance)
- Window filter: coverage row has a result (presence only), `tape_sum_count` within 1% of `volume_fp` (the sum of tape `count_fp` per ticker vs `volume_fp`), `max_gap_ms` under 10,000.
- `frac(trade)`: `count_fp` differs from its nearest integer by more than 0.001. Signed YES-direction size: +count_fp if `taker_outcome_side=='yes'` else -count_fp. T = `close_time`.
- Per series and overall: (1) share of trades and of contracts that are fractional; (2) median and p90 size of each class; (3) fractional share of contracts by minutes to close (15 one-minute buckets) and by UTC 4 hour block; (4) YES share of each class's contracts, and mean price paid for the side bought, by class (price paid = yes_price if taker side yes else 1 - yes_price); (5) per-window correlation between net fractional flow and net whole flow over (T-600 s, T-360 s], summarised per series (mean and median of the per-window Pearson... defined as the Pearson correlation ACROSS windows of the two nets; windows with no trade of either class count as 0).
- KILL (CLOSED, 1 try): fractional share of contracts under 2% or over 98% in EVERY series, or item 5 above +0.8 in EVERY series.
- Stage B thresholds (`f_min`, `w_min`, development median of |net flow| over (T-600,T-360], development = closing before 2026-11-08 00:00Z) would be fixed by stage A, but stage B is NOT run here. Stage B is justified only if stage A shows two clearly different crowds (my operational reading, fixed now: kill gate does not fire AND item-5 correlation is below +0.5 in at least 3 of 5 series AND the fractional share is between 5% and 95% in at least 3 series AND the two classes differ in size, p90 ratio of at least 3 or YES-share gap of at least 5 points). If met, I register stage B in a separate commit and report to the parent before running it.

## P4 stage A rules
1. Contracts taken by second of the minute (0 to 59 of `created_time`, UTC), per series and per minutes-to-close bucket. `peak = (contracts in seconds 0 to 9) / (total x 10/60)`. Interval: 1,000 bootstrap resamples of whole windows (fixed seed 20261112), 2.5th to 97.5th percentile.
2. From the book: for every minute boundary inside a window, size at each side's best ask and spread at the last snapshot in seconds 52 to 59, against the first snapshot in seconds 8 to 15. (YES ask = 1 - no_bid_px_1, size = no_bid_sz_1; NO ask = 1 - yes_bid_px_1, size = yes_bid_sz_1; spread = 1 - yes_bid_px_1 - no_bid_px_1.) Ratio = mean after / mean before, per series, with the window bootstrap interval.
3. Report `peak` and depth ratio for gold at 6 to 7 minutes to close and Bitcoin at 2 to 3 minutes, beside all-window figures.
- Reading: FINDING only if `peak` >= 1.3 with an interval clear of 1 AND touch depth lower after the boundary than before. Anything less: "no cluster", closed. No try is counted.

## Ledger count
Tests added to the shared ledger (about 1,100,000, z about 5.34; lenient N 8,795, z about 4.39): P4 stage A adds 0 (measurement). P3 stage A adds 1 only if its kill gate fires and closes the card; otherwise 0 until stage B. Stage B, if ever run, adds exactly 1 (the pooled five-series line); that moves neither bar at the shown precision (z 5.34 and 4.39 both unchanged to two decimals).

## One pass
The script writes a marker file; a second scored run refuses. Results are appended below.
