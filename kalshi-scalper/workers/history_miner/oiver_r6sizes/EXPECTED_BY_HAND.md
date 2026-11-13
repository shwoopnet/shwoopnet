# OIVER-DEPTH book-size builder (R6), expected by hand (History Miner, Nov 13, 2026)

Written BEFORE the code, from the Head of R&D's rulings of 21:10Z to 21:14Z. The R6 guard is the Head's ruling; Desk A is adding it to card 3 as a dated amendment. Layout of the R6 book file taken from `scripts/record_15m_book.py` on main (code only; no data read).

## What it does
- **Inputs:** the OIVER rows CSV (`../oiver_rows/oiver_rows.py` output) and one or more R6 `book.csv.gz` files.
- **Output:** the rows closing in [R6_START 2026-10-29T00:00Z, 2026-11-09T00:00Z), with two columns added, yes_bid_size and yes_ask_size. Rows closing before R6_START are dropped and counted before_r6.
- **R6 guard:**
  - R6_HELDOUT_FROM = 2026-11-09T00:00Z.
  - A book file whose path has a date folder (YYYY-MM-DD) on or after 2026-11-09 STOPS the build, as does an input row closing on or after it.
  - Book rows whose close_time is on or after Nov 9 are never looked up (they are not matched to any window).
- **Decision poll:** among the book rows with the window's ticker AND close_time equal to the window's close, the last row with t_recv_ms in [close - 190 s, close - 180 s] in ms, both ends inclusive. No such row leaves both sizes blank, counted no_poll.
- **Sizes:**
  - yes_bid_size = yes_bid_sz_1, the best YES bid (the recorder writes level 1 as the best);
  - yes_ask_size = no_bid_sz_1, since the best NO bid at p is the YES ask at 1 - p.
  - A blank or non-numeric size is written blank, counted missing_size once a window.
  - Written as repr(float).
- **Checks:** hm_guard on every path. Counts go to stderr.

## Open readings for the Head
- (a) The poll time is t_recv_ms (when the book was seen), not t_send_ms or the Date header.
- (b) No check that the R6 touch price equals the candle's quote. The size is the size at R6's best level at that poll.

## Made-up data (test_oiver_r6sizes.py)
Input rows (OIVER columns, made-up values):
- A: close 2026-10-28T23:45Z
- B: close 2026-11-02T12:00Z
- C: close 2026-11-03T08:15Z
- D: close 2026-11-06T20:30Z

Book file `book15r6/2026-11-02/1200/book.csv.gz` (all rows for the window's ticker unless stated):
- B: polls at close-195 s (bid sz 11, no sz 12), close-188 s (21, 22), close-181 s (31, 32), close-180 s exactly (41, 42), close-179 s (51, 52); and a decoy row for B's ticker with a DIFFERENT close_time at close-185 s (99, 99).
- C: polls at close-200 s and close-170 s only.
- D: one poll at close-185 s with yes_bid_sz_1 blank and no_bid_sz_1 7.

## Expected
- A: dropped (before_r6).
- B: sizes 41.0 and 42.0 (the close-180 s poll is the last in the interval; the decoy is not matched).
- C: both sizes blank (no_poll).
- D: yes_bid_size blank, yes_ask_size 7.0 (missing_size 1).

**Counts:** rows_in 4, before_r6 1, written 3, no_poll 1, missing_size 1.

## Refusals expected
- a book file under book15r6/2026-11-09/
- an input row closing 2026-11-09T00:00Z
- a HELDOUT_ path

## Test fix found before the first commit (no expected figure changed)
The first decoy row sat outside B's poll interval, so it tested nothing. It now sits at exactly B's close - 180 s, after the real row, so it would win the tie if close_time were not matched. A one-off mutant (match by ticker only, run in a temporary folder and deleted) gives B 99.0 / 99.0 and fails the test, so the decoy discriminates.

## Dated line, 2026-11-13 21:17Z: card 23b5bd9b (sha256 ae1f1ee6...), the 21:13Z amendment; reworked by hand before the code
- **Exchange time:** the poll time is the book row's server_date_header (the exchange's HTTP Date, whole seconds), not t_recv_ms. The decision poll is the last row with Date in [close - 190 s, close - 180 s], both ends inclusive. Among rows with the same Date second, the latest t_recv_ms wins, then the later row in the file. A row with an unreadable Date is skipped.
- **New column r6_poll:** 1 when a decision poll was found, 0 when not (both sizes are then blank). DEPTH's scorer uses it to form the replay set.
- **Made-up data:** each book row's Date is its intended second (close - 195, -188, -181, -180, -179 and so on). Its t_recv_ms sits 300 ms after that Date, and the decoy and the C and D rows likewise.
- **Expected values:** unchanged, with r6_poll B 1, C 0, D 1. B's close-180 s row has Date exactly close - 180 and is the last in the interval.
- **New check:** a row whose t_recv_ms is inside the interval but whose Date is outside it (B at Date close - 179, t_recv close - 180.7) must NOT be chosen. The existing close-179 row is shifted to t_recv close - 180.7 s to test exactly this, and B's sizes stay 41.0 / 42.0.

