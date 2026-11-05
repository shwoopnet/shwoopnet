# WXDEAD1 result (run once 2026-11-05, US Central afternoon): FALSIFIED

Registration `workers/WXDEAD1_REGISTRATION.md` (pushed before any candle or observation was fetched; commit 5c93196). Code `src/scalper/wxdead1.py`. N +2, running about 730,442, z bar 5.27.

## Numbers first
- Universe as registered: 11 daily-high and 7 daily-low series, closes 2026-08-31 to before 2026-10-03T16:00Z, 612 of 612 events fetched (frozen third never requested), 11 IEM one minute stations (no station dropped). Hourly candles, one batched call per event.
- **Try A (DEAD bracket still bid 3c or more, buy NO at the ask): 220 trades on 189 events, mean +1.16c, profit factor 1.09, clustered z +0.47 (bar 5.27), fees x1.2 +0.98c. D1 +3.39c (n 125), D2 -1.78c (n 95). VIOLATIONS 76 of 220 (34.5%; bar was at most 2%).**
- **Try B (WON bracket, buy YES at ask 97c or less): 13 trades on 13 events, mean +1.30c, PF 1.13, z +0.15, 9 of 13 lost.** Fees x1.2 +1.14c.
- Information (not rules): volume at least 10 candles A 215 trades +1.12c; high days A +(-0.22c) n 193, low days A +10.99c n 27 (9 violations).
- Registered verdict rule: LEAD needs 30 events, +1.0c in both halves, violations at most 2%, z 5.27. Violations and z fail both tries, D2 is negative for A, B has n 13 events (under 30). **FALSIFIED.**

## Why it failed (the useful finding)
The "official observation that already happened" is not the settlement number. IEM's one minute ASOS temperature is a noisy, partly gapped copy of the sensor (about 27,000 to 40,000 readings per station in 34 days, 60 to 90 percent of the minutes) and can read a degree above what the NWS climate report finally keeps. Example: Austin 2026-09-25 high settled at 98F while the one minute readings reached 99F at about 3 PM CT, so the 97 to 98 bracket looked dead from then on, traded at 56c to 99c YES (the market was right) and paid. Most of the 76 violating A trades are exactly this: the book priced the bracket as alive (NO costing 60c to 97c) and was right. Trades with NO price below 20c are 1 to 2 percent of the 220: the real "leftover bid on a dead bracket" the idea looked for was essentially absent, as WX2 predicted for prices. So the structural riskless leg does not exist at 1F resolution on this data; the book reads the climate-report sensor, we read a different one.
- Disclosed bug in an information line only: the registered "margin variant" (dead only if M is at least 1 beyond) was coded in the loosening direction and printed in the saved result (A n 533, -3.54c, 262 violations). Recomputed in the right direction after the run, information only, no try added: margin 1 A n 32 on 27 events, +6.99c, PF 2.26, z 1.6, still 3 violations (9%); B n 3. Margin 2 A n 10, -12.89c. Neither reaches 30 events nor zero violations, so the verdict stands. The registered rules and the primary numbers are unchanged.
- Cheap side only note: A and B buy the high-priced certain side by design (justified in the registration as a fact trade); the 3c to 30c cheap-side rule was not tested here, and no favourite-and-hold research was run.

## Forward / what would change this
Nothing to record: the CLI value is published after the close and one minute data are not that number. A version using NWS hourly METAR/ASOS 5 minute observations (the same product the climate report summarises) is a separate registration; given 34 days of history and the margin result above (9% violations even with 1F of slack) the prior is low. Holdout never read. No forecast recorder or live code touched.
