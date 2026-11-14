# FOMCTEXT build 1: the one count run (2026-11-14), on the Head's GO (06:24Z)

- Time: 2026-11-14T06:25:23Z to 2026-11-14T06:25:24Z, exit 0. Run once.
- Reader: fomctext.py sha256 28e55c3f1d14be008fdb7a31f6802889ad285ede4b59f8d577c9c7bcf9811880 (commit 5ad4a4c2, Amendment 5, Auditor B CLEAN 02:41Z).
- Guard: hm_guard.py c0b7826e; list HELDOUT_PULL_RUNS.md sha256 e0cb5fc5cdcedb270cd0df9608e995db5bb183a7bd508bd9e8e4976eaee8eae0, equal to origin/main at run time (it adds OICAND runs; no FOMCTEXT run is listed).
- Table: Desk C's STATEMENT_WORD_TABLE.csv (claude/idea-desk-c), sha256 493e6d6aa58a824fa63a0d7ad7666ba111b95585bd3afebcb6a359cbd2c2b38e.
- Lists: pull/FOMCTEXT_HIST_A/2026-11-14T0022Z_43533675204, job FOMCTEXT_HIST_A.json from main, sha256 6b79651769c6e115c64585f74f1b6e752e180b5d3fff6f8df42c2d55a41df7e4, equal to the run's embedded job.
- Candles: pull/FOMCTEXT_CANDLES/2026-11-14T0147Z_43542605086, job FOMCTEXT_CANDLES.json from main, sha256 636c0b7eb2547c47785d8378c4e34b0cfa7f5e2e070124db1cb3dcb5f5e466aa, equal to the run's embedded job.
- Command: python3 -I fomctext.py count <table> <lists job> <candles job> --lists <lists folder> --candles <candles folder>, from outside the data folder.
- Print: FOMCTEXT_COUNT_PRINT_2026-11-14.json, sha256 c374aee5761dd0ec577f541ce917d9d5135b4992b4d89a3d9eb0d57b4df6fde7. Committed before reading it and before seeing build 2's.
