# RISK1 result: the account under the current live rules, day-block bootstrap of the history

Worker RISK1, 2026-10-29, run once as registered (`workers/RISK1_REGISTRATION.md`, pushed before the run). A risk estimate, not a strategy test: no pass bar, no verdict on an edge. Count: 1 try. Code `src/scalper/risk1.py` (`python -m scalper.risk1 run`); full output in `data/risk1_result.txt` (not committed). Nothing here changes a live rule.

## What was simulated (rules from origin/main, 2026-10-29)

Gold (ladder: cap = target at the start, then +1 per 3 days toward floor((cash - savings)/43), at most 40; the 2% of cash rule; add-on from the pool clamped to a quarter of the base; lock 50), Dogecoin 5, Ethereum 1 on the smooth climb only. Bitcoin, XRP and the probes paused (so no 10 minute look is left). Gold quiet 20:00 to 24:00 CT. Band 0.88 to 0.97 at the 6 minute look, one crypto order per window (Dogecoin first), 5.5% window cap of the sizing base, 12% loss stop over 24 hours with open orders counted as lost (checked before each window and one minute after its orders), 25c exit (first later valid candle with the bought-side bid at or under 25c, at that bid, fee at C), pool and savings by `foldSkim` (everyWin). Fills: candle ask plus live slippage (gold +0.60c, Dogecoin +0.86c, Ethereum +0.87c), fee rounded up per order at the real count.

Data: 84 full US Central days, **2026-08-06 to 2026-10-28** (the files now hold 84, not 69). Thirds: T1 Aug 6 to Sep 2, T2 Sep 3 to Sep 30, T3 Oct 1 to Oct 28 (28 days each). 10,000 paths of 90 days per row, whole CT days resampled; 30 and 60 days are the first 30 and 60 days of the same paths. Seed 20261029. Net = final balance (savings included) minus start.

## Step 1: what each market does at 1 contract (live filters, one crypto per window, slippage, fee at C = 1)

| Market | Days | Entries | Lost at settle | 25c exits (all losses) | Mean net c/contract, ALL / T1 / T2 / T3 | PF ALL |
|---|---|---|---|---|---|---|
| Gold | 84 | 1,386 | 38 | 33 | +0.98 / +1.48 / +0.20 / +1.22 | 1.22 |
| Dogecoin | 84 | 2,514 | 32 | 126 | -0.47 / -0.43 / -0.51 / -0.47 | 0.91 |
| Ethereum (smooth, window not taken by Dogecoin) | 84 | 62 | 0 | 1 | +1.98 / +3.46 / +4.29 / -4.17 | 2.33 |

At C = 1 the fee rounds up to a full cent; at the real sizes it is cheaper per contract, so inside the simulation (300 path check, 30 days, $528) gold made **+1.53c a contract** (about 13.6 contracts an order, 486 orders, +$101 a path), Dogecoin **+0.04c** (+$1.9), Ethereum +1.9c (+$0.4). **Essentially all of the expected profit is gold.** Of the 126 Dogecoin exits, 30 would have won at settlement (gold: 5 of its 42 in-band exits before the quiet-hour filter; Ethereum: 15 of 126 before the smooth gate). 0 entries had a zero-volume decision candle, so the zero-volume variant is identical to the main run.

## Step 2: the table (all history days, ALL)

STOP_DAY = after a stop, off for the rest of that CT day and restarted (reseeded) next day; STOP_END = off for the rest of the path. Stop cost = mean net with that rule minus mean net with no stop. DD = worst peak-to-trough fall of the balance.

| Start | Horizon | p5 | p25 | median | p75 | p95 | mean | stop fires at least once | worst DD median / p95 | DD % median / p95 | ends below start | stop cost DAY / END |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| $528 | 30d | -16 | +50 | +99 | +149 | +220 | +100.1 | 1.8% | $52 / $93 | 8.7% / 16.1% | 7.9% (END 8.5%) | -$0.2 / -$0.9 |
| $528 | 60d | +37 | +136 | +211 | +286 | +404 | +213.0 | 3.9% | $69 / $117 | 10.4% / 18.5% | 2.1% (END 3.1%) | -$0.4 / -$4.3 |
| $528 | 90d | +103 | +232 | +330 | +435 | +599 | +337.6 | 5.5% | $80 / $133 | 11.2% / 19.3% | 0.5% (END 1.8%) | -$0.7 / -$10.1 |
| $1,028 | 30d | -9 | +112 | +200 | +291 | +420 | +202.3 | 1.0% | $94 / $168 | 8.0% / 14.7% | 5.9% (END 6.3%) | -$0.2 / -$1.0 |
| $1,028 | 60d | +105 | +288 | +423 | +564 | +790 | +431.1 | 1.8% | $124 / $209 | 9.6% / 16.7% | 1.3% (END 1.9%) | -$0.3 / -$4.1 |
| $1,028 | 90d | +246 | +486 | +670 | +868 | +1,170 | +684.8 | 2.6% | $146 / $238 | 10.3% / 17.4% | 0.3% (END 1.0%) | -$0.5 / -$9.6 |

Percentiles are STOP_DAY; STOP_END differs from it by at most $37 at the 5th percentile (90 days) and $5 at the median. Gold's cap at the end averages 12.3 / 13.6 / 14.9 ($528) and 24.6 / 27.1 / 29.9 ($1,028).

