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
