HISTORY (Nov 13, 2026, owner ruling): this note predates the privacy scrub; lines marked "[live figure removed, ask Main]" are blank on purpose. Read it as history, not as a current rule.

# Forward log packet: four log-only items for owner approval (backlog rows 32 to 35)

Date 2026-11-10. Nothing here changes an order, a size, a limit or an exit. Each item only records numbers the bot already holds, or one public read, AFTER the orders of that minute are sent. Research writes the spec and tests; the owner approves; a separate reviewed pull request builds it. Nothing was edited to write this.

[live figure removed, ask Main] These logs make the same questions readable from live fills.

## Ranking (value per cost, best first)

1. [live figure removed, ask Main] Unblocks the most rows for one public read per order.
2. [live figure removed, ask Main]
3. [live figure removed, ask Main]
4. [live figure removed, ask Main] Highest value for rows 22 and 24 but touches safety code and the 10 second loop, so highest review cost.

## Row 32: decision-time book snapshot

- [live figure removed, ask Main]
- [live figure removed, ask Main] Null for any missing piece, never a guess.
- [live figure removed, ask Main] Add a sibling `logBook` in the same loop: one extra public order book GET per ORDER (not per market) through `liveRequest`. Kalshi's market object carries only the top level, which is why `depthAtLimit` (DD1) is not a sum over levels. OICORE orders go through kalshiSlotRunLib.js, so the spec must say which writer owns the call.
- [live figure removed, ask Main]
- [live figure removed, ask Main] Drop rule: drop the log if it adds a read per tick or anything waits for it.
- [live figure removed, ask Main] Deploy: `bash functions/deploy-sizing.sh`.

## Row 34: qualified-but-no-order shadow rows

- [live figure removed, ask Main]
- [live figure removed, ask Main] The result is joined later from the public market result, not stored.
- [live figure removed, ask Main] Collect rows in an array like `riseLog`, write after the orders are sent. Use a NEW collection, not `kalshiLiveOrders`, because the page, loss stop and nightly report read orders and must never count a non-order (the reason slot orders have their own collection). It needs an admin-read, no-client-write rule in firestore.rules, so also `firebase deploy --only firestore:rules`. kalshiShadowLib.js does not exist in this repo; the nearest patterns are the `exitShadow` field and `kalshiLiveControl/probeRecord`.
- Cost: 0 reads, 0 new API calls; about 60 writes a day (about 1,800 a month, well under $0.01). Add a 30 day prune to an existing prune job so it cannot grow without bound.
- Cannot change an order: rows are built from values already computed, written after sending, errors swallowed; no trading code reads the collection.
- [live figure removed, ask Main] Deploy: `bash functions/deploy-sizing.sh` plus rules.

## Row 35: spot reference on orders

- [live figure removed, ask Main]
- Fields: `spotSymbol`, `spotMid`, `spotAgeS`, `spot60sRet`, `spotReadAt`; null on any failure. Stop the log if missing data stays above 20 percent.
- Where: beside `logRise`, same `riseLog` loop. One keyless public GET (Coinbase PAXG-USD for gold, BTC-USD for OICORE, XRP-USD for XRP) through `fetchFn` with a 5 second timeout, not `liveRequest` (which signs for Kalshi). It adds an outside host to functions, so the security scan's allowed list and the host gate must be updated on purpose: flag for the owner.
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- Gates: `SP1` (fields from a fixture response), `SP2` (timeout, 429, bad JSON write nothing), `SP3` (host fixed in code, no key, nothing stored picks it, security scan still passes). Deploy: `bash functions/deploy-sizing.sh`.

## Row 33: exit watch bid-read log

- Unblocks: rows 22 and 24 (debounce, grind versus gap) and 23 need the 10 second path through the 25c touch; [live figure removed, ask Main]
- [live figure removed, ask Main] The market object gives only the best bid and its size; `bid2` needs the book endpoint, so the spec must choose: bid and size only (0 extra reads) or one book read only at or below 40c (a few per touch).
- Where: `runExitWatch` in functions/kalshiLiveLib.js, the loop that reads the market and computes `ourBid` (about lines 1170 to 1185) and now `continue`s when the bid is above the 25c threshold. Buffer in memory, flush once per pass AFTER sells, so the IOC sell path and the `claimClose` lease are untouched; kalshiExitAlarmLib.js's heartbeat must not wait on it.
- [live figure removed, ask Main]
- Cannot change a sale: this is safety code, so the strictest gate. [live figure removed, ask Main]
- [live figure removed, ask Main] Deploy: `bash functions/deploy-push.sh`.

## Shared notes

- [live figure removed, ask Main]
- Deploys: 32, 34, 35 need `deploy-sizing.sh` (34 also the rules); 33 needs `deploy-push.sh`. No heartbeat change, so the exit alarm deploy order in CLAUDE.md is unaffected.
- None touches `FIXED_CONTRACTS`, `PAUSED_SERIES`, the caps, the 12% stop, the 25c line or any list. The SW0 and SI0 fixtures change only by added writes; re-record only under the CLAUDE.md rule (from main's code, byte match).
- [live figure removed, ask Main]
- Decision requested: approve each of the four, or a subset, as log-only pull requests with the gate names above.
