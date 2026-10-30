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

## Holdout C (read once, after A and B were pushed)

| Variant | Games | Mean ask | Mean ESPN p | Win rate | Net C=1 | PF C=1 | PF C=10 | Net fees x1.2 | z |
|---|---|---|---|---|---|---|---|---|---|
| V1 all, 0.08 | 494 | 0.423 | 0.569 | 0.395 | -4.72c | 0.80 | 0.82 | -5.10c | -2.21 |
| V2 all, 0.15 | 446 | 0.404 | 0.608 | 0.419 | -0.37c | 0.98 | 1.00 | -0.74c | -0.16 |
| V3 football, 0.08 | 352 | 0.424 | 0.575 | 0.384 | -5.89c | 0.76 | 0.77 | -6.26c | -2.34 |
| V4 NBA+MLB, 0.08 | 142 | 0.421 | 0.553 | 0.423 | -1.84c | 0.92 | 0.94 | -2.23c | -0.46 |

Way B (volume-only candles) is within 0.4c of Way A in C (V2 Way B -0.04c, PF 1.00). All three windows, C=1, pooled: V1 1,422 games -2.16c PF 0.90 z -1.82; V2 1,232 games +0.53c PF 1.03 z +0.42; V3 883 games -3.72c PF 0.82 z -2.54; V4 539 games +0.39c PF 1.02 z +0.19. By league (V1, all windows): NFL 104 games -6.95c, college football 779 -3.29c, MLB 421 +0.55c, NBA 118 -0.19c.

## Summary table: PF per window (C=1 / C=10)

| Variant | A | B | C |
|---|---|---|---|
| V1 | 1.09 / 1.12 | 0.85 / 0.87 | 0.80 / 0.82 |
| V2 | 1.17 / 1.20 | 0.96 / 0.98 | 0.98 / 1.00 |
| V3 | 0.98 / 1.01 | 0.83 / 0.85 | 0.76 / 0.77 |
| V4 | 1.17 / 1.18 | 0.89 / 0.91 | 0.92 / 0.94 |

## Information (not a variant): calibration
Over every ESPN row with a valid Kalshi quote on the candle ending at least 60 s later (home side), the Brier score of Kalshi's mid beats ESPN's in NFL (0.187 vs 0.193, 17,192 rows), college football (0.157 vs 0.169, 114,060), NBA (0.186 vs 0.194, 51,354) and ties in MLB (0.1716 vs 0.1717, 27,990). The Kalshi quote here is a minute or more later than the play, so this flatters Kalshi a little; it still says Kalshi's in-play price is at least as good a forecast as ESPN's, which is the honest alternative.

## Verdict
**ESPN1: FALSIFIED (all 4 variants).** No variant reaches PF 1.5 in any window (best 1.20, V2 window A, C=10); every variant is at or below 1.00 in B and C; no pooled z is above +0.53 against a deflated bar of 5.17. Positive at fees x1.2 only in window A. The counterparty did not show up: when ESPN's probability beats Kalshi's ask by 8c or more, the side wins about as often as the ask says (V1: ask 0.40, won 0.40), not as often as ESPN says (0.55). The gaps are ESPN's error and lag; Kalshi's in-play quoters track something at least as good (most likely sportsbook lines).

Prediction check: FALSIFIED was right. The numeric range (PF 0.6 to 0.95 in every window) was too low for window A (0.98 to 1.17) and right for B and C.

Facts: ESPN lag median 45 s, p90 77 s (D = 180 s). Games 1,613 matched (NFL 107, college football 962, NBA 120, MLB 424); unit = game; one entry per game; NHL absent (ESPN publishes no NHL probability). Fees 7% x C x p x (1-p) rounded up per order, C = 1 and 10, x1.2 check. Zero-volume candles (14.3%) both ways; the verdict is the same either way. **N tried: 4; running count about 439,028.**
