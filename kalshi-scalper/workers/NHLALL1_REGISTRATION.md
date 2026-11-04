# NHLALL1 registration: unconditional cheap-side pool on KXNHLGOAL 1+ goal rungs, with a ladder-sum filter

Written 2026-11-04 BEFORE any NHLALL1 candle was fetched and before any outcome was joined. Worker ID NHLALL1, session "Strategy Research V2". Research only: no order, no live code, no `functions/`, no L1, no OICORE, no promote verb.
**Owner rule (strict): CHEAP SIDE ONLY (ask 3c to 30c).** No favourite-side result is computed or printed. No 15 minute crypto or gold candle is used.
**N: +4** (+2 the pooled rule, +2 the ladder-sum filter; running count about 730,371 before, z bar 5.27).

## 1. Duplicate check (done)
Grep of README.md and workers/ for goal, scorer, under-round, NHLG1, PROPS1, SCOUT1, CALIB1, LIQ1, PRICEMATCH1, OVERROUND1, NFLFTD1. NHLG1 tested a Poisson MODEL against the quote on the same series (0 treated trades). CALIB1 measured the cheap side by ask bucket across categories (-2.4c to -10.4c); OVERROUND1 measured over-round on other ladders. Nobody tested the unconditional cheap rung of KXNHLGOAL or a within-game ladder-sum filter. Not a duplicate; this is not a model-vs-quote test.

## 2. Disclosure: what was already seen
NHLG1's information-only side finding (NOT evidence, not reused): on 18 TEST games, 247 cheap YES rungs (ask 3-30c) won 22.3% at mean price 15.8c, mean +5.6c, PF 1.46 (z about 1.7); sum of 1+ asks 3.31 against 3.88 expected scorers. **That is the reason this rule exists, so it is a selected hypothesis.** To keep the new test clean, ALL 25 events for which nhlg1.sqlite holds any candle (a superset of the 18) are EXCLUDED, and nothing about them is used. The list is in `workers/NHLALL1_CENSUS.json` (`excluded_events`); it is:
KXNHLGOAL-26APR01ANASJ, KXNHLGOAL-26APR02WPGDAL, KXNHLGOAL-26APR03PHINYI, KXNHLGOAL-26APR04BUFWSH, KXNHLGOAL-26APR04CHISEA, KXNHLGOAL-26APR04NSHSJ, KXNHLGOAL-26APR06CHISJ, KXNHLGOAL-26APR07NSHANA, KXNHLGOAL-26APR08WSHTOR, KXNHLGOAL-26APR09MINDAL, KXNHLGOAL-26APR09WPGSTL, KXNHLGOAL-26APR11CGYSEA, KXNHLGOAL-26APR11FLATOR, KXNHLGOAL-26APR11PHIWPG, KXNHLGOAL-26APR19UTAVGK, KXNHLGOAL-26APR23BUFBOS, KXNHLGOAL-26APR28MINDAL, KXNHLGOAL-26MAR19MTLDET, KXNHLGOAL-26MAR24CHINYI, KXNHLGOAL-26MAR28NJCAR, KXNHLGOAL-26MAR28OTTTB, KXNHLGOAL-26MAR28TORSTL, KXNHLGOAL-26MAR29NSHTB, KXNHLGOAL-26MAR31WPGCHI, KXNHLGOAL-26MAY10VGKANA.

## 3. Census (listings only, done; `workers/NHLALL1_CENSUS.json`)
Source: NHLG1's Kalshi listing already in `data/nhlg1.sqlite` (kmarket) and its ESPN game table (start times). This module copies only ticker, event, volume (never `result` or any price) and matches events to ESPN games with NHLG1's matcher (no player filter). Pre-cut (close before 2026-10-03T16:00Z; the frozen last third is never fetched or joined) 1+ goal rungs (strike 0.5) with volume above 0: 15,926 in **967 matched games** (0 unmatched events); 942 not excluded; 15,475 rungs, median 15 and mean 16.4 rungs per game. At about 6 markets a minute (NHLG1 measured 603 markets in 94 minutes under 429s), 3 hours is about 1,100 markets, **about 65 to 70 games, so at most about 130 to 140 trades with the cap of 2**. The 150 trade floor may be unreachable by construction; if so the verdict is NOT_ENOUGH_DATA and I say so.

