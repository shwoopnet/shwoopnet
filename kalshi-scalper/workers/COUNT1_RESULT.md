# COUNT1 result (run once, 2026-11-03, development only; frozen thirds untouched)

Registration `workers/COUNT1_REGISTRATION.md` sha256 `1000a968e26a59a384ef3e21dbbd8b8a3d0a73ed4316ec3c6fb0b825354bbfc4` plus Amendment 1 and Amendment 2 (pushed before scoring, commit 4260b6d). Code `src/scalper/count1.py` (one bug fixed before the successful run: the first run crashed on a tuple unpack before writing any result), tests `tests/test_count1.py`.

## Weekly (KXTRUTHSOCIAL, rule COUNT1-W): 26 development events, 238 markets, 13 events frozen unread
- Trades **n = 11** (take-up 0.42 per period; 69 markets had no valid quote). Wins 3 of 11 (27%) against a mean fill price of 11.5c (the model's mean p was 44%: overconfident). Mean net **+15.1c** per contract after fees, **PF 2.53**; halves +35.4c (n 4, PF 4.8) and +3.5c (n 7, PF 1.34). The profit is three winners (bracket hits at 9c, 11c, 4c prices paying 90c to 96c net) against eight small losses, so it is noise-sized: one fewer winner flips the sign.
- Control (every bracket with ask 3c to 30c): n 122, win 17.2%, mean +2.1c, PF 1.17. Rule minus control +13.0c on 11 trades (not distinguishable from zero).
- **Source check: 65.4% (17 of 26) of periods have the archive total inside the winning bracket, under the registered 70%: SOURCE_MISMATCH.** The CNN archive does not reproduce Roll Call's count closely enough (replies and counting rules), so the model's count so far is biased in some weeks.
- Verdict: **NOT_ENOUGH_DATA** (11 trades, under 150; also SOURCE_MISMATCH). No claim of an edge.

## Daily (KXTRUTHSOCIALD, rule COUNT1-D): smoke test only
Only the earliest development events had all markets fetched (rate limit), Amendment 2: 6 events scored, **0 trades**, source check 6 of 6 inside the winning bracket (n too small). 16 development events not scored; the fetch continues for the forward record. Verdict: **NOT_ENOUGH_DATA** (no trades).

## Forward plan (frozen, dated)
Rule exactly as registered; daily periods from 2026-11-04, weekly from the week starting 2026-11-08; tracker `ix.cnn.io/data/truth-social/truth_archive.json`; quotes read from candles after each period. Expected trades per month at the weekly take-up of 0.42 per period: 4.3 weeks x 0.42 = **about 1.8 a month, so 40 trades is about 22 months**; the daily cell's take-up is unmeasured (0 of 6 events), at a plausible 0.1 to 0.4 per day it would be 3 to 12 a month, 40 trades in 3 to 13 months. Before any forward read the source gap must be fixed (count Roll Call's rule more closely, e.g. test whether replies explain the 35% mismatch) which would be a new registration.

## Probe spec
Not triggered (not positive in both halves with a mechanism at n worth reading; the second half is +3.5c on 7 trades). If it ever qualified: 1 contract, ask 3c to 30c, at most 2 brackets per period, worst loss 60c per period, kill after 20 fills with net under -$3 or 40 fills with PF under 1.0.

## Not run
KXEOWEEK (publication lag), KXELONTWEETS (dormant, no overlap), KXPOTUSTWEETS (forward only, 5 overlapping events). N +4.

## COUNT1B update (2026-11-03, added after the numbers above, which are not edited)
The definition reconciliation (`workers/COUNT1B_RESULT.md`) ran 8 counting definitions on 55 settled periods before 2026-10-20: NO_DEFINITION_MATCHES (selected D7, confirmation 57.1%, bar 90%). Weekly SOURCE_MISMATCH stays (best 72% weekly under any definition). Daily: the plain archive count matched 19 of 19, a lead that needs its own daily-only registration from 2026-11-04 before the daily pace rule can be read. The forward freeze above is unchanged.
