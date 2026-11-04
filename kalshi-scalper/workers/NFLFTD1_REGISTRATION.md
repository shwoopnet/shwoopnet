# NFLFTD1 registration: NFL first touchdown scorer (KXNFLFIRSTTD), CHEAP side only, player share model

Written 2026-11-04 BEFORE any Kalshi price, candle or outcome of this series and before any ESPN play-by-play was joined. Worker ID NFLFTD1, session "Strategy Research V2", source row 2 of `workers/SCOUT1_REGISTRATION.md`. Research only: no live code, no `functions/`, no L1, no OICORE, no promote verb.
**Owner rule (strict): CHEAP SIDE ONLY (ask 3c to 30c).** No favourite-side result is computed or printed. No 15 minute crypto or gold candle is used.
**N: +2** (one rule, one try; coordinator keeps the total, about 730,367; z bar 5.27).

## 1. Duplicate check
`grep -il "first touchdown\|FIRSTTD\|NFLFTD"` over README.md, workers/, docs/: only SCOUT1 (the ranked table, this row) and the census json. PROPS1 covers anytime TD (KXNFLANYTD), not first TD; SCOUT1, OVERROUND1, BOOKS1, FAMSPORTS, SP1, OICORE_SHAPE_INVENTORY do not test it. Not a duplicate.

## 2. Census (listings only; `src/scalper/nflftd1.py census`; read no result, price or candle; run before this text)
- Settled KXNFLFIRSTTD markets with close and expected expiration before the frozen cut 2026-10-03T16:00Z, historical plus live endpoints: **334 events, 6,741 markets** (3 to 32 players an event, median 20). By month: 2025-09 64, 10 58, 11 67, 12 67, 2026-01 28, 02 1, 2026-09 48, 10 1 (the 2025 season and weeks 1 to 4 of 2026).
- Games sorted by close: first two thirds = FIT 222 games, last third = TEST **112 games** (TEST starts at KXNFLFIRSTTD-25DEC14MINDAL, 2025-12-15).
- ESPN reachable keyless: scoreboard `dates=20250907` lists events; core `.../events/ID/competitions/ID/plays` returns play-by-play (171 plays for one game; first page checked for reachability only, no outcome joined).
- Expected treated trades: a first-TD probability for any one player is at most about 0.15, so "model >= 3 x ask" can only hold for asks up to about 5c; I guess 0.2 to 0.5 treated trades a game, i.e. **20 to 60 in the 112 TEST games**, and at most 224 even if every game had two (the cap). That is under 150 on the expectation, and the TEST games number 112 (under about 150).

## 3. Rule (frozen for the forward run; nothing here is fitted yet)
**Look.** Last 1 minute candle of the market ending at or before the ESPN game start minus 300 s with a valid two sided quote (0 <= bid < ask <= 1, ask - bid <= 0.10). Cheap side YES if ask in [0.03, 0.30], else NO if 1 - bid in [0.03, 0.30]; the other side is never evaluated or printed.
**Model.** P(player scores the first TD) = P(his team scores first TD) x share. P(team first) = de-vigged DraftKings moneyline/spread from ESPN core odds when present, else 0.5 shifted by the game's Elo-free default (0.5). Share = his count of first-TD-type events (rush/receive TDs for his team) from his earlier games in the ESPN play-by-play, shrunk `(n_td + k x lg_share) / (n_team_td + k)` over the last up to 8 earlier games of his team, k fitted from {2, 4, 8, 16} on the FIT games only (log likelihood of the actual first scorer among listed players); a player with no earlier game in the data is skipped.
**Trade.** Buy the cheap side at its ask, C = 10 contracts, hard limit 0.30, held to settlement, when model probability of that side >= 3 x ask; at most 2 per game (highest ratio, ties by sha1 of the ticker). Control: all cheap sides, same look, 2 per game by sha1. Fee 7% x C x p x (1 - p) rounded up, per contract (stress x1.2).
**Statistic.** Mean net after fee (cents) with game-clustered z; PF; win rate against mean ask; treated minus control; T1/T2 halves of TEST; event overround (sum of the asks of all listed players) and, descriptive only, low versus high overround games (split at the median).

## 4. Time box and fetch discipline
Census was one listing pass (about 14 requests at 0.8 s). A full run would be ~334 ESPN games at 1 request a second (play-by-play plus odds, about 20 minutes) and Kalshi candles for the TEST markets only (112 games x about 20 players, 8 markets per request, 1 to 2 threads, backoff, md5-ordered prefix with a 45 minute box, cache outside the repo). **That run is NOT started now: the census gate below stops it.** The frozen last third (games from 2026-10-03T16:00Z) is never fetched or joined.

## 5. Numeric prediction (stated before)
Model-vs-quote fails: the market maker prices from the same shares plus injuries and usage. If it were run: win rate of the cheap side 4% to 7% against a mean ask of 7% to 10%, mean net -2 to -4c per contract (fee included), PF 0.5 to 0.8, treated no better than control, 20 to 60 treated trades. Higher-overround games lose more (OVERROUND1).

## 6. Kill rules and verdict words
- **NOT_ENOUGH_DATA** if expected or actual treated trades < 150 or games < 150 (the census gate; applies now: 112 TEST games, 20 to 60 treated expected). Forward plan below.
- **FALSIFIED** (once 150 treated trades exist) if mean net after fees is not above 0 in both halves, or PF < 1.5, or z below the deflated bar 5.27.
- NOT_YET_FALSIFIED otherwise. No promote verb.

## 7. Forward plan
The 2026 NFL regular season is under way (week 9, 2026-11-04). The frozen games from 2026-10-03T16:00Z to the end of the regular season (about 2027-01-10) are about 14 weeks x 14 games = 190 more games; with the 112 TEST games that is about 300 games and, at 0.2 to 0.5 treated a game, **60 to 150 treated trades by 2027-01-11**, so 150 is reachable only at the top of the range. Plan: model parameters fitted once on the FIT games (first 222) and frozen in a committed file; read once on or after 2027-01-11, TEST plus frozen games together, with NOT_ENOUGH_DATA if still under 150 treated (then the 2027 season, September, is the next chance). No recorder is needed: Kalshi candles and ESPN play-by-play are fetchable after the fact.
