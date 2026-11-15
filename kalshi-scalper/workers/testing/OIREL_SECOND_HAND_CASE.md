# OIREL haircut recompute, BUILD 2: hand case (Testing Desk, Nov 15, 2026). Written BEFORE any code.
Sources, read for the rule only: research branch claude/epic-ptolemy-0amjd9 `src/scalper/oirel.py` (docstring and decide()) and `workers/FALS5_RESULT.md` check 2 (the card); rnd-queue RND_QUEUE.md sections 2026-11-13 21:47Z (C1 to C6), 21:49Z (C7 to C10), 2026-11-14 02:30Z (C11: not an NC15 series, so 1c is primary); Desk A's input list (extract claude/forensics-desk 31351c1b `OIREL_extract.sqlite.xz` sha256 53f2f8c32b829bc39ce2c647898926eef4a8a3f1fa2ca804895a0a36e6322250, spec and cut log beside it; split 1789948800). I wrote the invented windows and the arithmetic below myself; I did not copy Desk A's windows or figures (their hand case was read as a spec of the haircut, and the figures in my table are my own).
## What I build: `oirel_second.py <extract.sqlite> <split_ts>`
Reads only the extract (tables market(ticker, series, open_ts, close_ts, result, strike, src), candle(ticker, end_ts, bid_c, ask_c, volume, oi)); writes nothing; prints aggregates only. Every candle with end_ts after its market's close is dropped before anything is read and counted. Windows: markets of series KXBTC15M.
Rule: back = candle ending exactly close - 360; signal = candle ending close - 180; fill = candle ending close - 120. NoData (counted, never a no-trade): a missing back or signal candle, or an open interest of 0 or missing at either, or a back oi of 0 or less. doi = oi(signal) - oi(back); FIRES when doi / oi(back) > 0.26764675317954373 (strict). A window that does not fire is "no fire". Two-sided check (C1): the signal candle needs 0 < bid < ask < 1 to pick a side, else "not two-sided" (no trade). Side: YES if its ask (yes ask close) is in [0.05, 0.50], else NO if 1 - yes bid close is in [0.05, 0.50], else "no side" (no trade). The fill candle: missing, or either quote missing: NoData; not two-sided (0 < bid < ask < 1 fails): "not two-sided" (no trade). Entry price p = (that side's ask on the fill candle) + h, h in {0, 0.01, 0.02}, never past 0.99 (min(p, 0.99)); a raw ask not in (0, 1) is no trade. 10 contracts. fee = ceil(0.07 x 10 x p x (1 - p) x 100 - 1e-9) / 100 per order, at the price p of that haircut. cash = 10 x (win - p) - fee with win = 1 if the result equals the side else 0; a void (result not yes or no, e.g. void) refunds the price and keeps the fee: cash = -fee, counted and printed. PF = sum of positive cash over the absolute sum of negative cash (infinite when no negative). Halves: floor(n/2) by fill order (fill time = close - 120, ties by ticker). Discovery = trades with close_ts before the split argument, validation = the rest. A line COUNTS toward the 20 to 30 only if cash PF at 1c >= 1.3 - 1e-9 with both halves >= 1.0 - 1e-9 AND cash PF at 2c >= 1.0 - 1e-9 (C7); 1c is primary (C8, C11 do not apply to this series; the signal and fill are 3 and 2 minutes before the close; the fill candle ends 120 s before the close, i.e. in the last 2 minutes, C8 says 2c is primary: MY READING, to confirm: print 1c, 2c and 0c, and call 2c the primary haircut because the entry is at 120 s). Every line says "upper bound, not fill-checked" and "fee mode per-order rounded".
## Invented windows (close_ts = 1000000 + 900 k; oi back / signal; b/a = yes bid / yes ask close)
| W | k | oi back | oi signal | signal b/a | fill b/a | result | expected |
|---|---|---|---|---|---|---|---|
| A | 1 | 2000 | 2535 | 0.20/0.22 | 0.20/0.22 | yes | 535/2000 = 0.2675 < 0.267646...: no fire |
| B | 2 | 2000 | 2536 | 0.09/0.11 | 0.09/0.10 | yes | 0.268 fires; YES; p 0.10, 0.11, 0.12 |
| C | 3 | 1000 | 1300 | 0.55/0.57 | 0.52/0.54 | no | YES ask 0.57 out; NO ask 0.45 in: NO; fill NO ask 0.48: p 0.48, 0.49, 0.50 |
| D | 4 | 1000 | 1300 | 0.20/0.22 | 0.24/0.25 | no | YES; p 0.25, 0.26, 0.27; loss |
| E | 5 | (no candle) | 1300 | 0.20/0.22 | 0.24/0.25 | yes | NoData |
| F | 6 | 0 | 1300 | 0.20/0.22 | 0.24/0.25 | yes | NoData (back oi 0) |
| G | 7 | 1000 | 1300 | 0.48/0.52 | 0.48/0.52 | yes | fires; both asks 0.52: no side |
| H | 8 | 1000 | 1300 | (bid missing)/0.30 | 0.24/0.25 | yes | fires; signal not two-sided: no trade |
| I | 9 | 1000 | 1300 | 0.39/0.41 | (no candle) | yes | fires; YES; fill candle missing: NoData |
| J | 10 | 1000 | 1300 | 0.09/0.11 | 0.96/0.98 | yes | YES; p 0.98, 0.99, 0.99 (never past 0.99); win |
| L | 11 | 1000 | 1300 | 0.09/0.11 | 0.19/0.20 | void | YES; p 0.20, 0.21, 0.22; void: cash = -fee |
Extra candles: W B has a candle ending at close + 60 (oi 9999, bid 0.98, ask 0.99) and W C one ending at close + 900: both dropped (2 dropped).
## Expected, by hand (fee = ceil(70 p (1 - p) - 1e-9) / 100)
| W | h 0: p, fee, cash | 1c: p, fee, cash | 2c: p, fee, cash |
|---|---|---|---|
| B | 0.10: 70 x 0.09 = 6.3 -> 7 -> 0.07; 10 x 0.90 - 0.07 = +8.93 | 0.11: 6.853 -> 7 -> 0.07; 8.90 - 0.07 = +8.83 | 0.12: 7.392 -> 8 -> 0.08; 8.80 - 0.08 = +8.72 |
| C | 0.48: 17.472 -> 18 -> 0.18; 5.20 - 0.18 = +5.02 | 0.49: 17.493 -> 18 -> 0.18; 5.10 - 0.18 = +4.92 | 0.50: 17.5 -> 18 -> 0.18; 5.00 - 0.18 = +4.82 |
| D | 0.25: 13.125 -> 14 -> 0.14; -2.50 - 0.14 = -2.64 | 0.26: 13.468 -> 14 -> 0.14; -2.60 - 0.14 = -2.74 | 0.27: 13.797 -> 14 -> 0.14; -2.70 - 0.14 = -2.84 |
| J | 0.98: 1.372 -> 2 -> 0.02; 0.20 - 0.02 = +0.18 | 0.99: 0.693 -> 1 -> 0.01; 0.10 - 0.01 = +0.09 | 0.99 (capped): +0.09 |
| L | 0.20: 11.2 -> 12 -> 0.12; cash -0.12 | 0.21: 11.613 -> 12 -> 0.12; -0.12 | 0.22: 12.012 -> 13 -> 0.13; -0.13 |
Windows 11: trades 5 (B, C, D, J, L; wins 3, losses 1, void 1), NoData 3 (E, F, I), no fire 1 (A), no side 1 (G), not two-sided 1 (H); 5 + 3 + 1 + 1 + 1 = 11.
Totals: h 0: positives 8.93 + 5.02 + 0.18 = 14.13; negatives 2.64 + 0.12 = 2.76; net +11.37; PF 14.13 / 2.76 = 5.119565. 1c: 8.83 + 4.92 + 0.09 = 13.84; 2.74 + 0.12 = 2.86; net +10.98; PF 4.839161. 2c: 8.72 + 4.82 + 0.09 = 13.63; 2.84 + 0.13 = 2.97; net +10.66; PF 4.589226.
Halves (n 5, floor(5/2) = 2 by fill order B, C, D, J, L): first half B, C: no negative: PF infinite; net 0c +13.95, 1c +13.75, 2c +13.54. Second half D, J, L: 0c: positives 0.18, negatives 2.64 + 0.12 = 2.76: PF 0.065217, net -2.58; 1c: 0.09 / 2.86 = 0.031469, net -2.77; 2c: 0.09 / 2.97 = 0.030303, net -2.88.
Discovery (split just after D's close): B, C, D: 0c positives 13.95, negatives 2.64: PF 5.284091, net +11.31; 1c 13.75 / 2.74 = 5.018248, +11.01; 2c 13.54 / 2.84 = 4.767606, +10.70. Validation J, L: 0c 0.18 / 0.12 = 1.5, net +0.06; 1c 0.09 / 0.12 = 0.75, -0.03; 2c 0.09 / 0.13 = 0.692308, -0.04.
COUNTS toward the 20 to 30: NO (the second half is under 1.0 at every haircut).
## Further hand cases
- Strictness: oi 2000 to 2535 does not fire, 2000 to 2536 fires; a window whose doi / back is exactly the threshold is not constructible in whole contracts, so the unit test also checks the comparison with the threshold itself as a float (`doi/back > RTHR` false when equal).
- A candle ending exactly at the close is kept; one ending 1 s after is dropped.
- Fee ceiling guard: a p whose 70 p (1 - p) is within 1e-9 above an integer rounds DOWN to that integer (the -1e-9).
- With every window NoData or no fire the printed n is 0, PF n/a, label "no evidence at n = 0"; fewer than 100 settled trades prints "n = x" beside the figures (this is a descriptive recompute of a closed history; the bar is C7).
- A series other than KXBTC15M in the extract is ignored (counted).
- The printout names the extract's sha256 (the raw file bytes of the .sqlite given), the split and every count; no ticker is printed.
