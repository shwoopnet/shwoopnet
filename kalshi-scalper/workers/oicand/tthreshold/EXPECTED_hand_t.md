# OICORE-NC15 threshold T: hand case, written BEFORE the reader code (Desk B build 1)

Rule (Desk A's DESK_A_FROZEN_OICORE_PLACES_DEFINITIONS_NOV13.md v5, section 1; text only): for each market (series), one rise per window = open_interest of the 1 minute candle ENDING at close - 180 s minus open_interest of the candle ENDING at close - 360 s. A trading day = a US Central calendar day (of the window's close time) with at least one window whose two candles exist. T = the 90th percentile, nearest rank (the ceil(0.9 n)-th smallest, n rises), of the rises of the LAST 20 trading days. Gate 0: fewer than 20 trading days, or T <= 0, or T < 5 contracts: NOT seated, reported. Prints per market the windows used (n), trading days available and used, T, the verdict and the dropped counts. It reads only ticker, close_time, end_period_ts and open interest: no price, result or quote. The fixture runs the reader with --days 3 (instead of 20) so the made-up data stays small; the real run uses 20.

## Made-up fixture (US Central = UTC-6 on these dates, after the Nov 1 change; every window's open interest is 1000 at close-360 s and 1000 + rise at close-180 s)
Series S1 (4 Central days): D0 = Nov 2: closes 16:00, 16:15, 16:30, 16:45Z, rises 1000, 2000, 3000, 4000. D1 = Nov 3: closes 16:00Z, 16:15Z, 16:30Z and 2026-11-04T05:30Z (Central Nov 3, 23:30), rises 10, 20, 30, 40. D2 = Nov 4: closes 16:00 to 16:45Z, rises 50, 60, 70, 80. D3 = Nov 5: closes 16:00 to 16:45Z, rises 90, 100, 110, 120; plus two more windows on Nov 5, one closing 17:00Z with NO candle ending at close-360 s, one closing 17:15Z whose candle at close-180 s has NO open interest field.
Series S2: Nov 3, 4, 5, four windows a day (16:00 to 16:45Z), rises 1,1,1,2 | 2,2,3,3 | 3,4,4,4.
Series S3: Nov 3 and Nov 4 only, four windows a day, rises 10,20,30,40 | 50,60,70,80.

## Expected, with --days 3
| series | windows used (n) | trading days available | used | T | verdict | dropped |
|---|---|---|---|---|---|---|
| S1 | 12 | 4 | 3 (Nov 3, 4, 5) | 110 | SEATED | missing candle at close-360: 1; no open interest field: 1; windows outside the last 3 trading days: 4 |
| S2 | 12 | 3 | 3 | 4 | NOT SEATED: T under 5 | none |
| S3 | 8 | 2 | 2 | n/a | NOT SEATED: fewer than 3 trading days | none |
Workings: S1 last three days Nov 3 to 5 give 12 rises 10 ... 120 in steps of 10; ceil(0.9 x 12) = ceil(10.8) = 11, the 11th smallest = 110. The 2026-11-04T05:30Z close is Central Nov 3, so it belongs to Nov 3 (a UTC date split would put it on Nov 4 and change nothing here only because day sets are by window; the day count 4 and used 3 would stay, but the Nov 3 window would be wrongly dated; the expected assigns it to Nov 3). S2: 12 rises sorted 1,1,1,2,2,2,3,3,3,4,4,4; the 11th = 4. Under 5, so not seated. S3: 2 trading days, fewer than 3: not seated, T not given.
Also expected: the reader stops (exit 2) on a ticker repeated across candle files, and prints "markets with no open interest at all: 0" for the fixture.
