# FUNDP1, CARRY1, BASIS1 result (2026-11-06): all three NOT_ENOUGH_DATA

Registration `workers/FUNDP1_REGISTRATION.md` (committed and pushed before scoring). Scorer `workers/fundcarry/fundcarry.py`, prints `workers/fundcarry/as_registered_output.txt` and `amend1_output.txt`. Development only: 2026-10-21 to 2026-10-31 (11 dates, 53 samples, D1 to 10-26, D2 from 10-27). The held-out dates 2026-11-01 to 2026-11-06 were never opened. Times below are UTC timestamps in the data; the recorder samples 3 to 7 times a day (US Central is UTC minus 5 hours until Nov 1, minus 6 after).

**Verdict word: NOT_ENOUGH_DATA for FUNDP1, CARRY1 and BASIS1.** Every test has 11 trading days against the registered 20-day minimum for a day-clustered z, so no FALSIFIED is declared and every figure below is information only. Single-stock perps cannot be scored at all: `status` is inactive in every development sample (a structural fact from the status column, not a return).

**Amendment 1 (after the as-registered run, disclosed).** The first CARRY1 run printed a mean of -6.6e16 bp: copper's recorded ask on 2026-10-31 (five samples, 00:40Z to 22:24Z) is 922337203685477.5807, an int64 no-ask sentinel. Amendment 1 drops a quote whose ask is over twice its bid (a defect screen, not a tuning of the rule). It changes only CARRY1 (and removes 4 of the census rows); FUNDP1 and BASIS1 are identical either way. Both outputs are committed. No verdict changes.

## FUNDP1 (fade a premium over 0.10%, hold 7 to 12 hours)
88 trades on 11 days. Mean net **-6.1 bp** per trade at the 0.05% fee (win 55%, day z 0.06); D1 **-20.3 bp** (65 trades), D2 **+33.9 bp** (23 trades); stress at 0.12% a side: **-20.1 bp** (win 33%, z -0.80), D1 -34.3, D2 +19.9. Prediction was -8 bp and about 45% wins: the mean is close, the win rate was higher. The halves disagree in sign with 23 trades in D2, which is noise. Census of premiums: 258 universe entries with an exit in window, 4 inside the 0.002% deadband and 4 at or over the 2% funding cap after Amendment 1 (6 as registered; the cap is crossed by sentinel-free quotes of a thin book), too few for edge case (c): NOT_ENOUGH_DATA for it.

## CARRY1 (long lowest premium, short highest)
43 trades on 11 days (Amendment 1). Mean **-9.8 bp** (win 40%, day z -0.12); D1 **-42.5 bp** (28), D2 **+51.3 bp** (15); stress **-37.8 bp**. Prediction -15 bp, 40% wins: within range. As registered (with the sentinel) the mean is meaningless (-6.6e16 bp).

## BASIS1 (funding proxy versus round-trip cost, and convergence)
88 entries on 11 days. Mean funding proxy **+38.7 bp** per entry against a mean round-trip cost of **73.4 bp** (10 bp of fees plus about 63 bp of recorded entry and exit spread, driven by the wide WTI and copper books). Difference **-34.8 bp** (D1 -50.9, D2 +10.8, day z -0.24). The claim (funding alone beats the cost) is not supported, but it is not declared falsified at 11 days. **Convergence is low: mean 12%, median 5%**; the premium barely closes in 7 to 12 hours, so it is persistent (a stale reference, a structural basis, or a real standing premium), contrary to the prediction (median 60% converged, funding +9 bp). Part of that persistence is the proxy: funding is not recorded, and a 38.7 bp proxy per 8 hours assumes the rate is per 8 hours, which may be wrong by a large factor either way.

## What would settle it
(1) The actual funding rate, which the public market object does not carry. A recorded `funding_rate` or the exchange's funding payments would replace the proxy. (2) At least 20 trading days of active quotes in a fresh development third and about 10 untouched dates. At the recorder's rate (about 4 usable entry samples a day) that is about **2026-11-20** with a re-registered cut. (3) The single stocks need their own active days; the 30 second recorder (`perps30/`, not on origin/main yet, 0 files) around the open and close is the natural source.

## Count
N +3 (one rule per test). Running about 730,458, deflated z bar about 5.27.
