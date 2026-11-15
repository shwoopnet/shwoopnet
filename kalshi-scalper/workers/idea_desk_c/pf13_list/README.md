# Independent PF 1.3 list (Idea Desk C, Nov 15, 2026, for the Head of R&D; the owner's item 2) [research]

**What this is.** Every tested card, rule or cell whose PRINTED result shows cash PF 1.3 or better with both halves 1.0 or better. Status is not a filter: closed, retired, falsified and not-new cards are all included.
- Lines are copied, never recomputed.
- Research results only; live account figures were excluded wherever recognised.

**Scope.**
- `claude/epic-ptolemy-0amjd9` (V2): 327 result files. The 138 that print some PF of 1.3 or more were read in two parts:
  - reader A: `kalshi-scalper/studies/`;
  - reader B: `kalshi-scalper/workers/`.
- Reader C: idea desks A, B and C, `claude/refine-live`, the History Miner and Forensics, plus the combo, politics, weather and event cards. That is 180 files.

**Files.**
- `QUALIFYING.csv` (50 rows): overall PF 1.3 or more and two printed halves each 1.0 or more.
  - Where a file prints thirds, the first two thirds stand in for the halves (BAND2, MKTTIME1), and the third is in the verdict column.
  - Three rows use a reader's judgement about which two blocks are the halves: EXITREPLAY1's D and H blocks, and W-OIGAP1's two periods. They are marked in the `window` and `half` text.
- `HALVES_NOT_PRINTED.csv` (296 rows): PF 1.3 or more with no half PFs printed. Many are sweeps (IDEAS20 and 100, PERPGEN, GEN4, USWEEP null halves).
- `WINDOWS_ONLY_NO_OVERALL.csv` (130 rows): two windows each 1.3 or more, but no overall PF printed. Examples: GEN6 and GEN7 survivors, SLOTEX variants, FALS3 and FALS4, EVT1, POLAPPR1, sports calibration cells.
- The `reader` column (A, B or C) says which pass found the row. The `source` column is branch:path:line, or a JSON key path.

**Not done.** No figure was re-derived, no verdict was changed, and a row's appearance here is not a pass or a recommendation. Many rows are diagnostics, controls, favourite-and-hold shapes the owner has banned, or falsified at their own bar. Read the verdict column.
