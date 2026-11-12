# MMMAP1 (registered Nov 12, 2026, before the script is run on any real book or trade row): where a maker's realized spread is positive, across the recorded 15 minute books
Source: Idea Desk A, protocol P8 (`origin/claude/idea-desk-a`, commit 5a42976, `workers/IDEA_DESK_A_PROTOCOLS.md`). A MEASUREMENT, not a strategy: no try is counted (N tried: 0 new; ledger unchanged), no simulation, no fill model, no order, zero Kalshi API calls, no network (git reads of recorder branches only). Script `src/scalper/mmmap1.py`, test `tests/test_mmmap1.py`. Run with `python3 -I`. The script refuses to run until this file is committed, clean and on `origin/claude/epic-ptolemy-0amjd9`.

## Why
The earlier maker work found negative markouts on the fast books (Q2B on the hourly Bitcoin ladder, 30 second markout -0.3c to -1.5c; R6T on the 15 minute crypto and gold books, -0.2c to -1.0c). Nobody has measured the slow books (NC15, recording since Nov 11). If MMSIM1 passes on its Nov 24 read the next question is "where else"; if it fails on adverse selection the next question is "is there a slower book with the same spread". This map answers both in advance.

## Data (all already recorded, public)
1. Hourly Bitcoin ladder `KXBTCD`: `origin/quote-data:book/<date>/<hhmm>/{book,trades}.csv.gz` (7 strikes nearest the money, top 5 YES and NO bids with sizes every 3 s from 55 minutes before the close; tape polled every 30 s, trade ids de-duplicated).
2. `origin/quote-data:book15r6/<date>/<hhmm>/{book,trades,coverage}.csv.gz`: the 15 minute crypto and gold series present there (KXBTC15M, KXETH15M, KXXRP15M, KXDOGE15M, KXGOLD15M, plus any other series the files hold), book every 2 s.
3. `origin/nc-data:nc15/<date>/<hhmm>/{book,trades,coverage}.csv.gz`: the 11 non-crypto series (KXSILVER15M, KXCOPPER15M, KXWTI15M, KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M, KXHYPE15M, KXBNB15M, KXAUDUSD15M, KXUSDCAD15M, KXNATGAS15M), whole window, book every 5 s.
Series count: 1 + 5 + 11 = 17 as the files stand; P8's text says 16. All series present in the files are measured and listed; the count is not a gate.

## Frozen-window handling (DATA_INVENTORY key; MMSIM1)
MMSIM1's held-out events are the KXBTCD hourly events closing on or after the development cutoff, read once on or after the Nov 24 read. MMMAP1 therefore keeps ONLY hourly-ladder events whose `close_time` is before **2026-11-07T15:00:00Z** (MMSIM1's actual development cutoff per MMPOWER1; this is stricter than the 2026-11-08 date in the brief, so it satisfies both). The script lists directories dated 2026-11-07 or earlier only, and drops every event at or after the cutoff by its `close_time` column before computing anything. Nothing from a later hourly event is scored, counted or printed. The 15 minute book15r6 and NC15 series are not under MMSIM1's freeze (NC15 is new data after every freeze, per NC15COVER1); the F1/F2 freezes concern outcome-based families, and MMMAP1 reads no outcome (below).

## No outcome is read
The markout is computed from the book and the tape only. The `result` column of `coverage.csv.gz` is deleted at read and never touched; no settlement, resolution, win/loss or P&L is read. `mid_h` is the mid of a later book snapshot. Because trades in the last 60 s of a window are dropped, the latest `mid_60` is the mid at about 1 s before the close at the earliest; for trades 1 to 3 minutes before the close the 60 s and 180 s mids can sit near a decided price, so the "5 to 1 minutes" bucket is reported apart and the headline is the all-bucket mean.

