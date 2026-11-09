# Strategy lifecycle spec (draft, Nov 9, 2026)

Owner priority, Nov 9, 2026: full time algo trading with a system that constantly rotates strategies in and out by pre-set pass rules and kill rules, instead of one slow read every 90 days. This file is a SPEC. It changes no trading code and nothing in it is live. Sections 2, 3 and 5 come from the research chat (V2) and 4 from the live refinement chat; the code plan, the automation line and the Charter change are the chief of staff's. Profit factor (PF) means gross wins over gross losses, net of fees, on a cash basis (fill price plus fee), per the owner's Nov 9 format directive.

## 1. Stages

| Stage | What runs | Money at risk | Who moves it |
|---|---|---|---|
| 0 Research | History scans, registered before scoring, last third held out and read once | none | research chat |
| 1 Shadow | The rule runs on live quotes and only LOGS (what it would have bought, a `wouldFill` flag); no order | none | research or refinement chat adds a logger (a code edit, owner merges) |
| 2 Incubator | A slot strategy at tiny size (1 contract), a hard max loss each and one total cap for all incubator strategies | capped, a few dollars to tens of dollars | owner merges the registry edit (today) |
| 3 Live | A slot or L1 strategy at its size ladder, inside the slot and account caps | the account's caps | owner merges |
| 4 Retired | Latched off; its orders still settle and are sold if open; its record stays in the report | none | automatic (kill rule) or owner |

## 2. Pass rules (promotion)
_To be filled from V2's input (minimum trades, cash PF, held-out half, deflation count and z bar by number tried, minimum days)._

## 3. How much evidence each stage needs
_To be filled from V2's input (fills needed to tell PF 1.5 from 1.0 at 80% power, cheap tail versus favourite, which strategy classes are judgeable in days)._

## 4. Kill and demotion rules, capital rules
_To be filled from Refinement's input (rolling N PF floor, consecutive loss latch, drawdown, the gold tripwire decay test; false kills against real failures on gold and OICORE; size per stage; step up rules)._

## 5. Multiple testing control for a rotating system
_To be filled from V2's input (promotion budget per quarter, alpha spending, how a retired strategy's record counts toward N)._

## 6. What can be automated, and what the Charter would have to allow

The line the code already draws, and the spec keeps: **nothing stored can add a strategy or enlarge one.** The registry (`SLOT_STRATEGIES`, `SLOT_HOLD_ALLOWED`) is a hard list in code (`functions/kalshiSlotLib.js`); a stored value cannot add or loosen anything, and CLAUDE.md treats that as a safety rule, not a convenience. So:

- **Automatic and safe (pre-authorize): KILL and DEMOTE inside caps.** A strategy that trips its numeric kill rule is latched off with no human step. This already exists for the slot (`killRules`, the sticky latch `kalshiSlotControl/killed`, `killCheck`; only a reviewed edit that moves `reviewedAt` re-arms it). It can only reduce exposure. The new part is more rules (rolling N PF floor, decay test) and a demotion that lowers size by a step before it latches off.
- **Automatic but must stay human (do not pre-authorize): PROMOTE.** A promotion means a registry or size edit in code. The spec makes the system do everything up to the merge: a nightly scorer that decides a strategy has met its pass rules writes a promotion packet and opens the pull request, and the owner's "merge" plus the deploy is the final step. This keeps "the owner is the one final say on whether anything goes live" (Charter, "The goal").
- **A middle option the Charter could allow, if the owner wants more speed:** the owner pre-approves, in advance and in writing, a bounded class of promotion: stage 1 to stage 2 only, 1 contract, hard max loss under a stated dollar figure each, one total incubator cap, a fixed number of promotions per quarter. The chief of staff may then merge that class of pull request on the nightly scorer's packet (the standing merge permission already exists for "merge" said to the Executive Assistant; this widens it to a pre-approved class) and the owner still runs the deploy. Anything above incubator size, any change to a live rule, size ladder, stop or market, and any favourite and hold structure stays with the owner each time. This is a Charter change and only the owner can make it.

## 7. Code needed on the existing slot framework

What already exists (read from origin/main, nothing to build): the registry and validator (`validateSlotStrategy`), per strategy kill rules and the sticky latch, slot dollar caps scaled to the sizing base (`slotCaps`), the shared 12% stop and 5.5% window limit, per strategy stop meters on the page (`kalshiOwnStops`), the skip log for strategies inside their entry span (`kalshiSlotSkips`, report `skips`), the order records and the nightly report with `slotOrders` rows. Missing, in build order:

1. **Shadow logger for any registered rule** (stage 1). A log only entry in the slot tick: for a rule that is registered as `stage: shadow`, write what it would have bought (ticker, side, price, size, `wouldFill`) to a new collection, never an order. Reuses the skip writer pattern; no new secret or endpoint.
2. **Stage field and incubator cap in code.** `stage` per strategy (shadow, incubator, live) in the registry, and one total incubator cap in code (a constant, never stored), checked in `slotOrderCheck` beside the existing per order, window, daily and lifetime caps.
3. **More kill rules.** Extend `killRules` with a rolling N PF floor and a decay test (the gold tripwire as code), and a demotion step (size down one step) before the latch. Each is a validator checked field with bounds in code.
4. **Nightly scorer.** A read only function (no Kalshi key, no write except its own report document) that reads the order rows, computes cash PF per strategy and window, runs the pass and kill rules and writes a lifecycle report: who passes, who is near a kill, who is dead. It never changes a strategy; a promotion proposal is a pull request drafted by the chief of staff from its output.
5. **Page.** A Lifecycle table on the Bot page (stage, trades, cash PF, distance to kill), percentages and PF only, Privacy view safe.
6. **Deploy order.** As always: exit watch (`deploy-push.sh`) before the minute function (`deploy-sizing.sh`), then the report (`deploy-report.sh`); `deploy-latest.sh` picks them.

**Pull request plan (four small PRs, each its own merge, so one bad hour ties to one change):** (a) shadow logger and `stage` field, inert; (b) incubator cap and extended kill rules with tests; (c) nightly scorer and report section; (d) Lifecycle table on the page. Each ships with a gate test stating the consequence (for example: "a strategy that trips its rolling PF floor is latched off and no order follows"), and the off equivalence fixtures must stay byte identical until a strategy is admitted.

## 8. Honest risks

- **More rotation means more false positives.** At a bar of PF 1.5 and a hundred rules tried, something clears it by chance; the Charter's own record says 17,500 generated strategies produced none at the bar. The control is the promotion budget and the deflation count in section 5, and every retired strategy counts toward N.
- **More rotation means more fees.** A one contract favourite slot is mostly fee (a 1c fee on an 8c win); an incubator that spends fees on ten candidates burns about $1 to $3 each for a read that is mostly noise. Budget fees as the price of a test.
- **Fast markets judge fast and also lie fast.** A 15 minute market gives hundreds of fills a month, but a favourite strategy with a 7% loss rate needs hundreds of fills to tell a 1.2 from a 1.0 (gold's own PF ran 4.4, 1.2, 0.9 in three periods on luck). Section 3 says how many fills each class really needs.
- **Auto kill can kill a good strategy on a bad draw.** The rules are calibrated on gold and OICORE's real histories (section 4) and a killed strategy can be re-armed only by a reviewed edit.
- **The limit is the edge, not the machinery.** Nothing we tested has PF 1.5 after deflation. A faster rotation system finds out sooner that a candidate fails; it does not create a strategy that works.
