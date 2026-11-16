# PREDRIFT1: follow the pre-game drift (History Miner, written Nov 16, 2026 ~15:35Z, before any read; the Head's 15:21Z steer)

Shape: the game or total price drifts in the 6 hours before tip; buy in the direction of the drift 1 hour before tip and hold.
Counterparty and prediction: late informed money (injury and lineup news, sharp bettors) moves a pre-game line and the move is not complete an hour before tip; recreational flow on the other side. Prediction: PF at 2c >= 1.3. Kill: PF at 2c under 1.0. Not lead-lag (one market's own past); not favourite-and-hold (entries 20c to 80c); differs from IGUNDER1, IGFADE1, IGTOTDOG1 (pre-game, own-drift trigger, no live time).

Data, holds and thirds exactly as INGAME_CARDS_NOV15.md Amendments 1 and 2 and Auditor B's NHL line (Nov 16, 15:19Z): recorder rows before 2026-11-13T00:00Z; results from IG_RESULTS and IG_RESULTS_NHL (closes 1794096000 to 1794527999), one combined folder. Markets: NBA, NFL and NHL totals, and NHL moneylines (NBA and NFL moneylines are held by SPORTS-PRE). Thirds by close: t1 before 1794355200, t2 to 1794528000.

Rule (built for the recorder's real ~2 minute gaps):
- Tip time = the listing's occurrence_datetime minus 3 hours (a schedule field, known before the game; on the markets checked it sits about 3 h after the start). Never close_time or result.
- Marks M6 = tip - 6 h and M1 = tip - 1 h. Quote at a mark = the last row of that ticker with t <= mark and t > mark - 10 min, two-sided; none: no trade.
- Drift d = mid(M1) - mid(M6). Trade if |d| >= 0.04. d > 0: buy YES at the M1 row's yes_ask; d < 0: buy NO at 1 - yes_bid. Only if that ask is 0.20 to 0.80.
- One entry per game per kind: totals (the recorder keeps one totals ticker per game) and NHL moneyline (of the game's two team tickers, the one first in string order). Hold to settlement.
- Net as ingame1.net; h 0, 1c, 2c; primary 2c; c 1 and 10. Bar: n >= 100 over t1 and t2; PF 2c >= 1.3 pooled and >= 1.0 in t1 and t2. Under 100: "no evidence at n = x". One try.

Hand case (invented): tip 10:00. Rows at 03:55 (0.40, 0.42), 08:58 (0.47, 0.49): d = +0.07, buy YES at 0.49; win h 2c: entry 0.51, fee ceil(1.7493) = 0.02, net +0.47; loss -0.53. A row at 03:45 only for M6 (15 min before): no trade. d = +0.03: no trade. M1 row (0.85, 0.87), d > 0: ask 0.87 out of range, no trade. d < 0 with M1 row (0.30, 0.32): buy NO at 0.70.

## Amendment 1 (2026-11-16 ~15:45Z, the Head's look-ahead test, before any read)
A game is kept only if its listing markets carry ONE occurrence_datetime, on minute :00, :30 or :05 with 0 seconds; others are dropped and counted per league (schedule_test_dropped_games). Checked on schedule fields only (no result): NBA 38 and NHL 33 games all pass; NFL 6 of 14 fail (kickoffs at :15, :20, :25, which are real NFL kickoff minutes; applied strictly as asked, flagged to the Head).

## Amendment 2 (2026-11-16 ~15:55Z, the Head 15:24Z, before any read)
NFL only: minutes :15, :20 and :25 are also allowed (real NFL kickoff minutes); one value per game is still required. NBA and NHL unchanged (:00, :30, :05).
