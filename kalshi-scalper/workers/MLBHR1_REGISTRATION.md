# MLBHR1 registration: replication of the NHL "cheap anytime rung" hint on MLB home runs (KXMLBHR) and hits (KXMLBHIT)

Written 2026-11-04 BEFORE any MLBHR1 candle was fetched and before any result was joined. Worker ID MLBHR1, session "Strategy Research V2". Research only: no order, no live code, no `functions/`, no L1, no OICORE, no promote verb.
**Owner rule (strict): CHEAP SIDE ONLY (ask 3c to 30c).** No favourite-side result is computed or printed. No 15 minute crypto or gold candle is used.
**N: +4** (HR pooled +2 with its ladder-sum filter, HIT pooled +2 with its filter; the HIT arms are a small pilot but are counted). Running count about 730,387, z bar 5.27.

## 1. Duplicate check (done)
Grep of README.md and workers/ for KXMLBHR, KXMLBHIT, home run, anytime, NHLG1, NHLALL1, MLBKS1/SCOUT1, PROPS1, CALIB1, USWEEP, NEWLIST1. KXMLBKS (strikeouts, a game-log model, SCOUT1/MLBKS1: 45 treated, negative), NBA/WNBA/NFL props (PROPS1 cheap control -4.87c) and the NHL goal ladder (NHLG1: a Poisson model against the quote, 0 treated; NHLALL1: sibling, same unconditional design on NHL) are the nearest items. Nobody has priced KXMLBHR or KXMLBHIT. Not a duplicate: this is the replication of the NHL structure on a different sport.

## 2. What is expected, stated in advance
The NHL result (cheap YES +5.6c, PF 1.46, z about 1.7 on 18 games, ladder sum 3.31 against 3.88 scorers) was information only and is a selected hypothesis. **I expect it NOT to replicate:** MLBKS1 found cheap pitcher-prop rungs lose, PROPS1 found cheap player props lose (-4.87c), CALIB1 found the cheap side loses by ask bucket across categories. A home run is a rare, heavily modelled event with a deep public market (median volume in the thousands of contracts).

## 3. Census (listings only; `workers/MLBHR1_CENSUS.json`, done before registration)
Source: Kalshi `/historical/markets` and `/markets?status=settled` for the two series (listing fields: ticker, event, close time, strike, volume; never `result`, never a price). Whole 2026 season is listed (not only from late August): **KXMLBHR 2,444 pre-cut events, 43,263 volume-positive 1+ rungs (median 18 a game); KXMLBHIT 2,445 events, 43,031 rungs (median 18)**, 2026-03-26 to 2026-10-02. 62 events close at or after the frozen cut 2026-10-03T16:00Z; they are never fetched or joined. Start time is read from the event ticker (YYMONDDHHMM in US Eastern daylight time); checked against ESPN's scoreboard for 2026-09-03 (CHW at HOU: ticker 14:10 EDT, ESPN 18:10Z): equal. ESPN scoreboards are reachable keyless; the box scores are NOT needed by the rule (see 5), so the ESPN expected-HR number is replaced by the realised count among the same quoted ladder (information only).
Binding limit: Kalshi's historical candles are one market per request, about 7 to 20 a minute under 429 backoff. A fully fetched ladder is about 18 requests, so a 2.5 hour box would give about 60 full games and about 110 trades after the cap of 2, which cannot reach 150. **Registered change from the coordinator brief to make the pooled rule reachable without selection:** the 2 rungs per game are chosen BEFORE any price (the two lowest sha1(ticker) among ALL the game's volume-positive 1+ rungs), and only those 2 candles are fetched in the pooled phase. A chosen rung that is not cheap at the look (ask outside 3c to 30c, bid/ask invalid, no candle) is no trade.

## 4. The rules (fixed now)
**Mechanism.** In an anytime event ladder, tail players' probability is underpriced (the sum of asks is below the realised count of events). Counterparty: market makers who price tail rungs from a headline rate and retail who buy the favourites.
**Universe.** Pre-cut games of one series, taken strictly in md5 order of the event ticker. A game enters the pooled rule only when both its chosen rungs were fetched. HR and HIT are scored separately.
**Look.** The last 1 minute candle of the market ending at or before game start minus 120 s with a valid two sided quote (0 <= bid < ask <= 1, ask - bid <= 0.10); `period_interval 1`, window start-3600 to start. Cheap side = YES if ask in [0.03, 0.30]; else NO if 1 - bid in [0.03, 0.30]; the other side is never evaluated or printed.
**Pooled rule (+2 HR, +2 HIT).** Buy the cheap side at its ask on each chosen rung that is cheap, C = 10, hard limit 0.30, held to settlement, taker, fee 7% x C x p x (1 - p) rounded up to the cent per order (x1.2 stress). Results other than yes/no dropped.
**Ladder-sum filter.** After the pooled phase, the remaining rungs are fetched for the md5 prefix of games whose chosen rungs are done (HR only unless time remains), so those games have a full ladder. Ladder sum = sum of YES asks (valid quotes, at least 8 rungs) of the game; **tercile cuts from the first third of the full-ladder games in md5 order only**, applied to all of them. Filtered rule = pooled trades of games in the lowest tercile. Realised events per game and the mean sum of asks are information (the stated reference is about 2.1 HR a game league wide; used for description only, no rule reads it).
**Statistic.** Mean net per contract after fee, SE and z clustered by game AND by Eastern date; lower 95% bound = mean - 1.96 x game-clustered SE; PF; win rate against mean price; halves = games split at the median start time; fees x1.2; by ask bucket (3-8c, 8-15c, 15-30c) as information.

## 5. Pass bar (fixed now, before any outcome)
- **LEAD** only if n >= 150 trades AND net after fees above 0 in BOTH halves AND game-clustered lower 95% bound above 0 AND PF >= 1.5.
- **FALSIFIED** if n >= 150 and not LEAD (net not above 0 in both halves or PF under 1.5).
- **NOT_ENOUGH_DATA** if under 150 trades. Applied separately to HR pooled, HR filtered, HIT pooled, HIT filtered. A LEAD is not a promotion: the z bar is 5.27 with the multiple-test count; no promote verb.

## 6. Time box (total 2.5 hours of candle fetching, 1 to 2 processes, 0.5 s sleep, backoff on 429, honest default User-Agent, cache `/home/user/.cache/mlbhr1/mlbhr1.sqlite` outside the repo)
HR pooled 90 minutes, HIT pooled 25 minutes (cheap HIT rungs, ask at most 30c, are rare since most starters have a hit chance above 50%, so this is a pilot), HR ladder fill 35 minutes. Stop at the box and score the prefix; no extension.

## 7. Prediction (stated before)
HR pooled: 250 to 450 trades (about 70% of chosen rungs are cheap), win rate about 0.9x of the mean price, mean net -4c per contract (plausible -9c to +2c), PF about 0.7. HIT pooled: 5 to 40 trades, NOT_ENOUGH_DATA about 95%. Filters: 5 to 40 trades each, NOT_ENOUGH_DATA about 95%. **Probability of any LEAD at most 3%** (the NHL +5.6c was 18 games and z 1.7).

## 8. Kill rules and forward plan
FALSIFIED as above ends that rule. NOT_ENOUGH_DATA on a filter: forward read on the 62 frozen post-cut events plus the 2027 season (about 2,430 games a series) with the same code and cuts frozen from this sample; only after the owner approves, no rule edit. This registration is not edited after the first candle is fetched.
