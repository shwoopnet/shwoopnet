# The second slot: design and Phase A guard rails

Written Oct 29, 2026 for the owner (Cameron). Status: **Phase A only.** The guard rails are code and tests (`functions/kalshiSlotLib.js`, `test/kalshiSlotGates.test.js`). They are inert: `SLOT_ENABLED` is `false`, `SLOT_STRATEGIES` is an empty array, nothing imports the module, nothing is deployed and nothing can place an order. No file that trades (`kalshiLiveLib.js`, `index.js`) was edited.

Nothing has passed the research bar yet. This design exists so that when a survivor does, admitting it is a small reviewed edit of one array, inside rules that were written and tested first.

## Decisions this design is built on (the owner, Oct 29, 2026)

1. A slot order may sit in the same market and window as L1 when it is on the **same side**. Only a **hedge** (the opposite side) is wrong.
2. A slot order may be more than one contract and may scale in, inside hard caps in code.
3. L1 and the slot are **one risk budget**: one window cap, one 12% loss stop.
4. Each strategy sells **only its own** contracts.

## 1. The direction rule

### Why the opposite side must be blocked

Kalshi keeps one **net position per market**. If L1 holds 3 YES and a slot order buys NO, the account does not hold 3 YES and some NO. It nets: the contracts cancel, the account's position shrinks or flips, and both exit engines then read a position that matches neither of their records. The exit watch's own comment says what follows: a sell on a position that is gone would OPEN the opposite one (`runExitWatch`, `flattenAll`). Two engines each believing they own the position is exactly the state in which that happens. Same-side orders add up cleanly, which is why they are fine.

### How "same side" is decided

The pure function is `directionDecision` in `kalshiSlotLib.js`. It refuses unless every source agrees:

- **L1 orders** (`kalshiLiveOrders`) and **slot orders** (`kalshiSlotOrders`) on that ticker. Orders whose status is `filled`, `sending` or `unknown` and that are not settled hold their side. In flight counts: a `sending` order may exist at Kalshi. An order with status `no fill` or `error` holds nothing.
- **A direction lock**, one document per ticker, `kalshiLiveDirection/{ticker}` with `{ side }`. This is what makes two function instances safe (below).
- Ticker case and spaces and status case are normalised before comparing, and ANY order with fills holds its side whatever its status (an `error` after a fill is still a position).
- **The live position** for the ticker (`/portfolio/positions`, signed: YES positive, NO negative). A position on the other side (for example a hand trade) blocks the order. An unreadable position blocks it.
- Contradictory books (both sides already present), a lock that cannot be parsed, a missing order list: all refuse. It fails closed.

### Two instances, and L1 and a slot order in flight together

Reading the orders is not enough: instance A (L1, YES) and instance B (slot, NO) can both read an empty book a few hundred milliseconds apart and both pass. Same problem class as the 15 duplicate orders, and the same cure: a key both instances write atomically **before any order is sent**.

- The lock document `kalshiLiveDirection/{ticker}` is read and written **inside the same `runTransaction`** that creates the order document (`kalshiSlotOrders/{clientOrderId}` for a slot order). The transaction reads the lock; if it exists with the other side it aborts; if it is absent it writes `{ side, by, ts }`; then it creates the order. Firestore transactions serialise on the documents they read, so the second writer retries, sees the first side, and refuses.
- The lock is never released inside the window. A ticker belongs to one 15 minute window, so the lock dies of age. A strategy that exits early therefore cannot re-enter on the other side in the same market, which is intentionally conservative.
- The lock only ever narrows what is allowed. Nobody else may delete it. A stale one-way lock can only cost a missed trade, never a hedge.
- **The pure function cannot stop the race; only the transaction can.** So `slotOrderCheck` refuses unless the caller passes `lockTxn: true`, meaning it read and wrote the lock inside the same `runTransaction` that creates the order document. The wiring PR must do the same for L1, and must include a two-instance test with a fake store that serialises transactions. Nothing in phase A takes the lock; this is the contract.
- Rules (changed in Phase B3, Oct 29, 2026, see `docs/SECOND_SLOT_WIRING.md` section 7): `kalshiLiveDirection` and `kalshiSlotOrders` are admin read and no client write; `kalshiSlotControl` (the kill latch) has no rule and stays closed to every browser. Admin read of a lock leaks nothing and helps debugging; delete the `kalshiLiveDirection` block in `firestore.rules` to close it.

