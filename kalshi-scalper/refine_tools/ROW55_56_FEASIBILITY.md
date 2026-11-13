HISTORY (Nov 13, 2026, owner ruling): this note predates the privacy scrub; lines marked "[live figure removed, ask Main]" are blank on purpose. Read it as history, not as a current rule.

# Feasibility, rows 55 and 56 (Nov 10, 2026). No strategy scored. About 25 public GETs, 2 to 4 s apart, no 429.
Repeat check: REFINE_RETRACTIONS.md has nothing on liquidations or sports lines; REFINE_STATUS.md mentions only flow/OI work, no OKX liquidation or sportsbook line test.

## Row 55 (OKX liquidation cascade, Bitcoin 15 minute): FORWARD_LOG
- [live figure removed, ask Main]
- Retention is short: 100 rows per call, newest 2.3 h; paging with after=<ts> reached back only about 17 h (after=now-17h empty). Not 60 days. No cascade count possible from history.
- Binance allForceOrders: HTTP 451 (restricted location) and the endpoint is gone for history anyway. Bybit: 403 geo block. Both unusable from here.
- Forward log spec: poll OKX every 5 min (page back with after= until ts older than last seen, dedupe by ts+bkPx+sz); also uly=ETH-USDT optional. Fields per liquidation: ts_ms, side, posSide, sz (contracts; USDT notional = sz x ctVal 0.01 BTC x bkPx, confirm ctVal from /public/instruments), bkPx. Also log per Kalshi KXBTC15M window: close time, ask/bid at the 6 min look, result. Sample size: cascades at the 98th percentile of a trailing week cluster; need about 8 weeks to get ~100 events. About 288 GETs/day, no key, well under 15 a minute.

## Row 56 (sports winner vs de-vigged non-Kalshi line): FORWARD_LOG (history DROP)
- [live figure removed, ask Main] Each game is two markets.
- ESPN site.api.espn.com scoreboard (keyless, undocumented): live/upcoming game shows DraftKings moneyline open and close (e.g. NY -1040 / MIL +670) plus spread and total. A past date (dates=20251115) returned odds None: ESPN keeps no closing line archive, so no backtest.
- Terms: unofficial endpoint, no published license; DraftKings lines are ESPN-displayed and linked to bet slips. Use for personal research only, low rate; fragile (schema can change).
- Forward log spec: every 10 min on game days, GET scoreboard for nba, nfl, nhl, (ncaam optional); for each event not started store ts, event id, start time, home/away, DK moneyline close/open, spread, total; same moment pull Kalshi yes bid/ask for both winner markets; after the game store Kalshi result. Fields: both vig-free probabilities computed offline. Need about 150 games per league for any read (NBA about 2 months). One DK line only, so "consensus" is a single book.
