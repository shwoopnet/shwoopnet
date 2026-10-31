# WXNEW1 result (scored once, 2026-10-31 03:30 UTC = 10:30 PM Central on Oct 30)

Registration: `workers/WXNEW1_REGISTRATION.md` (pushed before any fetch; four amendments, each pushed before any candle or outcome for scoring was read; amendment 4 followed a look at fetched-event COUNTS only). Ledger check: `workers/WXNEW1_LEDGER_CHECK.md`. Code: `src/scalper/wxnew1.py` (`fetch`, then `run`, refused a second time). Raw output (not committed, `data/` rule): `data/wxnew1_result.txt`.

## 1. Angles: what is new, what is runnable

| Angle | NEW / REWORD | RUNNABLE? | Outcome |
|---|---|---|---|
| (a) NWS vs The Weather Company settlement mismatch on daily highs | REWORD of the Director's Oct 29 check (0 mismatches in 67 days, NY and Chicago) | NOT_RUNNABLE as a trade (nothing to trade where the mismatch is zero; TWC history elsewhere exists only as the settled bracket) | Not tried |
| (a') Same question on the hourly TWC-station series (rounded ASOS vs TWC reading) | NEW | RUNNABLE but small: 5 series, 19 days, series stopped 2026-09-10 | Try WXH-TWC: **NOT_ENOUGH_DATA** (only 90 of its 2,090 events were fetched; 0 trades) |
| (b) Forecast-update lag, price vs latest model revision | REWORD of WX1 (market right, -4.70c, z -4.17) | RUNNABLE in principle (NBS archive, Open-Meteo previous-runs), not run | Not tried |
| (c) End-of-day bracket vs running observed maximum | REWORD of post-peak certainty (dead, 0.99 / 1.00) and WX2 (no quote left in 80c to 98c) | NOT_RUNNABLE (international highs have no settled market in the window) | Not tried |
| (c') Last-30-minutes nowcast of the HOURLY temperature ladders from public one-minute ASOS | NEW (ten strikes a degree apart, prices 5c to 95c at the look, not post-peak) | RUNNABLE | Try WXH-SYN: **FALSIFIED** (Miami) |
| (d) Monthly / weekly cumulative markets | NEW | NOT_RUNNABLE: monthly series have about 2 settled months; weekly average temperature has 8 events per city in 68 days | Not tried; NOT_ENOUGH_DATA, could be met about 2027-04 for weekly average temperature |
| Daily lows, daily rain | REWORD of WX1's mechanism (Director Oct 29) | Not examined further | Not tried |

## 2. Scored results (numbers from the one run)

**WXH-SYN, the Synoptic-index hourly ladders.** Of 4 series only Miami (`KXTEMPMIAH`) had the 100 fetched discovery events its fit needs (542 events fetched of 535 + others; the other three Synoptic series had 50 to 53 fetched events and 17 to 21 usable discovery events each, so by the registered rule they received no trades and are NOT_ENOUGH_DATA). The verdict is therefore **for Miami only**.

| Window (Miami, close hours 01 / 04 / 07 / 10 / 13 / 16 / 19 / 22 UTC only) | Trades | Needed | Mean net per contract | PF | Event-clustered z | Day-clustered z | Fees x1.2 mean / PF |
|---|---|---|---|---|---|---|---|
| Discovery (2026-08-23 to 2026-10-04, 41 days with trades) | 399 | 100 | -3.47c | 0.82 | -1.55 | -1.33 | -3.74c / 0.80 |
| Validation (2026-10-04 to 2026-10-19, 15 days) | 127 | 50 | -6.00c | 0.68 | -1.73 | -1.74 | -6.25c / 0.67 |
| Pooled discovery + validation | 526 | | -4.08c | 0.78 | -2.16 | -1.90 | deflated bar 5.27 not reached |
| Holdout (2026-10-19 to 2026-10-31) | not read (discovery and validation failed the PF bar) | 30 | | | | | |

Information: fitted Miami offset b +0.134 F, trend coefficient k -0.022, sigma 1.51 F on 301 usable discovery events. Mean price paid 0.37 (discovery) and 0.32 (validation); YES share of trades 0.49 and 0.54. **Brier score of the nowcast 0.159 (discovery) and 0.212 (validation) against 0.086 and 0.091 for the market mid on the same quotes** (1,246 and 330 quotes): the market is far better informed than a persistence-plus-trend model from two public ASOS stations, as the registration predicted (the numeric prediction was -3c to -6c, PF below 1, Brier within 10%; the loss matched, the Brier gap was much larger than the 10% guessed). The loss is the 4c to 6c quoted spread, the fee, and a nowcast that is worse than the quotes. The Synoptic metro index is not visible from the airport ASOS stations.

**WXH-TWC, the five TWC-station hourly ladders (KNYC, KORD, KLAX, KAUS, KDCA).** 90 events fetched (18 per series, 26 usable in discovery), no fit had 100 events, 0 trades: **NOT_ENOUGH_DATA**. This is a fetch shortfall, not a shortage of history: the 2,090 events (about 700 after the clock thinning) exist and finishing the download would take roughly 60 more minutes at the observed rate. On Miami's trade yield (about 1.2 trades per usable discovery event) it would give discovery counts above 100. The prediction for it stays FALSIFIED. A side result of the data that were fetched (info only): the rounded ASOS reading 30 minutes before the close equalled the settled value in 2 to 4 of 11 events per city, which says the 30 minute move dominates and says nothing yet about a rounding mismatch at the close itself.

Tries: 2 (WXH-SYN, WXH-TWC). Running count N: about 728,677 + 2 = **728,679**; deflated z bar about 5.27.

## 3. What this closes and what it leaves

- Closed (FALSIFIED): a persistence-plus-trend nowcast from public one-minute ASOS data against the Miami hourly temperature ladder, at 30 minutes before the close, edge threshold 6c, taker at the ask: -4.08c a contract (z -2.16), PF 0.78. The Chicago, New York and coastal Los Angeles Synoptic ladders were NOT tested (50 fetched events each).
- Not closed: the other three Synoptic ladders and the five TWC-station ladders (fetch shortfall, same rule, same prediction). Re-running them needs the download to be finished, then the one run; no new try.
- Everything weather that was not new stays where the ledger put it: forecast against market (WX1, FALSIFIED), ladder arbitrage (WX3, FALSIFIED), post-peak certainty (dead), settlement mismatch on daily highs (none in 67 days).

## 4. Proposed README section (not applied; README.md untouched)

> ## Result: WXNEW1 (2026-10-31), hourly temperature ladders against a public one-minute ASOS nowcast: FALSIFIED (Miami)
>
> Registered first (`workers/WXNEW1_REGISTRATION.md`, four amendments before any scoring), ledger check `workers/WXNEW1_LEDGER_CHECK.md`, result `workers/WXNEW1_RESULT.md`, code `src/scalper/wxnew1.py`. New weather family: Kalshi's hourly "temperature above K" ladders (Miami, Chicago, New York, coastal Los Angeles settled by Synoptic Data; five TWC-station cities for 19 days in Aug and Sep). Not a reword of WX1 (forecast against price), WX3 (ladder arbitrage) or post-peak certainty (prices are 5c to 95c at the look). At 30 minutes before the close, a persistence-plus-trend forecast from one-minute ASOS temperatures against the quotes, 6c edge, taker at the ask, fee at C = 10, fees x1.2. Because of Kalshi's rate limit only a clock-thinned third of events could be downloaded and only Miami had enough (542 events) for its fit. Miami: discovery 399 trades, -3.47c, PF 0.82; validation 127 trades, -6.00c, PF 0.68; pooled z -2.16 against a deflated bar of 5.27; holdout not read. The nowcast's Brier score is 0.16 to 0.21 against 0.09 for the market: the quotes know more than public airport readings. The other Synoptic ladders and all five TWC ladders are NOT_ENOUGH_DATA (download not finished), not tested. Two daily-high angles were closed without a try (settlement mismatch: Director Oct 29, zero in 67 days; forecast-update lag: a reword of WX1). Weekly average temperature and monthly markets are NOT_ENOUGH_DATA (8 events per city in 68 days; about 2 settled months). Tries +2, running count about 728,679 (z bar 5.27).
