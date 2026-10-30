# ESPN1 result: ESPN in-play win probability against Kalshi game-winner asks

Registration: `ESPN1_REGISTRATION.md` (pushed before any Kalshi price was read). Check: `ESPN1_CHECK.md`. Code: `kalshi-scalper/src/scalper/espn1.py`. Data (ignored by git): `data/espn1.sqlite`.

## ESPN lag (measured live, fixed before scoring, 2026-10-30 01:00 UTC)
ESPN's probability rows carry no publication time, only the play's `wallclock`. A poller read the live summaries of 5 games on 2026-10-29/30 (2 college football from 23:30Z, NBA from 00:00Z, NFL from 00:15Z), cycling about every 15 to 25 s, and logged when each new row first appeared (rows already present at a game's first poll excluded).

| League | Rows | Median lag | p90 | Max |
|---|---|---|---|---|
| College football | 156 | 48 s | 64 s | 261 s |
| NBA | 252 | 40 s | 85 s | 368 s |
| NFL | 42 | 51 s | 62 s | 64 s |
| All | 450 | **45 s** | **77 s** | 368 s (p99 259 s) |

The lag includes up to one poll cycle, so it overstates the true lag by roughly 10 s. p90 77 s is above 60 s, so by the registered formula **D = 180 s** (p90 rounded up to the next minute, plus 60 s): the entry candle must end at least 180 s after the play's wallclock. Revisions: 6 of 445 rows (1.3%) differ by more than 0.01 between the value seen live and the stored value read at 01:00Z, so the stored history is close to what a live reader saw.

## Data
1,635 Kalshi events in the window; 1,623 matched to ESPN games by date and team names (12 college football events unmatched, 2 ESPN games matched twice and dropped); 1,613 games with ESPN rows and Kalshi candles: NFL 107, college football 962, NBA 120, MLB 424. 262,386 ESPN rows with a wallclock. 625,159 one minute candles, 14.3% with zero volume. Windows by game date (thirds by count): **A** to 2026-09-16 (540 games), **B** 2026-09-17 to 10-04 (554), **C** from 10-05 (519, holdout). All NBA games fall in C (the season began in October), so V4 in A and B is MLB only.

## Windows A and B (written before C was read)
Net per contract after fees, one entry per game, held to settlement. Way A = any candle with a valid quote; Way B = candles with volume only (results within 0.1c of Way A everywhere, shown for Way A unless worse).

| Variant | Window | Games | Mean ask | Mean ESPN p | Win rate | Net C=1 | PF C=1 | PF C=10 | Net fees x1.2 (C=1) | z |
|---|---|---|---|---|---|---|---|---|---|---|
| V1 all, 0.08 | A | 444 | 0.385 | 0.529 | 0.421 | +1.75c | 1.09 | 1.12 | +1.39c | +0.85 |
| V1 | B | 484 | 0.395 | 0.551 | 0.382 | -3.14c | 0.85 | 0.87 | -3.50c | -1.59 |
| V2 all, 0.15 | A | 379 | 0.342 | 0.554 | 0.391 | +3.04c | 1.17 | 1.20 | +2.68c | +1.37 |
| V2 | B | 407 | 0.344 | 0.569 | 0.354 | -0.82c | 0.96 | 0.98 | -1.18c | -0.38 |
| V3 football, 0.08 | A | 204 | 0.344 | 0.510 | 0.358 | -0.31c | 0.98 | 1.01 | -0.64c | -0.12 |
| V3 | B | 327 | 0.390 | 0.562 | 0.373 | -3.51c | 0.83 | 0.85 | -3.87c | -1.48 |
| V4 NBA+MLB, 0.08 | A | 240 | 0.420 | 0.545 | 0.475 | +3.50c | 1.17 | 1.18 | +3.11c | +1.13 |
| V4 | B | 157 | 0.406 | 0.529 | 0.401 | -2.36c | 0.89 | 0.91 | -2.74c | -0.67 |

Pooled A+B (C=1): V1 -0.80c PF 0.96 z -0.56 (928 games); V2 +1.04c PF 1.06 z +0.67 (786); V3 -2.28c PF 0.88 z -1.29 (531); V4 +1.19c PF 1.06 z +0.51 (397). By league (V1, A+B): NFL 60 games -8.97c, college football 471 -1.43c, MLB 397 +1.19c.

**No variant reaches PF 1.5 in either window; the best is 1.20 (V2, window A, C=10), and every variant is below 1.0 in window B. No z is near the deflated bar of 5.17. All four fail the bar on A and B.**

The reading: when ESPN's number beats the ask by 8c or more, ESPN is the one that is wrong. On V1 ESPN said 0.53 to 0.55 on the side bought; the side won 0.38 to 0.42 of the time, close to the 0.39 ask. The gap is ESPN's model error (and its 45 s lag), not slow Kalshi quotes.
