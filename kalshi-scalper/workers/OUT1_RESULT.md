# OUT1: official teammate-out status vs backup NFL pass-catcher props, CHEAP side only. Result: NOT_ENOUGH_DATA at the census; nothing scored

Worker OUT1, session "Strategy Research V2", 2026-11-04. N: +2 (coordinator keeps the total). Discovery only, no live code. Owner rules held: cheap side only (ask 3c to 30c), no favourite-and-hold, no 15 minute crypto or gold candle trigger.

## Duplicate check
PROPS1 (game-log model, all cheap sides, 9 treated; its listings and candle database are reused read-only here, no re-fetch), XMET1, SPORTS-PRE (game-level), NFLFTD1 and NFLANYTD1 (NOT_ENOUGH_DATA and FALSIFIED, no injury trigger). None uses an official injury status as the trigger. Not a duplicate.

## Census (listings, injury reports and snap counts only; `src/scalper/out1_census.py`, output `workers/OUT1_CENSUS.json`)
No Kalshi candle, price or result was fetched or joined. Sources: nflverse `injuries_2024/2025/2026.csv` (report_status, the final game-week report) and `snap_counts_2024/2025/2026.csv`, nflverse `games.csv` (ESPN id map), keyless.
- NFL games listed before the cut 2026-10-03T16:00Z in PROPS1's database: **335**; with a nflverse REG/POST id and listed receiving or rushing player markets: **241** (the rest are preseason, which has no injury report).
- Trigger = a top-2 WR/TE/RB/FB by prior-4-game offense snaps (at least 3 prior team games) listed Out or Doubtful on the game-week report: **26 triggered games** (26 team-games; 23 in the 2025 season, 3 in 2026). Sensitivity, same data: top 3 gives 44 games, top 4 gives 68 (not the registered rule).
- Listed beneficiary rungs (every other listed pass-catcher or runner of that team in KXNFLRECYDS, KXNFLREC, KXNFLRSHYDS): **1,219** rungs in 26 team-games, median 5.5 players. PROPS1's candled NFL data and its control give a cheap side (ask 3c to 30c) on about 36% of markets and a model-at-3x-ask hit on about 2% of those cheap sides (9 of 397), perhaps 10% if the usage shift is real: expected treated trades **about 9 to 45**, at most 78 under the cap of 3 per game. The last third (TEST) holds about 9 triggered games, FIT about 17.
- **Under the bar of 60 games and about 150 expected treated trades on every count.** The brief expected 40 to 100 games from about 256 matched games; only 10% of NFL games have a top-2 skill player Out or Doubtful by this definition.

## Verdict: NOT_ENOUGH_DATA (census). Nothing registered for scoring, no candle fetched, the frozen third untouched.
Timing caveat recorded for any later read: the Friday report precedes the game by at least a day and an Out status is often public days earlier, so the quote may already carry it; the look would be the last candle at least 120 s before kickoff. Control for a later run: the same player's cheap rungs in games where the teammate was not out (win-rate lift minus ask lift).

## Forward plan
- NFL 2026 season: about 3 triggered games in weeks 1 to 4, then about 5 to 6 a month of regular season; 60 games needs the 2026 and 2027 seasons together and 150 treated trades is out of reach this way.
- NBA/NHL: the ESPN injuries endpoint with timestamps, polled forward from 2026-11-05 alongside the pre-game recorder: 15 to 60 treated a month (the brief), so 150 is 3 to 10 months away. A forward registration for NBA would need to be written before any quote is read.
- The pooled evidence already on file (PROPS1 control -4.87c, NFLANYTD1 -5.48c, MLBKS1 control -0.33c) says the cheap side of player props loses on average; a teammate-out trigger would have to lift the win rate about 6c over price to pass.

Running N: +2 (coordinator keeps the total, about 730,413; z bar 5.27). Registration hash: this file is the record; sha256 is printed in the README entry.
