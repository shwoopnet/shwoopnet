# XMET1 result (2026-11-03; registered in b70fda4 before any candle was read; script `src/scalper/xmet1.py`, tests `tests/test_xmet1.py`)

**Verdict: FALSIFIED.** One scored run on all settled history (gold 4,556 windows, 1,105 triggered; metals 2026-08-27 to 2026-11-02, platinum and palladium from mid September; 53 eligible dates, W1 17 / W2 18 / W3 18). Cost: fee 7% x C x p x (1-p) rounded up, C = 10, taker at the ask (x1.2 shown). N +2, running count about 728,722, deflated z bar about 5.27. Raw output: the lines below are the run's output unchanged.

```
gold windows 4556, triggered 1105, eligible metal windows (quote rule passed) 3587
H W1: n 168 days 17 PF 0.53 mean -9.92c z -5.17 | fees x1.2 mean -10.15c
H W2: n 404 days 18 PF 1.07 mean +1.26c z +0.50 | fees x1.2 mean +1.03c
H W3 holdout: not read (W1 failed)
H pooled (W1, W2): n 572 days 35 PF 0.89 mean -2.02c z -0.99
   KXSILVER15M: n 179 win rate 0.279 PF 0.88 mean -2.47c
   KXCOPPER15M: n 209 win rate 0.187 PF 0.63 mean -7.04c
   KXPLATINUM15M: n 86 win rate 0.256 PF 0.98 mean -0.28c
   KXPALLADIUM15M: n 98 win rate 0.367 PF 1.49 mean +7.99c
M control (against gold) W1: n 279 PF 0.92 mean -1.33c | W2: n 712 PF 0.81 mean -3.08c | pooled n 991 PF 0.84 mean -2.59c z -1.87
   silver n 358 PF 1.01, copper n 292 PF 1.06, platinum n 171 PF 0.57, palladium n 170 PF 0.52
H pooled win rate 0.257, payoff ratio 2.58, PF 0.89, mean -2.02c, n 572
STREAKS (chronological, p=observed): longest losing run 15 of n 572; in 100 trades p95 20 p99 25; chance of >=1 ten-loss run in 100 trades 76%
```

## Against the registered prediction
Win rate 0.257 (predicted 0.27 to 0.33: slightly below), payoff ratio 2.58 (predicted 1.8 to 2.8: inside), n 572 (300 to 900: inside), PF 0.53 and 1.07 (predicted 0.7 to 1.1: W1 below, W2 inside), pooled mean -2.02c (-3c to +1c: inside). The control landed within 0.6c of H pooled (registered: within 1c). The prior was right: the cheap side of the metals in gold's direction is not paid for the follow-through.

## What the numbers say
- Hypothesis H does not beat the mirror M (+0.57c on the pooled mean, bar +2.0c): the direction of gold's move adds almost nothing to which cheap side wins. The cost of buying a cheap side with a 26 percent win rate (about 2c a trade after fee) is what the pooled mean shows.
- Per metal, H is mixed and every cell is small: palladium PF 1.49 on 98 trades (z not given; one cell of four, W3 unread, not a finding), copper PF 0.63. In the control the pattern flips (palladium 0.52, copper 1.06): the metal cells are noise around the cost.
- W1 PF 0.53 on 168 trades has a date-clustered z of -5.17 (information only); W2 +0.50. The window split is not stable.
- The holdout W3 was NOT read (W1 and W2 did not both pass). The pooled line above is W1 + W2 only.

## Streak report (observed win rate 0.257)
Longest losing run in the chronological H sequence: 15 of 572. In 100 trades (independence assumed): 95th percentile of the longest losing run 20, 99th percentile 25, chance of at least one 10-loss run 76%. Real losses cluster by day (four metals per window), so this is a floor.

## Disclosures
- Fetch only: the first grouping (4 windows per request) was too slow under a shared rate limit, the second (10 windows) hit Kalshi's 10,000 candlestick cap for far-apart windows, the final grouping is at most 10 windows within 2 hours. No scoring rule, threshold, universe or window was changed after registration; the scored code was the registered code. Two fetch processes ran at the same time for a short while (same cache, same data).
- Missing candles: 5 gold and 1 copper settled markets have no candles in the signal range (they count as no signal / no quote).
- The leader's SD uses the previous 96 windows' same-slot 3 minute changes (registered). The cache is in /tmp (`XMET1_CACHE`), not committed.
- Not run: any variant (trigger factor, look, band). No forward registration is recommended.

## Forward read and recorder
No forward read recommended (FALSIFIED). If someone insists: at the observed H rate (572 trades in 35 read dates, about 16 a day) 150 fresh trades take about 10 days, earliest 2026-11-13; candles and results stay retrievable, so no recorder is needed. The registered earliest date (2026-12-01) was for a NOT_YET_FALSIFIED outcome and does not apply.
