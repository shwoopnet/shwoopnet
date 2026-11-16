# Perps bot integration: one-page plan (Head of R&D, Nov 16, 2026)

RESEARCH ONLY. Nothing here is built or live. A perps strategy goes live only after it clears the bar (forward n 100+, PF 1.3+ at taker plus 0.02%, 1.0+ at taker plus 0.05%, both halves), the Risk Analyst's review, and the owner's own popup with an exact spec, through the Chief of Staff's merge and deploy. No account figure, key or live number belongs in this file.

## 1. Unknowns to settle first (from the owner's live UI screenshots, then Kalshi's docs)
- Fee schedule, taker and maker, per name or per class. Research uses 12 bps taker and 5 bps maker a side as placeholders.
- Max leverage per name. The docs we hold say up to 6x for BTC only; 15x and 40x are unconfirmed.
- Minimum order size, contract multiplier and tick size.
- Margin model (cross or isolated), the maintenance margin, the liquidation price formula and the liquidation fee.
- Funding: the docs say every 8 hours (12 AM, 8 AM, 4 PM ET), clamp of 2%, rates under 0.01% set to zero, positive means longs pay shorts. Our recorded history shows one print a day for stocks and indices: check against the UI.
- Whether perps use a separate margin balance (a shard, like the event markets), and how money moves into it. The bot must never move money; topping up is the owner's, by hand.
- Trading hours per class (stocks: regular session only, or 24/7 like crypto?), halts and their handling.

## 1b. Early finding from the owner's live UI (Nov 16; not final until the order ticket and asset details are in)
- The perps position appears to be funded from the SAME cash balance as the event market account, not a separate margin balance (the header's cash plus the position value equals the portfolio exactly).
- Size is entered as a position value in dollars; leverage is chosen per position (other traders show about 2x to 4x); the ticket offers market orders.
- One test fill implies about 12 bps a side taker cost plus spread, about 0.24% round trip, which matches the research placeholder.
- Consequences: (a) perps P&L and margin move the event bot's sizing base and its loss stops unless the code separates them, so the Risk Analyst must decide whether the stops count perps; (b) the event bot's Flatten and exit watch iterate their own order documents and do not touch perps, so an open perp has no exit watch today; (c) any perps strategy needs its own sleeve limit as a share of the shared balance, so it can never starve the event strategies of cash.

## 1c. Facts from Kalshi's help pages and the owner's live list (Nov 16, about 12:40 PM CT), VERIFIED or OPEN
- CORRECTION to 1b: the margin account is SEPARATE from the predictions balance and customer-segregated; a liquidation never touches the predictions balance. A perps order can pull available cash from predictions automatically, which is why the header cash fell by the position value. VERIFIED (help pages). Still OPEN: whether the event bot's balance read and sizing base see that pull.
- Max leverage: the lightning number on each market page (owner). Examples: most large stocks 4.9x, NVDA 4.5x, MU 3.3x, SNDK 1.5x; US Tech 100 28.9x, US Large Cap 36.1x, US Small Cap 24.6x, SPY and QQQ 4.9x; BTC 15.4x, ETH 10.5x; gold 40x, silver and copper 17.7x. The API's leverage_estimate is lower (gold 15.3x, indices 10x to 12x) and size-dependent: use the page maximum as the ceiling and the API estimate as the size-aware figure. VERIFIED (owner UI).
- Fees: charged on notional on open and close, maker below taker; the rate in bps is not on the pages read. One live fill matches 12 bps a side taker. OPEN until get-fee-tier-rates is read.
- Funding: stock perps pay once a day at 4:00 PM ET; the 8-hour schedule is for other perps; rates under 0.01% are set to zero; clamp of 2%; positive means longs pay shorts. VERIFIED (help pages and our data).
- Hours: not 24/7; scheduled closures, holidays, pauses around corporate actions, daily settlements at 12:00 PM and 4:00 PM ET, Thursday maintenance about 3 to 5 AM ET. VERIFIED (help pages).
- Contract: 0.02 share (50 contracts = 1 share), minimum 1 contract. VERIFIED (help pages).
- Dividends pass through as cash (long receives, short pays); splits adjusted. VERIFIED (help pages).
- Interest is paid on eligible perps balances. VERIFIED (help pages); not used in research P&L.
- Liquidity: SPY and QQQ perps are thin; the liquid index perps are US Tech 100 and US Large Cap. VERIFIED (owner list).

## 2. API work (Main builds, after a passing strategy and the owner's popup)
- Read: the perps market list, book top, candles and funding history (public), plus our own positions, orders and margin (signed, the existing key only if Kalshi uses the same key, entered only through the secure credential form).
- Write: place a limit or immediate-or-cancel order, cancel, reduce-only close. No market order without a price cap.
- A new collection for perps orders, kept apart from the event market orders, with the same logging pattern (client order id fixed per signal, no retry of a lost answer).

## 3. Safety caps the Risk Analyst would need (proposed, all in code, none settable from the page)
- Leverage cap per position, set below the exchange maximum (proposed 2x until the strategy has a forward record at that size).
- Notional cap per position and per account, as a fraction of the perps margin balance.
- A stop at a fixed distance well inside the liquidation price, so a stop always fires before a liquidation could; reduce-only.
- A daily loss stop and a drawdown stop for the perps sleeve, separate from the event market stops, plus the account backstop.
- Funding guard: no new position whose expected funding cost over the hold exceeds a set share of the expected edge; book funding as cash.
- Halt and gap guard: no entry within N minutes of the open, the close or a halt; flatten before a known close if the strategy is intraday.
- Kill latch per strategy (losing streak, net under a line after N fills), re-armed only by a reviewed edit.
- A heartbeat and an alarm when an open perps position has no live exit watch, as for the event markets.

## 4. Order of work
1. Settle section 1 from the owner's screenshots and the docs.
2. Research: the pooled stock perps pass (ENGPERPS_POOL1), its forward shadow, the forward perps cards.
3. Only for a strategy that reaches CANDIDATE: the Risk Analyst writes the caps, Main builds the read and write path behind a code switch that is off, a dry run that logs would-be orders, then the owner's popup.
