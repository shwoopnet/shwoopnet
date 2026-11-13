HISTORY (Nov 13, 2026, owner ruling): this note predates the privacy scrub; lines marked "[live figure removed, ask Main]" are blank on purpose. Read it as history, not as a current rule.

# Review of docs/STRATEGY_RISK_SEPARATION.md (PR 689), with the SCALE_STEP review folded in (Nov 1, 2026, 7: [live figure removed, ask Main]

Requested by main at the owner's direction. [live figure removed, ask Main] Dollars are after fees. [live figure removed, ask Main]

## (1) Each strategy on its own, from the live record

| | L1 gold + Dogecoin | L1 all markets since Oct 7 | OICORE |
|---|---|---|---|
| Settled fills | [live figure removed, ask Main] |
| Losses | [live figure removed, ask Main] |
| Largest single loss | [live figure removed, ask Main] |
| Worst rolling 24 hours | [live figure removed, ask Main] |
| Worst UTC day | -$7.34 (Oct 27) | -$19.95 (Oct 10) | -$2.45 |
| Worst losing streak (orders in a row) | [live figure removed, ask Main] |
| Spend per order (cost of contracts) | [live figure removed, ask Main] |

[live figure removed, ask Main]

[live figure removed, ask Main]

[live figure removed, ask Main] [live figure removed, ask Main] This is enough to size a small probe, not to set a scaling rule.

## (2) Are the draft numbers sensible?

[live figure removed, ask Main]

| Draft parameter | My read | Why |
|---|---|---|
| OICORE own stop 4% of base | [live figure removed, ask Main] |
| OICORE own window cap 2% of base | [live figure removed, ask Main] |
| L1 12% stop, 5.5% window cap | [live figure removed, ask Main] |
| Account backstop 15% stop, 6.5% window cap | [live figure removed, ask Main] |
| OICORE size one per $50 of base, floor 10, ceiling 30 | [live figure removed, ask Main] |
| Step: up to 3 per 3 days, only after 30 settled fills net at or above zero | [live figure removed, ask Main] |
| Kill rules: 18 losses in a row; floor -$0.60 a contract | [live figure removed, ask Main] |

## (3) What a 10-loss streak costs OICORE (28% win rate, so 10 losses in a row is 3.7% from any one start; **within 100 trades it is 67%**, within 40 trades 32%, within 250 94%)

| Contracts | [live figure removed, ask Main] |
|---|---|---|---|
| 10 | $9.6 | $16.9 | $51.7 |
| 20 | $19.1 | $33.9 | $103.5 |
| 30 | $28.7 | $50.8 | $155.2 |

[live figure removed, ask Main] [live figure removed, ask Main]

## (4) Recommendation, parameter by parameter

1. [live figure removed, ask Main]
2. [live figure removed, ask Main] [live figure removed, ask Main] That is acceptable as a tripwire for a probe, but it should be a choice, not a surprise. [live figure removed, ask Main]
3. [live figure removed, ask Main]
4. [live figure removed, ask Main] Steps down at once when either fails. Do not let any step happen before the Nov 13 read.
5. [live figure removed, ask Main]
6. [live figure removed, ask Main]
7. **Account backstop:** 14% to 15% stop and 6.5% window cap are both fine. [live figure removed, ask Main]
8. [live figure removed, ask Main]

## What this can and cannot support
- [live figure removed, ask Main] They support a small probe with a streak tripwire, and the arithmetic of what a streak costs, which does not depend on the sample.
- [live figure removed, ask Main]
- [live figure removed, ask Main]

## Count for deflation
[live figure removed, ask Main] No edge claim anywhere here.