## 4. The rule (fixed now)
**Mechanism (stated in advance).** In an anytime goal scorer ladder, retail underprices depth and tail players' chances, because the quotes sum to less than the expected goals (a structural under-round of the whole ladder). No outside model. Counterparty: market makers and retail who price tail rungs from a headline rate.
**Universe.** The 1+ rungs above, games not excluded, in **md5 order of the event ticker**; a game is used only when ALL its volume-positive 1+ rungs have candles; the sample is the completed prefix when the time box ends (games are taken strictly in md5 order, passes retry failures).
**Look.** The last 1 minute candle of the market ending at or before ESPN game start minus 120 seconds with a valid two sided quote (0 <= bid < ask <= 1, ask - bid <= 0.10) (`period_interval 1`, window start-3600 to start; a game with no valid candle for a rung drops that rung). Cheap side = YES if ask in [0.03, 0.30]; else NO if 1 - bid in [0.03, 0.30]; the other side is never evaluated or printed.
**Pooled rule (+2).** Buy the cheap side at its ask on every such rung, C = 10 contracts, hard limit 0.30, held to settlement, **max 2 per game chosen by sha1 of the ticker** (lowest hash first; no price used). Fee 7% x C x p x (1 - p) rounded up to the cent per order, divided by C (x1.2 stress). Taker at the ask. Results other than yes/no dropped and counted. No control (it is the unconditional pool); a descriptive uncapped all-cheap line and by ask bucket (3-8c, 8-15c, 15-30c) is shown as information.
**Ladder-sum filter (+2).** Per game: ladder sum = sum of YES asks (at the same look, valid quote) over its 1+ rungs (games need at least 8 such rungs). **Tercile cuts are computed from the first third of the fetched games in md5 (fetch) order only**, then applied to all fetched games. The filtered rule is the pooled rule restricted to the lowest tercile (the most under-round games). Count of scorers per game and the mean sum of asks are information.
**Statistic.** Mean net per contract after fee over trades, SE and z clustered by game AND by ET event date; lower 95% bound = mean - 1.96 x game-clustered SE; PF = gross wins over gross losses after fee; win rate against mean price; halves H1 and H2 = fetched games split at the median start time; fees x1.2.

## 5. Pass bar (fixed now, before any outcome)
- **LEAD** only if n >= 150 trades AND net after fees above 0 in BOTH halves AND game-clustered lower 95% bound above 0 AND PF >= 1.5.
- **NOT_ENOUGH_DATA** if under 150 trades (reports n, games and the forward plan).
- Otherwise **FALSIFIED**. The same bar is applied separately to the pooled rule and to the filtered rule. A LEAD would not be a promotion: z bar 5.27 with the multiple-test count; no promote verb.

## 6. Time box
At most **3 hours** of candle fetching in total (1 to 2 processes, `/historical/markets/{ticker}/candlesticks`, one market per request, 0.5 s sleep, backoff on 429, honest default User-Agent, cache `/home/user/.cache/nhlall1/nhlall1.sqlite` outside the repo). Stop at the time box and score the prefix; no extension. The exact number of games is reported.

## 7. Prediction (stated before)
Expected mean net **-3c per contract** (plausible -8c to +3c), PF about 0.8, win rate about equal to or below price paid; trades 100 to 140 (so NOT_ENOUGH_DATA is the most likely verdict, about 70%). Probability of LEAD **at most 5%** (prior that cheap pools lose: CALIB1; the NHLG1 +5.6c was 18 games and z 1.7). Ladder-sum lowest tercile: no better than the pool.

## 8. Kill rules / forward plan
FALSIFIED as above ends the pooled idea. If NOT_ENOUGH_DATA, a forward read: the 225 frozen events after 2026-10-03 (about 25 a week) opened once, with the same code and cuts frozen from this sample, after the games are settled and the owner approves; no rule edit. This registration is not edited after the first candle is fetched.
