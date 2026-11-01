# Separate risk, sizing and scaling per strategy (design draft, Nov 1, 2026)

The owner (Nov 1, 2026): "each strategy can have different risk, sizing, and scaling parameters, dependent on its PF and its win rate", "L1 and OICORE should be completely separate with risk scaling". This is a DESIGN DRAFT. Nothing here is built, nothing changes live until the owner approves the numbers and each step ships as its own reviewed pull request.

## Where the two strategies are tied together today (read from the code)

| Coupling | Where | Effect |
|---|---|---|
| One loss stop | `botRisk` (`kalshiLiveLib.js`) adds the slot's net and open cost to L1's (`slotRiskForBotRisk`); the stop is 12% of L1's sizing base plus the add-on allowance | An OICORE loss can trip the stop that ends L1's session, and a bad L1 day shrinks OICORE's room |
| One session | The slot tick runs right after the L1 tick and needs the figures it hands over (`shareOut`); with none it skips ("no shared risk figures from the L1 tick") | When L1's stop ends the session, OICORE stops too |
| One window cap | L1's room is 5.5% of the sizing base minus everything in the window, OICORE's spend counted (`slotWindowSpent`); the slot may use at most half of it (`SLOT_WINDOW_SHARE`) and leaves $1.05 for one L1 contract | OICORE can take room from gold or Dogecoin in the same window, and the reverse |
| One sizing base | `sizeBase` comes from L1's review (balance minus skimmed profit); the slot's dollar caps are fractions of that same number (`slotCaps`) | OICORE's caps move with L1's review timing |
| One size source | OICORE's size is the fixed `contractsPerOrder: 10` in its registry entry | No ladder, no step, no link to its own record |
| Profit pool and add-on | L1 only (`foldSkim`, `skimAddon`, `addonCap`) | Correct: leave it that way |
| Kill rules | OICORE has its own latch (18 losses in a row, net under -$6 after 40 fills); L1 has none | Fine as is, but the dollar floor does not scale with size |

Deliberately NOT separated (keep shared): the direction lock (an order against another strategy's contracts is a hedge), the exit claim per market, the account balance read and the order size lock's role as a last guard. These are about one account, not about one strategy's risk.

## Proposed shape: a risk profile per strategy, plus one account backstop

Each strategy gets its own profile, kept in code (never a stored value or a page setting, same as today):

`{ sizing: how contracts per order are set, scaleStepMax: most contracts added per 3 day review, ownStop: loss stop measured on THIS strategy's orders only, ownWindowCap: money at risk in one window for THIS strategy, killRules }`

The account backstop stays and covers both: a combined stop (one number above each strategy's own) and a combined window cap. A strategy's own stop halts only that strategy; the backstop halts everything, as the loss stop does today.

### Why different numbers (from each strategy's own record)
- **L1** (gold, Dogecoin): wins about 92% to 95%, a win pays about 6c a contract, an early sell loses about 66c. Risk is the size of one loss, so size is set from the loss budget (one early sell should stay under about 1.1% of the base: -$8.70 was 1.1% of $779) and the 12% stop and 5.5% window cap stay as they are.
- **OICORE** (Bitcoin): wins about 28% to 30%, a win pays about 3 to 4 times its cost, a loss is the whole premium (6c to 50c a contract). Risk is the length of a losing streak, not one loss: size so a 10 loss streak costs no more than a set share of the base, because at a 28% win rate 10 losses in a row happens about 3.7% of the time and 18 about 0.3%.

### Draft parameters (for the owner to change)
| | L1 (as now unless noted) | OICORE (proposed) |
|---|---|---|
| Size rule | one contract per $43 of base, add-on capped at a quarter of base | one contract per $50 of base (gives 10 at today's base), floor 10, ceiling 30 until a reviewed edit |
| Step up | draft: up to 3 contracts per 3 day review (now 1) | up to 3 per 3 days, and only if the last 30 settled fills are net at or above zero |
| Step down | within 2 hours of a lower balance | at once if that test fails or the base falls |
| Own stop | 12% of base, L1 orders only | 4% of base, OICORE orders only (about 10 full 10-contract losses at 30c) |
| Own window cap | 5.5% of base | 2% of base (the slot's per window cap today) |
| Kill rules | none (loss stop only) | 18 losses in a row; net floor becomes -$0.60 a contract (-$6 at 10) |
| Account backstop | combined stop 15% of base, combined window cap 6.5% of base | same two numbers, shared |

The backstop numbers are my starting point, not a finding: today's 12% stop and 5.5% window cap bind both strategies together, so the backstop must be at least as loose as the larger of the two own limits and tighter than their sum.

## What exists in the database and code to build on
- L1 sizing state (cap, base, saved, pool) lives in the L1 sizing document; OICORE has no sizing state and needs its own document (new, admin read, no client write, like the other control documents).
- Slot orders are already separate (`kalshiSlotOrders`, `strategy: "SLOT"`), so a per-strategy stop and window cap can be computed from each collection without a migration.
- The page's risk meter already counts both; it would show each strategy's own stop used and the backstop.

## Build order (each its own pull request, deployed by the owner with `deploy-sizing.sh`)
1. This design, reviewed with the refinement chat (read only): loss sizes and window use from the live record, for both strategies.
2. Per-strategy stop and window cap in code with the defaults set so today's behavior does not change (the off-equivalence fixtures must stay byte for byte, and any re-record happens only from main's own code).
3. OICORE size ladder and step rule, behind the Nov 13 forward read or 30 settled fills, whichever comes later (10 fills and 3 wins so far, and V2's forward reference ledger is 0 for 6).
4. L1 step from 1 to 3 per review, after the refinement chat's review.
5. Page: per-strategy risk meters.

## Risks to say plainly
- Faster scaling makes the next loss bigger sooner: one early sell at 20 contracts is about -$13, at 24 about -$16.
- Separate stops mean the combined worst case can be larger than today's single 12%, which is why the backstop stays.
- OICORE's record is too small to set a size from. Its rules are a probe's rules until the forward read is in.
