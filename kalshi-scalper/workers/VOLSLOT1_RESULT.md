# VOLSLOT1 result (run once 2026-11-03; research only)

Registration `workers/VOLSLOT1_REGISTRATION.md` (commit 6e8c992, pushed before any outcome), code `src/scalper/volslot1.py`, tests `tests/test_volslot1.py` (5 ok),
printout `studies/volslot1_score_2026-11-03.txt`, marker `data/volslot1_score.json`. No change after the outcome. **W3 (2026-10-05 on) never loaded.**
Favourite ask 0.85 to 0.97 at close-180, fill at close-120, hard limit 0.97, held, C = 10, fee 7% x C x p x (1-p) rounded up. Worst single loss $9.73 at 10 contracts.

## Verdict: FALSIFIED (quiet class)
| class | window | n | win vs paid | payoff | PF | PF x1.2 | mean c | z |
|---|---|---|---|---|---|---|---|---|
| QUIET | W1 | 156 | 89.1% vs 89.4% | 0.108 | 0.88 | 0.87 | -0.96 | -0.42 |
| QUIET | W2 | 448 | 88.8% vs 89.9% | 0.102 | 0.82 | 0.80 | -1.63 | -1.10 |
| QUIET | pooled | 604 | 88.9% vs 89.8% | 0.104 | 0.83 | 0.82 | -1.46 | -1.16 |
| LOUD (control) | pooled (W1 / W2) | 559 (127 / 432) | 87.8% vs 87.9% | 0.127 | 0.92 (1.09 / 0.86) | 0.91 | -0.73 | -0.60 |
| MID | pooled | 1,130 | 88.8% vs 89.1% | 0.113 | 0.90 | 0.89 | -0.87 | -0.95 |
| ALL slots (control) | pooled (W1 / W2) | 3,897 (1,282 / 2,615) | 88.6% vs 89.4% | 0.108 | 0.83 (0.83 / 0.84) | 0.82 | -1.48 | -2.97 |

Quiet minus loud: W1 -1.8c (z -0.46), W2 -0.4c (z -0.23), pooled -0.7c (z -0.42): NOT positive in either half. Quiet minus all slots: +0.6c (z 0.24) W1, -0.2c W2, pooled +0.02c.
Kill rule 2 fires three ways (PF under 1.5 in W1 and W2, difference not positive in both halves, x1.2 PF under 1.0). No probe flag, so no capped-probe spec.

## Reading
- The quiet slots are not better than the others: the favourite loses in every class (all slots PF 0.83, z -2.97, win 88.6% against 89.4% paid), the same sign as the Bitcoin favourite
  (PF 0.77) and the mirror of the cheap-side loss. The volatility ordering does nothing: loud is no worse than quiet (loud PF 0.92 vs quiet 0.83).
- Payoff ratio 0.10: one loss (about 90c + fee) costs about 10 wins at 9c; the quiet win rate would need to be about 90.5% (1.6 points above what it was) for break-even.
- Streaks (`streaks.py`, independence, 88.9% win, 100 trades): longest losing run mean 1.8, 95th percentile 3. The risk is the loss COUNT (11 in 100 is normal and costs about $99 of $0.9
  wins per contract-ten), not a long streak.
- By series (quiet, pooled): silver PF 0.99 (n 163), copper 1.08 (98), WTI 0.68 (189), natural gas 0.62 (132), platinum 99 on n 10 (10 wins), palladium 1.07 (12). No FX row: EURUSD,
  GBPUSD and USDJPY have no classified trades in W1+W2 (candles start 2026-09-23, 30 day trailing history plus 8 observations per slot was not met in W2). Energy loses, metals are flat.
- Prediction check: right on the verdict and on the sign of the difference (predicted quiet minus loud +0.5c, got -0.7c), PF 0.83 inside 0.60 to 1.25, win rate 88.9% vs predicted 91.5% (the
  avg fill is 0.898, lower than the 0.92 I assumed), payoff 0.10 vs 0.08, trades 604 vs about 600.
- TODSEAS1's S9 midday result was a post hoc curiosity; its mirror does not hold up: the S9 favourite side is not special either.

## Disclosures
- Realised move is Kalshi's own quote path (sum of |change of YES mid| 1 minute candles to the look), not an outside price; it is a proxy and saturates when the mid is near 0 or 1, which
  is exactly where favourites sit, so "quiet" also means "price already pinned". The result does not show any quote-path definition would fail, only this one.
- 1,604 trades in W1+W2 unclassified (cold start: a slot needs 8 trailing windows and 8 slots); they are in the all-slots control only, not in quiet or loud.
- No event filter, holidays not removed; AUD/USD, USD/CAD left out (on file only inside W3). USWEEP1 (favourites across non-15-minute series) had no result at the time of running; not re-scored here.
- N: 3 tries, +6.
