# Recorder coverage for the new wheel places (OICORE's mechanism on Ethereum, XRP and the NC15 series) (Forensics desk, Nov 13, 2026)

Ordered by the Head of R&D (21:05Z, item 1). Counts and names only. Data read: the file LISTS of the recorder branches (`quote-data` for R6, `nc-data` for NC15) and the `series`, `close_time`, `polls`, `ok_polls`, `n429` columns of their coverage files; no price, book, trade or result column was used. Zero Kalshi requests. Taken at about 21:50Z Nov 13 (the clock), so "last" means the newest file then.

## 1. R6 (`book15r6`): Ethereum and XRP (also Bitcoin, gold, Dogecoin, same runs)

| Series | Windows recorded | First close | Last close | Polls (ok share) | 429s |
|---|---|---|---|---|---|
| KXETH15M | 1,223 | 2026-10-29T22:15Z | 2026-11-13T20:00Z | 471,328 (100.00%) | 0 |
| KXXRP15M | 1,223 | same | same | 473,365 (100.00%) | 0 |

85 coverage files (runs). Windows per day, identical for all five R6 series (Oct 29 to Nov 13): 7, 52, 41, 89, 76, 96, 95, 96, 88, 94, 85, 72, 73, 96, 88, 75 (Nov 13 is a part day, to 20:00Z). A full day is 96. **Gaps** (days under 88): Oct 30 (52), Oct 31 (41), Nov 2 (76), Nov 9 (72), Nov 10 (73); 85 to 89: Nov 1, Nov 6, Nov 8, Nov 12. Run starts that lag the 4 hour boundary by more than 30 minutes (from the folder names): Oct 30 05:37, 12:43, 18:34 and 22:38; Oct 31 02:16, 08:50, 15:16, 19:31; Nov 1 09:40, 16:27; Nov 2 17:07; Nov 6 09:18, 16:55; Nov 7 08:41; Nov 8 05:53, 13:14; Nov 9 09:40 and 20:40; Nov 10 11:18, 18:43; Nov 12 08:23, 12:34, 17:08, 20:26; Nov 13 08:43, 17:08. R6's stop dates: Bitcoin and Ethereum run to 2026-11-20 (the Nov 11 extension); XRP, Dogecoin and gold stopped after 2026-11-13 23:59Z, so **XRP's R6 coverage ends at the last close of Nov 13 20:00Z in these files**.

## 2. NC15 (`nc15`): the 11 non-crypto series and KXINX15M

12 coverage files (runs) from Nov 11 19:32Z to Nov 13 16:46Z (still running). Run folders: Nov 11 1932; Nov 12 0001, 0418, 0801, 1250, 1601, 2049; Nov 13 0001, 0401, 0846, 1201, 1646. Each run records to the next 4 hour boundary, so the gaps are: Nov 11 16:00 to 19:32 (before the first run) and 20:00 to Nov 12 00:00 (no run that block); then late starts of 18 minutes (Nov 12 04:18), 50 (12:50), 49 (20:49), 46 (Nov 13 08:46) and 46 (16:46).

| Series | Windows | First close | Last close | Days | Polls (ok share) | 429s | Largest gap between polls |
|---|---|---|---|---|---|---|---|
| KXSILVER15M | 181 | 2026-11-11T19:45Z | 2026-11-13T20:00Z | Nov 11, 12, 13 | 19,233 (100.0%) | 0 | 15.6 s |
| KXCOPPER15M | 181 | same | same | same | 21,348 (100.0%) | 0 | 15.6 s |
| KXWTI15M | 181 | same | same | same | 23,464 (100.0%) | 0 | 15.6 s |
| KXEURUSD15M | 181 | same | same | same | 22,566 (100.0%) | 0 | 15.6 s |
| KXGBPUSD15M | 181 | same | same | same | 23,089 (100.0%) | 0 | 15.6 s |
| KXUSDJPY15M | 181 | same | same | same | 24,812 (100.0%) | 0 | 15.6 s |
| KXAUDUSD15M | 181 | same | same | same | 26,395 (100.0%) | 0 | 15.6 s |
| KXUSDCAD15M | 181 | same | same | same | 26,864 (100.0%) | 0 | 15.6 s |
| KXNATGAS15M | 181 | same | same | same | 27,603 (100.0%) | 0 | 15.6 s |
| KXHYPE15M | 181 | same | same | same | 26,428 (100.0%) | 0 | 15.6 s |
| KXBNB15M | 181 | same | same | same | 27,986 (100.0%) | 0 | 15.6 s |
| **KXINX15M** | **13** | 2026-11-13T17:00Z | 2026-11-13T20:00Z | Nov 13 only, **one run** | 2,262 (100.0%) | 0 | 5.1 s |

