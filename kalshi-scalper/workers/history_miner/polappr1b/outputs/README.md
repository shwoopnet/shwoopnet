# Which build printed which file (History Miner, Nov 13, 2026)

- `madeup_compare.json` (14 rows) and `madeup_ext_compare.json` (63 rows): printed by d9f20c45 (Amendment 6 build), before the family read was added; they carry `skipped_by_cap` but no `family_read`.
- `madeup_ext2_compare.json` (82 rows): printed by d9f20c45; matched Refinement's scorer on every cell.
- `../real/POLAPPR1_REAL_HM.json`: d9f20c45, the single real-mode run (table 2e09bd5f), printed before seeing the first build's output.
- `../real/POLAPPR1_REAL_HM_F.json`: 28fe60ca, the same run with the Amendment 3 family read added; every cell equal to the file above. The recorded verdict (Head of R&D, 08:09Z) uses these labels.
