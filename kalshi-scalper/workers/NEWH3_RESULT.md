# NEWH3 result (V2 worker NEWH3, 2026-10-30, research only)

Registration `workers/NEWH3_REGISTRATION.md` (commit cf7413c, pushed before any scoring). Code `src/scalper/newh3.py`
(`PYTHONPATH=src python -m scalper.newh3 run`, run once). Printout `studies/newh3_result_2026-10-30.txt` (aggregates only).
Data: Bitcoin 15 minute candles `l1b`, `book`, `fresh` (7,869 windows: 4,357 discovery Aug 6 to Sep 20, 3,512 validation Sep 21 to
Oct 27); hourly ladder KXBTCD candles `lad2` then `conf2_lad` (1,500 closes, universes chosen 55 to 52 minutes before each close).
H1's discovery window is Aug 24 to Sep 20 (ladder history starts then; stated in the registration). Nothing closing on or after
2026-10-28 was loaded. Fill at the next candle's closing ask, held unless the rule sells, C = 10 screen, fee rounded up per order.
Nothing was changed after the score and nothing was re-run.

## Verdicts

| Hypothesis | Disc n / PF10 / PF1 / PF x1.2 | Val n / PF10 / PF x1.2 | Verdict |
|---|---|---|---|
| H1a BLADX_15M (buy the 15 minute side the hourly ladder calls 6c+ cheap) | 282 / 1.08 / 1.06 / 1.06 | 368 / 0.76 / 0.75 (z -2.10) | FALSIFIED |
| H1b BLADX_LAD (buy the ladder side the 15 minute book calls 6c+ cheap) | 233 / 0.78 / 0.76 / 0.77 | 303 / 0.92 / 0.91 | FALSIFIED |
| H2 WIDEN (cheap side after the spread widens to 4c and 2x in the last 5 minutes) | 3 / 0.00 | 0 | NOT_ENOUGH_DATA |
| H3 EXITOI (L1 exit at 120 s when open interest fell 5%+ from 360 s to 180 s) | 26 triggered of 1,331 entries; hold PF10 0.988, rule 1.001 | 29 of 1,028; hold 0.955, rule 1.006 (pooled day z +1.51) | NOT_ENOUGH_DATA |
| H2 control (cheap side, no widening; information) | 1,954 / 0.99 | 1,555 / 0.97 | not screened |

Zero volume both ways: no trade's fill candle had volume 0, so both lines are identical. **Screen passes: 0. No candidate written to
`workers/candidates/`, so no evaluator was frozen and no parity check was needed.**

## What each one says

- **BLADX (Bitcoin 15 minute book against the hourly ladder at the shared close):** a 6c gap between the 15 minute mid and the
  ladder's interpolation at the 15 minute strike appeared in 763 of 1,500 matched top-of-hour closes, but neither book is the stale
  one: buying the 15 minute leg was +3.0 points in discovery and -4.2 in validation; buying the ladder leg -3.2 and -0.2. The gap is
  the noise of two books' last quotes of the minute (as LOCK2H found), not a slow quoter. Together with NEWH2's GLADH on gold, the
  15 minute book against the hourly ladder is closed on both assets.
- **WIDEN:** the premise barely exists on minute candles. The Bitcoin 15 minute spread almost never reaches 4c and twice its earlier
  median in the last 5 minutes at a contested price (6 signals in 7,869 windows). Quoters do not visibly withdraw at minute
  resolution; if they do, it is under a minute (R6 recorder data). The no-widening control (the cheap side at 15c to 50c, 5 to 2
  minutes left) is PF 0.99 / 0.97, i.e. fairly priced.
- **EXITOI:** a 5% fall in open interest between 6 and 3 minutes left is rare on L1's Bitcoin entries (2%) and marks favourites that are
  already failing (loss rate 62% against 5% untriggered; the fill had already slipped to 0.80 to 0.87). Selling them at the 120 s bid
  beat holding in both windows (+$9.47 and +$30.07 at 10 contracts; PF +0.013 and +0.051), but on 26 and 29 triggered entries, below
  the registered 50, and pooled day z +1.51 (bar 2.0). The "sag" the brief asked about is not there in discovery (side bid change
  from 120 s to 60 s: triggered -0.4c, untriggered -0.7c); in validation triggered entries fell a further 9.8c. Reading: the open
  interest fall is a symptom of a reversal already in the price, not a forced seller pushing a sound favourite down. An L1 question
  for the owner at most; it would need about twice the history or a forward read.
- **Declined, no try spent:** the strike set from the opening 60 s average (L8, FALSIFIED 2026-10-07); a plain favourite bid sag read
  as a time exit (TIME1, TX1, TX2 in TIMEX1, EXIT2, and LATECAL's calibration).

## Count

**N added: 4** (H1a, H1b, H2, H3; the control and the sag lines are reported, not screened). Running count about 592,057 before, about
**592,061** after (plus other workers' additions).
