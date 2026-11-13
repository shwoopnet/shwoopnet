# ENDNET second build: hand-worked expected output on the invented rows (Testing Desk, Nov 13, 2026). Written BEFORE the scorer exists and before any run. All made up.
Text built from: LIVEDATA_CARDS_NOV13.md (card 1 and the "three readings pinned" lines, claude/idea-desk-b aca441ae, sha256 b7083dad61e9c269...). Not read: endnet.py. Cents; fee = 0.07 x p x (1 - p) of the price paid, rounded UP to the next cent; YES wins if the final total is above the strike; void = price refunded, fee kept.
Rule as I read it: entry minute = the FIRST third-period minute whose clock left is 180 s or less and whose score is exactly one goal apart; strike = the one with 0 <= f - total < 1; quote = the candle ending at that minute, two-sided (0 < bid < ask < 100); entry = YES at ask + 1c if the ask is 15 to 45c (inclusive) and spread (ask - bid) is 4c or less (inclusive); no other minute is tried or carried.

| game | entry minute | total | strike | quote (bid/ask) | outcome |
|---|---|---|---|---|---|
| G01 | index 7 (left 180) | 5 | 5.5 | 30/34 | ENTER at 35c, fee 2c, final total 6 > 5.5: win, net +63 |
| G02 | index 8 (left 120; tied at 180) | 7 | 7.5 | 18/20 | ENTER at 21c, fee 2c, final 7 not above 7.5: loss, net -23 |
| G03 | none (two goals apart throughout) | | | | no state |
| G04 | index 7 (left 180, 1-0) | 1 | 1.5 | no candle at that minute (later minutes have quotes, not used) | state, NOT entered: no usable quote |
| G05 | index 7 | 3 | 3.5 | 0/40 | state, NOT entered: not two-sided |
| G06 | index 7 | 3 | 3.5 | 44/46 | state, quote seen, NOT entered: ask 46 above the band |
| G07 | index 7 | 5 | 5.0 (f - total = 0) | 12/15 | ENTER at 16c, fee 1c, final 6 > 5.0: win, net +83 |
| G08 | index 7 | 3 | 3.5 | 41/45 | ENTER at 46c, fee 2c, final 3: loss, net -48 |
| G09 | index 7 | 3 | 3.5 | 30/35 | state, quote seen, NOT entered: spread 5c |
| G10 | index 7 | 3 | none (2.5 gives -0.5, 4.5 gives 1.5) | | state, NOT entered: no strike fits |
| G11 | none (one goal apart but every minute is period 2) | | | | no state |
| G12 | index 7 | 3 | 3.5 | 26/28 | ENTER at 29c, fee 2c, result void: net -2 (fee kept) |
| G13 | index 7 | 3 | 3.5 | no candle at index 7 (one at index 6, left 240: not used) | state, NOT entered: no usable quote |
| G14 | index 8 (left 121; at left 181 not yet) | 5 | 5.5 | 25/29 | ENTER at 30c, fee 2c, final 6 > 5.5: win, net +68 |

## Counts first (stage 1, development window)
- games 14; games with a qualifying state 12 (G03 and G11 have none); entries made 6 (G01, G02, G07, G08, G12, G14); states not entered 6 (G04, G05, G06, G09, G10, G13): no usable quote 2 (G04, G13), one-sided quote 1 (G05), ask above the band 1 (G06), spread above 4c 1 (G09), no strike 1 (G10).
- Median ask of the 6 entries (ask before the +1c): asks 15, 20, 28, 29, 34, 45: median 28.5c. Median ask over every state that had a two-sided quote at the entry minute with a strike (before the band and spread filters): asks 15, 20, 28, 29, 34, 35, 45, 46 (G07, G02, G12, G14, G01, G09, G08, G06): median 31.5c. Neither is above 45c.
- Entries by close date (UTC): Nov 18: 2, Nov 19: 1, Nov 22: 1, Nov 24: 1, Nov 26: 1. By week (Monday to Sunday, UTC close date): week of Nov 16: 4, week of Nov 23: 2. Fewer than 6 in every week.
- STAGE 1 VERDICT (card text): CLOSED: fewer than 6 qualifying entries a week (4 and 2). Median ask not above 45c.

## Stage 2 on the same rows (development only; one entry a game; every entry counted filled at ask + 1c)
- n = 6 filled; wins 3 (63 + 83 + 68 = 214 c), losses 3 (23 + 48 + 2 = 73 c, the void a fee-only loss counted in n and PF); net +141c, +23.5c a contract; cash PF 214 / 73 = 2.9315.
- Halves by close time then game id (first 3 and last 3): first G01, G02, G07: 146 / 23 = 6.3478; second G08, G12, G14: 68 / 50 = 1.3600.
- Verdict: NOT_ENOUGH_DATA at n = 6 (150 filled needed).
## Held-out
- A run on outside.json (a game closing 2026-12-16, on or after the held-out start 2026-12-15) is REFUSED before any state is read.
