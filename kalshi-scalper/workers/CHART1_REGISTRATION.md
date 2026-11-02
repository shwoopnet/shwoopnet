# CHART1 registration (Strategy Research V2, written 2026-11-02 BEFORE any Kalshi candle was downloaded, any settled value was joined to a ranking, or any PnL was computed; research only)

Owner direction: new non-L1, non-OICORE families in parallel; no new approval needed for a test on existing public data. Nothing here means trade. No live code, functions/, L1 or OICORE is touched.

## Ledger check
README grep for Netflix, Billboard, Spotify, FlixPatrol, KXTOPSONG, chart1: no hit. Not a duplicate. (Entertainment-category series list was read for tickers only.)

## Family and counterparty
Kalshi weekly Netflix rank markets (KXNETFLIXRANKSHOWGLOBAL, KXNETFLIXRANKSHOWGLOBAL2, KXNETFLIXRANKMOVIEGLOBAL, KXNETFLIXRANKMOVIEGLOBAL2, KXNETFLIXRANKSHOWRUNNERUP, KXNETFLIXRANKMOVIERUNNERUP and the US siblings), weekly. Second leg only if time allows: KXTOPSONG / KXTOPALBUM (Billboard weekly) and KXSPOTIFYW. Counterparty: retail traders who do not read the daily lead indicator (the daily top 10 on Netflix and FlixPatrol, the Spotify daily chart) that leads the weekly Tuesday result by several days. Why it may not exist: the market makers on these markets read the same daily pages.

## Data source
Netflix weekly files (keyless): https://www.netflix.com/tudum/top10/data/all-weeks-global.tsv (reachable, weekly only, settlement truth) and all-weeks-countries.tsv. Daily rankings (the signal): Netflix publishes only the rolling current day; FlixPatrol returns HTTP 403 from the sandbox; kworb.net Spotify daily is reachable but only the current day. No archive of daily ranks with history is on file or reachable. Kalshi candles: historical endpoint, yes_bid.close / yes_ask.close (live endpoint close_dollars).

## Universe (chosen on cost and liquidity and metadata only)
Weekly Netflix global show and movie rank series above, events with volume of at least 0.5M contracts. Fixed before any outcome is read.

## Exact rule and entry time
Entry time: Friday 12:00 UTC of the Monday-to-Sunday ranked week (about 3 days before the Tuesday release). Signal: the title holding rank 1 in the daily Netflix top 10 (global) on the last N=4 days Monday to Thursday, using the mode of those days. Buy YES on that title's rank-1 contract at the ask when ask <= (empirical hit rate of the daily-lead rule, fit on the discovery window only) - 0.08 after the fee. Exactly one contract, one entry per event, hold to settlement. No look-ahead: daily ranks only through Thursday of that week.

## Numeric prediction (written before scoring)
The daily lead rule hits rank 1 about 85% of weeks; market ask at Friday is about 70 to 80c on those titles; an edge of at least 8c exists on at least 20% of events; profit factor of the rule is at least 1.5 in each of three time windows after the fee. Prior that this holds: 5%.

## Fee
7% x C x p x (1-p) rounded up to the cent per order, taker at the ask, C = 1 per order (C = 10 for the lock arithmetic only).

## Windows, holdout, kill criteria
Three equal time windows by event close date; the last third is a frozen HOLDOUT, read once, only if the first two pass. FALSIFIED if profit factor < 1.5 in any of three equal windows after fees or the deflated bar (z about 5.27) is missed. NOT_ENOUGH_DATA if fewer than 150 settled trades. NOT_RUNNABLE if the daily ranking history cannot be obtained for the weeks traded: then NO outcome or PnL is computed, and the family becomes a FORWARD registration.

## Forward fallback (recorder described, not built)
1. Once a day at 23:30 UTC GET the Netflix Tudum top 10 daily lists (global show, global movie, US show, US movie) and the Spotify global and US daily chart (kworb), keyless.
2. Append (date, list, rank, title) rows to a CSV on the `quote-data` branch under chart/.
3. Once a day also GET the public Kalshi quotes for the open weekly rank events (best bid, ask, size) at the same time.
4. Gzip, push with the built-in token, never to main.
5. Scoring afterwards joins daily rank 1 on Mon to Thu, the Friday 12:00 UTC quote and the Tuesday settlement.
Earliest forward read: 150 settled trades needs about 150 weekly events; across about 6 Netflix series that is about 25 weeks of recording, so a first honest read is about 2027-05-03 at the earliest. An early information look (no verdict) is possible at 2026-12-14 once 6 weeks are on file.

## Overlap with L1
None. Weekly entertainment contracts held to a Tuesday settlement; L1 trades only 15 minute crypto and gold markets (L1_SERIES). No shared position, window, loss stop or capital rule; the slot library stays inert.

## Tries (N)
+2 (Netflix family, Billboard/Spotify leg). Running count after: about 728,700 (z bar about 5.27). Every result is quoted with window, n, cost, N.
