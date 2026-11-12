# WXDAYEND (card 74): confirmation of the registration, the kill rule and the finish-the-count plan (Testing Desk, Nov 12, 2026)

Written and committed BEFORE any answer of the job below exists. No Kalshi request was made to write it. No live account figure.

**Counts (registered, pulled, scored, closed, waiting):** 1 registered, 20 of 40 city-days read, 0 of 20 scored under the rule, 0 closed, waiting on: Main to dispatch `WXDAYEND_A` (22 requests), then `WXDAYEND_B` (up to 4).

## The registration (not mine; unchanged)

Source: `kalshi-scalper/refine_tools/CARDS_74_84_REGISTRATION_AND_RESULT.md` on `claude/refine-live` (card 74, Nov 11), read in full. Its facts: the daily high markets close one hour after the standard-time climate day ends only for events dated 2026-11-01 onward, so the sample is 10 events x 4 cities (NYC, LAX, DEN, DAL) = 40 city-days; edge-bracket framing, no favourite-late cell (no buy at 88c or above within 6 hours of the close).

**Kill rule, verbatim in substance:** FAIL if fewer than 3 of the 40 city-days show a YES ask at or under 0.96 on the winning bracket after the climate day ends.

**State:** Refinement pulled 20 (NYC 1 to 9, LAX 1 to 9, Denver 2). On all 20 the YES ask closed at 1.00 on every one minute candle of the final two hours (0 of 20 under 0.97). Its own errata (Nov 11) corrected "0 of 40" to "0 of 20". Dallas 0 pulled. The verdict "FAIL" therefore rests on half the registered sample; by the letter, the other 20 could still hold 3. Honest label until the count is finished: "FAIL on the half that was pulled, 20 city-days outstanding".

## What this desk added, fixed before any answer is read (all in `kalshi-scalper/workers/testing/`)

1. **Basis.** day_end = market close_time minus 3600 s. A city-day "shows" a price if any 1 minute candle with end_period_ts after day_end has yes_ask CLOSE at or under 0.96 (the field Refinement read). Reported beside it, not used for the verdict: the same test on yes_ask LOW, the number of post-day candles with no ask, and whether the two bases disagree (if they do, the Head decides; no choosing after the fact). No candle or no ask after day_end means "does not show".
2. **Unit.** one city-day = one event; the winning bracket is the one settled market with result yes (exactly one; zero or two is flagged unresolved and stays unread, never guessed).
3. **Replacement.** the 18 NYC and LAX city-days Refinement read stay as read (0 showing). Its 2 Denver reads are repeated by this pull and the new reads replace them (Refinement did not record which two).
4. **No new try.** This finishes the registered count only. No new rule, band, window or threshold, and no price test. Tries added to the ledger: 0 (the ledger row 108 stays "WXDAYEND, no new test").
5. **Labels.** The result is an existence count. Any profit statement is "no evidence at n = 40 city-days". If 3 or more show, the kill rule is not hit and the card goes back to the Head: buying a decided bracket in the 88c to 97c band is a favourite-shaped buy and needs the owner's 7e ruling before it is even measured (Desk A's flag, agreed). The book-replay line is "not available" (no order book exists for these brackets; candle asks only); a showing city-day would still need a book or haircut line before it is read as tradable.
6. **Family status.** Weather "forecast against market" is closed (3 FALSIFIED). WXDAYEND is the decided-fact mechanism with one FALSIFIED (WXDEAD1) and finishes its registered count and nothing more (Head's ruling in RND_QUEUE.md).

## Files

- `wxdayend.py`: `build-a` (turns Desk A's draft job into a runner-format job), `build-b <A run dir>` (reads A's four Nov 10 event lists, picks the single yes market of each, writes B), `score <A run dir> [<B run dir>]` (prints the count, the verdict, the label and the book-replay line). Reads files only; sends nothing.
- `wxdayend_desk_a_job.json`: Desk A's draft, copied unchanged from `claude/idea-desk-a` (`desk_a_jobs/DESKA_WXDAYEND_A.json`) as the source.
- `test_wxdayend.py`: made-up data (no Kalshi): winner finding, two-yes refusal, the day_end edge (a candle ending exactly at day_end does not count, 0.96 counts, 0.97 does not), the close versus low basis, FAIL at 2 of 40, kill rule not hit at 3 of 40, incomplete when any city-day is unread.
- `../kalshi_pull_jobs/WXDAYEND_A.json`: the runner-format job. Passes `python3 -I scripts/kalshi_pull.py WXDAYEND_A --dry-run` (22 requests, cap 22, 1 a second). Owner field is `MAIN` because the runner's `OWNERS` set has no Testing Desk entry; the runner is not changed here. Job file diffs are security-relevant (they name the exact URLs): Main's security look.

## Open points for Main

- Desk A's draft used a private format (`ep`, `series`); it would be refused by the runner ("bad job id"). The runner-format version is the one to dispatch.
- It uses the batched candles endpoint with one ticker. That endpoint is seen to answer for other series but not yet for these weather brackets. If the first two answers are empty or 404, stop and tell me; do not retry around it.
- Run order: A, then tell me; I run `build-b` on A's folder and commit `WXDAYEND_B.json` (4 requests) for Main to dispatch, then score within the hour.
- Score each pull within the hour it finishes: `python3 kalshi-scalper/workers/testing/wxdayend.py score <A folder> [<B folder>]`.
