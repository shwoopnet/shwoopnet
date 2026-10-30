# SPORTCONS1 result (2026-10-30)

Registered and pushed first (`workers/SPORTCONS1_REGISTRATION.md`, commit 6f2e49b), inventory in `workers/SPORTCONS1_INVENTORY.md`, code `src/scalper/sportcons1.py`, raw output `data/sportcons1_t1_result.txt` (local). Prices only; no settled result was read.

## Inventory in one paragraph
On file: R2 winner complement for 1,613 games (MLB 424, NBA 120, college football 962, NFL 107), 244,000 same-minute two-sided pair-minutes with both legs trading, median spread 1c, deep volume (median leg 282 to 18,878 contracts a minute by sport); R3 game total vs first-half total for 104 NFL games (only 16 with volume on both legs, 110 pair-minutes; NBA has no strike pair with K_game <= K_1H; no NHL first-half series). NOT on file: first-half winner, first-half spread, spread ladders (win by 5+/10+), winner vs spread. Those relations are NOT_RUNNABLE. The soft totals relation (1H over 25 vs game over 50) is not model-free and was not run.

## T1 strict locks (lock after rounded fees at C = 10, both legs at the asks, same minute, each leg at least 10 contracts)

| Relation | Window | Games | Games with lock > 0 | Games with lock >= 1c | Best lock |
|---|---|---|---|---|---|
| R2a YES+YES (no-tie sports) | discovery | 645 | 2 | 0 | +0.40c |
| | validation | 647 | 3 | 0 | +0.10c |
| | holdout | 321 | 1 | 0 | +0.20c |
| R2b NO+NO (all four) | discovery | 645 | 3 | 1 | +1.50c |
| | validation | 647 | 2 | 0 | +0.50c |
| | holdout | 321 | 0 | 0 | -0.20c |
| R3 game vs 1H total | discovery | 62 | 0 | 0 | -47.1c |
| | validation | 63 | 0 | 0 | -66.9c |
| | holdout | 95 | 0 | 0 | -56.1c |

Process note: the script printed all three windows at once, so the holdout was shown although the registration said it would be read only if discovery and validation passed. They did not pass, so the holdout decides nothing and shows the same picture (1 and 0 tiny locks).

What the positive minutes are: each is a single one-minute candle (11 positive minutes across 1,613 games and two directions, 244,000 pair-minutes), with no repeat, at tails (0.06 + 0.93, 0.03 + 0.98) or at 0.10c to 0.50c where the cent rounding of the fee, not the price, leaves a cent. The one +1.5c case is Weber State against Utah in the college football data on 2026-09-05, at 0.90 and 0.13 NO-side bids, in a minute volume of at least 10 on each leg; one minute, one game, not repeated in validation or holdout. None can be assumed fillable: candle quotes have no sizes and the quote is the minute's close, not the touch at an instant. Fees x1.2 was not run on these because none met the bar. Duration: single minutes only (no persistence beyond one candle in any example).

## Verdicts
- R2a winner YES+YES: **FALSIFIED** (0 games with a lock of at least 1c in every window).
- R2b winner NO+NO: **FALSIFIED** (1 game in discovery, 0 in validation; bar was 3 in each).
- R3 game total vs first-half total: **NOT_ENOUGH_DATA** (62 to 95 games per window with usable pairs, under the 100 required, and not a single positive lock; the K_game <= K_1H pairs are degenerate in-the-money against out-of-the-money quotes).
- First-half winner, spread ladder, winner vs spread: **NOT_RUNNABLE** (no data on file).
- T2 soft consistency: **not run**, as registered (T1 had no non-trivial count). No settled result was read. It costs no try.

Prediction check: predicted zero locks of at least 1c and best between -1.5c and -0.2c. Zero of at least 1c held in 8 of 9 cells (one +1.5c minute in R2b discovery); "best below -0.2c" was wrong for R2a/R2b, which show tiny positive flickers up to +1.5c. Direction right, size of the best slightly wrong.

N: 3 tries (R2a, R2b, R3). Running count 592,082 + 3 = about 592,085.

## Proposed README section (for the lead to merge)

## Result: SPORTCONS1 (sports consistency locks, winner complement and game vs first-half totals), 2026-10-30

Registered first (`workers/SPORTCONS1_REGISTRATION.md`), result `workers/SPORTCONS1_RESULT.md`, code `src/scalper/sportcons1.py`. Owner-approved family (KX10 item 9). Not repeated: favourites (SP1, F6), totals ladder locks (ARB5), maker quotes (MAKER1), ESPN lag (ESPN1). On file: winner complement for 1,613 games (MLB, NBA, college football, NFL; 1c spreads) and game against first-half totals for NFL only (NBA has no K_game <= K_1H pair; 16 NFL games trade on both legs). Not on file: first-half winner or spread, spread ladders (NOT_RUNNABLE). Buying both teams' YES or both NO at the asks, both legs trading at least 10 contracts the same minute, after rounded fees at 10 contracts: games with a lock of at least 1c were 0 / 0 / 0 for YES+YES and 1 / 0 / 0 for NO+NO (bar 3 per window); the few positive minutes (up to +1.5c) are single one-minute candles at price tails or fee rounding. R2a and R2b **FALSIFIED**; R3 **NOT_ENOUGH_DATA** (62 to 95 games, no positive lock); T2 not run. Quoters keep the two team markets and the totals pair inside the arithmetic at minute resolution. N +3; running count about 592,085.
