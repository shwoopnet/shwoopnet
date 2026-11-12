# QUOTE2B development read: pinned cutoff (Idea Desk A, Nov 12, 2026, committed BEFORE any score)

Scorer: V2's `src/scalper/quote2b.py` on `claude/epic-ptolemy-0amjd9`, unchanged, through `desk_a_quote2b/q2b_dev.py`. Its fill rule already includes the through-price clause (Q2B_REGISTRATION rule 4b), so no fill-rule change is needed.
- Cutoff: date constant `2026-11-07T15:00:00Z` (same as MMSIM1 Amendment 3). Development = hourly closes before it; later closes are dropped at load. The held-out is read ONCE on 2026-11-24 with MMSIM1, by the registered `run`, not this wrapper.
- No Kalshi calls: a strike-hour whose tape needs the API re-fetch (500+ rows in one recorded read) is excluded and counted; if more than 20% would be excluded the run says NOT_RUNNABLE and I report that instead.
- The minimum of 300 hours is lowered to 1 ONLY so the code prints its table. Development has well under 300 closes, so the verdict word printed is not a call. Reported as a diagnostic with n; no FAIL below about 100 trades.
- The wrapper writes to a scratch file, never to V2's read-once marker. No new try is added to the family count.
