# DAILY2 result: WTI, EUR/USD and USD/JPY daily markets against a fair value from the outside price

Worker DAILY2, Strategy Research V2, 2026-10-29. Registration `workers/DAILY2_REGISTRATION.md` (with amendment 1, 5 minute Yahoo bars, made before any Kalshi candle or outcome was fetched); census and ledger check `workers/DAILY2_CHECK.md`; code `src/scalper/daily2.py`. Data and raw printouts are in the session scratchpad, not in git.

## Part 1: windows A and B (written and pushed before window C was computed)

- **Data:** 41 trading days from 2026-08-31 to 2026-10-28, 2,530 settled markets and 78,482 one minute candles.
  - A: Aug 31 to Sep 17, 13 days. B: Sep 18 to Oct 7, 14 days. C: Oct 8 to Oct 28, 14 days.
  - WTI loses 4 days (Sep 17 to 22), where Kalshi had rolled to the November contract while `CL=F` was still October, as registered.
- **Universe strikes** (mid 0.05 to 0.95 at close - 75 min), over 41 days: WTI 169, EUR/USD 158, USD/JPY 187.
- **N tried = 8.** Running count about 438,918.

Per variant at C = 1 contract, fill at the candle after the signal; PF10 is the same at 10 contracts; zv is the number of fills on a zero-volume candle.

| Variant | A: orders / days / PF1 / PF10 / zv | B: orders / days / PF1 / PF10 / zv | A+B: orders / days / PF1 / mean / day-clustered z | PF x1.2 (A, B) | Verdict (registered rule) |
|---|---|---|---|---|---|
| WTI 60 min | 9 / 5 / 0.00 / 0.00 / 1 | 15 / 8 / 0.18 / 0.18 / 0 | 24 / 13 / **0.11** / -21.4c / -4.75 | 0.00, 0.17 | `NOT_ENOUGH_DATA` (13 days < 15; lost on 23 of 24 orders) |
| WTI 30 min | 9 / 5 / 0.61 / 0.62 / 1 | 13 / 8 / 1.17 / 1.20 / 2 | 22 / 13 / 0.90 / -2.0c / -0.19 | 0.60, 1.16 | `NOT_ENOUGH_DATA` (13 days) |
| WTI 10 min | 13 / 8 / 0.18 / 0.18 / 0 | 13 / 10 / 1.13 / 1.17 / 1 | 26 / 18 / **0.54** / -7.8c / -1.01 | 0.17, 1.12 | **`FALSIFIED`** |
| EUR/USD 60 min | 13 / 8 / 5.09 / 5.22 / 11 | 17 / 11 / 0.29 / 0.29 / 15 | 30 / 19 / **0.74** / -6.2c / -0.60 | 5.01, 0.28 | **`FALSIFIED`** |
| EUR/USD 30 min | 17 / 10 / 2.09 / 2.15 / 17 | 21 / 13 / 0.32 / 0.33 / 18 | 38 / 23 / **0.64** / -8.5c / -0.92 | 2.08, 0.31 | **`FALSIFIED`** |
| EUR/USD 10 min | 7 / 5 / 4.92 / 5.08 / 5 | 10 / 8 / 0.65 / 0.66 / 8 | 17 / 13 / 1.18 / +3.1c / +0.23 | 4.71, 0.64 | `NOT_ENOUGH_DATA` (13 days) |
| USD/JPY 60 min | 6 / 5 / 3.50 / 3.79 / 6 | 10 / 7 / 1.87 / 1.90 / 10 | 16 / 12 / 2.10 / +9.8c / +1.39 | 3.45, 1.82 | `NOT_ENOUGH_DATA` (12 days) |
| USD/JPY 30 min | 4 / 3 / inf / inf / 3 | 11 / 7 / 0.27 / 0.27 / 11 | 15 / 10 / 0.65 / -10.9c / -0.63 | inf, 0.26 | `NOT_ENOUGH_DATA` (10 days) |

**The information fill (at the signal candle itself) does not change the picture.** A+B PF there, for the 60, 30 and 10 minute looks: WTI 0.12 / 0.99 / 0.62, EUR/USD 0.86 / 0.59 / 0.92, USD/JPY 1.92 / 0.90 (60 and 30 only).

**Notes on A and B.**

- **No variant can pass, by design.** No window holds even 15 closes, against the bar's 30.
- **WTI: the model is wider than the market, not narrower as predicted.**
  - The reference level matches Kalshi's centre; a check of `S` against the strikes priced near 50c showed no basis error.
  - The model's trailing 10 hour volatility gives a wider distribution 30 to 60 minutes before the 2:30 PM settlement than Kalshi prices. So it buys cheap tails: 63 of 72 WTI orders were priced under 0.5, and 55 of those 63 lost.
  - Kalshi's tight pricing was right. WTI at 60 minutes lost on 23 of 24 orders, but it traded on only 13 days, so the registered day minimum makes it `NOT_ENOUGH_DATA`, not `FALSIFIED`. Recorded as registered.
- **EUR/USD and USD/JPY: almost every fill is on a candle with no traded volume.** EUR/USD 74 of 85 orders; USD/JPY 30 of 31. WTI's fills are almost all on traded candles (2 of 72 are not).
  - So the "fill" is a resting quote nobody traded, and the 10 contract figure is especially optimistic.
  - With zero-volume fills dropped, USD/JPY 60 has no orders at all, EUR/USD keeps 0 to 3 orders per window, and USD/JPY 30 keeps one.
  - The A windows look good for EUR/USD at every look and turn into large losses in B. That is the sign of noise on 5 to 13 days, not an edge.
- **USD/JPY 60 minutes is the only variant with PF >= 1.5 in both A (3.50) and B (1.87).**
  - It rests on 16 orders on 12 days, all on zero-volume candles: no order was printed against a trade.
  - It is under the 15 day minimum, so `NOT_ENOUGH_DATA`.
  - Its C is read once below with every other variant's.