A full 48 hours would be about 194 windows, so about 13 windows of each of the 11 are missing to the gaps above. NC15 stops by itself on 2026-12-31 23:59Z. **Weekends are not in these files yet** (Nov 11 to 13 is Wednesday to Friday): whether the FX, metals and oil series list windows on Saturday and Sunday is not known from these data. KXINX15M has about 3 hours of recording, so its first full day is Nov 14 at the earliest (and only weekdays have windows).

## 3. Candles with `open_interest`

OICORE's live code reads `open_interest_fp` from the public candlesticks answer (`functions/kalshiSlotRunLib.js` lines 59 to 61 and 247 to 249). **Checked by field names only:** in a landed candle answer of another series (the esports run VOIDSNAP_CANDLES) all 10,036 candles carry `open_interest_fp` beside `volume_fp`, `price`, `yes_bid`, `yes_ask`. That shows the field is part of the candle shape; it does NOT show that each of the new markets returns a populated value (a market that has no open interest could return a zero or an absent field). No landed candle run of ETH, XRP, silver, copper, WTI, FX, HYPE, BNB or KXINX15M was opened (the WHEEL0 runs are held until after the DEPTH1 read; SPXOI1_CANDLES has not landed). **Per market the answer is therefore "not known"; the test is one candlestick request per market (11 requests), which needs Main's allocation.** The research recorders save no per-candle open interest for any of these markets (R6 and NC15 save books and tape, not candles).

## 4. Extra live read budget (from the slot code, counts only)

For each added market, per 15 minute window, the slot tick does: (a) the quote read: markets of series outside L1's fixed list are read only in the minute or two before their entry span (`slotCalendarSeriesDue` and `slotSessionSeriesDue`, `functions/index.js` around line 687 to 692), about one public market read per series per window, none on other minutes; (b) the open interest condition: ONE public candlesticks GET per market (`start_ts` = close minus 480 s to `end_ts` = close minus 60 s, 1 minute interval) after the quote passes the band and spread tests (`kalshiSlotRunLib.js` 243 to 250), so at most one per market per window; (c) a skip or shadow row, one Firestore write per market per window at most (`kalshiSlotSkips`; the H1 controller's shadow rows would be the same count). **Totals for the 11 NC15 series plus Ethereum and XRP (13 markets, if all are added):** at most 13 quote reads and 13 candle reads per window, 26 public reads and 13 writes per 15 minutes, about 104 reads an hour at the peak (the 11 NC15 markets trade fewer hours: forex and metals are closed from Friday 17:00 to Sunday 18:00 Central). No Kalshi key; the one existing retry is `liveRequest`'s single re-ask of a 429. The queue's H1 line (RND_QUEUE.md 653: "a reviewed code list of markets inside a read budget") gives no number; I did not find a budget figure in the code or the queue, so none is stated here.

## 5. Update, Nov 14 at about 01:25Z: the open interest field check (OIFIELD_CHECK) has landed
One batched candlesticks request (run pull/OIFIELD_CHECK/2026-11-14T0114Z_43539336412, COMPLETE by pre-check), 11 NC15 non-crypto tickers of the window closing 2026-11-13T19:00Z, 8 one-minute candles each (88 candles). Read with `oifield_read.py` (only market_ticker and open_interest_fp; no price, book, trade or result). Result: **`open_interest_fp` is present and populated (a finite number) and nonzero in all 8 candles of all 11 tickers** (silver, copper, WTI, EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD, natural gas, HYPE, BNB), and it takes a different value in nearly every minute (distinct values per ticker 8 of 8, except GBP/USD 7 of 8). So the per-candle open interest that OICORE's live code reads exists for these markets in the public candles. One window and 8 minutes per market: it shows the field is there, not that it is populated in every window or at other hours. Section 3 above ("per market not known") is answered for this window.
