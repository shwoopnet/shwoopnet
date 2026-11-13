HISTORY (Nov 13, 2026, owner ruling): this note predates the privacy scrub; lines marked "[live figure removed, ask Main]" are blank on purpose. Read it as history, not as a current rule.

# Plan: [live figure removed, ask Main]

Builds on `REFINE_TIMING_NOTES.md`. No code changed. Line numbers are from `functions/kalshiLiveLib.js` and `functions/index.js` on this branch; `origin/main` has them about 6 lines later in `runL1Tick` since #672 added the send timing. The main session's pull request must re-find them.

## What the new fields mean (PR #672 and #675)

On `origin/main` the order record gets `tickStartMs` (the function start, the same as `ts`), `sentAtMs` (just before the order POST), `answeredAtMs` (just after Kalshi answers). The report derives `startLateMs` (how many ms after the clock minute the function started), `startToSendMs` (`sentAtMs - tickStartMs`: the preamble plus any wait behind an earlier market) and `answerMs` (`answeredAtMs - sentAtMs`: Kalshi's answer time). With these three the delay splits into: scheduler start lag, our own work before the POST, and Kalshi's answer time. One piece is still missing: **how long a candidate waited behind another candidate** (gold ahead of Dogecoin). A logging-only field `candidateStartMs` (the time the loop reached this candidate, set just before its `GET /markets/{ticker}`) would split `startToSendMs` into preamble versus waiting. I propose adding that to the next logging change; it is not required to start.

## Ranked options

### 1. Keep the function warm (option b). Rank 1: no change to any order rule

- **Change:** `functions/index.js` line 586, the `onSchedule` options of `kalshiLiveArmed` (`{ schedule: "every 1 minutes", secrets: [...], timeoutSeconds: 55, retryCount: 0, memory: "256MiB" }`): add `minInstances: 1`. Nothing in `runL1Tick`, `index.js` bodies or any store changes. Deployed with `deploy-sizing.sh`.
- **Could break:** no order logic. It costs money (an always-on instance; [live figure removed, ask Main] [live figure removed, ask Main]
- **Gates that prove no order changes:** none needed beyond the existing suite (a config flag); `SI0` replays the exported function with recorded calls and is unaffected. Add one tiny gate that the schedule line still says `every 1 minutes` and `timeoutSeconds: 55`.
- [live figure removed, ask Main]
- [live figure removed, ask Main]

### 2. Read the independent parts in parallel (option c). Rank 2: touches the order path's timing, not its rules

- **Changes (smallest set):**
  - [live figure removed, ask Main]
  - [live figure removed, ask Main]
  - [live figure removed, ask Main] Everything after it keeps its order.
- **Could break, and how to keep it safe:**
  - **Fixtures.** `test/kalshiSlotWiringGates.test.js` (SW0) and `test/kalshiSlotIndexWiringGates.test.js` (SI0) replay RECORDED call logs and the header says a change to `offEquivalence.json` or `offEquivalenceIndex.json` means the off-equivalence broke. Parallel reads change the order of calls, so these gates would fail. They can only be re-recorded "from main's own code when the branch matches byte for byte" (CLAUDE.md), which parallel reads would not. [live figure removed, ask Main] That is a rule change for those gates, not a free edit.
  - **Fail closed.** Today an unreadable balance, order list or risk figure stops the tick before any order. `Promise.allSettled` must keep this: any rejected required read means no order; only the per-series market-list read keeps its current "skip that series" behaviour.
  - [live figure removed, ask Main]
- [live figure removed, ask Main] (iv) the two fixtures re-checked as a multiset.
- [live figure removed, ask Main]
- [live figure removed, ask Main]

### 3. Move the writes that do not need to come first to after the loop (option d). Rank 3: smallest saving

- [live figure removed, ask Main] Keep `updateTest` where it is (the order record must show the answer; the existing design ends the session when an answer is unresolved). Move only `setSession` and `log` to after the candidate loop, collected into a list and written in order.
- **Could break:** `setSession({ ordersSent })` feeds the next tick's counters; `ordersSent` is also held in a local variable (line 958), so within the tick nothing reads the session value. If the function dies mid-loop, the session shows a stale count and the log misses a line: both are display only. [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main]

### 4. Not recommended: send gold and Dogecoin together (option e)

[live figure removed, ask Main] It would need a combined pre-check first. [live figure removed, ask Main]

## Order to do things

1. Now: nothing risky. [live figure removed, ask Main] Meanwhile add the logging-only `candidateStartMs` if the main session wants the preamble versus waiting split.
2. If the startLateMs trigger is met: option 1 (minInstances).
3. If the startToSendMs trigger is met and startLateMs is not: option 2 with the multiset gate.
4. [live figure removed, ask Main]
5. [live figure removed, ask Main] The lead (z about 3.0, post-hoc) may have been a correlate of something else.

## Honest total

[live figure removed, ask Main] [live figure removed, ask Main] It buys frequency, not much dollars.
