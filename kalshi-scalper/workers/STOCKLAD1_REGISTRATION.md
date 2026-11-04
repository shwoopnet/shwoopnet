# STOCKLAD1: single-stock close ladders and ranges, cheap side vs realised vol with student-t tails (2026-11-04)

Registered before any outcome, price or candle was fetched. The only data read was the public series list (titles, tickers, categories, frequency), which is a census of what exists.

**Duplicate check.** README and workers grepped (INX1, IDXFUT1, VRP2, VT1, PUB20, STOCK, equity, NVDA, TSLA, ladder, USWEEP1/2/3, NEWLIST1, CALIB1, OICORE_SHAPE_INVENTORY, EARN1, STRADDLE1). Index ladders (S&P, Nasdaq-100, Russell, Nikkei and others) were INX1/IDXFUT1 and the US sweeps; company KPI markets are EARN1 (NOT_RUNNABLE); earnings-call words are MENT1. No earlier worker priced single-stock close ladders against realised vol, so this is not a duplicate in design.

**Rule as it would run.** Series: Kalshi daily/weekly/monthly "company stock close above K" and range series for single names (Tesla, Nvidia, Apple, Microsoft, Amazon, Coinbase, Palantir, GameStop and similar). Reference: the stock's last price at the look (Yahoo chart, keyless) and daily realised vol of the prior 20 trading days scaled by sqrt(days to close). Tails: student t, df registered at 5 and re-fitted by moment on the first two thirds of events only. Look: the close before the event date (one look). Probability of each strike above/below from the t model. Trade: CHEAP SIDE ONLY (ask 3c to 30c) when model probability is at least 3x the ask, held to settlement, max 2 per event, hard limit 0.30. Control: all cheap strikes in the same events. Cluster: event. Frozen last third from 2026-10-03T16:00Z never fetched or joined. No favourite-side result is computed or printed. No 15-minute crypto or gold triggers.

**Numeric prediction (if it could run).** Mean net per contract after fees about -1c to 0c, PF 0.8 to 1.0; FALSIFIED about 85%.

**Kill rules.** FALSIFIED if mean net after fees is not above 0 in both halves or PF is under 1.5. NOT_ENOUGH_DATA under 150 trades with months to go. NOT_RUNNABLE if the census before the cut finds under 25 settled events or about 150 expected treated trades.

**Census (listings only, run 2026-11-04 on the public series list, 15,687 series).** Series whose title or ticker names a single listed company, across Financials, Companies, Crypto, Economics and Science and Technology: every one is a non-price market (CEO changes, product launches, deliveries, "KPI" annual metrics, subscribers, credit-card spend, lawsuits, market share, IPO super-voting). The only price ladders and ranges in Financials are indices (S&P 500, Nasdaq-100, Russell 2000, Nikkei, Hang Seng, Nifty, FTSE, EURO STOXX, KOSPI, Shanghai, Ibovespa), rates, FX, commodities and crypto. Single-stock close ladders or range series found: **0**. Settled events before the cut: **0** (bar 25); expected treated trades **0** (bar 150).

**N: +2** (one rule registered, never scored).
