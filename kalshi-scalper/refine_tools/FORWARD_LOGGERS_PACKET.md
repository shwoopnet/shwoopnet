# Forward-logger packet: six public-data recorders for owner approval (backlog rows 52, 54, 55, 56, 57, 60)

Date 2026-11-10. Research only. Nothing here changes an order, size, limit or exit, and nothing is built until the owner says yes. Each is a GitHub Actions recorder like `record-quotes.yml` (public data, no key, no secret, no order, built-in token pushes CSV to the `quote-data` branch under its own folder, never main, not published with the site). Same pattern as R6, so a stop is deleting one workflow. A "yes" per row (or a subset) is the decision requested. Sources: refine_tools ROW54_60 spec, ROW55_56 feasibility, w_feas rows 52 and 57, row 49 registration.

Income lens (INCOME_PAGE_DEC9): today is about $70 to $100 a month and $2,000 needs 20x to 30x the size or an unmeasured edge. A recorder earns nothing; it is only worth it if it can find a NEW edge on a market with volume. None can promise one.

Row 49 (weather highs): not a logger. Registered Nov 10, scoring not yet run; history exists (Kalshi historical plus IEM MOS archive), so it needs no recorder. Row 52 would be its twin on rain.

## Ranking (value per cost, best first)

1. Row 55, OKX liquidation cascade vs Bitcoin 15 minute. Cheapest, one keyless GET, lands on a market we already trade.
2. Row 52, rain vs NWS PoP. Only weather-family row that can reach n in weeks; weather history for row 49 already tests the idea cheaply, so 52 is the forward twin.
3. Row 56, sports winner vs a non-Kalshi line. Biggest Kalshi volume (best fit for the income goal) but the weakest data terms.
4. Row 60, Fed press conference word markets. Cheap but about 8 conferences a year.
5. Row 54, Fed curve vs KXFED. Cheap but about 8 meetings a year; n never arrives.
6. Row 57, poll aggregate vs approval markets. No permitted archive; recommend DROP.

## Per row

| Row | What to log, cadence, fields | Weeks to n>=40 per half | Terms risk | Overlap with L1 |
|---|---|---|---|---|
| 55 | OKX /public/liquidation-orders BTC-USDT SWAP (ETH optional). Poll hourly (OKX keeps about 17 h, 100 rows a call, page back with after= and dedupe by ts+bkPx+sz). Fields: ts_ms, side, posSide, sz, bkPx, ctVal. Plus per KXBTC15M window: close time, bid/ask at the 6 minute look, result. About 24 job runs a day, or fold into the quote recorder's 4 hour job. | About 8 weeks for about 100 cascade events (cascades cluster, so count windows, not liquidations); n 40 per half is the same 8 weeks, tight. | Low: public keyless OKX endpoint. Binance (451) and Bybit (403) unusable. | YES. KXBTC15M is OICORE's market (Bitcoin is paused in L1 but still read). A later rule would sit under the direction lock and shared 12% stop; log only now. |
| 52 | Twice a day per city: ts, series, ticker, yes_bid/ask, last, volume, close_time, window start/end, NWS gridpoint PoP + generatedAt, IEM GFS MOS p06/p12 + runtime, result after close. Series KXRAINDNYC, SFO, AUS, DC, NOLA, MKE, SATX. | 6 to 8 weeks, IF 4+ cities list daily markets; only 5 KXRAINDNYC markets exist in 2026 so listing is unverified, could be never. Spec says 40+ days over 3+ cities for a pilot. | Low: api.weather.gov (public, needs a User-Agent) and IEM (robots allow /api). MOS is a proxy for the NWS PoP. | NO. Weather, no shared market or window. |
| 56 | Every 10 min on game days: ESPN scoreboard (nba, nfl, nhl, optional ncaam) for events not started: ts, event id, start, DK moneyline open/close, spread, total; same moment Kalshi yes bid/ask for both winner markets; result after. Vig-free probabilities offline. | About 8 weeks for NBA (150 games per league wanted; 40 per half is about 80 games, so NBA about 4 weeks, NHL similar). Single book, so no consensus. | HIGH: unofficial ESPN endpoint, no license, DraftKings lines linked to bet slips, schema can change, no archive. Personal low-rate research only; the repo is public, so the data branch would republish those lines: needs an owner call. | NO. Sports, different markets. |
| 60 | Per press conference, before it: KXFEDMENTION-26DEC per word: ticker, word, yes_bid/ask, rules hash; trailing 8 conference base rate from earlier transcripts (Warsh-only and all); after: result per word. | Conference level: never (8 a year, first Dec 2026). Word level: maybe 3 conferences for 40 correlated rows. Not a real n in under a year. | Low (Kalshi public, Fed transcripts public). Chair change makes base rates thin. | NO. |
| 54 | Daily, 7 days before to 1 day before each FOMC (next Dec 8-9, then Jan): date, KXFED/KXFEDDECISION per market: ticker, bid, ask, volume, OI; DGS2, DTB3 (FRED), EFFR (NY Fed), days_to_decision, spread. | Never at event level (about 8 a year; 80 events is 10 years). Daily rows are one event repeated, so n 40 per half is not an honest count. | Low: FRED and NY Fed public. | NO. |
| 57 | Daily 10:00 ET: aggregate value and its 7 day earlier value as published, bracket bid/ask, close_time, result (KXAPRPOTUS weekly, KXTRUMPAPPROVE daily). | Weekly 80 weeks; daily rows are not independent. No honest n inside a year. | HIGH: RealClearPolling returns a bot challenge, natesilver.net disallows ClaudeBot, 538 is closed. No permitted source. | NO. |

## Cost and risk (all six)

- Firestore: 0. Kalshi key: none. Orders: none. Runner: free on a public repo; storage under about 50 MB a month per row (55 and 56 are the largest); each adds a tests gate like R6's FB1 to FB11 (public hosts only, no key, branch fixed, auto-stop date).
- Each should carry a built-in stop (suggest 60 days, or until n is reached) and a pre-registered bar written BEFORE the first row: profit factor 1.3 or better in each half after fees and the deflation for N tried (about 425,000, z bar about 5.2 for the shadow bank), a named counterparty, and n 40 per half or the verdict is DATA_LIMITED.
- None can hold a position at the same time as L1 except row 55 (OICORE's Bitcoin 15 minute market). Any later rule from 55 would need the second-slot review path.

## Recommendation and decision requested

Plainly: these recorders are research only and do not run without an owner yes. Recommended approval: 55 and 52 now (cheap, reach n in about 8 weeks, low terms risk). 56 only if the owner accepts the ESPN terms risk and a public data branch (or keep the file out of the public branch). 60 and 54 only as a tiny add-on for the Dec 8-9 FOMC (a few lines each, no n). 57: drop. Reality check for the income goal: even a pass reaches a shadow candidate, not a live strategy, and the first possible read of 55 or 52 is about early January 2027.
