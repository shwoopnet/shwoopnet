# INPLAY1: in-play cheap side priced by ESPN's win probability at fixed game-clock looks

Registered 2026-11-03 BEFORE any ESPN probability was joined to a Kalshi ask or any outcome was read for this test. Worker INPLAY1, session "Strategy Research V2". 1 rule. **N: +2.** Running count about 730,289 (coordinator keeps the total); z bar about 5.27.

## Duplicate check (done first)
- **SWING1** (2026-11-03): in-play price swing of 25c on the faller, cheap side, held. No ESPN probability used. Not this.
- **ESPN1** (FALSIFIED 4 of 4): ESPN win probability minus ask at every ESPN row, either side, gap of 8c or 15c, first signal per game, D = 180 s. Its calibration result (Kalshi mid has the better Brier than ESPN in NFL, college football, NBA; MLB ties) is the honest prior here. Not identical: INPLAY1 restricts to the cheap side (ask 3c to 30c), uses a RATIO trigger (p >= 3 x ask), and fixed game-clock looks. A subset of ESPN1's candidate space, but a different trigger, so it is a new (small) test, not a re-run.
- **BOOKS1** (NOT_ENOUGH_DATA, 0 treated trades): same ratio trigger with the DraftKings pre-game close; INPLAY1 swaps the outside reference for ESPN in-play probability. **BOOKS2, SPORTCONS1, SP1, FAMSPORTS, SPORTSPRE, CALIB1** (Sports 5-10c +1.81c [-2.14,+6.24], 186 events, not a lead): pre-game, totals, or arithmetic. Not this.
Verdict: not a duplicate of any single test; closest is ESPN1 plus BOOKS1. Expect a thin count.

## Counterparty and honest prior
Retail in-play flow that is slow or panicked on the trailing team. Honest prior: Kalshi's in-play mid already beats ESPN's probability (ESPN1 Brier), a 3x ratio on a cheap side is mostly ESPN model error, and cheap sides lose to the longshot bias (SWING1 control -4.5c, BOOKS1 control -5.7c). Prior of a pass 2%.

## Universe (metadata only)
`data/espn1.sqlite`, games with ESPN win-probability rows and Kalshi candles for both team tickers, ESPN start time before the frozen cut **2026-10-03T16:00Z**: college football (KXNCAAFGAME) 525 games, MLB (KXMLBGAME) 395. NFL (50 before the cut) and NBA (0) are excluded (under 150). Games starting from the cut are never read. Windows: W1 start before 2026-09-13T01:00Z, W2 after (as SWING1).

## Rule (one, no variants)
Looks L = start + 60, +90, +120 minutes (candle end time). At a look, the ESPN probability of team X is the last row with wall_ts <= L minus 180 s (D = 180 s, carried from ESPN1's measured lag; team probability: home = home_p, away = 1 - home_p - tie_p); X's quote is the candle ending exactly at L, valid if 0 <= bid < ask <= 1 and ask - bid <= 0.10, and the entry fill is that candle's ask plus nothing (one-minute latency is covered by D). **Trade:** buy X's YES at the ask if ask in [0.03, 0.30] (hard limit 0.30) and pE >= 3 x ask; hold to settlement; C = 10; **one per game** (earliest look, larger ratio if both teams, which cannot happen as the cheap side is unique). Fee 7% x C x p x (1-p) rounded up to the cent per order; fees x1.2 check. Net per contract = result - ask - fee/C.
**Control:** every cheap side (ask 3c to 30c, valid quote) at the same looks without the ratio condition, one per game and look averaged per game, matched on ask band (5 bands) and look.
**Information (not a rule):** Brier of pE against Kalshi mid on those cheap-side rows. Cheap side only: no favourite-side result is computed or printed.

## Numeric prediction
10 to 40 treated trades in W1+W2; if any, win rate at or below the mean ask, net -2c to -5c, PF 0.4 to 1.0. NOT_ENOUGH_DATA with probability about 85%; otherwise FALSIFIED.

## Kill rules
- FALSIFIED if mean net after fees is not above 0 in both halves (halves by date of the trades), or PF under 1.5, with 150 or more trades.
- NOT_ENOUGH_DATA under 150 trades in W1+W2: report trades per month of games and months to 150 (sports season changes), plus a forward freeze: the same rule scored from 2026-10-03T16:00Z on the games recorded since.
- A pass also needs day-clustered z at the deflated bar 5.27 and positive at fees x1.2. No retuning of 3x, 3c to 30c, looks or leagues after any result. Frozen W3 not opened.

Code `src/scalper/inplay1.py`, tests `tests/test_inplay1.py` (synthetic), result `workers/INPLAY1_RESULT.md`, `data/inplay1_result.txt`. No network calls; no live code; no promote verb.
