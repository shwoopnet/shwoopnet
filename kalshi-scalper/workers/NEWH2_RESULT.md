# NEWH2 result (V2 worker NEWH2, 2026-10-30, research only)

Registration `workers/NEWH2_REGISTRATION.md` (commit ce1e3e6, pushed before any scoring). Code `src/scalper/newh2.py`
(`PYTHONPATH=src python -m scalper.newh2 fetch`, then `run`, run once). Printout `studies/newh2_result_2026-10-30.txt` (aggregates only).
Data: gold 15 minute candles `l1b`, `book`, `fresh`, `five` (5,645 windows: 3,192 discovery Aug 6 to Sep 20, 2,453 validation Sep 21 to
Oct 27); silver `alts3` (to Oct 23); KXGOLDH candles fetched into `data/newh2_goldh.sqlite` (1,025 top-of-hour closes, strikes within
$12 of the 15 minute strike). **Disclosed after the fetch:** Kalshi's settled KXGOLDH listing starts at closes on 2026-08-23, so H4's
discovery window is Aug 23 to Sep 20. Nothing closing on or after 2026-10-28 was read. Fill at the next candle's closing ask, held,
C = 10 screen, fee rounded up per order. Nothing was changed after the score.

## Verdicts

| Hypothesis | Disc n / PF10 / PF1 / PF x1.2 | Val n / PF10 / PF x1.2 | Verdict |
|---|---|---|---|
| H1 GBREAK (CME daily break, favourite 55c to 88c at 6 min) | 73 / 0.98 / 0.96 / 0.97 | 18 / 0.51 / 0.51 | NOT_ENOUGH_DATA (point estimate below 1) |
| H2 GREOPEN (first 90 min after the reopen, cheap side 8c to 45c at 8 min) | 140 / 0.73 / 0.72 / 0.72 (z -1.44) | 100 / 0.85 / 0.84 | FALSIFIED |
| H3 GSILV (Kalshi silver moved 20c+, gold has not followed) | 39 / 1.09 / 1.08 / 1.08 | 17 / 0.59 / 0.58 | NOT_ENOUGH_DATA (validation negative) |
| H4 GLADH (15 minute book 6c+ off the hourly ladder) | 52 / 0.63 / 0.61 / 0.62 | 40 / 0.66 / 0.65 | NOT_ENOUGH_DATA (both windows lose) |
| H2 control (same side rule, all other gold windows; information) | 2,173 / 0.84 | 1,644 / 0.92 | not screened |

Zero volume both ways: no trade's fill candle had volume 0, so both lines are identical. **Screen passes: 0. No candidate written to
`workers/candidates/`, so no evaluator was frozen and no parity check was needed.**

## What each one says

- **GBREAK:** the dead hour does not leave the leading side cheap. Discovery win rate 76.7% against a 75.7% mean fill (+1.0 pt, PF 0.98);
  validation is worse (-12.7 pt on 18). Only 91 trades in both windows: Kalshi listed break windows on few days.
- **GREOPEN:** the cheap side after the reopen is NOT underpriced; it does slightly worse than the cheap side at other hours (gap -3.8 pt
  against the control's -1.6 pt in discovery). Makers do not carry the break's calm into the reopen.
- **GSILV:** 56 signals in both windows; the small discovery lean (+3.6 pt) reverses in validation (-11.5 pt). No sign gold's quote lags
  Kalshi silver.
- **GLADH:** when the 15 minute book sits 6c or more off the hourly ladder's interpolated value, the ladder is the one that is wrong:
  buying the 15 minute side the ladder calls cheap loses in both windows (win 23% against a 28% fill). The 15 minute gold book prices
  the instant at least as well as the ladder's two nearest strikes. 39 top-of-hour windows had no bracketing pair within $6 (data gap).
- **Declined, no try spent:** Bitcoin "average already locked" at 90 to 60 s (nothing of the 60 s average is fixed yet; the sub-minute
  version is BTCAVG and LATECAL); gold's first touch of 88c to 97c and the favourite after a lost favourite (owner's 2026-10-28
  instruction closes buy-the-favourite-and-hold work; the second is also close to NEWH1 FLIPREV).

## Count

**N added: 4** (H1 to H4, one rule each; the control is reported, not screened). Running count about 591,979 (after NEWH1) plus other
workers' additions, plus 4.
