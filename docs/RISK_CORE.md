# Risk core spec v1 (phase P1: written as pure functions, inert, not wired)

`functions/kalshiRiskCoreLib.js` holds the rules below as functions and constants. Nothing in `functions/` or the page imports it, it requires nothing, and a gate keeps it that way. Wiring it in is a later, reviewed phase (P5 and P6 of the scalability plan) behind its own switch. Percentages are of the sizing base.

## Account layer
- Window ceiling: 8 percent of the base across all seats in one 15 minute window (gold's one contract reserve sits inside it).
- Open money: 12 percent of the base, at most $150.
- Stops budget: the sum of every live seat's maximum loss must be at or under 30 percent of the base. This is the seat admission gate (`admitSeat`).
- Already in code, named only: the 40 percent account floor (`functions/kalshiHardStopLib.js`, `docs/HARD_ACCOUNT_STOP.md`) and the 12 percent daily stop (`RISK_PROFILES` in `functions/kalshiLiveLib.js`).

## Seat layer, per tier
| Tier | Contracts | Order cap | Daily cap | Maximum loss |
|---|---|---|---|---|
| Trial | 3 | $3 | $9 | its net floor minus $18 (a floor of zero is $18) |
| Full | 10 | smaller of 2.5 percent and $20 | smaller of 2.5 percent and $20 | $60 drawdown from its own peak since (re)start |
| Proven (above 10) | its own ladder | smaller of 2.5 percent and $20 | smaller of 2.5 x contracts, 6 percent and $75 | smaller of 5 x contracts, 12 percent and $150 |

A 1 contract probe uses the Trial caps at one contract and the Trial maximum loss. A seat's window budget is its own order's worst case cost (contracts x top price + fee); the fee function is a parameter.

## Allocation when a ceiling binds
Deterministic: tier priority Proven, Full, Trial, then probes; inside a tier the longest live record first (never highest profit factor), then the id. Each seat in turn gets its full order if it fits the window ceiling, the open money cap and its own caps; otherwise it is sized down to what is left. Under 1 contract it sends nothing: skip reason `window_ceiling` when the shared ceilings stopped it, `seat_cap` when its own caps did, `unknown_tier` for a tier the table does not know. The result depends only on the input list, so two instances agree.

## The Risk Analyst's answers R1 to R7 (constants and pure functions in the same library)
- R1, cached seat peak and drawdown: a cache may only REFUSE an order, never allow more than a replay would. A cache older than 3 minutes, unreadable or dated in the future means that seat sends nothing (`cachedSeatGate`). A full re-replay runs at least daily (`replayDue`); if the replay is worse than the cache the seat latches until the two agree and a critical item is logged (`auditCache`).
- R2, an unclear order answer: it quarantines ONLY that seat, counts its worst case (maxCost) as lost in every stop until resolved, and blocks that market for every seat until resolved. The whole session ends instead if the unclear answer is on a sell or exit, or if 2 or more seats have unclear answers within 60 minutes (`unclearAnswerDecision`).
- R3, per market across seats: the sum of contracts is at most 30 (`MARKET_CONTRACT_CAP`) and each order at most 25 percent of the touch size (`marketOrderContracts`; an unknown touch sends nothing). Opposite sides of one market are never allowed and the first seat in holds the direction for that window (`directionAllowed`). Seats are evaluated in priority order (Proven, Full, Trial, probes; longest live record first); a seat waiting on a feed runs last.
- R4, order budgets over a rolling 24 hours: 40 per seat (`SEAT_ORDERS_PER_DAY`, gold as the L1 seat has its own listed value of 60) and 300 per account as a runaway check that ends the session (`ACCOUNT_ORDERS_PER_DAY`). These replace the old 200 order cap when wired. Functions take a list of order times.
- R5: L1 is just another seat in the priority order and gold counts as the Full tier while under review. The one contract L1 reserve inside the 8 percent window ceiling exists only while gold is armed, none while latched (`goldReserveContracts`).
- R6, ladders: OICORE keeps its own ladder (20, 25, 30) as the written exception. Every other strategy that reaches Proven uses one generic ladder: 10, then 15 at a $1,000 base, 20 at $1,350, 30 at $2,000 (`genericLadderStep`), with OICORE's step tests (15 fills over 5 days, profit factor 1.3, net at least 1 x contracts, drawdown under 3 x contracts; `ladderStepTestsPass`) and the same down-steps. Once OICORE meets the proven bar it moves onto the generic ladder at its current size.
- R7, up-moves (a new Trial admission counts as one): at most 2 a day account-wide, each only if the 30 percent stops budget still fits after the move; a 24 hour cooling gap on the seat that moved and 6 hours account-wide after any up-move (`upMoveAllowed`, given a move log and now). Down-moves, stops and kills are never limited and are immediate.

## Rulings noted
- H3: a Trial seat that earns first and then gives it back is stopped only at a net of minus $18. That is a known difference from the lane's section 5 drawdown wording; it is not a loosening, since $18 from the start is the cap either way.
- H4: the 5 seat cap in the rotation and wheel libraries is removed only together with the stops-budget gate in code (that is the later controller pull request).

## Fail closed
An unusable base makes every ceiling zero. A bad size, price or fee makes an order cost infinite (nothing is sent). An unknown tier has an infinite maximum loss (never admitted). No input can raise a cap.

## Readings chosen where the spec was ambiguous
- "Net floor minus $18": the floor is a zero or negative net result in dollars, so the maximum loss is its size plus 18; a missing floor counts as zero.
- Probes: no separate row in the spec, so they use the Trial limits at one contract.
- Proven daily cap: kept as written (2.5 x contracts, 6 percent, $75); the Proven order cap equals Full's.
- Seat's own open contracts: counted against its tier's contract limit, so a seat cannot stack past its own size.
