# SCOUT1 result (run once 2026-11-04; registration `workers/SCOUT1_REGISTRATION.md` + Amendment 1; code `src/scalper/scout1.py`, tests `tests/test_scout1.py`, census `workers/SCOUT1_CENSUS.json`, raw `workers/SCOUT1_RESULT.json`)

**Verdict MLBKS1 (KXMLBKS pitcher strikeout ladders, cheap side, game-log negative binomial, model >= 3x ask): NOT_ENOUGH_DATA by count (45 treated trades of 150, 32 games of 25 needed), sign against the idea.** Owner rule held: cheap side only; no favourite-side figure computed. Frozen third (starts at or after 2026-10-03T16:00Z) never fetched.

## Numbers
- ESPN 2,439 games with box scores; 33,186 KXMLBKS markets kept (1,088 dropped, result not yes/no); match rate 0.996; 2,404 matched games, FIT 1,602, T1 401, T2 401. Fit on FIT only: k 2, r 64 (top of the grid), gamma 0.5, league starter mean 4.689 strikeouts, league team strikeouts 8.39 a game.
- TEST: 796 games with a model, 10,423 rungs. **Candles were fetched for 7,449 rungs in 576 games (72% of TEST games)**: Amendment 1 (rate limit: archived markets one request per ~3 s) stopped the one-by-one fetch after about 90 minutes, in sha1(game) order, so the covered games are a random subset. 7,441 rungs had a valid two-sided quote at the look.
- Cheap-side candidates (ask 3c to 30c): 5,098 in 576 games. Model Brier on quoted rungs **0.1667 vs quote mid 0.1588** (the model is worse than the market, as predicted).
- **Treated (model >= 3x ask, max 2 a game): n 45, 32 games, win 4.4% against mean price 6.7c, mean net -2.70c (se 3.11, game-clustered z -0.87), PF 0.60** (fees x1.2: -2.80c, PF 0.59). T1 n 6 (0 wins, -5.55c), T2 n 39 (-2.26c, PF 0.68).
- Control (every cheap side, max 2 a game by sha1): n 1,152, win 16.1% against price 15.5c, mean net -0.33c (z -0.30), PF 0.97 (T1 +0.44c, T2 -0.70c). All cheap sides: n 5,098, -1.12c (z -1.88), PF 0.92.
- Prediction check: treated 60 to 250 (got 45 on 72% of games, about 62 on all 796, below the range), win/price 0.5x to 1.0x (0.66 held), mean -5c to -0.5c (held), PF 0.3 to 0.9 (0.60 held), control -4c to -1.5c (control was -0.33c, a miss: the pooled MLB cheap rung is nearly fairly priced), model Brier worse (held).
- Kill rules: not FALSIFIED by the letter (needs 150 treated). The direction would be met: not positive in both halves, PF 0.60 under 1.5. NOT_YET_FALSIFIED is excluded by the negative sign.
- Forward plan: about 0.078 treated trades a game; 150 needs about 1,900 games, i.e. about the first 80% of the 2027 MLB season (to about September 2027). Not worth a recorder. The MLB cheap-side control is nearly fair (win 16.1% vs price 15.5c, -0.33c), unlike BOOKS1's -5.7c, but it is a control, not a trade, and inside one standard error.
- N +2 (running about 730,333, z bar 5.27). Registration sha256 now `33ea0126c1ad1e64312621dd2f6ae1832b5e33f176b6bfae5178992cbeb07e69` (the file includes Amendment 1); the hash in the first ledger entry, f287d1c39b9d05ec5240e772d979aa219f16b89ac24f79806484e41733c94183, is the original text.

## What the scouting found
1. The census (107 series, listings only) shows the unexplored space is mostly thin: every monthly or weekly economics, weather, commodity and transport series has under 100 settled events (CPI 63, payrolls 43, unemployment 63, ISM 14, ADP 19, GDP 21, monthly snow 4 to 7 events a city, weekly average temperature 6 events a city, weekly silver 30), and COVID, MTA, flights and CO2 series stopped.
2. Series with thousands of events are sports and esports: KXLOLGAME 2,829, KXCS2GAME over 4,427, KXVALORANTGAME 1,591, KXATPCHALLENGERMATCH over 4,213, KXITF over 3,474, KXWTAMATCH 3,325, KXNPBGAME 881, KXKBOGAME 752, KXT20MATCH 1,535, KXMLBKS 2,432, soccer leagues 270 to 454 each. Only MLB, NBA, NHL, NFL and soccer have a keyless results source; Challenger, ITF, NPB, KBO and cricket do not.
3. Hourly crypto, FX, index, silver and WTI ladders have a median market volume of 0 to 4: candles are mostly empty.
4. Rate limit: the archived (before about 2026-08-28) Kalshi candle endpoint is one market per request and, with other workers on the same address, answered at about 20 requests a minute. Budget hours for more than 3,000 archived markets; the live batch endpoint (8 markets) works from about 2026-08-28.

