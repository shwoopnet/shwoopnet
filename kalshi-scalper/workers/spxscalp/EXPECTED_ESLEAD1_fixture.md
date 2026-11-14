# ESLEAD1: expected figures on the made-up fixture, written BEFORE the scorer (rewritten for Amendment 1)

Computed independently (plain Pearson, separate arithmetic). dA(t)=mid(t)-mid(t-1) for t=1..9: 0,0.02,0,0.04,-0.01,0.04,0,0.01,0.04. dB(t)=ln(ES(t)/ES(t-1)). Lag k pairs dA[t] with dB[t-k]. Floor lowered to 3 pairs for the fixture.

| lag | n pairs | correlation |
|---|---|---|
| -3 | 6 | -0.1565 |
| -2 | 7 | -0.0959 |
| -1 | 8 | 0.5096 |
| 0 | 9 | -0.8854 |
| +1 | 8 | 0.9733 |
| +2 | 7 | -0.7208 |
| +3 | 6 | 0.4391 |

Printed line (fixture): `lead/lag, 1 minute change correlation Kalshi mid vs ES at lags -3..+3: -3: -0.156, -2: -0.096, -1: 0.510, +0: -0.885, +1: 0.973, +2: -0.721, +3: 0.439`. Verdict on the fixture: the largest is at lag +1, so "peak at lag 0" is NOT met (ES leads by one minute). Tolerance 0.0001 on each correlation (printed at 3 decimals), n exact.

Correction (before any freeze of a scorer): the printed line above first said "-3: -0.157". The exact lag -3 correlation is -0.156453, which prints -0.156 at three decimals; -0.157 came from rounding the already-rounded four-decimal figure twice. The table's -0.1565 (four decimals) is right. Printed line fixed to -0.156. No scorer had been run when this was found; build 1's output was compared AFTER the fix and shows -0.156.
