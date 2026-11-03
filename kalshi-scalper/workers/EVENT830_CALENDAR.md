# EVENT830 release calendar, Nov and Dec 2026 (research only)

Retrieved 2026-11-03. Every row is a US **8:30 ET** release. Eastern standard time applies from 2026-11-01, so 8:30 ET = **13:30 UTC = 7:30 am Central**.
The window to watch is the 15 minute market that **closes** at that time (opens 13:15 UTC, 7:15 CT); the look candle ends 13:27 UTC (7:27 CT) and the fill candle 13:28 UTC (7:28 CT).
Series: all 8 (KXSILVER15M, KXCOPPER15M, KXWTI15M, KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M, KXHYPE15M, KXBNB15M). Frozen list in `src/scalper/event830.py` (`RELEASES`).
Sources read today: bea.gov/news/schedule/full (200), census.gov/retail/release_schedule.html (200), dol.gov/ui/data.pdf (200; shows only the current week's embargo line), federalreserve.gov (200; no FOMC in scope).
bls.gov answered 403 (not worked around), so jobs, CPI and PPI dates are the CAL worker's reading of the BLS 2026 schedule on 2026-10-29 (`studies/EVENT_CALENDAR_2026.csv`, status verified). Claims are the standing Thursday rule.

## First ten qualifying dates (Central time)

| # | Date (CT) | Window closes (CT) | Release | Status |
|---|---|---|---|---|
| 1 | Thu 2026-11-05 | 7:30 am | Weekly jobless claims | by rule |
| 2 | Fri 2026-11-06 | 7:30 am | Employment Situation, Oct | confirmed |
| 3 | Tue 2026-11-10 | 7:30 am | Consumer Price Index, Oct | confirmed |
| 4 | Thu 2026-11-12 | 7:30 am | Weekly jobless claims | by rule |
| 5 | Fri 2026-11-13 | 7:30 am | Producer Price Index, Oct | confirmed |
| 6 | Tue 2026-11-17 | 7:30 am | Advance retail sales, Oct | confirmed |
| 7 | Thu 2026-11-19 | 7:30 am | Weekly jobless claims | by rule |
| 8 | Wed 2026-11-25 | 7:30 am | GDP second estimate Q3 and Personal Income and Outlays (PCE), Oct | confirmed |
| 9 | Thu 2026-12-03 | 7:30 am | Weekly jobless claims | by rule |
| 10 | Fri 2026-12-04 | 7:30 am | Employment Situation, Nov | confirmed |

## Full list, Nov and Dec 2026

| Date | Day | ET | UTC | CT | Event | Window close to watch (UTC) | Series | Type | Status |
|---|---|---|---|---|---|---|---|---|---|
| 2026-11-05 | Thu | 08:30 | 13:30 | 07:30 | Weekly jobless claims | 2026-11-05 13:30 | all 8 | CLAIMS | by rule (Thursday 8:30 ET; DOL release of 2026-10-29 read, per-date page not published) |
| 2026-11-06 | Fri | 08:30 | 13:30 | 07:30 | Employment Situation, Oct | 2026-11-06 13:30 | all 8 | JOBS | confirmed (BLS schedule read by CAL 2026-10-29; BLS answers 403 here) |
| 2026-11-10 | Tue | 08:30 | 13:30 | 07:30 | Consumer Price Index, Oct | 2026-11-10 13:30 | all 8 | CPI | confirmed (BLS via CAL 2026-10-29) |
| 2026-11-12 | Thu | 08:30 | 13:30 | 07:30 | Weekly jobless claims | 2026-11-12 13:30 | all 8 | CLAIMS | by rule |
| 2026-11-13 | Fri | 08:30 | 13:30 | 07:30 | Producer Price Index, Oct | 2026-11-13 13:30 | all 8 | PPI | confirmed (BLS via CAL 2026-10-29) |
| 2026-11-17 | Tue | 08:30 | 13:30 | 07:30 | Advance retail sales, Oct | 2026-11-17 13:30 | all 8 | RETAIL | confirmed (census.gov release schedule, read today: November 17, 2026) |
| 2026-11-19 | Thu | 08:30 | 13:30 | 07:30 | Weekly jobless claims | 2026-11-19 13:30 | all 8 | CLAIMS | by rule |
| 2026-11-25 | Wed | 08:30 | 13:30 | 07:30 | GDP second estimate Q3 and Personal Income and Outlays (PCE), Oct | 2026-11-25 13:30 | all 8 | GDP_PCE | confirmed (bea.gov full schedule, read today: November 25, 8:30 AM, both) |
| 2026-12-03 | Thu | 08:30 | 13:30 | 07:30 | Weekly jobless claims | 2026-12-03 13:30 | all 8 | CLAIMS | by rule |
| 2026-12-04 | Fri | 08:30 | 13:30 | 07:30 | Employment Situation, Nov | 2026-12-04 13:30 | all 8 | JOBS | confirmed (BLS via CAL 2026-10-29) |
| 2026-12-10 | Thu | 08:30 | 13:30 | 07:30 | Consumer Price Index, Nov, and weekly claims (one window) | 2026-12-10 13:30 | all 8 | CPI_CLAIMS | CPI confirmed (BLS via CAL); claims by rule |
| 2026-12-15 | Tue | 08:30 | 13:30 | 07:30 | Producer Price Index, Nov | 2026-12-15 13:30 | all 8 | PPI | confirmed (BLS via CAL 2026-10-29) |
| 2026-12-16 | Wed | 08:30 | 13:30 | 07:30 | Advance retail sales, Nov | 2026-12-16 13:30 | all 8 | RETAIL | confirmed (census.gov, read today: December 16, 2026) |
| 2026-12-17 | Thu | 08:30 | 13:30 | 07:30 | Weekly jobless claims | 2026-12-17 13:30 | all 8 | CLAIMS | by rule |
| 2026-12-23 | Wed | 08:30 | 13:30 | 07:30 | GDP third estimate Q3 and Personal Income and Outlays (PCE), Nov | 2026-12-23 13:30 | all 8 | GDP_PCE | confirmed (bea.gov full schedule, read today: December 23, 8:30 AM, both) |

## Left out on purpose

- Holiday-week claims **2026-11-26** (Thanksgiving), **2026-12-24** and **2026-12-31**: the day and time are not confirmed (DOL page gives only the current week), so no window is evaluated. If DOL confirms, append the date; do not guess.
- Any release not at 8:30 ET (ISM and Conference Board 10:00, EIA, FOMC 14:00) and minor 8:30 releases (import prices, trade balance, housing starts, durable goods): not part of the trigger. The minor ones sit in the control, which dilutes the contrast (conservative).
- January 2027 on: not yet frozen. Append from official schedules (BEA, Census and BLS pages) before each window closes; claims by Thursday rule. Daylight saving time begins 2027-03-14, after which 8:30 ET = 12:30 UTC and the list must use that.
- Expected volume: 8 qualifying dates in November, 7 in December (15 total), about 4.8 eligible trades per date, so about 70 trades by 2026-12-31 and 40 fills near 2026-12-04.
