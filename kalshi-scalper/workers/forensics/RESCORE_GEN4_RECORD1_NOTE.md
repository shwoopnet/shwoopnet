# Re-scores from the stale-quote audit: GEN4 forward rows and RECORD1, on R6 order books (method, written before running; 2026-11-12)

Ordered by the Head of R&D after `STALE_QUOTE_AUDIT_NOV12.md`. **Each is the same test: the registered rule and bar are unchanged, V2's own evaluator code is used unmodified, only the price source is swapped from the quote recorder's market-list copy to the R6 order book. No new try.** Public recorded data only, zero Kalshi requests, nothing about the live account. Committed before either script is run.

## Common rules

- **Windows.** Only windows that have BOTH quote-recorder rows and an R6 book, so every line is on the same windows. No Bitcoin 15 minute close on or after 2026-11-05 is opened (the CFRTI held-out block).
- **Outcome.** The `result` column of the R6 coverage file (Kalshi's own result), for the old lines and the new ones alike. Strike from the quote recorder's `strike` column. Spot index from the quote recorder's `spot.csv` through V2's own function. (The spot file is the exchanges' public trade feeds, not a Kalshi list quote.)
- **R6 rows as polls.** One poll per R6 book row: time = receive time; YES bid and size = best YES bid; YES ask = 1 minus the best NO bid, its size = that NO bid's size; an empty side is a bid of 0 or an ask of 1 (one-sided), as in V2's loader. R6 polls every 2 s where the quote recorder polled every 0.6 s. R6 rows are limited to the span the quote recorder covers for that test (GEN4: the last 152 s; RECORD1: the last 62 s), so a rule cannot enter earlier than it could have as registered.
- **Lines reported per rule**, in this order:
  - **L0, the old figure** as written in V2's ledger or read (all its windows).
  - **L1, the old method on the common windows**: V2's code on `quotes.csv`. A check that the code is reproduced, and the fair comparator.
  - **L2, book-priced (PRIMARY)**: V2's code unchanged on R6 rows: signal and fill from the book at the same poll, exit (where the rule has one) at the book bid.
  - **L3, book-priced with the team's fill convention**: signal as L2; the order fills only if the book at the first poll at least 2 s later (and, separately, 6 s later) still offers the ask seen or better (1 contract); it pays that later ask; a miss is no trade.
  - **L4, the mechanism line**: the rule picks its poll on `quotes.csv` exactly as it ran, but pays the R6 book's ask at the first book poll at or after that quote poll (and is dropped if that ask is above the quote ask seen: "limit" variant). It shows how much of the old figure was the copy.
- **Bars, unchanged.** GEN4 rows: the ledger's own flag, "forward PF 1.5 or better at 1 and at 10 contracts on 30 or more trades over 10 or more trade days". RECORD1: its registered read (mean per trade after fees with z, at 300 trades on 10 dates; margin 3c, minimum size as registered). Fees as each test registered them (V2's functions). Labels: under about 100 trades, "no evidence at n = x".
- **What is not done.** No rule is changed, no threshold moved, no new rule tried, no row dropped for its result. Every row of the ledger's 52 GEN4 rows is reported in the CSV, not only the ones named below.

## GEN4 forward rows (audit row 5)

Rows: the 51 frozen GEN4 candidates and `GEN4_REF_FAV150` in `workers/candidates/` on `claude/epic-ptolemy-0amjd9`. Windows: `KXBTC15M` closes from 2026-10-30 00:00Z to 2026-11-04 19:30Z (the ledger's last scoring). Named in the write-up: the spot-momentum rows the ledger showed above 1 (B42, B35, B06, B05, B11, B37, B03) and the favourite references (REF_FAV150, B01). Summary lines over all 52: how many rows are at PF 1.0 or better at 1 contract on each line, and the median PF.

**Prediction, before running:** on L2 the spot-momentum rows fall to about 1.0 or below (the old figures were the copy's age); the favourite references stay below 1; no row meets the ledger's flag (none could: 6 trade days).

## RECORD1 (audit row 1), covered part only

V2's `record1.py` rule unchanged. Windows: closes 2026-10-29 22:15Z to the registered read's last window on 2026-11-03, series Bitcoin, Ethereum, XRP, Dogecoin (R6 does not record Solana; Oct 22 to 29 is before R6 and stays VOID). Old figure for comparison: the registered read of 2026-11-03 (n 300, mean +3.81c, z 1.60) and L1 on the common windows.

**Prediction, before running:** on L2 the trade count falls sharply (most "spot beats the quote by 3c" instants disappear when the quote is current) and the mean is not distinguishable from zero.
