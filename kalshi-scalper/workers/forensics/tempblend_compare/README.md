# TEMPBLEND: the two builds compared on both invented row sets (Forensics desk, Nov 13, 2026; research only; no data, no Kalshi request)

Build 1: Desk C's `tempblend_score.py` sha256 `90227da8...` at `7c02c838` (`claude/idea-desk-c`), rows `test_rows.json` `2682931e`, watched `test_watched.json`, expected `12f32a04`.
Build 2: the History Miner's `tempblend2.py` `3fab82b3...` at `848fd4ae` (`claude/history-miner`), rows `rows_madeup.jsonl` `d1b1a989`, `expected_by_hand.json` `79dafadd`, `out_madeup.json` `ef217362`.
Card `658817e9` (sha256 `32112a10`), Amendment 1 (A1 to A18). All hashes were checked against the Head's message before running.

Run: `python3 -I map_and_compare.py <dir with c/ files> <dir with m/ files> <out dir>`. The script maps each row set to the other build's layout without changing a value (its docstring lists every
mapping choice) and compares the decision of EVERY city-hour (skip reason class, side, strike, ask, fee, pnl, void, member, calibration day) and the aggregates both outputs share. `outputs/` holds the
mapped row files, both builds' full outputs on both sets, and `COMPARE_OUTPUT.txt`.

Result: see `COMPARE_OUTPUT.txt`. Control: each build reproduces its own committed expected output exactly on its own set (build 1 on set 1 equals `test_expected.json`; build 2 on set 2 equals `out_madeup.json`
apart from its card line); and a deliberately changed copy of build 1 (spread 0.025, gap 0.55) is caught by the comparer on both sets.

## Third set: one row on each edge of the card (Nov 13, 2026; the Head's order of 15:21Z)

`edge_rows.py` builds 37 invented rows from the card text alone; `edge_hand_expected.json` holds the expected decision of each row, written BY HAND from the card and committed (`f731844c`) BEFORE either build was run on this set.
Three rows (E13, E14, T03) were added after the first run, because that run showed the original edges were not float-sensitive (a planted change of the tolerance to zero changed nothing); their hand expectations
were committed (`de0ce9be`) before they were run and the file says so. `edge_run.py` runs both builds and compares each row with the hand file and with the other build. Outputs: `outputs/edge/`.

**Result: ONE MISMATCH, reported, not fixed.** Row `T03_midpoint_tie_with_the_HIGHER_strike_nearer_in_floating_point` (v 70.7, s 69.1; strikes 69.5 and 70.3, both exactly 0.4 from the midpoint 69.9 on paper; in floating point
69.9 - 69.5 is 0.4000000000000057 and 70.3 - 69.9 is 0.3999999999999915). Card A7: two strikes equally near the midpoint within 1e-9 take the LOWER K. Hand expectation and build 2: K 69.5, ask 0.45, pnl +0.53.
Build 1: K 70.3, ask 0.55, pnl +0.43 (it sorts on the raw distance, then K). Every other row (36 of 37): both builds equal the hand file and each other. Aggregates on this set differ only through that row:
pooled development n 22 in both, PF 5.4873 against 5.550633, net 7.09 against 7.19 (build 1 against build 2); the verdicts are the same (CLOSED; held-out "no evidence at n = 2").
Controls: with the tolerance set to zero, or the gap line stripped of it, in a copy of build 1, the edge set now flags 5 and 4 rows against the hand file (it flagged none before E13, E14 and T03 were added).

## After Desk C's A7 fix (Nov 13, 2026; the Head's order of 15:26Z): SAME on all three sets

Build 1 is now `tempblend_score.py` sha256 `644770d9...` at `3619a351` on `claude/idea-desk-c` (the one changed line rounds the distance to 9 places before the tie-break; `test_rows.json` `2682931e`, `test_expected.json` `12f32a04` unchanged;
build 2 unchanged, `3fab82b3`). Re-run on both earlier sets and the full 37-row edge set: **no differing decision and no differing figure on any of the three** (edge set: 37 rows, 0 differences against the hand file in either build, 0 between the builds;
pooled development n 22, PF 5.5506 against 5.550633, net 7.19 in both; the T03 row now picks K 69.5, ask 0.45, pnl +0.53 in both; the only unrounded differences are each build's own rounding). The planted-fault control (tolerance set to zero in a copy
of build 1) is still caught (2 rows flagged). Outputs: `outputs/after_A7_fix/`. The earlier outputs (with the T03 mismatch) stay in `outputs/` as the record.
