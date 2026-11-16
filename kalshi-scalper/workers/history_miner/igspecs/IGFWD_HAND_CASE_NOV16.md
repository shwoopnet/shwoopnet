# Forward in-game loader, scorer plugin and listing job: hand case (History Miner, Nov 16, 2026, before code)

## ingame_fwd_load.py (the forward version of ingame_load.py 6ac835f4, same walls, forward window)
- Window: poll time and market close in [2026-11-17T00:00Z = 1794873600, 2026-12-15T00:00Z = 1797292800). Date directories 2026-11-17 to 2026-12-14 only.
- Ticker wall: KXNHLGAME, KXNBATOTAL, KXNFLTOTAL, KXNHLTOTAL, KXNBASPREAD, KXNHLSPREAD (no KXNBAGAME or KXNFLGAME: SPORTS-PRE).
- Order: t_recv_ms first; close_time first in a listing market, then the wall, then result and occurrence_datetime for kept markets only.
- Allow line: the mark "readable ONLY by the History Miner's forward ingame loader", "ingame_fwd_load.py", its own sha256, AND the sha256 of EVERY listing gz file it is given (the listings grow, so each auto-run's files must be named; a file not named refuses the run).
- Events: one per (league, game suffix, kind): {"key", "league", "kind", "rows": {ticker: [(t, bid, ask)]}, "result": {ticker}, "close": {ticker}, "occ": {ticker: occurrence string}}. Polls after their market's close are dropped and counted.

## ingame_events.py (the scorer plugin; contracts 10, haircuts 1c and 2c, hold to settlement)
- fee per order: ceil(round(100 x 0.07 x 10 x p (1 - p), 9)) / 100. cash = 10 x (1 - paid) - fee on a win, -10 x paid - fee on a loss, -fee on a void; paid = min(ask + h, 0.99).
- Schedule test (tip): the event's occurrence values must be one value, minute in {00, 30, 05} (NFL also 15, 20, 25), 0 seconds; tip = that time minus 3 h. Fail: "schedule test failed".
- IGFADE2: per ticker, consecutive two-sided rows <= 60 s apart with |mid change| >= 0.10; buy the fallen side (YES ask if mid fell, else 1 - yes_bid) if 0.15 to 0.60; the earliest such pair over the event's tickers.
  Case: rows (t 0: 0.40/0.42), (t 30: 0.52/0.54): NO at 0.48; result no, h 2c: paid 0.50, fee ceil(17.5) = 0.18, cash 10 x 0.50 - 0.18 = +4.82. Gap 70 s: no trade.
- IGLATEDRIFT1 (no spreads): quote = the last two-sided row in (mark - 300 s, mark]; marks tip + 5400 and tip + 7200; d = mid(7200) - mid(5400); |d| >= 0.08; buy the side it moved toward at its ask if 0.20 to 0.80; for the NHL moneyline only the first team ticker in string order.
  Case: tip T; rows (T+5300: 0.40/0.42), (T+7100: 0.50/0.52): d +0.10, YES at 0.52; result yes, h 2c: paid 0.54, fee ceil(17.388) = 0.18, cash 10 x 0.46 - 0.18 = +4.42. A row at T+4900 only for the first mark (500 s before): no trade.
- IGDOG1 (KXNHLGAME only): at tip + 4500 s, the last two-sided row within 300 s for each team ticker; exactly one with yes ask 0.15 to 0.35: buy its YES. Both or neither: no trade.
  Case: team A ask 0.30, team B ask 0.72: buy A YES at 0.30; result yes, h 2c: paid 0.32, fee ceil(15.232) = 0.16, cash 10 x 0.68 - 0.16 = +6.64.
- Summary per spec and haircut: n, pf, half1 and half2 (by entry time), net, day z, evidence ("no evidence at n = x" under 100), kill_fast flag (2c PF under 1.0).

## IG_FWD_RESULTS (kalshi-pull job, for Main)
GET /markets, settled, series the six above, min_close_ts 1794873600, max_close_ts 1797292799, limit 1000, max_pages 10 each, cap 80 requests.

## Amendment 1 (2026-11-16 ~16:45Z, Auditor B 16:20Z, before any forward row): KXNFLSPREAD removed from the loader wall, the listing job and IGFADE2 (BOOKS2 W3 holds it until the Head closes BOOKS2). Nothing else changed.

## Amendment 2 (2026-11-16 ~17:10Z, Auditor B 15:54Z notes 1, 2 and 4, before any forward row)
- Note 1 (C8): the plugin counts entries within 120 s of the close and prints their 2c profit factor (entries_within_120s_of_close).
- Note 2: IGFADE2 prints the count of consecutive polls of one ticker no more than 60 s apart, per UTC day; none at all prints 'no signal: cadence'.
- Note 4: the allow line is bound to the loader's sha256 and the committed job's sha256 (IG_FWD_RESULTS.json), not to every listing file. A listing RUN is accepted only if its STATUS is complete, its manifest's embedded job equals the committed job, every row is 200 and not truncated, every body's sha256 and byte count equal its manifest row, pages are 1..k per request with no cursor on the last, and the folder's files equal the manifest's files plus STATUS and manifest.json. The loader takes a folder of run folders.
