# NPBKBO1 result (2026-11-07): NOT_ENOUGH_DATA (4 treated of 150), every sign on the FALSIFIED side; both leagues RUNNABLE

Registration `workers/NPBKBO1_REGISTRATION.md` (commit c1c4425, sha256 `bacd00b92bd20e7936ac9be9a7d2d2e7d0bfb7950d9728bdf93178bded1f2cd6`, before any league game, candle or price). Code `src/scalper/npbkbo1.py`; scorer output `workers/NPBKBO1_SCORE_LOG.txt`; fitted parameters `workers/NPBKBO1_FIT.json`. Cheap side only (ask 3c to 30c), taker, held, C = 10, fee 7% x C x p x (1-p) rounded up, x1.2 stress. Scored once on all 1,282 qualified events (every one of the md5 prefix fetched, no 429, no block, no missing candle). N +1 (running about 1,230,541, z bar about 5.3). The frozen last third (events closing on or after 2026-10-03T16:00Z) was never listed beyond counts, fetched or joined.

## Reachability (the answer to SCOUT1's "no source")
SCOUT1 row 15 said NOT_RUNNABLE, no keyless results source. Retested 2026-11-07 with plain public requests: **NPB runnable** (npb.jp English calendar, day pages and game pages return 200; box score gives starters in table order and runs) and **KBO runnable** (koreabaseball.com's own public page JSON, `GetKboGameList`, gives starters and scores per date; the English site is stale but the Korean one is fine). No block was met or worked around. Parsed: NPB 833 usable games (41 unparsed or cancelled, 18 ties), KBO 673 usable games (16 ties, 36 postponed or cancelled dropped by status).

## Numbers first
| Arm | n | win | mean ask | mean net after fee | PF | day-clustered z | PF at fees x1.2 |
|---|---|---|---|---|---|---|---|
| CONTROL (all cheap-side candidates) | 44 | 15.9% | 25.9c | -11.34c | 0.50 | -2.04 | 0.49 |
| **TREATED (model >= 3x ask)** | **4** | 0.0% | 12.8c | **-13.53c** | 0.00 | -2.77 | 0.00 |
| treated D1 / D2 | 2 / 2 | 0 / 0 | 3.5c / 22.0c | -3.80c / -23.25c | 0 / 0 | | |
| info: treated, last third of pre-cut | 2 | 0.0% | 22.0c | -23.25c | 0 | | |
| info: control NPB / KBO | 13 / 31 | 7.7% / 19.4% | 27.2c / 25.3c | -20.97c / -7.31c | 0.20 / 0.65 | | |
| info: cheap side, model under 3x ask | 40 | 17.5% | 27.2c | -11.13c | 0.53 | -1.83 | 0.52 |

## Funnel
Kalshi events before the cut: NPB 822 (two-market settled), KBO 663. After the league match (date and team pair) and 20 prior games per club: NPB 710, KBO 572 (112 and 91 dropped early in the season). 1,282 candles fetched, all had a valid look 120 s before the start. **Only 44 of 1,282 (3.4%) had a side at 3c to 30c at the look: baseball favourites are almost never 70c or more, so the cheap side is rare, and 4 of those 44 had a model probability at 3x the ask.** The registered expected treated 20 to 50 was too high; the cheap-side share was lower than the 10% I guessed.

## Model
Fitted once on the first two thirds by date, game results only (K 8 for both leagues, home advantage 20 Elo points). **The fit chose the starter weight b = 0**: the shrunken starter-residual term (from results only; no ERA, KBO's feed has no earned runs) added nothing on the fit third, so the "starter" model is team Elo alone. Out-of-sample log-loss on the last third of pre-cut games: NPB 0.6773 (n 271), KBO 0.6636 (n 204), both close to the 0.693 coin flip, with and without the starter term (identical, b = 0). A starter ERA or a pitcher rating from a prior season might do better; this registered, walk-forward starter measure did not.

## Verdict: NOT_ENOUGH_DATA (4 treated, floor 150)
The prediction held on sign (treated mean negative, PF at or below 0.9) and missed on count (treated 4 against 20 to 60 predicted, cheap-side candidates 44 against 100 to 180). The control is the informative line: the cheap side of these markets is -11.3c per contract (NPB -21.0c on 13, KBO -7.3c on 31), worse than the pooled -5.5c to -6.2c baseline, with no model condition lifting it. No lead: nothing came near the 6c lift the standing rule needs; the point estimates are on 4 trades and carry no weight.

## Disclosures and deviations
- **A parse bug found at fit time and fixed before any price was read.** NPB's game page lists the winning club first, not the home club, so the first fit saw a home win rate of 1.00 and an absurd log-loss of 0.576. Home clubs now come from the day page (Home|runs|Game n|Venue|runs|Away); home win rate is 0.545 (NPB) and 0.520 (KBO), log-loss about 0.68. No candle or price had been read; the K, h, b fit was rerun and the final numbers are from the rerun only.
- The 2026 league seasons start from 1500 for every club (no prior-season carry); the starter in the data is the game's actual starter (the announced starter is the same in nearly every case), so a rare scratch carries a small lookahead, and it cannot help a model that ended with b = 0.
- Listings were read with the `result` field in a scratch file before registration; only counts were printed (disclosed in the registration).
- Candle asks are quotes, not fills; the look is the last 1 minute candle at least 120 s before the ticker start (US Eastern clock in the ticker).

## Accrual and the forward project
4 treated and 44 cheap-side candidates per 1,282 events, about one league season (NPB and KBO each run about March 27 to early October). **150 treated would need about 38 seasons**, and even the control (44 a season) has no room to test a conditional rule. Not a forward project, not recommended for the recorder; adding the postseason, 2027 openers and a second pitcher metric would not close a gap of that size. Spring 2027 (openers late March) is when new data would start, but the readable date for a registered claim is never at this accrual. The pooled cheap-side family is the thing the control keeps measuring as negative.

Research only; no promote verb; nothing touches trading code.
