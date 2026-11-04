# XI1 result (run once, 2026-11-04): starting XI vs Kalshi soccer anytime-goalscorer cheap YES rungs

Registration `workers/XI1_REGISTRATION.md`, sha256 `2022df46bbbac6fd986da13384ab88f09e2593c251a0ec9e3622e0de79899f40` (pushed before any candle, Kalshi result or ESPN goal). Code `src/scalper/xi1.py`, tests `tests/test_xi1.py` (8 passed), numbers `workers/XI1_RESULT.json`. Cheap side only (YES ask 3c to 30c). N +4.

## What was run
- Join: 104 Kalshi matches (EPL 39, La Liga 48, UCL 17), 99 joined to an ESPN fixture by surname + jersey (5 dropped, under 12 matched players), 1,925 markets joined, 1,376 are starters (A 225, M 619, D 532; no goalkeeper market), 1,291 of them opened at least 35 minutes before kickoff, in 94 matches. FIT 66 matches (204 non-own goals), TEST 33 (the last third by kickoff).
- Candles: 1,285 of 1,291 markets fetched, all 94 matches complete (nothing dropped, no time box reached). **Amendment (disclosed): one live batch request per match instead of one market per request.** The single-market endpoints ran at about 4 a minute under the shared limit (429s, some 404 on the historical endpoint); the batch returns the same quotes (compared on one market). The rule, look and universe are unchanged.
- Look: last valid candle ending at least 30 minutes before kickoff: 805 of 1,291 starter markets have one (486 had no valid two sided candle: not available); 731 are cheap.

## Results
| | n | matches | win | mean ask | net per contract | z (match/date cluster) | PF | halves | x1.2 |
|---|---|---|---|---|---|---|---|---|---|
| **U** cheap starter YES, max 2 per match | 187 | 94 | 5.35% | 8.19c | **-3.40c** (lower 95% bound -6.58c) | -2.09 | 0.58 | -4.37c / -2.46c | -3.51c |
| U uncapped (all cheap starters) | 731 | 94 | 4.92% | 7.64c | -3.24c | -4.15 | 0.58 | | |
| **M** model arm, TEST third | **6** | 5 | 16.7% | 6.17c | +10.05c (nothing) | 0.60 | 2.81 | +26.9c / -6.8c (3 and 3) | |
| Control for M (cheap A or M starters, TEST) | 90 | 30 | 8.89% | 11.18c | -3.00c | -1.21 | 0.71 | -4.0c / -2.0c | |

- **Win vs price (U uncapped by ask bucket): 3-10c 4.4% vs 5.9c (n 596), 10-20c 4.0% vs 11.6c (n 101), 20-30c 17.6% vs 25.7c (n 34).** Every bucket wins less than it costs.
- By league (U): EPL -2.6c (n 78), La Liga -4.6c (n 77), UCL -2.5c (n 32). By position (uncapped cheap): defenders -2.3c (n 465, z -2.6), midfielders -4.5c (n 243, z -2.9), attackers -8.0c (n 23); the cheap rungs are mostly defenders and midfielders at 3c to 10c.
- Model (shrunk FIT goals per 90, K 3): r_pos A 0.46, M 0.16 goals per 90, E_min about 78. Model minus ask on the control: median +1.8c, p90 +14.8c; treated (model >= 3 x ask) only 6 trades in 5 TEST matches, far under 150.
- Ladder sum (fetched starter 1+ asks per match, 8.6 rungs): mean sum of asks 0.926 against 0.809 scorers among those starters: asks sum ABOVE the realised scorers (over-round, the opposite of the NHL under-round NHLALL1 liked).

## Verdicts (per the registered kill rules)
- **U: FALSIFIED** (n 187 >= 150, 94 matches: PF 0.58 under 1.5, net negative in both halves, lower 95% bound below 0). The prediction (NOT_ENOUGH_DATA 60% / FALSIFIED 35%, net about -2c, win 1 to 3 points under the price) held on the sign and the direction; n and the verdict landed on the FALSIFIED side, the loss slightly bigger (-3.4c). Unlike NHLALL1, the unconditional cheap-YES structure does not carry over to soccer: starters' cheap rungs lose to fee plus a longshot bias.
- **M: NOT_ENOUGH_DATA** (6 treated of 150; 5 matches of 60). Prediction was 20 to 60 treated: missed low (the shrunk model rarely reaches 3 x ask, as in NHLG1 and PROPS1). Not above the control by any test that means anything at n 6.
- Not tested, said plainly: starter vs non-starter (no non-starter market was fetched), the 45-minute lineup release time (the quote at 30 minutes before kickoff may already include the news), later minutes or in-play.

## Forward plan
None for U (falsified). For M the TEST sample would need about 25x more matches: not reachable on three leagues (Serie A, Bundesliga, MLS, Ligue 1, Liga MX had 0 settled player markets before the cut), so not recommended. Smallest live probe: none. Killed assumption: that the starting XI is information the cheap 1+ goal quote lacks. N +4 (running about 730,421). Cheap side only.
