# WTIW1 result (2026-11-02; registration commit ed02a43, pushed before any candle; `src/scalper/wtiw1.py`, `tests/test_wtiw1.py`)

One scored read, raw output in `data/wtiw1_result.txt` (not committed). Cost: 7% x C x p x (1-p) rounded up per order, C = 10, taker at the ask, held; fees x1.2 shown. N: +6 for the three series, running count about 728,706, z bar 5.27. Windows: three equal thirds of the predicted events per series; W3 is the frozen holdout and was NOT read (W1 and W2 did not both pass and no Brier beat the market).

| Series | Events predicted | Universe strikes | Brier model / market mid | W1 | W2 | Pooled read | Verdict |
|---|---|---|---|---|---|---|---|
| KXWTIW + WTIW (WTI weekly) | 148 | 421 | 0.1404 / 0.1390 (132 strikes) | n 2, PF 0.00 | n 1, PF 0.00 | n 3, PF 0.00, mean -29.4c | NOT_ENOUGH_DATA by count (3 of 150); FALSIFIED on Brier (model worse) |
| KXTNOTEW + TNOTEW (10Y weekly) | 170 | 416 | 0.0867 / 0.0832 (109) | n 0 | n 1, PF 0.00 | n 1 | NOT_ENOUGH_DATA (1 of 150); FALSIFIED on Brier |
| KXUSDJPY + USDJPY (daily) | 1,047 | 2,441 | 0.1315 / 0.1299 (912) | n 16, PF 2.02, mean +13.0c | n 18, PF 0.83, mean -1.8c | n 34, PF 1.44, mean +5.2c, event z +0.77 | NOT_ENOUGH_DATA (34 of 150); FALSIFIED on Brier; PF under 1.5 in W2 |

Information-only gaps (not tries): at 5c, JPY W1 n 34 PF 1.23, W2 n 43 PF 0.52; at 12c JPY W1 n 8, W2 n 6. WTI and the yield trade almost nothing at any gap.

## Reading
The prior held. In all three series the 20 day volatility model's Brier is slightly WORSE than the market mid's (by 0.0014 to 0.0035), so the market at the look is at least as good a forecast, and the model almost never differs from the quote by 8c after the fee: 3, 1 and 34 trades in the read windows against the 150 needed. The only positive number, JPY W1 PF 2.02, is 16 trades with z +1.11 and reversed in W2 (PF 0.83): noise at this size. Counting convention as TSA1: the count rule gives NOT_ENOUGH_DATA, and the Brier criterion FALSIFIES independently. Disclosures: FRED is published with a lag, so the daily level is a number already public at the look, which favours the model; the quote is a quote, not a fill; hourly KXWTIH and KXSILVERH were not tried.

## Forward read and recorder
1. Pace: the whole history (4 years) gave 34 trades in two thirds of it for USD/JPY, about 0.2 a week, and 1 to 3 for the weeklies.
2. 150 trades at that pace is about 10 more years for USD/JPY and never for the weeklies: no forward read date is meaningful, none is registered.
3. A recorder is not needed (candles are retrievable later) and would not help: the limit is that the model rarely disagrees with the market.
4. No promote verb. Nothing was changed in `functions/`, L1 or OICORE.
