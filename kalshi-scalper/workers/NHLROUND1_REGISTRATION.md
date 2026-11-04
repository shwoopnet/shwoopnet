# NHLROUND1 registration: cheap YES rungs of KXNHLGOAL only in games whose ladder is under-round against the expected scorers

Written 2026-11-04 BEFORE any NHLROUND1 candle was fetched or outcome joined. Worker ID NHLROUND1, session "Strategy Research V2". Research only: no order, no live code, no `functions/`, no L1, no OICORE, no promote verb. No em dashes.
**Owner rule (strict): CHEAP SIDE ONLY (ask 3c to 30c).** No favourite-side result is computed or printed. No 15 minute crypto or gold candle is used.
**N: +2** (one rule, one try; running count about 730,395, z bar 5.27).

## 1. Duplicate check (done)
README and workers/ searched for NHLG1, NHLALL1, MLBHR1, NFLANYTD1, OVERROUND1, PRICEMATCH1. NHLG1: Poisson model vs quote, 0 treated trades. NHLALL1 (running now): unconditional cheap pool, plus a ladder-sum filter by TERCILE with cuts fitted on its first third fetched (a data-dependent cut). MLBHR1 and NFLANYTD1: other sports, same idea. OVERROUND1: over-round ordering in weather ladders. PRICEMATCH1: price matching across venues. Not an exact duplicate: NHLROUND1 differs from NHLALL1's filter by a THRESHOLD FIXED IN ADVANCE from ESPN data of the FIT games (no price, no Kalshi result), and is the "expected scorers" version (a mechanism: the ladder's YES asks should sum to about the number of distinct scorers; a sum clearly below it means the set is underpriced). It is a secondary claim on the same fetched games, so it adds no fetch.

## 2. Disclosure: what was seen
Seen by the research session (not evidence, not reused): NHLG1's information-only side finding on 18 TEST games (247 cheap YES rungs, mean +5.6c, ladder ask sum 3.31 against about 3.88 expected scorers). That is why the rule exists; the DIRECTION (sum below expected) comes from it, the NUMBERS below do not. The exclusion list is NHLALL1's `excluded_events` (25 events with any NHLG1 candle, a superset of the 18 games; `workers/NHLALL1_CENSUS.json`, listed in `workers/NHLALL1_REGISTRATION.md` section 2). Nothing about those games is used. The frozen last third (games from 2026-10-03T16:00Z, 225 events) is never fetched or joined.

## 3. Census (listings and ESPN only, done)
Games available: NHLALL1's census, 967 matched pre-cut games, 942 not excluded, 15,475 volume-positive 1+ rungs, median 15 per game. NHLROUND1 fetches nothing: it reads NHLALL1's cache (`/home/user/.cache/nhlall1/nhlall1.sqlite`, candles of the same markets) read-only. The achievable sample is whatever NHLALL1's 180 minute time box completes (about 65 to 70 games, md5 order of the event ticker). Of those, only games passing the filter below are treated, each with at most 2 cheap rungs, so the treated count is likely **under 150 trades (very likely about 40 to 100): NOT_ENOUGH_DATA is the expected verdict**, said now.

## 4. The rule (fixed now)
**Expected scorers E.** From ESPN box scores only (no Kalshi price, no Kalshi result): over the 645 FIT games (first two thirds of the matched pre-cut games by start time, NHLG1's split), the mean number of players with a volume-positive Kalshi 1+ rung in that game who scored at least one goal (ESPN `goals` by normalised name; the listing's name, strike and volume only). **E = 3.9085** (SD 1.79; mean 14.09 listed players per game). The all-skater league average distinct scorers per game is 5.52 and is NOT used: the ladder only lists about 14 players, so only the listed-player count is comparable to the ladder's sum.
**Margin m = 0.3** scorers, fixed a priori (about 8% of E, a clear but modest under-round; NOT tuned: the 3.31 vs 3.88 gap of NHLG1's 18 games, 0.57, was the direction only, and 0.3 is chosen as roughly half of it before any other game is looked at). **Filter: a game is treated when its ladder sum <= E - m = 3.6085**, where ladder sum = sum of YES asks over its 1+ rungs at the look, rungs with a valid quote only, at least 8 such rungs (the NHLALL1 definition, `entries()` in `src/scalper/nhlall1.py`; games with all rungs' candles done, md5 order).
**Look, trade, fee, statistic.** Exactly NHLALL1's: last valid 1 minute candle ending at least 120 s before ESPN puck drop (two sided, ask - bid <= 0.10); cheap side YES if ask in [0.03, 0.30] else NO if 1 - bid in [0.03, 0.30]; C = 10, hard limit 0.30, held, max 2 per game by sha1 of the ticker, fee 7% x C x p x (1 - p) rounded up per order (x1.2 stress), game-clustered SE and 95% bound, event-date clustered line, PF, win rate against mean price, halves H1 and H2 at the median start time of the treated games. Control line (information): the untreated games (ladder sum above E - m) under the same cap, and all games.
**Scoring happens ONLY after** `workers/NHLALL1_RESULT.md` exists (NHLALL1 finished and wrote its own result); the module refuses before that. Cuts and constants are in the code at the registration commit and not edited afterwards.

## 5. Pass bar (fixed before any outcome)
- **LEAD** only if n >= 150 treated trades AND net after fees above 0 in BOTH halves AND game-clustered lower 95% bound above 0 AND PF >= 1.5.
- **NOT_ENOUGH_DATA** if under 150 trades (report n, games, win vs price, net with CI anyway as information).
- Otherwise **FALSIFIED** (net not above 0 in both halves or PF under 1.5).
No promote verb; a LEAD would still face z 5.27.

## 6. Prediction (stated before)
Treated mean net -2c per contract (plausible -8c to +4c), PF 0.8 to 1.0, win rate about equal to or below price paid. Treated trades 40 to 100. Verdict NOT_ENOUGH_DATA about 85%, FALSIFIED about 12%, **LEAD at most 3%**. The filtered games are not better than untreated ones.

## 7. Forward plan
If NOT_ENOUGH_DATA, the same frozen filter (E 3.9085, m 0.3) is applied once to NHLALL1's forward read of the 225 frozen events after 2026-10-03 (about 25 a week), opened once after the games settle and the owner approves; no edit.
