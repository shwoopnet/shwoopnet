# RECORD1B: RECORD1's rule on a recorder with a clock check that measures what it claims (registered 2026-11-04, before any fixed-clock row exists or was read)

Worker RECCLOCK1. Research only; nothing here trades, nothing promotes.

## Why this exists
The RECORD1 read (2026-11-03, 300 trades, 13 dates, mean +3.81c, z 1.60, `clock_ok` False) is scored as written and is not edited or rerun. Its clock gate failed by a defect in the check, not by a drifting clock:
- `clock.csv` held 342 SNTP offsets in 60 runs (Cloudflare, one sample every 30 minutes, round trip halved). Median |offset| 5 ms, p90 13 ms, max 137 ms; 341 of 342 were 34 ms or less. Exactly one sample (run 2026-10-27/0225, 137 ms among 10, 4, 10) was over 100 ms (0.29%).
- `record1.py` takes `max(offsets)` per run and marks every trade of that run `clock_ok` False, then `clock_bad = any(...)`. So one lopsided UDP sample made 2 of 361 trades fail and the whole read fail. (A Date header is not involved; the recorder never used one.)
- The recorder fix (branch `claude/v2-recorder-clock`, commit f2ee344, not merged) keeps the least delayed of 8 samples per check and records `rtt_ms` and `version = clock2`; quote, spot and result rows are unchanged.

## What counts
Only runs whose `clock.csv` has a `version` column equal to `clock2` on every row (the fixed recorder). Older runs are never counted, whatever their date. A fixed-clock run with no answered sample is dropped and the drop is printed.

## Rule (unchanged from RECORD1, same code: `trade_for`, `p_yes`, `index_by_second`)
Index = median of Coinbase, Kraken, Bitstamp latest prices (5 s stale limit, 2 exchanges needed); normal model of the 60 s average, sigma from the previous 300 s of one second changes (100 changes needed); decision at the first poll at or after 60, 45, 30, 15 s before the close, earliest that qualifies, one trade per market; buy YES if p - ask - fee >= 0.03, NO if (1-p) - (1-bid) - fee >= 0.03; size on the bought side at least 5; fee 7% x p x (1-p) per contract (the code prices one contract, unrounded, as RECORD1 did; the C = 10 rounded fee of LAG15 is not used here); hold to settlement. Assets: BTC, ETH, XRP, SOL, and DOGE where it has trades (the 2026-11-04 look showed 5 assets with trades).

## Clock gate (the only change)
A fixed-clock run is `clock_ok` when the MEDIAN over its samples of |offset_ms| + rtt_ms/2 (the most the reading could be wrong by) is within 100 ms. A run with no usable sample is dropped. The read needs every counted run `clock_ok`. This is what RECORD1 meant (clock within 100 ms) with an honest error bound and no single-sample veto.

## Claim, pass bar (all fixed now)
At least 300 trades on at least 10 dates, all after the fix; mean net per contract >= +2.0c; date-clustered z >= 3.0 (`cluster_mean_z`); mean positive in both date halves and under fee x1.2; at least 3 of the assets with trades positive (`MIN_ASSETS` 3, as RECORD1); `clock_ok`. **Why this bar:** it is RECORD1's registered bar, so the replication is judged by the same ruler. **Honest status of the bar:** it is a lead bar, not the deflated one. The running count is about 730,413 tries before this read, so the family-wise bar is about z 5.27, which a 300 trade, 13 day read cannot reach unless the mean is far above anything seen. A pass at z 3.0 therefore means "a mechanism-bearing lead that replicated forward", never a switch. The route for that is the owner's capped probe channel (a reviewed edit, tiny size, with its own kill rule); nothing in this registration opens it.
**What mean and z the read needs:** the old information looks were +4.23c, z 1.86 on 334 trades and, latest (2026-11-04 evening, old rows, decides nothing), +5.23c, z 2.08 on 361 trades over 14 dates, i.e. a date-clustered standard error near 2.3c. At that noise z 3.0 needs a mean of about +6.9c; z 1.9 needs the old +4.2c. If the true mean is +4c the chance this read reaches z 3.0 is about 1 in 9.

## Kill rule and verdicts (same logic as RECORD1, `judge`)
FALSIFIED if n >= 300 and (mean < +0.5c or z < 1.0). NOT_YET_FALSIFIED only if every condition above holds. Otherwise NOT_ENOUGH_DATA, which is a stop, not an extension: more data needs a new registration and a new count.

## Prediction (numeric, stated before any fixed-clock row)
Mean +3c to +5c (old rows: +3.8c to +4.2c; some of that is the winner's curse of a read taken when the rule looked good, so I shade down), z 1.0 to 2.2. Verdict: NOT_ENOUGH_DATA 65%, FALSIFIED 25%, NOT_YET_FALSIFIED 10%. Shortfall mechanisms if it fails: SOL +0.4c and XRP's +10c on 56 trades are thin; the mean model gap of about 19c says the model disagrees with the quote by far more than the quotes are wrong, which is the signature of model error (the quotes already track spot), not of a lag.

## Read
One read, command `cd kalshi-scalper && PYTHONPATH=src python -m scalper.record1 record1b read` (information look: `... record1b look`, decides nothing). Guards in `src/scalper/record1.py`: refused before 300 trades on 10 dates, refused before 14 days after the first fixed-clock run (read date: **merge date + 14 days**, computed from the first `clock2` run folder, so no edit is needed), and refused a second time (`data/record1b_result.txt`). Rate observed: about 330 trades in 14 days, about 24 a day, so 300 new trades take about 13 days. Old `read` is unchanged.

## Ledger
N +2 (the rule is one try on the new window; the clock gate is a second check), running count about 730,413 to be kept by the coordinator. Code: `src/scalper/record1.py` (new functions `run_clock_ok_b`, `trades_b`, `main_b` after the old code), `tests/test_record1b.py` (synthetic). Recorder: `scripts/record_quotes.py` on branch `claude/v2-recorder-clock`.
