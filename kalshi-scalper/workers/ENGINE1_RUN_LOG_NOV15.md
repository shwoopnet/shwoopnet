# ENGINE1 run log (Desk A, Nov 15, 2026). Facts only, no results.

- 2026-11-15 spec e058c128a; fixture 83e1b2d4f (entries f24bf3bd3316e114, hand-computed expected 650425d60b3ca6e6); Desk A core c8c215381, then d77da9420.
- DISCLOSED CHANGE after seeing the second build's printed figures: Desk A's core now rounds each entry's cash to 9 places (as the Testing Desk's core does), so a 1e-17 float residue is neither a win nor a loss (fixture entry E9 at h 0.02). Presentation only; no figure moved by more than 1e-9. Accepted by the Head (Nov 15).
- Void label: a held void is "void" in both builds (the Head's ruling).
- Agreement: both builds agree to 1e-9 on 11 entries at h 0 and 0.02 (n=1), nine n=10 totals and the hold-all aggregate.

- 2026-11-16 run 1 (archive and perps, B1, loader 850ac0e8): attempt 1 computed about 10 minutes and died with a TypeError (a tuple key) in the JSON dump, after compute and before any print; nothing was read from it and its partial output file was deleted unread. Only change: engine1_run.py now writes string keys for tried_by_series (f04e2cf0b); loader, driver, split, enumerator and core are the frozen files (850ac0e8, 87354dab, c1e6f3d9, e42ee1a4, 53317e4b). Attempt 2 is the run.
- 2026-11-16 PERPSCALP1 one read: Auditor B's CLEAN for the rebuilt reader (d7dd92cb, 3663e2e54) was queued 13:14:07Z; the run started about 13:17Z; the print's sha256 was committed (b4e75df56) before it was read.
