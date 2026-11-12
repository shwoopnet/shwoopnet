# Why Dogecoin orders go out late in the minute, and what a fix would touch (read only; Oct 30, 2026, 8:15 PM CT)

Requested by the owner via the main session. I read `functions/index.js` (`kalshiLiveArmed`, line 585 on) and `functions/kalshiLiveLib.js` (`runL1Tick`, line 842 on). I changed nothing. A trading change is its own pull request from the main session after the owner approves.

## What I measured (R5 lead, not yet a finding)

[live figure removed, ask Main]

[live figure removed, ask Main] The split was chosen after I looked, so it is a lead; [live figure removed, ask Main]

## What happens in one minute (in order)

1. Cloud Scheduler fires the function once a minute. Start time varies by seconds (scheduler jitter and, on a cold instance, startup). `now` is taken after one Firestore read (the arm document).
2. Session document read. [live figure removed, ask Main] Each is a network call, one after the next.
3. [live figure removed, ask Main]
4. Candidates are tried one at a time in list order: gold first, then Dogecoin (paused markets are skipped). For EACH candidate: a fresh `GET /markets/{ticker}` (this is the price the order uses), the band check, the window cap arithmetic, a second halted check, the Firestore write that creates the order record (`createTest`), then the order POST to Kalshi, then three more writes (`updateTest`, `setSession`, the event log).
5. So when gold and Dogecoin are both in the entry window in the same minute, Dogecoin's market read does not start until gold's whole cycle has finished: gold's read, record write, POST, and three writes.

Two separate delays follow from this:
- [live figure removed, ask Main] Every market pays this.
- [live figure removed, ask Main]

[live figure removed, ask Main] That is the first thing to find out.

## What a fix could change (options, smallest first)

1. **Log only, zero trading risk:** record the time each order is sent (`sentAt`) and the time its market read finished, on the order document. Then the report can show exactly where the seconds go. This reads no new data and decides nothing.
2. **Keep the function warm** (a minimum instance for `kalshiLiveArmed`). Removes cold start lag. [live figure removed, ask Main]
3. **Read the market lists in parallel** (`Promise.all`) in step 2 and the independent preamble reads in step 3. Does not change any rule, only when the first order can start. Saves seconds.
4. **Move the after-order writes** (`setSession`, the event log) to after all orders are sent. Gold's cycle then ends sooner and Dogecoin starts sooner.
5. **Send gold and Dogecoin together** (read both markets, then both orders at once). The biggest gain for Dogecoin and the one that touches the most rules (see below). Not recommended before 1 to 4 and R5.

## What each could break (the risks)

- **Order size lock and sizing:** `maxContractsFor` is checked per order and reads only code constants, so reordering reads does not change it. [live figure removed, ask Main] [live figure removed, ask Main]
- [live figure removed, ask Main] Sending both at once would let both pass the check on the same room: a possible breach of the cap by one extra order. [live figure removed, ask Main]
- [live figure removed, ask Main] A second instance of the function running at once (a slow start overlapping the next minute) is covered by the same transaction, but a slower tick makes overlap more likely, so option 2 helps there too.
- **Halted and direction lock:** both are re-read right before the order is recorded. Any reordering must keep that read between the market read and the POST.
- **Fail-closed behaviour:** an unreadable balance, orders list or risk figure stops the tick before any order. Parallel reads must keep that: if any one fails, nothing is sent.
- **The exit watch** is a different function and is not touched by any option.
- **Quote freshness vs speed:** a faster order is based on a fresher price, which is the point. But sending earlier in the minute is also earlier in the 6 minute window; the registered rule's "6 minute look" would shift by a few seconds. [live figure removed, ask Main]

## Recommendation

Do option 1 (log send time) now: zero risk, and it turns the lead into a measurement. Let R5 count to 100 per arm. If the late start is mostly scheduler start lag, option 2 is the fix. [live figure removed, ask Main] Do not do option 5 without a combined window-cap check, and only if the owner wants it. I propose none of this as a live change; it needs the main session's pull request and the owner's approval.

[live figure removed, ask Main]
