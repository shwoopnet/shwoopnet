# BTCAVG result (V2 worker, 2026-10-29)

Registration `workers/BTCAVG_REGISTRATION.md` (commit 9c3badc, pushed before any price or result was read). Scorer `workers/BTCAVG_score.py`, data `quote-data` at b7dc9cbe8. Nothing in the rule, proxy, margin or windows changed after scoring.

## Part 1: W1 (10-22 to 10-24) and W2 (10-25 to 10-26), written before the holdout was read

149 Bitcoin windows scored (W1 + W2). Trades per variant (1 contract unless noted; PF at 1 / 10 contracts):

| Variant | W1 n, PF1 / PF10, net1 | W2 n, PF1 / PF10, net1 |
|---|---|---|
| D30 | 2, 0.00 / 0.00, -$0.70 | 2, 0.00 / 0.00, -$0.17 |
| D15 | 2, 0.00 / 0.00, -$0.06 | 1, 0.00 / 0.00, -$0.06 |
| D45 | 5, 0.07 / 0.09, -$1.15 | 2, 0.81 / 2.21, -$0.04 |
| D30L | identical to D30 (the next poll's price never differed) | |

Every window is far under the 30 trades the registration needs, so W1 and W2 alone already make every variant `NOT_ENOUGH_DATA`. 0 of 11 D30/D15 trades won (most were longshots: mean price 0.21 at D30, 0.03 at D15, where the model said the cheap side was 35 to 60c underpriced). D45 won 2 of 7.

Why so few: at 30 s left 72% of Bitcoin polls are one-sided (bid 0 or ask 1, the market already decided), which the rule skips by design (D30 skipped 102 of 149 windows for having no two-sided poll within 5 s of the decision time; D15 127, D45 77). Of the rest, the 5c margin fired on 4 (D30), 3 (D15) and 7 (D45).

Proxy-outcome agreement (W1+W2, 126 windows with at least 48 of 60 final seconds): 122/126 = 96.8%. By |A_proxy - strike|: under $5 3/7 (43%), $5 to $20 13/13, $20 to $50 31/31, over $50 75/75. The three-venue median is a good proxy away from the strike and a coin flip within $5 of it, which is exactly where a last-30-seconds edge would have to live.
D30 calibration: P 0.0-0.2 n 15, mean P 0.012, YES rate 0.067; P 0.8-1.0 n 15, P 0.997, YES 1.000. Clock offsets max 19 ms.
