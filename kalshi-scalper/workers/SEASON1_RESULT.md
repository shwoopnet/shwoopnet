# SEASON1 result (run once 2026-11-06): NOT_ENOUGH_DATA (partial fetch, rate limited), control sign negative

Registered 2026-11-05 (`workers/SEASON1_REGISTRATION.md`, commit 79f34a4) before any candle or result. Scorer `src/scalper/season1.py`, series list `workers/SEASON1_series.txt`, raw rows `workers/SEASON1_RAW.jsonl`, scorer output `workers/SEASON1_RAW_score.json`. Nothing after the frozen cut 2026-10-03T16:00Z was read.

## Numbers
- Census (listings only): 65 series (32 NFL teams, 30 MLB teams, KXNBAWINS), 302 event tickers, 1,597 settled markets, but only about 93 independent team-seasons (NFL 6 event tickers per team-season, one season of history). Below the registered 100 independent events.
- Fetch: Kalshi's public API rate limited the job twice (about 4 candle reads in 500 seconds on the last try), so it was stopped, not looped. Fetched 490 of 1,597 markets (NFL 433 from 17 teams, MLB 57 from 3 teams, NBA 0), 288 with a valid two-sided hourly quote at the look (14 days before close NFL, 21 MLB/NBA), 113 cheap (ask 3c to 30c), 55 picked (cap 3 per event by sha1), 23 events, 20 team-seasons.
- CONTROL (all picked cheap YES rungs, held, fee 7% x C x p x (1-p) rounded up, C=10, taker at the ask): n 55, wins 0, mean ask 7.89c, net -13.25c per contract (team-season bootstrap [-15.98, -10.93]), PF 0.00, fees x1.2 -14.33c. Halves D1 -10.56c (n 27), D2 -15.86c (n 28). NFL -13.48c (n 50), MLB -11.00c (n 5).
- TREATED arm (standings calculator probability >= 3x ask): NOT RUN. It needs a standings join (ESPN records by date) that was not built after the fetch stalled; 0 treated trades.

## Read
Every cheap rung that was scored lost (0 of 55), the same sign as the rest of the cheap-side record, but 20 team-seasons of one league season is nothing to conclude from. NOT_ENOUGH_DATA by the registered rule (under 100 independent events, under 150 treated); no lead. Early closing is worth noting: each strike closes the moment the standings decide it, so a fixed 14 to 21 day look keeps only still-undecided strikes.

## Accrual needed
About 100 independent team-seasons needs the NBA (31 a year), MLB (30) and NFL (32) seasons together, about 93 a year, so a full 2026-27 season of recorded ladders for 100 events, and 150 treated needs roughly 3 seasons at the expected 15 to 50 per season. Not worth a recorder. N +1 (running about 730,444), unchanged.
