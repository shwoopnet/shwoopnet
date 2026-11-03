# HRSEAS1 result: clock-block seasonality of the cheap tail on the hourly Bitcoin ladder (run once 2026-11-03)

Registered and pushed first (`workers/HRSEAS1_REGISTRATION.md`, sha256 `9b1ff73432e847fe32ff9669c4ee3987f172f558a2c90080d44f84a0a15e701a`); code `src/scalper/hrseas1.py`, tests `tests/test_hrseas1.py`; full development output `workers/HRSEAS1_output.txt`. Development scored once (`run`, refuses a second). The frozen last third was then read ONCE (`w3`), and only for the one slot that passed development, as registered in section 8. No rule, block, band or look changed after registration (the `w3` function was appended after the development run, for the registered purpose).

## Verdict: FALSIFIED. All 7 tail blocks fail; the one development PASS (favourite 85c to 97c on weekends) failed the frozen holdout.

**Data reach.** 956 settled KXBTCD hourly closes (2026-08-24 to 2026-11-03) in `data/conf2_lad.sqlite`; 772 in development (to 2026-10-10), 184 in the frozen last third. The cache has gaps (not every day has a ladder). KXETHD: 14 days only, not runnable. Nothing new fetched (the local cache is the only source of that span; the book recorder started 2026-10-29).

**Baseline (all hours, tail 3c to 30c, hard limit 0.30, C = 10, fee-rounded, development):** n 1,348, win 15.1% against a mean price 17.4c, net -3.3c per contract, **PF 0.78** (half 1 0.75, half 2 0.88). The tails are priced about fairly; the fee plus the spread is the loss, as in VOLGAP1, LADLONG1 and OIHR1.

**Tail, by block (development; PF half 1 / half 2; block minus control in c per contract, half 1 / half 2).**
| Block | n (both halves) | win vs price | PF h1 / h2 | block-control h1 / h2 | Verdict |
|---|---|---|---|---|---|
| ASIA_OPEN (00-02) | 176 | 17.0% vs 17.7c | 0.64 / 1.74 | -2.9 / +14.0 | FALSIFIED (h1) |
| NIGHT_LULL (03-06) | 230 | 12.2% vs 17.2c | 0.61 / 0.62 | -1.3 / -5.0 | FALSIFIED |
| LONDON_OPEN (07-09) | 157 | 14.6% vs 16.4c | 0.82 / 0.76 | +1.7 / -3.3 | FALSIFIED |
| US_OPEN (13-15) | 160 | 20.0% vs 19.7c | 0.93 / 1.03 | +1.0 / +0.3 | FALSIFIED (PF under 1.5; best block, win equals price) |
| US_CLOSE (19-21) | 164 | 12.2% vs 15.5c | 0.53 / 1.15 | -2.7 / +4.5 | FALSIFIED |
| FUNDING (00, 08, 16) | 166 | 16.3% vs 17.5c | 0.82 / 0.91 | +0.9 / +1.1 | FALSIFIED |
| WEEKEND (Sat, Sun) | 348 | 9.8% vs 14.1c | 0.60 / 0.61 | -2.0 / -5.4 | FALSIFIED (tails lose more, PF 0.60, the lull is priced too dear if anything) |

n per block is 157 to 348 (at or over the 150 floor), so the verdicts are FALSIFIED, not NOT_ENOUGH_DATA. No tail block clears PF 1.5 in both halves; no block-minus-control is positive in both halves with PF near 1.5. High-vol blocks (US open, Asia open) show win rates at or above price but the edge is 0 to 1c, not the 8c a PF of 1.5 needs. Low-vol blocks (night, weekend) are WORSE than baseline, the opposite of "tails too dear there" being exploitable on the tail side.

**Mirror (favourite 85c to 97c, nearest 0.90, hard limit 0.97).** Baseline n 1,438, win 92.6% vs price 91.1c, PF 1.14.
- NIGHT_LULL: n 239, PF 1.57 / 1.11, diff +2.3c / -0.7c: FALSIFIED (fails h2).
- **WEEKEND: n 315, win 95.9% vs 91.8c, PF 1.81 / 2.33, diff +2.9c / +3.5c: PASS_DEVELOPMENT** (the only slot to do so; bootstrap by close for the diff, 5th percentile +0.04c in h1 and -0.65c in h2, so the interval already touches zero).
- Registered consequence: read W3 once for this slot. **W3 (Oct 10 to Nov 3, 24 days, 3 weekends): n 81, win 92.6% vs price 92.5c, net -0.39c, PF 0.94 (fees x1.2: 0.93); control n 265 PF 0.96; weekend minus control +0.2c (bootstrap -5.3c to +5.3c). The edge is gone: FALSIFIED on the holdout** (n 81 is under 150, so the count is thin, but the PF and the 3.5c premium both vanish, and PF 0.94 is far from 1.5).
- Post-hoc diagnostic (not a bar): in development the weekend premium rests on 8 weekend days (the cache has gaps) against 25 other days; day-clustered z of the difference 2.3, and 7 of the 8 weekend days still held at least one losing favourite (13 losses of 315 at about 90c each). The family has nine slots tried; one development pass with z 2.3 on 8 clusters is what chance gives (about 9 x 0.01 expected), and the holdout agrees.

**Prediction check.** Baseline PF 0.78 (predicted 0.65 to 0.85, inside); win 15.1% vs 17.4c (inside); no block passes (true after the holdout); at most two blocks above 1.0 in a half: wrong (ASIA h2, US_CLOSE h2 and US_OPEN h2 are above 1.0, three; all at n 38 to 46, noise); block-minus-control within +-6c: ASIA_OPEN h2 +14.0c is outside, at n 45 and with h1 at -2.9c. Trades per block 157 to 348 (predicted 100 to 300): near.

## Interpretation
Hour-of-day and weekday effects in the hourly Bitcoin ladder's tail pricing are not there at this sample: win rates sit at or under price in every block, in both halves for 5 of 7. The maker quoting a constant vol is not visible in the cheap tail; the only apparent clock gain (weekend favourites) was one development half-pair and did not hold forward. The all-hours tail PF of about 0.78 and the favourite PF of 1.14 are the structural (unconditional) numbers.

## Probe spec
None. No slot is positive in both halves and the one that passed development failed the holdout. Months to 150 trades on the holdout slot is moot.

N +18 (nine slots at +2: seven tail blocks, two favourite mirrors). Running about 730,012 + 18 = 730,030 by this worker's count; the coordinator keeps the true total.
