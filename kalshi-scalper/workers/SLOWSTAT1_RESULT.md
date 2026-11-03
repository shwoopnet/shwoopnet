# SLOWSTAT1 result (2026-11-03): NOT_RUNNABLE

No outcome, price or candle was joined; the rule was not scored. `python -m scalper.slowstat1 census` (listings only, events closing before 2026-10-03T16:00Z, historical and live tiers):

| series | markets | events | scoreable markets (last third, 20+ contracts, 12+ events) |
|---|---|---|---|
| KXADP | 136 | 19 | 47 |
| KXEGGS | 19 | 19 | 7 |
| KX10YRDIRHM | 60 | 2 | 0 |
| KXUSDINRAW | 410 | 10 | 0 |
| KXTEMPHELP | 27 | 5 | 0 |
| KXPOWERKWH, KXUSHOME, KXNFCI, KXCFNAI, KXDATACENTCON, 5 menu-price series | 7 to 36 each | 1 to 6 | 0 |

Total 54 scoreable markets, an upper bound on trades, against the 150 minimum; the cheap-side filter would leave a fraction of 54 on 14 events. The same sweep found the rest of the slow-statistic list already tested (gas, claims, mortgage, TSA, Spotify, quakes, Fed funds) or dead (zero volume: AMSAVO, DDR5, B200, USDNOK, 30 year hourly). Kalshi lists these monthly series only since mid-2026, so the idea cannot be tested on history; it waits for events to accumulate.

Forward plan: rerun the census on 2027-02-01; run the registered rule only if one reference-backed series has 12 or more events before the cut and the scoreable total is 150 or more (KXADP alone would take until about 2028 at one event a month). No recorder needed. Pooled win rate versus price, PF versus control: not computed. N +2 (one rule registered, never scored), running count about 730,287, z bar 5.27.
