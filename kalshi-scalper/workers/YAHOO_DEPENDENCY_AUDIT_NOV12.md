# Yahoo dependency audit of the perp / overnight / cash-gap work (V2, Nov 12, 2026, 00:25Z; requested by Desk A through main)
Yahoo Finance is BARRED for all research (owner, Nov 11; terms clauses 2(d)(9), 2(e), 2(d)(10), `workers/YSPOT1_TERMS.md`). Audit by grep of the registrations and results; no Yahoo file was opened.
| Test | Rests on Yahoo data? | Evidence | Status now |
|---|---|---|---|
| CMD1, CMD2, CMD3 | YES | cash1m / futures Yahoo 1 minute bars (`workers/CMD_COMMON.md`) | marked barred (cb7177a3); CMD3 retired; do not extend |
| STOCKPERP (SPLAG1, SPHALT1, SPAUCT1 and any test using `cash1m/`) | YES | `STOCKPERP_REGISTRATION.md` line 7: "Cash: origin/perp-data:cash1m/<date>.csv.gz (Yahoo 1 minute bars incl. pre and post)"; SPHALT1 infers halts from Yahoo gaps; `STOCKPERP_RESULT.md` counts missing Yahoo 1 minute bars | results rest on barred data; not to be extended; a replacement needs a permitted cash tape or the perps' own halt fields (`halt_sources`, `schedule.is_open` from the same list call, STOCKPERP_DESIGN item 3) |
| CASHGAP1 | planned on Yahoo 5 minute bars, NOT run | registration: "Cash reference: Yahoo 5 minute bars"; result: NOT_ENOUGH_DATA, "No Yahoo bar was fetched" | no Yahoo data used; Yahoo version must not be run |
| CASHGAP2 | no Yahoo reference found by grep | uses the recorder's own `reference_price` (OVN_COMMON line 9: "every test below uses the recorder's own reference_price"; a Yahoo version is NOT_RUNNABLE) | not marked; keep to reference_price |
| OVN1, OVN2, OVN3 | no Yahoo found by grep | same shared file (OVN_COMMON) | not marked |
| OVN5 | forward read would use "later cash1m files" | `OVN5_REGISTRATION.md` line 9 | must NOT use cash1m; amend to reference_price only, or retire (descriptive instrument; 100 trade bar not reachable until mid 2027) |
Also (Desk A's note): overnight perp tests must treat an ex-date reference drop as offset by the cash dividend payment (long receives, short pays, per Kalshi's help page, `EXDIV1_GATE0.md`), never as P&L. Any test that scores an overnight or gap return on a dividend stock around its ex-date must exclude or adjust that day.
Not audited: files I could not grep for 'yahoo' or 'cash1m' (other perp-data derived tests by Refinement or Desk B); the owner's stop on the REF recorder's Yahoo reads is a PR in preparation (main).
