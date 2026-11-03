# COUNT1B result (run once 2026-11-03; measurement only, no price or trading outcome read; periods from 2026-10-20 untouched)

Registration `workers/COUNT1B_REGISTRATION.md` sha256 `ac644c6d7e0c2c64a2b8397fb0470c992d2814fae8ee79a363f95806788ec496` (pushed in commit a2742b3 before any match). Code `src/scalper/count1b.py`.

Events: 55 settled periods starting before 2026-10-20 (36 weekly, 19 daily; 4 have an open-ended winning bracket). Registered split pooled and sorted by period start: SELECTION 27 (all weekly), CONFIRMATION 28 (9 weekly, 19 daily). Note the split put every daily event in the confirmation half; that is the registered rule and was not changed.

| Def | Selection exact-bracket rate | Confirmation | Confirmation weekly / daily |
|---|---|---|---|
| D1 all posts, ET | 17/27 = 63.0% | 28/28 = 100% | 9/9, 19/19 |
| D2 no media-only | 2/27 = 7.4% | 6/28 | 0/9, 6/19 |
| D3 no ReTruths | 5/27 = 18.5% | 14/28 | 2/9, 12/19 |
| D4 no empty, no RT | 1/27 = 3.7% | 6/28 | 0/9, 6/19 |
| D5 no empty, no bare URL | 1/27 = 3.7% | 6/28 | 0/9, 6/19 |
| D6 no RT, no bare URL | 5/27 = 18.5% | 13/28 | 1/9, 12/19 |
| D7 all posts, UTC | 18/27 = 66.7% | 16/28 = 57.1% | 9/9, 7/19 |
| D8 D4 + UTC | 1/27 = 3.7% | 3/28 | 0/9, 3/19 |

**Chosen by the registered rule: D7 (highest selection rate), confirmation 57.1% (16/28), under 90%: NO_DEFINITION_MATCHES.** Best selection rate 66.7%.

## What the table says (read with care; none of this is a registered pass)
- Removing ReTruths or media-only posts makes the match much WORSE, so the archive already omits or under-counts what Roll Call counts; Roll Call counts MORE than the archive's non-reblog text posts, not fewer. The mismatch is not "the archive has extra posts".
- D1 (all posts, ET) matches all 19 daily periods and 26 of 36 weekly periods (72.2% weekly overall, same as COUNT1's 65% on 26 development events plus 9 more). UTC boundaries are wrong for the daily series, as the rules say ET. D7 only edged D1 on selection by one event (18 vs 17 of 27), which is the noise the 27-event half allows; the selection rule picked it, so the verdict stands as NO_DEFINITION_MATCHES.
- Because the split put all daily events in one half, the 100% daily result for D1 is a confirmation-half observation on a definition that did NOT win selection; it is a lead, not a pass. The unexplained part is the weekly series (10 of 36 mismatches under every candidate), which points at something none of the 8 definitions varies (replies captured by Roll Call, posts deleted after the weekly 10:00 AM ET record, or the weekly window end). Not tested here.

## Status of the COUNT1 blocker
SOURCE_MISMATCH is NOT cleared for the weekly series (best 72%); for the daily series the plain archive count (D1) matched 19 of 19, which needs a fresh, separately registered confirmation (a daily-only registration with D1 fixed, periods from 2026-11-04 onward) before it is used. No pace-model addendum is registered; N +0 for this worker.
