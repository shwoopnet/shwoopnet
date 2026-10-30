# NEWH4 result (V2 worker NEWH4, 2026-10-30, research only)

Registration `workers/NEWH4_REGISTRATION.md` (commit cedfb07, pushed before any scoring). Code `src/scalper/newh4.py`
(`PYTHONPATH=src python -m scalper.newh4 run`, run once). Printout `studies/newh4_result_2026-10-30.txt` (aggregates only).
Data, all local caches, nothing fetched: KXBTCD `lad2` then `conf2_lad` (1,500 hourly closes, 656 discovery Aug 24 to Sep 20, 844
validation Sep 21 to Oct 27); KXGOLDH `newh2_goldh` (1,025 hourly closes, 443 discovery Aug 23 to Sep 20, 582 validation). Nothing
closing on or after 2026-10-28 was loaded. Fill at the next candle's ask, held to settlement, C = 10 headline, fee rounded up per
order. Nothing was changed after the score and nothing was re-run.

## Verdicts

| Hypothesis | Disc n / PF10 / PF1 / PF x1.2 / win vs fill | Val n / PF10 / PF x1.2 / win vs fill | Verdict |
|---|---|---|---|
| H1 KINK-BTC (strike 5c+ off the leave-one-out probit curve, buy the cheap side 10c to 85c) | 355 / 0.94 / 0.91 / 0.92 / 26.2% vs 26.1% | 478 / 0.83 / 0.82 / 23.2% vs 25.1% (z -2.23) | FALSIFIED |
| H2 KINK-GOLD (same, KXGOLDH, 14 to 3 min left) | 261 / 0.86 / 0.84 / 0.85 / 22.2% vs 23.5% | 335 / 0.67 / 0.66 / 19.1% vs 24.0% (z -2.55) | FALSIFIED |
| H3 TAIL-BTC (YES or NO longshot asked 2c to 6c, 30 min left) | 1,221 / 0.64 / 0.55 / 0.63 / 2.9% vs 4.2% (z -2.87) | 1,562 / 0.72 / 0.71 / 3.3% vs 4.2% (z -3.03) | FALSIFIED |
| H4 TAIL-GOLD (same, 10 min left) | 293 / 0.40 / 0.35 / 0.40 / 2.0% vs 4.6% (z -4.07) | 634 / 0.39 / 0.39 / 1.9% vs 4.3% (z -4.92) | FALSIFIED |
| H5 NARROW-BTC (ladder width at most 0.6 of its own centre's realised move, buy the cheap side 10c to 35c) | 27 / 0.49 / 0.47 / 0.48 / 11.1% vs 19.2% | 58 / 1.08 / 1.07 / 20.7% vs 18.4% | NOT_ENOUGH_DATA (27 discovery trades; point estimate 0.49) |

**Zero volume both ways.** Bitcoin: almost every fill candle traded (KINK all; TAIL 1,178 of 1,221 and 1,525 of 1,562), PF
unchanged. Gold: most ladder fill candles had no trade (KINK 90 of 261 and 169 of 335 traded; TAIL 44 of 293 and 139 of 634).
Without them gold KINK is PF 0.70 / 0.66 and gold TAIL 0.00 / 0.15: worse, not better. **Screen passes: 0. No candidate written to
`workers/candidates/`, so no evaluator was frozen and no parity check was needed.** (Had one passed: the forward ledger reads only
15 minute series from `fresh.sqlite`, the quote recorder and R6; a ladder candidate would need a KXBTCD / KXGOLDH candle source
added to `fresh_update` or the QUOTE2B `book/` files wired in as a new source.)

## What each one says

- **KINK:** a strike 5c or more off the curve its neighbours draw is not a stale quote. On both ladders the "cheap" strike wins
  LESS often than its price (gold validation -4.9 points, worst on NO), so the curve is the wrong shape (the ladders carry fatter or
  skewed wings than a normal), and the outlying strike is the better price. Bitcoin discovery was fair (+0.1 point), so there is no
  edge there either; the fee makes it PF 0.94.
- **TAIL:** the ladders' deep longshots are overpriced, as the favourite-longshot bias says and as TAIL1 found on 15 minute gold:
  Bitcoin 2c to 6c sides win 2.9% to 3.3% against 4.2% paid, gold 1.9% to 2.0% against 4.3% to 4.6%. GEN3-H1's finding (cheap sides
  early in the hour TOUCH higher than priced) does not carry to settlement: whatever the path does, the longshot pays less than its
  price. The mirror, buying the 94c to 98c side, is buy-the-favourite-and-hold and was not tested (owner's 2026-10-28 instruction).
- **NARROW:** the trigger is rare (96 signals in 1,500 closes even with the fit noise that biases it toward firing), and the 85
  trades split 0.49 / 1.08. Nothing to read; LAD1's spot-based version (+0.10c) already said the ladder's width is about right.
- **Gold daily and weekly ladders (KXGOLDD, KXGOLDW):** not tried; locally only LADL1's two looks on 38 daily and 9 weekly closes.
  NOT_RUNNABLE on local data (one independent close a day cannot reach 100 discovery trades without pooling correlated strikes).
- **Declined, no try spent:** monotonicity locks (ARB2, the two snapshots, LOCK2H cover them); far strikes still bid near the close
  and the too-wide mirror of NARROW (both are buy-the-favourite-and-hold).

Reading across the round: on its own cross section the hourly ladder is priced at least as well as any simple model of it, and the
one systematic bias found is the familiar one (longshots overpriced), which can only be harvested by buying favourites.

## Count

**N added: 5** (H1 to H5, one rule each, no parameter searched). Running count about 592,061 plus other workers' additions, plus 5.
