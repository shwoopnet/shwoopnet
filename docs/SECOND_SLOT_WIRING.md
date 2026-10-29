# The second slot: wiring plan (Phase B)

Written Oct 29, 2026 for the owner. Status: **B1, B2 and B3 are built and tested (Oct 29, 2026), switched off, nothing committed or deployed by the session that built them.** Originally written as a plan. It turns the inert Phase A module (`functions/kalshiSlotLib.js`, `docs/SECOND_SLOT_DESIGN.md`) into a wired but still switched-off feature. Nothing here is built, deployed or turned on by this document.

Line numbers below are for `functions/kalshiLiveLib.js` and `functions/index.js` as they stand on `main` today (Oct 29, 2026). They will drift; the anchor text next to each one is what to search for.

## 0. The rule everything else serves: off-equivalence

While `SLOT_ENABLED` is `false` or `SLOT_STRATEGIES` is empty (how this phase ships), every deployed function must make the same reads, writes and orders, in the same order, as today. No new Firestore read, write or lock document, no new network call, no new secret, no new scheduled function.

**One gate.** `slotActive = SLOT_ENABLED === true && SLOT_STRATEGIES.length > 0`, worked out from the module's own constants. Nothing stored in Firestore, nothing in a request and nothing on the page can feed it.

- `kalshiSlotLib.js` exports `slotActive()` (a pure function of its two constants; no clock, no store, so the Phase A "no clock or store code" gate still passes).
- `index.js` computes `const SLOT_ON = slotLib.slotWatch()` once at load (the wider "watching" gate, see Review round 2), and builds the slot store, the slot hooks and every slot read **only inside `if (SLOT_ON)`**. With it false, the objects passed to the live library are the same objects as today, plus nothing.
- `kalshiLiveLib.js` receives the slot as one optional argument, `args.slot` (a bag of hooks). Every new line there sits under `if (slotOn(args))`, where `slotOn(args) = args.slot && slotLib.slotActive()`. Two locks on one door: the library will not act on a hook unless the constants agree, even if some caller passes one.
- There is no test backdoor. `slotOn` is the hook bag AND `slotLib.slotWatch()`; the gates replace `slotLib.slotWatch` on the module object for the length of a gate (the live library looks it up at call time) and always restore it. A gate fails if any non-test file contains `_testForce`.
- `kalshiLiveLib.js` may `require("./kalshiSlotLib")` (the slot library requires only `kalshiSignalLib`, so there is no cycle). It uses it for `slotActive`, `slotWindowSpent`, `slotRiskForBotRisk` and nothing else.

**How off-equivalence is proven, not argued** (details in section 9): before touching `kalshiLiveLib.js`, step B1 records golden call logs from the unmodified code, committed as fixtures. Every wiring step must leave those logs byte for byte the same.

## 1. Insertion points, one per function

Each row: where, what is added, and the gate. "Gate" always means `slotOn(args)` unless noted.