### What the later wiring PR must change in `runL1Tick` (do not edit it now)

L1 is the other half of the rule and today knows nothing about the slot.

1. After `l1Pick` chooses `pick.side`, and before `store.createTest(cid, record)`, L1 must take the same direction lock in a transaction with its order document. Today `createTest` creates `kalshiLiveOrders/L1-{ticker}` alone; the wiring PR makes that one transaction that also reads and writes the lock, and a refusal is recorded as a result line (`ticker: a slot order holds the other side`), not an error.
2. L1 must read the account position for the ticker for this check (or reuse a read), and treat unreadable as refuse for that market.
3. `windowUsed` must add `slotWindowSpent(slotOrders, ticker)` (section 4).
4. `botRisk` must add `slotRiskForBotRisk(slotOrders, since)` (section 4).
5. `closedByHand` (a hazard found while reading the code). It sums every sell fill on the ticker and side that is not the order's own entry or exit. A **slot** close is such a sell. With L1 holding 3 and the slot selling 5, `sold >= got - botSold` is true and L1's order would be wrongly marked "closed by hand", dropping a real L1 position out of the loss stop (the unsafe direction). The wiring PR must pass the set of slot order ids and slot exit order ids and skip them there, and the slot settle sweep must skip L1's in the same way.
6. `exitWatchIdle` and `EXIT_BUY_MINUTES` only know L1 orders. A slot position alone would not keep the L1 watch awake. That is correct (the L1 watch must not manage slot positions), so the slot exit engine needs its own wake rule.

## 2. The hard registry

`SLOT_STRATEGIES` is `Object.freeze([])`. A strategy exists only if a person edits that array in a pull request. Nothing read from Firestore, a request or the page can add or change one: the library has no store access at all, and a gate fails if it gains any (`fetch`, `firebase`, `.collection(`, `localStorage`, `request.data`).

An entry has exactly these fields (any other field is rejected, any missing field is rejected):

| Field | Meaning and bounds |
|---|---|
| `id` | 2 to 10 capitals or digits. It goes into the client order id. |
| `readme` | A path such as `kalshi-scalper/README.md#SLOT-XYZ`: the pre-registration, written before any live order. |
| `series` | A non-empty subset of `KXBTC15M`, `KXETH15M`, `KXGOLD15M` (`SLOT_SERIES_ALLOWED`). |
| `entry` | `sideRule` (`yes`, `no` or `favourite`), `priceMin`, `priceMax` inside 0.05 to 0.97, `leftMaxSec` at most 840, `leftMinSec` at least 120. |
| `exit` | `stopBid` (at least 0.01, below `priceMin`), `targetBid` (above `priceMax`, at most 0.99), `mustExitLeftSec` (at least 45 and below `entry.leftMinSec`). Every exit is before settlement. |
| `contractsPerOrder` | Whole number, 1 to 10. |
| `scaleIn` | `maxSteps` 1 to 3, `minGapSec` at least 30, `sameSideOnly: true`, `requirePriorFilled: true`. `maxSteps * contractsPerOrder` may not exceed 10. |
| `killRules` | `maxConsecutiveLosses` 1 to 5, and `minNet: { afterFills 5 to 100, net zero or a loss no bigger than the lifetime ceiling }`. |
| `forwardReadDate` | `YYYY-MM-DD`: when the forward test is read. |
| `reviewedAt` | `YYYY-MM-DD`: the date a human last re-armed it (section 3). Never later than `SLOT_LAST_REVIEWED_ON` (the module has no clock, so the edit that admits or re-arms a strategy moves that constant to its own date). |

