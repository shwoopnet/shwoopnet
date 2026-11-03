# INCENT1 result (2026-11-03, Strategy Research V2 worker; registration `workers/INCENT1_REGISTRATION.md`, sha256 6e84fd878aa46c563bed62a3771d34b0d1b10de4f9b63ebb136e0d2724300242, pushed before any book was sampled)

Code `src/scalper/incent1.py`, `incent1_sample.py`, `incent1_analyze.py`, tests `tests/test_incent1.py` (synthetic, 6 pass). Discovery only: nothing placed, no reward ever paid to anyone here. Sampling: 240 markets (seeded stratified sample of the active programs, 6 pool bands), 3 passes of book and market reads, 21:18 to 23:04 UTC on one Tuesday; 231 scored, 9 `no_price`. No weekend, no days: time-of-day and weekday variation are NOT covered.

## Programs found
`GET /incentive_programs` is public and keyless: **4,387 active** liquidity programs (on 4,387 markets), **6,948 upcoming**, none of type volume. All have discount factor 0.5, target 1,000 contracts (70 with 2,500), no per-account cap; periods 1 to 14 days (mostly 6 to 7). Pool per market per day: median $14.2, p10 $8.5, p90 $36, max $168; about $92k a day in total. Examples: KXRT (Rotten Tomatoes scores, $100 a day), KXYTVIEWSW (YouTube views), KXFEATURE, KXSTATELEG, KXCPIYOY, KXNFLTRADE, KXVOTEGENERAL (upcoming, $80 to $200 a day), KXLLM1, KXAAAGASM. Not the 15 minute crypto or commodity series L1 trades.

## Qualification (Help Center, as published)
Most US individual members; not affiliates, brokers, FCM customers, non-US. SSN on file above IRS thresholds. Snapshot once a second, both sides must show the target depth, payout rounded down, **under $1 per program is not paid**, paid after the program ends, Kalshi may change or end it at any time. A $100 lane clears the $1 floor in 70% of sampled markets (70 of 231 lanes earned 0, 3 of them because the book never had two-sided target depth). Small accounts are NOT excluded; minimum size is nothing beyond the $1 floor. No API restriction found on resting limit orders.

## What the books look like (the finding that matters)
Median resting depth is **13,775 YES and 14,708 NO bids** against a target of 1,000; 228 of 231 markets have 1,000+ both sides. The programs already attract professional depth, so the pool is shared with it; our $100 lane (q = up to 100 contracts a side at the reference level) holds about 0.3% of the pool per day at the median. Median 24h volume is **0** (most of these markets do not trade), which is why a rest-and-collect lane has few fills; it is also why fills, when they come, are the news.

## Table (per $100 resting, per day; lanes holding under $100 are not scaled up)
| case | reward median / p75 / p90 | AS cost median | net median / p90 | lanes with net > $0.10 | in 2+ of 3 passes |
|---|---|---|---|---|---|
| PESSIMISTIC (verdict: full-size crossing order in Q, fills x2, AS pess) | $0.31 / 0.66 / 1.58 | $0.00 | $0.19 / 0.86 | 124 of 231 (53.7%) | 124 |
| central | $0.31 / 0.66 / 1.58 | $0.00 | $0.26 / 1.13 | 144 (62.3%) | 139 |
| optimistic (Q clipped at target, AS gain) | $1.30 / 1.65 / 3.25 | $0.00 | $1.29 / 3.26 | 228 (98.7%) | 228 |
Pool bands (daily pool $3 to 12, 12 to 14, 14.1 to 14.2, 14.2 to 14.5, 14.5 to 19, 20 to 142): pessimistic net median 0.28, 0.33, -0.01, 0.22, 0.20, -0.01; the biggest pools are NOT the best per dollar because the big ones (KXRT) have the deepest competition and the most volume (fills and AS cost).
**Registered verdict by the code: VIABLE_SMALL_PROBE** (124 lanes, 53.7%, stable over passes).

## Read it honestly (why this is not yet a result)
1. **The registered verdict case is volume driven, and median volume is 0**, so most lanes pay "no adverse selection" because no fill is modelled. My fill-floor stress (information, not registered: each lane's two sides are filled in full once during the program period, volume ignored, same cost bounds) gives **46 positive lanes of 231, median net -$0.42 per $100 per day** under the pessimistic cost and median -$0.06 central. A rest-and-collect lane is a short option on a news jump. The mid-band cost (3.0c per fill pessimistic) is an UNMEASURED assumption; only the tail bids at 15c or less use MAKERTAIL1's measured (and itself NOT_ENOUGH_DATA) bounds.
2. **Q is modelled from one book snapshot** and counts a size-weighted sum up to the target depth; whether the real scorer counts a crossing order in full, and how much liquidity appears and disappears between snapshots (market makers re-quote every second), cannot be known from a few reads. The top lane (KXRT-GOD-90, 13% of a $100 a day pool for $93) shows the risk: the model gives it a big share because the first 1,000 contracts of depth are thin relative to 46k behind them.
3. Three passes in 106 minutes of one Tuesday evening. Pools and books change by program week.
4. Clarification of one choice made after seeing pass 0: a lane holding under $100 is not scaled up to $100 (the first code scaled a $3 lane by 33x; that was a bug in the conservative-direction sense, fixed before any pass was final). All nine numbers above are the final code.
5. Any fill is inventory held to settlement; this is a market-making lane. Not a price edge.

## Probe spec (only the smallest honest one; the owner decides; needs paid-reward evidence, not a model)
Goal: measure the actual paid reward against this model, not make money. Resting $200 total in two markets chosen by rule (31 lanes were positive in 2+ passes, cap at least $20, and positive in the fill-floor stress, pessimistic): e.g. `KXTOKENUSE-26NOV09-T203` (pool $30.8 a day, YES 0.55 and NO 0.15, cap $61, modelled reward $3.85, stress net +$2.56 per $100) and `KXYTVIEWSW-TAT26NOV08-2.5M` (pool $12.9 a day, YES 0.93 and NO 0.01). Hard prices at the reference level of each side, 100 contracts maximum a side, post both sides, cancel both on any fill of one side beyond 20 contracts or on the last day before settlement; kill: 5 days with total paid reward under $2, or net negative after 20 fills. **Worst day $:** the full loss of one filled side, the market's two cheapest sides cost at most $61 and $94 of resting capital (both sides together); expected fills a day about 0 to 2 contracts (volume 0 to 14). Daily reward modelled $0.3 to $4 for the lane (central $0.31 per $100). Payment arrives only after the program ends, so the first evidence is 6 to 7 days away. Not a 15 minute series.

## Verdict
**VIABLE_SMALL_PROBE by the registered rule, with the fill-floor stress against it (median net negative), so it is a candidate for a tiny paid-evidence probe, not an estimate of income.** The registered prediction (central $0.50 per $100 per day, 30% positive, probe viable 45%) was too high on reward (observed $0.31) and too low on positive share (53.7%, because volume 0 removes the cost). Tries: 1 rule, N +2.
