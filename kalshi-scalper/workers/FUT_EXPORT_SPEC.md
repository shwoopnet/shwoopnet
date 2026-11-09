# What to export for the GC and NQ futures tests (owner-facing, Nov 9, 2026)

You send us a FILE only. Never an account password, API key, login or screenshot of a login. Put the file where the main session tells you (not in chat). Menu names below can differ by version: if a step is missing, tell us what you see and we adapt.

## What we need
- Symbols: GC and NQ (full size) AND MGC and MNQ (micro) if the platform has them. Full and micro track the same price, so full-size history is enough if micro is not available.
- Continuous contract, two versions if the platform allows it: (a) UNADJUSTED (raw front month, each contract as traded) and (b) BACK-ADJUSTED (difference or ratio adjusted). If only one version exists, send it and tell us which. Roll rule: volume-based or fixed roll about 8 days before expiry; tell us which the platform uses (we will use our own roll on the unadjusted file).
- Bar sizes: DAILY (as long as possible, 10 or more years) and 1-MINUTE (as long as the platform allows, ideally 5 or more years; 15-minute only if 1-minute is capped).
- Time zone: US Central (or say what it is). Session: full electronic session (all hours), not regular hours only.
- Columns: date, time, open, high, low, close, volume (settlement price for daily if offered). Header row first.
- Format: CSV (comma separated, one row per bar). If the platform caps rows, split by calendar year (one file per symbol per year, named like NQ_1min_2023.csv); 1-minute data is about 350,000 rows per year.

## Steps by platform
1. NinjaTrader 8 (free to download; sim account needs no money; Topstep and many futures brokers give it): Tools, Historical Data. Select the instrument (NQ 12-26 or the continuous contract "NQ ##-##"), choose "Download" for a data provider (e.g. the free Kinetick end-of-day or CQG/Rithmic trial through your broker), set Type to Minute, Value 1, date range, click Download. Then Tools, Historical Data, tab Export: pick the instrument, Minute 1, From/To, set Export as CSV, choose the folder, Export. Repeat for Daily.
2. TradingView (Premium plan allows "Export chart data"): open the chart for NQ1! (or GC1!) with the Settings, Symbol, "Adjust data for dividends" off and "Back adjusted" as you want; in the chart toolbar use "Export chart data" and choose CSV with ISO timestamps. Bars exported are capped by plan (1-minute depth is limited), so also export Daily (full depth) and take 1-minute in as many chunks as the plan allows (scroll the chart back first).
3. Sierra Chart: needs a data feed subscription; File, Data Files, or Edit, Intraday Data File, Export to text, then CSV. 
4. Broker or prop platform (e.g. Topstep): usually runs on NinjaTrader, TradingView or TopstepX, so use steps 1 or 2 inside it.
If you cannot export history at all, tell us; we then say which free/low-cost source to use.

## Questions for you (please answer in chat, short)
- Do you have the actual GC and NQ script rules you saw a strong profit factor on? Send exact entry, exit, stop, position size, session hours, and the profit factor with the date range and cost assumptions the platform used. Backtests on a platform are normally in-sample, with optimistic fills and little cost, so we will rerun your rule as written on dates it was not tuned on (the last third, read once).
- Which platform made the backtest, and does it include commissions and slippage?
