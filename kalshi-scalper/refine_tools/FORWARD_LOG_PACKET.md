# Forward log packet: four log-only items for owner approval (backlog rows 32 to 35)

Date 2026-11-10. Nothing here changes an order, a size, a limit or an exit. Each item only records numbers the bot already holds, or one public read, AFTER the orders of that minute are sent. Research writes the spec and tests; the owner approves; a separate reviewed pull request builds it. Nothing was edited to write this.

Why now: rows 14, 20, 22, 23 and 24 ended DATA LIMITED because history has no order book depth and the R6 book recorder stops by itself after 2026-11-13. These logs make the same questions readable from live fills.

## Ranking (value per cost, best first)

1. Row 32, book snapshot on orders. Unblocks the most rows for one public read per order.
2. Row 34, qualified-but-no-order rows. No reads, about 60 small writes a day, fixes selection bias in every live split.
3. Row 35, spot reference on orders. One public GET per order, no key; mainly serves S1 and rows 16, 23, 29.
4. Row 33, exit watch bid-read log. Highest value for rows 22 and 24 but touches safety code and the 10 second loop, so highest review cost.

## Row 32: decision-time book snapshot

- Unblocks: row 14 (thin-bid skip; n 40 per half, gold about 17 orders a week, so about 5 weeks per half); row 20 (OICORE book imbalance; n 40 per half, about 60 OICORE fills a week, so about 2 weeks; live has about 81 settled but only top-level `bidSize`/`askSize`); rows 22, 23, 24 as the depth input (they also need rows 33 and 35).
- Fields on the order document: `bookTop3` (YES bid and YES ask, best 3 levels each as price and size; NO is the mirror), `exitDepth25to15` (summed size of the bought side's bids from 25c down to 15c, null if thin or unread), `bookDepthLevels: 3`, `bookReadAt` (ms). Null for any missing piece, never a guess.
- Where: `logRise` in functions/kalshiLiveLib.js already runs after every order is sent (loop over `riseLog` in `runL1Tick`, about line 1093) and writes with `store.updateTest`. Add a sibling `logBook` in the same loop: one extra public order book GET per ORDER (not per market) through `liveRequest`. Kalshi's market object carries only the top level, which is why `depthAtLimit` (DD1) is not a sum over levels. OICORE orders go through kalshiSlotRunLib.js, so the spec must say which writer owns the call.
- Cost: 1 public API call per order (about 77 a week), 0 Firestore reads, 0 extra writes if merged into the logRise update (else 1 per order, under $0.01 a month).
- Cannot change an order: runs after all orders of the minute are sent, whole body in try/catch returning false (as logRise does), no value feeds `l1Count`, the band, the caps or the size lock. Drop rule: drop the log if it adds a read per tick or anything waits for it.
- Gates: `BK1` (fields from a fixture book match a hand sum), `BK2` (failed read, 429, thrown error write nothing and the order record is unchanged), `BK3` (source gate: no decision code reads the fields, like DD1 in test/kalshiL1Gates.test.js). Deploy: `bash functions/deploy-sizing.sh`.

## Row 34: qualified-but-no-order shadow rows

- Unblocks: the selection problem in every live split (W-NOORDER1: 9 trigger-with-no-fill windows and 8 no-order windows with unstored reasons); the denominator for rows 14 and 20; first use is whether windows skipped by a cap earn within 0.5c of taken ones, n 40 per reason (window cap and one-crypto rule reach n first; rarer reasons will not).
- Fields, one row per skipped decision: `series`, `ticker`, `strategy` (L1 or OICORE), `lookSec`, `side`, `ask`, `bid`, `reason` (windowCap, oneCrypto, sizeLock, directionLock, noCandle, quietHours, orderLimit, other), `ts`. The result is joined later from the public market result, not stored.
- Where: the points inside `runL1Tick` (functions/kalshiLiveLib.js) that already pick a side and then skip it: the size lock branch ("order size refused", about line 1014), the window cap, the one-crypto rule, `QUIET_HOURS_CT`, the direction lock. Collect rows in an array like `riseLog`, write after the orders are sent. Use a NEW collection, not `kalshiLiveOrders`, because the page, loss stop and nightly report read orders and must never count a non-order (the reason slot orders have their own collection). It needs an admin-read, no-client-write rule in firestore.rules, so also `firebase deploy --only firestore:rules`. kalshiShadowLib.js does not exist in this repo; the nearest patterns are the `exitShadow` field and `kalshiLiveControl/probeRecord`.
- Cost: 0 reads, 0 new API calls; about 60 writes a day (about 1,800 a month, well under $0.01). Add a 30 day prune to an existing prune job so it cannot grow without bound.
- Cannot change an order: rows are built from values already computed, written after sending, errors swallowed; no trading code reads the collection.
- Gates: `NO1` (each skip reason writes exactly one row and the orders sent are identical with and without the logger, replayed like the SW0 and SI0 fixtures), `NO2` (a failing write changes nothing), `NO3` (rules are admin read and no client write; the page does not read it). Deploy: `bash functions/deploy-sizing.sh` plus rules.

## Row 35: spot reference on orders

- Unblocks: row 3 (S1 passed its bar but only 876 of 1,679 favourites had PAXG data) as a live shadow with no coverage hole; row 23 (informed exit gate); rows 16 and 29 and W-SPOT1. Needs n 40 per half on gold, about 5 weeks; OICORE (BTC) and XRP stamps feed rows 16 and 29.
- Fields: `spotSymbol`, `spotMid`, `spotAgeS`, `spot60sRet`, `spotReadAt`; null on any failure. Stop the log if missing data stays above 20 percent.
- Where: beside `logRise`, same `riseLog` loop. One keyless public GET (Coinbase PAXG-USD for gold, BTC-USD for OICORE, XRP-USD for XRP) through `fetchFn` with a 5 second timeout, not `liveRequest` (which signs for Kalshi). It adds an outside host to functions, so the security scan's allowed list and the host gate must be updated on purpose: flag for the owner.
- Cost: 1 public GET per order, 0 Firestore reads, 0 extra writes if merged into the logRise update.
- Cannot change an order: after the send, try/catch, 5 second timeout, null on failure, no decision code reads it.
- Gates: `SP1` (fields from a fixture response), `SP2` (timeout, 429, bad JSON write nothing), `SP3` (host fixed in code, no key, nothing stored picks it, security scan still passes). Deploy: `bash functions/deploy-sizing.sh`.

## Row 33: exit watch bid-read log

- Unblocks: rows 22 and 24 (debounce, grind versus gap) and 23 need the 10 second path through the 25c touch; 60 second candles showed no gain and R6 held about 16 gold exits. n 40 touches is roughly 3 weeks of gold exits (OICORE is held, so mostly gold).
- Fields appended on the order document, capped at 40 per position: `exitReads: [{ at (ms), bid, bidSize, bid2 }]` whenever the bought side's bid is at or below 40c. The market object gives only the best bid and its size; `bid2` needs the book endpoint, so the spec must choose: bid and size only (0 extra reads) or one book read only at or below 40c (a few per touch).
- Where: `runExitWatch` in functions/kalshiLiveLib.js, the loop that reads the market and computes `ourBid` (about lines 1170 to 1185) and now `continue`s when the bid is above the 25c threshold. Buffer in memory, flush once per pass AFTER sells, so the IOC sell path and the `claimClose` lease are untouched; kalshiExitAlarmLib.js's heartbeat must not wait on it.
- Cost: 0 reads (or a few book reads per touch); about 3 to 6 writes per early sell, about 15 sells a week, under $0.01 a month. Drop rule from the backlog: more than about 4 writes per exit or any slowing of the 10 second loop.
- Cannot change a sale: this is safety code, so the strictest gate. The sale is sent first, the log is wrapped in try/catch and swallowed, it never writes fields the exit logic reads (`exitStatus`, `exitCount`, `exitShadow`), and the existing E1 to E13 and F6 to F8 in test/kalshiExitGates.test.js pass unchanged.
- Gates: `XL1` (reads appended only at or below 40c, capped at 40), `XL2` (a thrown log error leaves the same sale, client order id and results, replayed against a recorded call log), `XL3` (the log is never awaited before the sell). Deploy: `bash functions/deploy-push.sh`.

## Shared notes

- Suggested build order: 32 and 35 together (one extra call each, one write), then 34, then 33 last.
- Deploys: 32, 34, 35 need `deploy-sizing.sh` (34 also the rules); 33 needs `deploy-push.sh`. No heartbeat change, so the exit alarm deploy order in CLAUDE.md is unaffected.
- None touches `FIXED_CONTRACTS`, `PAUSED_SERIES`, the caps, the 12% stop, the 25c line or any list. The SW0 and SI0 fixtures change only by added writes; re-record only under the CLAUDE.md rule (from main's code, byte match).
- Firestore reads for research (0.06 dollars per 100K) are negligible: reading all four logs weekly is well under one cent.
- Decision requested: approve each of the four, or a subset, as log-only pull requests with the gate names above.
