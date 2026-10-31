# Plan: sending Dogecoin orders earlier in the minute (ranked, read only; Oct 30, 2026, 9:55 PM CT)

Builds on `REFINE_TIMING_NOTES.md`. No code changed. Line numbers are from `functions/kalshiLiveLib.js` and `functions/index.js` on this branch; `origin/main` has them about 6 lines later in `runL1Tick` since #672 added the send timing. The main session's pull request must re-find them.

## What the new fields mean (PR #672 and #675)

On `origin/main` the order record gets `tickStartMs` (the function start, the same as `ts`), `sentAtMs` (just before the order POST), `answeredAtMs` (just after Kalshi answers). The report derives `startLateMs` (how many ms after the clock minute the function started), `startToSendMs` (`sentAtMs - tickStartMs`: the preamble plus any wait behind an earlier market) and `answerMs` (`answeredAtMs - sentAtMs`: Kalshi's answer time). With these three the delay splits into: scheduler start lag, our own work before the POST, and Kalshi's answer time. One piece is still missing: **how long a candidate waited behind another candidate** (gold ahead of Dogecoin). A logging-only field `candidateStartMs` (the time the loop reached this candidate, set just before its `GET /markets/{ticker}`) would split `startToSendMs` into preamble versus waiting. I propose adding that to the next logging change; it is not required to start.

## Ranked options

### 1. Keep the function warm (option b). Rank 1: no change to any order rule

- **Change:** `functions/index.js` line 586, the `onSchedule` options of `kalshiLiveArmed` (`{ schedule: "every 1 minutes", secrets: [...], timeoutSeconds: 55, retryCount: 0, memory: "256MiB" }`): add `minInstances: 1`. Nothing in `runL1Tick`, `index.js` bodies or any store changes. Deployed with `deploy-sizing.sh`.
- **Could break:** no order logic. It costs money (an always-on instance; I could not price it here, check the Firebase price page, likely a few dollars a month for 256 MiB). One effect to watch: a warm instance keeps the in-memory order reader (`makeRecentOrderReader`, which keeps orders older than 30 minutes in memory and refreshes every 15 minutes), so reads in a warm instance are fewer; staleness errs toward fewer orders, as the existing notes say. Two instances running together during a deploy are covered by the `L1-<ticker>` create-or-fail record.
- **Gates that prove no order changes:** none needed beyond the existing suite (a config flag); `SI0` replays the exported function with recorded calls and is unaffected. Add one tiny gate that the schedule line still says `every 1 minutes` and `timeoutSeconds: 55`.
- **Numeric trigger (build only if true), from the report after the timing fields have 100 Dogecoin orders:** at least 25% of those orders have `startLateMs` of 5,000 ms or more (the bot starts late often enough to matter) AND the no-fill share of the 5,000 ms or later arm is at least 10 points above the earlier arm (R5's own bar). If startLateMs is under 5,000 on more than 85% of orders, skip: the lateness is not scheduler start.
- **Fills gained (honest range):** the late arm is about 41% of Dogecoin attempts (about 40 a week) with a 43% no-fill share against 21%. If warm starts moved most of them to the early arm: +9 fills a week at best (22 points on 40 attempts), +5 if only part of the gap is the start (13 points), +0 if the split is not causal (the split was chosen after looking; z about 3.0, 177 orders). **Central 5, range 0 to 9 a week.**

### 2. Read the independent parts in parallel (option c). Rank 2: touches the order path's timing, not its rules

- **Changes (smallest set):**
  - `functions/index.js` lines 616 to 621: the loop that reads each remaining L1 series' market list one at a time (`for (const series of live.L1_SERIES.filter(...)) { try { for (const m of await kalshiMarketApi().markets(series)) ... } catch ... }`) becomes one `Promise.allSettled` over those series, each keeping its own error swallow. Result order into `market.quotes` must be the same as today (L1_SERIES order), because candidates are sorted by `L1_SERIES.indexOf` anyway (kalshiLiveLib line 947) but `quotes` order feeds `silent market` and other readers.
  - `functions/kalshiLiveLib.js` `loadQuotes` (line 46): the `for (const series of bot.SERIES)` read becomes parallel the same way.
  - `runL1Tick` preamble: the balance GET (line 876) does not depend on the 24 hour order read or `botRisk`; start it before line 863 and await it where it is used today (line 877). Everything after it keeps its order.
- **Could break, and how to keep it safe:**
  - **Fixtures.** `test/kalshiSlotWiringGates.test.js` (SW0) and `test/kalshiSlotIndexWiringGates.test.js` (SI0) replay RECORDED call logs and the header says a change to `offEquivalence.json` or `offEquivalenceIndex.json` means the off-equivalence broke. Parallel reads change the order of calls, so these gates would fail. They can only be re-recorded "from main's own code when the branch matches byte for byte" (CLAUDE.md), which parallel reads would not. So option 2 needs a NEW, owner-approved gate that compares the SET of calls (same requests, same bodies, order ignored for reads) and leaves every order and write in the same order. That is a rule change for those gates, not a free edit.
  - **Fail closed.** Today an unreadable balance, order list or risk figure stops the tick before any order. `Promise.allSettled` must keep this: any rejected required read means no order; only the per-series market-list read keeps its current "skip that series" behaviour.
  - **Size lock, window cap, double-order guard, halted and direction re-reads** are all in the per-candidate part (lines 964 to 1092) and are not touched.
- **Gates that prove no order changes:** (i) a new PAR1: same inputs, same orders out (ticker, side, count, limit, client id, record fields except timing); (ii) PAR2: one failed market-list read removes only that series, a failed balance read sends nothing; (iii) the existing SZ1 to SZ6, W1 to W5, OC1, GF, FS, OS tests and `test/kalshiL1Gates.test.js` unchanged and passing; (iv) the two fixtures re-checked as a multiset.
- **Numeric trigger:** the median `startToSendMs` for Dogecoin over 100 post-deploy orders is 6,000 ms or more while `startLateMs` is under 5,000 ms (so the time is spent inside the function, not before it), AND the median of (`startToSendMs` of the Dogecoin order minus `startToSendMs` of the gold order in the same minute) is under 1,500 ms (so waiting behind gold is not the main part; if it is, go to option 3).
- **Fills gained:** the saving is seconds, say 1 to 3 s of a 5 to 15 s late group. If no-fill share falls in proportion, **+1 to +4 a week; central +2**.

### 3. Move the writes that do not need to come first to after the loop (option d). Rank 3: smallest saving

- **Change:** `runL1Tick` lines 1068 to 1076, after a successful order POST there are three writes in a row: `store.updateTest` (the fill result), `setSession({ ordersSent })`, and the event `log`. Keep `updateTest` where it is (the order record must show the answer; the existing design ends the session when an answer is unresolved). Move only `setSession` and `log` to after the candidate loop, collected into a list and written in order.
- **Could break:** `setSession({ ordersSent })` feeds the next tick's counters; `ordersSent` is also held in a local variable (line 958), so within the tick nothing reads the session value. If the function dies mid-loop, the session shows a stale count and the log misses a line: both are display only. The 200 order limit reads the orders collection, not this counter (line 874), so it is unaffected. Keep the `ordersSent += 1` local update in place.
- **Gates:** the existing order record assertions stay; a new gate that the log and session writes still happen exactly once per order and after all POSTs; plus the fixtures (SW0 and SI0 record the writes, so these two would also need the multiset treatment or a re-record, same rule as option 2).
- **Numeric trigger:** over the minutes where gold and Dogecoin both ordered, the median of (Dogecoin `startToSendMs` minus gold `startToSendMs`) is 1,500 ms or more.
- **Fills gained:** two Firestore writes of roughly 50 to 300 ms each; **+0 to +2 a week, central +1**.

### 4. Not recommended: send gold and Dogecoin together (option e)

The window cap (`windowSpent`, lines 963 and 1002 to 1006) and the cash accounting (`committed`, lines 961 and 983) are updated order by order, so a simultaneous send would let both orders pass the same room check. It would need a combined pre-check first. Gold and Dogecoin are no longer in the same crypto-one-per-window group (Dogecoin left `CAPPED_SERIES`, line 996), so nothing else stops two in one window. I would only consider it after options 1 to 3 and R5 have read, with a combined-check gate (PAR3: two candidates in the same window cannot together exceed `L1_WINDOW_CAP_FRACTION` of the base).

## Order to do things

1. Now: nothing risky. Wait for the timing fields to reach about 100 Dogecoin orders (about 1.5 to 2 weeks at 40 to 70 a week). Meanwhile add the logging-only `candidateStartMs` if the main session wants the preamble versus waiting split.
2. If the startLateMs trigger is met: option 1 (minInstances).
3. If the startToSendMs trigger is met and startLateMs is not: option 2 with the multiset gate.
4. If the gold-ahead trigger is met: option 3.
5. If none of the triggers is met after 100 orders: drop the idea. The lead (z about 3.0, post-hoc) may have been a correlate of something else.

## Honest total

All three options together: **+3 to +10 Dogecoin fills a week, central +6**, against about 71 now (roughly +8%). The estimates come from a post-hoc split of 177 orders, and the gain only appears if the lateness is the cause and not just a marker of busy or slow minutes. At a cent or two of profit per contract and 13 contracts, +6 fills a week is about +$1 to $2 a week in expectation. It buys frequency, not much dollars.
