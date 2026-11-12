# PERPSLIST1 registration: is the recorded perps LIST a delayed copy? (2026-11-12, committed BEFORE any perp candle file is opened)

Asked by the Head of R&D (task G2). Two kept reads depend on it: PERPEQ1 (perp candles) and CASHSPREAD1 part B (spreads from the 30 second list files); PERPBIN1 uses perp candles with freshness "assumed". A measurement: no rule scored, nothing settles, zero tries, zero Kalshi requests, no helper. Nothing about the live account.

**What has already been seen (stated so the order of events is clear).** For the family cost table this desk read the header and summarised the bid-ask spreads of one `perps30` file (2026-11-06, the close window) and three hourly files. The candle files under `kalshi1m/` have not been opened; their columns are known only from the recorder script on main (`ticker, end_period_ts, bid_open ... bid_close, ask_open ... ask_close, price_*`).

**Data, all on `perp-data`.** List rows: `perps/perps-<date>.csv` (one snapshot an hour) and `perps30/<date>/` (every 30 s in the open and close windows), column `ts_utc` to the second, written by the recorder just after the list answered, with `bid` and `ask`. Candles: `kalshi1m/<date>.csv.gz` for the Equities and Indices perps, held for 2026-11-06, 08, 09, 10, 11. Only those tickers and dates can be compared.

**The comparison.** For each list row (status active, bid > 0, ask > bid) at time t, and each of the two minute boundaries around it, e (a candle's `end_period_ts`): d = t minus e in seconds, from -60 to +60. L = the list mid, (bid + ask) / 2. C = that candle's mid close, (bid_close + ask_close) / 2. s = the ticker's median absolute change of the candle mid close from one minute to the next over the 20 candles centred on e (pairs with fewer than 10 such candles, or s = 0, are dropped). r = |L minus C| / s. If the list is current, r grows with |d| the same way on both sides of the boundary. If the list shows the market as it was a seconds ago, rows taken shortly AFTER a boundary match that boundary's close best, and rows taken shortly before it match it worse.

**Primary statistic, fixed now.** A = median r over rows with d in (0, +12] divided by median r over rows with d in [-12, 0). Interval: 2,000 resamples of whole timestamps (every ticker read at one t is one cluster).

**Reading rule, fixed now.**
- Fewer than 30 distinct timestamps on either side: **"no evidence at n = x"**, whatever A is, with a statement of what would be enough.
- Interval of A entirely below 0.8: "the perps list lags the candles by seconds" (a delayed copy, as the market list is).
- Interval of A inside 0.8 to 1.25: "no lag of several seconds: the list and the candles are in step".
- Anything else: reported as unclear, with the numbers.

**Secondary, descriptive.** (1) Median r by d in 10 second bins from -60 to +60, with the bin of the minimum. (2) For rows with |d| at most 5: the share where the candle's mid close lies inside the list's bid to ask widened by 2 basis points of price on each side, and the mean absolute difference in basis points. (3) The same primary statistic separately for the hourly files and the 30 second files, and for Equities and Indices.

**What this cannot say, known in advance.** It compares the list with the candles, not with an order book: if both were delayed by the same amount A would read 1. CANDLEVSBOOK1 cleared the candles of the 15 minute binary market only; the perp candles come from a different endpoint. So "in step" means "the list is as fresh as the perp candles", not "both are current". There is no perp order book or tape recorded to act as a third clock. `ts_utc` is whole seconds and is stamped after the answer arrives, so about a second of the list's apparent age is the recorder's own.
