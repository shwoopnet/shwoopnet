# COMBODONE stage 1, second build (History Miner, Nov 13, 2026)

From Idea Desk C's card only (`claude/idea-desk-c` 593597e6, `COMBODONE_CARD.md`, Amendments 1 and 2) and Desk B's `INPUT_LAYOUT.md` (`claude/idea-desk-b` 22c2f47a; layout and output names, no values). Desk B's `combodone.py`, `HASH_NOTE_NOV13.md`, `fixture_outputs/` and the generator were NOT opened. Zero tries; a count; no combo-data file opened. `outputs/case_NN.json` are this build's prints on Desk B's eleven MADE-UP cases, committed BEFORE any comparison with Desk B's outputs. [research]

Usage: `python3 -I combodone2.py count <combo dir> <legs run dir>`.

## Readings this build had to choose (sent to Desk B and Idea Desk C; the card is Desk C's to amend)
1. Rows with an empty or cut leg string are counted apart, BEFORE the six not-eligible reasons (Desk B's layout field 3/4 order).
2. An unreadable quote row (no receive time or no ticker) counts toward the week if its receive time is in the week or, with no receive time, if its run folder's day is.
3. A run is completed if ANY coverage row of the folder has stopped_early 0 and the folder has a quotes file.
4. The week search walks consecutive UTC days from the first folder day; a day with no folder has 0 runs; the week's last day must be earlier than the latest folder day (point 10).
5. "Settled at t" is settlement_ts at or before t; "60 seconds before" is settlement_ts at or before t - 60 (60 s counts, 59 s does not).
6. A leg asked for but absent from every answer is "leg unknown"; a leg string part with no yes/no side is "leg unknown"; a non-integer `legs` is "leg unknown".
7. The refusal (point 16) tests only legs named in WHOLE leg strings of week rows against the tickers the leg job asked for.
8. The leg pull is not whole if: the manifest status is not "complete"; a 200 row is truncated or has no file; a job request has no 200 answer; or a request's last 200 page has a cursor.
9. "First eligible snapshot with a resting ask" is by receive time, then by run folder order; the median is over listed asks in cents, rounded to two places.
10. The book figure uses the same run folder's books file, matched by ticker.

## Final version (Nov 13, 2026, about 02:55Z), to the card through Amendment 5 (`claude/idea-desk-c` b0cb5a9e)
- Amendment 3 (b8317f4b) and Amendment 4 (c6dc2630) matched this build's readings already; one fix from Amendment 4 point 20: a `legs` value that is not a whole number (for example 2.5) is "leg unknown" (it was read as 2). None of the eleven cases' figures changed.
- Amendment 5 fingerprint, printed first with the number of files: sha256 of sorted lines "path<TAB>size<TAB>sha256 of the stored file's raw bytes" for every regular file at any depth under a top-level YYYY-MM-DD folder; a symbolic link anywhere there makes the count refuse (tested). It is computed before anything else is read.
- The finding that led to Amendment 5: under the path-and-size wording, cases 01 and 09 printed the same fingerprint while 735 files differed in content and the verdicts differed; under Amendment 5 they differ.
- `outputs/case_NN.json` now carry `fingerprint` and `fingerprint_files`; every other figure is identical to the compared set at 37332937 (same as Desk B on all 64 blocks).
