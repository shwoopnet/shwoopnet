# LIQREV R15 coverage-interval row builder, expected by hand (History Miner, Nov 13, 2026)

Written BEFORE the code, from Desk C's card `kalshi-scalper/workers/idea_desk_c/LIQREV_CARD.md` at d2822839 (sha256 f0257cce), Amendment 3 R15, and the Head of R&D's order of 21:15Z. The Testing Desk's and Desk C's code were not read. File layouts come from `scripts/record_oklq.py` and `scripts/record_15m_book.py` on main (code only). No data read. **No real run before 2026-11-30.**

## What it reads, and only that
- **OKX:** coverage.csv(.gz) files of the OKX recorder only; a path not named coverage.csv or coverage.csv.gz STOPS, so liquidations.csv is never opened. Columns used: t_start_ms, uly, oldest_ts_ms.
- **R6:** coverage.csv(.gz) files of book15r6 only; book.csv and trades.csv are never opened. Columns used: close_time, series, ticker. The R6 coverage file also carries a `result` column; the builder never reads it (the rows are read by column index, and that index is never taken).
- hm_guard runs on every path.

## Rules
- **Mode and read dates:** dev or held. The dev block is closes [2026-11-17, 2026-11-30); the held block is [2026-11-30, 2027-01-01). A dev run is refused before 2026-11-30T00:00Z and a held run before 2027-01-02T00:00Z (R13); the clock is injectable for tests.
- **R6 folder guard:** an R6 coverage path whose date folder (YYYY-MM-DD) is outside [block start - 1 day, block end - 1 day] STOPS. For dev that is Nov 16 to Nov 29; for held, Nov 29 to Dec 31. A job folder can cross midnight, so windows outside the block that sit in an allowed folder are skipped and counted outside_block.
- **One OKX coverage interval per row:** [oldest_ts_ms, t_start_ms] in ms, for that row's uly.
  - Why that span: the pass pages back without a gap from the newest liquidation at the time of its first request to oldest_ts_ms, whatever its stop reason. A page limit, out of time or a read failure only means nothing OLDER than oldest_ts_ms is known.
  - A row with a blank oldest_ts_ms (nothing read) gives no interval, counted okx_no_interval.
  - A uly other than BTC-USDT or BTC-USD STOPS.
- **Merge:** per uly, intervals are sorted and merged when the next start <= the current end. The joint coverage is the intersection of the two ulys' merged unions, because L(t) sums both swaps.
- **Windows:** R6 coverage rows with series KXBTC15M and a close in the block, de-duplicated by ticker. Rows of other series are counted other_series; repeated tickers are counted duplicate.
- **Covered:** some joint interval [a, b] with a <= close - 900 s and b >= close - 180 s, in ms. This is R15's [close - 720 s - 180 s, close - 180 s), half open at the end.
- **Output:** ticker, close_ts, liq_covered (1 or 0), sorted by close then ticker. Counts go to stderr.

## Made-up data (test_liqrev_cov.py); T0 = 2026-11-20T00:00:00Z = 1795132800 s; intervals and closes in seconds from T0 (made up, some off the 15 minute grid on purpose)
**OKX coverage:**

| row | uly | oldest | t_start |
|---|---|---|---|
| U1 | BTC-USDT | -3600 | +3600 |
| U2 | BTC-USDT | +3000 | +7200 |
| U3 | BTC-USDT | +9000 | +12000 |
| U4 | BTC-USDT | blank | +12500 (read_failed) |
| D1 | BTC-USD | -3600 | +12000 |

USDT merged: [-3600, +7200] and [+9000, +12000]. USD: [-3600, +12000].
**Joint:** [-3600, +7200] and [+9000, +12000].

**R6 coverage (folder book15r6/2026-11-20/0000/), every row with result "SHOULD_NOT_BE_READ":**

| row | ticker | close | span | expected |
|---|---|---|---|---|
| W1 | KXBTC15M-W1 | +1800 | [+900, +1620] | covered |
| W2 | KXBTC15M-W2 | +3840 | [+2940, +3660] | covered, and only by the MERGE: U1 ends 3600 < 3660 and U2 starts 3000 > 2940 |
| W3 | KXBTC15M-W3 | +8100 | [+7200, +7920] | not covered (joint ends at +7200) |
| W8 | KXBTC15M-W8 | +8700 | [+7800, +8520] | not covered: USD covers it, USDT does not; this tests the intersection |
| W4 | KXBTC15M-W4 | +12000 | [+11100, +11820] | covered |
| W5 | KXETH15M-W5 | +1800 | | other_series |
| W6 | a second row for KXBTC15M-W1 | | | duplicate |
| W7 | KXBTC15M-W7 | closes 2026-11-30T00:15Z | | outside_block |

**Expected CSV:**
```
ticker,close_ts,liq_covered
KXBTC15M-W1,1795134600,1
KXBTC15M-W2,1795136640,1
KXBTC15M-W3,1795140900,0
KXBTC15M-W8,1795141500,0
KXBTC15M-W4,1795144800,1
```
**Counts:** windows 5, covered 3, no_liq_coverage 2, outside_block 1, other_series 1, duplicate 1, okx_rows 5, okx_no_interval 1. The text SHOULD_NOT_BE_READ appears nowhere in the output.

## Refusals expected
1. a dev run with the clock at 2026-11-29T23:00Z
2. a held run with the clock at 2027-01-01T12:00Z
3. an R6 coverage file under book15r6/2026-11-30/ in dev mode
4. a liquidations.csv path given as OKX coverage
5. an OKX row with uly ETH-USDT
6. a HELDOUT_ path

## First test run (no expected figure changed)
The first run stopped "dev run refused before 2026-12-06": two block constants had been typed by hand and were wrong (2026-11-17 is 1794873600 and 2026-11-30 is 1795996800). They are now the computed values, and the printed block bounds were checked. Mutants run in a temporary folder and deleted:
- with no merge, W2 is not covered;
- with a union in place of the intersection, W3 and W8 are covered.
Both fail the test.
