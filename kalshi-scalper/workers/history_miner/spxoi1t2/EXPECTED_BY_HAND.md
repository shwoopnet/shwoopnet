# SPXOI1 T derivation, build 2: expected by hand (History Miner, Nov 13, 2026)

Written BEFORE the code, from the Head of R&D's spec of 18:49Z only. Desk A's code was not read. No real run read.

## Spec as built
- Input: one SPXOI1_CANDLES run (job file 497042e9 on main). The manifest's embedded job must EQUAL the job file given, and the file's sha256 must start 497042e9 (Auditor B's F1 on the SPXFV1 builder, applied here); status complete; every job request answered on pages 1..k at 200, no cursor left, no truncated row; every row MUST carry sha256 and bytes, both checked (F2); files inside the run folder; hm_guard on every path.
- A window is one job request: its ticker (`market_tickers`) and close = the request's `end_ts` + 120.
- Any close at or after 2026-12-01T00:00:00Z stops the run.
- oi_rise = OI(candle with end_period_ts = close - 180) - OI(candle with end_period_ts = close - 360). OI is `open_interest_fp` (a number in a string), else `open_interest`.
- A missing candle at either time drops the window, counted `dropped_no_candle`.
- OPEN READING, proposed: a candle that is present but has no readable OI also drops the window, counted separately as `dropped_no_oi`.
- Nothing else is read: no price, no volume, no result.
- T = nearest-rank 90th percentile of the oi_rise values: sort ascending, rank = ceil(0.90 x n), computed in integers as (90n + 99) // 100, and T = the value at that rank (1-based). n = 0 prints T none.
- Prints n, T and the counts. Nothing written but the printed line.

## Made-up run A (test_spxoi1t2.py builds it)
14 windows, closes 2026-11-05T18:00Z (1793901600) plus 900 s steps, tickers KXINX15M-26NOV05HHMM-MM in ET.
OI at close - 360 is 10000 in every window; OI at close - 180 is 10000 + rise; a decoy candle at close - 120 carries OI 99999 and must not be used.
Rises, windows 1 to 11 and 14: +500, -200, 0, +1200, +300, +800, +50, +2000, +700, +100, (11 below), (12 below), (13 below), +1500.
- W11: no candle at close - 360, so it is dropped (no_candle).
- W12: no candle at close - 180, so it is dropped (no_candle).
- W13: the close - 180 candle has open_interest_fp null, so it is dropped (no_oi).

The used rises, sorted: -200, 0, 50, 100, 300, 500, 700, 800, 1200, 1500, 2000. That is n = 11, rank = ceil(9.9) = 10, so **T = 1500**.
Counts: windows 14, used 11, dropped_no_candle 2, dropped_no_oi 1.

## Made-up run B
Run A without W14: n = 10, rank = ceil(9.0) = 9, so **T = 1200** (the integer rank avoids a float edge at an exact 9).

## Refusals expected
1. manifest job_id other than SPXOI1_CANDLES (embedded job differs from the file)
2. a row without sha256
3. a window closing 2026-12-02T16:15:00Z
4. run status partial
5. a HELDOUT_ path

## Ruled (Head of R&D, 2026-11-13 18:51Z)
- The open reading is ruled as built: a present candle with no readable OI drops the window, counted as dropped_no_oi, which matches build 1. No code change.
- For the comparison: build 1 takes windows from the lists run (ticker and close_time in [Nov 5, Nov 14)), build 2 from the job requests. Both should give 143. If n differs, Auditor B reconciles it before T is used.

## Finite check (Head of R&D, 18:55Z), by hand before the code
An OI value that is a bool, NaN or infinite is no readable OI, so the window drops as dropped_no_oi.
Made-up run C = run A plus three windows W15 to W17, whose close - 180 OI is `"nan"`, `"inf"` and JSON `true`, and whose close - 360 OI is 10000.
Expected: windows 17, used 11, dropped_no_candle 2, dropped_no_oi 4 (W13, W15, W16, W17), n 11, **T 1500** (unchanged from A).
