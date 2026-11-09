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

## 2. Pass rules (promotion), from the research chat (V2), 10 contract fees, cash PF

| Step | Rule |
|---|---|
| Shadow (paper, no money) | at least 150 fills, at least 10 days, PF 1.3 or better net, held out third untouched |
| Shadow to incubator (1 contract, cap $20) | at least 400 fills for a cheap tail strategy or 600 for a favourite strategy, at least 20 days, PF 1.5 or better on the held out half, deflated one sided z at or above the quantile for 0.05 divided by N tried (z 4.3 at N 5,000; z 5.4 at N 1.5 million, our count today) |
| Incubator to live | at least 300 more incubator fills at PF 1.3 or better and a positive sum after fees; size steps up only on new evidence (+300 fills per step) |
| Live kill (stated here, calibrated in section 4) | trailing 100 fills PF under 0.9, or cumulative loss over the stage cap; latch off, no automatic restart |

## 3. How much evidence each stage needs (V2)

Fills needed to tell a true PF 1.5 from a null PF 1.0 at 80% power, by entry price (win rate: 15% at a 10c entry; 29% at 20c; 95.6% at 93c; 93.6% at 90c):

| Bar (z) | tail 10c | tail 20c | favourite 93c | favourite 90c |
|---|---|---|---|---|
| alpha 0.05 | 388 | 222 | 610 | 439 |
| deflated 3.1 (p 0.001) | 970 | 555 | 1,526 | 1,099 |
| 4.0 | 1,471 | 841 | 2,314 | 1,667 |
| 5.4 | 2,446 | 1,399 | 3,846 | 2,771 |

At today's live rates (gold about 9 fills a day, all 15 minute markets about 30 a day), 388 fills is 43 days on gold alone and 13 days across all 15 minute markets. **Fast to judge:** 15 minute and hourly crypto, metals and indices (days to two weeks for 400 fills across markets). **Slow:** sports (game days only; the NFL pair had 12 dates, a season is about 17 per team). **Slowest:** daily strategies (one decision a day; PF 1.5 needs about two years).

## 4. Kill and demotion rules, capital rules
_To be filled from Refinement's input (rolling N PF floor, consecutive loss latch, drawdown, the gold tripwire decay test; false kills against real failures on gold and OICORE; size per stage; step up rules)._

## 5. Multiple testing control for a rotating system (V2)

Total alpha 0.05 per year; a budget of 4 promotions per quarter (each spends alpha 0.05 divided by 16, about 0.003, ahead of its z bar). Every hypothesis ever scored stays in N forever: a retired strategy's whole search counts, not only its winner. No re-scoring a failed candidate on the same data. Held out thirds are read once.

**Honest read on our own record (V2).** Fed with what we had, the rules would have PROMOTED on in sample PF: gold L1 (PF 4.28 over its first 97 fills), OICORE (PF 2.28 in discovery, 1.85 in validation), and Bitcoin, Dogecoin and XRP L1. Live: gold 1.21 over 307 fills but 4.28, then 1.26, then 0.88 across periods; OICORE 1.11 (77 fills); Bitcoin 0.72; Dogecoin 0.82; XRP 0.41; all settled L1 PF 0.94 (-$24.40 on 1,008 fills). A kill rule of trailing 100 fills PF under 1.0 would have retired XRP, Dogecoin and Bitcoin in about 4 to 12 days and saved most of -$49.99. But with only 1 of 8 live markets positive, automatic rotation mostly rotates fees: expect a false positive rate near 80% of promotions at our evidence levels.

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
