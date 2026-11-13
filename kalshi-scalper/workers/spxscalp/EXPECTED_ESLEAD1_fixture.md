# ESLEAD1: expected figures on the made-up fixture, written BEFORE the scorer

Computed independently (plain Pearson on the paired lists, the changes dES(t)=ES(t)-ES(t-1) and dK(t)=mid(t)-mid(t-1), t=1..9, mid rounded to 2 places). dES: 1,0,2,-1,2,0,1,2,-1. dK: 0,0.02,0,0.04,-0.01,0.04,0,0.01,0.04. Lag k pairs dES(t) with dK(t+k); pairs where t+k is outside 1..9 are dropped.

| lag | n pairs | correlation |
|---|---|---|
| -3 | 6 | -0.1673 |
| -2 | 7 | -0.0838 |
| -1 | 8 | 0.5028 |
| 0 | 9 | -0.8815 |
| 1 | 8 | 0.9734 |
| 2 | 7 | -0.7150 |
| 3 | 6 | 0.4345 |

Verdict on the fixture: the largest correlation is at lag +1, so the prediction "peak at lag 0" would be NOT met here (ES leads by one minute). Lag 0 is -0.8815 (a made-up value). A scorer that returns this table to 4 decimals, n per lag exactly as above, and the verdict "peak at lag +1, not lag 0", matches. Tolerance: 0.0001 on each correlation, n exact. A lag with fewer than 3 pairs prints n and "NA".
