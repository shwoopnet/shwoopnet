# SEARCH1 chosen-combination haircut recompute: hand case, written BEFORE the reader code (Idea Desk A, Nov 15, 2026)
Rule source: research branch `src/scalper/search1.py` (and `lstrats.favorite`, `analyze.valid_quote`; README:6030 pre-registration and the Oct 23 result). The CHOSEN combination (the printed result line, FALSIFIED, confirmation n 361, PF 1.31): Bitcoin and Ethereum 15 minute markets, entry at the candle ending EXACTLY 420 s before the close, favourite band 0.97 to 0.995 inclusive (YES if its ask is in the band, else NO if round(1 - YES bid, 4) is), exit SL50: after the entry, the first candle ending after the entry candle and at least 30 s before the close (end <= close - 30) whose bought-side bid is 0.50 or lower is sold at that bid (YES bid = bid close; NO bid = round(1 - ask close, 4)); otherwise hold to settlement. A market counts only if it has a yes or no result AND every one of its candles has a bid and an ask (a market with any incomplete candle is out whole). A usable quote at the entry candle: bid >= 0.001, ask <= 0.999, ask >= bid, ask - bid <= 0.10. Haircut (rnd-queue C1 to C10): entry price = ask + h (h = 0, 0.01, 0.02; never past 0.99); exit price = bid - h (never below 0.01); fee_up_order(price, 10) per order on EACH leg (an exit pays a second fee); cash = 10 x (exit - entry) - fee_in - fee_out, or 10 x (win - entry) - fee_in when held. The exit can fall in the last 2 minutes, so 2c is the PRIMARY line (C8) and 1c is printed. Halves floor(n/2) by close time. Candles ending after the close dropped. Label: "upper bound, not fill-checked; fee mode per-order rounded".
Printed result to compare: confirmation third (original days from about 2026-09-27 to 2026-10-23; the original cut day is INFERRED from 79 days x 2/3, not read) n 361, PF 1.31. The extract cuts from 2026-10-03, so only about Sep 27 to Oct 2 of the confirmation third survives: a recompute on the cut window, not a reproduction; it prints both the surviving confirmation days and the earlier days (discovery, where the combination was CHOSEN: information only, selected on that window).
## Invented windows (close C; b/a = YES bid / ask close; entry candle ends at C-420)
| W | candle at C-420 b / a | later candles | result | expected |
|---|---|---|---|---|
| S1 | 0.97 / 0.98 | yes bid stays above 0.50 | yes | YES at 0.98, held, win |
| S2 | 0.01 / 0.02 (YES ask 0.02 out of band; NO price 0.99 in band) | C-360: 0.02 / 0.03; C-240: 0.52 / 0.55 (NO bid 1 - 0.55 = 0.45) | no | NO at 0.99, SL50 exit at NO bid 0.45 |
| S3 | 0.96 / 0.97 | yes bid stays above 0.50 | no | YES at 0.97 (ask on the band edge), held, loss |
| S4 | 0.50 / 0.52 | | yes | skip (not in band) |
| S5 | no candle at C-420 (only C-360) | | yes | skip (no candle) |
| S7 | as S1 but one candle of the market has a null bid | | yes | skip (incomplete market) |
Close times increase with W (fill order S1, S2, S3).
## Expected, by hand (fee_up_order(price, 10) per leg)
S1: raw price 0.98, fee 0.02, cash +0.18; +1c price 0.99, fee 0.01, +0.09; +2c price capped 0.99, +0.09.
S2: raw entry 0.99, exit 0.45, fees 0.01 + 0.18, cash -5.59; +1c entry 0.99 (cap), exit 0.44, fees 0.01 + 0.18, -5.69; +2c exit 0.43, fees 0.01 + 0.18, -5.79.
S3: raw price 0.97, fee 0.03, cash -9.73; +1c price 0.98, fee 0.02, -9.82; +2c price 0.99, fee 0.01, -9.91.
Totals (n 3: 1 win, 2 losses, 1 of them an SL50 exit): raw net -15.14, PF 0.18 / 15.32 = 0.01175; +1c net -15.42, PF 0.09 / 15.51 = 0.00580; +2c net -15.61, PF 0.09 / 15.70 = 0.00573. Halves floor(3/2) = 1: half 1 = S1 (no loss: infinite), half 2 = S2, S3: PF 0 (raw net -15.32, +1c -15.51, +2c -15.70).
Skips: band 1, no candle 1, incomplete market 1.
