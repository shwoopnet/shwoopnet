# NEWH5 result (V2 worker NEWH5, 2026-10-30, research only)

Registration `workers/NEWH5_REGISTRATION.md` (commit 3e23846, pushed before any scoring). Code `src/scalper/newh5.py`
(`PYTHONPATH=src python -m scalper.newh5 run`, run once). Printout `studies/newh5_result_2026-10-30.txt` (aggregates only).
Nothing closing on or after 2026-10-28 was loaded. Nothing was changed after the score. Nothing touches the live bot.

**Parent (gold L1 as live):** 5,645 gold windows (3,192 discovery Aug 6 to Sep 20, 2,453 validation Sep 21 to Oct 27), 1,673 L1
entries (976 / 697; 9 signals with no fill candle; 41 hit the 25c exit). Signal at -360 s, fill at the -300 s candle's ask, live 25c
exit at minute closes. Baseline at C = 10: PF 1.226 (net +$102.94, worst day -$15.86) in discovery, 1.272 (+$88.82, worst day
-$15.76) in validation; at C = 16: 1.229 / 1.276, worst days -$25.31 / -$25.12. Zero volume both ways: no fill candle had volume 0,
so both lines are identical.

## Verdicts

| Filter (skip when ...) | Skipped disc / val | Skipped net C=10 disc / val | Skipped loss rate vs kept (disc; val) | Kept-minus-skipped day z (disc / val) | Verdict |
|---|---|---|---|---|---|
| F1 GLADF: hourly ladder 5c+ less sure of the favourite | 42 / 19 | +$21.10 / +$12.66 | 2.4% vs 5.4%; 0% vs 5.8% | -2.99 / -3.87 | NOT_ENOUGH_DATA (val under 20; the filter HURTS in both windows) |
| F2 GTHIN: window volume before the look under discovery's 20th pct | 195 / 2 | +$27.13 / +$1.05 | 5.1% vs 5.2%; 0 of 2 | -0.30 / n/a | NOT_ENOUGH_DATA (2 skipped in val; discovery says nothing) |
| F3 GOIDROP: open interest fell 5%+ from -540 s to -360 s | 7 / 11 | +$6.81 / +$7.78 | 0 of 7; 0 of 11 | n/a (no losses skipped) | NOT_ENOUGH_DATA |
| F4 GPRIOR: previous 15 minutes moved $6.73+ against the favourite | 96 / 57 | +$16.73 / +$7.02 | 4.2% vs 5.3%; 5.3% vs 5.6% | -0.32 / +0.02 | FALSIFIED |

**Screen passes: 0.** Not one filter removed entries whose net was negative, in either window, at either size, held or with the 25c
exit, at fees x1 or x1.2. Every one would have LOWERED net per opportunity (gold, C = 10, 25c exit, cents per contract per entry:
F1 1.055 to 0.839 and 1.274 to 1.093; F2 1.055 to 0.777; F3 1.055 to 0.985 and 1.274 to 1.163; F4 1.055 to 0.883 and 1.274 to 1.174).
C = 16 gives the same picture (per-order rounding changes nothing material).

## What each one says

- **GLADF (the brief's ladder idea):** as predicted, and stronger: when the hourly ladder is 5c or more less sure than the 15 minute
  book, the 15 minute favourite won MORE often (1 loss in 61 skipped entries against about 5.5% for the rest). The z of -3 to -4 is
  inflated by a skipped set with almost no losses, so read it as "the ladder is the wrong one", which is NEWH2's finding again. Do
  not build a ladder filter on gold.
- **GTHIN:** gold's volume rose a lot between the windows (the discovery 20th percentile, about 31,700 contracts before the look, is
  under almost every validation window), so the rule had 2 skips in validation. In discovery the thinnest fifth lost at the same rate
  as the rest (5.1% vs 5.2%) and made more per entry. Thin gold windows are not where the favourite fails. A relative definition
  (against a trailing level) would be a new try, and the discovery evidence gives no reason to spend it.
- **GOIDROP:** a 5% fall in open interest in the three minutes before the look almost never happens on gold (18 times in 1,673), and
  those 18 entries all won. The post-entry open interest signal (EXITOI) does not have a pre-entry twin on gold.
- **GPRIOR:** a hard previous 15 minute move against the favourite changes nothing: loss rate 4.2% vs 5.3% and 5.3% vs 5.6%, z
  about 0. Gold's 15 minute book already prices the previous window's move.
- **Declined without a try (in the registration):** how close the favourite came to flipping (`dip`, TREE1, FEAT1, DIP1) and whether
  the favourite led at the open (`dip` at the first candle, SMOOTH20 / SMOOTH2, `tib`); size tilts and entry-timing changes (SIZE3,
  BAND2, EL1, HUNT2).

Reading across the four: on gold, every pre-entry signal tried here that should have marked a weak favourite marked a STRONGER one or
nothing. That is consistent with gold's 6 minute favourite being the best-priced thing in the window, and with the gold edge (PF
about 1.2 to 1.3 at 10 to 16 contracts on this history) not being concentrated in any of these subsets.

## Count

**N added: 4** (F1 to F4, one rule each, no variants). Running count about 592,070 (after NEWH4) plus other workers' additions, plus 4.
