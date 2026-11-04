# SOCCERELO1: Kalshi soccer cheap side vs a walk-forward Elo with a draw model built from ESPN results. Held to settlement.

Registered 2026-11-04 BEFORE any Kalshi soccer candle price or Kalshi result was joined to an Elo probability (no Elo probability for any Kalshi match exists yet; the ESPN history fetch of the 2025-26 season was running when this was written, and the in-window ESPN results, Aug 28 to Oct 2 2026, are fetched only after this is pushed). Worker ID SOCCERELO1, session "Strategy Research V2". **N: +2** (one rule). Owner rule: CHEAP SIDE ONLY (ask 3c to 30c); no favourite-side result is computed or printed; no 15 minute crypto or gold candle trigger. Discovery only.

## Duplicate check (done first)
README and workers searched for soccer, Elo, draw. SOCCER1 tested Kalshi cheap soccer against the de-vigged DraftKings price (gap median +0.12c, treated 0 of 801, NOT_ENOUGH_DATA). BOOKS1/BOOKS2/BOOKNCAA1 are US two-way markets against a book. TENNIS1 and ESPORTM1/ESPORT1 are Elo on tennis and esports. **No Elo soccer test exists.** SCOUT1 row 14 asked for exactly this. Not a duplicate; a different reference (own ratings from results, no sportsbook).

## Honest prediction of the mechanism
SOCCER1 showed the book and Kalshi agree to about 0.1c. An Elo from one season of results is a noisier, weaker reference than the book, so where it disagrees with Kalshi by 3x the Elo is almost surely the one that is wrong. An edge would need BOTH the book and Kalshi to be wrong in the same direction. Expect nothing.

## Census (listings only, outcome free)
Kalshi settled GAME events before the frozen cut (listing, 2024-01-01 to 2026-10-03T16:00Z): all start on 2026-08-28 (new season launch), so history is one month: EPL 40, La Liga 50, Serie A 40, Ligue 1 36, Bundesliga 36, Eredivisie 39, Primeira 38, Liga MX 48, UCL 18; Turkey 0. About 345 matches, under the 500 line. Expected cheap outcomes about 2 per match, treated expected 0 to a handful. A price-only count of expected treated (pre-window ratings, SOCCER1's cached asks, no result) is run after this push and reported in the result file; it cannot change the rule.

## Ratings and fit rule (no Kalshi outcome used anywhere)
- Matches: ESPN core API completed league results (home/away names, UTC start, winner flag; a draw when neither side is the winner and ESPN status says completed). Leagues eng.1, esp.1, ita.1, ger.1, fra.1, ned.1, por.1, mex.1, uefa.champions. History 2025-08-01 to 2026-08-27 (warm-up), then in-window results 2026-08-28 to 2026-10-02. Nothing from 2026-10-03T16:00Z is fetched or joined.
- Model: one Elo pool keyed (league, team), start 1500, ratings pulled 25% toward 1500 after a gap over 45 days, Davidson three-way probabilities with scale 400: P(H) = gh/(gh+ga+nu), P(D) = nu/(...), P(A) = ga/(...), gh = 10^(d/800), ga = 10^(-d/800), d = rH + HA - rA; K step on expected score pH + pD/2.
- Fit: home advantage HA in {40,60,80,100}, draw parameter nu in {0.6,0.8,1.0,1.2}, K in {10,20,30} chosen by walk-forward log loss on the last two thirds of the warm-up season matches ONLY (all before Aug 28, 2026). Not refit afterwards. In-window ratings update with each result strictly after the match it predicts (prediction for a match uses only earlier matches). A team needs 5 earlier games to be rated; otherwise the match is not tradable (counted).

## Join and look
ESPN match to Kalshi GAME event by league, UTC date within one day and both team names equal (SOCCER1's matcher). Look: the last 1 minute candle ending at least 120 s before ESPN kickoff, valid quote (0 <= bid < ask <= 1, spread at most 0.10), from SOCCER1's cache (no new Kalshi fetch unless a match is missing).

## Trade (one rule, no tuning)
Cheap side only: the outcome side (YES, or NO = 1 minus bid) whose ask is in [0.03, 0.30], hard limit 0.30. TREATED when the Elo probability of that side >= 3 x ask. One contract at the ask, held to settlement, fee 0.07 x p x (1-p) rounded up per 10 (C = 10), at most 2 per match (largest q/ask). Control = all cheap outcomes. Cluster = match. Halves by start time of treated trades. Result text uses cheap-side rows only.

## Numeric prediction (before any join)
Rated and joined matches 250 to 340. Gap (Elo minus ask) on cheap outcomes: median between -2c and +1c, p90 under 12c. Treated n between 0 and 15 (point 3). Control mean net after fees between -2c and +1c, PF 0.9 to 1.1.

## Kill rules and verdicts
- FALSIFIED: treated n >= 150 and (mean net after fees not above 0 in both halves, or PF under 1.5).
- NOT_ENOUGH_DATA: treated n < 150 (or under 25 matches with a treated trade). Report n, months to 150 at the observed rate, and a forward plan (the leagues are in season; weeks to months depending on rate).
- A pass needs 150 treated trades, both halves positive, PF >= 1.5 and z against the N-adjusted bar (running N about 730,379, z bar 5.27). Nothing here promotes.

## Execution
ESPN 1 request per second, honest User-Agent; no new Kalshi fetch planned; caches in /tmp/claude-0/soccerelo1 and /tmp/claude-0/soccer1. Code `src/scalper/soccerelo1.py`, tests `tests/test_soccerelo1.py` (synthetic).
