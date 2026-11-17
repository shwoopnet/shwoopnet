# Recorder spec: perps public trade tape and the 17:00Z settlement marks (Forensics Desk, 2026-11-17, for Main)

Research only. Public GET, no key, no auth header, no order, generic User-Agent, redirects refused, own branch `perp-live-data` (orphan, as the live recorder), gzipped CSV by hour, built-in token only, six-try push loop, never main, no live figures. Stops itself on 2027-02-26. Extends `scripts/record_perps_live.py`; no new workflow, no new schedule, same concurrency group (never cancels a running job).

## 0. Facts that bind the spec
- The hourly snapshots of Oct 21 to Nov 13 hold only 3 to 7 rows a day. That gap is PERMANENT: the snapshot cannot be re-made, and no recorder can fill it. Anything that needs minute prices before Nov 14 uses the Kalshi 1 minute candles (back-servable) and nothing else. FUNDX2 scored 0 trades for this reason; its forward version FUNDX2-F reads Nov 24 on the live recorder's rows.
- The live recorder already stores, once a minute for every market, `settlement_mark_price`, `reference_price` and `liquidation_mark_price` (the list read). So the 17:00Z mark is ALREADY captured at one minute resolution from the day the recorder started (Nov 16); what is missing is a labelled daily row and a cross-check, not a new read.

## 1. Trade tape (GET /margin/trades)
- Documented: ticker optional (omit = all margin markets), limit 1 to 1000 (default 100), cursor, min_ts, max_ts, is_block_trade; fields trade_id, ticker, count, price, created_time, taker_side, is_block_trade. Retention not stated; depth UNTESTED.
- Recorder step: every 5 minutes inside the existing job, one GET with no ticker, `min_ts` = the last poll's newest created_time minus 60 s (overlap, de-duplicated by trade_id, id not stored), limit 1000, follow the cursor to the end. Columns kept: receive time, server Date header, ticker, created_time, price, count, taker_side, is_block_trade. File `perplive/<date>/<HH>/tape.csv.gz`; coverage row per poll (pages, trades, duplicates dropped, 429s, newest created_time, whether the cursor ended).
- Request budget: 288 polls a day plus pages. A quiet market day is about 1 page a poll, so about 300 to 600 requests a day, 0.2 to 0.4 a minute, at 10 tokens each. The live recorder now spends about 2 requests a minute plus 12 a minute in the fast lane (14:30 to 21:00Z weekdays); the tape adds under 3 percent. The fast lane's last read showed n429 = 0 (to be re-checked at 15:10Z Nov 17); the published Basic read budget is 400 tokens a second, so this is far under it. A 429 waits 2 s doubling to 30; three in a row end the step, not the job; a short tape poll never delays the 60 s list read (run the tape step after it, bounded to 20 s).
- Ordering: 10 trades a second would need more than 1,000 rows per 5 minutes; if a poll's cursor does not end within 5 pages (5,000 trades), write what was read, set `truncated=1` in the coverage row and read on at the next poll (min_ts keeps its place).
- One probe, before it is built (counts only, 1 request): on a WEEKDAY, GET /margin/trades with `min_ts` = 7 days ago, limit 1000, no ticker. Print only: HTTP code, number of trades returned, oldest created_time returned, whether a cursor came back. If the oldest is within 7 days and the cursor ends, the tape is back-servable and a one-time back-pull (about 20 requests per week of history, 1.2 s apart) replaces the safety copy; if the answer is empty or the oldest is only hours old, the recorder IS the only copy and starts at once. Saturday probes are inconclusive (market closed).
- Size: trades are small; about 2 to 8 MB a day gzipped if it holds the whole account's perps tape (estimate, not measured).

## 2. 17:00Z settlement marks
- What we need: the settlement mark each perp is marked to at its daily settlement, with the funding print's own `mark_price` (21:00Z, 14:00Z for gold, per the funding history) beside it, so an overnight or gap test can be priced at the mark and not at a quote.
- Already captured: `settlement_mark_price` at 60 s resolution in the list rows. Added step (no new request): at every list read between 16:55 and 17:05 UTC, the recorder also writes the row to `perplive/<date>/settle.csv.gz` with a `settle_window=1` flag, so the 17:00Z mark is one small file per day and the exact change at the instant can be seen. No extra read.
- Daily cross-check (one request a day): the first read after 21:15Z, GET /margin/funding_rates/historical with no ticker and start_ts = today 00:00Z, end_ts = tomorrow 00:00Z, written to `perplive/<date>/funding_day.csv.gz` (ticker, funding_time, rate, mark_price). That gives every market's print and mark price of the day (also repairs a missed funding day; the Nov 7 print is still missing from our funding file and needs one back-pull of start_ts 2026-11-07, end_ts 2026-11-08).
- Unknown, to be settled by the first week's rows, not guessed: whether the "17:00Z" mark moves at that instant or is fixed earlier. The settle file lets it be read from data.

## 3. Cost
- Runner minutes: no new job. The recorder is the existing continuous job (the 250 minute guideline is already exceeded by it, owner's merge accepted); this adds about 20 s of read time an hour, under 1 percent of its minutes.
- Branch size: tape 2 to 8 MB a day, settle files about 0.1 MB a day, funding_day about 0.05 MB a day, so about 100 to 250 MB by Feb 26 on `perp-live-data` (estimate; the recorder's own coverage rows will replace it).

## 4. Gates to write with the build (Main's tests)
PLT1 only the Kalshi external host and the three paths (/margin/markets, /margin/markets/orderbooks, /margin/trades, /margin/funding_rates/historical); PLT2 no key or auth header; PLT3 redirects refused; PLT4 429 backoff, three in a row ends the step and not the job; PLT5 tape step cannot run longer than 20 s and cannot delay the list read; PLT6 trade_id dedupe with overlap; PLT7 settle window rows flagged; PLT8 the stop date.

## 5. What this does NOT do
It does not fill the Oct 21 to Nov 13 snapshot gap, does not call any signed endpoint (the fee tier endpoint stays uncalled), does not place or read an order, and holds no live figures.
