# OIREL haircut recompute: hand case, written BEFORE the reader code (Idea Desk A, Nov 15, 2026)
Source of the rule: research branch `src/scalper/oirel.py` (decide) and `workers/FALS5_RESULT.md` check 2: KXBTC15M; level = open interest of the candle ending 360 s before the close; doi = open interest of the candle ending 180 s before the close minus level; fire when doi / level > 0.26764675317954373 (strict); cheap side at the signal candle: YES if its ask (yes_ask close) is 0.05 to 0.50 inclusive, else NO if 1 - yes_bid close is 0.05 to 0.50; fill at that side's ask on the candle ending 120 s before the close; held to settlement; 10 contracts; a missing signal, back or fill candle, or open interest 0 or missing at either = NoData (counted, never a no-trade). Haircut (rnd-queue C1 to C10): two-sided only; entry price = ask + h (h = 0, 0.01, 0.02), never past 0.99; fee = fee_up_order(p, 10) = ceil(0.07 x 10 x p x (1-p) x 100 - 1e-9) / 100 per order; cash = 10 x (win - p) - fee. Every candle ending after its market's close is dropped before anything is read (standing reader rule). Halves: floor(n/2) by fill order (the fill candle's time). Label: "upper bound, not fill-checked"; fee mode "per-order rounded". Invented windows only; the extract schema is market(ticker,series,open_ts,close_ts,result,strike,src), candle(ticker,end_ts,bid_c,ask_c,volume,oi).
## Invented windows (C = the window's close_ts; oi = open interest; b/a = yes bid / yes ask close)
| W | oi at C-360 | oi at C-180 | b/a at C-180 | b/a at C-120 | other candle | result | expected |
|---|---|---|---|---|---|---|---|
| 1 | 1000 | 1300 (0.30, fires) | 0.20 / 0.22 | 0.23 / 0.25 | | yes | YES, p 0.25 |
| 2 | 1000 | 1100 (0.10) | 0.20 / 0.22 | 0.23 / 0.25 | | yes | no fire |
| 3 | 1000 | 1400 (0.40) | 0.80 / 0.82 | 0.78 / 0.80 | | no | NO, p 1 - 0.78 = 0.22 |
| 4 | 1000 | 1300 | 0.28 / 0.30 | 0.28 / 0.30 | | no | YES, p 0.30, loss |
| 5 | (none) | 1300 | 0.20 / 0.22 | 0.23 / 0.25 | | yes | NoData (no back candle) |
| 6 | 1000 | 1300 | 0.58 / 0.60 | 0.57 / 0.59 | | no | NO, p 1 - 0.57 = 0.43 |
| 7 | 1000 | 1300 | 0.48 / 0.52 | 0.48 / 0.52 | | yes | fires, no side (both asks 0.52), no trade |
| 8 | 1000 | 1300 | 0.03 / 0.04 | 0.03 / 0.04 | | yes | fires, no side (yes ask 0.04, no ask 0.97), no trade |
| 9 | 1000 | 1300 | 0.18 / 0.20 | 0.18 / 0.20 | candle ending C+60 with b/a 0.98 / 0.99 | yes | YES, p 0.20 (the after-close candle is dropped; reading it would change nothing here except a check that it is ignored) |
Window times: W k closes at base + 900 k, so fill order is W1, W3, W4, W6, W9.
## Expected, by hand (fee_up_order(p, 10), per order, shown with p)
| W | raw p, fee, cash | +1c p, fee, cash | +2c p, fee, cash |
|---|---|---|---|
| 1 | 0.25, 0.14, +7.36 | 0.26, 0.14, +7.26 | 0.27, 0.14, +7.16 |
| 3 | 0.22, 0.13, +7.67 | 0.23, 0.13, +7.57 | 0.24, 0.13, +7.47 |
| 4 | 0.30, 0.15, -3.15 | 0.31, 0.15, -3.25 | 0.32, 0.16, -3.36 |
| 6 | 0.43, 0.18, +5.52 | 0.44, 0.18, +5.42 | 0.45, 0.18, +5.32 |
| 9 | 0.20, 0.12, +7.88 | 0.21, 0.12, +7.78 | 0.22, 0.13, +7.67 |
Totals (n 5, wins 4, losses 1, NoData 1, no fire 1, no side 2): raw net +25.28, PF 28.43 / 3.15 = 9.0254; +1c net +24.78, PF 28.03 / 3.25 = 8.6246; +2c net +24.26, PF 27.62 / 3.36 = 8.2202.
Halves floor(5/2) = 2 by fill order: first half W1, W3 (no loss: PF infinite; raw net +15.03; +1c +14.83; +2c +14.63), second half W4, W6, W9 (raw PF 13.40 / 3.15 = 4.2540; +1c 13.20 / 3.25 = 4.0615; +2c 12.99 / 3.36 = 3.8661).
Discovery/validation pair (printed pair): with the split after W3's close, discovery = W1, W3 and validation = W4, W6, W9: the same figures as the halves.
