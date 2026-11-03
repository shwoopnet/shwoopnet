# FAMXV registration: Kalshi against Polymarket on the same game, and internal consistency (written 2026-11-03, before any Polymarket game price was downloaded or any gap computed; 2 tries, running count about 728,732 before, 728,734 after, z bar about 5.27)

Research only. No order, no live code, no functions/, no L1, no OICORE. Verdict words: FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE, DUPLICATE.

## 1. Duplicate check
**Internal consistency (monotonicity, bracket sums, same event two tickers): DUPLICATE.**
| Test | What | Verdict |
|---|---|---|
| 2026-10-23 structure scan | KXBTCD monotonicity (238 strikes), KXBTC/KXETH range sums | 0 violations; range bids sum 0.75/0.67, asks 2.96/5.84 |
| ARB1 (10-13/14) | mutually exclusive events, 12 scans | FALSIFIED |
| ARB2, ARB3, ARB4 (10-28/29) | every open event full set and ladder; deadline ladders; range vs above ladder | FALSIFIED, best -1.5c / +0.6c / +0.1c, zero opportunities; RULES1: the one flag (USCLIMATE) is a TRAP; FEE1: size reveals nothing |
| WX3 (10-27) | daily-high temperature buckets | FALSIFIED |
| ARB5, SPORTCONS1 | sports totals ladders, winner complement | FALSIFIED / NOT_ENOUGH_DATA |
Killed assumption: that stale quotes leave locks at the top of the book. Market makers enforce arithmetic inside the fee. Not repeated here.
**Cross-venue:** PM1 (10-13: Polymarket 15 minute price vs Kalshi; Brier Bitcoin 0.1523 vs 0.1406), PM2, PM3, PM1 noon ladder (10-27: 0 usable strike-time pairs), XVENUE1 (10-30: resolutions differ 1.44%, measurement only). Killed assumption: that Polymarket carries information Kalshi's price lacks. All inputs were crypto. **Different input that is new: Polymarket's price on non-crypto events, here sports game winners, where both venues copy the same sportsbook lines.** Fed, CPI and election pairs were considered: there are about 8 FOMC meetings a year and a handful of matched events, so independent pairs cannot reach 150 in months; NOT_ENOUGH_DATA by arithmetic, not run.

## 2. Reachability (2026-11-03)
Polymarket gamma (`gamma-api.polymarket.com/events?slug=`) and CLOB (`clob.polymarket.com/prices-history?market=<token>&startTs&endTs&fidelity=1`) reachable, 1 minute history for resolved game markets works (checked on `nba-mia-tor-2026-10-03`, moneyline token, points about every 60 s). Game slug: `<nba|nfl>-<away>-<home>-<YYYY-MM-DD>`; its `sportsMarketType: "moneyline"` market is the winner. No allowlist change needed. Blocked: none for this test.

## 3. Question, counterparty, prior
When Polymarket's price for a team is above Kalshi's ask by a margin, does Kalshi's team win more often than its ask? **Counterparty:** Kalshi quoters slower than Polymarket's or retail leaving a stale ask. **Honest prior of a pass: 2%.** Both copy sportsbooks, PM1 found Kalshi the better predictor, and ESPN1 found Kalshi's mid beat an outside forecast.

## 4. Universe (fixed now)
The 258 NBA and NFL games in `data/espn1.sqlite` (`match`, `egame`: KXNBAGAME 138, KXNFLGAME 120, with ESPN start time and both Kalshi team tickers and their 1 minute candles). College football and MLB excluded (slug scheme unverified for college; MLB out of season). A game enters only if a Polymarket event is found by trying the slugs `<sport>-<away>-<home>-<date>` and the reversed order, date = ESPN start date in UTC and in US Eastern, lower-case Kalshi/ESPN team codes; if none found, dropped and counted.

## 5. Rule (fixed now)
Look: 60 minutes before the ESPN start. Kalshi: the last valid two-sided candle (bid < ask, ask minus bid at most 0.10, 0.02 <= prices <= 0.98) ending between 90 and 30 minutes before the start. Polymarket: the last history point at or before the look for the token of the same team, no more than 15 minutes old. gap(team) = P_pm(team) - Kalshi ask(team). For each game take the team with the larger gap; trade if the gap is at least the try's threshold: buy that team YES at the Kalshi ask, C = 10, fee `ceil(0.07 * C * p * (1-p) * 100)/100`, held to settlement. Stress fees x1.2.
- **Try A:** gap at least 0.04. **Try B:** gap at least 0.08.
Information, not a verdict: Brier of Polymarket's price, of Kalshi's mid and of the blend; the distribution of gaps.

## 6. Windows, gates, frozen holdout
W1, W2, W3: thirds of eligible games by date. **W3 frozen, read only if W1 and W2 pass.** Gates: pooled at least 150 trades, PF at least 1.5 in each of W1 and W2, mean at least +2c, event z at least 5.27, positive at fees x1.2, and Polymarket-blend Brier no worse than Kalshi's. Else FALSIFIED if PF under 1.5 with at least 30 trades per window, else NOT_ENOUGH_DATA.
N: +2, z bar about 5.27 at N about 728,734.

## 7. Numeric prediction (before any run)
Median absolute gap 1c to 2c; a gap of 4c or more in 4% to 12% of games, 8c or more in under 2%. Trades: A 10 to 30, B 0 to 5, so **NOT_ENOUGH_DATA by count**; Kalshi's Brier beats Polymarket's by 0.001 to 0.01. Mean on A trades -2c to +1c.

## 8. Expected read date and data needed
Today on the 258 games. Data needed for a verdict: 150 triggered trades is about 150 / 0.08 = 1,900 games, i.e. a full NBA season plus an NFL season (about 2027-04-20 for NBA and NFL regular seasons to date); candles and Polymarket history stay retrievable after the fact, so no recorder is needed.
