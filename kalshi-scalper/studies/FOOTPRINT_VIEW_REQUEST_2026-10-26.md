# Request: a read-only footprint view on the Kalshi page (2026-10-26, owner chose "2")

Confirm with the owner in the build session before building. Read-only, no orders, no settings, no new Firestore writes.

**What.** For one market at a time (the bot's live series: gold, XRP, Dogecoin, natural gas, Bitcoin, Ethereum), a chart with one column per minute and one row per YES price in cents. Each cell shows two numbers: taker sells (left) and taker buys (right). Under it, one delta bar per minute (buys minus sells) and a running total. Mark the bot's entry (6 or 10 minutes before the close) and exit with a vertical line. Last 20 to 40 minutes of the selected market.

**Data.** Kalshi's public trade tape, no key: `GET /markets/trades?ticker=...&min_ts=...&max_ts=...&limit=1000` (follow `cursor`). Fields used: `created_time`, `yes_price_dollars`, `count_fp`, `taker_outcome_side`. A taker buying YES (`yes`) lifts the ask: a buy. A taker buying NO (`no`) hits the bid: a sell. Reference code and a test: `kalshi-scalper/src/scalper/footprint.py`, `kalshi-scalper/tests/test_footprint.py` (bar and level aggregation, delta, point of control, stacked-imbalance count).

**Reference rendering.** Two private pages, one with the busiest 40 minutes of a Challenger tennis match and one with the gold 7:30 PM ET window that held the owner's $9.58 loss on 2026-10-25 (data and drawing code were in the research session's scratchpad; the layout is: canvas grid, shaded cells at 3 to 1 imbalance and at least 50 contracts, outlined point of control, hover readout).

**Constraints from CLAUDE.md.** The blank-slate gates fix the hosts the page may call; the trade tape is on the same Kalshi API host the Kalshi page already reads, but check test/blankSlateGates.test.js and add the endpoint on purpose if it is missing. No new setting, toggle or order path.

**What it is not.** A reading tool. The research tests of trade-tape rules (TAPE20, 16 rules, 2,322 entries) found none that predicts the 15 minute outcomes; a footprint adds price-level detail and its tennis test is registered separately. Nothing here changes live trading.
