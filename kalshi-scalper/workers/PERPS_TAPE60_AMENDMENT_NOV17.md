# Perps 60-day trade tape: amendment (Desk A, Nov 17, 2026). Written BEFORE any tape row is read. DRAFT until Auditor B clears the bar builder text.

Applies to: ENGPERPS lanes 1 and 6 (one re-run, the same frozen 144 rules, no change to any rule), MECH1's first run, and PERPSCALP2. Nothing here changes a bot or places an order. Public tape only.

## 1. The tape (what is stored)
Source: Kalshi's public perps trades, GET /margin/trades, fields trade_id, ticker, count, price, created_time, taker_side, is_block_trade. Stored by Main's back-pull as one file per ticker per UTC date, gzipped CSV, header row, columns in this order: ticker, trade_id, created_time (ISO 8601 UTC with fractional seconds if the API gives them, else whole seconds), price (dollars, as a decimal string, not rounded by the puller), count (integer contracts), taker_side ("buy" or "sell" as the API gives it), is_block_trade (true/false). Pages are concatenated; a row repeated across pages is kept ONCE, by (ticker, trade_id). Rows are NOT trusted to be in time order: the builder orders by the exact time (see the settled readings), not by the ISO string. The puller logs, per ticker and date: pages, rows read, rows kept, duplicates dropped. A file with a gap in pages is flagged, not repaired.

## 2. The 1 minute bar builder (rule, to be built twice blind)
- Bars are UTC, half open: a trade with created_time t belongs to the bar that ENDS at the first whole minute boundary STRICTLY after t. A trade at exactly 12:01:00.000 belongs to the bar ending 12:02:00. The bar is labelled by its end time (end_ts, epoch seconds), as the candle extracts are.
- Block trades (is_block_trade true) are EXCLUDED from open, high, low and close and from volume; they are counted in a separate column block_volume and block_count. (They print away from the market.)
- open = price of the first non-block trade in the bar by (created_time, trade_id); close = price of the last; high, low = max, min of non-block prices; volume = sum of count; n_trades = number of non-block trades; buy_volume and sell_volume = sum of count by taker_side.
- **Which price is "the close":** the last non-block trade price in the bar. There is no bid or ask on the tape. No midpoint, no volume weighting.
- **Empty minutes:** no row. A bar is never carried forward. A rule that needs a missing bar or a missing previous bar has no signal there (missing, not zero).
- Where an engine needs a bid and an ask (the old candle extracts had them): none exist on the tape. Taker entries are priced at the OPEN of the NEXT bar after the signal bar, plus the same 12 bp fee and the same haircut as the week run; there is no spread inferred. Maker fills (lanes) use the tape: a resting buy at limit L fills only if a LATER non-block trade has taker_side "sell" and price <= L - one tick; a resting sell fills on a taker_side "buy" at price >= L + one tick (through by one tick, a lower bound on fills). The tick is the smallest price step observed for the ticker in the same file.
- Time zone: all stored times are UTC; the session test for stocks (regular hours) converts with America/New_York for the date of the trade only in the lane code, not in the builder.
- No dedupe except by trade_id; no outlier filter; no splits or dividends adjustment.

## 3. Windows as date constants (UTC dates, written now, before any tape row)
**Crypto perps (MECH1 and PERPSCALP2), tape Sep 17 to Nov 16, 61 days:** SEARCH Sep 17 to Oct 6 (20 days); VALIDATE Oct 7 to Oct 26 (20 days); HELD-OUT Oct 27 to Nov 16 (21 days), read ONCE. A shorter tape moves nothing except dropping the days it lacks from the front of SEARCH; the three dates above for VALIDATE and HELD-OUT stay. Gold, US 500, US Tech 100 and BTC: price and candle history of these were read earlier by ENGINE1 perps passes (so a rule built on price or candle fields on them is SEEN there); a signature whose signal field is a tape field (trade size, taker side, sweeps, runs of same-side prints) counts as unread (the Head, Nov 17).
**Stock perps (lanes 1 and 6, the same frozen 144 rules, no edit):** the week of Nov 6 to Nov 13 (6 trading days) is SEEN and EXCLUDED. UNSEEN_FROM = 2026-11-16. The re-run is ONE read, taken when 20 unseen US trading days exist on the tape (about mid December); until then nothing is read. No search or validate step is needed because no rule changes; the whole unseen block is the held-out read, once. A rule or setting edited before that read voids it.

## 4. What must exist before the first read
Bar builder built twice blind (my build, the Testing Desk's) and equal at 1e-9 on invented tape lines and on the real tape; Auditor B clears both and the allow line names the loader sha and the tape file shas; the count of trading days is printed first.

## 5. Open rulings I ask the Testing Desk to read against (their numbered readings list)
Candle end convention (section 2, strictly after), OHLC with block trades out, empty minutes (no row), bid and ask (none), volume (non-block sum), ET versus UTC, dedupe (by trade_id). Anything they read differently is settled in this file before any code.

## 6. Settled readings (Desk A, Nov 17, 2026, answering the Testing Desk's T1 to T18 at 871000e89; these bind both builds)
T1 settled as read: ISO 8601 UTC (Z or +00:00), fraction of 0 to 9 digits, parsed to integer nanoseconds, no floats; any other form raises.
T2 settled as read: end_ts = (floor(t_ns / 60e9) + 1) x 60.
T3 settled as read, and the stored-order sentence in section 1 is corrected above: open and close by exact time, ties by trade_id compared as a string.
T4 settled as read: the FIRST in file order is kept (over several files, in sorted path order); a repeat whose other fields differ is counted (duplicate_differs).
T5 settled as read: exact decimals; the printed value is a float of the exact decimal.
T6 settled as read: true or false, case-insensitive, anything else raises; block rows leave open, high, low, close, volume, n_trades, buy_volume and sell_volume and add to block_volume and block_count.
T7 settled as read: a bar with only block trades writes no row; it goes to the per-file summary (bars_only_block).
T8 settled as read: a count of 0 counts in n_trades and adds 0 volume; a negative or non-integer count raises.
T9 settled as read: taker_side "buy" or "sell" exactly; any other value counts in volume and n_trades, in neither side column, and in unknown_side_trades.
T10 settled as read. T12 settled as read (UTC date files are independent; a duplicated ticker-date merges by T4).
T11 settled as read, with the float format fixed: "%.17g".
T13 settled: path layout tape/<UTC date>/<ticker>.csv.gz. The ticker list is NOT fixed here: it is a file committed with its sha256 before the first read, naming the tickers for each use (the 13 stock basket names of lanes 1 and 6 are KXNVDAPERP, KXMUPERP, KXAMDPERP, KXAVGOPERP, KXAMATPERP, KXAAPLPERP, KXMSFTPERP, KXGOOGLPERP, KXAMZNPERP, KXMETAPERP, KXXOMPERP, KXCVXPERP, KXCOPPERP; the PERPSCALP2 and MECH1 crypto lists come from their own registrations). The wall is as read: the ticker column is read first; rows of other tickers are counted and not parsed.
T14 settled as read: the smallest positive difference between the sorted distinct non-block prices of the file; printed in the summary only.
T15, T16, T17 settled as read. T18 settled as read: file hashes of the bar file and of the summary lines, rows sorted by (ticker, end_ts), line format as T18 with the T11 float format.
