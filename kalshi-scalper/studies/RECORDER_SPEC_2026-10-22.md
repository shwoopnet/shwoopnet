# Recorder spec: do Kalshi 15-minute crypto quotes lag the spot index in the last two minutes?

Status: PROPOSAL from the strategy-research session (2026-10-22). Not built. Places no orders. Needs no keys and no secrets. The main session and the owner decide whether to run it.

## Why
Every test so far saw the book at one-minute resolution. At that resolution the market already prices what spot shows (README: H7, L2, L3, BOUND, LEADLAG all FALSIFIED). The 15-minute crypto markets settle on a 60-second average of a spot index (CF Benchmarks), so in the final minute or two the outcome is largely determined by prices that are already printed. If Kalshi's quotes react slower than spot by even a few seconds, a taker order placed in those seconds may be paid for the lag. This cannot be tested with one-minute candles. It is the only structural idea left that could give an edge larger than a few cents.

## What to record (public data only)
1. **Kalshi quotes**, for the open BTC, ETH, SOL, XRP and DOGE 15-minute markets (the series that exist and are liquid): from 150 seconds before each close until the close, poll the public order book (REST `GET /markets/{ticker}/orderbook`, or the market's best bid and ask) at up to 2 Hz per market, with back-off on HTTP 429. Row: `t_utc_ms`, `ticker`, `yes_bid`, `yes_ask`, `bid_size`, `ask_size` (top of book, plus the next two levels if cheap), and the market's strike.
2. **Spot**, same assets, same window, plus 10 minutes before it: the public websocket trade or ticker feed of Coinbase, Kraken and Bitstamp (the main exchanges in the index), one row per update with `t_utc_ms`, `exchange`, `price`. Keep the exchange's own timestamp and the local receive time.
3. **The settlement result** per market afterwards (already available from the public API), so nothing needs to be joined by hand.
4. Clock: record NTP offset once an hour. Sub-second analysis needs the recorder's clock within about 50 ms.

Volume: about 5 markets x 150 s x 2 Hz x 96 windows = under 150,000 quote rows a day, plus spot ticks. Small. SQLite or CSV files are enough.

## How long
At least 14 days (about 1,300 windows per asset). Fewer than 10 days returns NOT_ENOUGH_DATA by rule.

## What I will do with it (pre-registered when the data exists, not before)
RECORD1: at fixed seconds before the close (for example 60, 45, 30, 15), build the expected settlement probability from the spot data already printed (the known part of the 60-second average plus a simulated remainder) and compare it to the market's ask or bid. Rule: buy the side whose expected value beats the price by at least 3c after the fee. Claim: mean net per contract at least +2c, z at least 3.0, at least 300 trades over at least 10 days, positive in both halves, positive at x1.2 fee. Plus a latency read: how many seconds after a spot move of a given size do the quotes move.

A pass is a lead, not a switch. Fillability is a separate test: the depth at the ask against the order size, and the bot's own order latency (its `seenAt` against the exchange time is already logged).

## Kill criteria (written now)
- If quotes are within about 1c of the spot-implied probability in every second sampled, FALSIFIED: no lag to trade.
- If the lag exists only in seconds when depth at the ask is below 5 contracts, NOT a tradable edge at this account size.

## Where it must run
A long-lived process. The research workers are restarted every 30 to 40 minutes, so it cannot run there. It needs the main session's server (or any always-on host). It is read-only: no Kalshi key, no Alpaca key, no order endpoint.

## Cost / risk
No trading risk. Server time and a few megabytes a day. The one operational risk is Kalshi's public read rate limit: use at most 2 requests a second per market, back off on 429, and never run it in parallel with the order flow's own reads on a shared key if one is ever used (it uses none).
