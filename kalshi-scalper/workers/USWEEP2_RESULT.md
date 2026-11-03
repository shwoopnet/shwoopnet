# USWEEP2 result (run once, 2026-11-03): no lead; coverage was small

Registration `workers/USWEEP2_REGISTRATION.md` (first commit cdeedc7, Amendment 1 favourite half dropped, Amendment 2 series list frozen), data `workers/USWEEP2_RESULT.json`, series `workers/USWEEP2_SERIES.json`. **Tail only (ask 5 to 15c); no favourite result was computed or printed.**

## Enumeration
Bulk `/markets` (status settled, `mve_filter=exclude`, hourly close windows) gives 1,000 markets a page at about 5 to 8 pages a minute under the shared 429s, about 5,000 to 7,000 markets a minute and no series list needed; 60 days of non-parlay markets (millions) is out of reach, so 72 hourly windows (3 days) were crawled: 330,612 markets, 1,481 series seen, 635 candidates (>= 15 markets, 2 dates in the 3 days), 607 counted exactly over 60 days (7 to 10 a minute; 203 hit the 1000 page cap). Batched candle requests (up to ~8 markets each, under 10,000 candles) ran fast: 121 requests for 1,200 markets.

## Coverage
Eligible (>= 300 settled, >= 20 dates, median volume >= 100, not USWEEP1, not parlay or 15 minute): **174 series**. **Tested 62** (budget 1,200 candle markets, by volume): 60 Sports, 1 Politics, 1 Mentions; 37 W, 25 D, 0 H. **112 eligible not tested** (candle budget). Not reached: about 14,000 series that closed rarely or under 15 markets in the 3 day crawl (so no stage B count); 51 of the 62 produced at least one tail entry. Non-sports recurring series (price ladders, economics, weather) are almost all USWEEP1, 15 minute or already-covered families, so this sweep is nearly a sports sweep.

## Result
117 cells (3 looks x tail), **548 tail entries in all** (win rate 10% at 9.7c to 10c paid). Pooled net **-1.09c per contract**: look 360 min -0.77c (n 220), 1440 min -2.30c (n 200), 4320 min -0.24c (n 122), the 60 min look +9.9c on n = 6 (nothing). **0 cells meet the LEAD rule; 4 are positive in both halves and none has n >= 40 per half** (luck gives about a quarter of the cells with data). Largest z with any n: 1.70 (KXSERIEATOTAL, n 4). No mechanism cluster; no watch candidate file written.

## Verdict
N added **3 x 62 = 186**. FALSIFIED as a family for the registered tail rule on this sample (no cell reaches the deflated bar of about 5.27; pooled net is negative, as predicted). The power is low: 548 entries over 117 cells means almost every cell has n under 20, so this is coverage, not a strong negative.
Resume: `USWEEP2_CACHE=<scratchpad>/us2 python3 -m scalper.usweep2 {crawl,census,select,fetch,score}`; frozen last thirds were never fetched.
