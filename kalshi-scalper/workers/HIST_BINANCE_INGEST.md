# INGEST 1: Binance Vision BTC and ETH (spot 1m, perp 1m, perp funding)

Approved under the Charter (Nov 7, 2026). Script: `src/scalper/histbinance.py` (resumable fetch plus clean, stdlib only). Data: `data/hist_binance/` (git-ignored, verified with `git check-ignore`). No strategy statistic was computed.

## What was fetched, and from where

Host that works: `https://data.binance.vision/data/...` (bulk zips, HEAD and GET both 200). Binance main API (451) was not used. No 403, 429 or 451 came back from this host in 1,080 requests, so nothing is blocked here. One transient curl failure (HTTP code 0) was retried by rerunning the resumable job.

Layout: `data/hist_binance/<SYMBOL>_<stream>/<YYYY-MM>.csv.gz` (monthly for complete months to 2026-10, one file per day for 2026-11-01 to 2026-11-06) and `manifest.json` (per-file status, rows, defects, checksum result). Columns for klines: `ts_s, open, high, low, close, volume, trades, taker_buy_base_vol` (ts_s is the unix second of the bar OPEN). Funding: `ts_s, interval_hours, rate`. `histbinance.load(symbol, stream)` returns rows. Quote volume and the other columns of the raw files are dropped.

Every zip was checked against its `.CHECKSUM` file: 540 of 540 matched, none missing. Politeness: 0.3 s before each request.

## Per symbol and stream

| Stream | First (UTC) | Last (UTC) | Rows | Missing minutes (gaps) | Zero-volume bars | Dup | Bad OHLC | MB on disk |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT spot 1m | 2019-01-01 00:00 | 2026-11-06 23:59 | 4,124,391 | 4,089 (22) | 287 | 0 | 0 | 106.9 |
| ETHUSDT spot 1m | 2019-01-01 00:00 | 2026-11-06 23:59 | 4,124,390 | 4,090 (22) | 288 | 0 | 0 | 96.4 |
| BTCUSDT perp 1m | 2020-01-01 00:00 | 2026-11-06 23:59 | 3,601,440 | 1,440 (1) | 369 | 0 | 0 | 83.8 |
| ETHUSDT perp 1m | 2020-01-01 00:00 | 2026-11-06 23:59 | 3,601,440 | 1,440 (1) | 302 | 0 | 0 | 84.2 |
| BTCUSDT funding | 2020-01-01 00:00 | 2026-10-31 16:00 | 7,488 | 0 gaps over 8h | n/a | 0 | 0 | under 0.1 |
| ETHUSDT funding | 2020-01-01 00:00 | 2026-10-31 16:00 | 7,488 | 0 gaps over 8h | n/a | 0 | 0 | under 0.1 |

