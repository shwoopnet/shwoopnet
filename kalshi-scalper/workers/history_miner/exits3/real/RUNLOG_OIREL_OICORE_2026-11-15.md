# EXITS3: the one run of OIREL and the OICORE rule history (2026-11-15 15:53:48Z), on Auditor B's CLEAN (15:53Z) under the Head's lighter paper gate

- Code: exits3.py f3f05e17 (commit 7b65f72e); spec efe0df91; hand case 4a897d20. Exit 0 for both.
- Data: Forensics' OIREL_extract.sqlite.xz (claude/forensics-desk 31351c1b), xz sha256 53f2f8c32b829bc39ce2c647898926eef4a8a3f1fa2ca804895a0a36e6322250, sqlite sha256 53b5e677114635c6...: KXBTC15M, closes 2026-08-06 00:00Z to 2026-10-02 23:45Z (XOI1's W3 from Oct 3 cut). Candles after a close dropped.
- Guard list HELDOUT_PULL_RUNS.md c561184a (equal to main). Touched: only the extract above (decompressed in scratch) and this repo's code.
- Prints, committed before reading: EXITS3_OIREL.json sha256 eaad8940e55a5026c2e3a2a741f2af8bf28a6fc29f63cb46023d2b5d98b4511b; EXITS3_OICORE.json sha256 849b8bf235c460050b4c55d5bf01d2736e4772a3969d4f3905e33c12b5f8b3c6.

**Read these with the prints (Auditor B's conditions):**
1. **OICORE here is the RULE HISTORY as FALS4 defines it** (src/scalper/fals4.py on the research branch, as I read it: doi > 86,299.56, cheap side 0.05 to 0.50, fill at the -120 ask, 10 contracts). It has NO 8c floor (the live OICORE floor is 8c), so it is NOT live-comparable.
2. **Both cards enter at the candle ending 120 s before the close.** The only exit mark is the candle ending 60 s before the close, so T and S measure that ONE candle. M (at 180 s) is before entry and is empty by construction: every M row is "M n/a, held", equal to hold.
3. **The primary haircut is 2c (C8):** entry and exit in the last 2 minutes. 0 and 1c are printed too.
4. **C1 was added** (signal and fill candles two-sided); the "not_two_sided" count is in each print.
5. This is information on the same cut-window data. A pass is not a verdict: it needs a second build and Auditor B's CLEAN under 16b. Upper bound, not fill-checked; per-order rounded fee at 10 contracts.
