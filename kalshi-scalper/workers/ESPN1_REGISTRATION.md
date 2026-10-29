# ESPN1 registration: ESPN in-play win probability against Kalshi game-winner asks
Written 2026-10-29 ~19:40 UTC, before any Kalshi price or candle for these markets was read, and before any ESPN probability was joined to a Kalshi quote. Research only. Worker ESPN1. See `ESPN1_CHECK.md` for why this is not a reword.

## Counterparty
Kalshi in-play quoters (market makers and takers re-quoting during play) who update slower than ESPN's per-play model, so a 8c+ gap between ESPN's probability and the ask is mispricing they pay for. **Honest alternative (expected):** quoters follow live sportsbook lines, which are faster and better than ESPN's model; a big gap is then ESPN's model error (or ESPN's lag), and buying it loses.

## Universe (time and data availability only)
Kalshi series `KXNFLGAME`, `KXNCAAFGAME`, `KXNBAGAME`, `KXMLBGAME`: every settled market whose close time is 2026-08-30 00:00 UTC to 2026-10-29 00:00 UTC (counts at registration: 108, 1,001, 123 and 431 events). `KXNHLGAME` is out because ESPN publishes no NHL win probability. Each Kalshi event is matched to one ESPN game of the same league by date (ticker date, plus or minus 1 day) and team names (Kalshi `yes_sub_title` against ESPN display name, short name, location, abbreviation); unmatched events and ESPN games without `winprobability` are counted and dropped.

## Data
- ESPN `site.api.espn.com/apis/site/v2/sports/{league}/summary?event={id}`: `winprobability` rows (homeWinPercentage, tiePercentage, playId) joined to the plays (`plays`, or `drives` for football) for each play's `wallclock`. t = wallclock (the row itself has no time). Rows without a wallclock are dropped. Team probability: home = homeWinPercentage; away = 1 - home - tie.
- Kalshi 1 minute candles (`scalper.api.candlesticks`) for both team markets, from the first play's wallclock minus 10 minutes to the market close. Use the candle's closing yes_bid, yes_ask, and its volume.

## ESPN lag, and the delay D (fixed before scoring)
The probability rows have no publication time, so the lag from the play's wallclock to the number appearing publicly is measured live on 2026-10-29/30 (college football 23:30Z, NBA 00:00Z, NFL 00:15Z): a poller reads the live summaries every ~15 s and records the first time each new row is seen (rows already present at a game's first poll are excluded). Lag = first seen - wallclock (resolution about 15 s). **D = 60 s if the 90th percentile lag is at most 60 s; otherwise D = (90th percentile lag rounded up to the next whole minute) + 60 s.** D is fixed from the sample before any scoring and is not a variant. Also reported: the share of rows whose live value differs from the post-game stored value by more than 0.01 (revisions would mean history is not what a live reader saw).

## Rule (exactly)
For each game, walk the ESPN rows in wallclock order. At row t, for each team X with probability pX:
- skip if pX <= 0.005 or pX >= 0.995 (outcome effectively known; not the model's forecast);
- entry candle = the first candle of X's YES market with end_ts >= t + D and end_ts <= t + D + 120 s (none: no entry at this row);
- valid quote: bid >= 0.01, ask <= 0.99, ask >= bid, and ask in [0.03, 0.97];
- signal if pX - askX >= threshold.
The first row with a signal (if both teams signal, the larger gap) gives the one entry of the game: buy X's YES at that candle's closing ask, hold to settlement (1 if X's market settles yes, else 0). At most one entry per game.

**Zero-volume candles, both ways:** Way A uses any candle with a valid quote; Way B uses only candles with volume > 0 (the first candle with volume > 0 inside the same time window). The verdict uses the worse of the two.

**Fees:** 7% x C x p x (1 - p), rounded up to the cent per order, at C = 1 and C = 10; the check at fees x 1.2 (the rounded fee times 1.2). No exit fee (held to settlement).

## Variants (N = 4, each counted)
- V1: all four leagues, threshold 0.08
- V2: all four leagues, threshold 0.15
- V3: football only (NFL + college football), threshold 0.08
- V4: NBA + MLB, threshold 0.08

## Windows, unit, judging
Matched games sorted by game date (UTC date of the first play), split into thirds by game count at whole-date boundaries: A (discovery), B (validation), C (holdout, read once, only after A and B are written into the result). Independent unit: the game (one entry per game). Per window: entries (games), win rate, mean price paid, net per contract, PF = gross winning net / gross losing net, at C = 1 and C = 10, and at fees x 1.2.
**Bar (RULES.md):** PF >= 1.5 in each of the three windows after fees (C = 1 and C = 10), positive at fees x 1.2, and pooled z of net per game >= 5.17 (deflated for N about 439,000). A variant with fewer than 30 entries in any window is NOT_ENOUGH_DATA. Otherwise anything short of the bar is FALSIFIED. No variant can be "promoted"; a pass earns only a forward test registration.

## Prediction (numeric)
V1: PF 0.6 to 0.95 in every window, net about -2c to -6c per contract, win rate near the ask paid and well below ESPN's probability. All four FALSIFIED. Prior of any pass: 3%.

## Information only (not variants)
Calibration over all rows with a valid quote: Brier score of ESPN's probability versus Kalshi's mid against the result, by league.

## Count
Running count about 439,024 before ESPN1; with these 4 variants about **439,028**.
