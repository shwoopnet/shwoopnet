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
