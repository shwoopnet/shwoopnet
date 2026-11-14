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

## Correction after Auditor B's read (Nov 14), written BEFORE the code change: the open interest field rule
Desk A's v3 F1 (section 7): `open_interest_fp` is read FIRST; `open_interest` only if `open_interest_fp` is ABSENT (the key is not there). A value that is null, blank, not finite (nan, inf) or a bool is UNREADABLE, and an unreadable value is a missing candle (a "candle without open interest" drop, with NO fallback to the other field). The first reader tried `open_interest` first and used float() with no such tests; fixed to this rule.
New hand cases (series S4, with --days 3), on the same three Central days Nov 3 to 5 as S1's valid windows (rises 10 ... 120, twelve windows), plus seven case windows on Nov 5 (close-360 candle always "1000.00"):
- a) fp "1500.00" and open_interest "9999" both present: reads fp, rise 500 (counts).
- b) fp "abc" and open_interest "9999": unreadable, NO fallback: dropped (candle without open interest).
- c) fp the JSON bool true and open_interest "9999": unreadable: dropped.
- d) fp "nan": dropped. e) fp "inf": dropped. f) fp "" (blank): dropped.
- g) fp key absent, open_interest "1700": reads open_interest, rise 700 (counts).
Expected S4: windows used n 14 (twelve base rises plus 500 and 700), trading days 3 available, 3 used, rises sorted 10 ... 120, 500, 700, ceil(0.9 x 14) = ceil(12.6) = 13, the 13th smallest = 500, so T 500, SEATED; dropped: candle without open interest 5 (b, c, d, e, f). A reader that tried open_interest first would take 9999 for (a), (b), (c) and would give a different n and T.
Also printed from now on: the first and last Central day used, for each market. Expected: S1 "days used 2026-11-03 to 2026-11-05", S2 the same, S3 "2026-11-03 to 2026-11-04", S4 "2026-11-03 to 2026-11-05". The S1, S2 and S3 lines above are otherwise unchanged.

## Final scope (the Head, Nov 14): allowed series and the EVENT830 cut, hand cases written BEFORE the code change
Only KXHYPE15M and KXBNB15M are readable from the OICAND backfill (the other nine places are held for open cards). New parameters: `--allowed-series` (default KXHYPE15M KXBNB15M) and `--series` (default the same); the reader STOPS (exit 2, "STOP: series not allowed") if `--series` names any series outside the allowed list. It also ignores every market of another series without touching its candlesticks. The EVENT830 13:30Z cut stays in the reader as `--cut-series` (default the eight EVENT830 series, which include KXHYPE15M and KXBNB15M): a window of such a series whose close is 13:30:00Z on 2026-11-05, 11-06, 11-10, 11-12 or 11-13 is dropped and counted as "event830_forward_close". Open interest fields only, as before.
Fixture additions (run with --allowed-series S1 S2 S3 S4 S5 --cut-series S5 --days 3): series S5 has the three Central days Nov 3, 4, 5 with windows 16:00 to 16:45Z and rises 10, 20, ... 120 (twelve), plus a window closing 2026-11-04T13:30:00Z with rise 3000 (a 13:30Z close but NOT a cut date, so it counts) and a window closing 2026-11-05T13:30:00Z with rise 5000 (a cut date: dropped).
Expected S5: windows used n 13 (twelve plus the 3000), 3 trading days available and used (Nov 3 to Nov 5 Central; both 13:30Z closes are Central 07:30), the rises sorted ..., 120, 3000, ceil(0.9 x 13) = ceil(11.7) = 12, the 12th smallest = 120, so T 120, SEATED; dropped: event830_forward_close 1. A reader without the cut would have 14 rises and T = 3000 (the 13th of 14).
Stop test: running with `--allowed-series S1 --series S1 S2` must stop with exit code 2 and the message "STOP: series not allowed" before printing any market. The S1 to S4 lines above are unchanged.
