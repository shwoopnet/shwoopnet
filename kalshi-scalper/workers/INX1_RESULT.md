# INX1 result (run once, 2026-10-29, Strategy Research V2, worker INX1): all six tries FALSIFIED; holdout C not read

Registration: `workers/INX1_REGISTRATION.md` (pushed in commit 31e3cbc before any scoring). Code `src/scalper/inx1.py` (`yahoo`, `fetch`, `run`; `holdout` not run). Data, not committed: `data/inx1.sqlite` (Kalshi public markets and 1 minute candles), `data/inx1_yahoo/` (Yahoo 5 minute bars of ^GSPC, ^NDX, ^VIX, ^VXN).

## Data

- 47 trading days with a 4 pm event, 2026-08-24 to 2026-10-28 (Kalshi's settled reach starts 2026-08-24; Yahoo 5 minute bars reach 2026-08-06). Windows by date thirds: A 2026-08-24 to 09-14, B 09-15 to 10-06, C 10-07 to 10-28 (15 to 16 days each).
- KXINXU (S&P 500): 2,940 above-K markets in the 4% download screen, 432 in the registered universe (mid 0.05 to 0.95 at close - 75 min), about 9 a day.
- KXNASDAQ100U (Nasdaq 100): 11,161 markets in the screen (strikes every 10 points), 1,166 in the universe, about 25 a day. On 7 days the ^NDX or ^VXN 5 minute bar was missing at the look; no entry on those days (as registered).

## Windows A and B (fill at the candle ending one minute after the signal, as registered)

PF after fees; n orders, independent days in brackets (every order is a different market). Fees x1.2 moves no PF by more than 0.04.

| Variant | A: PF at 1 / 10 contracts (n, days) | B: PF at 1 / 10 contracts (n, days) | Verdict |
|---|---|---|---|
| S&P 60 min | **0.29** / 0.30 (30, 15) | 0.80 / 0.83 (32, 16) | FALSIFIED |
| S&P 30 min | **1.00** / 1.06 (30, 15) | 0.98 / 1.01 (32, 16) | FALSIFIED |
| S&P 10 min | **0.67** / 0.70 (30, 15) | 1.55 / 1.61 (32, 16) | FALSIFIED |
| Nasdaq 60 min | **1.45** / 1.50 (28, 15) | 0.88 / 0.90 (32, 16) | FALSIFIED |
| Nasdaq 30 min | 3.18 / 3.30 (30, 15) | **1.30** / 1.35 (30, 15) | FALSIFIED |
| Nasdaq 10 min | **0.90** / 0.92 (25, 13) | 1.07 / 1.10 (29, 15) | FALSIFIED |

Net at 1 contract, A / B: S&P 60 -$2.20 / -$0.64; S&P 30 +$0.01 / -$0.09; S&P 10 -$1.23 / +$2.20; Nasdaq 60 +$1.31 / -$0.39; Nasdaq 30 +$5.42 / +$0.77; Nasdaq 10 -$0.29 / +$0.26. Every variant has at least 13 days with a trade in each window, so none is `NOT_ENOUGH_DATA` by the registered minimum (8); each fails PF 1.5 in A or B.

**Zero volume.** Many fill candles carried a quote and no trade (S&P 60 min 13 of 30 in A, 22 of 32 in B; Nasdaq 30 and 60 min 23 to 28 of about 30). With those fills dropped, the PFs swing from 0.00 to 6.46 on a handful of trades (for example Nasdaq 30 min 6.46 / 5.29 on 7 and 5 trades; S&P 30 min 0.50 / 0.00); no variant clears 1.5 in both windows on that reading with a meaningful count, and no verdict changes. Full lines in the run output below.

**Information (signal and fill on the candle ending at D, not registered as the fill):** S&P 60 0.94 / 0.38, S&P 30 1.36 / 1.24, S&P 10 1.09 / 0.83, Nasdaq 60 2.12 / 0.00, Nasdaq 30 1.89 / 0.49, Nasdaq 10 0.25 / 1.35. Moving the fill by one minute flips the sign of the window for four of six variants, which is what 25 to 32 orders a window look like: noise.

## Holdout

Window C (2026-10-07 to 10-28) was **not read**: every variant failed A or B, so it decides nothing (the registration computes C only if a variant survives). The pooled day-clustered z was therefore not computed; with 47 days it could not have reached the deflated bar of about 5.17 in any case.

## Reading

- **The orders are almost all cheap tails:** 354 of 360 orders bought the side priced under 50c (YES on 193, NO on 161), and 85% of all 360 orders lost. The model's distribution is WIDER than Kalshi's in the last hour, not narrower as the registration predicted: VIX and VXN (30 day implied vols) scaled by the square root of the minutes left put more weight on a large last-hour move than the market does. The registered "edge" is that vol mismatch, and buying 8c to 15c tails off it is roughly a zero-sum coin flip after the fee.
- **Kalshi's quote is the better forecast at every look (information, windows A and B only, every universe strike with a two-sided candle at D + 60):** Brier score of the model against the Kalshi mid, S&P 60 / 30 / 10 min 0.156 / 0.159 / 0.134 against 0.120 / 0.140 / 0.119; Nasdaq 0.166 / 0.165 / 0.152 against 0.134 / 0.144 / 0.125. The counterparty did not show up; the honest alternative did: Kalshi's index quoters price the level in real time (as gold priced COMEX in GOLDFV1), and a public index print plus a 30 day implied vol is a worse forecast than their quote.
- Nasdaq 30 min A (PF 3.18 on 30 orders, +$5.42) is the kind of window that looks like a lead and is not: its own B is 1.30, its D-candle version is 1.89 then 0.49, and with zero-volume fills dropped it is 7 trades.
- Liquidity is not the problem (median 4 pm S&P event about 370,000 contracts traded); the quote is simply already right. Quote candles are sparse near the close (a two-sided candle at D + 60 for 97% of S&P universe strikes at 60 minutes, 64% at 10 minutes; Nasdaq 91% to 50%), so the 10 minute looks trade fewer strikes than they could; a forward-filled quote was not tried (not registered).

## Counts

Tries: 6 (S&P and Nasdaq x 60, 30, 10 minutes). INDEX1 (the parked 12:30 ET card) is not run separately. Running count before INX1 about 438,904 (V2_STATUS), after INX1 about 438,910 (other V2 workers may have added in parallel). Fees: 7% x C x p x (1 - p) rounded up per order, C = 1 and 10; x1.2 checked. Fill: closing ask (YES) or 1 - closing bid (NO) of the Kalshi candle ending one minute after the signal. No live order rows were used.

## Verdict

**FALSIFIED** (all six variants fail PF 1.5 in window A or B; holdout not read). The family "index level and implied vol against Kalshi's daily index ladders" has no edge at 60, 30 or 10 minutes before the close in 47 days of history. A different index idea would need information Kalshi's quoters do not have (not the index print, not VIX), which this family does not provide.

## Run output (windows A and B)

```
S&P 4 pm days 47: 2026-08-24 to 2026-10-28; window cut A <= 2026-09-14, B <= 2026-10-06
KXINXU-10 [main]  A: n 30 days 15 PF1 0.67 PF10 0.70 net1 -1.23 loss 90.0% PFx1.2 0.66 zerovol 1 PF1(no zv) 0.68 | B: n 32 days 16 PF1 1.55 PF10 1.61 net1 +2.20 loss 75.0% PFx1.2 1.53 zerovol 2 PF1(no zv) 1.63
KXINXU-30 [main]  A: n 30 days 15 PF1 1.00 PF10 1.06 net1 +0.01 loss 90.0% PFx1.2 1.00 zerovol 14 PF1(no zv) 0.50 | B: n 32 days 16 PF1 0.98 PF10 1.01 net1 -0.09 loss 87.5% PFx1.2 0.96 zerovol 21 PF1(no zv) 0.00
KXINXU-60 [main]  A: n 30 days 15 PF1 0.29 PF10 0.30 net1 -2.20 loss 96.7% PFx1.2 0.29 zerovol 13 PF1(no zv) 0.51 | B: n 32 days 16 PF1 0.80 PF10 0.83 net1 -0.64 loss 87.5% PFx1.2 0.78 zerovol 22 PF1(no zv) 0.95
KXNASDAQ100U-10 [main]  A: n 25 days 13 PF1 0.90 PF10 0.92 net1 -0.29 loss 88.0% PFx1.2 0.87 zerovol 8 PF1(no zv) 0.85 | B: n 29 days 15 PF1 1.07 PF10 1.10 net1 +0.26 loss 82.8% PFx1.2 1.05 zerovol 10 PF1(no zv) 1.38
KXNASDAQ100U-30 [main]  A: n 30 days 15 PF1 3.18 PF10 3.30 net1 +5.42 loss 70.0% PFx1.2 3.14 zerovol 23 PF1(no zv) 6.46 | B: n 30 days 15 PF1 1.30 PF10 1.35 net1 +0.77 loss 86.7% PFx1.2 1.28 zerovol 25 PF1(no zv) 5.29
KXNASDAQ100U-60 [main]  A: n 28 days 15 PF1 1.45 PF10 1.50 net1 +1.31 loss 82.1% PFx1.2 1.44 zerovol 25 PF1(no zv) 0.00 | B: n 32 days 16 PF1 0.88 PF10 0.90 net1 -0.39 loss 87.5% PFx1.2 0.86 zerovol 28 PF1(no zv) 5.21
side x price>=0.5 (orders, losses): yes/dog 193/170, no/dog 161/134, no/fav 5/2, yes/fav 1/1
```
