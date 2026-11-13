# OIVER rows builder (one shared builder for the OIVER scorers), expected by hand (History Miner, Nov 13, 2026)

Written BEFORE the code, from the Head of R&D's order of 21:05Z and the 19:53Z convention. No landed answer opened.

## What it does
- **Inputs:** one results LIST run, which must be job CFRTI_K_LISTS, and one or more CANDLE runs with job_id in {CFRTI_K_CANDLES, CFRTI_K_PROBE, CFRTI_K_R6SLICE}.
- **Checks on every run:** status complete; every job request answered on pages 1..k at 200 with no cursor left; no truncated row; every row carries sha256 and bytes and both match; files inside the folder; hm_guard on the folders, the output and every file.
- **Windows:** every KXBTC15M ticker named in a candle run's requests.
  - close_ts and event_ticker come from the list (close_time and event_ticker), and result is as Kalshi wrote it.
  - A requested ticker absent from the list is dropped and counted no_list_row.
  - Any window closing at or after 2026-12-01T00:00Z stops the build.
- **Columns, from the candles of that ticker:** ticker, event_ticker, close_ts, oi_180, oi_360, yes_bid, yes_ask, no_bid, no_ask, result.
  - oi_180 and oi_360 are open_interest_fp (else open_interest) of the candle ending close - 180 and close - 360. A missing candle, a bool or a non-finite value is written blank, counted missing_oi once a window.
  - yes_bid and yes_ask are the close_dollars of the candle ending close - 180.
  - A bid of 0 or under is no bid and an ask of 1 or over is no ask (blank, counted no_bid and no_ask).
  - Rule 18: a crossed or locked quote (yes_bid >= yes_ask - 1e-9) blanks all four prices, counted crossed_or_locked.
  - no_bid = 1 - yes_ask and no_ask = 1 - yes_bid, rounded to 6 places, blank where their source is blank.
  - No candle at close - 180 blanks all four prices, counted no_quote_candle.
- **Overlap:** a ticker in two candle runs must have identical candles at close - 180 and close - 360 (else the build stops); counted duplicate_agree.
- Numbers are written with Python repr after the rounding; rows are sorted by (close_ts, ticker). Counts go to stderr.

## Made-up runs (test_oiver_rows.py)
LIST run (job CFRTI_K_LISTS), two pages:
- M1 KXBTC15M-26NOV040700-00, event KXBTC15M-26NOV040700, close 2026-11-04T12:00:00Z (1793793600), result yes
- M2 KXBTC15M-26NOV040715-15, close 12:15Z (1793794500), result no
- M3 KXBTC15M-26NOV040730-30, close 12:30Z (1793795400), result no (page 2)
- M5 KXBTC15M-26NOV040745-45, close 12:45Z, result yes (page 2, never requested by a candle run: not a window)

CANDLE run 1 (job CFRTI_K_CANDLES), one batched request naming M1, M2, M3, M4:
- M1: close-360 OI "500000.00"; close-180 OI "590000.00", yes_bid 0.20, yes_ask 0.22; a decoy at close-120 (OI 1, bid 0.5, ask 0.6)
- M2: close-360 OI "400000.00"; close-180 OI "410000.00", bid 0.40, ask 0.40 (locked)
- M3: no close-360 candle; close-180 OI "300000.00", bid 0.00, ask 0.30
- M4 KXBTC15M-26NOV040800-00: candles, but no list row
CANDLE run 2 (job CFRTI_K_R6SLICE): M1 again, the same two candles exactly.

## Expected CSV
```
ticker,event_ticker,close_ts,oi_180,oi_360,yes_bid,yes_ask,no_bid,no_ask,result
KXBTC15M-26NOV040700-00,KXBTC15M-26NOV040700,1793793600,590000.0,500000.0,0.2,0.22,0.78,0.8,yes
KXBTC15M-26NOV040715-15,KXBTC15M-26NOV040715,1793794500,410000.0,400000.0,,,,,no
KXBTC15M-26NOV040730-30,KXBTC15M-26NOV040730,1793795400,300000.0,,,0.3,0.7,,no
```
**Counts:** windows 3, no_list_row 1, missing_oi 1, crossed_or_locked 1, no_bid 1, no_ask 0, no_quote_candle 0, duplicate_agree 1.

## Refusals expected
1. A run-2 M1 candle that differs at close - 180.
2. A list run whose job_id is not CFRTI_K_LISTS.
3. A candle run with job_id NOSIDE1_CANDLES.
4. A row without sha256.
5. A list close_time of 2026-12-02 for a requested ticker.
6. A HELDOUT_ path.

## Dated line, 2026-11-13 21:10Z: Auditor B's F1 to F4 and the Head's ruling on F1's range (tests written before the code change)
- **F1:** WINDOW_FROM = 2026-09-12T00:00:00Z, WINDOW_TO = 2026-11-09T00:00:00Z. A window (a requested ticker with a list row) whose close is outside [FROM, TO) STOPS the build, at both ends. This replaces the Dec 1 stop. Why: every unread or unfrozen KXBTC15M held-out starts on or after Nov 9 (DEPTH1, CFRTI1-BTC and CFRTI-B from Nov 9; W-SPOTLEAD1's block from Nov 11; CFRTI-K from Nov 14). The landed CFRTI_K runs end Nov 4, so no blinding issue.
  Consequence: CFRTI_K_PROBE's 24 windows close on Aug 20, before FROM, so passing that run stops the build. It stays in the allowed jobs only so the Head can rule otherwise.
- **F2:** per request id and page, the rows in manifest order. Earlier non-200 rows (429 retries or other repeated answers, which the runner writes without file or sha256) are ignored. The LAST row of each page must be the page's one 200 row, with file, sha256 and bytes present and truncated false. The build STOPS on: a page whose last row is not 200; two 200 rows for one page; pages not 1..k; a truncated row; a cursor on the last page.
- **F3:** the embedded job must equal an audited job, compared by sha256(json.dumps(job, sort_keys=True, separators=(",", ":"))). The as-run hashes (each equals its job file as it stood before PR #888, which changed only the "heldout" note text afterwards) are:
  - CFRTI_K_LISTS c8f9e739...;
  - CFRTI_K_CANDLES 9ee22620...;
  - CFRTI_K_PROBE af06ad9a...;
  - CFRTI_K_R6SLICE 65217aba....
- **F4:** list rows of one ticker from several requests or pages are merged.
  - The row with a non-empty result is kept.
  - The build STOPS if close_time or event_ticker differ, or if two non-empty results differ.
  - Windows with a blank result are counted as blank_result (the base set has 0).

### Expected, by hand
- **Base set:** unchanged CSV and counts, plus blank_result 0.
- **429 before the 200** on the candle request: the same CSV and counts.
- **List request 2** repeats M1 with result "" (settled then unsettled), and request 1 gives M2 with result "" while request 2 gives "no" (unsettled then settled): the same CSV as the base (M1 yes, M2 no), blank_result 0.
- **M2 blank in both requests:** M2's row has an empty result; blank_result 1; everything else unchanged.

### New refusals expected
- a window closing 2026-09-11T23:45Z (before FROM)
- a window closing 2026-11-09T00:00Z (at TO)
- a candle request whose last row is a 429
- a candle request whose last row is a 404
- an embedded job that differs from the audited one (an extra key)
- list rows of one ticker that disagree on close_time
- list rows of one ticker that disagree on yes against no
