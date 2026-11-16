# PERPMON1: fade the stock perp's weekend move on Monday (History Miner, registered Nov 16, 2026 ~16:05Z, FORWARD card; no candle read)

The Head (Nov 16 15:28Z): YES as a forward card, read once at 8 Mondays (about 2027-01-04), counted in the perps Bonferroni-Holm family. No price of the data set has been read by me before this registration.

Data: perp-data branch, kalshi1m/ (1 minute candles of Kalshi's public perpetual candlestick endpoint, record_perps_candles.py).
Universe: every ticker the public perps list marks Equities (single stocks), EXCLUDING the six perps already read: SPY, QQQ, NVDA, AAPL, US500, US Tech 100 (and any index perp). Fixed at the read from the recorder's ticker list; a ticker must have candles on both the Friday and the Monday.
Mondays: the 8 US trading Mondays 2026-11-09, 11-16, 11-23, 11-30, 12-07, 12-14, 12-21, 12-28 (a Monday that is a US market holiday is skipped, not replaced). Friday = the trading day before.

Rule (one try):
- F = mid of the last candle ending at or before Friday 21:00 UTC (16:00 New York in winter). M = mid of the candle ending at Monday 15:30 UTC (first hour of the cash session; if missing, the last candle in 15:25 to 15:30). mid = (bid + ask) / 2 of the candle's close quote; a candle without both sides is missing.
- Weekend move r = M / F - 1. If |r| >= 1.0 percent: fade it at 15:30 UTC Monday (sell if r > 0 at the bid, buy if r < 0 at the ask), exit at the candle ending Monday 20:59 UTC at the opposite touch. One trade per ticker per Monday. Position 1 unit of notional; return in percent.
- Costs: the touch on both legs (already in the bid and ask) plus a fee of 0.05 percent a side (0.10 percent round trip) unless Main supplies the published Kalshi perps taker fee before the read, in which case that fee is used and stated.
- Counterparty and prediction: the few takers active while the perp reopens overpay for weekend news; the move partly reverses during Monday's cash session. Prediction: profit factor after cost >= 1.3, and positive on at least 5 of the 8 Mondays.
- Bar at the read (one read only): n >= 100 trades, PF after cost >= 1.3, PF of the first 4 Mondays and of the last 4 Mondays each >= 1.0, day-clustered z (per-Monday mean over its standard error, 8 dates) >= 2.0, and a Bonferroni-Holm pass inside the perps family as the Head keeps it. Under 100 trades: "no evidence at n = x". Kill: PF after cost under 1.0.
- Nothing is read before 2027-01-04 except the ticker list (no price). No interim look.

## Amendment 1 (2026-11-16 ~16:15Z, the Head 15:29Z, before any read)
Costs now match the perps grid, replacing the 0.10 percent round trip: taker 12 bps a side and maker 5 bps a side, both printed and both ASSUMED until Kalshi's fee page is read; plus a per-fill haircut ladder of 0.02 percent and 0.05 percent on each leg. Every figure is printed at the four combinations (taker or maker, 0.02 or 0.05 percent). The bar is judged at taker with the 0.05 percent haircut; a rule that clears only at maker is flagged, not passed. Everything else stands.

## Amendment 2 (2026-11-16 ~16:20Z, the Head 15:30Z, before any read)
The bar replaces Amendment 1's single judging point (the 1c and 2c analogue): PF after cost >= 1.3 at taker with the 0.02 percent haircut, with the first 4 and the last 4 Mondays each >= 1.0 at that cost, AND PF >= 1.0 at taker with the 0.05 percent haircut. n >= 100, day-clustered z >= 2.0 (at taker 0.02 percent) and the perps Bonferroni-Holm pass still apply. A pass only at maker is flagged, not counted.
