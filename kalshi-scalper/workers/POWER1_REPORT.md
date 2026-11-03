# POWER1: how soon can each forward test decide, and what effect could it detect? (support analysis, N +0, 2026-11-03)

Support task. No new try, no outcome scored, no frozen holdout read. Code `src/scalper/power1.py` (`PYTHONPATH=src python3 -m scalper.power1 table`), tests `tests/test_power1.py`
(analytic formulas checked against simulation), table `workers/POWER1_TABLE.csv` (one row per test, every column below plus the raw grid). Inputs are the arrival
rates and prices in each worker's own registration or result (source per row in the CSV `source` column); anything I had to assume is marked `assumed`.

## Headline (read this first)

1. **At the registered deflated bar (z 5.27) no forward test can pass inside 120 days at a +2c edge, and the next fastest test needs more than 2,700 days.** The shortest run that
   reaches z 5.27 at +2c on the median is 308 days (MAKERTAIL1, 36 fills a day, 80% power: 415 days). Everything else needs 2,700 days or more (7 years and up) at +2c.
2. **At +5c a trade only the high-count tests get there:** MAKERTAIL1 in 49 to 66 days (median to 80% power), then WXENS1 512 to 689 days, USWEEP1 460 to 755, SPORTSPRE 437 to 588,
   RAINCAL 800 to 1,080. EVENT830, BARRIER1, DERIBIT, NOWCAST1, FEDIMPL1, COUNT1 and ELECT1 cannot reach it in any horizon the project has (11 to 100+ years).
3. **What a test CAN do inside a quarter is kill, and kill weakly.** At the floor n the edge you need for 80% power at 5.27 is 15c to 32c per trade on cheap-side prices of 6c to 40c.
   That is an edge bigger than the price paid on the 6c to 12c tests (a win rate 2.5 to 4 times the ask). A real +2c edge survives the registered kill rules only 4% to 28% of the time
   (a zero edge survives 2% to 17%), so "NOT_YET_FALSIFIED" is worth a likelihood ratio of roughly 2 to 3, not a green light.
4. **Reference: the bar was only ever reachable by edges as large as L1's and OICORE's.** Live L1 gold at its published +4.3c a contract (sd 19c, win rate 96%) needs about 543 trades
   (70 days at 7.8 fills a day, 94 days to 80% power) to reach z 5.27; OICORE's history edge (+13.9c, sd 45c) needs 443 trades (74 days at 6 a day, 99 days to 80% power). A +2c edge on a
   sd 30c to 50c cheap-side trade needs 7,500 to 45,000 trades (80% power).
5. **Implication for the goal "profitable and ready to deploy":** waiting on forward readings of thin cheap-side edges is not a path to a deployable strategy inside a quarter. Only
   families with (i) a per-trade edge of at least the cheap price itself, or (ii) a payoff with a low sd (favourites, which the Oct 28 ban covers), or (iii) 30+ trades a day, can decide
   in 30 to 120 days, and of those only MAKERTAIL1 is cheap-side, and its development sign is negative (-0.96c to -1.56c per resting order, DEV).

## Model (so it can be checked by hand)

One contract at mean price a, held to settlement. Fee per contract = ceil(70 a (1-a)) cents / 10 (7% x C x p x (1-p), C = 10, rounded up). Break-even win rate c = a + fee. A true edge
e (dollars per contract AFTER fee) means win probability p = c + e. Net per trade = win - c, sd = sqrt(p (1-p)) (the fee is a constant at a given price, so it moves the mean, not the sd:
at a = 12% the sd is 33c, at 5.8% it is 24c, at 25% it is 44c, at 50% it is 50c). Day clustering: deff = 1 + (m - 1) rho, standard error sd x sqrt(deff / n). (a) Edge with 80% power:
(z + 0.8416) x se. (b) Trades for expected z: deff (z sd / e)^2, for 80% power deff ((z + 0.8416) sd / e)^2; days = trades / arrival rate. (c) A Monte Carlo (20,000 runs per cell, seed 20261103;
beta-binomial day clusters; cluster-robust z with the G/(G-1) factor; the registered PF and both-halves kill rules) gives the false positive and pass rates; NOT_ENOUGH_DATA is
compound Poisson (clusters arrive at rate/m, m trades each) at the low, central and high arrival rate of the registration. Days count from 2026-11-03 with accrual running; add any delay for a recorder that is not yet live.
Checks in the tests: the closed forms invert each other, the simulated power at the analytic 80% edge is 0.80 +/- 0.03 (no clustering) and 0.80 +/- 0.06 (60 clusters), the zero-edge z>=2 rate is 0.023 +/- 0.008.