## Definitions (per taker trade; P8 verbatim, with the implementation choices fixed here)
- Snapshot mid: `mid = (y1 + (1 - n1)) / 2` with `y1` = best YES bid, `n1` = best NO bid, so YES ask = 1 - n1. A snapshot with either best bid missing or zero is not usable (no mid).
- `mid0` = the mid of the last usable snapshot at or before the trade time. Snapshot time is `t_recv_ms` (NC15 and book15r6) or `poll_ts_local_ms` (hourly); trade time is `created_time` (server stamp, microseconds).
- Trade price `x` = `yes_price_dollars`. Direction `s` = +1 when `taker_outcome_side` is "yes" (taker bought YES), -1 when "no".
- Effective half-spread `e = s * (x - mid0)`.
- Markout `m_h = s * (mid_h - mid0)` with `mid_h` = the mid of the first usable snapshot at or after trade time + h seconds, for h = 30, 60, 180; the snapshot must be within 10 s of that target time or `m_h` is missing for that trade (the trade stays in the other horizons).
- Realized half-spread `r_h = e - m_h`: what a maker filled at the touch keeps after the price has moved for h seconds. The headline is `r_60`.
- All of `e`, `m_h`, `r_h` are reported in cents (x100).
- Drops (P8): trades in the last 60 s before the window close; trades with no usable snapshot inside the 10 s before them; whole windows whose coverage row `max_gap_ms` exceeds 15,000 or whose own snapshots show a gap above 15 s (hourly windows have no coverage file, so the snapshot gap is the test; the gap is the largest difference between consecutive snapshot times in the window).
- Touch depth: the size resting at the best bid on the side the taker hit, at the `mid0` snapshot: a taker who bought YES hits the YES ask, which is the NO best bid, so the touch is `no_bid_sz_1`; a taker who bought NO hits the YES best bid, so the touch is `yes_bid_sz_1`. This is the queue a new maker order would join. Per series the headline is the median over retained trades (also reported: the median of the smaller of the two best-bid sizes, the NC15COVER1 definition).
- Window = one ticker (an hourly strike counts as one window). Date = UTC date of the window close.

## Tables (what is reported)
Per series: taker trades (retained), contracts, dates, windows, quoted half-spread at the snapshots (mean of (1 - y1 - n1)/2 over usable snapshots up to 60 s before the close), mean `e`, mean `m_30`, `m_60`, `m_180`, mean `r_60` with a 90% interval from resampling whole windows (2,000 draws, seed 20261112, ratio of sums over resampled windows), contract-weighted `r_60` (descriptive only), median touch, taker contracts an hour of recorded book time, share of taker contracts that are fractional (non-integer `count_fp`), trades with `r_60`, and qualifies yes/no. Then, per series, the same means by UTC 4 hour block (0, 4, 8, 12, 16, 20) and by minutes to close (15 to 10, 10 to 5, 5 to 1). A cell with fewer than 30 trades is printed blank (a count is printed; the mean is not). Each 15 minute series is its own line; the R6 series are the comparison lines for NC15.

## Qualification rule (fixed now, all five must hold)
A series is worth a market-making simulation only if, over the retained trades with a defined `r_60`:
1. mean `r_60` is at least **+0.5c**;
2. the lower end of its 90% window-resampled interval is **above zero**;
3. at least **500** taker trades;
4. from at least **3 dates** (distinct UTC close dates with at least one retained trade);
5. the median touch depth is **under 2,000 contracts** (a new order behind tens of thousands of contracts never fills; the R6 header row shows about 12,900 at Bitcoin's best bid).
The script runs on whatever dates exist and prints "qualifies yes/no" with the failing conditions named; with under 3 dates every series is "no (dates)". No parameter is tuned: the horizons, drops, 10 s lag, 15 s gap, 30-trade cell floor and the cutoff are the numbers above.

## What a qualifier means
A qualifying series becomes a candidate MARKET EXTENSION of MMSIM1 (a version under lifecycle 7g, not a new strategy), registered only AFTER the Nov 24 MMSIM1 held-out read, and only as its own pre-registered simulation. If no series qualifies the write-up says "no slow book pays a maker" and the market-making family has nowhere else to go on recorded data.

## Limits, said plainly
A realized spread assumes the maker is filled on every taker trade at the touch; queue position can only make it worse, so a positive `r_60` is necessary, not sufficient. Five second books blur `mid0` and the 30 second markout. Three days is a small sample for hour-of-day cells; cell counts are printed and thin cells left blank. The local recorder clock and the server trade stamp differ by under 10 ms per the clock files, ignorable against a 2 to 5 s poll. Pooling 17 series is 17 looks at the same bar: one qualifier is a lead for MMSIM1, not a finding. Several tickers of one hourly event are correlated; the interval resamples windows, not events, so the hourly interval is somewhat too narrow.

## When
Earliest run: **2026-11-15** (NC15 needs 3 full UTC dates: Nov 12, 13, 14, since Nov 11 started at 19:32Z and is partial; the script runs earlier but every NC15 series then reads "no (dates)"). Offline, about 2 hours. Results go in `workers/MMMAP1_RESULT.md`.
