# IGFADE1 and IGUNDER1 hand case (History Miner, Nov 15, 2026, before code; invented rows)

Readings fixed here (the card's words made exact):
- A row counts only if t_recv < 1794528000000 and yes_bid, yes_ask parse as numbers. mid = (bid + ask) / 2. Two-sided 0 < bid < ask < 1.
- Game = event suffix after the first "-"; league = NBA, NHL or NFL from the event's series prefix. Kind = the recorder's kind column (ml, total).
- IGFADE1: for each moneyline ticker, consecutive rows of that ticker (by t_recv) with gap <= 45 s, both two-sided, |mid2 - mid1| >= 0.10. Entry side = the side that fell; its ask (YES ask, or 1 - yes_bid for NO) must be 0.15 to 0.60. The game's entry is the EARLIEST such qualifying pair (by the second row's time) over its moneyline tickers. A jump whose ask is out of range does not block a later one.
- IGUNDER1: live time = the earliest second row of a pair of consecutive rows of one moneyline ticker of the game with gap <= 45 s. Entry = the earliest row (t >= live time) of any totals ticker of the game that is two-sided; buy NO at 1 - yes_bid; traded only if that is 0.35 to 0.65 (else no trade for the game).
- Market used must be in the results listing with close in [1794096000, 1794528000); third 1 if close < 1794355200 else third 2. Result yes, no or void.

Cases:
F1 ml ticker rows: t 0 (0.40, 0.42), t 30 (0.52, 0.54): jump +0.12, YES rose, buy NO at 1 - 0.52 = 0.48. Result no: h 2c, c 1: entry 0.50, fee ceil(1.75) = 0.02, net 1 - 0.50 - 0.02 = +0.48.
F2 same but t 50: gap 50 s, no entry.
F3 rows (0.80, 0.82) then (0.68, 0.70) 20 s later: YES fell 0.12, buy YES at 0.70: out of range, no trade; a later pair (0.50, 0.52) to (0.38, 0.40) buys YES at 0.40 in range: that is the entry.
U1 ml rows t 0, t 100 (gap 100), t 120 (gap 20): live at 120. Totals rows: t 110 (0.40, 0.44) before live, ignored; t 140 (0.45, 0.47): NO at 0.55, in range. Result no, h 2c: entry 0.57, fee ceil(1.7157) = 0.02, net +0.41. Result yes: -0.59.
U2 first totals row after live is (0.20, 0.22): NO at 0.80, out of range: no trade for the game.
U3 a market not in the listing, or closing on or after the cut: dropped.
Bar: n >= 100, PF2c >= 1.3, third 1 and third 2 PF2c >= 1.0 each.