| # | Function and anchor | Line | What is added (only when the gate is true) |
|---|---|---|---|
| 1 | `closedByHand`, the `for (const f of r.body.fills)` loop, after `if (f.order_id === t.orderId) continue;` | ~626 | `if (ignoreOrderIds && ignoreOrderIds.has(f.order_id)) continue;` New optional parameter `ignoreOrderIds` (a `Set`, default `undefined`). With `undefined` the line is a no-op, so the function is identical. |
| 2 | `settleOpenOrders`, both `closedByHand(` calls | 650, 664 | Pass `ignoreOrderIds: args.ignoreOrderIds`. New optional argument, `undefined` today. |
| 3 | `botRisk`, the `closedByHand(` call and the return | 689, ~722 | Pass `ignoreOrderIds`. Optional new argument `slotOrders`: when present, add `slotRiskForBotRisk(slotOrders, from)` field by field to `net`, `openCost`, `trades` (addonAtRisk stays as is, the slot has none) before the return. When absent the return is today's object, same keys. |
| 4 | `runL1Tick`, after `if (await store.hasUnresolved())` | 806 | `if (slotOn) { if (await args.slot.hasUnresolved()) return end("attempted", "a second-slot order is unresolved ...") }`. A lost answer on a slot order ends the whole session, as for L1. |
| 5 | `runL1Tick`, the 24 hour read | 811 | After `recentList` is built: read `slotOrders = await args.slot.allOrders()` (the whole collection, not only 24 hours, because the slot's lifetime cap needs it); on any error `note(...)` and `return { skipped: "slot orders unreadable" }`, the same fail-closed shape as the L1 read above it. `recentOrders += slotOrders.filter(inLast24h).length` so the 200 order limit counts both. |
| 6 | `runL1Tick`, the `botRisk(` call | 824 | Pass `slotOrders` and `ignoreOrderIds` (built from `slotOrders` by section 6). |
| 7 | `runL1Tick`, immediately after the loss stop `if (risk.worst <= floor + 1e-9) {...}` closes | ~866 | `if (slotOn && args.shareOut) Object.assign(args.shareOut, { cash, sizeBase, risk, peak, stopAt, allowance, floor, recentList, slotOrders })`. This is how the slot tick later sees the same shared figures without a second balance read. `args.shareOut` is an object the caller passes only when the slot is on. |
| 8 | `runL1Tick`, in the `for (const c of candidates)` loop, before `const windowUsed` | 934 | `+ (slotOn ? slotWindowSpent(slotOrders, ticker) : 0)` added to the `windowUsed` sum. The gross figure, never `openAtRisk`. |
| 9 | `runL1Tick`, just before `store.createTest` | 966 | Slot only: read the account position for this ticker (`GET /portfolio/positions`, `ticker` param, the same read `runExitWatch` makes); unreadable means `results.push(ticker + ": the position could not be read, nothing sent")` and `continue`. Then `directionDecision({ ticker, side: pick.side, l1Orders: recentList, slotOrders, lock: null, position })`; refusal means a result line `ticker + ": a slot order holds the other side"` and `continue`. |
| 10 | `runL1Tick`, `store.createTest(cid, record)` | 967 | `const created = slotOn ? await store.createTestLocked(cid, record, { ticker, side: pick.side }) : await store.createTest(cid, record);` `createTestLocked` returns `true`, `false` (document exists, same meaning as today) or `"direction"` (the lock holds the other side). `"direction"` is a result line, not an error. |
| 11 | `exitWatchIdle` | 1034 | Not edited. The new `slotExitIdle` lives in the slot library and `index.js` combines the two (row 15). |
| 12 | `runExitWatch` | 1064 | **Not edited.** The L1 watch keeps selecting `t.strategy === "L1"` from `kalshiLiveOrders`. Slot positions are handled by `runSlotExits` in a separate pass (section 2). The only reason to touch it would be to subtract slot contracts from its `holding`, which we deliberately do not do (risk 8). |
| 13 | `flattenAll` | 1154 | New optional argument `slot` (hooks). After the `for (const p of held)` loop and before `return { ok: true, results }` (line 1195): `if (slotOn({ slot })) { await slot.afterFlatten({ results, now }) }`, wrapped in try/catch so a bookkeeping failure never changes what Flatten returns. Section 5. |
| 14 | `index.js`, `firestoreLiveStore` | 276 | Add `createTestLocked` (section 3) as a new method. The existing methods are not edited. |
| 15 | `index.js`, `kalshiLiveExit` | 529 and the loop at 534 | `if (!SLOT_ON) { if (await live.exitWatchIdle(...)) return; } else { idle = (await live.exitWatchIdle(...)) && (await slotLib.slotExitIdle(...)); if (idle) return; }`. Inside the loop, after `runExitWatch`, `if (SLOT_ON) { try { await runSlotExits({...}) } catch (e) { console.error(...) } }`. With `SLOT_ON` false the code path is the one that exists today. |
| 16 | `index.js`, `kalshiLiveArmed`, `runL1Tick(` call | 602 | Add `slot: SLOT_ON ? slotHooks(db) : undefined` and `shareOut` to the args object. After the call, `if (SLOT_ON) { try { await runSlotTick({...shared}) } catch (e) { console.error(...) } }`. |
| 17 | `index.js`, `settleOpenOrders(` call | 621 | After it, still inside its own try/catch: `if (SLOT_ON) await runSlotSettle({...})`. The L1 call gets `ignoreOrderIds` only when `SLOT_ON`. |
| 18 | `index.js`, `kalshiFlattenAll` | 489 | `live.flattenAll({ ..., slot: SLOT_ON ? slotHooks(db) : undefined })`. |

`slotHooks(db)` is one function in `index.js` that returns the hook bag (`hasUnresolved`, `allOrders`, `afterFlatten`, `ignoreIds`, ...). It is only called when `SLOT_ON`.

## 2. The new file: `functions/kalshiSlotRunLib.js`

All I/O is injected, exactly like `runL1Tick`: a `store` object, `fetchFn`, `keyId`, `pem`, `now`, `logEvent`, `setSession`. The file has no `getFirestore`, no `process.env`, no clock (`now` is passed), no `Math.random`, and no `require` except `./kalshiSlotLib`, `./kalshiLiveLib` (for `liveRequest`, `exitBody`, `claimClose`, `windowKey`, `L1_WINDOW_CAP_FRACTION`) and `./kalshiSignalLib`. A gate checks that list. `kalshiLiveLib` does not require this file (so no cycle); `index.js` requires both.

### `runSlotTick(args)` (entry)

Called by `kalshiLiveArmed` right after `runL1Tick`, in the same minute function. It shares the function's secrets and its quotes (`market.quotes` already holds Bitcoin, Ethereum and gold 15 minute markets). No new scheduled function.

Order of work, each step failing closed (a skip with a note, never an order):

1. `strategies = slotLib.activeSlotStrategies()`; empty means return at once with no I/O at all (second line of defence for off-equivalence).
2. Preconditions, the same ones L1 uses: `session.active === true`, `enabled === true`, `active` (exchange trading), `store.halted()` false (read again immediately before every order, like L1), no unresolved slot or L1 order. If `runL1Tick` ended the session this minute (loss stop, lost answer), the slot does nothing: it re-reads the session through `args.sessionNow()` or uses the `{ ended }` return of `runL1Tick`, whichever the caller passes.
3. `shared = args.shareOut`. If it is empty (`runL1Tick` returned before the stop check, for example on a balance read failure), the slot skips: no shared figures, no order.
4. The kill latch: one read of `kalshiSlotControl/killed`. A document that cannot be read is passed on as unreadable, which `killCheck` treats as killed. Per strategy the latch is `doc[strategyId]` (an object with `killedAt`) or `null`.
5. For each strategy and each quote whose series is in `strategy.series`, whose market is open, and whose seconds left lie inside the entry window: read the market (`GET /markets/{ticker}`), choose the side by `sideRule` (`favourite` means the side with the higher ask; the touch price of the chosen side is the limit), read the position (`GET /portfolio/positions?ticker=`), pick the step (the lowest step not yet attempted, up to `maxSteps`).
6. **The shared stop on the new order.** Before sending, require `shared.risk.worst - orderCost > shared.floor` (the order is treated as lost the moment it exists). L1 never needs this because its window cap keeps one window under the stop; the slot, which can be bigger, does. If it fails, skip with a note.
7. **The entry transaction** (section 3): `store.runSlotEntry({ ticker, side, decide })`. `decide(lockDoc, slotOrdersFresh, l1DocFresh)` is a pure function that calls `slotLib.slotOrderCheck({...all inputs..., lockTxn: true, lock: lockDoc, slotOrdersComplete: true})` and, if allowed, returns `slotOrderRecord(...)` plus the lock to write. The transaction creates the order document `kalshiSlotOrders/{cid}` and writes the lock in the same commit. No order document means no send.
8. Send the order with `liveOrderBody(ticker, limit, side, cid, exchangeIndex, count)` and the same response handling as `runL1Tick`: 2xx with `order_id` records the fill; 409 calls `findOrder`; an ambiguous status (0, 429, 5xx) marks the document `unknown` and **ends the session** with a message; any other status marks `error` and ends the session. Never retried. Client order id `S-{ID}-{TICKER}-{step}` (already in the library).
9. After all sends, nothing is logged to L1's `riseLog`. The slot has no logging-only fields in this phase.
10. It returns `{ results }`, and `index.js` logs it with `console.log` only. No new control document is written in this phase (a page note belongs to the later page phase).

### `runSlotExits(args)` (exits)

Called inside the existing `kalshiLiveExit` loop (every ~10 seconds), after `runExitWatch`. It uses the same secrets.

1. `list = await store.slotRecentFilled(now - lookback)` (a query on `kalshiSlotOrders` for `status == "filled"` and `settled == false`; same two-equality shape as `recentFilled`, no index).
2. For each order, the strategy is looked up **by id in the code registry**; an order whose `slotId` is no longer registered is not exited by this engine and is surfaced in the result (it will settle on its own, or Flatten closes it). Its exits come from the strategy: `stopBid`, `targetBid`, `mustExitLeftSec`. The engine reads the market, computes the bid of the side held (the same arithmetic as `runExitWatch`: yes side uses `yes_bid`, no side uses `1 - yes_ask`), and decides sell if the bid is at or under `stopBid`, at or over `targetBid`, or the seconds left are at or under `mustExitLeftSec`.
3. If selling is due and `enabled === true`: `claimClose(store, ticker, "slot", now)` first (before the position read, same as `runExitWatch`), read the position, `othersUnsold = L1 unsold on ticker + other slot orders unsold on ticker` (both from reads: one `slotRecentFilled` list and one `store.l1UnsoldOnTicker(ticker)`; either unreadable means skip), then `count = slotSellCount({ order, position, haveClaim: true, othersUnsold })`. Zero means record `exitStatus: "skipped"` with a note (never sell).
4. Claim the exit on the order document atomically (`claimSlotExit(id, tries)`, the same transaction shape as `claimExit`), send `exitBody(...)` with id `slotExitClientOrderId(order.id, tries + 1)` as an immediate-or-cancel close. Handle the answer exactly as `runExitWatch` does: success patches `exitStatus`, `exitCount`, `exitProceeds`, `exitAt`, `exitOrderId`, and when everything is sold applies `slotSettledFields(order, "exit")` plus `settledAt: now`; 409 marks `unknown`; an ambiguous answer marks `unknown` and ends the session; a refusal marks `error` and counts a try (max 3).
5. When `enabled` is not true it records `exitShadow` once per order and sends nothing, like L1.
6. After a slot sale (success or failure) it calls `store.releaseClose(ticker, "slot")` so the 90 second lease does not hold L1's own 25 cent stop off that market (risk 4). The release only clears a claim held by `"slot"`.
7. Kill rule evaluation after any settle or exit that completes an order: `slotLib.slotKillStatus` over the fresh orders; if killed, write the latch in the **same transaction** as the settle patch (section 3 describes `settleSlotWithLatch`).

### `runSlotSettle(args)` (settle sweep)

A slot twin of `settleOpenOrders`, called right after it. Reads open filled slot orders (`slotOpenFilled()`), asks the public market for its result, and runs the hand-close check with `ignoreOrderIds` containing the **L1** entry and exit order ids and all other slot ids. Writes `slotSettledFields(t, result)` plus `settledAt`, and the kill latch in the same transaction when a rule trips. It reuses `closedByHand` exported from the live library, with its new `ignoreOrderIds` argument. At most 12 markets per run, as today.

## 3. The direction lock: `kalshiLiveDirection/{ticker}`

**Document.** `{ side: "yes"|"no", by: "L1"|"SLOT:<id>", ts }`, document id equal to the ticker. A ticker belongs to one 15 minute window, so a lock dies of age and is never deleted. Nobody releases it (design doc section 1).

**Who writes it.** Only two code paths, each inside the transaction that creates the order document:

- `firestoreSlotStore.runSlotEntry` (slot orders, collection `kalshiSlotOrders`).
- `firestoreLiveStore.createTestLocked` (L1 orders, collection `kalshiLiveOrders`), used only when `SLOT_ON`.

**Slot transaction** (`db.runTransaction`):

1. `tx.get(lockRef)`.
2. `tx.get(slotCollection)` (the whole collection, so the lifetime cap and one-attempt-per-step see the same data at commit time) and `tx.get(l1Ref)` for `kalshiLiveOrders/L1-{ticker}` (the only L1 order id a ticker can have).
3. Call `decide(lock, slotOrders, l1Docs)`. It runs `slotOrderCheck` with `lockTxn: true`. The pure function reads `lock`; an existing lock on the other side refuses; no lock is fine.
4. If allowed: `tx.set(lockRef, { side, by, ts })` only when absent (an existing same-side lock is left alone), then `tx.create(orderRef, record)`. If the order document already exists, `create` throws and the whole transaction, lock write included, rolls back. That is the same "already attempted" signal as `createTest`.
5. The position is read before the transaction (a network call must not sit inside a transaction). The lock closes the gap, not the position read.

**L1 transaction** (`createTestLocked`): `tx.get(lockRef)`; if it exists with the other side return `"direction"` without writing; else set the lock if absent and `tx.create(orderRef, record)`; return `true`. An order document that already exists returns `false`, as `createTest` does today. L1 does not read the slot collection inside its transaction because the lock is the one record both engines write first.

**Two instances.** During a deploy, instance A (L1 yes) and instance B (slot no) both reach the lock transaction. Firestore serialises them on the lock document: the loser retries, sees the winner's side and refuses. A fake store that serialises transactions (a single async queue per document id) is part of step B3's tests (SW8).

**What a refusal costs.** A missed entry. Never a hedge. A lock left behind by an order that did not fill also blocks the other side for the rest of that window; this is deliberate.

**Kill latch.** `kalshiSlotControl/killed`, one document, a map `{ [strategyId]: { killedAt, reason } }`. Written only inside the transaction that records the settle or exit which tripped the rule. Stored data can only turn a strategy off; only a code edit that moves `reviewedAt` later than `killedAt` turns it back on (already enforced by `killCheck`).

## 4. The shared risk

Both numbers come from the slot library's existing pure functions, which already have parity gates against `botRisk` and `windowUsed`.

- **Window cap.** In `runL1Tick`'s loop (row 8), `windowUsed` gains `+ slotWindowSpent(slotOrders, ticker)`. `slotOrders` is the full collection read at row 5. The sum is the gross `maxCost` of slot orders that are or were money in that window, sold or not. L1's `room = 0.055 * sizeBase - windowUsed` shrinks accordingly. The mirror image is already inside `slotOrderCheck` (it subtracts L1's spend, takes at most half the cap, and leaves $1.05 for one more L1 contract).
- **Loss stop.** `botRisk` returns today's four numbers plus the slot's, added field by field: `net`, `openCost`, `trades`. `risk.worst = net - openCost` therefore includes a slot stop-out the minute it is sold, and every unsettled slot order counted as lost. The existing floor check at line 858 needs no edit: it already reads `risk.worst`. A slot loss therefore ends the whole session, L1 included. That is the owner's "one budget".
- **Order of evaluation inside a minute.** L1 runs first and decides on the figures it read. The slot tick then runs on fresh reads (it re-reads the order collections, because L1 may have created an order this minute) and counts L1's new spend in its own `l1Used`. The slot never goes first.
- **Slot reads happen at most once per minute for the tick** and once per exit pass for exits. They happen only when the slot is on.
- **Add-on and skim.** `foldSkim`, `skimAddon` and `reviewSizing` keep reading only L1 orders. Slot profit is never reinvested into L1 size.

## 5. Flatten

`flattenAll` stays the owner's emergency exit: it still sells the account's whole position per ticker under `claimClose(store, ticker, "flatten", now)`, so slot contracts are sold with L1's. The halt is set first by `kalshiFlattenAll` (line 478), and the slot tick re-reads `store.halted()` before every order, so nothing new enters while it runs.

New, only when the slot is on, via `slot.afterFlatten({ results, now })` (row 13):

1. For every result whose `status` is `sold`, `partly sold` or `skipped` with detail "already closed": every unsettled, filled slot order on that ticker is marked closed by Flatten: `settled: true, result: "hand", flattened: true, settledAt: now`. A `hand` result carries no pnl, so it stays out of the loss stop (the same treatment as a hand close; the owner sees the real loss in the account). Tickers whose result is `error`, `no fill` or `skipped` for a lease reason are **not** marked, because contracts may still be held.
2. Set the kill latch for every active strategy: `killedAt: now, reason: "flattened by the owner"`. Nothing re-enters until a reviewed edit moves `reviewedAt` past that time.
3. The whole of `afterFlatten` is wrapped in try/catch in `flattenAll`, so a failure to write bookkeeping never changes the result Flatten returns to the owner. The failure is added to the event log text.

The claim is taken by Flatten before any sale and the slot exit takes the same lease with a different `who`, so they cannot sell the same market at the same moment (`claimClose` already refuses a different holder inside 90 seconds).

## 6. `closedByHand` and `settleOpenOrders` ignore the other engine's fills

The hazard (found in the design review, and sharper than first described): Kalshi books a NO buy on the YES side, so a **slot NO entry fill reads as a sell of side no** in the fills list, and a slot exit reads as a sell too. Either would be counted by L1's `closedByHand` as "the owner sold it by hand", and L1's real position would drop out of the loss stop (the unsafe direction).

Fix, behind row 1 and 2:

- `ignoreIds(slotOrders, l1Orders)` builds a `Set` of every `orderId` and `exitOrderId` of **both** collections, except nothing is subtracted for the order being checked: `closedByHand` already skips the order's own `orderId` and `exitOrderId`, and the set only adds the other orders' ids.
- L1's `botRisk` and `settleOpenOrders` get the set only when the slot is on.
- The slot sweep passes the same kind of set to `closedByHand`, so an L1 sell, or another slot step's fill, is never read as a hand close of a slot order.
- An exit whose answer was lost has no recorded `exitOrderId`; that case already ends the session and needs the owner, so it is not handled by guessing.
- Known limit, stated so nobody trusts it too far: a genuine hand sale on a ticker where both engines hold contracts cannot be told apart by which engine it belongs to. The rule stays conservative: an order is "closed by hand" only when the fills cover everything that order still held, and otherwise it stays open and counted as lost.

`foldSkim`, `exitWatchIdle`, the push alert library and the nightly report all select `strategy === "L1"` from `kalshiLiveOrders` and never see `kalshiSlotOrders`; none of them is edited.

## 7. `firestore.rules`, the scan and the rules tests

Rules to add (the same shape as `kalshiLiveOrders`):

```
match /kalshiSlotOrders/{id}   { allow read: if isAdmin(); allow write: if false; }
match /kalshiLiveDirection/{id} { allow read: if isAdmin(); allow write: if false; }
```

`kalshiSlotControl` (the kill latch) gets **no rule**, so it is closed to every browser, like `kalshiLiveClosing`.

**A decision for the owner:** the Phase A design doc says `kalshiLiveDirection` should have no rule at all. The instruction for this phase says admin read. Admin read of a lock document leaks nothing and helps debugging; no rule is stricter. The plan follows the instruction (admin read, no write) and the design doc line must be edited to match. If the owner prefers closed, delete the second block; nothing else changes.

Tests and scanners affected:

- `test/kalshiSlotGates.test.js`: the line asserting `!/kalshiSlot/.test(firestore.rules)` and the one asserting `index.js` has no `kalshiSlotOrders` must be rewritten as "the rule exists, is admin read, and has no client write", and the "phase A inert" file walk must allow `index.js`, `kalshiLiveLib.js`, `kalshiSlotRunLib.js` and the deploy docs to mention the slot library (still nothing else: no workflow, no script, no page). The line asserting `!/SLOT_|kalshiSlot/.test(live_src)` becomes "the live library mentions the slot only inside the gated blocks" (checked by the SW1 source scan below). These are the three Phase A gates the design doc already says move at phase C; they are rewritten, not weakened: each stays a gate on a smaller surface.
- `.claude/skills/security-audit/scripts/scan.js` section 3 already checks every `kalshi*` collection: write must be `if false` or admin, read must call `isAdmin()`. The new blocks pass. Run the scan once after the rules edit and expect no new FAIL or WARN. No scan change is needed unless a new HTTP endpoint is added; none is planned.
- `test/kalshiFlattenGates.test.js` line 131 (the claim documents have no client rule) is unaffected.
- Rules cannot be exercised offline here (no emulator). The rules gate is therefore a text gate; the real check is the deploy-time `firebase deploy --only firestore:rules` by the owner, which this phase does not run.

## 8. The page

The page reads `kalshiLiveOrders` (Bot page listeners at `index.html` lines ~1099 and ~1113) and matches account fills and positions to those orders (`kalshiPositionRows`, `kalshiFillIsBot`, `kalshiIsExitFill`, `kalshiResolveOrders`, around lines 2421 to 2590). It never reads `kalshiSlotOrders`, so **slot orders are not shown as L1 orders** and no L1 total includes them. That is the safe default and needs no page edit in this phase.

What the owner will see while a slot is live and no page card exists: slot contracts show up in the account's Open positions as positions with **no matching bot order**, and slot fills as fills with no matching order. Existing page logic treats an unmatched fill as a manual trade ("not the bot"). That is wrong in label but safe: it overstates nothing and changes no order. It is why the first real admission (phase H) must come with the page card.

What the later page card needs (not in this phase):

- A read-only listener on `kalshiSlotOrders`, admin only, with its own limit.
- `kalshiPositionRows`, `kalshiFillIsBot` and `kalshiIsExitFill` taught the slot order ids and exit order ids, so slot positions and fills are labelled as the slot's, not "manual" and not L1's.
- Every dollar through `kalshiMoney` (Privacy view), a separate "Second slot" card, no control that can change a slot, and a Changelog line. The tests `test/kalshiLayoutGates.test.js` and the pre-ship page checks must pass.
- The Bot page's silent-market list (`KAL_WATCH`) and the notification centre stay L1 only.

## 9. Existing tests that touch the changed functions, and how each stays unchanged

No existing test is edited by B1 or B2. A change to one means the off-equivalence broke; fix the code.

| Test file | What it covers | Why it stays unchanged |
|---|---|---|
| `kalshiL1Gates.test.js` (W1 to W5, probe, smooth, OC1, store read counts, `sessionTradesCached` counts at ~837) | `runL1Tick` numbers, window and stop, read counts | Their fake stores have no `createTestLocked`, no `slot` hooks and no `shareOut`. With `args.slot` absent every new branch is skipped, so reads and returns are identical. The returned object gains no keys. |
| `kalshiL1MutationGates.test.js` | mutated variants of L1 rules | Same reason. |
| `kalshiLiveGates.test.js` | `runLiveTest`, `runArmedTick`, store interface | Not edited. |
| `kalshiExitGates.test.js` (E1 to E13) | `runExitWatch`, `claimClose` order, `exitWatchIdle` | Not edited; `claimClose` count gate (`kalshiFlattenGates` line 129 expects exactly two `await claimClose(store, ` calls in the live library) stays true because the slot's claims are in the new file, not in `kalshiLiveLib.js`. |
| `kalshiFlattenGates.test.js` (F6 to F8) | `flattenAll` per-market claim and fresh position read | `flattenAll` gets one extra gated block after the loop; with no `slot` argument it is skipped. |
| `kalshiHandSoldGates.test.js` (H5, H11 to H13) | `closedByHand` | The new `ignoreOrderIds` check is a no-op when `undefined`. |
| `kalshiSettleGates.test.js` | `settleOpenOrders` | The new argument is optional and unused today. |
| `kalshiAccountGates.test.js`, `accountIdGates.test.js` | account snapshot, `DEFAULT_ACCOUNT_ID` | Not touched. |
| `kalshiSlotGates.test.js` | the slot library | Three inertness assertions are rewritten as in section 7. Every other gate is unchanged. |
| `securityAgentGates.test.js`, `pagesPublishGates.test.js` | scan fails on a bad fake repo, publish excludes | Unchanged. |

**New gates (file `test/kalshiSlotWiringGates.test.js`, plus one fixture file):**

- SW0 golden logs: fixtures `test/fixtures/offEquivalence.json` hold the call logs (every `store.*` call with its arguments, every `fetchFn` URL and method, in order, and the return values) of `runL1Tick`, `botRisk`, `settleOpenOrders`, `runExitWatch`, `exitWatchIdle`, `flattenAll` and `closedByHand` run against fixed fake stores and a scripted `fetchFn`. **They are recorded from the unmodified `kalshiLiveLib.js` in step B1, before any edit to it**, with the generating script committed beside them. The gate replays the same scenarios with the wiring present and the slot off and requires deep equality.
- SW1 source scan: strip comments from `kalshiLiveLib.js`; every occurrence of `slot` (case-insensitive) must sit inside a statement guarded by `slotOn(`; `kalshiSlotLib` is the only slot module it requires.
- SW2 `index.js` scan: `SLOT_ON` is derived only from `slotLib.slotActive()`; every `kalshiSlot*`, `kalshiLiveDirection` and `slotHooks` mention is inside an `if (SLOT_ON)` block or in a function only called from one; no new `defineSecret`, no new `onSchedule`, `onCall`, `onRequest`.
- SW3 no test backdoor (`_testForce`) in any non-test file, and `slotOn` is exactly the constants.
- SW4 with the real constants (switch off) `runSlotTick`, `runSlotExits`, `runSlotSettle` return having made zero calls to any injected function.
- SW5 off-path: with the slot on (forced) and no registered strategy, nothing is sent.
- SW6 opposite side blocked in both directions, in the transaction, with a stale position read and with a lost-order read.
- SW7 a slot loss since `since` makes `runL1Tick` end the session with "loss stop"; an unsettled slot order is counted as lost.
- SW8 two instances: a fake store that serialises transactions per document; L1 yes and slot no race, exactly one order document and one lock exist, and the loser sends nothing.
- SW9 `closedByHand` does not mark an L1 order "hand" because of a slot NO entry fill or a slot exit fill, and the reverse.
- SW10 slot sells only its own contracts: account holds L1 3 plus slot 5, slot sells at most 5; holds fewer than the sum, slot sells no more than `holding - othersUnsold`; opposite side held, sells 0.
- SW11 Flatten with the slot on marks only tickers that sold, sets the latch, leaves a failed ticker's slot orders open, and returns the same result as without.
- SW12 a lost answer on a slot buy or sell ends the session and is never retried.
- SW13 `claimClose` is taken before the position read, and released only if held by `"slot"`.
- SW14 the 200 order limit counts slot orders when on, and not when off.

## 10. Build order

Each step is one reviewed commit, each ends with `npm test` and the pre-ship checks green, and none deploys anything. The switch stays off in all three.

**B1. Exit engine, slot run library, and the safety net (no edit to `kalshiLiveLib.js` yet).**
1. Record the golden call logs from the untouched `kalshiLiveLib.js` and commit them with their generator script (SW0 fixtures).
2. Add `slotActive()` and `slotExitIdle()` to `kalshiSlotLib.js` (pure; the Phase A "no clock or store" gate must still pass).
3. Write `kalshiSlotRunLib.js`: `runSlotExits`, `runSlotSettle`, `runSlotTick`, all with injected I/O, against fake exchanges in the style of `kalshiExitGates.test.js`.
4. Tests SW4, SW5, SW10, SW12, SW13 and the fake-exchange tests for each function, including the SX id and the immediate-or-cancel body.

**B2. L1 and Flatten wiring, behind the gate.**
1. Edit `kalshiLiveLib.js` for rows 1 to 10 and 13 only, each under `slotOn`. Add `require("./kalshiSlotLib")`.
2. Run SW0 first: it must pass before any new behaviour test is written.
3. Tests SW1, SW6, SW7, SW9, SW11, SW14.
4. Rewrite the three Phase A inertness assertions (section 7).

**B3. `index.js`, rules, store and the remaining tests.**
1. `index.js`: `SLOT_ON`, `firestoreSlotStore`, `createTestLocked`, `releaseClose`, `slotHooks`, rows 14 to 18. Nothing here runs when `SLOT_ON` is false.
2. `firestore.rules` (section 7), the doc edit to `SECOND_SLOT_DESIGN.md` (one line about the lock rule, and a pointer to this file), the Changelog is not touched (no user-visible change).
3. Tests SW2, SW3, SW8, and a final full `npm test`, then `node .claude/skills/security-audit/scripts/scan.js` and `/pre-ship`.
4. A deploy note in this file: the three functions that change (`kalshiLiveArmed`, `kalshiLiveExit`, `kalshiFlattenAll`) and the rules. With the slot off the deploy is behaviour-neutral, so it can go with `functions/deploy-sizing.sh` and `functions/deploy-push.sh`; the owner decides when.

Admission of a strategy (phase H) remains a separate pull request: an entry in `SLOT_STRATEGIES`, `SLOT_ENABLED = true`, a README pre-registration, and the page card from section 8 in the same or an earlier change.

## Ten biggest risks

1. **Off-equivalence is broken by an edit that looks harmless** (an added read, a changed return shape, a reordered call). Mitigation: golden call-log fixtures recorded before any edit, plus the source scans SW1 and SW2. If a golden log has to change, stop.
2. **A slot NO entry fill or a slot exit read as a hand sale of an L1 order** (Kalshi books a NO buy as a sell on the YES side). This would drop a real L1 loss out of the stop. Mitigation: `ignoreOrderIds` built from both collections, test SW9.
3. **The direction race between two instances** (A reads empty, B reads empty, both send opposite sides). Mitigation: the lock is read and written in the same transaction that creates the order, for both engines, plus SW8. Residual: a position read made just before the transaction can be stale, so the lock, not the position, is the guard.
4. **A shared close lease stalls L1's 25 cent stop.** `claimClose` refuses a different holder for 90 seconds, so a slot sale on a ticker would hold L1's exit off it. Mitigation: the slot releases its own claim after each attempt (`releaseClose`, only clears `by === "slot"`). If that write fails, L1's stop on that market waits up to 90 seconds.
5. **The slot starves L1 through the lock.** A slot entry early in the window (up to 14 minutes left) can lock a side before L1 decides, and L1 then skips the opposite side. This is the owner's rule working as written, but it can cost L1 an order. Mitigation: slot entry windows are set per strategy in the reviewed registry; the first admission should keep them away from L1's 6 and 10 minute looks, or accept the cost explicitly.
6. **The shared stop is one-way.** A slot loss ends L1 too, by design, and the session stays off until the owner restarts it. A badly chosen strategy can therefore switch the proven gold ladder off. The slot's own daily and lifetime caps and kill rules exist to keep that rare; they are not a guarantee.
7. **Flatten bookkeeping can lag the sale.** Orders are marked closed only after the sells return; a crash between leaves slot orders "open" and counted as lost (the safe direction), and the next settle sweep corrects them. A sale that fails leaves contracts held and the order open.
8. **Each engine caps its sell by its own contracts, but L1's watch is not taught about the slot.** If a hand trade leaves the account holding fewer contracts than L1 plus the slot believe, L1's `min(remaining, holding)` can sell contracts the slot thinks are its own. Direction-safe (it can only reduce, never open the opposite side), but the slot's record is then wrong until its sweep. Left as is on purpose, because editing the L1 watch is the riskiest change available.
9. **The page labels slot fills and positions as "manual" until the card exists.** Nothing trades differently, but the owner could misread the Bot page, and the Privacy and notification logic ignore the slot. Admission must not happen before the page card.
10. **Cost and reads.** When on, each minute adds a full read of `kalshiSlotOrders`, a position read per candidate, a market read and a transaction that reads that collection; the exit loop adds a query every ~10 seconds while a slot order is open. It is small, but this repo has been billed for exactly this kind of read before. The slot collection read should be bounded (an index of the last N days plus a running lifetime total document) before a strategy has more than a few hundred orders. The slot also cannot be disabled by a stored setting, only by a code edit (`SLOT_ENABLED = false`) and a deploy, which is slower than a switch; the kill latch and Flatten are the quick tools.


## Status and deploy note (step B3 done, Oct 29, 2026)

B3 built `functions/kalshiSlotStoreLib.js` (the Firestore side, with the database injected so a fake can drive it), wired `functions/index.js` behind `SLOT_ON = slotLib.slotActive()`, added the two rules and added `runSlotSettle` to the run library (section 2 listed it; B1 had left it out, and without it a slot order held to the close would never settle). Differences from the plan, all in the cautious direction:

- The store lives in its own file instead of `index.js`, so the lock transaction, the leases and the Flatten bookkeeping are tested against an in-memory database. `index.js` only calls it under `SLOT_ON`; `firestoreLiveStore` gained one method, `createTestLocked`, which nothing calls while the slot is off.
- Flatten bookkeeping marks a slot order closed by hand only when the ticker's result is `sold` or `already closed`. A `partly sold` market keeps its order open (the shared stop counts it as lost). The kill latch is still set for every active strategy whatever the results were.
- The exit idle check asks the slot only after L1's check says idle, so a minute L1 needs is never made idle by a slot read.
- The tick, the exits and the settle sweep each run in their own try/catch after L1's work, so a slot failure is logged and never stops L1's minute, its 25c exit line or its settle sweep. The Flatten hook is already wrapped in `flattenAll`.

**Proof it is off-equivalent:** `test/kalshiSlotIndexWiringGates.test.js` SI0 replays seven scenarios of `kalshiLiveArmed`, `kalshiLiveExit` and `kalshiFlattenAll` through `index.js` (firebase stubbed, in-memory database, scripted exchange) and requires every database operation, request and console line to equal `test/fixtures/offEquivalenceIndex.json`, recorded from `index.js` before the wiring (`node test/fixtures/indexHarness.js <copy of the old index.js placed in functions/>`). SI2 flips the gate on in memory and shows the same orders go out and nothing is written to a slot collection with no strategy registered.

**Deploy note.** With `SLOT_ENABLED = false` and `SLOT_STRATEGIES` empty the deploy is behaviour-neutral, so it can go whenever the owner chooses; the owner deploys, nothing here does.

- `bash functions/deploy-sizing.sh` ships the minute function (`kalshiLiveArmed`).
- `bash functions/deploy-push.sh` ships the exit watch (`kalshiLiveExit`) and `kalshiFlattenAll`.
- The rules ship with `npx firebase-tools deploy --only firestore:rules --project shwoopnet` (or `functions/deploy-paper.sh`, which deploys the rules too). They can go before or after the functions; until a slot order exists there is nothing in either collection.
- No new secret, scheduled function, callable or endpoint is added, so no new environment variable and no change to the security scan's allowances.
- Before the FIRST admission (phase H) the page card (phase F) must exist: until then slot fills and positions show on the Bot page as unmatched account activity (section 8).


## Review round 2 (Oct 29, 2026): what changed after the independent review

Every item below has a gate; the ones marked (fails before) were written to fail against the previous code first.

1. **Turning the slot off, or deleting a strategy, no longer orphans a live position (high, fails before).** There are now two constants in `kalshiSlotLib.js`. `slotActive()` (entries: `SLOT_ENABLED` and a registered strategy) is the narrow gate and only the entry tick uses it. `slotWatch()` is `slotActive() || SLOT_EVER_USED`, where `SLOT_EVER_USED` ships `false` and is set to `true` by the pull request that first admits a strategy and never set back (gate SI14b fails if a strategy is active while it is false). Everything that protects an open slot position runs on `slotWatch()`: the exit pass, the settle sweep, the exit-loop idle check, the slot's dollars in `botRisk` and the window cap, the direction lock, L1's clamp and Flatten. An order whose strategy is gone is exited by `FALLBACK_EXIT` (a stop at 25c, no target, out 60 seconds before the close). It stays a constant in code: nothing stored can move it, and while it is false (how this ships) the off-equivalence logs are byte for byte the same. Gates: `SW-ORPHAN`, `SW-WATCH-ONLY`, the fallback gate.
2. **A hedge made by an old revision is caught (high, fails before).** During the deploy that first admits a strategy, an old instance's L1 order never reads the lock (`createTest` is a bare create), so a slot NO and an L1 YES could both exist. The lock cannot fix an instance that does not read it, so the exit pass is the net: every pass it reads the other orders on the market, and a slot order that sits against another order's unsold contracts (L1's always, or an earlier slot order) is sold at once with reason `hedge` and its strategy is latched off. The exit loop runs about every 10 seconds, so the exposure lasts seconds. Gate `SW-HEDGE` creates the opposite L1 order with a bare create after a real slot entry. Residual: those seconds are real exposure, which is why the first admission should be deployed while no L1 order is likely (outside minutes 3 to 10 of a quarter hour) and the slot's caps are small.
3. **Entry window judged at commit time (medium).** `runSlotTick` takes an injected `clock` (`index.js` passes `Date.now`). Before the transaction and again inside `decide` it recomputes the seconds left, refuses a minute older than 20 seconds, and `slotOrderCheck` gets the fresh figure. A strategy whose `leftMinSec` is not at least 20 seconds above its `mustExitLeftSec` never enters. Gate `SW-CLOCK`.
4. **A failed write after a lost answer cannot leave the strategy running (medium).** On every lost-answer, 409 and refusal path (entry and exit) the order is: latch the strategy off, end the session, and only then write the order's status, each step on its own. `hasUnresolved` also counts `exitStatus: "unknown"`, and an exit that stays `"sending"` for over 60 seconds (the claim now stores `exitClaimedAt`). A sale mid-flight is not unresolved, so a normal sell never ends the session. Gate `SW-LOST-ANSWER`, `SI3b`.
5. **L1's exit watch is slot aware (medium, two findings).** With the slot watched, `runExitWatch` subtracts the slot's unsold contracts on the same ticker and side from the account position before it sells (`args.slot.unsoldOn`), and sells nothing if that cannot be read. A count that is zero only because of the slot's contracts is retried, never written as `skipped`. It also gives its close lease back when its pass ends (`store.releaseClose`, holder checked), so it cannot hold the slot's stop off a market for 90 seconds. Gates `SW-EXIT-1`, `SW-EXIT-2`, `SW-EXIT-3` (off: identical calls whether or not hooks exist).
6. **A transient "nothing sellable" no longer disables the slot exit (medium, fails before).** `skipped` is permanent, so it is written only when a clean position read shows none of the side. A zero that comes from the other engines' contracts is retried on the next pass.
7. **A lost-answer slot order cannot make L1 drop a real loss (low).** `slotIgnoreSet` adds a `ticker:<T>` marker for every market with a slot entry or exit of unknown state, and `closedByHand` answers `unknown` for it, so the L1 order stays open and counted as lost. Gate `SW-LOST-ID`.
8. **Structural gates (low).** `SW1b` walks every use of the slot in `kalshiLiveLib.js` and requires a guard (`slotOn(`, `slotLive`, the slot-only argument checks) on its own line or an enclosing block (it fails if an unguarded `args.slot.` call is added; checked by hand). `SW3` and `SI1` ban any backdoor and any use of `slotActive` in `index.js`. The `_testForce` bypass is gone.

**Said plainly, because the brief asked for no test to change.** Tests that existed on `main` are unchanged. Inside this branch's own gates three assertions of `test/kalshiSlotGates.test.js` were loosened in the wiring phase (the recursive "no file mentions the slot library" scan now exempts the slot libraries, `kalshiLiveLib.js` and `index.js`, and the three "not touched" assertions became guarded-use assertions). That is expected for a wiring phase. The real off-equivalence proof is `SW0` and `SI0` (recorded call logs, never regenerated), backed by `SW1b`, `SW1c` and `SI1`.

**Accepted and documented, not fixed.**

- *Firestore rules change while the slot is off.* `firestore.rules` gains admin-read blocks for `kalshiSlotOrders` and `kalshiLiveDirection`. Both collections are empty and were default-deny before; the deploy is a no-op for behaviour. If byte for byte unchanged rules are wanted, move that hunk into the admitting pull request.
- *The window cap can be overshot by one order of each engine when two instances overlap during a deploy.* L1's window check and its order creation are not in one transaction with the slot's read. The slot side is protected (its `decide` re-reads inside the transaction). The 12% loss stop still bounds the worst case. Not fixed because L1's create path may not gain a read of the slot collection while the slot is off.
- *Security scan.* One FAIL (`body-parser`, GHSA-27r3-jxmh-p828) comes from the dependencies already on `main`; this branch changes no `package.json` or lockfile. Run `npm audit fix` in `functions/` in its own pull request before the slot goes live.

**Before the first admission (hard prerequisites, in the same or an earlier pull request).**

1. The page card (phase F): an admin-only read of `kalshiSlotOrders`, `kalshiFillIsBot`, `kalshiPositionRows` and `kalshiIsExitFill` taught the slot ids so slot fills are not shown as manual trades, the slot's dollars in Stop Loss and Risk, every figure through `kalshiMoney`. `SI14` is rewritten, not deleted: it already requires the page to name `kalshiSlotOrders` once `SLOT_ENABLED` or a strategy exists.
2. A phone alert for a slot close (a `kalshiSlotOrders` trigger beside `kalshiPushOrder`). Same gate.
3. `SLOT_EVER_USED = true` in `kalshiSlotLib.js`, in the same change that sets `SLOT_ENABLED = true`.
4. Deploy `kalshiLiveExit` and `kalshiFlattenAll` (`functions/deploy-push.sh`) BEFORE or with `kalshiLiveArmed` so no old exit watch is alive when the first slot order can exist, and deploy in a quiet minute.
