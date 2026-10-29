# FAM2 result: XLEAD1, macro futures leading the 15 minute Kalshi quotes (run once, 2026-10-29)

Registration: `workers/FAM2_REGISTRATION.md` (pushed in 26ab25a before scoring). Novelty: `workers/FAM2_CHECK.md`. Family A (DVOL against the ladder's implied volatility) was judged tested as LAD1 and not run.

**All four tries FALSIFIED (kill: PF under 1.0 in W1). Holdout W3 not read:** every try failed before it, so reading it would decide nothing.

PF after per-order rounded fees, primary fill (closing ask of the candle ending at the decision minute, macro bars that ended a minute earlier). W1 = closes 2026-10-01 to 10-09, W2 = 10-10 to 10-18.

| Try | W1 n | W1 PF at 1 / 10 | W2 n | W2 PF at 1 / 10 | Mean per contract W1 / W2 | Fees x1.2 W1 / W2 | Verdict |
|---|---|---|---|---|---|---|---|
| V1 ES=F shock -> Bitcoin, Ethereum, hold | 252 | 0.86 / 0.88 | 200 | 0.71 / 0.73 | -2.94c / -6.24c | -3.31c / -6.59c | FALSIFIED |
| V2 same, sell at the bid 3 min later | 252 | 0.50 / 0.55 | 200 | 0.53 / 0.59 | -5.87c / -4.99c | -6.54c / -5.64c | FALSIFIED |
| V3 DX-Y.NYB shock -> gold (opposite), hold | 107 | 0.81 / 0.83 | 109 | 1.08 / 1.10 | -3.96c / +1.48c | -4.33c / +1.11c | FALSIFIED |
| V4 ^TNX shock -> gold (opposite), hold | 30 | 0.79 / 0.81 | 23 | 1.43 / 1.46 | -4.03c / +8.00c | -4.37c / +7.60c | FALSIFIED (W2 also under 30 trades) |

Day-clustered z: V1 -0.72 / -1.07, V2 -2.79 / -2.21, V3 -0.97 / +0.31, V4 -0.44 / +0.82; nothing near the deflated bar of about 5.17. Next-candle fills: V1 0.93 / 0.72, V3 0.80 / 1.04, V4 0.73 / 1.47 (no verdict changes). Zero-volume entry candles: none, so both readings are identical. V2 held 1 and 5 trades to settlement for want of an exit bid. Known slip, decides nothing: the script's V2 next-candle line scores hold-to-settlement, not the 3 minute exit.

**Information: the lag profile answers the question directly.** Correlation of the macro 1 minute change with the Kalshi YES mid change k minutes later (k = 0 is the same minute):

| Pair | k = -1 | k = 0 | k = +1 | k = +2 | n (k = 0) |
|---|---|---|---|---|---|
| ES=F -> Bitcoin, Ethereum | +0.029 | **+0.378** | +0.016 | +0.000 | 27,483 |
| DX-Y.NYB -> gold | -0.022 | **-0.353** | -0.002 | +0.002 | 15,353 |
| ^TNX -> gold | -0.028 | **-0.336** | -0.002 | -0.017 | 4,776 |

The macro moves and the Kalshi quotes move in the same minute (correlation about 0.35 in magnitude), and from one minute on there is nothing (|corr| 0.02 or less). Kalshi Bitcoin, Ethereum and gold do not lag the S&P future, the dollar or the 10 year yield by a minute or more; the counterparty named in the registration did not show up. Prediction (peak at k = 0, FALSIFIED) held.

N tried: 4 (running count about 438,674 plus other workers'). Data: Yahoo ES=F, DX-Y.NYB, ^TNX 1 minute, 2026-10-01 to 10-29 (public, scratchpad, not committed); Kalshi candles from `book`, `fresh`, `five`. Code: `src/scalper/xlead1.py` (`python -m scalper.xlead1 <yahoo_dir> --lag`). Nothing to build.
