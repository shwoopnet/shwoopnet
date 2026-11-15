# ENGINE1 run log (Desk A, Nov 15, 2026). Facts only, no results.

- 2026-11-15 spec e058c128a; fixture 83e1b2d4f (entries f24bf3bd3316e114, hand-computed expected 650425d60b3ca6e6); Desk A core c8c215381, then d77da9420.
- DISCLOSED CHANGE after seeing the second build's printed figures: Desk A's core now rounds each entry's cash to 9 places (as the Testing Desk's core does), so a 1e-17 float residue is neither a win nor a loss (fixture entry E9 at h 0.02). Presentation only; no figure moved by more than 1e-9. Accepted by the Head (Nov 15).
- Void label: a held void is "void" in both builds (the Head's ruling).
- Agreement: both builds agree to 1e-9 on 11 entries at h 0 and 0.02 (n=1), nine n=10 totals and the hold-all aggregate.
