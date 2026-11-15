# FLIPS0-X haircut recompute: hand case, written BEFORE the reader code (Idea Desk A, Nov 15, 2026)
Rule source: research branch `src/scalper/flips0x.py` (series_rows) with `ideas100.py` (ENTRIES L1360 = 360 s left, band 0.88 to 0.97; rule FLIPS_0 and `flips`, `path`, `side_mid`), `ideas20.py` (`load_btc`, `at`, `entries`) and `lstrats.favorite`, `analyze.valid_quote`; README:6084 pre-registration and the Oct 23 result (n 536, raw PF 1.77, NOT_ENOUGH_DATA). Per market of the 16 non-Bitcoin non-Ethereum 15 minute series: candles with a missing bid or ask are DROPPED at load (a market keeps its other candles); the decision candle is the one ending exactly 360 s before the close, `e` = the candles strictly before it; the favourite is `favorite(bid, ask, (0.88, 0.97))`: YES if its ask is in the band, else NO at round(1 - bid, 4), after the usable-quote test (bid >= 0.001, ask <= 0.999, ask >= bid, ask - bid <= 0.10); FLIPS_0 needs len(e) >= 4 and zero flips on the favourite side's mid path (side mid of each earlier candle, then of the decision candle; YES mid = (bid + ask)/2, NO mid = 1 - that); a flip count ignores minute changes of 0.004 or less (absolute), then counts sign changes between consecutive remaining changes; hold to settlement. Haircut (rnd-queue C1 to C10): price = ask + h (h 0, 0.01, 0.02; never past 0.99), fee_up_order(price, 10) per order, cash = 10 x (win - price) - fee; halves floor(n/2) by close time; every candle ending after the close dropped. The printed "net minus the series' own all-entries mean" is NOT used here: the PF is on the unadjusted cash (the printed raw PF 1.77). Entry candle 360 s before the close: 1c is PRIMARY (C8), 2c printed. NC15-type thin series (silver, copper, WTI, natural gas, FX) would take 2c primary under C11; the recompute prints per-series rows only for information. Label: "upper bound, not fill-checked; fee mode per-order rounded".
Printed result: n 536 over about Aug 6 to Oct 23; the extract cuts per series (spec): XOI1 from 2026-10-03 for XRP, HYPE, BNB, NEAR, ZEC; FXREF1 from 2026-10-03T16:00Z for WTI, EUR/USD, GBP/USD, USD/JPY; W3 from 2026-10-05 for gold, silver, copper, natural gas, platinum, palladium; Dogecoin has no cut (it ends at 2026-10-23). So the survivors are a mix of windows: a cut-window recompute, NOT a reproduction of 536.
## Invented windows (close C; candles ending at C-600, C-540, C-480, C-420, then the decision candle at C-360; b/a = YES bid / ask close)
| W | earlier candles' YES mids | decision candle b / a | result | expected |
|---|---|---|---|---|
| F1 | 0.84, 0.86, 0.88, 0.90 | 0.91 / 0.92 | yes | YES p 0.92, 0 flips, win |
| F2 | 0.84, 0.88, 0.86, 0.90 | 0.91 / 0.92 | yes | skip (2 flips) |
| F3 | 0.20, 0.17, 0.14, 0.11 (so NO mids 0.80, 0.83, 0.86, 0.89) | 0.05 / 0.06 | no | NO p 0.95 (YES ask 0.06 out of band, NO 0.95 in), 0 flips, win |
| F4 | 0.80, 0.82, 0.84, 0.86 | 0.89 / 0.90 | no | YES p 0.90, 0 flips, loss |
| F5 | only three earlier candles 0.84, 0.86, 0.88 | 0.91 / 0.92 | yes | skip (fewer than 4 earlier candles) |
| F6 | 0.84, 0.86, 0.88, 0.90 | 0.97 / 0.98 | yes | skip (YES ask 0.98 out of band; NO price 0.03) |
| F7 | 0.84, 0.86, 0.8575, 0.88 | 0.89 / 0.91 | yes | YES p 0.91; the -0.0025 minute change is ignored, 0 flips, win |
(Earlier candles use bid = mid - 0.01 and ask = mid + 0.01.) Close times increase with W; fill order F1, F3, F4, F7.
## Expected, by hand (fee_up_order(price, 10))
F1: raw p 0.92, fee 0.06, cash +0.74; +1c p 0.93, fee 0.05, +0.65; +2c p 0.94, fee 0.04, +0.56.
F3: raw p 0.95, fee 0.04, +0.46; +1c p 0.96, fee 0.03, +0.37; +2c p 0.97, fee 0.03, +0.27.
F4: raw p 0.90, fee 0.07, -9.07; +1c p 0.91, fee 0.06, -9.16; +2c p 0.92, fee 0.06, -9.26.
F7: raw p 0.91, fee 0.06, +0.84; +1c p 0.92, fee 0.06, +0.74; +2c p 0.93, fee 0.05, +0.65.
Totals (n 4, 3 wins, 1 loss): raw net -7.03, PF 2.04 / 9.07 = 0.2249; +1c net -7.40, PF 1.76 / 9.16 = 0.1921; +2c net -7.78, PF 1.48 / 9.26 = 0.1598. Halves floor(4/2) = 2: half 1 = F1, F3 (no loss: infinite), half 2 = F4, F7: raw 0.84 / 9.07 = 0.0926, +1c 0.74 / 9.16 = 0.0808, +2c 0.65 / 9.26 = 0.0702.
Skips: flips 1, too few earlier candles 1, band 1.