## Table A: what each test can see (a = mean price, `deff` includes my assumed rho)

| Test | price | sd/trade | deff | trades/day (low-high) | floor | days to floor | edge for 80% power at 5.27, at floor | same at 30 / 60 / 120 d | z3 at 120 d | verdict possible 30/60/120 d |
|---|---|---|---|---|---|---|---|---|---|---|
| EVENT830 | 25.0c | 44.08c | 2.14 | 1.15 (0.93-1.38) | 150 | 130.4 | 32.18c | 67.1 / 47.44 / 33.55c | 21.09c | no/no/no |
| WXENS1 | 12.5c | 33.96c | 1.6 | 4.0 (1.6-8.0) | 150 | 37.5 | 21.43c | 23.96 / 16.95 / 11.98c | 7.53c | no/yes/yes |
| MAKERTAIL1_comb | 5.8c | 24.12c | 2.75 | 36.0 (21.0-57.0) | 150 | 4.2 | 19.96c | 7.44 / 5.26 / 3.72c | 2.34c | yes/yes/yes |
| MAKERTAIL1_NO | 5.7c | 23.93c | 1.85 | 18.0 (10.0-28.0) | 150 | 8.3 | 16.24c | 8.56 / 6.05 / 4.28c | 2.69c | yes/yes/yes |
| MAKERTAIL1_YES | 5.8c | 24.12c | 1.85 | 18.0 (10.0-28.0) | 150 | 8.3 | 16.37c | 8.63 / 6.1 / 4.31c | 2.71c | yes/yes/yes |
| NOWCAST1 | 12.0c | 33.41c | 1.0 | 0.023 (0.016-0.03) | 150 | 6521.7 | 16.67c |  / 173.81 / 122.9c | 77.25c | no/no/no |
| FEDIMPL1 | 10.0c | 30.91c | 1.0 | 0.068 (0.05-0.11) | 150 | 2205.9 | 15.43c | 132.27 / 93.53 / 66.13c | 41.57c | no/no/no |
| COUNT1_weekly | 11.5c | 32.84c | 1.0 | 0.059 (0.04-0.09) | 150 | 2542.4 | 16.39c | 150.88 / 106.69 / 75.44c | 47.42c | no/no/no |
| COUNT1_daily | 10.0c | 30.91c | 1.0 | 0.1 (0.03-0.3) | 150 | 1500.0 | 15.43c | 109.07 / 77.13 / 54.54c | 34.28c | no/no/no |
| BARRIER1 | 12.0c | 33.41c | 2.0 | 0.12 (0.1-0.14) | 150 | 1250.0 | 23.58c | 152.19 / 107.61 / 76.09c | 47.83c | no/no/no |
| USWEEP1_NATGAS | 92.0c | 26.18c | 7.12 | 11.2 (8.0-14.0) | 100 | 8.9 | 42.69c | 23.29 / 16.47 / 11.64c | 7.32c | yes/yes/yes |
| USWEEP1_GOLDD | 92.0c | 26.18c | 2.9 | 4.8 (3.0-6.5) | 100 | 20.8 | 27.24c | 22.7 / 16.05 / 11.35c | 7.14c | yes/yes/yes |
| USWEEP1_SILVERD | 92.0c | 26.18c | 2.55 | 4.1 (2.5-5.5) | 100 | 24.4 | 25.55c | 23.04 / 16.29 / 11.52c | 7.24c | yes/yes/yes |
| USWEEP1_BRENTD | 92.0c | 26.18c | 1.7 | 2.4 (1.5-3.5) | 100 | 41.7 | 20.86c | 24.58 / 17.38 / 12.29c | 7.73c | no/yes/yes |
| USWEEP1_HIGHTSATX | 92.0c | 26.18c | 1.18 | 1.6 (1.0-2.2) | 100 | 62.5 | 17.38c | 25.08 / 17.74 / 12.54c | 7.88c | no/no/yes |
| ELECT1_REF | 12.0c | 33.41c | 1.0 | 0.0 (0.0-0.0) | 150 | fixed read | 91.31c | 91.31 / 91.31 / 91.31c | 57.4c | no/no/no |
| RAINCAL | 40.0c | 49.31c | 1.72 | 5.8 (4.2-7.5) | 150 | 25.9 | 32.27c | 29.96 / 21.19 / 14.98c | 9.42c | yes/yes/yes |
| DERIBIT_IMPLIED | 50.0c | 49.97c | 1.13 | 2.33 (1.5-3.5) | 150 | 64.4 | 26.54c | 38.88 / 27.49 / 19.44c | 12.22c | no/no/yes |
| SPORTSPRE | 38.0c | 48.93c | 1.36 | 8.3 (6.7-10.0) | 200 | 24.1 | 24.7c | 22.14 / 15.66 / 11.07c | 6.96c | yes/yes/yes |
| STRADDLE1 | - | 12.0% | 1.9 | 0.0 (0.0-0.0) | 300 | fixed read | 1.53% | 1.53 / 1.53 / 1.53% | 0.96% | yes/yes/yes |
STRADDLE1 is in percent of premium (sd 12%), blocked on a data source rather than on time; its z 5.27 detectable edge on the 4,355 first-two-thirds events is 1.53% of premium (0.96% at z 3), and
the 2,155-event final third alone could see only 2.2%. ELECT1 is one night: REF has 5 trades, so the edge needed (91c) exceeds the largest possible win (88c): it can never decide.

