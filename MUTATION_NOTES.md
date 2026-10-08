# Mutation check of `functions/kalshiLiveLib.js`, 2026-10-08

Method: single-line mutations applied by hand (a script) to a scratch copy: stop thresholds, size rounding, window edges, price and limit rounding,
band edges, balance and shard checks, create-first, halt, unresolved, expiry, order limit, the ambiguous-answer rules, `botRisk`, order body
fields, production-host check. Each was run against `kalshiL1Gates`, `kalshiLiveGates`, `kalshiSignalGates` and `kalshiAccountGates`.

First pass: 58 mutants listed, 9 not applicable because the line occurs in both the single-order path and the L1 path (49 run, 39 killed, 10
survived). Second pass: those 9 lines mutated one occurrence at a time (17 runs, 14 killed, 3 survived). Total 66 runs, 53 killed, **13 survived**.
Nine of the 13 were real gaps and are now killed by `test/kalshiL1MutationGates.test.js` (M1 to M8):

| Survivor | Why it mattered | Gate |
|---|---|---|
| stop `<=` became `<` | down exactly the stop amount would not have stopped | M1 |
| size `floor` became `round` | 1.75 contracts of budget would have bought two | M2 |
| window edges moved 30 s and 60 s | the 330 to 400 s window was untested at its edges | M3 |
| committed cash ignored when sizing | two markets on one shard could both take the full share | M4 |
| `strategy === "L1"` filter removed | an older single test order would feed the L1 stop | M5 |
| unreadable balance row treated as zero | a half-readable balance would be trusted | M6 |
| `enabled !== true` loosened | a truthy non-true switch value would pass | M7 |
| 2xx reply without `order_id` counted as sent (L1 path) | a malformed success would be booked as an order | M8 |

Left as equivalent mutants (cannot change behaviour): removing the `$2` per-contract cap check (a contract in the 88c to 97c band costs
under $1.00, so it cannot trip); removing `Number(t.fillCount) > 0` in `botRisk` (a zero fill pays and costs zero); `availableFor` returning
`Infinity` instead of `0` for a missing shard (the next check treats a non-finite balance as unreadable and refuses, so it refuses either way).

Not covered: the same 2xx-without-`order_id` mutant on the older single-order path (`runLiveTest`). That path is not called from the page
(see `REVIEW_NOTES.md` on `claude/condense-review`), so it was left.
