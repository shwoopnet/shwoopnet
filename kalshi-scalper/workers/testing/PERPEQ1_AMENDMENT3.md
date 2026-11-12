# PERPEQ1 amendment 3 (Testing Desk, owner of the read since Nov 12, 2026; dated Nov 12, 2026; before any PERPEQ1 outcome exists)

**This amendment corrects a stale line. It moves no cutoff and changes no rule, bar or try.**

`workers/PERPEQ1_REGISTRATION.md` on `claude/epic-ptolemy-0amjd9` still carries the line "READ-ONCE MARKER: not yet read; first read allowed on or after 2026-12-30" and "Development read date 2026-12-01; held out 2026-12-01 on". Those were overtaken by `PERPEQ_AMENDMENT1.md` and `PERPEQ_AMENDMENT2.md` (owner decision relayed by main, Nov 7). The registration in force is:

- Development: trading dates 2026-11-09 to **2026-12-21** inclusive (30 trading dates). First development read: **2026-12-22** after the close.
- Held out: **2026-12-22 to 2027-02-01** inclusive (27 trading dates), never loaded by the scorer, read once on or after **2027-02-02** and only after a LEAD on development.
- Corrected marker line: `READ-ONCE MARKER: not yet read; first development read allowed on or after 2026-12-22; held-out read allowed on or after 2027-02-02 only after a LEAD; after each read: READ ON <date>, commit <hash>`.

Rule, bars (100 trades, 30 trading-date clusters, PF 1.5 in each half, net above 0 in both halves, PF 1.2 at fee x1.2, trigger better than control, day-clustered z 5.27), cost assumption and its 2 tries (fade and control) are unchanged.

Added by the Head of R&D's ruling (Nov 12): the result is reported with "perp candle freshness assumed, not measured"; cash PF with n by cluster; under 100 trades the label is "no evidence at n = x"; the output goes to the Verification Analyst through Main before any figure travels. The scorer carries the cutoffs as date constants and refuses to run before 2026-12-22; it is written and tested on synthetic rows only, with no perp candle opened.

READ-ONCE MARKER: not yet read; first development read allowed on or after 2026-12-22; held-out read allowed on or after 2027-02-02 only after a LEAD; after each read: READ ON <date>, commit <hash>
