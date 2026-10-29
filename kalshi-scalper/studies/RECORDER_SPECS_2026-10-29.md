# Recorder specs for new data (research branch, 2026-10-29)

Written for the owner after "widen the data". Each spec is public endpoints only, no key, and feeds one hypothesis that must be pre-registered in `kalshi-scalper/README.md` before any recorded row is read. Nothing here is a workflow; the owner reviews and merges any recorder on `main`.

Why recorders at all: every family that failed did so on cost, and three questions can only be answered with data Kalshi's history does not keep: **queue position** (resting-order fills), **depth beyond the touch** (size at a price), and **quotes in thin markets between trades** (hourly candles carry trades, not quotes, so CPI and mention markets showed no bid or ask before the event).

Common to every spec: store the poll time on our clock and the server `Date` header (the current recorder reports `clock_ok False`); gzip CSV per hour; one row per market per poll; endpoints `GET /trade-api/v2/markets/{ticker}/orderbook?depth=N` (returns `yes_dollars` and `no_dollars`, each a list of [price, size] bids; YES ask = 1 minus the best NO bid) and `GET /trade-api/v2/markets/trades?ticker=...&min_ts=...`. Measured latency about 0.18 s a call. Public rate limits allow roughly 10 calls a second sustained; every spec below stays under 3.

## R1. QUOTE2B, Bitcoin hourly ladder book and tape (already specified; the main session starts it 2026-10-29 03:50 UTC)

- Records: KXBTCD, the 7 strikes nearest the money of the event closing at the next hour, re-picked once an hour; order book depth 5 every 3 s; trade tape every 30 s.
- Size: about 50 MB a day raw, 6 to 8 MB gzipped; 14 days about 100 MB.
- Feeds: QUOTE2B (two-sided quoting with a real queue model). Counterparty: impatient takers crossing a 1c spread on the hourly ladder. Kill: profit factor under 1.5 after maker fees and measured adverse selection, or under 1 in either half, on at least 300 independent hourly events; NOT_ENOUGH_DATA under 300.

## R2. 15 minute book and tape for Bitcoin, Ethereum and gold, whole window

- Records: KXBTC15M, KXETH15M, KXGOLD15M, the single live market of each, order book depth 5 every 2 s for the whole 15 minutes (not only the last 150 s as today), plus the tape every 15 s.
- Size: 3 markets x 43,200 polls a day x about 300 bytes = about 40 MB a day raw, about 6 MB gzipped (gold only in its trading hours).
- Feeds: MAKER5 (MAKER4 with a real queue model; MAKER4's verdict was decided by a fill bound because no sizes exist mid-window) and an L1 execution study (how often the L1 entry would have filled one tick better resting at the touch). Counterparty: mid-window takers; adverse selection measured, not assumed. Kill: MAKER4's registered bar (PF 1.5, both halves above 1, stress 1.2) on at least 300 independent closes.

## R3. Economic release ladders, quotes before the release

- Records: the ladders of the next CPI, payrolls, jobless claims and Fed decision events (series found by `GET /series?category=Economics`), every strike, order book depth 3 every 60 s from 48 hours before the release to the release time, and every 10 s in the last hour.
- Size: about 40 strikes x 3,000 polls per event = about 120,000 rows, about 30 MB raw per event; roughly 8 events a month.
- Feeds: CPI2 (sell the over-wide tails before a release and buy back after, never held to settlement: who pays is the buyer of lottery-ticket tails; CPI1 could not run because hourly candles had no quotes) and a release-day ladder consistency check (ARB2 logic at 10 s resolution). Kill: CPI2 profit factor under 1.5 after two spreads and fees across at least 30 independent releases (about 4 months), or under 1 at stress.

## R4. Weather daily-high ladders, the morning quotes

- Records: the daily-high ladders of the 7 most liquid cities (KXHIGH... series), every bracket, depth 3 every 60 s from 06:00 to 18:00 local time.
- Size: 7 cities x 6 markets x 720 polls a day = about 30,000 rows, about 7 MB a day raw.
- Feeds: WX4, the intraday drift of the bracket that holds the morning forecast, sold before settlement (WX1 to WX3 tested holding to settlement and lost to a market that already knows the forecast; a pre-settlement test needs the intraday quotes that candles lack). Counterparty: morning sellers who reprice slowly as station readings arrive. Kill: PF under 1.5 after two spreads on at least 60 independent city-days, or below 1 in either half.

## R5. Sports in-play book (one sport, one season slice)

- Records: NBA game-winner markets in play, depth 5 every 2 s, tape every 10 s.
- Size: about 10 games a night x 2.5 h x 1,800 polls = 45,000 rows, about 12 MB a night raw.
- Feeds: SPORTS2, quoting between scoring runs with a queue model (MAKER1 lost on tennis with only the tape; the fill model decided it). Counterparty: in-play takers after momentum swings. Kill: MAKER4's bar on at least 300 independent games.

## Longer history without a recorder

Kalshi's public `GET /historical/markets/{ticker}/candlesticks` covers settled markets back to their listing at 1 minute (recent) and 1 hour (older) resolution; it carries the best bid and ask only where they existed at the candle's end. That already covers everything a candle-based test needs (THETA1 uses it now). It cannot provide depth, queue position or quotes in thin markets between trades, which is what R1 to R5 add.

## Order of value

1. R2 (decides MAKER4 properly, and the L1 execution question, on the markets the bot trades).
2. R1 (running).
3. R3 (the only way economic releases can be tested before settlement).
4. R4, then R5.
