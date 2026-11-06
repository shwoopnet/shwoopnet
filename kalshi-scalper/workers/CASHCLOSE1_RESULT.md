# CASHCLOSE1 result (2026-11-06): NOT_ENOUGH_DATA (no data exists yet; nothing scored)

Registration: `workers/CASHCLOSE1_REGISTRATION.md` (commit 7240d44).

**Verdict: NOT_ENOUGH_DATA.** No `perps30/` file (close files) exists on origin/perp-data as of 2026-11-06 16:00 UTC (checked every commit of the branch; the 09:10 to 10:30 New York window had already ended, 11:10 EST). The hourly history cannot stand in: only 7 of 73 hourly samples fall in an open or close window, none gives a 10 minute or 20 minute return, and single-stock perps were inactive (bid 0) before 2026-11-03. No Yahoo bar was fetched and no outcome computed.

**When it becomes testable.** Read date 2026-12-01 (dev files 2026-11-06 to 2026-11-30; files from 2026-12-01 held out). Bar: 150 trades; about 10 to 12 qualifying perps give 150 trades at 13 to 15 close days, about 2026-12-01 to 2026-12-08. The recorder stops by itself after 2026-12-07 (21 trading days); a longer test needs a reviewed STOP_DATE edit.

N +1 as registered. Research only.
