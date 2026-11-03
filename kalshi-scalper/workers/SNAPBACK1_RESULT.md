# SNAPBACK1 result (development read, run once 2026-11-03; rule, grid, bars and split exactly as registered in `SNAPBACK1_REGISTRATION.md`, sha256 0741ddc7...b09330; nothing changed after seeing results)

Code `src/scalper/snapback1.py`, tests `tests/test_snapback1.py` (committed before the run), output `workers/SNAPBACK1_output.txt`. Data: Kalshi public `margin` candlesticks, 1 minute, with open interest, KXBTCPERP and KXETHPERP, 2026-06-03 to 2026-11-03. Development = first two thirds (102.1 days), halves at 51 days; **the last third was never read** (no trigger, count or return computed after the cut), because no cell survived.

**Data reach.** Hourly and 1 minute candles with price OHLC, bid/ask OHLC, volume and open interest; about 153 days of history for BTC, ETH, SOL, XRP (gold from 2026-09-10); a public trade tape; the market list. No funding rate or payment field anywhere (funding assumed: 1 bp against the position per 00/08/16 UTC time crossed). Only BTC and ETH were fetched and tested.

| cell (k, x, T) | n (BTC/ETH) | per month | win | payoff | PF | expectancy bp (net) | worst loss | longest loss run | half 1 / half 2 expectancy | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 2, 2%, 2 | 125 (61/64) | 37.2 | 21.6% | 1.65 | 0.46 | -22.9 | -101 bp | 16 | -22.1 / -23.7 | FALSIFIED |
| 2, 2%, 3 | 125 | 37.2 | 20.0% | 1.85 | 0.46 | -23.1 | -101 bp | 17 | -25.9 / -20.4 | FALSIFIED |
| 2, 5%, 2 | 103 (45/58) | 30.7 | 24.3% | 1.62 | 0.52 | -19.9 | -101 bp | 9 | -18.6 / -21.3 | FALSIFIED |
| 2, 5%, 3 | 103 | 30.7 | 23.3% | 1.95 | 0.59 | -17.1 | -101 bp | 9 | -18.8 / -15.4 | FALSIFIED |
| 3, 2%, 2 | 51 (24/27) | 15.2 | 17.6% | 1.80 | 0.39 | -27.6 | -77 bp | 12 | -31.7 / -23.3 | FALSIFIED |
| 3, 2%, 3 | 51 | 15.2 | 17.6% | 2.06 | 0.44 | -25.1 | -77 bp | 12 | -36.6 / -13.2 | FALSIFIED |
| 3, 5%, 2 | 46 (21/25) | 13.7 | 19.6% | 1.80 | 0.44 | -25.0 | -75 bp | 10 | -24.8 / -25.1 | FALSIFIED |
| 3, 5%, 3 | 46 | 13.7 | 19.6% | 1.95 | 0.47 | -23.4 | -75 bp | 10 | -30.8 / -15.3 | FALSIFIED |

Worst loss: always the 0.5 ATR stop (-0.5 ATR) plus fees, at most about -101 bp, i.e. about $1.01 per $100 notional (no gap model: a real gap through the stop would be worse; stated optimism). Pooled z of the expectancy is -1.4 to -3.9 (negative, significant in the loosest cell).

**Reading.** More events than the owner's agent predicted (46 to 125 per cell in 102 days, 14 to 37 a month, so NOT_ENOUGH_DATA did not apply to any cell), but the win rate is 18 to 24% (predicted 30%) and the payoff 1.6 to 2.1 (predicted 5x). Information only (not a try, seen after the verdict): the GROSS mean before fees and funding is about zero (-3.5 to +7.1 bp per trade); ATR(1h) is only about 61 bp, so the 0.5 ATR stop is about 30 bp, barely above the 24 bp round-trip fee, and 75 to 80% of trades end at the stop. The fee, not the signal, decides: there is no measurable snapback edge to pay for, so a lower fee would not rescue this in the form tested. The signal's gross mean is within noise of 0 in all eight cells, so a maker fee or a wider stop is a different idea needing a new registration, not a variant of this one.

**Verdict: SNAPBACK1 FALSIFIED in all 8 cells (development only; frozen third unread, correctly).** Prediction check: the survival odds (5 to 10%) were generous; the expected NOT_ENOUGH_DATA was wrong (events were plentiful). Months to 40 forward events: 1.1 months in the loosest cells (37 a month), 2.9 months in the tightest (13.7 a month), moot after the verdict. **Decision value:** do not apply for perps access on the strength of this idea. **Nothing trades from this**; the owner's Kalshi account is personal and perps access needs an application. N added: +8 (running about 730,003). Streaks via `scalper.streaks.empirical_streaks` are in `workers/SNAPBACK1_output.txt`.
