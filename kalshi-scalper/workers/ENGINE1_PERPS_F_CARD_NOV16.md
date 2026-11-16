# ENGINE1-PERPS-F: the forward card for the perps block (Desk A, Nov 16, 2026; the Head's order). Frozen before any further read.

**What is frozen:** the rule grid and every setting of ENGINE1_PERPS_AMENDMENT_NOV16.md and ENGINE1_PERPS_HAND_CASE_NOV16.md (21 filters x 2 sides x 10 exits = 420 rules per name; haircuts 0.02% and 0.05% a side as the gate, 0.1% and 0.2% as a stress line that never gates; taker fee 12 bp (the gate) and maker 5 bp (flagged), both ASSUMED; funding booked, a print missing from the extract leaves a trade out of the gates; the boundary clip and cooldown by hold; the 10 trade day floor; one-sided day-clustered p; Benjamini-Hochberg at 5%), the code at these hashes: engine1_perps.py 175a7ccd8eb26c6b, engine1_split.py rewritten only by the dated note below, engine1_extract_load.py eded8ea1 (a new loader build for the later extracts needs its own line from Auditor B), engine1_perps_run2.py ba3cbcfd. A change to any of them before the read is a new, dated amendment, written before the read.

**Names:** SPY and QQQ (a third look at their days, the earlier two zero reads counted), US 500 and US Tech 100 (a second look), gold once its 1 minute candles exist (a first look).

**One read.** It is made when EVERY name read has at least 10 SEARCH and 10 VALIDATE trading days with funding complete, about Dec 1 to 5. A trading day is a UTC date with a funding print and at least 300 one minute candles. Until then nothing is scored: a count-only check of the days (dates, candle counts, funding print dates; no price, rate or result) is allowed. No rerun in between; each rerun would add tries.

**Split:** the SEARCH and VALIDATE dates are rewritten from the new extracts' distinct trading dates (the first floor(D/2) dates SEARCH, the rest VALIDATE; D at least 20) in a dated note, with the extract's candle-end dates, BEFORE the read.

**Denominator:** m = 2,184 (read 1's 504 + pass 2's 1,680) + the new rules of this read (420 per name read: 1,680 for the four names, +420 with gold), printed before any result. Each name's earlier days stay in its SEARCH; the new days are fresh; the read says which result rests on days read before.

**Outputs and bars:** as the amendment: combos tried and m, SEARCH passes, VALIDATE passes after BH, funding-unbooked count, taker and maker lines (a maker-only pass flagged "assumes resting fills; fill rate unknown"), the stress line apart, avg hold and gross move per cell. Any survivor needs a second build and rule 16b before anyone acts, then the account-size table (percent of the account only) and the 1x, 2x, 5x, 10x leverage table under Kalshi's margin rules (read from Kalshi's pages first); a perps survivor is information for the forward shadow only.

**Kill:** if the read finds no survivor, ENGINE1-PERPS-F is closed as FALSIFIED for this grid; a new grid would be a new card.

**Count to date for this block:** 504 (read 1) + 1,680 (pass 2) = 2,184 tries, 0 passes, both plumbing reads (3 to 4 SEARCH days).
