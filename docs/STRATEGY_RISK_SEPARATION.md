# Separate risk, sizing and scaling per strategy (design draft, Nov 1, 2026)

**Status, Nov 3, 2026:** steps 2 (each strategy's own stop, no number changed) and 5 (the own stop meters) are built and live. Steps 3 and 4 and every number in the proposed parameter table below are still drafts; the live own stop for both strategies is 12% of the sizing base (`RISK_PROFILES`), and an L1 stop still ends the session, which also stops OICORE.

The owner (Nov 1, 2026): "each strategy can have different risk, sizing, and scaling parameters, dependent on its PF and its win rate", "L1 and OICORE should be completely separate with risk scaling". This is a DESIGN DRAFT. Nothing here is built, nothing changes live until the owner approves the numbers and each step ships as its own reviewed pull request.

## Where the two strategies are tied together today (read from the code)

| Coupling | Where | Effect |
|---|---|---|
| One loss stop (as it was before Nov 2; each strategy now has its own 12% stop plus the combined backstop) | `botRisk` (`kalshiLiveLib.js`) adds the slot's net and open cost to L1's (`slotRiskForBotRisk`); the stop is 12% of L1's sizing base plus the add-on allowance | An OICORE loss can trip the stop that ends L1's session, and a bad L1 day shrinks OICORE's room |
| One session | The slot tick runs right after the L1 tick and needs the figures it hands over (`shareOut`); with none it skips ("no shared risk figures from the L1 tick") | When L1's stop ends the session, OICORE stops too |
| One window cap | L1's room is 5.5% of the sizing base minus everything in the window, OICORE's spend counted (`slotWindowSpent`); the slot may use at most half of it (`SLOT_WINDOW_SHARE`) and leaves $1.05 for one L1 contract | OICORE can take room from gold or Dogecoin in the same window, and the reverse |
| One sizing base | `sizeBase` comes from L1's review (balance minus skimmed profit); the slot's dollar caps are fractions of that same number (`slotCaps`) | OICORE's caps move with L1's review timing |
| One size source | OICORE starts at `contractsPerOrder: 10` and steps up by its own record (`SLOT_LADDERS.OICORE`, built in #699) | Linked to its own record and the balance; no link to L1's steps |
| Profit pool and add-on | L1 only (`foldSkim`, `skimAddon`, `addonCap`) | Correct: leave it that way |
| Kill rules | OICORE has its own latch (18 losses in a row, net under -$6 after 40 fills); L1 has none | Fine as is, but the dollar floor does not scale with size |

Deliberately NOT separated (keep shared): the direction lock (an order against another strategy's contracts is a hedge), the exit claim per market, the account balance read and the order size lock's role as a last guard. These are about one account, not about one strategy's risk.

## Proposed shape: a risk profile per strategy, plus one account backstop

Each strategy gets its own profile, kept in code (never a stored value or a page setting, same as today):

`{ sizing: how contracts per order are set, scaleStepMax: most contracts added per 3 day review, ownStop: loss stop measured on THIS strategy's orders only, ownWindowCap: money at risk in one window for THIS strategy, killRules }`

The account backstop stays and covers both: a combined stop (one number above each strategy's own) and a combined window cap. A strategy's own stop halts only that strategy; the backstop halts everything, as the loss stop does today.

### Why different numbers (from each strategy's own record)
- **L1** (gold, Dogecoin): wins about 92% to 95%, a win pays about 6c a contract, an early sell loses about 66c. Risk is the size of one loss, so size is set from the loss budget (one early sell should stay under about 1.1% of the base: -$8.70 was 1.1% of $779) and the 12% stop and 5.5% window cap stay as they are.
- **OICORE** (Bitcoin): wins about 28% to 30%, a win pays about 3 to 4 times its cost, a loss is the whole premium (6c to 50c a contract). Risk is the length of a losing streak, not one loss: size so a 10 loss streak costs no more than a set share of the base, because at a 28% win rate a run of 10 losses is 3.7% from any one starting point but 67% likely somewhere in 100 trades (32% in 40, 94% in 250), and the 18 loss kill fires by chance 6% of the time in 100 trades at a 28% win rate (28% if the true rate is 20%).

### Parameters after the refinement chat's review (Nov 1, 2026; its note is `kalshi-scalper/REFINE_RISK_SEPARATION_REVIEW.md` on the refinement branch)
| | L1 | OICORE |
|---|---|---|
| Size rule | as now: one contract per $43 of base, add-on capped at a quarter of base | stays 10 until 100 settled fills AND the Nov 13 read; ceiling 15 (20 only by a reviewed edit at 250 fills) |
| Step up | keep +1 per 3 day review (the owner kept +1 on Nov 1; +2 only if insisted, never +3) | at most +2 per 3 days, and only after 60 settled fills net at least +1c a contract AND at least 20% wins |
| Step down | within 2 hours of a lower balance | back to 10 if the last 60 fills net under -$1 a contract |
| Own stop | 12% of base, L1 orders only | 4% of base (a proposal; live is 12%), OICORE orders only; at 15 contracts and a $540 base a normal 10 loss run can end it, so the kill rules and this stop are close together |
| Own window cap | 5.5% of base | 2% of base, plus a per-order dollar cap of 1% of base (it would cut the 39c to 50c entries, where the wins came from, at 25 or more contracts) |
| Kill rules | none (loss stop only) | 18 losses in a row, or net under -$6 after 40 fills (keep both) |
| Account backstop | combined stop 15% of base, combined window cap 6.5% | same two numbers, shared (14% would lose nothing) |

Reviewed facts behind these numbers (live record to Nov 1): L1 gold and Dogecoin 393 fills, 18 losses, largest loss -$9.58, worst 24 hours -$11.30 (1.5% to 2.1% of base), worst streak 2. OICORE 10 fills, 7 losses, largest -$1.70, worst streak 3, order spend median $0.70 and at most $4.50. OICORE shared a window with an L1 fill in 1 of its 10 windows, so today the coupling costs nothing in dollars and the separation matters for later scaling. A step gate of "30 fills net at or above zero" was too weak (a no-edge probe passes it 43% of the time in simulation, a real +5 point edge only 71%), hence 60 fills at +1c and 20% wins.

Cost of a 10 loss streak (review): at the median 9c entry, $9.6 / $19.1 / $28.7 at 10 / 20 / 30 contracts; at a mean 16c entry $16.9 / $33.9 / $50.8; at a 50c entry $51.7 / $103.5 / $155.2.

The backstop numbers were my starting point, not a finding: today's 12% stop and 5.5% window cap bind both strategies together, so the backstop must be at least as loose as the larger of the two own limits and tighter than their sum.

## What exists in the database and code to build on
- L1 sizing state (cap, base, saved, pool) lives in the L1 sizing document; OICORE has no sizing state and needs its own document (new, admin read, no client write, like the other control documents).
- Slot orders are already separate (`kalshiSlotOrders`, `strategy: "SLOT"`), so a per-strategy stop and window cap can be computed from each collection without a migration.
- The page's risk meter already counts both; it would show each strategy's own stop used and the backstop.

## Build order (each its own pull request, deployed by the owner with `deploy-sizing.sh`)
1. This design, reviewed with the refinement chat (read only): loss sizes and window use from the live record, for both strategies.
2. Per-strategy stop and window cap in code with the defaults set so today's behavior does not change (the off-equivalence fixtures must stay byte for byte, and any re-record happens only from main's own code).
3. OICORE size ladder and step rule: BUILT in #699 (Nov 6, 2026): steps 10, 12, 15, 20, 30, each earned on its own record and balance.
4. L1 step from 1 to 3 per review, after the refinement chat's review.
5. Page: per-strategy risk meters.

## Risks to say plainly
- Faster scaling makes the next loss bigger sooner: one early sell at 20 contracts is about -$13, at 24 about -$16.
- Separate stops mean the combined worst case can be larger than today's single 12%, which is why the backstop stays.
- OICORE's record is too small to set a size from. Its rules are a probe's rules until the forward read is in.
