# S-ESFEAT1, forward follow-up of the early-sell separation, registered 2026-11-08 before any forward fill is scored
Source: S/w_earlysell_sep/REGISTRATION.md and out.txt (run3.py, report generated 2026-11-07). That read passed nothing (survivors []); two features were the only ones whose high-risk group was the lowest tercile in BOTH split directions. Those two are carried forward. Nothing else.

## The two leads (fixed)
1. Paid price in the lowest tercile (T1, price of the side bought, avgFill if yes else 1 - avgFill). Cutoffs from the TRAIN (early) half, by market: gold T1 is paid <= 0.911, Dogecoin T1 is paid <= 0.903 (out.txt "price cuts fwd"; T2 upper edges 0.94 and 0.941, unused). Earlier read: train 9.1% (10/110) vs rest +7.6 points, test 12.9% (8/62) +5.3 points; reverse direction also T1 (+9.6 train, +3.0 test).
2. rise3 in the lowest tercile (T1). Cutoffs from the same early train half, by market: gold T1 is rise3 <= 0.05, Dogecoin T1 is rise3 <= 0.04 (run3.py cuts on 78 gold and 104 Dogecoin early-half rows; the T2 edges 0.12 and 0.135 are unused). Earlier read: train 7.8% (5/64) +5.3 points, test 11.8% (8/68) +3.7 points; reverse also T1 (+5.6, +6.9). Rows with no rise3 are left out of lead 2 only.

## Forward window and outcome
Gold (KXGOLD) and Dogecoin (KXDOGE) L1 fills (count > 0, avgFill present) with order ts AFTER 2026-11-08T12:44:00Z. Dogecoin is paused since Nov 3, so this is expected to be gold only; gold reopens Sunday about 6 PM CT. Early sell = result "exit"; non-early = settled yes/no. Open or unsettled fills are not counted until they settle.

## Statistic
Per lead: early-sell rate in the high-risk group H (T1) vs the rest, exact Clopper-Pearson 95% intervals, difference in points, and a one-sided exact Fisher test (H higher). Cutoffs are never refit.

## Read point
20 early sells (about 2 to 4 weeks) or 300 fills, whichever comes first. Before that the script prints counts only and no verdict.

## Pass bar (information only; any change to the bot needs the owner)
A lead passes only if at the read point: the H early-sell rate exceeds the rest by at least 4 points AND the one-sided exact Fisher p is under 0.05 before deflation (reported with the deflated bar) AND the direction matches both halves of the earlier read (T1 was H in train and test, forward and reverse: true for both leads, fixed here). A lead that fails is CLOSED and not re-run on a new cut or cutoff (circling rule).

## Multiplicity
Cuts counted: these 2 leads, plus the earlier read's 16 feature-direction tests, plus its score (2) and about 24 group rates per direction. Total cuts carried in the count: 2 + 16 = 18 tests (plus the score tests, 20). Bonferroni one-sided bar over 20 is p under 0.0025; the script reports the raw p and the 20-test bar and says which clears. Only a clear of the raw bar plus the 4 point and direction conditions is a "lead confirmed"; clearing the 0.0025 bar is the only thing that would be called a finding.

## Dollars
Any dollar figure is fill-booked: count * (exitAvg for an early sell, 1 or 0 for a settled fill, minus avgFill of the side bought) minus entry fee avgFee * count. The exit fee is not in the data, so early-sell losses are slightly understated. settledPnl (limit-booked) is not used. Descriptive only.
