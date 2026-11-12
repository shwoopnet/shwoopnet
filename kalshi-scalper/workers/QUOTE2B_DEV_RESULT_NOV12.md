# QUOTE2B development read (Idea Desk A, Nov 12, 2026). Diagnostic, not the held-out read.

Pinned cutoff and wrapper committed before scoring (`QUOTE2B_DEV_AMENDMENT.md`). V2's scorer unchanged; closes before 2026-11-07T15:00Z only (171 loaded, 154 usable by coverage, 131 scored; 23 excluded because their tape needed the API re-fetch and no Kalshi calls were made, 15%, under the 20% NOT_RUNNABLE line). Held-out not opened; no read-once marker touched; no try added.

Result (1,341 pairs posted in 130 hours; buy side filled 1,045, sell side 1,079; 791 cycles completed, 542 stopped):
- C=1, registered verdict basis (maker fee = taker 7%): cash PF 0.00 in every third and both halves, net -61.7c per hour, total -$80.78, z -12.9.
- Same at maker 1.75%: PF 0.00, -45.5c per hour. Zero maker fee: PF 0.00, -29.2c per hour, total -$38.30. C=10 is the same shape (PF 0.00 on every fee row).
- Spread earned $8.08 against stop and flatten loss $36.22 (C=1). Markout of fills: -1.18c per contract at 30 s (z -19), -0.98c at 5 minutes.
The loss does not need the fee: at zero maker fee it still loses 29c an hour.

Reading: this is the through-price fill rule V2 already registered, and it agrees with the MMSIM1 Rule P finding from a different quoting rule (re-quote each minute, stop at 5c, flatten T-10). Two-sided quoting on this ladder loses in development on both. n is 131 hours, below the registered 300, so the printed word FALSIFIED is not the registered call; the held-out read on Nov 24 is. Caveat: the excluded 23 heavy-tape hours are busier hours, so the sample is skewed toward quiet ones.
