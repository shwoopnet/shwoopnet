# XETH1 result (scored once 2026-11-04; registration `workers/XETH1_REGISTRATION.md` sha256 28cc8fb9...6b03, commit 178e5d8, before any candle or outcome; code `src/scalper/xeth1.py`, tests `tests/test_xeth1.py`; printout `studies/xeth1_result_2026-11-04.txt`, raw `workers/XETH1_RESULT.json`)

**Verdict: NOT_ENOUGH_DATA** (8 filled trigger trades of 150; 5 trigger events in 986 development closes, 0.19 trades a day, about 746 more days at that rate). Cheap side only; no favourite-side result computed.

Data: OKX BTC-USDT and ETH-USDT 1 minute klines (60,700 each), 986 hourly KXETHD closes in the development period (42 dates, 2026-09-02 to 2026-10-13 closes; last third dropped before any listing), 299 listings, 1,782 strike candle series. Trigger classes over the 986 closes: TRIG 5, F (BTC beyond 2 sd and ETH followed) 78, NONE 903; control sample 215 events by md5 mod 4.

| group | half | n | win | paid | PF | PF x1.2 | mean/contract |
|---|---|---|---|---|---|---|---|
| TRIG | H1 | 4 | 0.0% | 13.8c | 0.00 | 0.00 | -14.6c |
| TRIG | H2 | 4 | 0.0% | 9.2c | 0.00 | 0.00 | -9.9c |
| TRIG | all | 8 | 0.0% | 11.5c | 0.00 | 0.00 | -12.3c |
| control | H1 / H2 | 172 / 160 | 7.6% / 8.7% | 12.3c / 11.8c | 0.53 / 0.66 | 0.52 / 0.65 | -5.5c / -3.8c |
| control | all | 332 | 8.1% | 12.1c | 0.59 | 0.58 | -4.7c (z -2.93) |
| F (info) | H1 / H2 / all | 66 / 59 / 125 | 19.7% / 10.2% / 15.2% | 13.0c / 12.4c / 12.7c | 1.57 / 0.74 / 1.16 | 1.55 / 0.73 / 1.14 | +5.9c / -3.0c / +1.7c (z +0.45) |

Prediction check: trigger rate predicted 0.2 events a day, got 0.12 events a day (5 in 42 days, the low edge of 0.1 to 0.6); NOT_ENOUGH_DATA predicted and found. Control PF 0.59 against the predicted 0.7 (the unconditional hourly cheap tail loses, as LADLONG1 PF 0.64 / 0.72). With 8 trades, nothing about the trigger can be read; the 0 of 8 wins is consistent with the control's 8% win rate (chance of 0 of 8 at 8% is about 51%). The information group F (ETH did follow) is flat: pooled +1.7c, z +0.45, halves +5.9c / -3.0c, nowhere near the bar.

Implementation notes (not rule changes): listings were fetched only for the needed closes (all TRIG, all F, the control sample), with the event ticker derived from the close time in New York time and verified against the 19 listings first fetched; the OKX klines cover the 25 hours before each look; candles fetched with 429 backoff. Seven closes at Eastern hours 02 to 05 had empty listings (no hourly event then).

Forward plan: none. At 0.12 trigger events a day (about 0.19 trades a day) 150 trades need roughly 2 years, so a history or forward read of THIS trigger cannot ever finish; loosening the trigger (for example 1.5 sd) would be a new registered try. Probe spec: none, both halves not positive. N +2, running about 730,232 (z bar 5.27). Killed assumption: a Bitcoin lead leaves the hourly ETH ladder's cheap side underpriced; the trigger is too rare to test, and the unconditional ETH tail is -4.7c.