## Dated line, 2026-11-13 21:30Z: the exchange-time OFFSET formula (frozen sheet DESK_A_FROZEN_OIVER_SHADOW_DEFINITIONS_NOV13.md at 61fb9854, sha256 cb45e79b, section 1, which repeats the wheel sheet's section 0); this replaces the 21:17Z line's per-row Date reading; reworked by hand before the code
- **Clock:** for a candidate poll, offset = the MEDIAN over the 120 most recent rows of the SAME run folder, which means:
  - any ticker;
  - ordered by t_recv_ms, stable in file order;
  - at or before that poll, the poll itself included;
  - rows with a readable Date header only;
  - of (header seconds + 0.5 - t_recv_ms / 1000).
  The poll's exchange time = t_recv_ms / 1000 + offset.
- **Decision poll:** the last poll by exchange time with exchange time in [close - 190 s, close - 180 s], at or before D = close - 180 s and at most 10 s before it.
- **Open, to be confirmed by Desk A's dated line:**
  - (a) with FEWER than 120 readable rows before the poll, the median of all of them (at least 1; a poll with none has no exchange time and is skipped);
  - (b) for an even count, the mean of the two middle values (Python statistics.median).
- **The one file is one run folder.** Each book.csv.gz is treated as its own run.

### Reworked made-up data
"X" is the true exchange time of a row. Date = floor(X) and t_recv_ms = round((X - skew) x 1000).
- **Run 1, `book15r6/2026-11-02/1200/book.csv.gz`:**
  - 200 filler rows of ticker KXBTC15M-F, with skew 10.0 s, X from close_B - 1000.5 in 1 s steps;
  - then 130 filler rows with skew 2.3 s, X from close_B - 330.5 to close_B - 201.5;
  - then B's polls, all with skew 2.3 s, at X = close_B - 195.5 (11, 12), -188.5 (21, 22), -181.5 (31, 32), -180.5 (41, 42) and -179.5 (51, 52);
  - then the decoy: B's ticker, close_time close_B + 900, with the same X and t_recv as the -180.5 row and later in the file, sizes 99/99.
  - For every B row, the last 120 rows are all skew 2.3 with X fraction .5, so each term is floor(X) + 0.5 - (X - 2.3) = 2.3 exactly. Offset 2.3, so the exchange time is X.
- **Run 2, `book15r6/2026-11-03/0800/book.csv.gz`** (C and D only, fewer than 120 rows, skew 2.3, X fraction .5, so the offset is again 2.3 and the exchange time is X):
  - C's polls at close_C - 200.5 and close_C - 170.5;
  - D's one poll at close_D - 185.5, with yes_bid_sz_1 blank and no_bid_sz_1 7.

### Expected (the same as before)
- B: 41.0, 42.0, r6_poll 1. The -180.5 row is the last with X in [-190, -180]; -179.5 is outside, and the decoy is not matched.
- C: blank, blank, 0.
- D: blank, 7.0, 1.
- A: dropped.
- Counts: rows_in 4, before_r6 1, written 3, no_poll 1, missing_size 1.

### Mutants that must FAIL the test
| mutant | B's sizes |
|---|---|
| each row's own Date (the 21:17Z build) | Date of -179.5 is -180, inside the interval: 51 / 52 |
| raw t_recv | -179.5 receives at -181.8, inside the interval: 51 / 52 |
| the median over the WHOLE run | 200 rows of 10.0 against 135 of 2.3, offset 10.0, each B row shifted +7.7 s, so -188.5 becomes -180.8, the last inside: 21 / 22 |
| match by ticker only | the decoy: 99 / 99 |
