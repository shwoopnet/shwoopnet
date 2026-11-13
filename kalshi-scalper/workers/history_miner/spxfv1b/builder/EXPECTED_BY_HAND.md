# SPXFV1 rows builder, expected by hand (History Miner, Nov 13, 2026)

Written BEFORE the builder code, from the text of PR 907's job files (SPXOI1_LISTS, SPXOI1_CANDLES) and spxfv1b.py's input layout. No real run read.

## What the builder does (Kalshi half)
- Reads the LISTS run and the CANDLES run by manifest rows: status must be `complete`; every job request answered on pages 1..k at 200 with no cursor left; no truncated row; every file inside its run folder; sha256 and bytes checked when present. Both folders go through hm_guard.
- From the list: every market with ticker starting `KXINX15M-`: `ticker`, `event_ticker`, `close_ts` = epoch of `close_time`, `result` as Kalshi wrote it (spxfv1b decides what it accepts).
- A list market closing at or after 2026-12-01T00:00:00Z STOPS the build (the jobs are development dates only).
- The decision candle is the one whose `end_period_ts` equals close_ts - 120. `yes_bid` = its `yes_bid.close_dollars`, `yes_ask` = its `yes_ask.close_dollars`. A missing bid is written 0 (no bid) and a missing ask 1 (no ask); a market with no candle at that end time is written 0 and 1. spxfv1b reads both as no quote.
- Rows sorted by close_ts then ticker. Numbers written with Python's `%g`-free `repr` of the float (0.4, 0.43, 0.0, 1.0).
- Counts to stderr: rows, quoted (both sides present), missing_side, no_candle.

## Made-up runs (built by test_builder.py)
List run, request `settled_KXINX15M`, two pages (page 1 carries a cursor, page 2 none):
- M1 `KXINX15M-26NOV051300-00`, event `KXINX15M-26NOV051300`, close 2026-11-05T18:00:00Z, result yes
- M2 `KXINX15M-26NOV051315-15`, close 18:15Z, result no (page 1)
- M3 `KXINX15M-26NOV051330-30`, close 18:30Z, result void (page 2)
- M4 `KXINX15M-26NOV051345-45`, close 18:45Z, result empty (page 2)
Candle run, one request a ticker (c001 to c004):
- M1: candles ending close-180 (bid 0.38 ask 0.41) and close-120 (bid 0.40 ask 0.43)
- M2: candle ending close-120 with yes_bid lacking close_dollars, ask 0.55
- M3: only a candle ending close-180 (bid 0.20 ask 0.25)
- M4: candle ending close-120, bid 0.10 ask 0.12

## Expected output
Epochs: 18:00Z Nov 5 = 1793901600 (PR 907: c001 end_ts 1793901480 = close - 120); +900 each.
```
ticker,event_ticker,close_ts,yes_bid,yes_ask,result
KXINX15M-26NOV051300-00,KXINX15M-26NOV051300,1793901600,0.4,0.43,yes
KXINX15M-26NOV051315-15,KXINX15M-26NOV051315,1793902500,0.0,0.55,no
KXINX15M-26NOV051330-30,KXINX15M-26NOV051330,1793903400,0.0,1.0,void
KXINX15M-26NOV051345-45,KXINX15M-26NOV051345,1793904300,0.1,0.12,
```
Counts: rows 4, quoted 2, missing_side 1, no_candle 1.

## Refusals expected
1. list manifest status `partial`
2. a candle file whose sha256 does not match
3. list page 2 missing (pages 1..k broken)
4. a list market closing 2026-12-02T16:15:00Z (held-out)
5. a run folder path containing HELDOUT_ (hm_guard)
