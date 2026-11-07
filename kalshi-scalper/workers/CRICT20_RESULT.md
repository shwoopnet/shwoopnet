# CRICT20 result (run once 2026-11-07): NOT_ENOUGH_DATA (treated n 10 of 150), nothing to follow up

Registration `workers/CRICT20_REGISTRATION.md` (sha256 e100ebf39913f2ed74965ddeea94d6a6fd63fe6460cebdff71aebeff50278852, commit 8422d2b, before any cricket candle or result). Code `src/scalper/cric1.py` and `tests/test_cric1.py` (committed before the first candle). Raw scorer output `workers/CRICT20_SCORE_LOG.txt`, per-row table `workers/CRICT20_ROWS.json`, fitted parameters `workers/CRICT20_PARAMS.json`. Cheap side only, ask 3c to 30c, taker at the ask, held, fee 7% x C x p x (1-p) rounded up with C = 10; N +2 (running about 1,230,542, z bar about 5.3). Frozen third (closes from 2026-10-03T16:00Z) never listed, fetched or joined.

## Numbers first
| Arm | n | win | mean ask | net per contract after fee | PF | z | PF at fees x1.2 |
|---|---|---|---|---|---|---|---|
| CONTROL (all cheap-side rows, rated events) | 115 | 8.7% (10) | 14.3c | **-6.47c** | 0.52 | -2.47 | 0.51 |
| **TREATED (model >= 3 x ask)** | **10** | 10.0% (1) | 8.3c | +1.14c | 1.15 | 0.12 | 1.14 |
| treated D1 (first half by start) | 5 | 0.0% | 9.4c | -10.02c | 0.00 | -2.95 | 0.00 |
| treated D2 | 5 | 20.0% (1) | 7.2c | +12.30c | 3.61 | 0.67 | 3.55 |
| info: treated KXT20MATCH / KXODIMATCH | 8 / 2 | 0% / 50% | 7.3c / 12.5c | -7.75c / +36.70c | 0.00 / 7.27 | | |
| info: control KXT20MATCH / KXODIMATCH | 105 / 10 | 8.6% / 10.0% | 14.3c / 14.4c | -6.59c / -5.28c | 0.51 / 0.62 | | |
| info: untreated cheap-side rows | 105 | 8.6% | 14.9c | -7.20c | 0.49 | -2.64 | 0.48 |

## Funnel
1,457 settled yes/no events listed before the cut (211 of the 1,668 in the registration census were dropped because a market settled as `scalar`, that is a void or abandoned match, a small deviation from the registration's 1,668 that follows TENNIS1's rule of keeping only yes/no results); 177 without a start time in the ticker; 748 with no Cricsheet match (Indian state and private leagues, Sri Lankan franchise league, UAE, Cricsheet not carrying them); 17 ambiguous (dropped); 24 with a team under 5 earlier matches; **487 rated events (372 KXT20MATCH, 115 KXODIMATCH), all with candles, from 2026-05-14 to 2026-10-03** (the earlier events carry a date only, no start time). **Quoted at the look: 479 of 487 (98%)**, median 30 minutes before the start (the look candle), none stale beyond the 3 hour rule; 364 of 479 had no side at 3c to 30c (76%); **115 cheap-side rows (24% of quoted); 10 treated (2.1% of rated events).**

## Fit (Cricsheet 2024 to 2025 only, before Kalshi's cricket series existed)
3,201 ready T20 matches, grid kt {0.5, 1, 2} x w {0, 0.5, 1}: best kt = 2.0 (the edge of the grid), w = 0.5, log loss 0.6257 against a coin's 0.6931; toss term b = +0.082 (a toss winner gets about 2 points). The rating has real information on Cricsheet itself (mostly associate internationals, where mismatches are large); the result says nothing about whether it beats the market price.

## Verdict: NOT_ENOUGH_DATA
10 treated trades against the 150 floor. The kill rules do not apply (their count floor is 150). Point estimates are noise: the treated mean is +1.14c on 10 trades with 1 win (z 0.12), D1 -10.02c and D2 +12.30c are 5 trades each, and the KXODIMATCH +36.70c is 2 trades with one winner at 14c. **What the table does show:** the CONTROL (every cheap-side row in the rated universe) is -6.47c, PF 0.52, z -2.47, the usual cheap-side baseline (-5.5c to -6.2c pooled), so cricket's cheap side is priced like every other cheap side; and the model's treated picks are not a visible lift on it (treated p was 13% to 70% at asks of 3c to 21%, mostly associate and women's sides with few matches where a rating swings widely). Prediction check: rated events 450 to 520 (hit, 487); quoted at least 90% (hit, 98%); cheap-side rows 60 to 110 (slightly missed, 115); treated 8 to 40 (hit at the low end, 10); treated win rate 0.6 to 1.0 of the ask (8.3c ask, 10% win, ratio 1.2, noise on 10); mean net -1c to -8c (missed, +1.14c, on 10 trades); PF 0.3 to 1.1 (missed marginally, 1.15). No lead: nothing came near a 6c lift on a usable count.

## When this becomes readable
**It does not.** Treated accrues about **0.5 a week** (10 in the 20 weeks from 2026-05-14 to 2026-10-03; the rated universe is about 24 events a week and the treated share 2%). 150 treated needs about 300 weeks, near **2032**. The frozen third (2026-10-03 onward) would add perhaps 2 to 4 treated trades by January 2027. Not a forward project, not worth a recorder slot. The one thing that could change this is a bigger rated universe: a results source for the Indian state and private leagues, the Sri Lankan franchise league and UAE (about 750 of 1,457 events are unrated for that reason), which would at most double the count, still about 150 years short of... no: still about 3 years short at the same hit rate. Even that does not fix a model whose treated picks are 2% of events.

## Corrections to the ledger
SCOUT1's row 17 (CRIC1, "no ratings or results source reachable", NOT_RUNNABLE) was wrong: Cricsheet `all_json.zip` is reachable (HTTP 200, 149 MB, 23,243 files, T20 to 2026-11-03). The row stands corrected as NOT_ENOUGH_DATA for the Cricsheet-covered part (this test) and NOT_RUNNABLE for the unrated 750 events (no results source for those leagues).

## Limits
Candle asks are quotes, not fills; the look is 30 minutes before the ticker's Eastern start (toss time is not in any file; a late or rain-delayed start moves it); name matching is by normalised team name with a 2 day window and an ambiguity drop (17 events); the XI in a Cricsheet file is the XI that played, which can differ from the team sheet at the toss by an injury replacement; kt landed on its grid edge; the treated sample (10) cannot separate any effect from luck.
