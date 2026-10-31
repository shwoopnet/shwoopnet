# Amendment 1 to MAKER5 and L1Q1 (2026-10-31, V2 worker R6T; owner decision relayed by the main session)

Amends `workers/R6T_REGISTRATION.md` (commit 7d5917f). Written and pushed BEFORE any R6 data row was opened. The only R6 things looked at before this file: file NAMES (`git ls-tree`, as the AUTO readiness line does), the recorder source, the registration, and the scorer source. No row of `book.csv.gz`, `trades.csv.gz` or `coverage.csv.gz` under `book15r6/` on `origin/quote-data` has been read. The commit that contains this file is the one that precedes the first row opened; its hash is in the worker's report and in the README line of this amendment's follow-up.

## What changes

1. **Earliest read date UNCHANGED:** 2026-11-06 00:00 UTC (6:00 PM CT, Nov 5).
2. **NEW posted-order gate.** The single run of `run maker5` and `run l1q1` does not execute until at least **300 scored windows with an order posted exist for BOTH MAKER5 and L1Q1**. If the gate is not met on Nov 6 the run waits: the AUTO loop re-tries on each later pass, rather than the single allowed run being spent on an under-sampled test (which would end `NOT_ENOUGH_DATA` and burn the run). The existing refusals stay: before the date, under 300 usable windows, a second run. A refusal for the gate is not a run and does not count as the one run.
3. **Definition of posted (exactly as already registered, counted from PRICE fields only):**
   - MAKER5: a window in which the posting poll exists (the first poll at or after T-12 min, within 30 s of it), with a best YES bid and a best NO bid, YES bid below YES ask (YES ask = 1 minus the best NO bid), and a mid between 0.20 and 0.80.
   - L1Q1: a window with an L1 signal at the 6 minute look: signal poll S = the last poll at or before T-360 s, within 10 s of it, and exactly one side whose ask at S is 0.88 to 0.97 (YES ask = 1 - best NO bid; NO ask = 1 - best YES bid).
   - The counter reads only the book price and size columns, `close_time` and the coverage usability fields already registered. It never opens `trades.csv.gz`, never reads a fill, a settled `result`, or any outcome. (Usable-window counting from coverage already existed; "scored" here means usable by the registered coverage test AND posted. The L1Q1 usability test also requires a `result` of yes or no, as registered; the counter checks only that the field is present for usability, exactly as `count` already does, and uses it for nothing else.)
4. **Nothing else changes:** N is unchanged (the 18 tries already counted, running count about 439,124), and no rule, threshold, fee, size, queue model, bar, z bar, thirds or holdout changes. Prediction and kill criteria are unchanged.
5. **Nothing from R6 was opened before this amendment was pushed** (see the header; the commit hash is reported by the worker).
6. **The counts produced afterwards (`workers/R6T_COUNTS_2026-10-31.md`) are INFORMATION ONLY:** posted-order and signal counts per day per market, windows and coverage, and a projection of when each count reaches 300. They read no fill, no trade, no outcome, and no rate, net, PF, win or loss is computed or printed.

## Code

The gate lives in `src/scalper/r6tests.py` only (a price-rows-only counter, `posted_counts`, and a refusal in `run`), with `tests/test_r6_gate.py` on synthetic rows. The AUTO readiness line prints the two posted counts.