## Table B: how long, how often wrong

| Test | days to z 2 / 3 / 5.27 at +2c (median run) | days at +5c | n for 80% power at 5.27, +2c | +5c | FP: survive kill rule, edge 0 | FP: z>=3, edge 0 | survive kill rule at +2c | P(NOT_ENOUGH_DATA) low/central/high rate, horizon |
|---|---|---|---|---|---|---|---|---|
| EVENT830 | 3,616 / 8,135 / 25,105 | 578 / 1,302 / 4,017 | 38829 | 6213 | 17.4% | 0.07% | 27.8% | 95% / 70% / 31%, 120 d |
| WXENS1 | 461 / 1,038 / 3,202 | 74 / 166 / 512 | 17229 | 2757 | 5.4% | 0.01% | 15.5% | 8% / 0% / 0%, 117 d |
| MAKERTAIL1_comb | 44 / 100 / 308 | 7 / 16 / 49 | 14935 | 2390 | 5.7% | 0.80% | 14.0% | 0% / 0% / 0%, 120 d |
| MAKERTAIL1_NO | 59 / 132 / 409 | 9 / 21 / 65 | 9896 | 1584 | 4.3% | 0.16% | 14.0% | 0% / 0% / 0%, 120 d |
| MAKERTAIL1_YES | 60 / 134 / 415 | 10 / 22 / 66 | 10047 | 1608 | 4.7% | 0.08% | 14.7% | 0% / 0% / 0%, 120 d |
| NOWCAST1 | 48,529 / 299 y / 923 y | 7,765 / 17,470 / 53,911 | 10423 | 1668 | 2.4% | 0.02% | 11.3% | 100% / 100% / 100%, 120 d |
| FEDIMPL1 | 14,052 / 31,616 / 97,564 | 2,248 / 5,059 / 15,610 | 8923 | 1428 | 4.5% | 0.03% | 17.2% | 100% / 100% / 100%, 120 d |
| COUNT1_weekly | 18,283 / 41,137 / 348 y | 2,925 / 6,582 / 20,311 | 10073 | 1612 | 2.5% | 0.02% | 11.1% | 100% / 100% / 100%, 120 d |
| COUNT1_daily | 9,555 / 21,499 / 66,343 | 1,529 / 3,440 / 10,615 | 8923 | 1428 | 4.2% | 0.03% | 17.7% | 100% / 100% / 100%, 120 d |
| BARRIER1 | 18,603 / 41,856 / 354 y | 2,976 / 6,697 / 20,666 | 20846 | 3336 | 7.2% | 0.01% | 17.1% | 100% / 100% / 100%, 120 d |
| USWEEP1_NATGAS | 436 / 980 / 3,025 | 70 / 157 / 484 | 45560 | 7290 | 43.6% | 28.50% | 55.6% | 0% / 0% / 0%, 120 d |
| USWEEP1_GOLDD | 414 / 932 / 2,874 | 66 / 149 / 460 | 18557 | 2970 | 28.5% | 11.03% | 44.1% | 0% / 0% / 0%, 120 d |
| USWEEP1_SILVERD | 426 / 959 / 2,959 | 68 / 153 / 474 | 16317 | 2611 | 27.7% | 8.90% | 44.6% | 0% / 0% / 0%, 120 d |
| USWEEP1_BRENTD | 485 / 1,092 / 3,370 | 78 / 175 / 539 | 10878 | 1741 | 26.0% | 3.96% | 48.2% | 0% / 0% / 0%, 120 d |
| USWEEP1_HIGHTSATX | 505 / 1,137 / 3,509 | 81 / 182 / 561 | 7551 | 1209 | 25.4% | 3.09% | 49.9% | 7% / 0% / 0%, 120 d |
| ELECT1_REF | - / - / - | - / - / - | 10423 | 1668 | 7.9% | 0.13% | 10.4% | 100% / 100% / 100%, 0 d |
| RAINCAL | 721 / 1,622 / 5,006 | 115 / 260 / 801 | 39047 | 6248 | 6.6% | 0.24% | 11.8% | 0% / 0% / 0%, 59 d |
| DERIBIT_IMPLIED | 1,214 / 2,732 / 8,430 | 194 / 437 / 1,349 | 26416 | 4227 | 1.7% | 0.24% | 4.4% | 100% / 77% / 0%, 59 d |
| SPORTSPRE | 394 / 886 / 2,734 | 63 / 142 / 437 | 30514 | 4883 | 5.1% | 0.24% | 11.8% | 0% / 0% / 0%, 59 d |
Notes on Table B. Days are the median run (expected z reaches the bar) and are shown with the floor applied (a test cannot read before its floor). The 80% power versions are in the CSV
(`days80_*`, `n80_*`). `y` is years. The false positive column is "a test with a true edge of 0 survives the registered kill rules at the floor n" (pooled PF, each half positive, x1.2 fee PF above 1;
EVENT830's event-minus-control condition is not modelled, so its figure is an overstatement). **A zero edge passing z 5.27 is 7e-8 in the normal approximation and 0 in 20,000 simulated runs for
every test except the USWEEP1 rows, where it is not an edge: a favourite at 92c loses rarely and in lumps, so a run with no losing day makes the cluster-robust z infinite (28% for natgas at n 100). The
registered statistic would be undefined there; read those rows as "the test cannot be judged by a z at n 100", not as a pass rate.**

## Which tests can decide within 30, 60 and 120 days, at a plausible +2c

"Decide" is split in two because the registered rules mostly kill and almost never pass:

* **Can reach a verdict other than NOT_ENOUGH_DATA (floor n reached, central rate).**
  * Within 30 days: MAKERTAIL1 (4.2 days combined, 8.3 days per side; but with day clusters I would not read under 10 days), RAINCAL (25.9 days; the read is fixed at 2027-01-01, so it is date-bound, not count-bound), SPORTSPRE (24.1 days at 8.3 a day to its floor of 200; also read 2027-01-01), USWEEP1 natgas (8.9), gold daily (20.8) and silver daily (24.4) if the ruling allows.
  * Within 60 days: add WXENS1 (37.5 days at 4 a day, but only if the recorder is live; it is not on origin yet and the range is 19 to 94 days), USWEEP1 Brent (41.7).
  * Within 120 days: add DERIBIT-IMPLIED (64 days, but its stop is 59 days away, so P(NOT_ENOUGH_DATA) is 77% central and 100% at the low rate), USWEEP1 Texas high (62.5). EVENT830 reaches its 150 floor in 130 days (109 to 161), so it will be NOT_ENOUGH_DATA at 120 days with probability 70%.
  * Never inside any horizon: NOWCAST1 (6,500 days), FEDIMPL1 (2,200), COUNT1 weekly (2,500), COUNT1 daily (1,500, assumed rate), BARRIER1 (1,250), ELECT1 (one night, 5 trades).
* **Can PASS z 5.27 with 80% power at +2c inside the horizon:** none, at 30, 60 or 120 days. Smallest detectable edge at 120 days with 80% power: MAKERTAIL1 3.7c (4.3c per side), then SPORTSPRE 11.1c (at its 59 day stop 15.7c), WXENS1 12.0c (at the 117 day stop), USWEEP1 11.4c to 12.5c, RAINCAL 15.0c (at 59 days 21.2c), DERIBIT 19.4c, EVENT830 33.6c, BARRIER1 76c, COUNT1 54c to 75c, FEDIMPL1 66c, NOWCAST1 123c. Anything above about 30c is above the largest win the price allows, i.e. cannot happen.
* **Ranking by how plausible a decision is** (smaller is better; "plausible edge" = +2c): 1 MAKERTAIL1 (detects 3.7c in 120 days, on a strategy whose development sign is negative and that the owner would not deploy without a pass), 2 SPORTSPRE (11c at its stop; prior of a pass 3%), 3 WXENS1 (12c at its stop, 8% chance of NOT_ENOUGH_DATA even at the central rate), 4 USWEEP1 x5 (11c to 12.5c; **ruling needed, favourite-and-hold ban of Oct 28; no daily feed exists, ledger rows stay at 0 trades**), 5 RAINCAL (15c at 120 days, 21c at its stop), 6 DERIBIT-IMPLIED (19c, likely NOT_ENOUGH_DATA), 7 EVENT830 (34c), then the five dormant rows, which cannot decide.

## The five USWEEP1 watch items (ruling needed)

All five are favourites held to settlement (ask 0.85 to 0.97), so the Oct 28 owner instruction bans further research on them. They are listed because the arithmetic is the most favourable of the
whole set: a favourite's sd is 25c, so 460 to 750 days reach z 5.27 at +5c and 11c to 12.5c is detectable inside 120 days. At the registered probe kill (40 fills, PF under 1.0) the zero-edge false kill
rate is not the issue; the issue is that the rare 97c loss makes 40 fills mostly a count of lucky days (natgas 40 fills in 4 days is 4 independent days). Not built, not scored, not proposed.

## False positive and NOT_ENOUGH_DATA, in plain words

* P(a zero-edge test passes z 5.27): effectively 0 (7e-8). The deflated bar does its job. P(passes z 3): 0.01% to 0.8% (0.24% for the 15 minute-scale tests with 150 trades).
* P(a zero-edge test survives its registered kill rules at the floor n): 1.7% (DERIBIT) to 17% (EVENT830, overstated) for cheap-side tests; the survivors are then killed by the z bar, so the registered chain gives ~0% false passes.
* P(a real +2c edge survives the kill rules): 4% to 28% for cheap-side tests. Power to reach z 3 at +2c at the floor n is 0.2% to 2.4%. The registered bars were written to protect against false positives, and they are almost blind to a true +2c edge at these counts.
* P(NOT_ENOUGH_DATA at the stop date): RAINCAL 0% (350 expected trades vs floor 150), SPORTSPRE 0%, WXENS1 0% central (8% at the low rate), MAKERTAIL1 0%, DERIBIT-IMPLIED 77% central (100% low), EVENT830 70% central at 120 days (95% at the low rate), NOWCAST1, FEDIMPL1, COUNT1, BARRIER1 and ELECT1 100%.

## Reference rows (published live fills only, no new reads)

| Row | Edge used | sd per trade | Trades per day | Trades to z 5.27 (median / 80% power) | Days |
|---|---|---|---|---|---|
| L1 gold live (README: 155 fills, 149 wins, +$44.06 at 6.7 contracts) | +4.3c per contract (assumed rho 0.1) | 19c | 7.8 | 543 / 731 | 70 / 94 |
| OICORE Bitcoin history (358 trades, PF 2.33, win 29.1%; live CSV: 24 orders on 5 dates, 18 settled, 5 wins, +$25.03) | +13.9c | 45c | 6.0 | 443 / 595 | 74 / 99 |

If either live edge is half its published size, the days roughly quadruple (for L1 gold 280 to 375; for OICORE 295 to 400). At +2c L1 gold needs 908 days and OICORE 2,200 days.

## What this means for the owner's goal

* The registered z 5.27 is a bar that only a large or very frequent edge can clear on a quarter's data. A deployment decision for a new cheap-side family inside 120 days is not available from any registered forward test, at a plausible edge.
* Where waiting is worth it: MAKERTAIL1 (decides cheaply either way, in under a month, and the side split is already a hypothesis), and the 15 minute and recorded tests that are date-bound anyway (SPORTSPRE, RAINCAL, DERIBIT, WXENS1: they reach 150 to 350 trades by their read date, so they cost nothing to leave running, but expect NOT_YET_FALSIFIED at best, which is not a deploy signal).
* Where waiting is not worth it: NOWCAST1, FEDIMPL1, COUNT1, BARRIER1, ELECT1 (decades), EVENT830 (a verdict near March 2027, and a 150-trade pass bar that cannot be met at the registered z; the 40-trade early kill on 2026-12-04 is its only near-term event).
* The only way to a decision this quarter is more trades per day on a lower-variance payoff, or a bigger measured edge than 2c. That points at the families the project already has live (L1, OICORE), not at adding thin forward tests. Widening to 30+ trades a day on a new cheap-side family (weather brackets at 4 a day is not enough: 17,000 trades at +2c) would still not decide by itself.

## Limits (say them plainly)

Normal approximation for the closed forms (poor at 5% prices and small n; the Monte Carlo covers the pass and false positive cells only). A single price a per test, a single edge definition (edge after fee at a fixed price,
no price-dependent edge), rho and the cheap-side mean price assumed where not registered (EVENT830 rho 0.3, a 0.25; WXENS1 rho 0.2; MAKERTAIL1 rho 0.05; BARRIER1 rho 0.5; USWEEP1 rho 0.3 to 0.6; DERIBIT, SPORTSPRE and RAINCAL a and rho; COUNT1 daily rate; STRADDLE1 m and rho). Arrival rates are the workers' own, so any wrong rate scales
days linearly (the low and high rates are in the CSV). The registered statistic is not the same in every test (PF kill rules, Brier tests and control subtraction are not modelled, except PF and both-halves in the survival rule), so the z-based columns are the bar they all share, not each test's whole verdict.
MAKERTAIL1's fills are selected (a resting order fills when the price falls), which the Bernoulli model ignores. Nothing here is a result about any strategy.
