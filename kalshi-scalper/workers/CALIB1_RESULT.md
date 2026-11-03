# CALIB1 result (run once, 2026-11-03): no LEAD; the cheap side loses to its price almost everywhere

Registration `workers/CALIB1_REGISTRATION.md` (sha256 `24a9c230e97e6216a948b2269f1378974af356546999822896e7ffbbf172f6cc`, commit 52f8370, pushed before `score`). Data `workers/CALIB1_RESULT.json`, code `src/scalper/calib1.py`, tests `tests/test_calib1.py`. **Cheap side only (ask 3c to 30c); no favourite-side figure was computed or printed.** Cached development data only, no new Kalshi fetch, frozen thirds untouched (0 frozen markets in the caches).

## Pooled
**16,041 cheap-side entries, 3,535 events, 12,479 markets** (USWEEP1 11,541; USWEEP2 1,308; USWEEP3 575; NEWLIST1 2,617, before deduplication of (market, look)). Life class: D 14,076 entries, W 1,950, H 15 (the sweeps' hourly series barely reach the cheap band, so H says nothing).

Pooled calibration curve, all classes (win rate vs mean price paid, net after fee, event-cluster 95% interval):
| ask | n | events | win | price | win - price | net per contract |
|---|---|---|---|---|---|---|
| 3-5c | 2,217 | 1,285 | 1.4% | 3.5c | -2.1c | -2.43c [-3.10, -1.63] |
| 5-10c | 4,740 | 1,693 | 2.4% | 6.5c | -4.1c | -4.56c [-5.15, -3.91] |
| 10-15c | 3,333 | 1,462 | 5.2% | 11.6c | -6.4c | -7.17c [-8.12, -6.15] |
| 15-20c | 1,902 | 1,170 | 11.6% | 16.9c | -5.4c | -6.37c [-8.07, -4.63] |
| 20-30c | 3,849 | 1,838 | 15.9% | 24.9c | -9.1c | -10.43c [-11.97, -8.89] |

Every bucket's upper bound is below zero. Daily class (D) has the same shape (-2.4, -5.1, -7.3, -6.9, -10.5c). Weekly class (W, 1,950 entries) is the only place a bucket is near zero: 5-10c +0.23c [-3.32, +4.06] (n 458, 180 events), and 15-20c -3.20c [-8.93, +2.89]; both intervals include zero and W 10-15c and 20-30c are clearly negative (-6.45c, -10.10c). Least bad in cents: the 3-5c bucket (-2.4c; it loses because its win rate is a third of its price and the fee is 0.3c). Relatively most overpriced by win-rate/price: 3-15c (win about 0.4 of the price paid); 15-30c win about 0.65 of the price. Worst dollars: 20-30c, driven by Economics (-17.9c on 1,309 entries, 575 events).

## The 40-cell grid (the only claims; N +40)
15 cells NOT_ENOUGH_DATA (Politics, Entertainment, Crypto: under 30 events in a half), **25 NEGATIVE_OR_NO_EDGE, 0 LEAD**. 25 cells have >= 30 events per half; 39 of 40 have any entry (Crypto 3-5c has none). **Cells with net > 0 in both halves: 2** (Sports 5-10c: H1 +0.58c [-4.52, +6.69], H2 +2.96c [-2.82, +9.58], 186 events, lower bounds below zero in both; and Entertainment 15-20c, which is n = 2, two winners, artifact). **Cells with lower bound > 0 in both halves: 0** (the one cell with a whole-sample lower bound above 0 is that n = 2 Entertainment cell). Closest to break-even: Sports 5-10c (all +1.81c [-2.14, +6.24]) and Sports 15-20c (-0.82c [-6.39, +5.30]); Climate and Weather 15-20c H2 -0.83c [-5.73, +4.31]. Worst: Economics 20-30c -17.90c, Economics 15-20c -12.06c, Crypto 10-15c -12.8c (n 31). Weather (1,631 events, the best-powered category): every bucket negative with the whole-sample upper bound below zero except the 3-5c H2 half. Observations only: by time to close, every bucket is negative (<=1h -6.1c, 1-6h -5.5c, 6-24h -7.0c, 1-3d -4.3c, >3d -8.8c); Mentions (18 entries, 5 events) outside the grid +0.42c, no meaning.

## Verdict and use
The prediction held (pooled negative in every bucket; zero LEADs). The cheap side wins about 40 to 65 percent of what it costs; the gap is larger than the fee in every bucket, so it is mispriced AGAINST the buyer (longshots are overpaid for), not just fee-bound. A nearly neutral pocket is Sports at 5-10c and 15-20c (small samples, 90 to 190 events, wide intervals). This is a calibration map, not a signal: a LEAD would only have been a place to look with a mechanism-bearing registered test. N +40.

## Caveats
1. Events overlap in time (the weather ladders of one date across cities, weekly ladders of one week): the event cluster does not remove day or regime correlation, so intervals are still optimistic. 2. The sample is what the earlier sweeps downloaded (60 day window, md5 samples of at most 600 / 40 markets per series, hourly candles for D and W): not every market, and Economics and Weather ladders dominate by count. 3. A quote requires 0 < bid < ask < 1, which drops one sided cheap asks (bid 0); a one sided quote may be the cheapest and most lottery-like entry, so the cheap side as traded may differ. 4. Entry at the candle's last ask, not a fill: no queue, no depth, no spread beyond the ask. 5. Looks are each cache's own and are not comparable across classes; the look-to-close table is descriptive. 6. Cheap side only by the owner's rule: nothing is said about the favourite side. 7. The category list was fixed from entry and event counts printed by `extract` (no outcome aggregated).
