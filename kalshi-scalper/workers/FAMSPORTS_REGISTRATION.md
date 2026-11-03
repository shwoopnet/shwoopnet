# FAMSPORTS registration: NBA, NFL and NHL game totals against a public box-score model (written 2026-11-03, before any final score was downloaded, any model value computed or any outcome compared; 2 tries, running count about 728,730 before, 728,732 after, z bar about 5.27)

Research only. Nothing places an order. No live code, no functions/, no L1, no OICORE. Verdict words: FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE, DUPLICATE, registered forward test.

## 1. Duplicate check (grep of README.md, workers/OICORE_SHAPE_INVENTORY.md, workers/SPORTS*, SPORTSPRE, ESPORT1, ESPN1, SPORTCONS1, arbitrage, monotonic, bracket)
| Earlier test | Input | Verdict | Why this is not it |
|---|---|---|---|
| SP1 (2026-10-13) | Kalshi price only, 88c to 97c game-winner favourites, 12 series | FALSIFIED, -4.19c, z -2.8 | no outside forecast, winners |
| F6 and F7 (2026-10-27) | Kalshi quote only: tennis favourites; total UNDER at YES mid 0.40 to 0.60 | FALSIFIED (-0.22c; -1.56c, z -0.59) | no reference model, one fixed price band. Its own note: win rate equals price, fee and spread are the whole loss |
| ARB5 (2026-10-29) | crossed totals ladder inside one game | FALSIFIED, zero locks in 691 games | internal arithmetic, no model |
| SPORTCONS1 (2026-10-30) | winner complement, game vs first-half total | FALSIFIED / NOT_ENOUGH_DATA | internal arithmetic |
| ESPN1 (2026-10-30) | ESPN in-play win probability vs game-winner ask | FALSIFIED 4 of 4 | winners, in play, ESPN's probability |
| SPORTSPRE (2026-10-31) | ESPN pre-game win probability vs moneyline | forward recorder, not read | winners, ESPN's probability |
| ESPORT1 (2026-11-02) | Elo from Kalshi's own maps | FALSIFIED | esports winners |
Killed assumption in every row: that Kalshi's sports price is wrong relative to something public. Win rate equals price, and the fee plus the spread are the whole loss. **Never tried: a TOTALS line against a points model built from public final scores.** The only totals tests were internal (ARB5, SPORTCONS1) or price-band-only (F7). That is the new input. Not a reword of any of them.
Player props: no player-prop series is on file (sports1.sqlite holds only KXNBATOTAL, KXNBA1HTOTAL, KXNFLTOTAL, KXNFL1HTOTAL, KXNHLTOTAL) and none was downloaded, so props are NOT_RUNNABLE in this pass. Spreads (win by N) likewise have no data on file (SPORTCONS1 inventory). Soccer: no series on file.

## 2. Reachability from this sandbox (checked 2026-11-03)
Reachable: ESPN scoreboard `site.api.espn.com/apis/site/v2/sports/<sport>/<league>/scoreboard?dates=YYYYMMDD` (ONE day per request; a date range returns HTTP 400), Polymarket gamma and CLOB, basketball-reference.com (not scraped). Blocked or keyed: stats.nba.com (403), the-odds-api.com (401, needs a key), pinnacle.com (302, no keyless line). **So a sportsbook consensus line is NOT available; the reference is a simple model from public box scores only.**

## 3. Question, counterparty, prior
Is a Kalshi game-total line wrong in a way that a points model built only from teams' earlier final scores can see? **Counterparty:** retail over/under bettors, who bet overs (Bartlett and O'Hara, NBER, 41.6 million Kalshi trades, `NEWH16_DIGEST.md` source 2; F7 saw the over lose -3.07c against the under -1.56c). **Honest prior of a pass: 2%.** A trailing-average model is much weaker than the lines it competes with. Most likely result: model Brier worse than the market's mid, FALSIFIED.

## 4. Universe (fixed now)
Settled `KXNBATOTAL`, `KXNFLTOTAL`, `KXNHLTOTAL` markets in `data/sports1.sqlite` (full-game totals only; first-half series excluded). The game (event) is the unit. A game enters only if ESPN has it (matched by date and the two team codes in the ticker), it has a start time and both teams have 5 or more earlier completed games. Games failing are counted and dropped, not tried another way.

## 5. Reference (fixed now)
Public final scores from ESPN's scoreboard, one request per day from 2025-09-01 to 2026-11-02, every completed game of NBA, NFL and NHL. For a game on day d: F_x = mean points scored and G_x = mean points allowed by team x in its last 10 completed games before day d (this and last season, at least 5). `pred_total = (F_A + G_B)/2 + (F_B + G_A)/2`. Over probability at strike K (the market's `strike`, always a half number): `1 - Phi((K - pred_total) / sigma)`, sigma fixed now: NBA 19.0, NFL 14.0, NHL 2.4. No fitted parameter, no tuning.

## 6. Rule (fixed now)
Look: for each strike of the game, its first candle with a valid two-sided quote (0.01 <= bid < ask <= 0.99, ask minus bid at most 0.10) ending between 120 and 10 minutes before ESPN's start time. For each such strike, the side bought is the one with the larger `p_side - ask_side - fee/C`, the taker fee `ceil(0.07 * C * p * (1-p) * 100)/100` at p = ask, C = 10. One entry per game: the strike and side with the largest edge, if the edge is at least the try's threshold. Fill at that ask, held to settlement (settled result from the market).
- **Try A:** threshold 0.08, all three sports.
- **Try B:** threshold 0.15, all three sports.
Cost: fee as above, stress x1.2.

## 7. Windows, gates, frozen holdout
W1, W2, W3 are thirds of the ELIGIBLE GAMES by game date (not of trades), fixed before anything is scored. **W3 is the frozen holdout and is read only if W1 and W2 both pass.** Gates: pooled W1 + W2 at least 150 trades; PF at least 1.5 in each of W1 and W2 after fee; mean at least +2c a contract; event z at least 5.27; PF positive at fees x1.2; AND model Brier on the over/under outcome of the strike nearest a 50c mid (one per game) better than the market mid's Brier, else FALSIFIED. Fewer than 150 trades with Brier passing is NOT_ENOUGH_DATA.
N: +2 (A and B), z bar about 5.27 at N about 728,732.

## 8. Numeric prediction (before any run)
Model Brier worse than the market's mid by 0.005 to 0.03. Trades 60 to 300 per try, win rate close to the ask, mean -3c to -7c a contract, PF 0.5 to 0.9. Verdict FALSIFIED. Smallest honest live probe, if the owner ever wants one: see the result file; it is only meaningful if the model Brier passes.

## 9. Expected read date
Today (history on file). The NBA and NHL seasons are a few weeks old, so W1 to W3 are thin for them; if NOT_ENOUGH_DATA, the data needed is a full season of games (about 1,230 NBA games Oct to April) readable on or after 2027-04-20 from history, with no recorder needed.
