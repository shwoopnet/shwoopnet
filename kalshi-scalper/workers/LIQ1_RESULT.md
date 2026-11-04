# LIQ1 liquidity result (run once, 2026-11-04): FALSIFIED both rules; tight spread and busy candles rank the loss but do not remove it

Registration `workers/LIQ1_REGISTRATION.md` (sha256 `e57fb2d116a660881dca8378e7fea851e5efc9f1a305c68116aecadafe645004`, commit 770c9e0, pushed before `score`). Data `workers/LIQ1_RESULT.json`, code `src/scalper/liq1_spread.py` (not liq1.py, which is the earlier liquidation check), tests `tests/test_liq1_spread.py`. **Cheap side only (ask 3c to 30c); no favourite-side figure computed.** Cached development data, no new fetch, frozen third untouched. Cuts fitted on the first two thirds of events: spread 2.0c and 5.0c, volume 0 and 30.93.

Pool 16,201 cheap entries, 3,558 events. Max 2 per event; event-cluster 95% intervals; net after fee per contract.

| group | n | events | win | price | win - price | net [95%] | PF | D1 net | D2 net | out-of-fit third net |
|---|---|---|---|---|---|---|---|---|---|---|
| TIGHT (spread <= 2c, trade) | 3,544 | 2,230 | 8.61% | 10.72c | -2.11c | -2.79c [-3.84, -1.72] | 0.71 | -2.97c | -2.61c | -2.29c |
| HIGHV (volume > 30.93, trade) | 2,754 | 1,770 | 9.59% | 13.46c | -3.87c | -4.68c [-5.80, -3.50] | 0.62 | -4.79c | -4.58c | -3.91c |
| WIDE (spread >= 5c, placebo) | 3,362 | 2,052 | 7.82% | 16.85c | -9.02c | -10.01c [-11.07, -8.97] | 0.38 | -9.04c | -10.90c | -10.88c |
| LOWV (volume 0, placebo) | 4,152 | 2,450 | 7.32% | 13.58c | -6.26c | -7.08c [-8.03, -6.19] | 0.45 | -6.52c | -7.60c | -7.70c |
| CONTROL (all cheap) | 6,515 | 3,558 | 8.29% | 13.49c | -5.21c | -6.02c [-6.81, -5.23] | 0.52 | -5.28c | -6.75c | -6.85c |

## Verdict
**TIGHT: FALSIFIED** (net negative in both halves, interval entirely below zero, PF 0.71 against 1.5). **HIGHV: FALSIFIED** (PF 0.62, both halves negative). Neither is a LEAD; no forward trade. The prediction (TIGHT about -2c to -6c, FALSIFIED) held; TIGHT came in at the optimistic end, HIGHV in the middle.

## What it does show (observation, not a claim)
The loss ranks monotonically with the liquidity score: TIGHT -2.8c, CONTROL -6.0c, WIDE -10.0c, a gap of 7.2c between tight and wide that is stable in D1, D2 and the out-of-fit third. Busy candles (HIGHV -4.7c) beat untraded ones (LOWV -7.1c). Same picture as OVERROUND1: the cheap side is overpriced most where the book is stale, and even in the best tercile the win rate (8.6%) is 2.1c under the price paid and the fee (about 0.7c) makes it worse.

## Caveats
1. **Price confound.** TIGHT entries average 10.7c against 16.9c for WIDE: a 1c to 2c spread is common at 3c to 10c asks and rare at 20c to 30c, and CALIB1 already showed the 20c to 30c bucket is the worst in cents. So part of the ranking is the ask bucket, not liquidity itself; the ask mix per group is in the JSON (`ask_mix`) and no price-matched comparison was registered. 2. Same sample as CALIB1 (60 day window, md5 samples per series, Weather and Economics ladders dominate by count; NEWLIST1 has grown to 2,777 entries since CALIB1's 2,617). 3. 65% of entries have zero candle volume, so "volume" is mostly "did the look candle trade"; the hourly and daily candles are coarse. 4. Entry at the candle's last ask, not a fill; no queue or depth. 5. Events overlap in time (weather ladders across cities), so intervals are optimistic. 6. Cheap side only by the owner's rule.

## Forward plan
None as a trade. If the ordering is ever used it is a filter inside another registered rule, never an entry; a forward read would log spread and look-candle volume on new events after 2026-10-03T16:00Z against the fixed cuts (2.0c, 5.0c, 0, 30.93). N +4.
