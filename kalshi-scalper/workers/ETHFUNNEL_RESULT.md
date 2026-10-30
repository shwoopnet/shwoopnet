# ETHFUNNEL result (2026-10-30, measurement, 0 tries; registration `workers/ETHFUNNEL_REGISTRATION.md`)

Read by `src/scalper/ethfunnel.py run` on the 1 minute candles on file (8,111 Ethereum windows, decisions 2026-08-05 6:54 PM CT to 2026-10-30 9:09 AM CT). Decision candle = the candle ending 360 s before the close. No outcome field is read. Times are US Central.

**Short version.** The worst one minute step is the whole story: of 2,273 in-band windows in the last 78 days, 102 (4.5%) had no pullback worse than -0.005; the 4 candle rule and the 0.10 climb rule remove almost nothing (at the 6 minute look a market is 9 minutes old, so there are always at least 4 earlier candles, and a side priced 0.88 or more has nearly always climbed 0.10). Contention with other crypto orders removes about half of history's passing windows but only 1 of 4 on the live days.

## Run A: last 78 days (2026-08-13 9:09 AM CT to 2026-10-30 9:09 AM CT)

| Stage | Windows | Share of all windows | Share of the previous stage |
|---|---|---|---|
| 1 all windows | 7,400 | 100.00% | |
| 2 a side at 0.88 to 0.97 at the look | 2,273 | 30.72% | 30.7% |
| 3 at least 4 earlier candles (alone, on stage 2) | 2,273 | 30.72% | 100.0% |
| 4 worst one minute step -0.005 or better (alone, on stage 2) | 102 | 1.38% | 4.5% |
| 5 climb 0.10 or more (alone, on stage 2) | 2,251 | 30.42% | 99.0% |
| 6 all of the above = the live rule | 102 | 1.38% | 4.5% of stage 2 |
| 7 live rule and no other crypto order first | 50 | 0.68% | 49.0% of stage 6 |

5,127 windows had no side in the band; 0 had no decision candle; 0 had an invalid quote. Stage 6 is 1.31 a day, stage 7 is 0.64 a day.

## Run B: live days, 2026-10-23 1:30 PM CT to 2026-10-30 9:09 AM CT (6.82 days)

| Stage | Windows | Share of all windows | Share of the previous stage |
|---|---|---|---|
| 1 all windows | 647 | 100.00% | |
| 2 a side at 0.88 to 0.97 at the look | 151 | 23.34% | 23.3% |
| 3 at least 4 earlier candles | 151 | 23.34% | 100.0% |
| 4 worst one minute step -0.005 or better | 4 | 0.62% | 2.6% |
| 5 climb 0.10 or more | 150 | 23.18% | 99.3% |
| 6 all of the above = the live rule | 4 | 0.62% | 2.6% of stage 2 |
| 7 live rule and no other crypto order first | 3 | 0.46% | 75.0% of stage 6 |

