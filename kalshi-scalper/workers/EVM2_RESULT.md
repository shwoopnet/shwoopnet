# EVM2 result (run once 2026-11-06, development only): NOT_ENOUGH_DATA (0 trades; the trigger never occurs)

Registration `EVM2_REGISTRATION.md`; code `EVM_score.py`, output `EVM_output.txt`. Development 656 closes, 627 with a usable basis; held out third never read.

**Zero closes had |B| of 20 bp or more.** Descriptive distribution of |B| at the decision minute (disclosed, not a new try): median 1.55 bp, 90th percentile 3.10, 99th 5.03, maximum 7.45. The ladder's 50 percent strike sits within a few basis points of the perp mid 25 minutes before every close, so there is no basis to trade (the registered prediction of a 10 to 25 percent trigger rate was wrong; the ladder is anchored to the same price, not slow).
For reference the control (every close, sign of B, any size): n 627, gross -0.45 bp, cost 25.44 bp (recorded perp spread plus 24 bp fee plus 1 bp funding), net -25.88 bp, PF 0.07 (x1.2 net -30.97, PF 0.05); D1 net -25.73 bp (n 313), D2 -26.03 bp (n 314). As predicted, the gap carries no information and the cost is the whole result.
Verdict: NOT_ENOUGH_DATA under the registered rule (0 of 100 trades), and in substance no mechanism: more data on Bitcoin hourly will not change it unless the ladder starts lagging. N +1. Read 2026-11-06.
