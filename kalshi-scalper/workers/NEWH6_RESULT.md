# NEWH6 result (V2 worker NEWH6, 2026-10-30, research only)

Registration `workers/NEWH6_REGISTRATION.md` (commit 14639a6, pushed before any scoring; amendment 9ba6094 for OPENLEAN, pushed
after a run that scored zero OPENLEAN entries and before any OPENLEAN trade was scored). Code `src/scalper/newh6.py`
(`PYTHONPATH=src python -m scalper.newh6 run`, then `openlean` for the amendment's one re-read). Printouts
`studies/newh6_result_2026-10-30.txt` and `studies/newh6_openlean_2026-10-30.txt` (aggregates only).
Data, local caches only, nothing fetched: gold 15 minute candles `l1b`, `book`, `fresh`, `five` (5,645 windows: 3,192 discovery
Aug 6 to Sep 20, 2,453 validation Sep 21 to Oct 27); Bitcoin `l1b`, `book`, `fresh` (7,869: 4,357 / 3,512). Nothing closing on or
after 2026-10-28 was loaded. Every trade is a round trip: bought at the next candle's ask, sold at a bid inside the window, never
held to settlement; fee rounded up per order on the buy and the sell; C = 10 headline. A zero bid at the sale candle moved the sale
to the next candle (at most to 120 s left), else booked at 0: this happened 5 times in all (gold CLOCK_R discovery 4, gold OPENLEAN
discovery 1). Nothing was changed after the score.

## Verdicts

| Rule | Market | Disc n / PF10 / PF1 / PF x1.2 | Val n / PF10 / PF x1.2 | Verdict |
|---|---|---|---|---|
| H1 STOPRUN (former 85c+ favourite first bids 30c or less at 600 to 300 s; buy, sell 2 min later) | gold | 25 / 1.07 / 0.95 / 1.01 | 11 / 3.05 / 2.88 | NOT_ENOUGH_DATA |
| H1 STOPRUN | Bitcoin | 35 / 0.79 / 0.73 / 0.76 | 22 / 0.87 / 0.83 | NOT_ENOUGH_DATA (point estimates below 1) |
| H2F CLOCK_F (in-band favourite at 480 s, buy at 420 s, sell at 300 s, after L1's 6 minute wave) | gold | 410 / 0.51 / 0.27 / 0.47 (z -4.57) | 261 / 0.46 / 0.43 | FALSIFIED |
| H2F CLOCK_F | Bitcoin | 499 / 1.00 / 0.55 / 0.92 | 453 / 0.82 / 0.77 | FALSIFIED |
| H2R CLOCK_R (cheap side after the 6 minute wave, buy at 240 s, sell at 180 s) | gold | 806 / 0.30 / 0.21 / 0.28 (z -7.00) | 453 / 0.47 / 0.44 | FALSIFIED |
| H2R CLOCK_R | Bitcoin | 958 / 0.40 / 0.27 / 0.38 (z -10.0) | 579 / 0.73 / 0.69 | FALSIFIED |
| H3 OPENLEAN as registered (first-second quote `bid_o`/`ask_o`) | both | 0 runnable windows | 0 | NOT_RUNNABLE |
| H3 OPENLEAN amended (first candle's closing quote; fade a 5c+ lean toward the previous leader, 780 s to 540 s) | gold | 894 / 0.60 / 0.55 / 0.57 (z -5.63) | 693 / 0.62 / 0.58 | FALSIFIED |
| H3 OPENLEAN amended | Bitcoin | 1,170 / 0.57 / 0.52 / 0.53 (z -7.48) | 967 / 0.57 / 0.53 | FALSIFIED |

Zero volume both ways: only one trade (gold OPENLEAN discovery) had a zero-volume fill or sale candle; without it PF 0.61, so both
lines are the same. **Screen passes: 0. No candidate written to `workers/candidates/`, so no evaluator was frozen and no parity
check was needed** (`forward_eval` exists in the module for STOPRUN and CLOCKFLOW in case one is ever wanted; it is unused).

## What each one says

- **STOPRUN:** a favourite of 85c+ that breaks 30c between 10 and 5 minutes left is rare (gold 36, Bitcoin 57 in 83 days), so it
  cannot be screened. The bid did not bounce on Bitcoin (sale 21.9c against a 22.2c fill in discovery); gold's small positive is
  25 and 11 trades. No sign of stop-loss sellers pushing the bid below value that a taker could collect after two fees.
- **CLOCKFLOW:** the 6 minute favourite wave is visible in the price but too small to trade. On Bitcoin the held favourite's bid
  rose from 420 s to 300 s in 75% of windows (sale 93.6c against a 92.6c ask), about 1c gross, which the two fees (about 1c a contract
  at 10 contracts) and the spread take: PF 1.00 in discovery, 0.82 in validation. Gold's book does not rise (sale below fill). Fading the
  wave (cheap side at 3c to 15c, one minute hold) loses most of the contract to the spread: the cheap side keeps falling.
- **OPENLEAN:** the premise is absent. Kalshi's book opens EMPTY (first-second bid about 0, ask about 1, every window), and the first
  two-sided quote (60 s in) does not lean toward the previous window's leader: mean lean gold +0.3c / +0.1c, Bitcoin -0.8c / -0.8c,
  with 5c+ leans toward and against about equally common. Fading a lean that is not a bias just pays the round trip (about 3.5c
  per trade).
- **Declined without a try (in the registration):** momentum through 50c (HIST1 trigger 3, S27, S35, GEN1's grammar), a gold and
  Bitcoin pair (BK4, BK5, O14, S42; no stated reason the pair is mispriced), frozen-quote breakouts and one-sided churn (S33, S29,
  S32).

**Data note for later workers:** the candles' opening fields of a window's first minute (`bid_o`, `ask_o` of the candle ending
840 s before the close) are an empty book in every gold and Bitcoin window; "opening quote" ideas need the closing quote of that
candle or the recorder.

## Count

**N added: 8** (STOPRUN 2, CLOCK_F 2, CLOCK_R 2, OPENLEAN 2; the amendment re-read is the same 2 tries, as in CONF1; the
descriptive lean lines and hold-to-settlement information are not counted). Running count about 592,074 (after NEWH5) plus other
workers' additions, plus 8.