## Ranked table of the unchosen rows (take the next row as an amendment before any outcome is joined)
| # | ID | Kalshi series (events / markets, median market volume) | Reference or mechanism (reachable keyless?) | Nearest tested item and why this differs | M | T | Score | Runnable? |
|---|---|---|---|---|---|---|---|---|
| 2 | NFLFTD1 | KXNFLFIRSTTD first touchdown scorer: 338 / 6,741 (about 20 cheap players an event), median 1,601 | P(first TD) = P(team scores first TD) x the player's touchdown share; ESPN play by play gives the first scorer and game logs: yes | PROPS1 has anytime TD (KXNFLANYTD) not first TD; no ledger line | 2.5 | 40 | 4.04 | yes (next in line) |
| 3 | WXAVGT1 | KXAVGTK* weekly average temperature, 10 cities: 6 events each from 2026-08-24 (60 in all; live every week) | NOAA NCEI daily TMAX/TMIN (checked reachable): the part of the week already observed is a fact, the rest is climatology; forward-only | FAMWX (daily highs/lows vs a forecast) is DUPLICATE; weekly averages are not in the ledger. Source is weather.com so a source mismatch is possible | 3 | 15 | 3.61 | partly (history 60 events: NOT_ENOUGH_DATA by count, forward plan) |
| 4 | NHLG1 | KXNHLGOAL anytime goal scorer: > 103 / > 6,000 (Apr to Jun capped; the 2025-26 season is longer), median 415; in season now | Poisson goal rate from a game log; ESPN box scores | PROPS1 lists NHL as out of scope | 2 | 60 | 3.56 | yes |
| 5 | WXSNOW1 | monthly snow in 14 cities (4 to 7 events each, 4 to 7 markets each: about 85 events, 380 markets) and KXRAINNYCM 36 / 222 | NOAA daily PRCP/SNOW (reachable): running total to date is a fact, the rest is climatology | COUNT2 (tornado) and RAINCAL; none on cumulative precipitation | 3 | 8 | 2.86 | no on history (fails the census: 85 events), forward Nov to Mar |
| 6 | GOLF1 | KXPGATOUR 63 / > 6,171, KXPGATOP20 44 / 4,548, KXPGATOP10 44 / 4,548, KXPGAR1LEAD 38 / 4,228; H2H 1,340 events (TENNIS1's census) | Leaderboard after each round plus a stroke model; ESPN leaderboard by round | TENNIS1 judged golf NOT_ENOUGH_DATA (about 50 treated); no golf entry in the ledger | 2 | 20 | 2.61 | history yes, count no (63 tournaments) |
| 7 | ESPORTM1 | match winners: KXLOLGAME 2,829 / 5,844, KXCS2GAME > 4,427 / > 8,868, KXVALORANTGAME 1,591 / 3,255 | Elo from Kalshi's own settled matches only (no outside results source found) | ESPORT1 did the MAP markets with the same self-built Elo and was FALSIFIED (PF 0.88, 0.83) | 1 | 200 | 2.30 | yes, but self-referential and a near duplicate |
| 8 | MMA1 | KXUFCFIGHT 717 / 1,474, median 372,836 | ESPN fighter records, no rating history | TENNIS1's census: about 30 treated, NOT_ENOUGH_DATA | 1.5 | 30 | 2.24 | count no |
| 9 | TNOTED1 | KXTNOTED daily 10 year yield: > 400 / > 6,000 (median volume 0), KXTNOTEW 170 / 2,544 (median 8) | Treasury par yield or FRED DGS10 (FRED flaky from here) with a trailing volatility | WTIW1 did the WEEKLY series (1 trade, NOT_ENOUGH_DATA) and USD/JPY daily; the daily 10 year was not run | 2 | 10 | 2.08 | thin quotes, likely NOT_ENOUGH_DATA |
| 10 | MLBPROP1 | KXMLBHR > 334 / > 11,057, KXMLBHIT > 186 / > 10,316, KXMLBTB > 153 / > 10,060, KXMLBHRR > 110 / > 9,384 (all listed from late August 2026 only) | Per plate appearance rates from ESPN | PROPS1 out of scope; MLBKS1 is the same pipeline on the series with the widest cheap ladder | 1.5 | 20 | 1.95 | yes (short history) |
| 11 | ECONREL1 | CPI 63 / 508, core CPI, payrolls 43 / 396, unemployment 63 / 599, ISM 14, ADP 19, GDP 21, housing starts 6; non-US (Brazil inflation, central bank decisions) fewer than 30 each | nowcasts and releases (FRED, BLS) | CPI1, ECONNEW1, ECONNEW2, NOWCAST1, MENT1 (all FALSIFIED or NOT_ENOUGH_DATA) | 2 | 10 | 2.08 | fails the census (events < 150, markets < 1,500 per series) and is a duplicate in spirit |
| 12 | HRLY1 | hourly range and above/below ladders on crypto (KXBTC, KXETH, KXSOLE, KXXRP, KXDOGE, KXBNBD, KXHYPE), FX (KXEURUSDH, KXUSDJPYH), indices (KXINXU, KXNASDAQ100U), silver and WTI (KXSILVERH, KXWTIH): hundreds of hourly events each in 3 to 9 days of capped listing; **median market volume 0 to 4** | spot (Coinbase works; OKX perps for silver, WTI, equity indices; Binance blocked) | LAD1, HOURLY1, VOLGAP1, IDXFUT1, XLADDER1, NEWH4 TAIL, LADLONG1, E4 | 1 | 40 | 1.61 | mostly empty candles ("KXGOLDH candles start 900 s before the close, mostly zero volume" is the precedent) |
| 13 | BOOKNCAA1 | KXNCAAMBGAME 5,283 / 10,566, KXNCAAWBGAME 4,078 / 8,156 | ESPN core odds endpoint returns DraftKings closing moneylines for D1 men's games (checked on 10 games) | BOOKS1 ran CFB, MLB, NFL, NBA: 0 treated of 258 cheap sides, median gap +0.76c; the same structure | 1 | 5 | 0.78 | runnable and predicted NOT_ENOUGH_DATA (book and Kalshi are one price) |
| 14 | SOCCERELO1 | KXEPLGAME 437, KXLALIGAGAME 454, KXSERIEAGAME 430, KXLIGUE1GAME 354, KXBUNDESLIGAGAME 347, Eredivisie 285, Portugal 294, Turkey 270, Liga MX 287, UCL 301 events (about 3 markets each) | Elo from ESPN results or Pinnacle closing odds (football-data.co.uk reachable) | **an untracked `src/scalper/soccer1.py` is in the shared tree: another worker has it; not taken** | 1 | 40 | 1.6 | claimed elsewhere |
| 15 | NPBKBO1 | KXNPBGAME 881 / 1,824, KXKBOGAME 752 / 1,564 | no keyless results source (ESPN has no NPB/KBO feed: HTTP 400 on the scoreboard) | none | 1 | 0 | 0 | **NOT_RUNNABLE** |
| 16 | CHALLITF1 | KXATPCHALLENGERMATCH > 4,213, KXITFMATCH > 3,474, KXITFWMATCH > 3,000, KXWTAMATCH 3,325 (tour level is TENNIS1's) | no results source for Challenger and ITF (TENNIS1 checked Sackmann, ESPN) | TENNIS1 states NOT_RUNNABLE | 1 | 0 | 0 | **NOT_RUNNABLE** |
| 17 | CRIC1 | KXT20MATCH 1,535 / 3,228, KXODIMATCH 133, KXIPLGAME 75 | no ratings or results source reachable | none | 1 | 0 | 0 | **NOT_RUNNABLE** |
| 18 | MENTION1 | KXWCMENTION, NBA/NFL mention one-offs, 465 Mentions series | transcripts are not keyless for history | MENT1, MENTIONBASE1 (NBA: PF 1.25 then 1.04, no edge) | 1 | 0 | 0 | **NOT_RUNNABLE** |
| 19 | DEAD1 | KXCASED COVID 256 events ended 2022-08; KXMTA 47 ended 2025-08; KXFLIGHTORD 53 ended 2025-11; KXCO2 12 ended 2022; KXOIL 11 ended 2022 | would have references (CDC, MTA open data checked reachable) | n/a | 3 | 0 | 0 | **fails the census** (series stopped or under 150 events) |
| 20 | RARE1 | awards, state elections and referendums, hurricanes (annual counts, KXHURCTOT), F1 and NASCAR races (24 a year), World Cup (104 games, ended 2026-07-19), government shutdown, deadline/hazard one-offs (KXKHAMENEIOUT, KXHORMUZNORM), KXHMONTH 31 | various | ELECT1 (midterms, run on election night) and CALIB1 | 2 | 0 | 0 | **fails the census** (under 40 events each) |
| 21 | YRFI1 | KXMLBRFI run in the first inning 2,462 / 2,557, median 153,434 | binary near 50%: the cheap side (ask 3c to 30c) practically never exists | none | 1 | 0 | 0 | structurally empty |
| 22 | RAIND1 | KXRAINNYC daily NYC rain 869 / 895 (stopped 2026-07-16) | NOAA PRCP is reachable, a forecast archive is not (Open-Meteo timed out) | RAINCAL (forward only, NWS PoP) | 1 | 5 | 0.78 | model weaker than the market |
| 23 | WKCMD1 | weekly commodities: silver 30 / 1,250, corn 4, others under 30 events | OKX/Yahoo | USWEEP1/2/3 (tail sweep), WTIW1 | 2 | 3 | 1.2 | fails the census |
| 24 | CHARTS1 | Spotify daily, Netflix weekly, Billboard, app store rank | kworb shows only the current day | SPOTD1 (FALSIFIED/short), CHART1 (NOT_RUNNABLE) | 2 | 0 | 0 | tested |

Next in line: row 2 NFLFTD1 (KXNFLFIRSTTD first touchdown scorer, 338 events, 6,741 markets, in season now). Rows 3 and 5 (weather) are forward-only and need a recorder. Row 4 (NHL anytime goal) is being taken by another worker (`nhlg1_census.py`, NHLALL1 in the tree). Row 14 (soccer) is SOCCERELO1, registered by another worker.

## Printout (`python -m scalper.scout1 score`)
```
cheap_entries 5098
games_with_cheap 576
quoted_rungs 7441
brier_model 0.16667762095247238
brier_mid 0.15883852976750437
treated {'n': 45, 'games': 32, 'mean_c': -2.7022, 'se_c': 3.1126, 'z': -0.8682, 'pf': 0.602, 'win': 0.0444, 'price': 0.0667}
treated_x1.2 {'n': 45, 'games': 32, 'mean_c': -2.7982, 'se_c': 3.1134, 'z': -0.8988, 'pf': 0.5933, 'win': 0.0444, 'price': 0.0667}
treated_T1 {'n': 6, 'games': 5, 'mean_c': -5.55, 'se_c': 0.6976, 'z': -7.9557, 'pf': 0.0, 'win': 0.0, 'price': 0.0517}
treated_T2 {'n': 39, 'games': 27, 'mean_c': -2.2641, 'se_c': 3.5878, 'z': -0.631, 'pf': 0.6756, 'win': 0.0513, 'price': 0.069}
control_cap2 {'n': 1152, 'games': 576, 'mean_c': -0.3329, 'se_c': 1.1211, 'z': -0.2969, 'pf': 0.9747, 'win': 0.1606, 'price': 0.1547}
control_cap2_x1.2 {'n': 1152, 'games': 576, 'mean_c': -0.5181, 'se_c': 1.1212, 'z': -0.4621, 'pf': 0.9611, 'win': 0.1606, 'price': 0.1547}
control_cap2_T1 {'n': 370, 'games': 185, 'mean_c': 0.4395, 'se_c': 1.9347, 'z': 0.2271, 'pf': 1.0338, 'win': 0.1703, 'price': 0.1565}
control_cap2_T2 {'n': 782, 'games': 391, 'mean_c': -0.6983, 'se_c': 1.3743, 'z': -0.5082, 'pf': 0.9473, 'win': 0.156, 'price': 0.1538}
all_cheap {'n': 5098, 'games': 576, 'mean_c': -1.1168, 'se_c': 0.5956, 'z': -1.8751, 'pf': 0.9151, 'win': 0.1508, 'price': 0.1529}
all_cheap_x1.2 {'n': 5098, 'games': 576, 'mean_c': -1.2999, 'se_c': 0.5956, 'z': -2.1824, 'pf': 0.9022, 'win': 0.1508, 'price': 0.1529}
all_cheap_T1 {'n': 1653, 'games': 185, 'mean_c': -1.7541, 'se_c': 1.0124, 'z': -1.7326, 'pf': 0.8681, 'win': 0.1446, 'price': 0.153}
all_cheap_T2 {'n': 3445, 'games': 391, 'mean_c': -0.8111, 'se_c': 0.7351, 'z': -1.1034, 'pf': 0.938, 'win': 0.1538, 'price': 0.1528}
```
