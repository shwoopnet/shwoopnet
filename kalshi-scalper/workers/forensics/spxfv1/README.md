# SPXFV1 build 2: rows builder and Databento pull (Forensics desk, Nov 13, 2026)

Ordered by the Head of R&D at 16:57Z (the owner's top priority, KXINX15M). Research only. Invented rows only so far; nothing real has been built or read.

| File | What it does |
|---|---|
| `spxfv1_rows_builder.py` | `windows`: pull-run folders (settled list answers and candle answers) to the windows CSV; `futures`: a private Databento ohlcv-1m CSV to the futures CSV and the canonical extract hash. No network. |
| `spxfv1_databento_pull.py` | `cost`: per-day `get_cost` (a metadata call, spends nothing) and their sum; `pull`: only if the sum is within the cap (0.25 USD), one get_range per day into ONE scratch csv outside the git working tree, and prints the spend. No key is handled (the proxy supplies the credential). |
| `test_spxfv1_rows_builder.py` | 16 checks on invented rows, expectations worked out by hand: decision candle exactly close minus 120 s, missing side as 0.0 or 1.0, void and empty results, held-out stop at 2026-12-01T00:00:00Z, HELDOUT_ and listed-run refusals, ns timestamps to bar-start seconds, the roll's instrument id, the canonical hash, refusal inside the git tree, cost first and the abort over the cap. All pass. |

Input spec read from the History Miner's `spxfv1b.py` (sha256 `9032013a...` at `3ecd0925`), not from the Testing Desk's build: windows CSV `ticker, event_ticker, close_ts, yes_bid, yes_ask, result` (result yes, no, void or empty; empty stops build 2);
futures CSV `ts_event_s` (bar START), `symbol` (must be `ES.c.0`), `instrument_id`, `close`. **Layout check:** build 2 itself ran `dev` on the builder's two output files built from invented rows (one traded window), in a scratch copy with its guard.

**Canonical extract hash (to agree with the Testing Desk):** sha256 over the lines `<ts_event_s>,<instrument_id>,<close with two decimals>\n`, sorted by (ts_event_s, instrument_id). ES ticks are 0.25, so two decimals are exact. The Testing Desk should confirm it uses the same line format.

**Cost.** The quoted price for the six days (the Testing Desk's query: GLBX.MDP3, ES.c.0, ohlcv-1m, continuous, 14:30Z to 21:00Z on Nov 5, 6, 9, 10, 11 and 12) was read on Nov 13 at about 18:45Z by `cost`: a total of 0.008543 USD, well under the 0.25 cap. The pull has not been run.
Decisions the builder makes that are not in the Head's text (each is for Auditor B and the Head to confirm): a missing bid or ask in the decision candle is written 0.0 or 1.0 (build 2 reads that as no quote) and counted by reason; a scalar result is a void; no result is `empty` (build 2 stops); any market closing on or after 2026-12-01T00:00:00Z stops the builder.
