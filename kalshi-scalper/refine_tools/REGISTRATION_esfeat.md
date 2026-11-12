# S-ESFEAT1, forward follow-up of the early-sell separation, registered 2026-11-08 before any forward fill is scored
[live figure removed, ask Main] That read passed nothing (survivors []); two features were the only ones whose high-risk group was the lowest tercile in BOTH split directions. Those two are carried forward. Nothing else.

## The two leads (fixed)
1. Paid price in the lowest tercile (T1, price of the side bought, avgFill if yes else 1 - avgFill). [live figure removed, ask Main] Earlier read: train 9.1% (10/110) vs rest +7.6 points, test 12.9% (8/62) +5.3 points; reverse direction also T1 (+9.6 train, +3.0 test).
2. rise3 in the lowest tercile (T1). [live figure removed, ask Main] Rows with no rise3 are left out of lead 2 only.

## Forward window and outcome
[live figure removed, ask Main] Early sell = result "exit"; non-early = settled yes/no. Open or unsettled fills are not counted until they settle.

## Statistic
[live figure removed, ask Main] Cutoffs are never refit.

## Read point
[live figure removed, ask Main] Before that the script prints counts only and no verdict.

## Pass bar (information only; any change to the bot needs the owner)
[live figure removed, ask Main] A lead that fails is CLOSED and not re-run on a new cut or cutoff (circling rule).

## Multiplicity
Cuts counted: these 2 leads, plus the earlier read's 16 feature-direction tests, plus its score (2) and about 24 group rates per direction. Total cuts carried in the count: 2 + 16 = 18 tests (plus the score tests, 20). Bonferroni one-sided bar over 20 is p under 0.0025; the script reports the raw p and the 20-test bar and says which clears. Only a clear of the raw bar plus the 4 point and direction conditions is a "lead confirmed"; clearing the 0.0025 bar is the only thing that would be called a finding.

## Dollars
[live figure removed, ask Main] The exit fee is not in the data, so early-sell losses are slightly understated. settledPnl (limit-booked) is not used. Descriptive only.
