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

## Part 2: W3 holdout (10-27 to 10-29), read once after Part 1 was pushed (1cb270c)

107 Bitcoin windows scored.

| Variant | W3 n, PF1 / PF10, net1 / net10, x1.2 net1 | All three windows pooled, n and net1 |
|---|---|---|
| D30 | 3, 7.82 / 8.37, +$0.59 / +$6.04, +$0.58 | 7, -$0.28 |
| D15 | 4, 0.21 / 0.22, -$0.73 / -$7.03, -$0.74 | 7, -$0.85 |
| D45 | 9, 2.84 / 3.03, +$1.12 / +$11.78, +$1.10 | 16, -$0.07 |
| D30L (next-poll fill) | 3, 6.90 / 7.44, +$0.51 / +$5.28 | 7, -$0.36 |

Proxy-outcome agreement W3: 94/97 = 96.9% (under $5: 1/3; $5 to $20: 13/14; above $20: 80/80). All windows: **216/223 = 96.9%**, and **4 of 10 within $5 of the strike**. D30 calibration W3: P under 0.2 n 10, mean P 0.007, YES 0.10; P 0.8 to 1.0 n 8, P 0.978, YES 0.875. Clock: max offset 137 ms, 7% of W3 windows over 100 ms.

## Verdict

**BTCAVG (D30, D15, D45): NOT_ENOUGH_DATA.** No window has the 30 trades the registration needs (largest: D45 W3 with 9). Trades in total across 256 windows: D30 7, D15 7, D45 16. Pooled, every variant is at or below zero (D30 -4.0c a trade, D15 -12.1c, D45 -0.4c), and the bar (PF 1.5 in each window, deflated z 5.17) is out of reach on this sample at any outcome. Tries: 4 (N = 4: D30, D15, D45, D30L); running count about 438,940 plus other workers'.

What the numbers say, without deciding anything:
- **The rule rarely fires because the book is already decided.** At 30 s left 72% of Bitcoin polls are one-sided (bid 0 or ask 1). Where the book is two-sided the model and the book mostly agree within 5c.
- **When the model disagrees, the model is usually the one that is wrong in the tails.** At D30 the model put P under 0.2 (mean 0.01) on 25 windows and 2 of them settled YES (8%): the model is far too sure. The cheap-side buys this produced (D15 mean price 0.03 in W1/W2) lost. The reason is the proxy: a three-venue last-trade median agrees with settlement in 97% of windows overall but in only 4 of 10 within $5 of the strike, which is exactly where a late-minute mispricing would have to be. A model built on this proxy cannot see BRTI's basis to Coinbase, Kraken and Bitstamp, and the quoters can (or price as if they can).
- The 10 contract figures are 1 contract times about 10 (mean fill 9 to 10 of 10 at the recorded ask), so size at the touch was not the constraint; the number of signals was.
- This does not read RECORD1 and does not replace it; RECORD1's registered read (300 trades, 10 dates, five assets) stays as written.

A rerun on more recorder days would need its own registration; the proxy error near the strike, not the sample size, is what I expect to decide it (my prior of a pass stays about 3%).
