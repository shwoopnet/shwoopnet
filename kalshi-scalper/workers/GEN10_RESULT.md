# GEN10 result (2026-10-30): gold's trade tape at 10 second resolution, mid-window entries (840 to 420 s) held to settlement. FALSIFIED

Registration `workers/GEN10_REGISTRATION.md` (commit b8e3a42, pushed before any row was built). Discovery frozen in `workers/GEN10_FROZEN.md` (commit 13c3e84; `workers/GEN10_frozen.json` sha256 f73d61d6...; control and distinct lists hashed there) before any validation row was built. Validation read once (`data/gen10/validation.json`, 14:16 UTC). Code `src/scalper/gen10.py`, bars from `data/gen9/bars.sqlite` (GEN9's public-tape fetch, not re-fetched). Nothing closing on or after 2026-10-28 00:00 UTC was read. **There is no holdout in this file** (the bars end 2026-10-27), so the RULES three-window bar could not have been met by anything here.

**Fill model, stated plainly:** the entry is an APPROXIMATION from trade prices (the next 10 s bar's last trade on the side + half the candle spread + 1c), not a book: no depth, no queue, no latency beyond the 10 s bar. One fee, 7% x C x p x (1 - p) rounded up per order, C = 10 (C = 1 and fees x1.2 reported); settlement free. Held to settlement, no exit.

## Ledger check (from the registration, in short)

Already closed on gold or on the tape: T1 to T4 (first 5 minutes, flow held or scalped, FALSIFIED), TAPE20 (flow before the 6 minute decision as an L1 filter, no pass), FP2 (gold footprint as an L1 loss warning, closed with the L1 ban), SWEEP1 (Bitcoin prints and sweeps, retired unrun), FLOW1 and PERPFLOW1 (Binance and perpetual flow, FALSIFIED), GEN6 and GEN7 (candle and open interest features, gold 0 of 5,000 at 840 to 240 s), GEN9 (the same 10 s bars, round trips, gold FALSIFIED at discovery), MECH1 (no taker type, no whales). New here: 10 s tape features over the whole mid-window, gold alone, either side chosen by a signed tape condition, held with one fee.

## Counterparty and prediction (registered)

Follower paid by slow quoters, fader paid by impatient takers on the other side; expected alternative: the quote at 7 to 14 minutes left is calibrated and the flow is already in it. Predicted: base PF 0.88 to 0.95, median discovery PF about 0.90, about 3 survivors (0 to 12), none beating the side-shuffle control at PF 1.3, family FALSIFIED (prior 85%).

## Funnel (gold, KXGOLD15M)

| | Gold |
|---|---|
| Discovery windows / rows / days (Aug 6 to Sep 20, sampled days) | 1,704 / 125,972 / 23 |
| Validation windows / rows / days (Sep 21 to Oct 27, sampled days) | 1,368 / 104,030 / 17 |
| Generated (all in N) | 21,219 |
| rejected: no signed condition / under 30 trades / duplicate | 3,472 / 1,167 / 11,580 |
| Distinct | 5,000 |
| Discovery PF over all distinct: median / 95th pct | **0.86** / 1.08 |
| Median distinct rule's mean net per trade (C = 10) | -3.19c |
| Distinct at screen size (100+ trades, 15+ days) | 4,274 |
| ... with discovery PF 1.0 or more / 1.3 or more | 311 / 10 |
| **Passed discovery (PF 1.5 at size)** | **3** (1.97, 1.88, 1.50) |
| **Passed validation (PF 1.3, 50+ trades, stress PF above 1.0)** | **0 of 3** (1.20, 0.72, 0.70) |
| Beat the side-shuffle control (validation PF above the 95th percentile of 200 shuffles) | **0 of 3** |
| Family control: discovery failures at size passing the validation screen | 33 of 4,271 (**0.8%**); their validation PF median 0.87, 95th pct 1.11 |
| Control rule (survivors at least control + 5 points) | not met (0% against 0.8%) |

**Unconditioned base** (information looks, counted), the first in-band bar of every window from 840 s down, held, C = 10:

| | n | PF | mean | win rate | mean fill |
|---|---|---|---|---|---|
| Discovery YES | 1,693 | 0.85 | -3.88c | 50.6% | 52.8c |
| Discovery NO | 1,693 | 0.88 | -2.99c | 49.4% | 50.7c |
| Validation YES | 1,365 | 0.88 | -2.90c | 49.9% | 51.1c |
| Validation NO | 1,365 | 0.86 | -3.56c | 50.1% | 52.0c |

(BOTH equals YES here: YES is tried first at each bar and whenever YES is in the 15c to 85c band so is NO, so BOTH always takes the YES row at the first in-band bar.) The side bought wins almost exactly its price: a 51c average fill and a 50% win rate. The loss of about 3c a trade is the cost (about 1.65c of spread and padding, about 1.5c of fee), as predicted (0.88 to 0.95).

## The three survivors, discovery then the one validation read

| rule | Disc PF (n, days, mean, win rate, fill) | Val PF (n, days, mean, win rate) | Val stress / C = 1 | Val day z | Shuffle median / 95th pct | Unconditioned same side and range, val |
|---|---|---|---|---|---|---|
| no 600 s, tbig <= 0 & dpw > 25 | 1.97 (100, 18, +8.7c, 89%, 79c) | **1.20** (108, 15, +2.6c, 83%) | 1.18 / 1.15 | 1.07 | 0.85 / 1.22 | 0.85 (1,202, -3.4c) |
| both 600 s, dp30 <= 0 & dpw > 25 & f30 > -2306 | 1.88 (111, 21, +7.9c, 89%, 80c) | 0.70 (41, 15, -6.1c, 76%) | 0.69 / 0.68 | -0.94 | 0.89 / 1.62 | 0.88 (1,202, -2.7c) |
| no 660 to 600 s, bigdir30 > -1 & f60 > 476.7 & dpw > 17 | 1.50 (143, 19, +6.7c, 81%, 73c) | 0.72 (82, 16, -6.3c, 68%) | 0.71 / 0.70 | -1.20 | 0.86 / 1.31 | 0.85 (1,306, -3.4c) |

All three are one bet: at 10 to 11 minutes left, buy the side priced 73c to 80c after the price has moved 17c to 25c toward it since the window opened (`dpw`, a new feature), with a tape condition that barely cuts the set. In discovery an 80c side won 89% (its price says 80%); in validation 83% and 76%, inside the noise of its price. The one that held above 1.0 (1.20 on 108) is below the shuffle 95th percentile (1.22), so even that is within what the band and time alone give with a random side.

## Best 10 of discovery at size (information; the first three are the survivors)

| rule | Disc PF (n, mean) | Val PF (n, days, mean) | Val z | Shuffle median / 95th |
|---|---|---|---|---|
| no 600 s, tbig <= 0 & dpw > 25 | 1.97 (100, +8.7c) | 1.20 (108, 15, +2.6c) | 1.07 | 0.85 / 1.22 |
| both 600 s, dp30 <= 0 & dpw > 25 & f30 > -2306 | 1.88 (111, +7.9c) | 0.70 (41, 15, -6.1c) | -0.94 | 0.89 / 1.62 |
| no 660 to 600 s, bigdir30 > -1 & f60 > 476.7 & dpw > 17 | 1.50 (143, +6.7c) | 0.72 (82, 16, -6.3c) | -1.20 | 0.86 / 1.31 |
| both 660 s, f60 <= 2069 & bigdir30 > -1 & big30 > 868.6 | 1.43 (115, +6.7c) | 1.14 (193, 17, +2.8c) | 0.84 | 0.86 / 1.12 |
| no 660 s, dp30 > -2 & px > 76 | 1.41 (111, +4.2c) | 0.95 (98, 14, -0.8c) | -0.24 | 0.87 / 1.31 |
| yes 840 to 480 s, f30 > 2306 & fw <= -5730 & i10 > -0.5528 | 1.41 (107, +6.6c) | 1.13 (205, 15, +2.5c) | 0.83 | 0.89 / 1.08 |
| no 480 to 420 s, px <= 24 & c60 <= 199 & fw > -5730 | 1.40 (203, +6.3c) | 1.00 (52, 16, +0.1c) | 0.01 | 0.85 / 1.43 |
| both 540 s, dp30 > -2 & c10 > 27 & iw <= -0.1276 | 1.39 (202, +6.0c) | 0.86 (321, 17, -3.0c) | -1.47 | 0.86 / 1.06 |
| yes 600 to 540 s, f60 <= -3830 & px > 61 & f30 <= 263.2 | 1.35 (115, +4.9c) | 1.00 (225, 16, 0.0c) | 0.02 | 0.86 / 1.04 |
| no 480 to 420 s, dp60 <= -8 & px > 24 & i30 <= -0.385 | 1.31 (135, +6.1c) | 0.93 (101, 17, -1.5c) | -0.36 | 0.86 / 1.24 |

Ten of ten fell in validation; the best validation PF of the ten is 1.20 and the best day z 1.07. Two of the ten (rows 4 and 6, validation 1.14 and 1.13) are above their shuffle 95th percentile by 0.02 to 0.05 of PF, with day z under 1 and discovery PF under the gate; they are noted as what a best-of-5,000 produces, not as findings. The signed flow since the open (`fw`, `iw`), the time since a big print (`tbig`) and the move since the open (`dpw`) appear in the top rules because they were the new axes, and none of them held.

## Verdicts

- **Gold: FALSIFIED** (3 of 4,274 passed discovery; 0 of 3 passed validation; 0 of 3 beat the side-shuffle control; family control 0% against 0.8%).
- No candidate file, no forward ledger entry, no R6 evaluator (nothing survived; an R6 evaluator for this shape would rebuild the same 10 s bars from R6's `trades` and price the entry at R6's recorded ask at the first poll after the signal bar, and is not written because there is nothing to run on it).
- **N added: 21,219 draws + 3 base looks + 3 unconditioned same-side-and-range looks = 21,225**; running count about **700,154**, Bonferroni z bar about **5.26**.
- **Prediction check.** Base PF 0.85 to 0.88 (predicted 0.88 to 0.95: slightly worse, the cost is about 3.2c and the rounding of the fee at C = 10 adds a little); median discovery PF 0.86 (predicted about 0.90); 3 survivors (predicted about 3, 0 to 12); validation pass rate 0% (predicted 0% to 15%); control 0.8% (predicted 2% to 6%: lower, because a held outcome at 50+ trades rarely reaches 1.3 with stress above 1.0); no survivor beat the shuffle at 1.3 (predicted); family FALSIFIED (predicted, prior 85%).

## For the lead

With GEN9 (round trips) and GEN10 (held) on the same 10 second gold bars, the public trade tape has now been read both ways on gold between 14 and 7 minutes left and the answer is the same as TAPE20's and GEN7's: the side bought wins its price and nothing in sub-minute flow, prints, bursts or the move since the open changes that. The one pattern the generator kept finding (the 75c to 80c side after a 20c move toward it at 10 minutes left) is the band and the time, not the tape (shuffle control), and it did not hold. Tape-feature entries on gold's 15 minute market should be marked closed for both trade shapes; what is left for the tape is a book-priced maker question (MAKER5 / QUOTE3 on R6), not a taker entry.

## Proposed README section (for the lead to merge; README.md not edited)

```
## Result: GEN10 (gold trade-tape generator, mid-window entries held to settlement), 2026-10-30

Registered first (`workers/GEN10_REGISTRATION.md`, commit b8e3a42), frozen and hashed before validation (`workers/GEN10_FROZEN.md`, commit 13c3e84), validation read once; result `workers/GEN10_RESULT.md`, code `src/scalper/gen10.py`, bars from GEN9's public-tape file (gold, 3,072 markets, 10 s bars). Signal bar 840 to 420 s before the close (nothing in the last 6 minutes), side 15c to 85c chosen by at least one signed tape condition (GEN9's 16 features plus signed flow since the open, its share, the move since the open and the time since a big print), fill at the next 10 s bar's last trade + half spread + 1c (from trades, not a book), one fee at C = 10, held to settlement. 21,219 draws to 5,000 distinct; median discovery PF 0.86 (base 0.85 to 0.88: the side wins its price and pays about 3c); 3 of 4,274 at size passed discovery (1.97, 1.88, 1.50, all the 73c to 80c side after a 17c to 25c move toward it at 10 to 11 minutes left); **0 of 3 passed validation** (1.20, 0.72, 0.70), 0 of 3 beat the side-shuffle control (200 shuffles of the side per trade), family control 0.8%: **FALSIFIED**. No holdout exists in the file (ends Oct 27), so nothing here could meet the three-window bar; no candidate, no R6 evaluator. Tape-feature taker entries on gold's 15 minute market are closed for round trips (GEN9) and held (GEN10). N +21,225; running count about 700,154 (z bar 5.26).
```

## Files

`src/scalper/gen10.py`, `workers/GEN10_REGISTRATION.md`, `workers/GEN10_FROZEN.md`, `workers/GEN10_frozen.json`, this file. Distinct, control, validation and log files in `data/gen10/` (not committed).
