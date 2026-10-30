# REFINE-COUNTS R1 and R3 (counts only, not a try, N unchanged)

Script: `src/scalper/refine_counts.py`. Candle bid/ask and each market's close time only. No result, win or loss, settledPnl, payout, final price or any outcome column was selected or written. No win rate, PF or P&L appears anywhere. CSVs: `workers/REFINE_R1_counts.csv`, `workers/REFINE_R3_counts.csv`.

## Definitions

- Look: the 1 minute candle ending exactly 360 s before the close (`close_ts - 360`). `kalshiLiveLib.js` (read only): `L1_WINDOW_MS = [330000, 400000]`, `entryLead` gives "6m" to every series not in `EARLY_PROBE_SERIES` (XRP, natural gas), so gold and Dogecoin both decide at 6 minutes.
- Pick, as in `l1Pick`: a usable two sided quote (`valid_quote`), then YES at its ask if the ask is in the cell, else NO at `1 - bid` if that is in the cell. Prices rounded to 4 places, 1e-9 tolerance as in live.
- Cell edges (price of the bought side), each window goes to the first cell it fits, live band first:
  - **band_88_97**: 0.88 <= price <= 0.97 (the existing band, edges inclusive, same as `L1_BAND`).
  - **c_86_88**: 0.86 <= price < 0.88 (88c belongs to the band, not here).
  - **c_97_98**: 0.97 < price <= 0.98 (97c belongs to the band).
- Dates and hours are US Central, from the market's close time. Weeks run Monday to Sunday (Central). A window is "on file" if its market has at least one candle row in any local database (all `data/*.sqlite` merged by ticker, union of candles).
- no_candle_windows: windows on file with no candle ending exactly at the 6 minute look. bad_quote_windows: candle present but not a usable two sided quote (empty book); counted as no entry.
- CSV note for R1: `no_candle_windows`, `windows_on_file` and `bad_quote_windows` are per series and day and repeat on each of the three cell rows; do not sum them across cells.

## History span

- Gold (KXGOLD15M): 2026-08-05 to 2026-10-30 (76 days with windows, 5,877 windows on file). Dogecoin (KXDOGE15M): 2026-08-05 to 2026-10-30 (87 days, 8,111 windows). So the file is about 87 days long, longer than the 69 expected. Both first and last days are partial (08-05 has 20 windows, 10-30 has 38).
- Missing candles at the look: gold 2 windows (2026-08-06 and 2026-08-13, one each); Dogecoin 0. Unusable quotes: gold 10, Dogecoin 3.
- Gold is a weekday market, so low window counts are expected rather than missing data: no windows on 11 Saturdays (08-08, 08-15, 08-22, 08-29, 09-05, 09-12, 09-26, 10-03, 10-10, 10-17, 10-24; 09-19 has 3, 08-09 has 3), about 26 to 27 on Sundays, about 65 on Fridays since 09-20 (66, 65), full days about 90 to 95. Dogecoin has about 95 windows every day except the two partial edge days. Per-day counts for every day are in the CSV (`windows_on_file`).
- Limit: a market with no candle rows at all would not appear in `windows_on_file`, so that count cannot see a window whose whole candle history is absent.

## R1 weekly totals (entries per Central week, Monday start)

Gold:

| Week from | days | 86-88c | 88-97c | 97-98c | no candle |
|---|---|---|---|---|---|
| 08-03 (partial) | 4 | 8 | 65 | 20 | 1 |
| 08-10 | 6 | 16 | 145 | 19 | 1 |
| 08-17 | 6 | 15 | 176 | 12 | 0 |
| 08-24 | 6 | 17 | 154 | 22 | 0 |
| 08-31 | 6 | 29 | 137 | 15 | 0 |
| 09-07 | 6 | 16 | 150 | 15 | 0 |
| 09-14 | 7 | 17 | 156 | 19 | 0 |
| 09-21 | 6 | 19 | 129 | 21 | 0 |
| 09-28 | 6 | 15 | 139 | 14 | 0 |
| 10-05 | 6 | 23 | 134 | 16 | 0 |
| 10-12 | 6 | 18 | 122 | 17 | 0 |
| 10-19 | 6 | 15 | 132 | 18 | 0 |
| 10-26 (partial, to 10-30) | 5 | 25 | 107 | 13 | 0 |

Gold, mean of the 10 full weeks 08-17 to 10-19: 18.4 (86-88c), 143 (88-97c), 16.9 (97-98c) a week.

Dogecoin:

| Week from | days | 86-88c | 88-97c | 97-98c | no candle |
|---|---|---|---|---|---|
| 08-03 (partial) | 5 | 14 | 140 | 22 | 0 |
| 08-10 | 7 | 33 | 228 | 23 | 0 |
| 08-17 | 7 | 24 | 218 | 41 | 0 |
| 08-24 | 7 | 31 | 222 | 43 | 0 |
| 08-31 | 7 | 26 | 199 | 34 | 0 |
| 09-07 | 7 | 26 | 222 | 38 | 0 |
| 09-14 | 7 | 21 | 236 | 40 | 0 |
| 09-21 | 7 | 30 | 210 | 52 | 0 |
| 09-28 | 7 | 26 | 199 | 46 | 0 |
| 10-05 | 7 | 27 | 204 | 49 | 0 |
| 10-12 | 7 | 28 | 177 | 25 | 0 |
| 10-19 | 7 | 32 | 170 | 29 | 0 |
| 10-26 (partial, to 10-30) | 5 | 14 | 123 | 20 | 0 |

Dogecoin, mean of the 11 full weeks 08-10 to 10-19: 27.6 (86-88c), 207.7 (88-97c), 38.2 (97-98c) a week. The 88-97c count has fallen over the last three weeks (177, 170, 123 in a partial week) against about 215 earlier; this is a count, not a judgement. Daily counts by cell are in the CSV.

## R3 Dogecoin 88c to 97c entries by Central hour of the close

The band at the 6 minute look, all 87 days, 2,548 entries in total. Hour is the close time's hour (a window closing 14:00 to 14:59 is hour 14). Total over the whole history by hour:

| hour | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| entries | 97 | 103 | 96 | 102 | 92 | 109 | 115 | 103 | 104 | 108 | 109 | 81 |

| hour | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| entries | 93 | 106 | 129 | 112 | 99 | 109 | 110 | 103 | 114 | 117 | 124 | 113 |

Roughly flat across the day (81 to 129 per hour over 87 days, about 1 per hour per day); each hour has 4 windows a day, so per-hour per-day counts in the CSV are 0 to 4. Hours with a daylight saving change would have 23 or 25 hours that day; the only change in the span is the November one, after the data (2026-11-01).

## Caveat: candle replay against live

This is a candle based replay, not the live order records. ETHFUNNEL (`ETHFUNNEL_RESULT.md`) found the replay matched live to within 1 of 556 windows for Ethereum and Bitcoin (99.8%), but the Dogecoin band replica disagreed on **4.68%** of windows (26 of 556: 19 where the replay would order and no record exists, 7 where a record exists and the candle close was not in band). That check was on Dogecoin's 88-97c band only and nothing was verified for gold, nor for the two outer cells (no live orders exist outside the band). Counts here also do not model balance, the window cap, one crypto order per window, the 12% stop or a bot outage; they count windows whose quote was in the cell, not orders placed. The 360 s candle close is not the quote at the tick, and it can be a different price. Gold counts include windows in which the live bot would have had Dogecoin or XRP ahead of it only for crypto; gold is never blocked by that rule.
