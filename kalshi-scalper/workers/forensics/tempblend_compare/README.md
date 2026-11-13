# TEMPBLEND: the two builds compared on both invented row sets (Forensics desk, Nov 13, 2026; research only; no data, no Kalshi request)

Build 1: Desk C's `tempblend_score.py` sha256 `90227da8...` at `7c02c838` (`claude/idea-desk-c`), rows `test_rows.json` `2682931e`, watched `test_watched.json`, expected `12f32a04`.
Build 2: the History Miner's `tempblend2.py` `3fab82b3...` at `848fd4ae` (`claude/history-miner`), rows `rows_madeup.jsonl` `d1b1a989`, `expected_by_hand.json` `79dafadd`, `out_madeup.json` `ef217362`.
Card `658817e9` (sha256 `32112a10`), Amendment 1 (A1 to A18). All hashes were checked against the Head's message before running.

Run: `python3 -I map_and_compare.py <dir with c/ files> <dir with m/ files> <out dir>`. The script maps each row set to the other build's layout without changing a value (its docstring lists every
mapping choice) and compares the decision of EVERY city-hour (skip reason class, side, strike, ask, fee, pnl, void, member, calibration day) and the aggregates both outputs share. `outputs/` holds the
mapped row files, both builds' full outputs on both sets, and `COMPARE_OUTPUT.txt`.

Result: see `COMPARE_OUTPUT.txt`. Control: each build reproduces its own committed expected output exactly on its own set (build 1 on set 1 equals `test_expected.json`; build 2 on set 2 equals `out_madeup.json`
apart from its card line); and a deliberately changed copy of build 1 (spread 0.025, gap 0.55) is caught by the comparer on both sets.
