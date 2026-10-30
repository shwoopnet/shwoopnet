# GEN11 result (2026-10-30): Bitcoin's trade tape at 10 second resolution, mid-window entries (840 to 420 s) held to settlement. FALSIFIED

Registration `workers/GEN11_REGISTRATION.md` (commit fe50738, pushed before any row was built). Discovery frozen in `workers/GEN11_FROZEN.md` (commit c61b744; `workers/GEN11_frozen.json` sha256 e2c960ef...; control and distinct lists hashed there) before any validation row was built. Validation read once (`data/gen11/validation.json`, 14:41 UTC). Code `src/scalper/gen11.py`, which sets the series, folder, seed and prior count and calls `src/scalper/gen10.py`'s functions unchanged; bars from `data/gen9/bars.sqlite` (GEN9's public-tape fetch, 1,004 of the 3,983 sampled Bitcoin markets, not re-fetched). Nothing closing on or after 2026-10-28 00:00 UTC was read. **There is no holdout in this file** (the bars end 2026-10-27), so the RULES three-window bar could not have been met by anything here.

**Fill model, stated plainly:** the entry is an APPROXIMATION from trade prices (the next 10 s bar's last trade on the side + half the candle spread + 1c), not a book: no depth, no queue, no latency beyond the 10 s bar. One fee, 7% x C x p x (1 - p) rounded up per order, C = 10 (C = 1 and fees x1.2 reported); settlement free. Held to settlement, no exit. No open interest feature exists in the grammar and the entry window ends 420 s before the close, so the GEN6 / FALS5 open interest jump at 180 s was never in reach.

## Ledger check (from the registration, in short)

Already closed on Bitcoin or on the tape: TAPE20 (flow in the 2 minutes before the 6 minute decision as an L1 filter, five series pooled, no pass), SWEEP1 (Bitcoin big prints and sweeps on L1's contracts, retired unrun), FP2 (gold only), T1 to T4 (first 5 minutes, flow held or scalped, FALSIFIED), FLOW1 and PERPFLOW1 (Binance and perpetual flow, FALSIFIED), GEN6 and GEN7 (candle and open interest features; the only Bitcoin survivor is the open interest jump at 180 s, outside this window and this feature set), MECH1 (no taker type and no whales behind even that), GEN9 (the same 10 s Bitcoin bars, round trips, FALSIFIED at discovery), GEN10 (this grammar on gold, FALSIFIED). New here: 10 s tape features over minutes 1 to 8, Bitcoin alone, either side chosen by a signed tape condition, held with one fee, no open interest input.

## Counterparty and prediction (registered)

Follower paid by slow quoters, fader paid by impatient takers on the other side; expected alternative: Bitcoin's quote at 7 to 14 minutes left is calibrated from spot within seconds and the flow is already in it. Predicted: base PF 0.86 to 0.93, median discovery PF about 0.88, 2,000 to 3,000 distinct at size, about 5 survivors (0 to 20), validation pass 0% to 20%, control 1% to 6%, none beating the side-shuffle control at PF 1.3, family FALSIFIED (prior 85%).

## Coverage and the minimum

Half the days (GEN9's seed 909) and, within them, a seeded quarter of the markets (the 6 hour fetch budget). The registered minimum was 300 discovery windows on 15 days; **558 windows on 23 days** met it. Validation 446 windows on 19 days.

## Funnel (Bitcoin, KXBTC15M)

| | Bitcoin |
|---|---|
| Discovery windows / rows / days (Aug 6 to Sep 20, sampled days, fetched markets) | 558 / 42,954 / 23 |
| Validation windows / rows / days (Sep 21 to Oct 27, sampled days, fetched markets) | 446 / 33,466 / 19 |
| Generated (all in N) | 28,442 |
| rejected: no signed condition / under 30 trades / duplicate | 4,661 / 3,066 / 15,715 |
| Distinct | 5,000 |
| Discovery PF over all distinct: median / 95th pct | **0.87** / 1.26 |
| Median distinct rule's mean net per trade (C = 10) | -3.12c |
| Distinct at screen size (100+ trades, 15+ days) | 2,923 |
| ... with discovery PF 1.0 or more / 1.3 or more | 471 / 23 |
| **Passed discovery (PF 1.5 at size)** | **5** (1.63, 1.59, 1.58, 1.55, 1.53) |
| **Passed validation (PF 1.3, 50+ trades, stress PF above 1.0)** | **0 of 5** (1.02, 0.99, 0.96, 0.84, 0.81) |
| Beat the side-shuffle control (validation PF above the 95th percentile of 200 shuffles) | **0 of 5** |
| Family control: discovery failures at size passing the validation screen | 17 of 2,918 (**0.6%**); their validation PF median 0.87, 95th pct 1.12 |
| Control rule (survivors at least control + 5 points) | not met (0% against 0.6%) |

**Unconditioned base** (information looks, counted), the first in-band bar of every window from 840 s down, held, C = 10:

| | n | PF | mean | win rate | mean fill |
|---|---|---|---|---|---|
| Discovery YES | 558 | 0.85 | -3.85c | 49.3% | 51.4c |
| Discovery NO | 558 | 0.90 | -2.54c | 50.7% | 51.6c |
| Validation YES | 446 | 0.89 | -2.82c | 50.9% | 52.0c |
| Validation NO | 446 | 0.86 | -3.56c | 49.1% | 51.0c |

(BOTH equals YES, as on gold: YES is tried first and whenever YES is in the 15c to 85c band so is NO.) The side bought wins its price: a 51c to 52c average fill and a 49% to 51% win rate, with the YES and NO sides swapping which is the slightly better one between the two splits. The loss of about 3c a trade is the cost (about 1.5c of spread and padding, about 1.5c of fee), as predicted (0.86 to 0.93).

## The five survivors, discovery then the one validation read

| rule | Disc PF (n, days, mean, win rate, fill) | Val PF (n, days, mean, win rate) | Val stress / C = 1 | Val day z | Shuffle median / 95th pct | Unconditioned same side and range, val |
|---|---|---|---|---|---|---|
| no 480 s, c30 > 877 & f10 > -5124 | 1.63 (102, 23, +9.6c, 59%, 48c) | **1.02** (129, 19, +0.4c, 49%) | 1.00 / 1.00 | 0.08 | 0.89 / 1.20 | 0.92 (331, -1.7c) |
| both 780 to 720 s, c10 <= 365 & f60 <= -5738 & big30 > 3753 | 1.59 (110, 23, +9.4c, 70%, 59c) | 0.99 (43, 16, -0.3c, 63%) | 0.97 / 0.97 | -0.05 | 0.86 / 1.34 | 0.85 (444, -3.6c) |
| both 720 s, big30 > 2000 & iw <= 0.092 & dp30 > 3 | 1.58 (100, 23, +8.4c, 75%, 65c) | 0.96 (80, 17, -0.9c, 66%) | 0.95 / 0.94 | -0.18 | 0.83 / 1.25 | 0.83 (430, -4.2c) |
| both 660 s, i30 > -0.077 & iw <= -0.092 & c30 > 451 | 1.55 (102, 23, +8.9c, 70%, 59c) | 0.81 (78, 19, -4.5c, 55%) | 0.79 / 0.79 | -0.68 | 0.87 / 1.32 | 0.83 (413, -4.0c) |
| both 600 s, dp10 <= -5 | 1.53 (108, 23, +8.8c, 57%, 47c) | 0.84 (73, 19, -4.0c, 43%) | 0.83 / 0.82 | -0.78 | 0.86 / 1.43 | 0.83 (388, -4.0c) |

Unlike gold's three (one bet seen three ways), these are five different bets: a busy 30 s at 8 minutes left; a big print with 60 s flow against the side at 12 to 13 minutes; a big print with the price moving toward the side at 12 minutes; flow against the side since the open with flow for it in the last 30 s at 11 minutes; a 5c drop against the side in the last 10 s at 10 minutes. Each had a discovery PF of 1.5 to 1.63 on 100 to 110 trades, which is where the best of 2,923 rules at size lands under the null, and every one went to about 1.0 or below in validation with a day z between -0.8 and +0.1. The best, 1.02 on 129 trades, is below its shuffle 95th percentile (1.20), so even its 0.4c a trade is inside what the band and the time give a random side. Note the survivors' validation PFs are on average a little above the base (0.81 to 1.02 against 0.83 to 0.92): a random-side control of their own windows (the shuffle medians, 0.83 to 0.89) says that is the windows they picked, not the side.

## Best 10 of discovery at size (information; the first five are the survivors)

| rule | Disc PF (n, mean) | Val PF (n, days, mean) | Val z | Shuffle median / 95th |
|---|---|---|---|---|
| no 480 s, c30 > 877 & f10 > -5124 | 1.63 (102, +9.6c) | 1.02 (129, 19, +0.4c) | 0.08 | 0.89 / 1.20 |
| both 780 to 720 s, c10 <= 365 & f60 <= -5738 & big30 > 3753 | 1.59 (110, +9.4c) | 0.99 (43, 16, -0.3c) | -0.05 | 0.86 / 1.34 |
| both 720 s, big30 > 2000 & iw <= 0.092 & dp30 > 3 | 1.58 (100, +8.4c) | 0.96 (80, 17, -0.9c) | -0.18 | 0.83 / 1.25 |
| both 660 s, i30 > -0.077 & iw <= -0.092 & c30 > 451 | 1.55 (102, +8.9c) | 0.81 (78, 19, -4.5c) | -0.68 | 0.87 / 1.32 |
| both 600 s, dp10 <= -5 | 1.53 (108, +8.8c) | 0.84 (73, 19, -4.0c) | -0.78 | 0.86 / 1.43 |
| no 780 to 720 s, f30 <= 7058 & px <= 68 & c10 > 436 | 1.48 (115, +8.5c) | 0.84 (155, 19, -4.1c) | -1.18 | 0.89 / 1.21 |
| both 540 s, f30 <= 0 & c60 > 1944 | 1.44 (103, +7.1c) | 1.24 (159, 19, +4.1c) | 1.40 | 0.86 / 1.15 |
| both 540 to 420 s, fw <= -18,130 & px <= 39 | 1.43 (115, +8.2c) | 0.84 (90, 19, -3.8c) | -0.65 | 0.89 / 1.27 |
| both 660 to 600 s, f60 > -35,040 & bigdir30 > -1 & fw <= -65,700 | 1.42 (209, +6.7c) | 0.88 (176, 19, -2.6c) | -0.75 | 0.85 / 1.11 |
| both 480 to 420 s, iw <= -0.046 & dp60 > 0 & f60 <= -12,430 | 1.40 (126, +6.0c) | 0.71 (124, 19, -6.4c) | -1.49 | 0.84 / 1.18 |

Ten of ten fell in validation. The best validation PF of the ten is 1.24 (row 7, `both 540 s, f30 <= 0 & c60 > 1944`: a busy minute at 9 minutes left with the last 30 s of flow not for the side), above its shuffle 95th percentile (1.15) with day z 1.40 and a discovery PF under the gate; it is one of 2,923 rules at size and about 17 such rules (0.6%) would pass the validation screen by chance, so it is noted as what a best-of-5,000 produces, not as a finding. Nothing in it is registered forward.

## Verdicts

- **Bitcoin: FALSIFIED** (5 of 2,923 passed discovery; 0 of 5 passed validation; 0 of 5 beat the side-shuffle control; family control 0% against 0.6%).
- No candidate file, no forward ledger entry, no R6 evaluator (nothing survived; an R6 evaluator for this shape would rebuild the same 10 s bars from R6's `trades` and price the entry at R6's recorded ask at the first poll after the signal bar, walked through its levels for 10 contracts, and is not written because there is nothing to run on it).
- **N added: 28,442 draws + 3 base looks + 5 unconditioned same-side-and-range looks = 28,450**; running count about **728,623** (from the lead's 700,173), Bonferroni z bar about **5.27**.
- **Prediction check.** Base PF 0.85 to 0.90 (predicted 0.86 to 0.93: at the low end; the cost is about 3.1c, the fee rounding at C = 10 adds a little); median discovery PF 0.87 (predicted about 0.88); 2,923 at size (predicted 2,000 to 3,000); 5 survivors (predicted about 5, 0 to 20); validation pass rate 0% (predicted 0% to 20%); control 0.6% (predicted 1% to 6%: a little lower, as on gold); no survivor beat the shuffle at 1.3 (predicted); family FALSIFIED (predicted, prior 85%).

## For the lead

With GEN9 (round trips, both markets), GEN10 (held, gold) and GEN11 (held, Bitcoin) on the same 10 second bars, Kalshi's public trade tape between 14 and 7 minutes left has now been read both ways on both markets, and the answer is the same on each: the side bought wins its price, a taker pays about 3c to hold and about 6.5c to round trip, and nothing in sub-minute flow, imbalance, bursts, prints, the move since the open or the time since a big print changes the settlement odds. On Bitcoin the survivors were five unrelated bets rather than gold's one, which is the signature of selection noise on a smaller sample (558 windows), and every one of them went to the base in validation. Taken with TAPE20 (flow adds nothing to the favourite held), MECH1 (no taker type behind the one late Bitcoin effect) and GEN7 (nothing before 5 minutes left in candles or open interest), tape-feature taker entries on Bitcoin's 15 minute market should be marked closed for both trade shapes, as gold's were. What remains for the tape is book-priced and maker-side (QUOTE1, MAKER5 / QUOTE2B on R6's real queue), and the one Bitcoin effect that exists (the open interest jump at 180 s) is outside the owner's allowed window and is already under its own forward reads.

## Proposed README section (for the lead to merge; README.md not edited)

```
## Result: GEN11 (Bitcoin trade-tape generator, mid-window entries held to settlement), 2026-10-30

GEN10's grammar on Bitcoin, nothing changed but the series and seed. Registered first (`workers/GEN11_REGISTRATION.md`, commit fe50738), frozen and hashed before validation (`workers/GEN11_FROZEN.md`, commit c61b744), validation read once; result `workers/GEN11_RESULT.md`, code `src/scalper/gen11.py` (calls `gen10.py`), bars from GEN9's public-tape file (Bitcoin, 1,004 of 3,983 sampled markets: half the days, a seeded quarter of their markets; 558 discovery windows on 23 days against a registered minimum of 300 on 15, 446 validation windows on 19 days). Signal bar 840 to 420 s before the close (nothing at 360 s or later; no open interest feature, so the GEN6 / FALS5 jump at 180 s is out of reach by construction), side 15c to 85c chosen by at least one signed tape condition from GEN9's 16 features plus GEN10's 4, fill at the next 10 s bar's last trade + half spread + 1c (from trades, not a book), one fee at C = 10, held to settlement. 28,442 draws to 5,000 distinct; median discovery PF 0.87 (base 0.85 to 0.90: the side wins its price and pays about 3c); 5 of 2,923 at size passed discovery (1.63, 1.59, 1.58, 1.55, 1.53; five unrelated bets, not one); **0 of 5 passed validation** (1.02, 0.99, 0.96, 0.84, 0.81; day z -0.8 to +0.1), 0 of 5 beat the side-shuffle control (200 shuffles of the side per trade), family control 0.6%: **FALSIFIED**. The best of the ten best in validation (1.24 on 159, `both 540 s, f30 <= 0 & c60 > 1944`) is what 0.6% of 2,923 rules produce by chance and is not registered. No holdout exists in the file (ends Oct 27), so nothing here could meet the three-window bar; no candidate, no R6 evaluator. Tape-feature taker entries on Bitcoin's 15 minute market are closed for round trips (GEN9) and held (GEN11), as gold's are (GEN9, GEN10). N +28,450; running count about 728,623 (z bar 5.27).
```

## Files

`src/scalper/gen11.py`, `workers/GEN11_REGISTRATION.md`, `workers/GEN11_FROZEN.md`, `workers/GEN11_frozen.json`, this file. Distinct, control, validation and log files in `data/gen11/` (not committed).
