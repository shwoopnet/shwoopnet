# CMD4 registration: break-even fee map per metal, energy and index perp (2026-11-06, before any score)

Shared rules: `workers/CMD_COMMON.md`. Development part only (sessions 2026-10-30, 11-02, 11-03; held-out sessions never read). 12 cells (N +12): 6 pairs times the two primary rules, CMD1 R1 at H = 15 and CMD1 R2 at H = 5, with the CMD1 trigger definitions unchanged.

**What it computes.** Per pair and rule: trades, gross after the recorded spread and before fee (bp), break-even fee per side = that mean divided by 2, hit rate, net at 5, 12 and 24 bp a side. A cell with under 10 trades is printed as n only and carries no break-even.

**Mechanism / why.** The 12 bp a side placeholder is the whole question for these perps; the map shows how much fee each instrument could stand if the rule had an edge, and whether the cheapest instruments (gold 0.47 bp spread, US 500 0.95 bp) are the ones with any.

**Prediction.** Every break-even fee is under 3 bp a side (pairs with spreads of 4 bp or more, copper and WTI, under 1.5 bp), no cell reaches the 12 bp placeholder, and the cheapest pairs have too few trades (under 10) to print. **Verdict:** a map, not a LEAD: each cell is NOT_ENOUGH_DATA unless 60 trades on 15 clusters, which needs the forward sample (about 2026-12-04, then as CMD1). A cell showing a break-even fee above 12 bp a side would be listed as a lead for the forward read only, never as a pass.