## Thirds resampled alone (STOP_DAY; STOP_END and no stop within $14 of the mean everywhere)

| Days | Start | Horizon | p5 | median | p95 | mean | stop at least once | worst DD median / p95 | ends below start |
|---|---|---|---|---|---|---|---|---|---|
| T1 | $528 | 30d / 90d | +30 / +292 | +169 / +594 | +313 / +931 | +170 / +599 | 1.9% / 4.0% | $54 / $93 ; $83 / $131 | 2.1% / 0.0% |
| **T2 (weakest)** | $528 | 30d / 90d | **-68 / -80** | **+39 / +118** | +156 / +349 | +41 / +126 | 0.0% / 0.5% | $65 / $123 ; $106 / $189 | **28.1% / 16.9%** |
| T3 (last) | $528 | 30d / 90d | +11 / +146 | +94 / +328 | +188 / +531 | +96 / +332 | 0.0% / 0.0% | $36 / $61 ; $52 / $81 | 2.9% / 0.1% |
| T1 | $1,028 | 30d / 90d | +94 / +652 | +337 / +1,187 | +596 / +1,787 | +339 / +1,200 | 0.1% / 0.2% | $94 / $159 ; $149 / $230 | 1.0% / 0.0% |
| **T2 (weakest)** | $1,028 | 30d / 90d | **-126 / -123** | **+78 / +247** | +301 / +694 | +82 / +258 | 0.0% / 0.0% | $120 / $225 ; $194 / $340 | **26.7% / 15.3%** |
| T3 (last) | $1,028 | 30d / 90d | +37 / +329 | +194 / +669 | +370 / +1,064 | +196 / +679 | 0.0% / 0.0% | $66 / $109 ; $97 / $147 | 1.9% / 0.0% |

The 60 day rows are in `data/risk1_result.txt`. **The weakest period is T2 (September), not the last third**: gold earned only +0.20c a contract at C = 1 there. October (T3) was a good gold month and had no stop in any path.

## Unregistered sensitivity (information only, labelled as such): gold slippage

The result rests almost entirely on gold's edge of about +1.5c a contract at size, and a 13 to 30 contract order may pay more than the +0.60c measured on today's sizes. Same paths, STOP_DAY, ALL days:

| Gold slippage | Start | 30d median (p5) | 30d below start | 90d median (p5) | 90d below start | 90d stop at least once |
|---|---|---|---|---|---|---|
| +0.60c (live) | $528 | +99 (-16) | 7.9% | +330 (+103) | 0.5% | 5.5% |
| +1.5c | $528 | +38 (-66) | 27.6% | +120 (-65) | 15.6% | 10.8% |
| +2.5c | $528 | -19 (-113) | 62.7% | -58 (-196) | 71.7% | 22.0% |
| +0.60c (live) | $1,028 | +200 (-9) | 5.9% | +670 (+246) | 0.3% | 2.6% |
| +1.5c | $1,028 | +79 (-108) | 24.6% | +246 (-91) | 12.8% | 5.4% |
| +2.5c | $1,028 | -38 (-203) | 63.9% | -116 (-359) | 73.7% | 8.1% |

About 2c a contract of extra cost on gold turns the expected result negative.

## Reading it

- The $1,028 rows are close to twice the $528 rows in dollars, with the same percentage drawdowns (median about 8% to 11%, 95th percentile about 15% to 19%) and a lower stop rate, because gold's size is the only thing that scales and the window cap and stop scale with it.
- The 12% stop rarely fires (1% to 6% of paths over 30 to 90 days on all days) and costs almost nothing when the bot restarts the next day (-$0.2 to -$0.7 of mean). Left off for the rest of the path it costs $1 to $10 of mean over 90 days. It is not what bounds the typical bad month: the typical worst fall ($52 to $146) happens slowly, under the stop.
- Dogecoin at 5 contracts adds roughly nothing in this history (+0.04c a contract at size, PF 0.91 at C = 1 after slippage and the 25c exit), against +2.66c a contract in its live record so far. Ethereum is about 1 order every 4 days.

## Assumptions, plainly

1. The future looks like these 84 days, resampled. The history's mean is the main assumption; one bad month in three (T2) shows what a weaker gold month does.
2. Every order fills in full at the candle ask plus the 30 day live slippage per market; no market impact, no depth limit at 13 to 30 gold contracts (see the slippage table); no missed fills.
3. History outcomes (Kalshi results) and candle quotes; the 25c exit at the candle's closing bid with a valid quote (spread at most 10c), never inside the minute.
4. The owner restarts after the deposit, so the ladder starts at its target (12 at $528, 23 at $1,028); after a STOP_DAY stop the restart reseeds the same way.
5. Not modelled: shards (all cash assumed usable), the 200 orders a day limit, hand trades, Flatten, Bitcoin or XRP coming back, rule changes during the horizon, weekday order (days are drawn at random, so weekends land anywhere, gold has none on Saturday).
6. Days are resampled independently, so a run of bad days longer than the history shows is under-represented.

Prediction check (registered before the run): median 30 day net at $528 predicted +$60 (+$20 to +$120), measured +$99; stop at least once predicted about 10%, measured 1.8%; share below start predicted 10% to 20%, measured 7.9%; T3 predicted lower than ALL, measured about equal (T2 is the weak third); stop cost predicted small, measured -$0.2.
