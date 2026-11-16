# NBAREB: the NBALADDER search on the rebounds ladder (Idea Desk C, Nov 16, 2026; engine family spec; the Head of R&D's order of 17:20Z; written before any price is pulled)

**Question.** The same one as NBALADDER, on a different stat: among the rebounds rungs (KXNBAREB) of one game, does any simple rule on timing, rung position, price, recent move, spread, volume or rung age earn more than it costs? The 624 cells, features, gates, unit and print are exactly NBALADDER's (`../nbaladder/NBALADDER_CARD.md`), run by the same audited plugin: `engine/nbaladder_reb.py` changes four module constants (series, list job, list id, candle jobs) and nothing else.

**Why rebounds.** From the census listing of Nov 9 games (ticker and event counts only, no price): rebounds 389 markets in 8 games (48.6 a game), threes 351 (43.9 a game), assists 249 (31.1 a game). Rebounds has the most rungs after points, so the best chance of 3 signals a day. Rebounds' total traded volume was also the largest of the three (Desk B's listing). Threes and assists are possible later specs.

**Uniqueness and flags.** Same as NBALADDER. PROPS1 (closed Nov 16) listed KXNBAREB; this spec is a different question and a different window. It is a **version** of NBALADDER on a new market (7g), so it counts toward the owner's 5 at PF 1.3+ but not the unique list, and the search is only worth running because rebounds' prices could differ from points' (more role-driven counts). Not cheap-side, not lead-lag, not parity, not market making.

**Clock.** Time to the scheduled END (occurrence), with the same clock check (one value per game, exactly on :00 or :30, else the game is dropped and counted).

**Rules this spec tries: 624** (3 times x 4 bands x 2 sides x 2 exits x 13 filter options), all counted in m.

**Gates, unit, label.** As NBALADDER: 3 signals a day (48 trades on 16 days) as a filter on the printed table, then n 100 or more, 40 or more games, 10 or more trade days, PF 1.3 or more at the primary haircut with both halves 1.0 or more, 2c PF 1.0 or more, Benjamini-Hochberg over m. Unit: the game; z and p from game-level sums. M10 with no mark is counted and held to settlement, printed both ways. Label: "development; candle replay, upper bound, not fill-checked". Dollars a week at 5 contracts rank the rules that clear the gates.

**Windows, as epochs.**
- Development: KXNBAREB closes **1792540800 (2026-10-21) to before 1793923200 (2026-11-06)**.
- Never pulled: closes 1793923200 to before 1794528000 (2026-11-13).
- Validate: closes **1794528000 to before 1796342400 (2026-12-04)**, pulled after Dec 4, read once on the Head's go, **in the same joint print as NBALADDER and SIBHIT-R (three families, one m)**.
- **Holds to confirm (Auditor B):** PROPS1 held KXNBAREB 2025-26 and a frozen part from 2026-10-03T16:00Z, and is now closed. Whether its frozen part is released for this window is Auditor B's hold map. The list job's heldout line says so. No other card on KXNBAREB is known to me (the registry names PROPS1 only).

**Independence.** The development days are the days SIBHIT and the NBA fade and follow cards read for points. Rebounds' prices on those days were never read. The census listing gave counts only.

**Data.**
- `KXNBAREB_LISTS_A`: 1 list request, up to 8 pages, closes 1792540800 to 1793923199.
- Candle jobs `NBAREB_CANDLES_P1` and `_P2` are built from that list by `engine/build_nbareb_candles.py` after it lands and passes Auditor B's structure check. Same windows and sizes as NBALADDER: about 120 games, about 125 requests, two files.

**Prediction (numeric, before any read).** The same as NBALADDER's: under no edge the best of 624 cells reaches PF 1.15 to 1.30 by luck on 16 days; P(a rule clears every gate on development and holds on the joint read) about 4%. If NBALADDER and NBAREB both produce a development winner with the same cell, that agreement is the only evidence worth a second look; I will say so before I read either.

**Kill fast.** No rule with 48 or more trades and PF 1.3 or more at 1c with both halves 1.0 or more, or nothing survives BH.
