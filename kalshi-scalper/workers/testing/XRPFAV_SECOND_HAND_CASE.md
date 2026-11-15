# XRPFAV6 and XRPFAV10 haircut recompute, BUILD 2: hand case (Testing Desk, Nov 15, 2026). Written BEFORE any code.
Sources, read for the rule only: research branch claude/epic-ptolemy-0amjd9 `src/scalper/regime_b2.py` (rows XRPFAV6 and XRPFAV10; README:9192); Desk A's input list (extract claude/forensics-desk 31351c1b `XRPFAV_extract.sqlite.xz` sha256 be6bc75f080843492989fb18ca08d2836ceb4465d7af520677cf11075bca7f13, closes before 2026-10-03; spec and cut log beside it; Desk A's hand case sha256 736d6c69... was read as the statement of the haircut, my windows and figures below are my own); rnd-queue C1 to C10 (C11 does not apply: not an NC15 series).
## What I build: `xrpfav_second.py <extract.sqlite> <XRPFAV6|XRPFAV10>`
Reads only the extract (market(ticker, series, open_ts, close_ts, result, strike, src), candle(ticker, end_ts, bid_c, ask_c, volume, oi)); prints aggregates only (no ticker), writes nothing. Every candle ending after its market's close is dropped and counted. Series KXXRP15M (others ignored, counted); a market whose result is not yes or no is excluded and counted.
Rule (card): pick = the LAST candle (by end time) whose time left (close - end_ts) is in [left_lo, left_hi]: XRPFAV6 [330, 400] (rule maxspread 0.02), XRPFAV10 [570, 640] (no spread limit). No candle in range: skip (no candle). The picked candle: bid or ask missing, bid <= 0, ask >= 1 or ask <= bid: skip (bad quote). XRPFAV6: spread (ask - bid) over 0.02 skips (MY READING: with 1e-9 slack, so a spread of exactly 0.02 passes; the card compares raw floats and 0.91 - 0.89 prints 0.020000000000000018, which the raw card would skip: to confirm with Desk A). Favourite side: YES if the YES ask >= the NO ask (1 - bid, rounded to 6 places), else NO; p = that side's ask; band 0.88 <= p <= 0.92 inclusive (1e-9 slack; MY READING for the same float reason); outside: skip (band). Hold to settlement; 10 contracts. Haircut (C1 to C10): price = min(round(p + h, 6), 0.99), h in {0, 0.01, 0.02}; fee_up_order = ceil(0.07 x 10 x price x (1 - price) x 100 - 1e-9) / 100 per order; cash = 10 x (win - price) - fee. PF = sum of positive cash over the absolute sum of negative cash (infinite with no loss, n/a with no win). Halves floor(n/2) by close time (ties by ticker). The entry candle is 330 to 640 s before the close, not in the last 2 minutes, so 1c is primary (C8) and 2c is printed beside it; a line COUNTS only at 1c PF >= 1.3 with both halves >= 1.0 and 2c PF >= 1.0 (C7, 1e-9 slack). Every line: "upper bound, not fill-checked; fee mode per-order rounded".
## Invented windows (close = 2000000 + 900 k; the quote is on the candle(s) named; b/a = YES bid / YES ask close)
| W | k | candles | result | XRPFAV6 | XRPFAV10 |
|---|---|---|---|---|---|
| 1 | 1 | C-360 and C-600: 0.90 / 0.91 | yes | YES p 0.91 win | same |
| 2 | 2 | both: 0.07 / 0.09 (NO ask 0.93) | yes | skip (band) | skip (band) |
| 3 | 3 | both: 0.08 / 0.09 (NO ask 0.92, inclusive) | yes | NO p 0.92 loss | same |
| 4 | 4 | both: 0.87 / 0.88 (YES ask 0.88, inclusive) | yes | YES p 0.88 win | same |
| 5 | 5 | both: 0.87 / 0.90 (spread 0.03) | no | skip (spread) | YES p 0.90 loss |
| 6 | 6 | one candle at C-480 | yes | skip (no candle) | skip (no candle) |
| 7 | 7 | C-400: 0.89 / 0.90 and C-360: 0.50 / 0.51; C-640: 0.89 / 0.90 and C-570: 0.50 / 0.51 | yes | last in range = C-360: p 0.51: skip (band) | last in range = C-570: skip (band) |
| 8 | 8 | both: bid 0.00 / ask 0.91 | yes | skip (bad quote) | skip (bad quote) |
| 9 | 9 | both: bid 0.90 / ask missing | yes | skip (bad quote) | skip (bad quote) |
| 10 | 10 | both: 0.90 / 0.91 | void | excluded (no yes or no result) | excluded |
| 11 | 11 | both: 0.89 / 0.91 (spread exactly 0.02) | yes | YES p 0.91 win | YES p 0.91 win |
## Expected, by hand (fee = ceil(70 price (1 - price) - 1e-9) / 100)
| trade | h 0: price, fee, cash | 1c | 2c |
|---|---|---|---|
| W1 and W11 (win, p 0.91) | 0.91: 5.733 -> 6 -> 0.06; 0.90 - 0.06 = +0.84 | 0.92: 5.152 -> 6 -> 0.06; 0.80 - 0.06 = +0.74 | 0.93: 4.557 -> 5 -> 0.05; 0.70 - 0.05 = +0.65 |
| W3 (loss, p 0.92) | 0.92, fee 0.06: -9.20 - 0.06 = -9.26 | 0.93, fee 0.05: -9.35 | 0.94: 3.948 -> 4 -> 0.04: -9.40 - 0.04 = -9.44 |
| W4 (win, p 0.88) | 0.88: 7.392 -> 8 -> 0.08; 1.20 - 0.08 = +1.12 | 0.89: 6.853 -> 7 -> 0.07; 1.10 - 0.07 = +1.03 | 0.90: 6.3 -> 7 -> 0.07; 1.00 - 0.07 = +0.93 |
| W5 (XRPFAV10 only, loss, p 0.90) | 0.90, fee 0.07: -9.00 - 0.07 = -9.07 | 0.91, fee 0.06: -9.16 | 0.92, fee 0.06: -9.26 |
**XRPFAV6:** trades W1, W3, W4, W11 (n 4, wins 3, loss 1). h 0: positives 0.84 + 1.12 + 0.84 = 2.80, negatives 9.26, net -6.46, PF 0.302376; 1c: 0.74 + 1.03 + 0.74 = 2.51, 9.35, net -6.84, PF 0.268449; 2c: 0.65 + 0.93 + 0.65 = 2.23, 9.44, net -7.21, PF 0.236229. Halves floor(4/2) = 2: first W1, W3: 0c 0.84 / 9.26 = 0.090713, 1c 0.74 / 9.35 = 0.079144, 2c 0.65 / 9.44 = 0.068856; second W4, W11 (no loss): infinite. Counts: skip band 2 (W2, W7), skip spread 1 (W5), skip no candle 1 (W6), skip bad quote 2 (W8, W9), excluded result 1 (W10); 4 + 2 + 1 + 1 + 2 + 1 = 11 windows.
**XRPFAV10:** trades W1, W3, W4, W5, W11 (n 5, wins 3, losses 2). h 0: positives 2.80, negatives 9.26 + 9.07 = 18.33, net -15.53, PF 0.152755; 1c: 2.51, 9.35 + 9.16 = 18.51, net -16.00, PF 0.135603; 2c: 2.23, 9.44 + 9.26 = 18.70, net -16.47, PF 0.119251. Halves floor(5/2) = 2: first W1, W3 (same as XRPFAV6's first half); second W4, W5, W11: 0c positives 1.12 + 0.84 = 1.96, negatives 9.07, PF 0.216098; 1c 1.77 / 9.16 = 0.193231; 2c 1.58 / 9.26 = 0.170626. Counts: skip band 2 (W2, W7), skip no candle 1 (W6), skip bad quote 2, excluded result 1; 5 + 2 + 1 + 2 + 1 = 11.
COUNTS: no, for both (every PF is under 1).
## Further hand cases
- The pick is the LAST candle by end time in the range (W7), not the first and not the nearest to the middle.
- Range edges inclusive: a candle with 400 s left (XRPFAV6) or 330 s, 570 s, 640 s (XRPFAV10) is in range; 401 or 329 is not.
- A candle ending 1 s after the close is dropped and counted; a candle ending exactly at the close is kept (and is never in range).
- Price cap: raw p 0.92 plus 2c never exceeds 0.94, so the 0.99 cap is checked by a unit test on the price function (0.98 + 0.02 -> 0.99).
- Empty extract or no trade: n 0, PF n/a, no crash; the printout carries the extract's raw sha256, the rule id and every count, and no ticker.
