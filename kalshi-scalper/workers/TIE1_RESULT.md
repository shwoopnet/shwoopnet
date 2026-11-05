# TIE1 result (run once 2026-11-05, about 11:40 AM Central): NOT_ENOUGH_DATA (treated n 39 of 150), treated mean negative

Registration `workers/TIE1_REGISTRATION.md` (commit before any price; sha256 f154591808b6612c2e120f695c1d483780a078516762972fb1aa82a395fa8953). Code and raw print: `workers/tie1/` (`score1.out`). Cheap side, ask 3c to 30c, taker at the ask, held, fee 7% x C x p x (1-p) rounded up with C = 10; N +2 (running about 730,447, z bar 5.27).

## Numbers first
| Arm | n (ties) | win | mean ask | mean net after fee | PF | z | PF at fees x1.2 |
|---|---|---|---|---|---|---|---|
| CONTROL (all cheap-side candidates) | 78 | 14.1% | 13.6c | -0.36c | 0.97 | -0.10 | 0.95 |
| **TREATED (deficit 0 or 1 after leg 1)** | **39** | 17.9% | 18.9c | **-2.01c** | **0.87** | -0.35 | 0.85 |
| treated D1 (before 2026-07-30) | 10 | 10.0% | 19.2c | -10.29c | 0.41 | -1.15 | 0.40 |
| treated D2 (from 2026-07-30) | 29 | 20.7% | 18.8c | +0.85c | 1.06 | 0.12 | 1.04 |
| info: deficit 2 or more | 39 | 10.3% | 8.4c | +1.28c | 1.17 | 0.27 | 1.15 |
| info: treated, hosts leg 2 | 13 | 7.7% | 21.1c | -14.58c | 0.28 | -2.00 | 0.28 |
| info: treated, away in leg 2 | 26 | 23.1% | 17.8c | +4.28c | 1.34 | 0.57 | 1.32 |

## Funnel
139 settled KXUECLADVANCE ties; 117 matched to exactly two ESPN legs (22 dropped: single leg or no unique match); 2 without a two sided quote at the look; 37 with no side at 3c to 30c (both sides above 30c); 78 candidates, 39 treated.

## Verdict
**NOT_ENOUGH_DATA**: 39 treated trades against the 150 floor, so no verdict on the claim. The point estimates are all inside noise (best arm z 0.57, worst -2.00 on 13 trades, which is one information cell among six and not a try). Treated is not above zero in both halves (D1 -10.29c), so under the registered kill it would also read FALSIFIED if it had 150 trades. The prediction missed on count (candidates 90 to 130 predicted, 78 seen; treated 55 to 100 predicted, 39 seen) and held on sign (treated mean negative, PF 0.3 to 0.9 predicted, 0.87 seen); it missed on "treated beats control" (it was 1.7c worse). No lead: nothing came near the 6c lift over the pooled -5.5c to -6c baseline that the standing rule demands (control here is -0.36c, a much better baseline than the pooled cheap side, so the family is not a worse place, just not an edge).

## Accrual
The ties cluster in the July and August qualifying rounds plus a handful of spring knockouts, about 140 settled ties a year of which about 117 usable and about 39 treated. 150 treated needs roughly 4 seasons, so no forward probe is worth building; adding KXUELADVANCE (a few dozen ties a year) would not change that. Not recommended for the recorder.

## Other families checked by count only (no price fetched)
Season-long futures, playoff qualification, awards and touch ladders have 1 to 2 settled events a series (one season each), far under 100 events; KXNCAAFWINS has 73, KXSERIECCUPADVANCE 45, drafts 20 or fewer, KXSVKCUPADVANCE 110 is a single match equal to the game winner. SEASON1 (another worker) already owns win-total ladders.

## Limits
Name matching is by token overlap and ESPN covers 22 fewer ties than Kalshi lists; the look is the last 1 minute candle at least 300 seconds before the ESPN kickoff, so a market that closed early or moved in the last minutes is not seen; candle asks are quotes, not fills; one trade per tie so n is independent ties but only 2 seasons of two-leg ties exist (2026 only).
