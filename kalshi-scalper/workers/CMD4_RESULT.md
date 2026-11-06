# CMD4 result (2026-11-06): NOT_ENOUGH_DATA per cell; map printed (development only)

Registration `workers/CMD4_REGISTRATION.md`. Cells with at least 10 trades (gross after the recorded spread, before fee; break-even fee per side = gross / 2):
| pair | rule | n | gross bp | break-even fee bp/side | net 5 | net 12 | net 24 | hit |
|---|---|---|---|---|---|---|---|---|
| silver | R2 H=5 | 60 | +0.48 | 0.24 | -9.5 | -23.5 | -47.5 | 0.43 |
| copper | R1 H=15 | 39 | +0.15 | 0.07 | -9.9 | -23.9 | -47.9 | 0.36 |
| copper | R2 H=5 | 75 | -2.76 | -1.38 | -12.8 | -26.8 | -50.8 | 0.37 |
| WTI | R2 H=5 | 11 | -0.81 | -0.41 | -10.8 | -24.8 | -48.8 | 0.45 |
Under 10 trades (n only): gold R1 0, R2 0; silver R1 3; WTI R1 1; US 500 R1 0, R2 0; Tech 100 R1 5, R2 0 (the cheapest perps, gold 0.5 bp and the two indices, almost never show a 10 bp basis deviation or an uncaught 5 bp futures move, so they have no map at all). **Verdict word NOT_ENOUGH_DATA for every cell** (60 trades on 15 clusters needed; three clusters exist). Prediction held: every break-even fee is under 3 bp a side (all under 0.3 bp, none near the 12 bp placeholder), copper and WTI under 1.5, the cheap pairs under 10 trades. Next read about **2026-12-04**.
N +12 as registered. No lead.
