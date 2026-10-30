# FALS4 result: falsifier for GEN6's open interest core (Bitcoin cheap side at 180 s after an open interest jump), research only

Registration `workers/FALS4_REGISTRATION.md` (commit c8bc905, pushed before any scoring). Code `src/scalper/fals4.py`, written from the raw candles (`data/l1b`, `book`, `fresh`, first file wins). **I never read `src/scalper/gen6.py`**: the re-implementation matched GEN6 exactly, so there was no gap to explain. 7,869 Bitcoin windows (discovery 4,357, Aug 6 to Sep 20; validation 3,512, Sep 21 to Oct 27). Nothing closing on or after 2026-10-28 00:00 UTC was loaded. Fills at the next candle's closing ask, C = 10, fee rounded up per order, held to settlement, unless stated.

## Verdict: SURVIVES (RULES word: NOT_YET_FALSIFIED; two history windows only, forward decides)

No registered BROKEN or CHANGED line was crossed. One caveat that is not a registered line but matters for execution: a fill ONE MINUTE LATER (the candle ending 60 s before the close) gives discovery PF **0.94** (validation 1.66). The edge sits in the quote of the minute right after the signal.

## Check 1: re-implementation (exact)

| | discovery | validation |
|---|---|---|
| core (doi = oi at -180 minus oi at -360, > 86,299.56) | n **222**, PF **2.28**, win 29.3%, mean fill 0.178, day z 4.09 | n **333**, PF **1.85**, win 27.6%, fill 0.192, day z 4.42 |
| YES only / NO only | 123, 2.65 / 99, 1.89 | 186, 1.97 / 147, 1.72 |

Trade counts and PF equal GEN6's to the shown digits. (My day z is clustered by day; GEN6's 4.53 is a little higher, a different z method.)

## Check 2: look-ahead audit (no leak found)

- **`oi` is the end-of-candle snapshot, aligned with that candle's trades.** Over 110,166 one-candle steps, |change in oi| never exceeds that candle's own volume (0 violations). Paired with the next candle's volume it does 10,361 times, and with the previous candle's 2,437 times, so the test discriminates. The first candle's oi is never above its volume (7,869 of 7,869), and the placeholder candle 60 s after the close repeats the close candle's oi (7,415 of 7,415). So the oi at the signal is known when the signal candle ends, which is when the fill candle begins.
- **Missing candles:** every one of the 7,869 settled windows has the -360, -180 and -120 candles; no selection through gaps (YES rate 50.1%).
- **Results are joined by ticker**, and the ticker's time part equals `close_ts` (in ET) for all 7,869 windows.
- **The 5c to 50c band uses the signal candle only** (in code). Also requiring the fill ask in the band: disc 108, PF 2.49; val 174, PF 1.85.
- **Latency stress (fill at the candle ending -60):** disc n 221, PF **0.94**, z -0.20; val n 332, PF 1.66, z 2.34. The registered CHANGED line was validation below 1.3; it was not met. Discovery collapsing is reported as a caveat.

## Check 3: costs

| | discovery PF | validation PF |
|---|---|---|
| C = 10 (headline) | 2.28 | 1.85 |
| C = 1 | 2.16 | 1.75 |
| C = 10, fees x1.2 | 2.26 | 1.82 |
| signal ask + 0 (info) | 2.15 | 1.68 |
| signal ask + 1c | 1.98 | 1.55 |
| signal ask + 2c | **1.83** | **1.44** |

## Check 4: fill realism

40% of discovery (89 of 222) and 36% of validation (119 of 333) fills are under 5c. **Excluding them:** disc n 133, PF **2.22**; val n 214, PF **1.87**. Fill candles with volume under 10 contracts: 0 of 555 (candle volumes are 10^5 scale; this says nothing about the size at the ask, which candles do not show). Zero-volume signal or fill candles: 0. Without the 5 best trades: disc 2.02, val 1.69 (top 5 are 9% to 11% of gross wins).

## Check 5: threshold drift (information)

