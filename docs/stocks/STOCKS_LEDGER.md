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
