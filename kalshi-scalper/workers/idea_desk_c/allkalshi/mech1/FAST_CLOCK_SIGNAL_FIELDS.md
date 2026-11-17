# MECH1 fast-clock side: signal fields we hold, markets with 10 or more signals a day (Desk C, Nov 17, 2026)
Built from FILE LISTINGS of the data branches (trees only, no blob opened) and the recorders' own column constants in scripts/. No outcome, price or result was read. "Signals a day" is the clock count: how many times a day the field changes or a window opens, not a count of trades. HOLDS: R6 gold, Bitcoin, Ethereum, XRP, Dogecoin are under H20 (open), nc15 Silver, Copper, WTI, EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD under H21 (to 1798070400), KXINX15M under H15 from Dec 1; HYPE, BNB and NATGAS 15 minute are unheld for closes before Nov 19 (H22). Desk A and the Verification Analyst apply HOLDS.json, this list is not a clearance.

Branch paths below are on origin; "files" counts committed .csv.gz folders or files.

## A. 15 minute series (96 windows a day per series; every series also gives one poll every 2 s inside a window)
| Family | Field | Clock | Source and path | Held range |
|---|---|---|---|---|
| 15m crypto and gold (KXBTC15M, KXETH15M, KXXRP15M, KXDOGE15M, KXGOLD15M) | best 5 YES and NO bid prices and sizes (depth, imbalance, spread, price level, price change) | every 2 s, 96 windows a day | quote-data `book15r6/<date>/<HHMM>/book.csv.gz` (cols t_send_ms, t_recv_ms, server_date_header, ticker, series, close_time, yes_bid_px_1..5, yes_bid_sz_1..5, no_bid_px_1..5, no_bid_sz_1..5); recorder scripts/record_15m_book.py | 2026-10-29 to 2026-11-16, 104 folders |
| same five | public trade tape of each window (price, count, taker side, created time) | every trade, a window after the close | quote-data `book15r6/<date>/<HHMM>/trades.csv.gz` | same 104 folders |
| same five | window coverage and result, clock offset | per window; hourly clock check | `coverage.csv.gz` (close_time, series, ticker, polls, 429s, tape pages, trades, volume, result), `clock.csv.gz` | same |
| 15m non-crypto (Silver, Copper, WTI, EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD, HYPE, BNB, NATGAS, INX) | same book, tape and coverage fields, every 5 s | 96 windows a day (forex and metals shut at weekends) | nc-data `nc15/<date>/<HHMM>/{book,trades,coverage,clock}.csv.gz`; scripts/record_nc_book.py | 2026-11-11 to 2026-11-16, 31 folders |
| 15m crypto (Bitcoin, Ethereum, XRP, Dogecoin, Solana and gold) older recorder | YES bid and ask, sizes, strike, status, last 150 s of each window about twice a second | 96 windows a day | quote-data `quotes/<date>/<HHMM>/quotes.csv.gz` (t_send_ms, t_recv_ms, ticker, yes_bid, yes_ask, bid_size, ask_size, strike, status) | 2026-10-22 to 2026-11-16, 129 folders |
| spot prices for the same windows | Coinbase, Kraken, Bitstamp public trades (price, size, exchange time) in the 10 minutes before each close | every trade, 96 windows a day | quote-data `quotes/.../spot.csv.gz` (t_recv_ms, exchange, asset, price, size, exchange_time) | same 129 folders; Coinbase and Bitstamp reads are an owner-accepted terms risk |
| window results and per window poll coverage | settled result, poll counts | per window | `quotes/.../results.csv.gz`, `coverage.csv.gz`, `clock.csv.gz` | same |
| 15m Bitcoin with options context | Kalshi book plus Deribit marks (mark IV, underlying, index, strike, kind, expiry rank) every poll | 96 windows a day | quote-data `deribit/<date>/<HHMM>/{kalshi,deribit,index,results,coverage}.csv.gz` (recorder scripts/record_deribit.py) | 2026-11-02 to 2026-11-16, 85 folders |
| Bitcoin hourly ladder (KXBTCD, 7 strikes near the money) | best 5 YES and NO bids with sizes every 3 s from 55 minutes before each hourly close, plus the tape | 24 closes a day | quote-data `book/<date>/<HHMM>/{book,trades,coverage}.csv.gz`; `quotes/.../ladder.csv.gz` (near-money strikes, last 150 s, gold daily and weekly, BTC and ETH hourly) | book 2026-10-29 to 2026-11-16 (104 folders), ladder 104 folders |

