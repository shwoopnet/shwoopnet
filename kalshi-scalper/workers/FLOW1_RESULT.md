# FLOW1 result (2026-11-04): FALSIFIED on the registered kill rules (Bitcoin 15 minute, taker flow, cheap side)

Scored once, `python3 -m scalper.flow1 score KXBTC15M`, at 05:12 UTC on the random prefix of 2,568 of 3,940 qualifying Bitcoin windows (Aug 6 to Oct 2; tape from /historical/trades and /markets/trades; Amendment 1 time box). The holdout was NOT read (the kill rules fired) and no window closing on or after 2026-11-03 was used. No favourite-side result exists. ETH and gold replication were not run (the rule says only if Bitcoin survives).

| half | LOW-flow cheap side | HIGH-flow cheap side | low minus high |
|---|---|---|---|
| D1 | n 423, win 14.7% vs paid 11.9c, net +2.10c, PF 1.23, 30 days | n 401, 15.7% vs 14.1c, +0.88c, PF 1.08 | +1.21c |
| D2 | n 426, win 15.5% vs paid 13.5c, net +1.29c, PF 1.13, 31 days | n 466, 20.8% vs 15.1c, +4.89c, PF 1.46 | -3.60c |

- Pooled D low at C=1: +1.13c; fees x1.2 PF 1.16. Within-day permutation of the low-minus-high difference: observed -1.35c, one sided p 0.487; low-half date-clustered z 1.55.
- By month (low): Aug +1.86c PF 1.20 (370), Sep +1.91c PF 1.20 (435), Oct -1.88c PF 0.84 (44).
- No R6 windows in D (they sit in the holdout): D1+D2 low n 849, +1.69c, PF 1.18.
- OICORE overlap (information only, not a claim): fixed threshold 100 of 849 low-half trades, inside PF 1.94 (+7.46c) vs outside PF 1.10; trailing 24 h p90: 28 of 849, inside PF 7.41. These are subsets of an already failed rule and are not a lead (they are the OICORE trigger, which is live).

Verdict (registered): FALSIFIED. D1 low PF 1.23 and D2 low PF 1.13 are under 1.5, and D2 low minus high is negative (the flow ordering does not hold in the second half; permutation p 0.49). The lead threshold (-0.036) was flagged as fitted in the registration; the cheap side being slightly positive after fee in both halves (PF 1.1 to 1.2) is the whole cheap-side pool in 5c to 50c asks, not flow information. No probe spec. N +2 charged (Bitcoin rule); the ETH and gold replications were not run, so their +4 is not spent.
