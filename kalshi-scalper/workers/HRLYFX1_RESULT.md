# HRLYFX1 result (2026-11-04): NOT_RUNNABLE (census), cheap side only

Nothing registered (registration is only for a runnable test). No candle, outcome or reference price was fetched or joined; the frozen third (closes from 2026-10-03T16:00Z) was excluded from the listing query. Cheap side only; no favourite-side result computed. No promote verb.

## Duplicate check
Not a duplicate. Hourly FX/silver/WTI ladders with a spot nowcast were never tested: SETTLE1 (result, line 45) lists `KXEURUSDH`, `KXWTIH`, `KXSILVERH` as untried and says a ladder test needs a different mechanism than "the quote lags"; WTIW1 says hourly KXWTIH and KXSILVERH not tried; FXREF1 was NOT_RUNNABLE on the reference; COMDAY1 was daily; ALTLAD1 (crypto hourly, Student-t, 3x ratio) is the same rule on other coins and its rule B was clearly losing (104 treated, -4.35c, PF 0.29, win 1.9% vs model 21.7%).

## Census (settled listings and close times only), 2026-09-04 to 2026-10-03T15:59Z
| series | events | markets |
|---|---|---|
| KXEURUSDH | 0 | 0 |
| KXUSDJPYH | 0 | 0 |
| KXSILVERH | 449 | 18,195 |
| KXWTIH | 472 | 19,428 |

FX hourly has no settled markets at all in the Yahoo 5-minute window (consistent with FXREF1: FX history starts 2026-09-23 in other series and the hourly FX tickers list nothing here), so FX is dropped. Silver and WTI: 921 events, about 40 markets per event, closes 2026-09-04T00:00Z to 2026-10-02T21:00Z.

## Expected treated trades (prior from ALTLAD1, no outcome used)
ALTLAD1 treated rate: 104 of 12,008 strikes with model probability 0.03 to 0.97 at the 10 minute look (0.87%), 29 at the 30 minute look (0.24%). Generously assume 12 such strikes per silver/WTI event (a 40-strike ladder has most strikes far from the money): 921 x 12 x 0.87% is about 96 at 10 minutes and about 27 at 30 minutes, before dropping looks whose 5-minute reference window has a gap (silver and WTI have a daily break) and before the cap of 2 per event. Both are under 150. Even if the density were double, the 10 minute rule on crypto was losing, not a near miss.

## Verdict and forward plan
`NOT_RUNNABLE` / `NOT_ENOUGH_DATA` (expected treated about 100 at best, about 30 at 30 minutes, against 150). Win vs price and PF vs control: not computed. Forward plan: a keyless Yahoo 5-minute spot recorder (RECPLAN1 item 1) for SI=F, CL=F, EURUSD=X and USDJPY=X plus hourly ladder quote capture would give, at the same rate, about 100 treated trades per 30 days at the 10 minute look (silver and WTI together, about 460 events a month), so a read after about 45 days; but ALTLAD1's sign and SETTLE1's "silver and WTI quotes equal their reference at 2 to 3 minutes" make a pass unlikely (prior under 3%), so the recorder is not recommended on this idea alone. N +0 (no rule registered).
