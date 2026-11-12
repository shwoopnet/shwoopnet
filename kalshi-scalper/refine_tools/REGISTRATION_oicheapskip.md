# S-OICHEAPSKIP1: [live figure removed, ask Main]

Registered 2026-11-08, BEFORE any skip exists. Source: S/w_design_oi/DESIGN.md (OICORE_SKIP7, PR 742). Measure only: no rule, no order. Public GET only, no key.

## Group
Skip records with reason `cheap_skipped` and time at or after the deploy timestamp (argument, or the file DEPLOY_TS in this folder). Each has ticker, detail.price (the signal price: rounded-up cheaper-side touch) and, in the stored record, the side in `note`. [live figure removed, ask Main] Rows whose side cannot be found are counted "side unknown" and excluded, and a report change to carry the side is the fix. Before the deploy there are none: prints NOT DEPLOYED. Outcome: public GET /markets/{ticker} result. Win = result equals the side.

## Cash booking at 5 contracts (design section d)
paid = signal price. [live figure removed, ask Main] [live figure removed, ask Main] Also recorded: the deploy date, because OICORE's streak, kill and ladder win-rate inputs change from that day (cheap fills leave its record).

## Prior and multiplicity
[live figure removed, ask Main] Sim about 7 percent. About 420 earlier splits tried, so the group was picked after seeing data (selection bias). [live figure removed, ask Main]

## Decision (fixed now)
Read at 40 signals (about 10 days) and again at 80.
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- Otherwise extend to 80. [live figure removed, ask Main]
[live figure removed, ask Main]
