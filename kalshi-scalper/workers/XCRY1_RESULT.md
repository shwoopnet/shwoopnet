# XCRY1 result (2026-11-03; registered in d274ec5 before any data; `src/scalper/xcry1.py`, `tests/test_xcry1.py`, run once)

**FALSIFIED.** Bitcoin spot moving at least 1.0 trailing-sigma between 360 s and 180 s before the close, then buying the same-direction cheap side (ask 0.05 to 0.50) of HYPE, NEAR, Zcash and BNB 15 minute markets at 180 s, held to settlement, lost in both windows read. The W3 holdout was not read (W1 and W2 both under PF 1.5). Not a pass; no promote verb.

Data: 25,868 settled markets (four series, 2026-08-27 to 2026-11-02, 68 dates), 25,814 eligible (Bitcoin signal, valid quote, spread <= 0.10, 5 minute volume >= 10); OKX BTC-USDT 1 minute klines (99,700). Cost: fee 7% x C x p x (1-p) rounded up, C = 10, taker at the ask (x1.2 stress). N = 728,704, z bar 5.27.

Printed result (verbatim from the one run):
```
eligible markets 25814; Bitcoin trigger fired in 5318; follow trades 976; control trades 1387
follow W1: n 393 days 23 PF 0.85 mean -2.59c z -1.11 | fees x1.2 mean -2.81c | payoff ratio 3.00
control W1: n 509 days 23 PF 0.87 mean -2.11c z -1.41
follow W2: n 338 days 23 PF 0.82 mean -3.31c z -1.26 | fees x1.2 mean -3.54c | payoff ratio 3.01
control W2: n 435 days 23 PF 0.69 mean -5.07c z -2.04
W3 holdout: not read (W1 and W2 did not both pass)
follow pooled (windows read): n 731 days 46 PF 0.84 mean -2.93c z -1.67
control pooled (windows read): n 944 days 46 PF 0.78 mean -3.47c z -2.43
follow win rate 21.8% on 731; payoff ratio (avg win / avg loss) 3.01; mean entry price 0.235
streaks: longest losing run 21; 100 trades at win rate 21.8%: p95 23 p99 30; P(>=1 ten-loss run in 100) 0.894
  by asset: HYPE n 188 PF 1.03 (+0.56c, z +0.18); NEAR n 182 PF 0.76 (-4.39c); ZEC n 179 PF 0.83 (-2.81c); BNB n 182 PF 0.74 (-5.17c)
XCRY1: FALSIFIED | W1 PF 0.85 under 1.5; W1 not positive at fees x1.2; W2 PF 0.82 under 1.5; W2 not positive at fees x1.2
OICORE (OIREL research rule, Bitcoin) windows 584 in 2026-08-06..2026-10-27; XCRY1 trades in that span 731; in a window where OICORE also fires 43 (5.9%)
daily PnL correlation XCRY1 vs OICORE over 45 days: -0.22
```

Reading:
- The numeric prediction was right on the verdict and the profit factor (0.85 predicted, 0.84 observed, inside 0.6 to 1.1) and wrong on the shape: win rate 21.8% (predicted 27%, range 24% to 31%) and payoff ratio 3.0 (predicted 2.2, range 1.9 to 2.6), because the mean entry price was 0.235, not about 0.30; trades 976 (predicted 2,000 to 5,000), because the cheap side matched the direction less often than guessed. Streaks are longer than the registered table because the win rate is lower: observed longest losing run 21; at 21.8% the 95th/99th percentile of the longest run in 100 trades is 23/30 and a 10-loss run in 100 trades has chance 0.89.
- The control (cheap side AGAINST Bitcoin) is also negative (PF 0.78), and worse than the follow in W2. The Bitcoin direction carries no usable information over the quote: both sides of the cheap-side bet lose about the fee plus the longshot premium. Follow beats control by 0.06 in PF pooled (0.84 vs 0.78) and 0.5c a contract, not distinguishable from noise (z of each is below 2.5 in magnitude).
- Per asset only HYPE is near break-even (PF 1.03, z +0.18); with four assets and no correction that is noise.
- Overlap with OICORE: 5.9% of XCRY1 trades (43 of 731, in the span 2026-08-06 to 2026-10-27 where Bitcoin open interest is stored) sit in a window where the OIREL research rule also fires on Bitcoin; the daily PnL correlation is -0.22 over 45 days. Both are information only; with a FALSIFIED result they do not matter.
- Counterparty read: consistent with the registered prior. The alt quote already reflects Bitcoin; the settlement average gives 120 s of drift to come but nothing beyond what the quote prices.

Limits and disclosures (none changes the verdict):
- Registered code was run unchanged after commit d274ec5; no change after registration. The follow and control windows are the date thirds of all eligible markets (23 dates each).
- One venue (OKX USDT) is not the CF Benchmarks index; the basis is unmeasured. A 1 minute resolution hides a sub-minute lead. Fill is assumed at the quoted ask with no size; candles show none.
- Trades in one window share Bitcoin's move (up to four per window), so n counts correlated trades; statistics are clustered by date.
- W3 was not read, so it is still a clean holdout for any later variant, but no variant is planned.

Forward read: none planned (FALSIFIED). If the owner wants one anyway: earliest 2026-12-03 (30 new days after the history end), no recorder needed for a candle-and-kline re-read.
