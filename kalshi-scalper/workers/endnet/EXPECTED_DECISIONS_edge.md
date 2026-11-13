# ENDNET: the expected decisions of the EDGE set, written BEFORE any run (MADE-UP rows, Nov 13, 2026, 15:27Z by this desk's clock)

Committed before `edge_set_MADE_UP_DATA.py` exists and before the scorer is run on it. Eighteen games, closing one a day from 2026-11-21 (game k closes on Nov 20 + k days at 02:00Z, so games 1 to 10 are the first half and games 11 to 18 the second half, which starts 2026-12-01). Every game has a state minute at 240 s left (not qualifying) and an entry minute as stated. Prices in cents.
Fee per contract: ceiling to the cent of (7% x p x (1 - p) x 10 x 100) cents, over 10. Pay = ask + 1.

| k | game | the edge | decision |
|---|---|---|---|
| 1 | e01_exactly_180s | 180 s left (the line is "<= 180"), 3-2, line 5.5, bid 28 ask 30, YES | ENTER, pay 31, fee 1.5c, pnl +0.675 |
| 2 | e02_181s | 181 s left | SKIP "no state minute" |
| 3 | e03_line_one_above | total 5, line 6.0 (f - total = 1: two goals needed) | SKIP "no strike one goal away" |
| 4 | e04_line_just_inside | total 5, line 5.9 (f - total = 0.9) bid 28 ask 30, YES | ENTER, pay 31, pnl +0.675 |
| 5 | e05_line_below_total | total 5, line 4.5 (already decided) | SKIP "no strike one goal away" |
| 6 | e06_two_strikes | total 5, lines 5.5 (bid 28 ask 30, YES) and 6.5 (bid 8 ask 10, NO) | ENTER on 5.5 only, pnl +0.675 |
| 7 | e07_ask_14 | ask 14 (bid 12) | SKIP "ask out of band" |
| 8 | e08_ask_15_spread_4 | ask 15 bid 11, NO | ENTER, pay 16, fee 9.408 -> 10c = 1.0c, pnl -0.170 |
| 9 | e09_ask_46 | ask 46 (bid 43) | SKIP "ask out of band" |
| 10 | e10_spread_5 | bid 10 ask 15 | SKIP "spread too wide" |
| 11 | e11_void | bid 28 ask 30, result "void" | ENTER (counted), NOT settled, not scored |
| 12 | e12_result_null | bid 28 ask 30, result null | ENTER (counted), NOT settled, not scored |
| 13 | e13_candle_one_minute_early | the only candle ends one minute BEFORE the entry minute | SKIP "no candle at the entry minute" |
| 14 | e14_one_look | the first qualifying minute (170 s) has no candle; a later qualifying minute (110 s) has a good one | SKIP "no candle at the entry minute" (one look only) |
| 15 | e15_tie_then_one_goal | tied at 170 s (not qualifying), 3-2 at 120 s with a candle, bid 28 ask 30, NO | ENTER at the 120 s minute, pay 31, fee 1.5c, pnl -0.325 |
| 16 | e16_overtime | period 4, 100 s left | SKIP "no state minute" |
| 17 | e17_away_leads | home 2, away 3, line 5.5, bid 28 ask 30, YES | ENTER, pay 31, pnl +0.675 |
| 18 | e18_spread_4_mid | bid 36 ask 40, NO | ENTER, pay 41, fee 16.9 -> 17c = 1.7c, pnl -0.427 |

## Expected printed figures
- `measure`: games 18 | entries 9 | skipped: ask out of band 2, no candle at the entry minute 2, no state minute 2, no strike one goal away 2, spread too wide 1 (that is 9 skips, and 9 + 9 = 18). Ask at entry: sorted (15, 30 x 7, 40), median **30.0**, lowest 15, highest 40. Entries a week over 4 weeks: **2.25**. STAGE 1: CLOSED, on the week line (2.25 under 6) and not on the ask line.
- `score`: entries 9, settled 7 (e11 and e12 are unsettled), wins 4 (k = 1, 4, 6, 17). Development: n 7 | wins 4 | net 4 x .675 - .170 - .325 - .427 = **+1.778** | mean +0.2540 | gains 2.700 against losses 0.922: **cash PF 2.93**.
- First half (k 1 to 10): settled k = 1, 4, 6, 8: n 4 | wins 3 | net 2.025 - .170 = **+1.855** | mean +0.4638 | PF 2.025 / .170 = **11.91**.
- Second half (k 11 to 18): settled k = 15, 17, 18: n 3 | wins 1 | net .675 - .325 - .427 = **-0.077** | mean -0.0257 | PF .675 / .752 = **0.90**.
- VERDICT: NOT_ENOUGH_DATA (7 settled entries, need 150).
