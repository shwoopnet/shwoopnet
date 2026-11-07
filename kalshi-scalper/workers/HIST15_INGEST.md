# HIST15 ingest (INGEST 3, Nov 7, 2026)

Purpose: extend our Kalshi 15 minute history backwards with Kalshi's public `/historical` endpoints. Research only: no key, no order, no trading code. Only the settlement `result` field is stored; no outcome was read and no strategy statistic computed.

Script: `src/scalper/hist15.py` (`list`, `fetch`, `report`; resumable, 3 s spacing, one 6 s retry, stops after 3 consecutive failed requests). Cache: `data/hist15/<series>.sqlite` (git-ignored, verified with `git check-ignore`). Schema = `data/fresh.sqlite` (`market`, `candle`, same columns) plus `listing`, `nocandle`, `meta`, `calllog`, so `scan.py`'s `kalshi_fresh` adapter could read a file once it is pointed at it. A market is in `market` only if candles came back (as in fresh); markets with an empty answer sit in `nocandle`.

## Status: listing complete, candles only a sample

The candle fetch is the slow step and I stopped after a bounded run. **Only gold is fully fetched.** BTC and ETH are listed in full but only the newest 203 and 100 markets have candles. The ingest is resumable: `python3 -I src/scalper/hist15.py fetch KXBTC15M` continues from the newest unfetched market backwards.

Boundary used: oldest close already held in the pooled files is 2026-08-06 00:00Z for all five series (l1b/e3b, A01/A03), so the listing keeps markets closing before 2026-08-06 00:00Z (last listed close 2026-08-05 23:45Z).

Facts about the endpoints (new vs HISTORY_SOURCES.md):
- `/historical/markets` ignores `min_close_ts` and `max_close_ts` (returned Sep 7 with `max_close_ts` Aug 1). It pages newest first, 1,000 per page, so the listing walks past about 3,200 markets (Aug 6 to Sep 7) per series before the first kept row. A full BTC listing is 26 pages, about 127 s.
- Candle fields differ from the live tier: `yes_bid.close` not `close_dollars`, `volume`/`open_interest` not `_fp`. Parsed in `parse()`.
- Both `api.elections.kalshi.com` and `external-api.kalshi.com` answer. 429s on candles appear in bursts even at 3 s; about 8 percent of candle requests failed twice (retry after 6 s) and were left for the next run, never 3 in a row, so there was no hard STOP.
- **Time per 1,200 markets, measured: gold 86 min, BTC 100 min, ETH 72 min** (3 s spacing plus 429 retries; about 4 to 5 s per market). Full BTC or ETH (about 22,100 each) is about 30 hours each at this rate; XRP and DOGE were not started.

## Per series (all counts before 2026-08-06 00:00Z)

| | listed (settled, yes/no) | with candles | no candles | first close with candles | last close | candle rows |
|---|---|---|---|---|---|---|
| KXGOLD15M | 311 | 285 | 26 | 2026-07-31 19:00Z | 2026-08-05 23:45Z | 3,887 |
| KXBTC15M | 22,136 | 203 | 0 | 2026-08-03 19:00Z (listing: 2025-12-10 22:00Z) | 2026-08-05 23:45Z | 3,045 |
| KXETH15M | 22,123 | 100 | 0 | 2026-08-04 23:00Z (listing: 2025-12-10 22:00Z) | 2026-08-05 23:45Z | 1,500 |
| KXXRP15M, KXDOGE15M | not started | | | | | |

Listed markets by month (BTC; ETH within 10 of it): Dec 2025 1,566 (22 days), Jan 2,972, Feb 2,676, Mar 2,928, Apr 2,820, May 2,928, Jun 2,835, Jul 2,931, Aug 1 to 5 480. That is 239 distinct UTC dates, 96 windows a day at most (the months run 1 to 7 percent short of 96 a day, so some windows are absent from Kalshi's listing or never settled yes/no). Gold: 23 windows on 07-31, then 288 on Aug 1 to 5.

## Gaps and defect screen (counts only, over the candles fetched so far)

| | gold | BTC | ETH |
|---|---|---|---|
| gaps over 15 min between fetched closes | 7 (215 missing windows) | 8 (9 missing windows, these are fetch failures to retry, not Kalshi gaps) | 0 |
| gap over 6 h | 2026-08-01 04:00Z to 08-03 04:30Z (weekend, 24/5 market) | none | none |
| markets with under 10 candles | 32 | 0 | 0 |
| markets with 15 or more candles | 236 | 203 | 100 |
| null bid or ask close | 0 | 0 | 0 |
| crossed (bid_c > ask_c) | 0 | 0 | 0 |
| out of range (below 0 or above 1) | 0 | 0 | 0 |
| bid_c = 0 (no bid) candles | 173 | 171 | 62 |
| sentinel bid 0 with ask 0.99 or more | 30 (19 with ask 1.00) | 0 | 0 |
| markets with no two sided quote in the last 8 min | 10 | 0 | 0 |
| markets with no 6 minute candle / no 10 minute candle | 31 / 27 | 0 / 0 | 0 / 0 |

Gold's thin and empty markets are the usual early-history pattern (the series was new on 2026-07-30, so 26 of 311 returned no candles at all and 32 have under 10). BTC and ETH, in the small sample, are clean: every market has both the 6 and 10 minute candle. The sample is the newest days only, so it says nothing about December to June; the screen must be rerun after the fetch continues (`report`).

## Unseen data this leaves (never read by any registration)

Everything in this cache closes before 2026-08-06 00:00Z, earlier than any file in A01 to A13 (pool starts 08-05/06), so none of it has been read by a registration. It is all outside W1, W2, W3 and the holdout as defined in DATA_INVENTORY.md (they start 08-05). Assignment is for the analysts; counts available once fetched:

| series | windows listed (fetchable) | fetched now | independent UTC dates | span |
|---|---|---|---|---|
| KXBTC15M | 22,136 | 203 | 239 (3 with candles) | 2025-12-10 to 2026-08-05 |
| KXETH15M | 22,123 | 100 | 239 (2 with candles) | 2025-12-10 to 2026-08-05 |
| KXGOLD15M | 311 | 285 | 5 (4 with a full day) | 2026-07-31 to 2026-08-05 |

Gold gives only 285 windows on 5 dates, too few for any three window design. BTC and ETH, once fully fetched, would give about 22,000 windows each on 239 dates, roughly 2.5 times the whole current BTC book (about 8,680), which is enough for three development windows of about 80 dates each. Caveat: Kalshi's quote regime in Dec 2025 to Jul 2026 may differ from the current one (market maker participation grew), so a rule found there must still pass forward reads.

To finish: about 30 hours per crypto series at 3 s spacing, resumable in slices (`fetch SERIES --max 1200` is about 80 to 100 minutes). Newest-first order means the part adjacent to the held data arrives first. XRP and DOGE: run `list` then `fetch`; their earliest event dates were not checked.
