# CALIB1: hand case (2026-11-15 ~16:20Z, before the code and before any read)

The loader is underdog2x.load() reused unchanged (cuts, SOL cut, third-3 drop in the first pass); it is imported, not copied.

**Rows:**
- **K1:** a market with candles at 600, 300 and 120 s left, all two-sided:
  - at 600 s bid 0.20, ask 0.23 gives a YES row at 0.23 (bucket [0.20, 0.25)) and a NO row at 0.80 (bucket [0.80, 0.85));
  - at 300 s bid 0.10, ask 0.12 gives YES 0.12 ([0.10, 0.15)) and NO 0.90 ([0.90, 0.95));
  - at 120 s bid 0.0 (one-sided): no row, counted "not two-sided" at 120 s.
  - Result no: the YES rows lose and the NO rows win.
- **K2:** the 300 s candle missing: counted "missing" at 300 s, no row.
- **K3:** an ask of exactly 0.25 goes to bucket [0.25, 0.30) (the edge goes to the higher bucket), with 1e-9 slack.
- **K4:** a void result: no row, counted "void".

**Bucket statistics:** take one bucket with 4 rows, asks 0.20, 0.22, 0.24, 0.22 and wins 1, 0, 1, 1.
- n 4; wins 3; win rate 0.75; mean ask 0.22; gap 0.53 (53c).
- Fee at 1 contract: ceil(100 x 0.07 x a(1 - a)) / 100 = 0.02 for each of 0.20 (1.12), 0.22 (1.2012) and 0.24 (1.2768), so the mean fee is 0.02.
- z = (3 - 0.88) / sqrt(0.16 + 0.1716 + 0.1824 + 0.1716) = 2.12 / sqrt(0.6856) = 2.5604...

**Candidate test:**
- **C1:** third 1 n 300 gap 0.05 fee 0.02, third 2 n 320 gap 0.045 fee 0.02: both gaps >= 0.04, the same sign, so CANDIDATE.
- **C2:** third 2 n 299: not a candidate.
- **C3:** third 2 gap 0.039 (under fee + 0.02 = 0.04): not a candidate.
- **C4:** a negative gap in both thirds is never a buy candidate. Selling is tested only on the mirror side's own row.

**Neighbours:** a candidate at [0.20, 0.25) prints [0.15, 0.20) and [0.25, 0.30) of the same pool, look and side. At the ends ([0.00, 0.05) or [0.95, 1.00)) only the one neighbour exists.

**Null expectation (Amendment 2):**
- A bucket with 300 rows at ask 0.50 in each third: sd = sqrt(300 x 0.25) / 300 = 0.028868; threshold = fee(0.50) 0.02 + 0.02 = 0.04; z = 1.385641; P(one third) = 1 - Phi(1.385641) = 0.082931; P(both) = 0.006878.
- A bucket under 300 in either third contributes 0 and is not eligible.
- **Hand-case slip (disclosed, first test run):** I wrote P(one third) = 0.082931 and P(both) = 0.006878 from a rounded normal tail. The exact values are 1 - Phi(1.385641) = 0.082928 and P(both) = 0.006877. The test asserts the exact values to 1e-6. The example in the card's Amendment 2 (0.0829, 0.0069) stands as rounded.
