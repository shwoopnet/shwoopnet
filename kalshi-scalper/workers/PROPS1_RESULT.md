# PROPS1 result (2026-11-04): NOT_ENOUGH_DATA (candle access, not the model), cheap side only

Registration `workers/PROPS1_REGISTRATION.md` (sha256 `48a5e1ccde90282c1842decfb30555bf41533e60330ea5c9afc1352e8334d759`), pushed before any candle or box score was fetched. Code `src/scalper/props1.py`, tests `tests/test_props1.py` (11 pass). Data `data/props1.sqlite` (git-ignored); raw numbers `workers/PROPS1_RESULT.json`. N +2. Frozen games (from 2026-10-03T16:00Z) were never fetched or joined.

## What was built and run
- ESPN box scores (1 req/s, descriptive User-Agent): NBA 1,320 games (2025-26), WNBA 2025-26, NFL 2025 season and 2026 weeks 1 to 4 (6 box scores returned 404).
- Kalshi listings (no candles) of the 12 series before the cut: 131,856 settled markets; player-name to box score match rate NBA 98.3%, WNBA 98.1%, NFL 96.8%.
- Matched games per league: NBA 1,082, WNBA 340, NFL 256; FIT first two thirds (721, 226, 170), TEST last third in halves T1 and T2 (180+181, 57+57, 43+43 = 560 TEST games).
- Fit on FIT ESPN stats only (no Kalshi data): k = 1 in all 12 family fits (almost no shrinkage), r = 4 to 8 for basketball, and r = 1 (the edge of the registered grid) for the NFL yard stats, which means the negative binomial is a poor shape for yards (disclosed; k and r were not retuned).
- 21,380 TEST markets in the sha1 sample (40 per game). **Only 1,099 of them (304 games) had their candles fetched**: Kalshi's historical candle endpoint answered one market per request at roughly 4 to 15 seconds each under polite use (about 12 markets a minute after rate-limit backoff), so the 17,932 historical requests would take about 25 to 30 hours. I stopped at the time budget; the order of fetching was by sha1 of the player-game, so the 1,099 are an outcome-blind subset.

## Result on the fetched subset (information only; below the 150-trade bar)
| | n | games | mean net (c) | win | price | PF |
|---|---|---|---|---|---|---|
| Treated (model >= 3x ask, max 2 a game) | **9** | 9 | +4.5 (SE 10.6) | 11.1% | 6.1c | 1.76 (T1 -7.5c n 5; T2 +19.6c n 4) |
| Control, cap 2 a game | 397 | 246 | **-4.87 (SE 1.67), z -2.9** | 12.9% | 16.7c | 0.68 (T1 -4.5c, T2 -5.3c) |
| All cheap sides | 550 | 246 | -4.05 (SE 1.49) | 13.6% | 16.7c | 0.72 |

Verdict: **NOT_ENOUGH_DATA** (9 treated trades against 150; no inference from them). Treated trades are rare: 9 of 1,099 fetched markets (0.8%), so the full sample would give roughly 150 to 200 before the 2 per game cap, about the bar, and needs the 25 to 30 hours of polite fetching.

## Information that did not need candles (model calibration on all 55,098 TEST markets with a model probability)
The model UNDER-predicts: model chance 0.151 (bucket 0.1 to 0.2) won 15.6%; 0.272 won 29.4%; 0.422 won 47.8%; 0.593 won 65.9%; 0.791 won 81.4%; far tail 0.009 won 3.6% and 0.035 won 6.1%. NFL is worst (0.009 predicted, 7.7% won; 0.42 predicted, 54% won). So the 3x ratio is inflated in the upper-middle by a biased model, not by a market error; fixing the model needs a second registration. Control cheap sides lose 4 to 5c a contract in both halves, the usual cheap side price (win 12.9% against 16.7c paid).

## Forward plan
1. Finish the candle fetch for the remaining 20,000 sampled TEST markets (about 25 to 30 hours of polite fetch, resumable: `PYTHONPATH=src python3 -u -m scalper.props1 candles` then `score`), same registered rule; that run, not this one, settles PROPS1. The NBA 2026-27 and NHL seasons start in November, so a pre-game recorder is also feasible: a recorder-only branch cut from origin/main taking the live prop ladders' bid/ask in the 30 minutes before tip-off plus the next morning's ESPN box scores, which would bring the live batch candle endpoint (8 markets a request) instead of the one-market historical one.
2. Not done: MLB and NHL props (listed, not in scope).
