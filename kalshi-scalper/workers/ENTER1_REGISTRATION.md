# ENTER1 registration (Strategy Research V2, discovery lane, written 2026-11-03 before any price, candle or outcome was read; research only)

Brief: cheap side (ask 3c to 30c) held to settlement on Kalshi entertainment/culture/media/tech markets that resolve on a public, frequently updated number that is partly known at the look. Nothing here means trade; there is no promote verb.

## What was looked at before this file (disclosure; none of it is a price or an outcome)
1. The cached `/series` list (15,680 series): counts by category and by settlement source name, ticker prefixes, frequency and `volume_fp`. Entertainment 2,595 series; by source: Spotify 336, Billboard 327, Rotten Tomatoes 242, Luminate 107, Metacritic 72, Netflix 19, YouTube Charts about 15, Apple (App Store ranks) 36, IMDb 25, Google Trends 14, Wikipedia 1.
2. Reachability of reference feeds from this sandbox (HTTP status or one row only): kworb current day 200 but dated pages 404; Rotten Tomatoes and Metacritic pages 200 (current score only); Wayback availability and CDX: empty or no answer; Box Office Mojo and The Numbers 200; Wikimedia pageviews REST 200 (history works); Apple RSS charts 200 (current only); YouTube charts 200 (current only); Google Trends 400; xtracker.polymarket.com post feed 200 (Elon since 2025-11-18, realDonaldTrump since 2026-01-21, WhiteHouse since 2026-01-15; no Fed, IMF or WEF account).
3. Settled market COUNTS and event dates only (not a price, not a result tally) for KXELONTWEETS (111 markets, 9 events, 2025-02-21 to 2025-04-18), KXPOTUSTWEETS (114 markets, 14 events, weekly in 2025-04 on, monthly in 2026) and KXFEDTWEETS (90 markets, 14 events, 2026-06 to 2026-09). A full settled-market census of the 300 RT/MC/App/Billboard series was started and stopped: the shared API limit (429) made it too slow. That is stated as not done.
4. No Kalshi series for box office, Wikipedia pageviews, Google Trends numbers or follower counts exists in the series list except one-offs and annual markets (KXWIKIARTICLE annual, KXFOLLOWERCOUNT* and KXYOUTUBESUBS one-offs).

## Ledger check (stop-if-duplicate)
README and workers grepped for MENT1, CHART1, SPOTD1, ESPORT1, USWEEP1/2, CPI1, SPORTCONS1, OICORE_SHAPE_INVENTORY, Netflix, Spotify, Billboard, box office, Rotten, Wikipedia, pageviews, tweets, YouTube, app store. Covered: MENT1 (earnings words, FALSIFIED), CHART1 (weekly Netflix, NOT_RUNNABLE: no daily archive), SPOTD1 (daily Spotify winner, FALSIFIED, persistence only), ESPORT1, USWEEP1 (119 of 15,663 series reached; 13,856 not, rate limit; its sample contained no entertainment series by name in the ledger). Not covered anywhere: Rotten Tomatoes / Metacritic score markets, App Store rank, YouTube chart markets, X post-count markets (no ledger line for tweets, Elon or xtracker). Not a duplicate.

## STEP 1 selection rule (fixed now, applied to the series list and feed probes)
A series is RUNNABLE only if (a) at least 100 settled markets AND at least 25 events, (b) a keyless reference for the same period that records the number AS OF the look (a history, not today's value), reachable from this sandbox, and (c) a settlement definition that the reference measures (same account, same counting rule). No series meeting all three: verdict `NOT_RUNNABLE`, and the result says which feed or recorder would be needed. Series are never chosen by price or outcome.

## STEP 2 rule (registered for whichever series passes STEP 1; applied only if one does)
Look: 24 hours before close. Implied probability from the reference: P(count > K) = 1 - Phi((K + 0.5 - c - m) / s) with c = count so far, m = trailing 14 day mean rate x time left, s = 2.0 x sqrt(m) (overdispersion fixed now), floored at 0.01 and capped at 0.99. Buy the cheap side (YES or NO) when its ask is 0.03 to 0.30 (hard limit 0.30) and the implied probability of that side is at least 3x the ask. One contract per strike, held to settlement, at most 3 strikes per event. Control: every cheap ask in the band 0.03 to 0.30 at the same look. Fee 7% x C x p x (1-p) rounded up, C = 10, ask taker; fees x1.2 stress. Three windows by event date, last third frozen unread.

## Numeric prediction (before any data)
Mean net per contract of the rule between -6c and +1c, win rate near the ask (3x ratio mostly noise from a crude Poisson model against a market that already shows the count); PF 0.3 to 1.1. Prior that any family here passes PF 1.5 in all windows: 2%. NOT_RUNNABLE expected (about 80%).

## Kill rules
- `FALSIFIED`: mean net after fees not above 0 in both halves, or PF under 1.5 in any window, or pooled event-clustered z under the deflated bar (about 5.27), or x1.2 PF under 1.
- `NOT_ENOUGH_DATA`: under 150 trades; the result must give the months-to-go and a dated forward freeze.
- `NOT_RUNNABLE`: no series passes STEP 1.
- Frozen last-third holdout is not read unless the first two windows pass. No tuning, no second look, no variant.

## Overlap with L1
None: no 15 minute market, no gold or crypto; nothing touches `functions/`, live code, L1 or OICORE.

## N
+k = +2 (the single registered rule, two feed classes considered: a score/rank class and a post-count class). Running count about 730,060 + 2 = about 730,062 (coordinator keeps the total; z bar about 5.27). Expected read date: the STEP 1 result is written the same day (2026-11-03); a forward freeze, if any, in the result.
