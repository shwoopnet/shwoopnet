# XRPFAV6 and XRPFAV10 haircut recompute: hand case, written BEFORE the reader code (Idea Desk A, Nov 15, 2026)
Rule source: research branch `src/scalper/regime_b2.py` (rows XRPFAV6 and XRPFAV10; README:9192): KXXRP15M markets with a result; per market the pick is the LAST candle (by end time) whose time left (close - end_ts) lies in [left_lo, left_hi]: XRPFAV6 330 to 400 s (so the candle ending 360 s before the close), XRPFAV10 570 to 640 s (the candle ending 600 s before the close); skip the market if that candle has bid or ask missing, bid <= 0, ask >= 1 or ask <= bid; XRPFAV6 also skips a spread (ask - bid) over 0.02, XRPFAV10 has no spread limit; the favourite side is YES if the YES ask >= the NO ask (1 - bid), else NO; skip unless its ask p is 0.88 to 0.92 inclusive (the card's raw band test); hold to settlement. Haircut (rnd-queue C1 to C10, same as OIREL): price paid = p + h, h = 0, 0.01, 0.02, never past 0.99; fee_up_order(price, 10) per order; cash = 10 x (win - price) - fee; halves floor(n/2) by close time; every candle ending after its market's close dropped. Entry candle is 330 or 570 s before the close: not in the last 2 minutes, so 1c is primary (C8), 2c printed. Label: "upper bound, not fill-checked; fee mode per-order rounded". The printed 481 and 358 (Sep 3 to Oct 13, unrounded fee) cannot be reproduced whole: the extract cuts from 2026-10-03 (XOI1), so the surviving window is Sep 3 to Oct 2.
## Invented windows (close C; candle at C-360 for XRPFAV6, the same quote at C-600 for XRPFAV10; b/a = YES bid / YES ask close)
| W | b / a | result | XRPFAV6 | XRPFAV10 |
|---|---|---|---|---|
| A1 | 0.89 / 0.90 | yes | YES p 0.90 (win) | same |
| A2 | 0.10 / 0.11 | no | NO p 0.90 (win) | same |
| A3 | 0.88 / 0.89 | no | YES p 0.89 (loss) | same |
| A4 | 0.88 / 0.91 (spread 0.03) | yes | skip (spread over 0.02) | YES p 0.91 (win) |
| A5 | 0.92 / 0.93 | yes | skip (p 0.93 over 0.92) | skip |
| A6 | candle only at C-600: 0.89 / 0.90; none at C-360 | yes | skip (no candle in range) | YES p 0.90 (win) |
| A7 | 0.00 / 0.92 | yes | skip (bid 0) | skip |
Close times increase with W (fill order A1, A2, A3, A4, A6).
## Expected, by hand (fee_up_order(p, 10); price = p + h)
Per trade cash (raw / +1c / +2c): win at 0.90 (A1, A2, A6) +0.93 / +0.84 (price 0.91, fee 0.06) / +0.74 (price 0.92, fee 0.06); loss A3 (p 0.89, fee 0.07) -8.97 / (0.90, fee 0.07) -9.07 / (0.91, fee 0.06) -9.16; win A4 (p 0.91, fee 0.06) +0.84 / (0.92, fee 0.06) +0.74 / (0.93, fee 0.05) +0.65.
**XRPFAV6:** trades A1, A2, A3 (n 3, 2 wins, 1 loss). Raw net -7.11, PF 1.86 / 8.97 = 0.2074; +1c net -7.39, PF 1.68 / 9.07 = 0.1852; +2c net -7.68, PF 1.48 / 9.16 = 0.1616. Halves floor(3/2) = 1: half 1 = A1 (no loss: infinite), half 2 = A2, A3: raw 0.93 / 8.97 = 0.1037, +1c 0.84 / 9.07 = 0.0926, +2c 0.74 / 9.16 = 0.0808.
**XRPFAV10:** trades A1, A2, A3, A4, A6 (n 5, 4 wins, 1 loss). Raw net -5.34, PF 3.63 / 8.97 = 0.4047; +1c net -5.81, PF 3.26 / 9.07 = 0.3594; +2c net -6.29, PF 2.87 / 9.16 = 0.3133. Halves floor(5/2) = 2: half 1 = A1, A2 (infinite), half 2 = A3, A4, A6: raw 1.77 / 8.97 = 0.1973, +1c 1.58 / 9.07 = 0.1742, +2c 1.39 / 9.16 = 0.1517.
Counts XRPFAV6: skip spread 1, skip band 1, skip no candle 1, skip bad quote 1; XRPFAV10: skip band 1, skip bad quote 1.