## B. Perpetuals (stocks, indices, gold and other metals, oil, crypto): 1 minute bars, 1,440 candles a day per name that trades round the clock, fewer for stocks (regular hours 390 a day)
| Family | Field | Clock | Source and path | Held range |
|---|---|---|---|---|
| stock, index, metal and crypto perps | bid and ask OHLC, price OHLC, price mean, previous price, open interest, volume | every minute | perp-data `kalshi1m/<date>[.only].csv.gz` (ticker, end_period_ts, bid_open..ask_close, price_open..price_close, price_mean, price_previous, open_interest, volume); scripts/record_perps_candles.py | 2026-09-02 to 2026-11-15, 84 files (stocks only from Nov 5 when they listed; indices, gold, BTC, ETH go back to Sep) |
| same | funding rate and mark price, funding prints | each funding time (hourly for crypto, daily 16:00 ET for stocks) | perp-data `funding/<date>[.only].csv.gz`, `by-ticker.csv.gz`, `all-history.csv.gz` (ticker, funding_time, funding_rate, mark_price) | 2026-09-02 to 2026-11-15, 86 files |
| all 88 perps on the public list | quote, size, price, reference price, settlement mark, liquidation mark, halt sources, is_open, leverage | every 30 s inside the open and close windows (and every 10 s on Sunday evenings) | perp-data `perps30/<date>/{open,close}.csv.gz` (record_perps_fast.py), `perps/perps-<date>.csv` hourly (record_perps.py) and `perps/perps-lev-<date>.csv` | perps30 2026-11-06 to 2026-11-16 (3 files), hourly 2026-10-21 to 2026-11-17 (30 files) |
| cash side of the same names | Yahoo 1 minute bars | every minute | perp-data `cash1m/<date>.csv.gz`; STOPPED after Nov 11 (Yahoo terms), data stays | 2026-11-06 to 2026-11-11, 4 files |
| perps trade tape (60 day back-pull, Main building, not landed) | every trade, price and size | every trade | not yet in any branch | pending |

## C. Event and other fast feeds
| Family | Field | Clock | Source and path | Held range |
|---|---|---|---|---|
| NBA, NHL, NFL in game | moneyline, spread, total bid, ask, sizes, last, volume | about 20 s while a game is hot, 2 minutes before | sports-data `ingame/<date>/<HHMM>/{obs,coverage}.csv.gz` (t_recv_ms, server_date, event, kind, ticker, strike, yes_bid, yes_ask, bid_size, ask_size, last_price, volume) | 2026-11-08 to 2026-11-16, 47 folders |
| BTC liquidations | OKX liquidation side, size and bankruptcy price | every event | quote-data `oklq/<date>/<HHMM>/liquidations.csv.gz` | 2026-11-11 to 2026-11-16, 24 folders |
| politics quotes | bid, ask, sizes every 30 minutes (slow, under 10 a day per market) | 30 minutes | pol-data `polrec/<date>/<HHMM>/quotes.csv.gz`, `results.csv.gz` | 2026-11-11 to 2026-11-17 |
| combos | quote, book, trades | every 30 minutes (slow) | combo-data `combo/...` | 2026-11-12 to 2026-11-17 |
| daily, REF, weather | Kalshi count and weather brackets and reference pages | 15 minutes to hours (slow) | quote-data `daily/runs`, `ref/runs`, `wxens/runs` | 2026-11-04 to 2026-11-17 |

## What does NOT give 10 or more signals a day
politics, combos, ref, weather and the hourly perps list (24 a day but with only a handful of fields); sports pregame (`sportspre`, stopped Nov 11: ESPN terms).

## Schema notes for Desk A (MECHANISM_ENGINE_SPEC.md section 1)
- Signal fields in the spec map to columns above: price level and change (bid/ask columns), spread (ask minus bid), book depth or imbalance (the 5 level size columns), open interest (kalshi1m open_interest, deribit kalshi.csv open_interest), volume, funding rate (funding_rate), settlement mark (perps `settlement_mark`), trade tape flow (trades.csv.gz, record_quotes spot), a spot price elsewhere (spot.csv.gz), a cross-market residual (any pair above).
- No funding rate exists for the 15 minute markets; no settlement mark for them; open interest exists only for perps candles, the BTC Deribit-linked feed and the older 15m quote file by market, not in R6 or nc15.
- Gaps: R6 and nc15 have one result per window only in coverage.csv.gz (read last); perps full-day files from Nov 6 for stocks, `.only` files are candles only.
