# OEXIT1 result: selling half at 3x on OICORE (2026-11-03, run once, registration `workers/OEXIT1_REGISTRATION.md` commit 4d64d15)

**Verdict: DOES NOT SUPPORT (3x, and also 2x and 4x).** The exit changes almost nothing, as predicted: profit factor is slightly LOWER with it in both history halves and the longest losing run is the same. No change after registration. Code `src/scalper/oexit1.py`, tests `tests/test_oexit1.py` (pass), raw numbers `workers/OEXIT1_result.json`. Parity first: the no-exit rule reproduces OICORE exactly (discovery n 222 PF 2.28, validation n 333 PF 1.85; the live-list model reproduces the recorded PnL to the cent, net +$25.03).

## History (Bitcoin 15 minute, OICORE fires, C = 10, fee 7% x C x p x (1-p) rounded up on each leg incl. the sale)
86 fire-dates 2026-08-06 to 2026-11-03: H1 08-06 to 09-04, H2 09-05 to 10-05 (history, 358 trades), HOLD 10-06 to 11-03 (236 trades, read once).

| set | rule | n | PF | win rate | longest losing run | P(10-loss run in 100) | half-sales | net $ |
|---|---|---|---|---|---|---|---|---|
| H1 | without | 151 | 2.564 | 30.5% | 19 | 0.559 | | 177.46 |
| H1 | 3x | 151 | 2.562 | 30.5% | 19 | 0.559 | 23 | 177.18 |
| H1 | 2x / 4x | 151 | 2.561 / 2.562 | 30.5% | 19 / 19 | | 27 / 21 | 177.12 / 177.21 |
| H2 | without | 207 | 2.170 | 28.0% | 15 | 0.667 | | 201.31 |
| H2 | 3x | 207 | 2.168 | 28.0% | 15 | 0.667 | 26 | 200.92 |
| H2 | 2x / 4x | 207 | 2.167 / 2.169 | 28.0% | 15 / 15 | | 37 / 16 | 200.75 / 201.07 |
| HISTORY | without | 358 | 2.327 | 29.1% | 19 | 0.622 | | 378.77 |
| HISTORY | 3x | 358 | 2.325 | 29.1% | 19 | 0.622 | 49 | 378.10 |
| HISTORY | 2x / 4x | 358 | 2.324 / 2.325 | 29.1% | 19 / 19 | | 64 / 37 | 377.87 / 378.28 |
| HOLDOUT | without | 236 | 1.606 | 27.1% | 9 | 0.706 | | 143.35 |
| HOLDOUT | 3x | 236 | 1.605 | 27.1% | 9 | 0.706 | 24 | 142.99 |
| HOLDOUT | 2x / 4x | 236 | 1.604 / 1.605 | 27.1% | 9 / 9 | | 28 / 17 | 142.93 / 143.09 |

Trades converted: 0 losses turned into wins and 0 wins turned into losses in every set and variant. The exit costs 0.2 to 0.8 cents per trade in the sale fee (rounded up to a cent on each sale) and nothing else.

## Why (the structural point)
OICORE fills at the candle ending 120 s before the close. Only two candles follow: the one ending 60 s and the one ending at the close, whose bid is already a settled quote (about 0.99 for a winner). A 3x bid at 60 s is a winner about to settle, and the sale at the next candle lands at about 0.999, so selling half equals holding it minus a one cent fee. A loss cannot be converted because by the time the bid is at 3x the contract is almost settled. The "6c to 50c contracts that can reprice mid window" do reprice, but before the entry, not after it: the position lives for about two minutes. This is also why it differs from SLOTEX (that sold everything at 60 s and gave up the last minute of the win); here nothing is given up except fees. A test of a streak-cutting exit would need a longer hold (an earlier entry), which is a different strategy.

## Live list (18 filled of 24, `workers/OICORE_LIVE_ORDERS.csv`; the rule at the price paid and filled count; n = 18 is far too small to decide anything)
Without (model equals recorded): PF 3.23, win rate 27.8% (5 of 18), longest losing run 5, net +$25.03. With 3x: PF 3.23, win rate 27.8%, longest run 5, net +$24.99 (3 half-sales); 2x identical to 3x; 4x net +$25.00 (2 sales).

## Decision rule (as registered)
PF with higher than without in each history half: NO (H1 2.562 vs 2.564, H2 2.168 vs 2.170). Longest losing run shorter: NO (19 vs 19). **DOES NOT SUPPORT**; 2x and 4x the same. The holdout (read once, reported separately) agrees (1.605 vs 1.606, run 9 vs 9). Prediction check: PF change -0.002 (predicted -0.03 to 0.00), win rate unchanged, longest run unchanged: matched.

Tries: N +3 (2x, 3x, 4x), running count about 728,730 (z bar 5.27). Streak figures use `scalper.streaks` at each set's observed win rate (independence assumed; real losses cluster). Nothing here changes any order; no promote verb.
