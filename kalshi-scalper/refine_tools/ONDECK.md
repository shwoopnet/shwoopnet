# On-deck shadow candidates (live side), current as of 2026-11-10

Basis: cash, PF per contract, fee unrounded (matches live avgFee), hold to settlement. N tried for deflation about 770. Bonferroni z about 5.2 is unreachable at these n, so every rule below is a SHADOW candidate, never a pass. Shadow rows assume a fill at the touch (upper bound): read wouldFill. Sources: REFINE_STATUS.md Nov 9 to Nov 10 entries, SHADOW_REGISTRATIONS_WEEK1.md.

## Registry (PR 753: [live figure removed, ask Main]

| id | [live figure removed, ask Main] |
|---|---|---|---|---|
| GOLDALL | [live figure removed, ask Main] |
| GOLDHI6S | [live figure removed, ask Main] |
| XRPFAV6 | [live figure removed, ask Main] |
| XRPYES10 | [live figure removed, ask Main] |

Independent means a window not used to pick the rule (gold Aug 13 to Sep 1 covers 1,358 of 2,153 listed windows; Aug 6 to 12 and earlier not reached; [live figure removed, ask Main] XRPFAV6 [live figure removed, ask Main] [live figure removed, ask Main] [live figure removed, ask Main]

## Pass and kill rules (common, from the lifecycle spec, set before any forward row)

- [live figure removed, ask Main]
- [live figure removed, ask Main]
- Counterparty: none named for any rule.
- [live figure removed, ask Main]

## Retired before their first forward row

- [live figure removed, ask Main]
- ETHL1: candles 0.90 (361) / 0.75 (383) at +0c, 0.77 / 0.64 at +1c.
- [live figure removed, ask Main]
- BTCHI10 (and XRPFAV10): dropped before merge. BTCHI10 independent window 1.27 (66) / 1.05 on the 78 percent pull, later 1.584 (n 83) / 1.304 on the full pull, but V2's Jun to Aug run had 0.90 (n 289) on overlapping months, so it is contested; do not re-add on this alone.

## Closed lists (do not re-run without a new reason)

- [live figure removed, ask Main] Best cells about 1.0 to 1.07.
- [live figure removed, ask Main]
- W-SUPPLY1: untested public series, L1 structure, 0 of 54 pass. [live figure removed, ask Main] [live figure removed, ask Main]
- Hourly ladders (KXGOLDH, hourly strikes): not testable with the data held. KXGOLDH ladder (25,391 strikes) not pulled; G3H1 pass is VOID (universe look-ahead).
- [live figure removed, ask Main] Ethereum paused in code.
- [live figure removed, ask Main] Consistent with EXIT1.
- [live figure removed, ask Main] NOT_ENOUGH_DATA, swung 0.74 / 1.07 / 1.59 as n grew.

## Still hunting

Needs data, not a result: see SUNDAY_SUPPLY_DRAFT.md.
