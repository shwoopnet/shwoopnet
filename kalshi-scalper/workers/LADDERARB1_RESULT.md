# LADDERARB1 result (2026-11-03): NOT_RUNNABLE (census fails the 150-trade floor; no outcome joined)

Registration `workers/LADDERARB1_REGISTRATION.md` (sha256 `b0366771fce49707a3924eb053d3be47498ee5cf6b7c5e30921bcb1e1b5da482`), code `src/scalper/ladderarb1.py`, tests `tests/test_ladderarb1.py`. The census ran after the thresholds were fixed and read only quotes, never a result column. Frozen last third never loaded. No fetch.

**Census (events with at least 5 quoted strikes, before 2026-10-03T16:00Z; treated trades = kink or arb triggers, max 2 per event; looks 60 / 20 minutes):**
- KXINXU daily (inx1): 29 events, 0 / 0 triggers. KXNASDAQ100U daily (inx1): 29 events, 3 / 1 triggers. (KXINXU in `ladders.sqlite`, 140 events, and KXETHD, 86 events: no candles near either look.)
- KXBTCD hourly (NEWH4 duplicate, listed for scale): 20 minute look only (candles are not stored at 60 minutes), 736 + 170 events, 5 + 2 triggers. Gold hourly: no candles at either look. Gas and other newlist1 ladders: 5 of 1,028 events had 5 quoted strikes. Weather brackets are not "above K" ladders.
- KXINX (xladder1) are range brackets, not monotone, excluded (their 64 flagged strikes are not a ladder kink).
- Total treated trades in the whole sample, new families only: about 4. Rate about 0.07 per event-look, so even at two index ladders a day it is about 0.14 trades a day: 150 trades takes roughly 1,000 days.

**Verdict: NOT_RUNNABLE** (about 4 against 150). The kink on Bitcoin and gold is NEWH4 (FALSIFIED), arbitrage locks are ARB1 to ARB5 and the others (0 locks). Win rate vs price paid, PF vs control: not computed (no outcome joined, by design).

**Forward plan.** Nothing worth recording: the index ladders almost never kink beyond 3x on the cheap side, so a recorder would need years. If one is wanted anyway, the book recorder (`record_book.py`) would need KXINXU added; I do not recommend it. Keep the trigger code for a second look only if Kalshi lists a thinner-quoted ladder family (rates, temperature "above" markets) with at least 20 events a month.

N +4 (2 rules x +2). Running count about 730,297 (coordinator keeps the total; z bar 5.27).
