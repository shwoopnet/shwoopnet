# LADFADE result (V2 worker, 2026-10-30, research only)

Registration `workers/LADFADE_REGISTRATION.md` (commit a197b9e, pushed before any holdout fill or outcome was read). Code
`src/scalper/ladfade.py` (`holdout` run once; nothing changed after the score). Forward candidate `workers/candidates/LADFADE_BTC.json`
(freeze 2026-10-30T12:00:00Z) stays registered and keeps reporting as a dead candidate; it earns nothing.

## The one read: NEWH9 frozen holdout (closes 2026-10-18 00:00 to 2026-10-30 00:00 UTC, Oct 17 7:00 PM to Oct 29 7:00 PM Central)

Funnel over 1,136 holdout KXBTC15M windows: 568 not at :30 or :45 (clock), 78 gap (no ladder event, bracket or candle), 231 flat
(ladder p 0.45 to 0.55), 83 overshoot gap under 3c, 71 fill ask outside 30c to 70c, **105 trades on 12 days**.

| | n | win rate | mean fill | PF C = 10 | PF C = 1 | PF x1.2 | net C = 10 | net x1.2 | day z |
|---|---|---|---|---|---|---|---|---|---|
| all | 105 | 41.9% | 0.401 | **1.01** | 0.99 | 0.99 | +$1.56 | **-$1.75** | 0.02 |
| bought YES (ladder leaned NO) | 55 | 41.8% | 0.385 | 1.07 | 1.05 | 1.05 | +$8.83 | +$7.11 | 0.19 |
| bought NO (ladder leaned YES) | 50 | 42.0% | 0.418 | 0.94 | 0.93 | 0.93 | -$7.27 | -$8.86 | -0.30 |

Zero volume both ways: no trade touched a zero-volume candle; identical without. Running N 627,846, deflated z bar 5.24.

**Verdict: FALSIFIED** (PF at C = 10 1.01, under 1.5; net at fees x1.2 negative). Within the prediction (PF 0.85 to 1.20, 60 to 120
trades, fill 0.36 to 0.42).

## What it says

- The ladder WAS the better estimate: the faded side's mean ladder chance was 0.405 and it won 41.9%.
- But the overshoot is gone within one minute. At the signal candle the faded side's ask averaged **0.341** (6.4c under the ladder);
  at the next candle, where a fill is possible, it averaged **0.401**, on top of the ladder. The 15 minute book corrects its own
  first-minute overshoot in about a minute, so a taker who sees it on a 1 minute candle pays fair price plus the fee.
- Only a sub-minute source could test the earlier entry (the quote recorder covers only the last 150 s of each window, and R6 does
  not cover KXBTC15M's opening minute together with the ladder), and the gap it would chase is about 6c for under a minute against a
  1.7c fee and a spread. Not registered.

## Count

N added: **1**. Running count about 627,845 (after NEWH9) + 1 = **about 627,846**; deflated one-sided z bar 5.24.
