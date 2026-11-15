# Desk A, structure and cross-market cards, Nov 15, 2026 (no data read, nothing built)

Order from the Head (Nov 15): non-perps, NEW mechanism only, not lead-lag, OI, favourite-late or a closed family. Register before reading. Each card needs the Verification Analyst's four uniqueness checks and Auditor B before any read. Held-outs: the last third by date, read once on the Head's go; nothing here touches an open card's held-out (to be checked against HELDOUT_REGISTRY.md when the data window is named).

## HOURBRIDGE1: the hourly ladder prices the 15 minute market that closes at the same time

Mechanism: the hourly Bitcoin and Ethereum "above K" ladders (KXBTCD, KXETHD) and the 15 minute market (KXBTC15M, KXETH15M) that closes on the same hour settle on the same reference over the last quarter hour. Inside that last quarter hour the ladder gives a full distribution of the hour-end price, so it implies a probability for the 15 minute market's own strike (taken from the market record, set at its open). Where the 15 minute quote and the ladder-implied probability differ by more than cost, buy the cheaper side of the 15 minute market, held to settlement (no favourite rule: the side is chosen by the gap, not by the price band). Counterparty guess (to be tested, not claimed): the 15 minute book is thinner and quoted by different participants than the ladder.
Not lead-lag (both legs are Kalshi quotes at the same instant; no outside lead), not OI, not favourite-late (the side follows the ladder gap, any price from 5c to 95c), not an ARB lock (no leg is hedged; it is a model gap).
Closest existing: CFRTI and CFRTIK (settlement-reference) and LADDER cards. Difference: those use an outside reference price; this uses only Kalshi's own ladder as the fair value.
Data needed: `ladder.csv` from the quote recorder (from Oct 28, last 150 s before each hourly close) and the 15 minute quotes in `quotes.csv` for the same window; the strike of the 15 minute market. Step 0: do the windows line up (same close, readable strike, ladder rows with mid 3c to 97c near the strike)?
Prediction (numeric, before any read): at least 150 windows with a gap of 4c or more after interpolation; net per contract after fee and a 2c haircut above 0.
Kill: under 100 usable windows by the end of development, or 2c PF under 1.0 on the development third.

## ADJWIN1: one 15 minute window's result, and the next window's starting price

Mechanism: the strike of each 15 minute market is set at the start of its window, so the window's first quotes (near 50c) should carry no information about direction. If participants anchor on the last window's result (momentum or reversal belief), the first quotes drift off 50c in a way that is not paid for by the next result. Rule: after a window that settled with a move of at least X sigma (X frozen before reading), buy the side the anchoring leaves cheap at the first look after open, held to settlement.
Not favourite-late (entry is at the open, price near 50c), not OI, not lead-lag. Closest existing: SEARCH1 and the CALIB cards (price level against frequency). Difference: the conditioning variable is the previous window's outcome, not the price.
Data needed: NC15 and R6 candles (open and early-window quotes), results. Step 0: does the first quote differ from 50c by more than 1c on average after a large previous move?
Prediction: the signed first-quote gap exists on at least 3 of 5 series, and the next-window win rate differs from the price by 3 points or more on the development half.
Kill: first-quote gap under 1c, or n under 150.

## NOT BUILT (stopped at step 0)

SEQ1, crossing sibling windows of different series that share a close time for dispersion: would be lead-lag by another name, rejected on sight under 7e rule 2.

Owner decisions needed: none. The Head decides which of the two go to Auditor B and the Verification Analyst first.
