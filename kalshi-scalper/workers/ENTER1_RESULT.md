# ENTER1 result (2026-11-03): NOT_RUNNABLE at STEP 1; no outcome or PnL computed

Registration: `workers/ENTER1_REGISTRATION.md` (commit 348e326, pushed before this file). Verdict by the registered rule: `NOT_RUNNABLE`. Window: none. n: 0 trades. Win rate vs price: not computed. PF: not computed. Cost: fee 7% x C x p x (1-p) rounded up, C = 10, not applied (nothing scored). N: +2 (running about 730,062; z bar about 5.27).

## What is covered already (duplicate check)
MENT1 (earnings words, FALSIFIED PF 0.86), CHART1 (weekly Netflix, NOT_RUNNABLE), SPOTD1 (daily Spotify winner, FALSIFIED), ESPORT1, CPI1, USWEEP1/2 (generic sweeps, reached 119 of 15,663 series, rate limited; no Rotten Tomatoes, Metacritic, App Store, YouTube chart or X post-count series was among its tested series). Never touched: RT/Metacritic score markets, App Store ranks, YouTube charts, X post counts.

## STEP 1 (rule: at least 100 settled markets and 25 events, AND a keyless reference dated at the look, AND the same counting rule)
| Family (Kalshi series) | Kalshi side | Reference fetchable from this sandbox | Verdict |
|---|---|---|---|
| Rotten Tomatoes (242 series, KXRT*/RT*) and Metacritic (72, KXMC*) score thresholds | one movie or game per series, few strikes; settled counts not enumerated (API 429) | current score only; Wayback availability and CDX return nothing | no dated reference: NOT_RUNNABLE |
| Spotify daily/weekly (KXSPOTIFYD, ALBUMW, ARTISTW) | SPOTD1 covered the daily winner | kworb current day only (dated URLs 404) | covered / NOT_RUNNABLE for rank thresholds |
| Netflix Top 10 (19), Billboard (327, mostly one-offs) | weekly; CHART1 | daily rank archive unobtainable | NOT_RUNNABLE (CHART1) |
| App Store rank (KXAPPRANK*, 9 series daily) | daily | Apple RSS current only | NOT_RUNNABLE |
| YouTube charts (KXYTVIEWSD, KXYTDAILYTOPVIDEO, ~15) | daily | charts page current only | NOT_RUNNABLE |
| Box office | no Kalshi box-office series exists (only Golden Globes box-office award) | Box Office Mojo, The Numbers reachable | no market to trade |
| Wikipedia pageviews | only KXWIKIARTICLE (annual, one event a year) | Wikimedia REST works, full history | too few events (a) |
| Google Trends numbers, follower counts, subscribers | one-offs and annual (KXYOUTUBESUBS, KXFOLLOWERCOUNT*) | none dated | too few events |
| X post counts (the only family where the number is partly known AND a dated history exists): KXELONTWEETS | 111 markets, 9 events, 2025-02-21 to 2025-04-18 | xtracker.polymarket.com post feed starts 2025-11-18 | zero overlap |
| KXPOTUSTWEETS | 114 markets, 14 events (weekly 2025-04 on, monthly 2026) | realDonaldTrump on xtracker from 2026-01-21 | 6 markets, 5 events overlap |
| KXFEDTWEETS | 90 markets, 14 events (2026-06 to 2026-09) | no Fed account on xtracker | no reference |

No series meets (a), (b) and (c). Nothing was scored, no price or outcome was read, no variant run.

## What would make it runnable
1. A dated recorder (the CHART1 recorder plan, extended): daily at the look, write Rotten Tomatoes / Metacritic score and review count, App Store top 200, YouTube daily chart and kworb Spotify lists to the `quote-data` branch beside Kalshi quotes for the same series. RT/MC/App/YouTube markets have too few events per series, so the pooled sample is slow: about 1 to 2 qualifying trades a week at best, so 150 trades is on the order of 2 years.
2. For post counts: the xtracker feed already exists from 2025-11-18 (Elon, about 14,400 posts), so a forward test needs only Kalshi quotes recorded 24 hours before each weekly or monthly close of the X-count series (KXELONTWEETS, KXPOTUSTWEETS). Elon's Kalshi series stopped listing settled events in 2025-04 under this ticker; whether a newer ticker exists was not found. POTUS: monthly events, about 12 a year, about 13 strikes: under 30 qualifying trades a year, so 150 trades is years away. Frozen forward date, if the owner wants it: from 2026-12-01, first read when 150 trades exist (not before 2028).

## Probe spec
None: no positive in both halves exists. (Spec would be 1 contract, hard limit 0.30, kill at 40 fills with PF under 1.0, worst day one contract at 30c per strike, 3 strikes per event; it cannot reach 40 fills in less than about a year on POTUS tweets.)

Code: `src/scalper/enter1.py` (rule and fee only), `tests/test_enter1.py` (synthetic, passes). Caveat: the series list is a cached copy from 2026-10-30; settled counts for the 300 score and rank series were not enumerated because of the Kalshi 429 limit.
