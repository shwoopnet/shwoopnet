# TODSEAS1 result (run once 2026-11-03; research only)

Registration `workers/TODSEAS1_REGISTRATION.md` (commit 7be3955, pushed before any outcome), code `src/scalper/todseas1.py` (pushed before the score), tests
`tests/test_todseas1.py` (7 ok), printout `studies/todseas1_score_2026-11-03.txt`, marker `data/todseas1_score.json`. No change after the first outcome.
**W3 (2026-10-05 on) was never loaded.** Cheap side ask 0.05 to 0.30 at close-180, fill ask at close-120, hard limit 0.30, held, C = 10, fee 7% x C x p x (1-p)
rounded up. Worst single loss $3.15 at 10 contracts.

## Verdicts
**FAM (all ten slots pooled): FALSIFIED.** n 562 (W1 190, W2 372), win 8.7% vs 9.2% paid, payoff 9.1, PF 0.87 (W1 0.82, W2 0.90; x1.2 0.86), mean -1.09c, day z -0.93;
slot minus neighbour control -2.3c (z -1.40; W1 -0.4c, W2 -2.9c). Baseline (all event-free non-slot cheap sides): W1 PF 0.83 n 1,877, W2 PF 0.74 n 3,863: the cheap side
loses by itself and the slots do not beat it.
**Every single slot: NOT_ENOUGH_DATA** (pooled W1+W2 under 150, as predicted; the registered rule says nothing is widened).

| slot | n (W1/W2) | win vs paid | PF W1 / W2 | mean c | diff vs control W1 / W2 (z) |
|---|---|---|---|---|---|
| S1 HALT_IN 17:00 ET | 22 / 36 | 12.1% vs 10.2% | 1.40 / 0.98 | +1.2 | +15.9c (1.58) / +1.6c (0.19) |
| S2 HALT_OUT 18:15 ET | 17 / 22 | 7.7% vs 10.5% | 0.00 / 1.20 | -3.5 | -2.1c / +3.3c |
| S3 FX_ROLL | 0 / 6 | 0% vs 8.8% | - / 0.00 | -9.4 | - / -3.4c |
| S4 TOKYO_FIX | 0 / 3 | 0% | - | -7.2 | - |
| S5 TOKYO_CLOSE 15:30 JST | 27 / 47 | 9.5% vs 7.7% | 2.58 / 0.67 | +1.2 | +11.8c (1.40) / -9.2c (-2.08) |
| S6 PRE_LONDON 07:00 | 28 / 47 | 8.0% vs 7.4% | 1.36 / 0.83 | +0.1 | -6.5c / -8.9c (-1.71) |
| S7 LSE_CLOSE 16:30 | 21 / 49 | 10.0% vs 9.1% | 0.00 / 1.53 | +0.3 | -16.0c (-2.65) / -0.3c |
| S8 PRE_US 09:00 ET | 23 / 49 | 8.3% vs 9.0% | 0.46 / 1.03 | -1.3 | +6.5c (1.46) / +5.2c (1.17) |
| S9 NY_MIDDAY 12:00 ET | 23 / 56 | 1.3% vs 8.7% | 0.47 / 0.00 | -8.0 | -12.7c (-1.40) / -11.1c (-2.70) |
| S10 US_LATE 15:00 ET | 29 / 57 | 14.0% vs 11.6% | 0.79 / 1.35 | +1.7 | +1.7c (0.30) / +1.5c (0.28) |

Which slots were already covered (not re-tested): EVENT1 Try A (NYSE open/close, London/Tokyo/HK opens, 8:30 releases, ISM, FOMC, EIA), EVENT830, PUB20 P03 Friday,
P06 fix windows (W3 FALSIFIED), P09 settlement windows, P10 weekend reopen, P07 month end.

## Reading
- No slot reaches PF 1.5 in both W1 and W2 with a positive control difference. The two closest: S1 (W1 15.9c diff, W2 +1.6c, PF 0.98) and S10 (both diffs +1.5c to +1.7c, z under 0.4,
  PF 0.79 and 1.35). S8 PRE_US has a positive diff in both halves (z 1.46, 1.17) but PF 0.46 / 1.03, i.e. it only loses less than its neighbours.
- S9 NY_MIDDAY is the opposite, a slot that loses more than its neighbours in both halves (1 win in 79: 1.3% against 8.7% paid, z -2.95): a post hoc curiosity (the midday lull is
  where the maker is RIGHT), not tested further, not a trade (it would be a favourite-and-hold entry on the other side, closed 2026-10-28).
- By class: metals PF 1.18 (n 295), energy 0.56 (212), FX 0.61 (55): the pooled family hides a metals/energy split that exists in the baseline too, not a clock effect.
- **No probe flag.** The registered flag (positive mean net AND positive diff in both W1 and W2) fired on no slot, so there is no capped-probe spec.
- Prediction check: right on the verdict (FAM FALSIFIED, 9 of 10 NOT_ENOUGH_DATA), the PF (0.87 vs 0.85 predicted for FAM; slots 0 to 2.6 on tiny n) and win rate (8.7% vs
  12% to 16% predicted: the 0.30 band is mostly 5c to 12c longshots, avg fill 9.2c, not the 13c to 17c I assumed); trade counts per slot 39 to 86 inside the 40 to 140 predicted.
- Streaks: `streaks.py` at 8.7% over 100 trades would give a longest losing run of about 25 on average (not run; the losing run in S9 W2 was 56 of 56).

## Disclosures
- UK/US/Japan holidays not removed; AUD/USD and USD/CAD left out (on file only inside W3); FX candles start 2026-09-23, so FX has no W1.
- Control falls back to other series at the same neighbour times when a series has none (dropped counts above). S1 W1 dropped 6 of 22.
- The control halt-hour exclusion for S1 to S3 removes the neighbours that close inside the 60 minute break.
- Slot list fixed before any outcome; only the hour-of-day distribution of market closes (metadata) and the outcome-free `counts` (trades per slot and third) were seen first.
- N: 11 tries, +22.