`validateSlotStrategy` returns the reasons. `activeSlotStrategies` returns `[]` when the switch is off, when **any** entry is invalid (one typo refuses the whole registry rather than silently dropping one guard), or when an id repeats. Ten ways to be out of bounds are covered by gate "validation rejects anything out of bounds".

## 3. Hard caps and kill rules (constants in `kalshiSlotLib.js`)

| Constant | Value |
|---|---|
| `SLOT_ENABLED` | `false` |
| `SLOT_MAX_CONTRACTS_PER_ORDER` | 10 |
| `SLOT_MAX_OPEN_CONTRACTS_PER_MARKET` | 10 (the slot's own unsold contracts in a ticker, all strategies together) |
| `SLOT_MAX_SCALE_STEPS` | 3 |
| `SLOT_DEPTH_SHARE` | 0.25 of the size resting at the touch |
| `SLOT_WINDOW_SHARE` | 0.5 of the shared window cap, at most |
| `SLOT_L1_RESERVE` | $1.05 of window room always left for one more L1 contract |
| `SLOT_CAP_FRACTIONS` | shares of the sizing base: `perOrder` 1%, `perWindow` 2%, `openTotal` 3%, `daily` 2%, `lifetime` 6% |
| `SLOT_CAP_CEILINGS` | hard dollar ceilings: `perOrder` $20, `perWindow` $40, `openTotal` $60, `daily` $20, `lifetime` $60 |
| `slotCaps(sizingBase)` | `min(fraction * base, ceiling)` for each cap; all zero for a base that is not a positive finite number, which refuses every order |

**The dollar caps scale with the sizing base (the owner, Oct 29, 2026).** The gold ladder makes L1 bigger as the account grows, so a fixed dollar cap would leave the slot a shrinking share of the risk budget. Each cap is a fixed share of the same sizing base L1 uses, with a hard dollar ceiling that no base, however large, can pass. Examples: base 250 gives daily $5, lifetime $15, per order $2.50; base 400 gives per window $8 and open total $12; base 500 gives per order $5. A zero, negative, infinite or non-numeric base gives zero caps and no order. The per-order share stays below the daily share, so one order can never be bigger than the daily cap. The kill rule `minNet.net` may not be a loss larger than the lifetime ceiling (-$60).

The daily and lifetime caps are checked against the NEW order's cost: the count is cut until `cost <= cap + worst` (worst is zero or negative), so one order can never overshoot either cap. These are in addition to the shared 12% L1 stop (section 4), not instead of it. They are set conservatively on purpose: research showed size does not change profit factor except through fee rounding, so there is no reason to start near a ceiling. The count is cut against the caps for the sizing base passed in `input.sizingBase`.

**Depth.** Kalshi's market object carries only the top level of the book (same limit as the L1 depth log, `depthLevels: "top"`). The depth rule is therefore "at most 25% of the size at the touch you hit". Unknown depth refuses.

**One gate.** `slotOrderCheck(input)` is the single function every slot order must pass (the earlier `slotMayEnter` and `slotSideRule` were removed because they accepted a caller-built strategy and skipped checks; the flag-taking variants live only under `_testOnly`). It never throws: a ticker outside the `KX...15M-DDMMMYYHHMM-NN` shape is refused. It checks, in order: strategy active (looked up by id in the code registry), ticker shape, market allowed, side rule, order books read in full (`slotOrdersComplete`, because the lifetime cap needs the whole collection, and every slot order must carry a numeric `ts`), the lock proof (`lockTxn`), kill rules, price band, time window, direction (section 1), scale-in step (one attempt per step, ever: a failed step is not retried; step n only while step n-1 is still open and no earlier step of that strategy on the ticker was sold), base and window fraction usable, daily and lifetime loss caps, then **cuts the count** down until the per-order, per-market, depth, per-order dollars, per-window dollars, total dollars and the **shared window limit** all hold. Under one contract means refuse. It returns `{ allowed, count, cost, cid, reasons }`.

**Kill rules.** Per strategy, evaluated on its own final non-hand results by `killCheck`, in settlement order (`settledAt`, which the wiring writes beside the settle, else `ts`), and sticky: the strategy is killed if ANY prefix of that history trips a rule (N consecutive losses, or net below a threshold after N fills), so a late win cannot un-kill it. Only results on or after `reviewedAt` count, so a reviewed edit that moves `reviewedAt` also re-arms a streak or net kill. When one fires, the wiring writes a latch (`kalshiSlotControl/killed`, with `killedAt`) in the SAME transaction that records the settle. A latch blocks the strategy while `killedAt` is at or after the strategy's `reviewedAt`. **The only way back on is a reviewed code edit that moves `reviewedAt` later than the latch.** A latch that cannot be read counts as set. Stored data can only switch a strategy off, never on. The kill rules, caps and `SLOT_ENABLED` all fail closed, in the same spirit as the paused series and the probe drop rule.

## 4. The shared risk budget, as pure functions

The contract the later wiring must honour, with exact names:

- **Window cap.** `slotWindowSpent(slotOrders, ticker)` (also `slotRiskForL1(...).windowSpent`) returns the slot's gross dollars in that ticker's window, using the same terms as `runL1Tick`'s `windowUsed`: `maxCost` of orders with status `filled`, `sending` or `unknown`, whether or not later sold or settled; any order with fills counts, whatever its status. A sold position still occupies its window. This gross figure, NOT the at-risk dollars (`openAtRisk`, informational only), is what feeds `windowUsed`. The wiring adds it to L1's `windowUsed` so `room = L1_WINDOW_CAP_FRACTION * sizeBase - windowUsed` shrinks. The slot's own check does the mirror image: it subtracts L1's spend (excluding L1's add-on) from the same `0.055 * sizeBase`. A window fraction larger than L1's is refused. A gate pins the mirrored constant and `windowKey` to the live ones.
- **Loss stop.** `slotRiskForBotRisk(slotOrders, since)` returns **the same shape `botRisk` returns**: `{ net, openCost, worst, addonAtRisk: 0, trades }`. `net` is the realised slot result since `since` (hand-closed orders left out, as everywhere), INCLUDING the sold share of an order still open, so a stop-out is a loss the moment it is sold; `openCost` counts every unsettled slot order as lost (in flight in full; with fills for the contracts not yet sold, whatever the status). The accounting mirrors `botRisk` line for line (a parity gate runs the same fixtures through both); the deliberate differences are fail-closed: an unreadable `maxCost` is assumed to be the per-order maximum, an exit or settled loss with no readable pnl is booked as lost, and an order with no readable `ts` counts inside every window. The slot exit engine must record a completed early sale with `slotSettledFields(order, "exit")` (`settled: true, result: "exit"`, realised `settledPnl`) plus `settledAt`, like L1's exit watch. The wiring changes `runL1Tick` to use `risk = botRisk(...) + slotRiskForBotRisk(...)` field by field, so the 12% of `sizeBase` stop sees both. A slot loss therefore ends the whole session (and L1 with it), which is the owner's "one budget". The slot adds no add-on.
- **Settlement parity.** `slotSettledFields` equals `settledFields` for the same inputs (pinned by a gate), so a slot result and an L1 result sit on one footing.
- `slotRiskContract(slotOrders, now)` gives the full figures the guards read: open total, open per window, open contracts per ticker, the 24 hour and lifetime nets.

## 5. Orders

**Collection.** Slot orders live in `kalshiSlotOrders`, never `kalshiLiveOrders`. The L1 exit watch (`runExitWatch`), the settle sweep, `foldSkim`, `exitWatchIdle` and the push alerts all select `strategy === "L1"` from `kalshiLiveOrders`; a different collection means the L1 exit watch **cannot** sell a slot contract by accident, and the slot engine cannot touch an L1 one. Slot documents carry `strategy: "SLOT"`, `slotId`, `step`, plus the same money fields as an L1 order (`count`, `fillCount`, `maxCost`, `status`, `settled`, `settledPnl`, `exitCount`, `exitProceeds`) so the pure functions above read them unchanged. `foldSkim` (the size pool) filters on `strategy === "L1"` and must keep ignoring them: slot profit is not reinvested into L1 size.

**Client order id.** `slotClientOrderId(strategyId, ticker, step)` = `S-{ID}-{TICKER}-{step}`. It derives only from things both instances compute identically, never from `randomUUID()` or a time. The document id in `kalshiSlotOrders` is that same string, and creating it is the atomic claim (it fails if present), exactly like `createTest(cid, record)` for L1. Kalshi's own uniqueness check refuses a second send. It cannot collide with `L1-...`, `X-...` or `FLAT-...`. A step that did not fill (`no fill`, `error`) is not retried under the same id; the scale-in rule permits one attempt per step.

**Slot exits.** Immediate-or-cancel closes only, built by the existing `exitBody` (side `ask` to close YES, `bid` to close NO), with id `slotExitClientOrderId(orderId, tries)` = `SX-...`, never `X-...`. A lost answer ends the session, as for L1. Never retried. Before any slot sale:

1. `claimClose(store, ticker, "slot", now)` (the shared `kalshiLiveClosing/{ticker}` lease) is taken **before** the position is read. If L1's exit watch or Flatten holds it, the slot does nothing this time. `claimClose` allows the same holder to retake it, so the later wiring must give the slot its own `who` and keep instances apart by an atomic claim on the order document (like `claimExit`).
2. The position is read after holding the lease.
3. `slotSellCount({ order, position, haveClaim, othersUnsold })` returns `min(own unsold filled contracts, contracts the account holds on that side minus othersUnsold)`, where `othersUnsold` is the unsold contracts of L1 and of the slot's other orders on that ticker, and **zero** unless the order is `filled`, unsettled and has unsold contracts (settled, hand-closed, errored and unfilled orders sell nothing), or if there is no lease, the position or `othersUnsold` is unreadable, the account holds nothing, or the account holds the **opposite** side. That is the rule that prevents a sale from opening the opposite position. An L1 order handed to it returns zero.
4. If total holdings are smaller than the sum of what all owners think they hold (a hand trade took some), each engine is still capped by the live position; the slot also stops opening new orders on that ticker and the discrepancy is shown, rather than guessing who lost them.

**Flatten.** `flattenAll` sells the whole account position per ticker, which includes slot contracts, and today never touches an order document. After the wiring, Flatten must (a) still sell the account's whole position, (b) then mark every slot order on those tickers as closed by Flatten (like a hand close: settled, no pnl, so it leaves the loss stop untouched but the realised loss is visible in the account), and (c) set the slot's kill latch so nothing re-enters afterwards. Flatten already takes `claimClose(..., "flatten", ...)` first, so a slot close cannot run at the same moment.

## Wiring checklist (for phases B to D; found in review; **wired in Phase B1 to B3, Oct 29, 2026, still switched off**)

Status: every item below is done and tested behind the one gate `slotActive`: `runL1Tick`, `botRisk`, `closedByHand`, `settleOpenOrders` and `flattenAll` in `functions/kalshiLiveLib.js` (B2); the engine and its settle sweep in `functions/kalshiSlotRunLib.js` (B1, `runSlotSettle` added in B3); the Firestore store, the direction lock transaction and the Flatten bookkeeping in `functions/kalshiSlotStoreLib.js`, called from `functions/index.js` only when `SLOT_ON` (B3); the rules (B3). The tests that were listed as having to move did not move: the golden call logs prove the deployed functions are unchanged while the slot is off. Not done: the page card, the alerts and any admission (phases F to H).

- `runL1Tick`: add `slotWindowSpent` (the gross figure, not `openAtRisk`) to `windowUsed` near `kalshiLiveLib.js` line ~934; read the slot collection, the position and the lock in ONE transaction with `createTest`; leave the `held` crypto check unchanged; run the slot AFTER L1's decision in the same tick and count the slot's spend only then (the slot already leaves `SLOT_L1_RESERVE` and takes at most half the cap, but order of evaluation still matters). Wrap every slot call in try/catch so a thrown error cannot abort L1's minute.
- `botRisk` (line ~677) filters `t.strategy === "L1"` and takes an `orders` argument: add a slot-orders argument or add `slotRiskForBotRisk` field by field. Slot orders need their own settle sweep (market result, `slotSettledFields`, `settledAt`, the kill latch in the same transaction).
- `closedByHand` must skip slot entry and exit order ids (and the slot sweep must skip L1's). `foldSkim` and `exitWatchIdle` must keep ignoring slot orders.
- Tests that will have to move at phase C: `test/kalshiL1Gates.test.js` (W1 to W5 window and stop numbers, any assertion on `botRisk`'s exact return or on store read counts), `test/kalshiL1MutationGates.test.js`, `test/kalshiHandSoldGates.test.js` (H5, H11 to H13), `test/kalshiExitGates.test.js` (E11 to E13, F6 to F8 if Flatten gains slot bookkeeping), `test/kalshiSettleGates.test.js`, `test/kalshiAccountGates.test.js`. The phase A inertness gate (nothing mentions the slot library, `kalshiLiveLib.js` untouched) is rewritten at phase C.
- Add the two-instance lock test (a fake store that serialises transactions) before any order can be sent.

## 6. What is not in Phase A, and the later phases

Not in Phase A: any exit engine, any change to `runL1Tick`, `botRisk`, `closedByHand`, the exit watch or `flattenAll`, any change to `functions/index.js`, any Firestore rule, any page card, any alert, any deploy, any admitted strategy, any switch turned on.

Each later phase is its own reviewed pull request with the owner's deploy, in this order:

- **B. Slot exit engine** (`runSlotExitWatch`, using `slotSellCount`, `SX-` ids, the shared lease, its own wake rule), tested with fake exchanges like `kalshiExitGates.test.js`.
- **C. Wiring into `runL1Tick` and `botRisk`**: the direction lock transaction, `windowUsed` plus `slotWindowSpent`, `slotRiskForBotRisk` added to the loss stop, `closedByHand` ignoring the other engine's sells, Flatten's slot bookkeeping. Gates: opposite side blocked in both directions, a slot loss trips the shared stop, the window cap is shared.
- **D. Wiring into `functions/index.js`**: the scheduled entry function, the store (`kalshiSlotOrders`, `kalshiLiveDirection`, `kalshiSlotControl`), deploy script, the security scan's allowance if any new endpoint is needed (none is planned).
- **E. Firestore rules** for the new collections (admin read only, no client write; `kalshiSlotControl` closed), with the rules gate. Done in B3.
- **F. Page card** (read only, Privacy-masked through `kalshiMoney`, no control that can change a slot) and its changelog line.
- **G. Alerts** (closes and stops only, like the existing push rules; a slot entry never buzzes).
- **H. The first admission**: one entry in `SLOT_STRATEGIES`, with its README pre-registration, forward read date and kill rules, and `SLOT_ENABLED` set to `true`, in its own pull request after a research survivor passes the bar (profit factor 1.5 or better in each of three windows after fees and deflation, with a named counterparty). That pull request is where the owner decides, not this document.

Until H, the second slot cannot do anything. The research session's candidate numbers do not change that.

## The invariants, as tests (`test/kalshiSlotGates.test.js`)

Inert module; switch alone does nothing; one bad entry refuses the registry; ten-plus out-of-bounds mutations rejected; opposite side blocked in both directions and in flight; lock, order list and position failures refuse; slot risk returned in `botRisk`'s shape; shared window limit; hard caps; slot-only loss caps; kill rules and re-arming; deterministic ids that cannot collide; own-contracts-only sales; mirrored constants equal to the live ones; live library untouched and no Firestore rule opened.