Stage 6 is 0.59 a day (history 1.31), stage 7 is 0.44 a day. Stage 6 windows: 10/24 6:24 AM, 10/26 7:24 AM, 10/27 1:54 PM, 10/29 9:54 PM CT. Stage 7 drops the last (Dogecoin's band is open in that window). The 10/29 9:54 PM window is after the order export's time (10/29 10:32 AM CT).

## Distribution of the worst one minute step (in-band windows only; the step values themselves)

| | n | min | p5 | p10 | p25 | p50 | p75 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|---|---|
| Run A | 2,273 | -0.4600 | -0.2150 | -0.1800 | -0.1150 | -0.0695 | -0.0300 | -0.0130 | -0.0055 | +0.0300 |
| Run B | 151 | -0.2700 | -0.1900 | -0.1800 | -0.1200 | -0.0750 | -0.0400 | -0.0200 | -0.0100 | +0.0100 |

Histogram (Run A / Run B): below -0.10: 680 / 47; -0.10 to -0.05: 736 / 49; -0.05 to -0.02: 549 / 43; -0.02 up to the threshold (fails): 206 / 8; passes with a pullback: 21 / 0; no pullback at all: 81 / 4. Median in-band window has a worst minute of about -0.07 (a 7 point drop in the bought side's mid at some minute on the way up). Float note about the live comparator (a fact about the code, not a sweep): windows whose worst step is exactly a one cent pullback compute to -0.0050000000000000044 and fail; Run A has 12 such windows that failed and 1 that passed, Run B has 1 that failed.

## Contention (windows where the live gate passes but another crypto order would be taken first; assumes a candidate order fills, so an upper bound)

| | Stage 6 | Blocked | Bitcoin only | Dogecoin only | Both |
|---|---|---|---|---|---|
| Run A | 102 | 52 | 9 | 35 | 8 |
| Run B | 4 | 1 | 0 | 1 | 0 |

## Prediction check

- History pass share about 1.4% of windows (about 1.3 a day): **held**. Stage 6 is 1.38% and 1.31 a day.
- The worst-minute step removes the most in-band windows: **held**. It removes 95.5% of stage 2; the other two stages remove 0% and 1.0%.
- Live days give at least 3 qualifying windows: **held** (4 at stage 6, 3 at stage 7). "In which case contention with Dogecoin explains most of the gap": **did not hold**. Contention accounts for 1 of the 4 live-day windows. The history rate (1.31 a day) would give about 9 stage 6 windows over 6.82 days; the replay found 4 (0.59 a day), so the live days were already thin before any contention. Against the actual order records the replay's Ethereum windows match (below), so the live-day shortfall is mostly the gate meeting a quieter stretch than history (151 in-band windows in 647, 23% against 31%), not contention.

## Parity statement

Checked against a local private export: the nightly report `live_report.json` in the session scratchpad (1,233 order rows, generated 2026-10-29 15:32 UTC), of which only `ts`, `ticker` and `status` were read, never `result`, `settledPnl` or `avgFill`. Counts only, no row committed, no token used. Period 2026-10-23 1:30 PM CT to 2026-10-29 10:32 AM CT, 556 windows per series. XRP records (it was live until 10/28) were treated as holding the window.

| Replica | Disagreements | Share | Kind |
|---|---|---|---|
| Ethereum (stage 7 logic) | 1 | 0.18% | replay would order (10/26 7:24 AM CT), no record |
| Bitcoin (smooth gate) | 1 | 0.18% | replay would order (10/26 10:39 AM CT), no record |
| Dogecoin (band) | 26 | **4.68%** | 19 replay would order, no record; 7 a record where the candle close was not in band |

**Parity gate: STOP rule triggered for the Dogecoin replica (4.68% against the 2% limit).** Per the registration nothing was tuned. The Ethereum and Bitcoin replicas agree with the records on 99.8% of windows (2 Ethereum records, both reproduced; the replay adds one the bot did not make). So stage 6 (the Ethereum gate itself) is verified against live to within one window; stage 7 and the contention counts rest on the Dogecoin replica and are **unverified against live**. Candidate reasons, not tested: the candle close at 360 s is not the quote at the tick (the 7 "record, replay no" windows); the bot had no orders at all from 10/24 10:54 AM to 6:09 PM CT (7.3 hours, 6 of the 19 Dogecoin extras fall there, so it may have been off or stopped); balance, window cap or halt, which the replay does not model; the order export is a report, not a log of attempts. The 10/26 mornings for Ethereum and Bitcoin sit near that same kind of gap. Needed to close it: the owner's Copy all orders export (every attempt, with its note) and the bot's event log for 10/23 to 10/29.

## Re-read

Live-day columns are re-read once on 2026-11-12 with FLIPS0-F. Nothing is scheduled by this note.

No recommendation: the decision on series order, a display label or the gate is the owner's. N stays about 728,648 (0 tries).
