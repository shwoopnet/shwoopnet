# OVERROUND1 result (run once, 2026-11-04): FALSIFIED as a trade; the overround does rank the loss

Registration `workers/OVERROUND1_REGISTRATION.md` (sha256 `58084d4b8589422c825e800f9d383744d8e52fd94ec227ad527c2842932cf457`, commit 9b3d63a, pushed before `score`). Data `workers/OVERROUND1_RESULT.json`, code `src/scalper/overround1.py`. Cheap side only (ask 3c to 30c); no favourite-side figure computed. Frozen third untouched, no new Kalshi fetch.

Sample: 872 weather-temperature events (48 series, 28 dates), one effective look (T1440), cuts 0.07 and 0.12. Cheap entries (max 2 per event, smallest md5): LOW 402 (222 events with a cheap side), MID 550, HIGH 470, ALL 1,422 (786 events).

| group | n | events | win | price | win - price | net per contract [event-cluster 95%] | PF | half 1 net | half 2 net |
|---|---|---|---|---|---|---|---|---|---|
| LOW (trade) | 402 | 222 | 10.95% | 11.79c | -0.84c | -1.58c [-4.77, +1.79] | 0.85 | -2.84c | -0.26c |
| MID | 550 | 309 | 7.64% | 11.64c | -4.01c | -4.73c [-7.05, -2.24] | 0.56 | -4.53c | -4.93c |
| HIGH (placebo) | 470 | 255 | 6.81% | 13.50c | -6.70c | -7.52c [-9.65, -5.11] | 0.42 | -8.14c | -6.90c |
| ALL (control) | 1,422 | 786 | 8.30% | 12.30c | -4.00c | -4.76c [-6.26, -3.19] | 0.58 | -5.71c | -3.80c |

LOW minus HIGH: +5.9c per contract, event-cluster 95% [+1.8, +9.9]. Development third only (where the cut was fitted): LOW -0.14c (PF 0.99), MID -4.0c, HIGH -8.5c.

## Verdict
**FALSIFIED** by the registered rule: LOW net is negative in both halves (-2.84c, -0.26c) and PF 0.85 is far under 1.5. The prediction (LOW -3c to -5c) was too pessimistic for LOW (-1.6c) and wrong on HIGH (HIGH is clearly worse, the gap interval excludes 0). The hypothesis half "loss concentrates in HIGH overround" holds: monotone LOW -1.6c, MID -4.7c, HIGH -7.5c, in both halves; the half "LOW is near fair or better" is only near fair: win 10.95% against a price of 11.79c, interval spanning zero, and the fee (about 0.7c) is the whole remaining gap. Not a LEAD, no forward trade. The finding is an OBSERVATION for the calibration map: within temperature brackets the richly quoted books are where the cheap side is most overpriced.

## Caveats
One family (daily temperature brackets, 28 dates), so dates and cities are correlated; the event cluster does not remove that. Overround here is mostly a function of how many brackets are quoted rich at 24 hours; only the T1440 look survived (hourly candle gaps). Entries are at the candle's last ask, no fill model. LOW has only 222 independent events. 

## Forward plan
Not worth a trade test. If the monotone ordering is to be used, only as a filter inside some other registered rule (never a standalone entry); a forward read would log overround at the 24 hour look on new temperature events after 2026-10-03T16:00Z against the fixed cuts 0.07 and 0.12. N +2.