Total on disk: 356 MB (`du`). The perp klines and funding files start 2020-01 (the 12 monthly files for 2019 answered 404 and are recorded as `absent_404`; the perp contract has Vision files from 2020-01). Funding is 8 hourly throughout; the funding files carry only complete months, so the last funding row is 2026-10-31 16:00 (November's partial month is not published as a monthly file and was not fetched). Spot and perp end on 2026-11-06, the last complete UTC day before the run.

Defects, by name:

- **Missing minutes, spot:** 22 gaps, identical in BTC and ETH (so they are exchange-wide maintenance or outage windows, not file damage). Lengths in minutes: 360, 600, 61, 480, 140, 3, 120, 60, 354, 128, 150, 210, 60, 230 (231 in ETH), 60, 79, 90, 150, 284, 270, 120, 80. All fall 2019-03 to 2021-09 except one on 2023-03-24 12:39 (80 min). Several start at 01:59 or 02:59 UTC, the maintenance window. None from 2023-04 to 2026-11. Gaps are NOT filled; a user must treat a bar after a gap as having no valid prior minute.
- **Missing minutes, perp:** one whole day, 2026-10-28 (1,440 minutes), in both symbols. The spot data for that day is complete. Not filled.
- **Zero-volume bars:** spot 2019 to 2021 and 2023 only (BTC by year: 2019 76, 2020 50, 2021 89, 2023 72; ETH 78, 49, 89, 72), none 2022 or 2024 on. Perp: scattered in every year 2020 to 2025 (BTC 2, 59, 64, 118, 89, 37). Kept in the file with volume 0 (flat O=H=L=C bars); a user decides whether to treat them as no trade.
- **Duplicate timestamps, non-monotonic order, bad OHLC (high under low, or open/close outside the range), timestamps off the minute:** 0 in every file.
- **Header rows:** futures files carry a header; skipped. Spot files have none.

## The 2025 timestamp unit change (handled and tested)

Binance Vision spot files switched from milliseconds to microseconds with the 2025-01-01 file. `norm_ts` converts any value of 1e15 or more (microseconds; a millisecond stamp reaches 1e15 only in year 33658) to milliseconds, then to seconds. Checked on the boundary: 2024-12-31 23:59 (millisecond file, 2024-12) has close 93,576.00 and 2025-01-01 00:00 (microsecond file, 2025-01) opens at 93,576.00, ts 1,735,689,540 and 1,735,689,600, one minute apart. The manifest counts microsecond rows: 972,000 per symbol, which equals exactly 675 days times 1,440 (2025-01-01 to 2026-11-06). Perp files stayed in milliseconds (0 microsecond rows).

## Cost

Disk: 356 MB for 7.85 years of two symbols and three streams, about 45 MB per year. Time: the whole ingest (both symbols, all streams, 540 zips plus 540 checksum files) took 921 seconds, about 15 minutes (the sleep is 0.3 s per request, so most of it is download and gzip). A measured single-symbol run for 2024-01 to 2026-11 (2.85 years, three streams) took 233 seconds, so about 82 seconds per symbol-year; the full run averaged about 60 seconds per symbol-year. One year for both symbols and all three streams is therefore about 2 minutes and 45 MB. Resume: rerun the same command; files already marked ok in the manifest are skipped. To refresh: rerun with the same arguments; the monthly file for a newly complete month and new daily files are picked up (the current-month daily files that are already ok are kept).

## What this data is, and what tests it can and cannot support

This is an UNDERLYING path (Binance spot and the USD-M perpetual), not Kalshi's contract price. Binance BTCUSDT is a different venue from the reference Kalshi's crypto markets settle on, so even the underlying is a proxy (the Kalshi rulebook source for the reference index is not checked here).

Can support:
- Rules defined on the underlying path alone, for the Kalshi 15 minute crypto markets: the shape of the last 6 to 10 minutes (smooth climb, `rise3`, `rng5`, flips0 analogues built on the underlying instead of on the contract's mid), the probability the underlying finishes a 15 minute window above or below where it was at the 10 or 6 minute mark, and how that depends on the move so far, volatility and the hour. This gives a long, many-regime estimate of how often a given underlying move REVERSES in the remaining minutes, which is the physical quantity the 88c to 97c band is betting on.
- Funding research (FUND1 style) on a perp: 6.8 years of 8 hourly funding for both symbols, with 1 minute perp prices to mark each funding interval. Venue caveat: Binance, not Kalshi's perpetual.
- Spot-vs-perp basis and lead-lag at 1 minute, and regime or volatility context for any crypto family.

Cannot support:
- Any profit, fill or profit factor for a Kalshi contract. The price paid (the ask in the 88c to 97c band), the spread, the fee, the depth and the fill are not in this data. A backtest on this data alone can only say how often the underlying did something, never what the contract cost.
- Minute data is open, high, low, close: the exact crossing order inside a minute, and the settlement average (if the market settles on an average of the last seconds) are not recoverable.
- Anything about gold (not in this ingest), natural gas, forex or the other markets.
- Bars missing in the gaps listed above (about 0.1 percent of 2019 to 2021 minutes).

Linking to Kalshi's price needs a QUOTE MODEL calibrated on the Kalshi contract data: the crypto 15 minute candles and fills in `data/fresh.sqlite` and the Dec 2025 onward data from the other ingest (BTC and ETH 15 minute markets exist from 2025-12-11 only, about 11 months). The honest chain is: (1) fit the contract's price at minute m-before-close as a function of the underlying's distance to strike and time left, on the Kalshi months where both exist; (2) check that fit by period, not pooled; (3) apply it to the underlying history to get a MODELLED contract price for 2019 to 2025; (4) any result from step 3 is a model result, to be labelled as such and never quoted next to a live figure. A model fitted on 11 months of one regime is the weak link: it inherits the Kalshi market's pricing of that period, which may differ from earlier years.

## Held-out arithmetic

Underlying history available: spot 2019-01-01 to 2026-11-06, which is 7.85 years (perp 6.85 years). Calendar years: 2019, 2020, 2021, 2022, 2023, 2024, 2025, plus 2026 to date (10.2 months). Gaps by year are listed above and 2022, 2024 and 2025 have no spot gaps.

- Charter three windows plus a final held-out slice, on whole years: W1 2019 to 2020 (2 years), W2 2021 to 2022 (2 years), W3 2023 to 2024 (2 years), held out untouched: 2025 plus 2026 to date (1.85 years). Each window then holds roughly 70,000 fifteen minute windows per symbol (35,000 per year), and the held-out slice about 65,000. Alternative: W1 2019 to 2021 (3 years), W2 2022 to 2023, W3 2024 to 2025, held out 2026 to date (0.85 year, about 30,000 windows). The first split keeps the held-out slice a full-ish year and is the recommended one.
- Cost of the held-out slice: it can be read ONCE. If a rule is fitted or even looked at on 2025 to 2026, it is no longer held out, and with no further data to fetch the next held-out slice is forward data only (the live record, which is not an independent sample of the same size).
- Overlap with Kalshi data: only 2025-12-11 onward has contract prices. So any test that includes the contract price is limited to about 11 months, the same as today; this ingest adds years only for the underlying part of the claim, and the quote model above is the bridge, with the limits stated.
- Counting windows is not counting independent trades: BTC and ETH move together, so a window where both fire is one bet, and 15 minute windows on one underlying are autocorrelated in volatility. The effective sample is smaller than the row counts, and should be stated per window before a bar is set.
- The number of rule variants tried must be deflated for, as in the Charter bar, and the number tried on THIS data counts from the first look.
