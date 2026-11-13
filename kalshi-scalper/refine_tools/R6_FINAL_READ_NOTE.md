# R6 final read, cutoff constants (written Nov 12, 2026, before the read)

- Tool: r6_final_fixed2.py --live (scratch; reruns the registered R6 questions: gold depth-sum, OICORE trigger depth, W10, W12). It is a descriptive tool, not a new test.
- CUTOFF CONSTANT: the Nov 12 13:00Z run reads recorded R6 days through 2026-11-11T23:59:59Z only. Days after that are not read in this run.
- The FINAL complete read is the rerun after the recorder ends (it stops itself from 2026-11-13T23:59Z): earliest 2026-11-14.
- READ-ONCE MARKER: R6 FINAL READ NOT RUN as of 2026-11-12T03:40Z.
- Known gaps: short days on quote-data (10-29 partial, 10-30, 10-31, 11-02, 11-09 have one block fewer); coverage.csv.gz not checked.
- Cost: --live pulls public Kalshi candles for about 239 markets (about 17 minutes at full speed); under the current 25 reads an hour that is about 10 hours of the whole shared budget.

Dated line Nov 13, 2026 (Head of R&D ruling on the owner poll, text only): the R6 recorder now runs to Dec 31 by the code on main (checked by the History Miner), so "the recorder ends" in the lines above is no longer 2026-11-13. NAMED CUT registered now: the R6 final read, whenever it is made, reads recorded days through 2026-11-13T23:59:59Z only (the cutoff constant), not later days; it is not made before the Head of R&D gives the word, and the stale reminder for 2026-11-14T01:00Z was deleted. The marker stays: R6 FINAL READ NOT RUN.
