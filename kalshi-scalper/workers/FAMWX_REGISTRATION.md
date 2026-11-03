# FAMWX registration and result: weather daily highs/lows against a public keyless forecast (2026-11-03)

Status: **DUPLICATE. No new try, no code, no data fetched, N unchanged (about 728,726 as of QSTALE1; z bar about 5.27).**

## 1. Duplicate check (grep of README.md, workers/WXNEW1*, RAINCAL*, OICORE_SHAPE_INVENTORY.md; TEMPHR* and other WX* files do not exist)

The exact test (Kalshi KXHIGH*/KXLOW* city ladder priced against a public forecast, taker at the ask, hold to settlement) was run twice and failed both times:

- **WX1 (2026-10-13, Open-Meteo previous-day-1 forecast)**: 7 cities, -3.3c, z -2.5, listed under "Tried and failed".
- **WX1 rerun (2026-10-22, NWS National Blend of Models 12Z run of D-1, normal with the blend's own sigma)**: 1,197 trades over 67 days, **-4.70c, day-clustered z -4.17**, both halves negative, fee x1.2 -4.91c, 1 of 7 cities positive; the 3c-threshold version -4.26c, z -4.74, 0 of 7. Calibration by decile was fine; every disagreement loses: where the forecast and the market differ, the market is right.
- WX2 (late-day certainty): by 6 hours before the close no bucket is quoted in 80c to 98c. Post-peak: brackets already 0.99/1.00 at 8:35 PM ET (37 decided LAX cases all 1.00). Both close the "observed max so far vs strike ladder" input.
- WX3 (ladder arbitrage, 10 cities): 1 lock in 2,698 hours, FALSIFIED. WXNEW1 (hourly ladders, ASOS nowcast): Miami -4.08c, z -2.16, market Brier 0.086 vs nowcast 0.159; the other cities NOT_ENOUGH_DATA (fetch shortfall). Scout/FLB1: weather -0.38c / -2.80c. Settlement check: Kalshi highs matched the NWS climate report on 67 of 67 days.
- RAINCAL (KXRAIN against NWS PoP): already registered 2026-10-31 as a forward test, recorder on review branch `claude/v2-recorder-raincal`, one read 2027-01-01.
- Daily lows (KXLOWT*): the Director (Oct 29) and WXNEW1 ledger check call them a reword of WX1 plus post-peak (the low is observed by mid morning, so the same 0.99/1.00 shape). Never run, never needed a try.

## 2. The assumption that killed it, and what input would be different

Killed assumption: that the retail price of a round-number strike lags a public point forecast. Measured: the market is at least as informed as the best free point forecast (blend of models, newest runs, live observations), and it charges a 4c to 6c spread plus fee on top. Information arriving later in the day (observations) is already priced to 0.99/1.00 before a public hourly source can see it.

Different inputs considered and why none is a cheap first pass today:
- **Ensemble spread** (Open-Meteo ensemble API, keyless): only improves sigma of a forecast the market already beats; there is no archive of past ensemble runs to score 68 days, so it would need a forward recorder. A recorder-only item, not run.
- **Forecast revision timing**: reword of WX1 at another hour (WXNEW1 ledger, angle b). The market was already right with the freshest run used.
- **Observed max so far vs strike ladder**: closed by WX2 and post-peak (nothing left in 80c to 98c).
- Daily lows: same shape, same verdict expected (prior of passing under 3%).

Verdict: **DUPLICATE** of WX1 (twice), WX2, WX3, post-peak, WXNEW1. The only open weather items are already registered: RAINCAL forward read 2027-01-01, WXH-TWC/WXH-SYN remaining cities (finish a download, one run, no new try), weekly average temperature (about 2027-04).

## 3. Smallest honest live probe (stated; NOT recommended, nothing to probe on temperature)

- Temperature highs/lows: **no probe**. -4.70c at z -4.17 on 1,197 trades is a measured loss; a live probe would only pay it.
- Rain is the only weather rule without a historical verdict, and its forward data already stands in for a probe. If the owner insists on money before 2027-01-01: RAINCAL's rule exactly (7:00 AM local standard time look, buy YES only at an ask at least 8c below the NWS PoP or NO at a bid at least 8c above it), **1 contract, hard limit price: ask or complement at most 0.60 (never buy above 60c)**, at most 6 orders a day. **Kill rule:** stop at 40 fills if PF under 1.2, or at any cumulative loss of $15. **Worst day:** 6 x (0.60 + fee 0.02) = **$3.72** (all lose). **40 fills:** RAINCAL predicts 250 to 450 trades in 60 days, i.e. 4 to 7 a day, so 40 fills exist about 6 to 10 days after the first live order. 40 fills prove nothing about a 1.5 profit factor (needs 300 trades per the bar); it is a plumbing and fill-quality check only. Prior that it clears the full bar (PF 1.5 in three windows, deflated z 5.27): under 3%.

## 4. Data/owner action

None needed for temperature. For rain: merge `claude/v2-recorder-raincal` so the recorder runs (the forward test starts only when it does). No registration hash beyond the commit that adds this file (see report).
