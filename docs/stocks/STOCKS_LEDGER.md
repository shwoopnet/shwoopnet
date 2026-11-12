# Stocks ledger (starts Nov 12, 2026; ids and counts only, no result figures)

Rule (Head of R&D ruling 5): every variant, cell or rule scored against outcomes counts as one try; measurements that score no rule count zero. This file holds counts and ids. No Databento-derived figure goes in it.

## Prior tries carried in (from CLAUDE.md; exact N for the old work was never written down, so this is a floor)
| Id | What | Tries | Status |
|---|---|---|---|
| P-EQ-ORB | Equities opening-range breakout, volume filter, trailing stop (computeORBAnalysis), read at 30/60/180/365 day windows on 16 symbols | at least 1 strategy, 4 window reads | WITHDRAWN Aug 2026 for lookahead (entry booked at rangeHigh); no figure quotable |
| P-EQ-FAILEXIT | Exit when the breakout fails | 1 | did not work |
| P-EQ-CONFBAR | Confirmation-bar delay | 1 | reported 13.26 on lookahead, 0.94 honest |
| P-CR-ORB | Crypto ORB-style trend strategy | at least 1 strategy, 3 window reads | PF 1.94 fell to 1.05 when priced honestly; 25bp excluded spread |
| P-CR-EXEC | Four crypto execution variants (market, maker, hybrid, hybrid with chase gate) | 4 | CLAUDE.md process note |
| P-ADV6 | Six strategy families the advisor board proposed | 6 proposed, not scored | testable, unrun |
| P-3ERR | Three backtest errors found in one weekend, all flattering | 3 | corrected |

Floor for prior tries: at least 8 scored strategy variants (1+1+1+1+4), window reads not counted separately.

## This desk, registered Nov 12, 2026 (none scored)
S1 1, S2 2, S3 2, S4 2, S5 2, S6 2, S7 1 (first wave, scripts and synthetic tests written), S8 2, S9 1, S10 1 (deferred). Total 16, scored 0.

## Retired unread, Nov 12, 2026 (Head of R&D ruling; tries scored 0, no data bought)
| Card | Reason |
|---|---|
| S1 overnight vs intraday, index ETFs | arithmetic: net d about 0.03 to 0.06, PF about 1.04 to 1.13, cannot clear 1.5 |
| S2 long-short line | never judged (borrow and dividend upper bound); net PF about 0.9. The S2 LONG LEG is NOT retired: HELD after the pilot (Head ruling Nov 12 ~17:11Z) |
| S3 one-week reversal, illiquid | screen only, cannot pass; spread (15 bp each way) consumes it |
| S4 opening gap fade | screen only, cannot pass |
| S5 post-gap drift | screen only, cannot pass |
| S7 first 30 predicts last 30 | net d about 0.04 to 0.05, PF about 1.05 to 1.1 |
Registered tries counted: still 16 registered, 0 scored. Left: S6, S8, S9 (blocked on price definition and the Head's ruling), S10 deferred.

| S6 leveraged-ETF rebalance | retired unread Nov 12 (Amendment 5): net PF about 1.0 to 1.15, about 300 events |
| S9 opening cross imbalance | retired unread Nov 12 (Amendment 5): PF about 1.0 to 1.2 |
Held: S2 long leg (after the pilot), S8 (after the cutoff ruling). Deferred: S10. Tries scored 0.
| S8 closing auction imbalance | retired unread Nov 12 (Amendment 6): registered entry not enterable on NYSE, broker access unknown, about $75 a year at $5,000 a trade |
Final for now: nine retired unread or deferred, one held (S2 long leg, behind the pilot). Tries scored 0.
