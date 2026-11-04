# OVERROUND1 registration: does the event overround condition the loss of the cheap side? (2026-11-04)

Registered before any outcome was joined. Discovery only: no live code, no `functions/`, no L1, no OICORE, no promote verb. **Owner rule (strict): CHEAP SIDE ONLY, ask 3c to 30c.** No entry above 0.30 is built, counted, scored or printed (code asserts it); no favourite-side result is computed; no 15 minute crypto or gold candle trigger.

## Duplicate check
README and workers searched for "overround", SKEW1, CALIB1, BOOKS1, USWEEP1/2/3, NEWLIST1, ARB1-5, LADLOCK, FAMXV, OICORE_SHAPE_INVENTORY. Only RACELOCK T2 (a sum-of-mids fair share rule for 5 leg races, with a different trade) uses an overround. CALIB1 conditions by category, ask bucket, life class and look-to-close; none conditions a cheap-side entry on the event's sum of YES asks. Not a duplicate.

## Hypothesis and mechanism
CALIB1: the cheap side wins about 0.4 to 0.65 of its price. Hypothesis: that loss sits in HIGH-overround events (thin books padded by market makers: every outcome is quoted rich) and the cheap side of LOW-overround events (competitive books, sum of asks near 1) is near fair or better. Variable derived from Kalshi's own quotes; no outside price.

## Definitions (fixed here)
- **Event and outcomes:** the markets of one event (ticker without its last dash segment) in the USWEEP1 census that is a mutually exclusive partition by STRUCTURE (no outcome used): at least 4 outcomes, at least 3 brackets (`-B...`) and exactly 2 open ends (`-T...`), nothing else, series not `capped`, all outcomes with candles in the cache, one common anchor. Nested "above K" ladders are excluded (not exclusive).
- **Overround** at a look = sum over ALL outcomes of the YES ask (latest candle at or before the look, at most one period old; 0 < ask < 1, bid 0 allowed) minus 1. If any outcome has no such ask the event-look has no overround and is dropped.
- **Cheap-side entry:** CALIB1's rule: for each outcome the side whose ask is in [0.03, 0.30] on a two sided quote (0 < bid < ask < 1; NO ask = 1 - bid), bought at the ask, held to settlement. Per event-look at most **2** entries: the two with the smallest md5(ticker). Fee 7% x C x p x (1-p) rounded up to the cent, C = 10.
- **Looks:** the cache's own (class D: 1440, 360, 60 minutes before the anchor; none added or chosen). A look with fewer than 30 event-looks has no tercile and is dropped (counts reported).
- **Terciles:** within each look, event-looks sorted by anchor time (then event id); the lower and upper cut are the 1/3 and 2/3 quantiles (`sorted[int(n/3)]`, `sorted[int(2n/3)]`) of overround over the **first two thirds only**; applied to all. LOW is overround below the lower cut, HIGH at or above the upper cut. Never refit.
- **Frozen third:** nothing with an anchor or close at or after 2026-10-03T16:00Z (1791043200) is read; the cache holds none (asserted in code).
- **Cluster:** the event (one look per event survives in the cache, so event = day-city).

## Structure census (no outcome read; `python3 -I -m scalper.overround1 census`)
872 events (872 event-looks) from 48 weather-temperature series, 28 distinct dates. Only the 1440 minute look (T1440) keeps 30 event-looks (T360 and T60 have 16 each: hourly candle gaps leave an outcome unquoted), so the rule is effectively one look. Overround quantiles 5/25/50/75/95: 3, 6, 9, 13, 27 points; 6 negative. Cuts 0.07 and 0.12. Picked cheap entries per tercile: **LOW 402, MID 550, HIGH 470** (254, 336, 282 events). Over the 150 floor, so runnable. USWEEP2 and USWEEP3 caches hold 1,200 and 1,285 sampled markets (md5 sample, at most 40 per series), no event with its siblings complete (0 events with at least 4 outcomes all cached); NEWLIST1 has 0 complete events of 9,744. They add nothing; no new Kalshi fetch.

## Trade, statistic, prediction
Trade: buy the cheap side (rule above) of LOW-tercile events, held to settlement. Statistic: mean net per contract after fees, win rate vs mean price, profit factor (sum of positive nets over sum of negative nets), event-cluster bootstrap 95% interval (2,000 draws, seed 20261104), halves by event time within the group. Controls (descriptive): ALL cheap sides, MID, and HIGH as the placebo; LOW minus HIGH with a cluster interval; development-third-only table (the cut was fitted there).

**Numeric prediction (before any outcome):** LOW mean net -3c to -5c per contract (win rate about 0.5 to 0.7 of price), PF 0.3 to 0.6; HIGH not clearly worse than LOW (gap under 2c with an interval containing 0); verdict FALSIFIED. Prior that LOW is positive in both halves with PF at least 1.5: 3%.

## Kill rules
- **NOT_ENOUGH_DATA** if the LOW group has under 150 trades.
- **FALSIFIED** if LOW mean net after fees is not above 0 in BOTH halves, or its PF is under 1.5.
- Otherwise LEAD_FOR_FORWARD_TEST only (a place for a pre-registered forward test; the z bar of about 5.27 is not claimed on this sample, 28 dates, one family).
Read once; `score` refuses a second run (`workers/OVERROUND1_RESULT.json`). No look, tercile, structure or per-event cap is changed after the first outcome.

## Forward plan (if NOT_ENOUGH_DATA or a LEAD)
New temperature events after 2026-10-03T16:00Z (the frozen third) are read only by a forward registration naming the cuts above (0.07, 0.12 at T1440) before they are opened; a record of overround at the look is also the only new variable to log.

## N
**N +2** (one rule, LOW cheap side; the placebo and control are descriptive and charged nothing).

Code `src/scalper/overround1.py`, tests `tests/test_overround1.py` (synthetic only).
