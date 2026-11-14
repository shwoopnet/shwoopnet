# SOCDERIV stage 1 counts on SOCDERIV_LISTS: record (History Miner, Nov 13, 2026, about 08:25Z)

- **Gate.** The run `pull/SOCDERIV_LISTS/2026-11-13T0806Z_43390567279` was opened on the Testing Desk's 08:17Z message, which said Auditor B's structure check had passed. The History Miner did not have Auditor B's check itself; the Head of R&D's record (08:15Z) is that the Testing Desk had not opened the run and was waiting for that check. If the check had not passed, this second build opened the run ahead of it (standing rule 16). Counts only, no price, no result field.
- **First print replaced before any comparison.** The first print found no BTTS leg in any of the 723 games with a derivable kickoff, because the reader looked for the made-up layout's `-YES` suffix and the real tickers end in `-BTTS`. Reading R16 (the BTTS leg is the one market of event `KX<LG>BTTS-<GAMEKEY>`, the series file's words) was added and the counts re-printed (`real/SOCDERIV_LISTS_COUNTS_HM.json`, commit 2980f5de). The Head ruled the same reading at 08:21Z; Desk B writes it into the registration.
- **Disclosure.** The second print's figures were sent to the Testing Desk (copy the Head) at about 08:19Z, before the Head's 08:21Z ruling that they go to no one until the Testing Desk has printed. The Testing Desk says its counts were committed at 47c3b1f1 before that message; the comparison is against that commit.

## Dated line, 2026-11-14 ~01:00Z: two candle runs (A and B), and hm_guard (written before the code change)
- The landed candles are two runs: SOCDERIV_CANDLES_A (requests c0000 to c0106) and SOCDERIV_CANDLES_B (c0107 to c0213), from the committed job files on main. The reader takes one candle folder, so:
  - The candles argument may name several folders, comma-separated.
  - Each folder must be whole for ITS OWN job (load_run as before), and their answers are merged by request id.
  - A request id present in two folders STOPS ("request id in two candle runs").
  - With --job files, the order is the lists job, then one job per candle folder in the order given.
- hm_guard.refuse_all runs on every path argument before anything is opened (pending since Nov 13; now added).
- Nothing in the measure changes.
- **Expected by hand:**
  - (1) made-up case_01, with its candle run split into two folders by request id (first half, second half) and given as "A,B", prints EXACTLY outputs/case_01.json;
  - (2) the same split with one request id copied into both folders stops;
  - (3) every one of the 23 made-up cases printed through the one-folder path is unchanged.
- **Addendum, 2026-11-14 ~01:00Z (Auditor B's two additions; written before the code):**
  - (4) a market ticker asked in two DIFFERENT candle folders, even under different request ids, STOPS ("ticker in two candle runs");
  - (5) the merged answers are ordered by request id, so giving the folders as "B,A" prints exactly what "A,B" prints, and both equal outputs/case_01.json for the split case;
  - (6) with --job files, a count other than 1 + the number of candle folders stops. A lone lists job, which zip used to accept, now stops.
  - The single-folder path is byte-unchanged.
- **Checks run on the change, 2026-11-14 ~02:30Z (made-up data only):**
  - before the change, all 23 made-up cases through one folder printed exactly the committed outputs;
  - after the change: case_01 split into two folders printed exactly outputs/case_01.json, both as "A,B" and as "B,A";
  - the split with one request id in both folders stopped "request id in two candle runs: c0000";
  - the split with one of A's tickers asked again in B under a new id stopped "ticker in two candle runs";
  - all 23 cases through one folder printed exactly the committed outputs again;
  - hm_guard read the list 974f2713 on every run.