Trailing 30 day 90th percentile of doi at 180 s over all Bitcoin windows, earlier days only (first usable day Aug 16). The threshold rose from 115k to 216k (median 121k; higher than 86.3k because GEN6's percentile pooled all four looks). Disc n 72, PF **5.19**, z 4.54; val n 67, PF **2.65**, z 2.63. A higher, moving bar keeps the edge and concentrates it.

## Check 6: stability

PF in every 8 day block from Aug 6: 2.11, 2.61, 3.85, 1.15, 1.88, 1.74, 2.90, 2.63, 1.27, 1.63, 1.55 (last block 3 days). **11 of 11 above 1.0**, lowest 1.15 (Aug 30 to Sep 6, n 29). Longest run of losing trades 19 (normal for a 28% win rate over 555 trades). Longest stretch without a new equity high: 7 days. Net +$492 at C = 10 over 555 trades.

## Check 7: counterparty (prediction PF below 0.77; confirmed)

The favourite in the same windows, next candle ask, held: disc n 222, PF **0.36**, z -4.68; val n 333, PF **0.45**, z -5.56. Below FALS3's unconditional 0.77, as predicted. As registered, this is close to mechanical (the complement of the cheap side, minus spread and fees), so it confirms the arithmetic more than the story.

## Check 8: proxies at matched counts (none explains it)

| cheap side at 180 s, held | discovery | validation | overlap with core (disc / val) |
|---|---|---|---|
| no condition (base) | 2,431, PF 1.18 | 1,863, PF 1.01 | |
| 3 minute volume >= 623,602 (disc matched) | 222, PF 1.39 | 481, PF 1.01 | 48 / 159 |
| abs mid move over 3 min >= 0.43 (disc matched) | 224, PF 1.32 | 176, PF 0.82 | 4 / 7 |
| base resampled to the core's hour mix (2,000 draws, median / 95th) | 1.25 / 1.72 | 0.97 / 1.26 | |
| **core** | **222, 2.28** | **333, 1.85** | |
| core with 3 minute volume below the disc median | 45, PF 1.42 | 16, PF 0.52 | |
| core with volume at or above the median | 177, PF 2.50 | 317, PF 1.96 | |
| high volume but doi NOT above 86.3k | 174, PF 1.12 | 322, PF 0.65 | |

corr(doi, 3 minute volume) over the base = 0.17. Volume, a big move and the hour each give a validation PF near 1; the core's 1.85 is above the hour-mix 95th percentile (1.26). What matters is new contracts being created, not trading as such: heavy volume WITHOUT an oi jump loses (0.65).

**Path, description only:** in core windows the cheap side's mid fell 9 to 12 points over the 3 minutes before the signal (base: 14 to 15 points) and then held flat or ticked up over the next minute (+0.6 to +1.5 points, base -0.2 to -0.8). It is not a crash window (the move proxy barely overlaps). Read: a wave of new contracts while the favourite firms up, after which the cheap side stops falling.

## Prediction check

Check 1 reproduced (predicted, 70%). No leak (predicted, 75%); latency stress validation 1.66 was in the predicted 1.2 to 1.6 range plus a little, but discovery 0.94 was worse than I expected. + 2c stayed above 1.3 in both (predicted, 60%). Sub-5c exclusion gave 2.22 / 1.87, above the predicted 1.3 to 1.8. Drift validation 2.65, above the predicted 1.3 to 1.9. 8 day blocks: predicted at least one under 1.0 (65%); wrong, none was. No proxy matched (predicted, 60%).

## For the lead

- Not broken on the history. The bar is still unmet: z 4.42 / 4.53 against about 5.2, and two windows only. The forward row `REF_GEN6_OICORE` is the right next read.
- **Execution is the weak point.** The edge needs a fill within about a minute of the signal candle's end (PF 2.28 / 1.85 at -120, 0.94 / 1.66 at -60). On a live path that reads oi from the candle API after the candle closes, the reading lag has to be measured first. The R6 book recorder (5 levels with sizes) can check whether the -120 ask had size behind it.
- The drift version (trailing p90, 67 validation trades) is a cleaner forward definition than the fixed 86.3k, because open interest grows. It is information here, not a new candidate.

## Tries

23 scored variants (core, YES / NO, latency, fill band, C = 1, x1.2, signal +0 / +1c / +2c, sub-5c, drift, stability, favourite, base, volume, move, hour, two volume splits, high volume without doi, top 5 removed, mid path). N added **23**; running count about 563,336 + 23 = **about 563,359**.
