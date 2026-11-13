# resting2 on Refinement's edge set v2 (Nov 13, 2026): SAME

Build: resting2.py fe1e4ab5 (ae3cafe4). Rows: claude/refine-live ffd9b829, refine_tools/v1v2_cross_compare/edge_set/v1edge2 and v1edge2_signals.csv, V1 development block (test clock and temporary markers). Printed BEFORE opening expected_by_hand_v2.json (96ab50c7). No scorer or script of Refinement's opened.

- Counts: 8 signals, 8 orders, 6 filled, 2 not filled, 2 crossed_quote (the crossed and the locked window). Hand file: the same.
- version PF25 1.343031, parent PF +1c 1.243031, +0c 1.306466, missed parent PF 1.443031; net per contract-week version 0.110002, parent +1c 0.125044, +0c 0.152425; weeks 3. Hand file: the same to 6 places.
- Bar (1) MET (diff 0.09999999999999987, under the 1e-9 tolerance), bar (2) NOT MET, bar (3) MET (finite: second half 0.345812 against first -0.738726), missed test TRUE; verdict NOT_ENOUGH_DATA (FALSIFIED OR, information only: true). Hand file: the same.
- Mutation TOL = 0 (scratch copy): bar (1) NOT met and the missed test FALSE; nothing else moves. Hand file's strict compare: the same.
- Mutation sort by close only (scratch copy): bar (3) NOT met (second half 0.100887 against first 4.149760); nothing else moves. Hand file's close-only figures: the same.

## Rule 18 on every book row (Nov 13, 2026)

Build: resting2.py with the scope change (this commit). Rows: 7072ec1c (one crossed later row added to KXBTC15M-U0L). Hand expectation ca51fa54 (scope_ruling_row): U0L stays NOT FILLED, every figure unchanged. Result: SAME: 6 filled, 2 not filled, 2 crossed_quote, version PF25 1.343031, parent PF +1c 1.243031, missed 1.443031, all bars as before. Discrimination: the previous build (ae3cafe4) fills U0L on the crossed row and reads 7 fills, version PF25 1.214771, missed PF inf, bar (1) NOT met; my own W11 case (inv/v1cross) fills under the previous build and does not under this one.
