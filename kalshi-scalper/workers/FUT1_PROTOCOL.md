# FUT1: trend and carry on NYMEX crude oil and natural gas futures (registered Nov 9, 2026, before any rule is scored)
Research only. No account, no order, no spend, no key. Futures N is counted in its own ledger (workers/fut_ledger/), separate from the Kalshi N.

## Data (verified reachable Nov 9)
EIA public daily futures settlement series, no key: WTI contracts 1 to 4 (RCLC1..4, 1983/85 to 2024-04-05) and Henry Hub gas contracts 1 to 4 (RNGC1..4, 1993/94 to 2024-04-05). Files saved to data/fut/ (git-ignored; hashes go in workers/DATA_CHECKSUMS.txt). The series ends 2024-04-05 (EIA stopped updating it), so the test is historical. Equity index futures (ES/NQ) are NOT covered: still no reachable free source (Yahoo 429, Stooq reset).
## Continuous series construction (stated, fixed)
EIA contract 1 is the SPLICED nearest contract, so the raw C1 jumps at each expiry. Returns are built on contract identity: on a roll day the return is C1(t) against C2(t-1) (yesterday's second contract is today's first); otherwise C1(t) against C1(t-1). A roll day is detected where |C1(t)-C2(t-1)| < |C1(t)-C1(t-1)| and the C2-C1 spread of day t-1 is above 0.2% of price; ties are NOT rolls. Returns are therefore roll-adjusted P&L in dollars per contract (price change x contract multiplier: CL 1,000 barrels, NG 10,000 MMBtu); no back-adjusted price level is used for signals, only cumulative roll-adjusted returns.
## Rule family (all registered; N counted = 2 markets x 13 variants = 26, plus combined = 28)
Daily rebalance at the settle: position +1, 0 or -1 contract, set from data up to the previous settle (no lookahead; the signal on day t earns day t+1).
- TSMOM: sign of the trailing roll-adjusted return over L in {20, 60, 120, 250} trading days (4 variants).
- CARRY: long if C1 above C2 (backwardation), short if below, with a deadband of 0.2% of price (1 variant).
- TSMOM+CARRY: trade only when TSMOM(L) and CARRY agree, else flat, L in {60, 120, 250} (3 variants).
- Long/short skew checks: long-only versions of each of the above (5 variants) as the passive-beta control.
## Costs per contract per side
Full-size: commission and exchange fees 2.50 USD, slippage 1 tick (CL 10 USD, NG 10 USD) per side, applied on every change of position (a flip costs two sides); a roll costs one extra side (close old, open new). Stress: x2 on all costs. Micro contracts (MCL) have the same tick count at 1/10 the dollar scale; results scale linearly except fees, which are relatively larger, so micro is reported as a stress, not as a separate test.
## Judging (set now)
Windows: dev covers the first two thirds of each market's dates split W1/W2 of equal length; the last third by date is the HOLDOUT, read once and only for a rule that survives dev. Bar: net of costs, per window mean daily P&L > 0, annualized Sharpe >= 0.5 AND profit factor >= 1.5 on daily P&L in W1 and W2 each, with the day-block (month) bootstrap one-sided p below 0.05/N (N the futures ledger). Floors: 1,000 trading days per window. A trend rule that only holds on long-only crude 1986-2008 is the oil bull market, not a rule: the long-only controls must be beaten.
Predictions (stated before scoring): zero survivors (about 80%); if any, TSMOM on gas or carry on crude; equity-style trend profits since 2014 are weak. Verdict words: NOT_ENOUGH_DATA, FALSIFIED, NOT_YET_FALSIFIED (needs holdout), never a promote.
## Timeline
Scorer takes a day to write and test on synthetic data; first dev read within 24 hours of this commit.

## Amendment 1 (before scoring, Nov 9): variant count
The scorer lists 14 variants per market (4 TSMOM, 1 CARRY, 3 TC, 5 long-only controls of TSMOM and CARRY, 1 long-only TC:60), not 13, so N = 2 x 14 + 2 = 30 (stricter than the 28 written above). The exact list is workers/fut_ledger/FUT1_VARIANTS.txt, committed before the first score. Scorer: src/scalper/fut1.py (selftest passes: roll detection, costs, no lookahead).
