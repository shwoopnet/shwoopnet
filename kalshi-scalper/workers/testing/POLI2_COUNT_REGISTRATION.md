# POL-i2 overnight staleness: count step (T2-2). Registration confirmed, pins declared, scorer and job committed before any data (Testing Desk, Nov 12, 2026)

No Kalshi request was made to write this. No outcome, settlement result or exit price is used by anything below. No live account figure.

**Counts:** registered 1 (the card), pulled 0 of 3 stages, scored 0, closed 0. Waiting on: Main to dispatch stage 0 (`POLI2_SERIES`, 1 request).

## The registration (not mine)

Row POL-i2 of `kalshi-scalper/refine_tools/POLITICS_CARDS_NOV11.md` on `claude/refine-live` (worker P2, Nov 11, "registered BEFORE any scoring"; unchanged since: that file's latest change on the branch is its Nov 11 commit, and the ranking by Desk B on Nov 12 quotes it without changing it). The rule: at 22:00 ET close take the YES mid of each liquid politics market (at least 200 contracts of settled volume in the prior 7 days, fixed from the list); at 07:00 ET, if the price moved 5c or more overnight and the ask is still within 1c of the 06:30 ET quote (the quote did not yet follow), buy the direction, side priced 10c to 90c, one per market a day; exit 24 hours later at the bid. Follow arm is the card; fade is a control; the better arm is not chosen after the fact. **Kill: PF under 1.0, or fewer than 40 qualifying gaps per half.** Data: hourly candles. Common bars of the card file: PF 1.3 in both halves, n at least 40 per half, per-event clustering, deflation N about 7,950 on the card (the Head's current bar is z 5.46 on N about 2,113,000 and cash PF 1.5 in three windows; this step claims nothing against either).

This step is only the first half of the card's own test line ("count qualifying gaps, then the follow and fade arms"). It stops at the count. Count step try cost: 0 tries added (a count is not a test); the follow and fade arms would be the tries, charged only if the count clears and the Head orders them.

## Pins I had to declare (the card is silent or hourly candles cannot give it); all fixed in `poli2_count.py` before data

1. **Universe:** every series Kalshi tags category Politics (one request), not a hand list. If the answer is truncated or holds more than 400 series I stop and ask you.
2. **Window and held-out:** markets that closed 2025-11-05 to 2026-11-04. `HELD_OUT_FROM = 2026-11-05T00:00Z` is a date constant in code; nothing closing later is listed or requested, so it stays unread for a scoring step.
3. **Liquid:** lifetime volume of 200 contracts or more in the list (a pre-filter to save requests), then the card's own rule (200 contracts in the 7 days before 22:00 ET) on the candles.
4. **Deviation from the card, flagged:** the 06:30 ET quote does not exist in hourly candles. "Not yet followed" is the proxy |ask(07:00) minus ask(06:00)| at most 1c (bid for a NO buy). The count is reported on that strict basis and on a loose basis without the proxy; the kill uses the strict one; if only the loose count clears, you decide.
5. **Qualifying gap:** two-sided closes at the candles ending 22:00 ET (day D) and 06:00 and 07:00 ET (D+1); |mid move| at least 5c; side bought priced 0.10 to 0.90 at 07:00; liquid; one per market per day. Clusters (series, date) and the number of series with a gap are reported with the count, because markets of one event are one story. Gaps whose market closes within 24 hours of the entry are counted separately (their exit would be a settlement).
6. **Halves:** the qualifying gaps in date order, first half the first floor(n/2).
7. **Label:** below 100 gaps "no evidence at n = x". The count is not a result.

## AMENDMENT 1 (Nov 12, 2026, before any data; the Head of R&D's rulings of 16:55Z; nothing else changes)

1. **No stage 0.** `POLI2_SERIES.json` is deleted from this branch. The Politics series list is read from Desk B's CENSUS_LISTING pull (the whole series list with categories) when it lands, at zero extra requests. `poli2_count.py build-s1` takes that folder.
2. **Window halved on purpose.** The count uses only markets closing after 2026-09-12 and before the 2026-11-05 held-out constant. This halves the sample on purpose, to fit the request budget; there is no `/historical` call at all now. It also makes pins P2 above read "(2026-09-12, 2026-11-05)".
3. **Budget.** Stage 1 (one live list per series, at most 3 pages each) plus stage 2 together must be 400 requests or fewer for the Head to place the count in the dispatch order; `build-s2` caps itself at 400 minus the stage 1 request count and drops the lowest-volume markets (reported) rather than exceed it; if stage 1 alone is over 400 it stops. The exact total goes to the Head once the census file lands.
4. **06:30 ET deviation accepted.** "Not yet followed" = the ask at the 06:00 and 07:00 ET hourly candles within 1c. Strict and loose are both reported, the kill reads strict, and the result states that the registered instant (06:30 ET) does not exist at hourly resolution.
5. **Count only, no profit figure.** Fewer than 40 qualifying gaps in either half closes the card without a further read.

## AMENDMENT 2 (Nov 12, 2026, before any POL-i2 data; the exact total the Head asked for)

The census pull landed (`kalshi-pull-data` `pull/CENSUS_LISTING/2026-11-12T1703Z_43265329747`). Its `series_Politics` answer is **complete** (2.98 MB, not truncated, valid object, no cursor): **2,469 Politics series**, of which 1,353 are `one_off`, 976 `custom`, 60 `annual`, 34 `monthly`, 33 `weekly`, 12 `daily`. One list per series would be 2,469 requests, far over the 400 budget, and a one-off series has no repeating overnight structure. **Pin P1 changes: the universe is the Politics series with frequency daily, weekly or monthly = 79 series.** Stated plainly: this is a floor, not the card's universe; a liquid one-off or custom series (for example an approval or nomination series) is left out, so a count below the kill line closes only this universe. (The census also shows only 16 Politics series had any market settle on Nov 10, so "the 100 most liquid" does not exist.)

**EXACT REQUEST TOTAL: stage 1 = 79 requests, job cap 100 (21 slack for second pages)** (`kalshi_pull_jobs/POLI2_LISTS.json`, built from that answer, passes `--dry-run`; one live list per series, closes 2026-09-12 to 2026-11-04, at most 237 if every list paged three times), **stage 2 capped at 400 minus the stage 1 requests actually sent, 300 at the worst** (the builder subtracts them from 400 and drops the lowest-volume markets, reporting the number dropped). So the ceiling is 400 and the stage 1 job costs 79 now.

## AMENDMENT 3 (Nov 12, 2026, before any POL-i2 data; ruled by the Head of R&D at 17:58Z; wording credited to Desk B's duplicate POL-i2 registration, which the Head withdrew and which never read data; this registration is the one that stands, and Desk B's own wording is still to be reconciled when it arrives)

1. **The unit of the kill is the SERIES-MORNING, not the gap.** Several markets of one event moving together count once. CLOSED if fewer than **40 series-mornings with a qualifying gap in either half** (halves by date). Gaps are still reported beside.
2. **A cost kill.** CLOSED if the **median round trip at the entry hour is above 5c** (the whole spread at the 07:00 ET entry candle plus two taker fees of 0.07 x mid x (1 - mid), Forensics' definition in `HOW_TO_PRICE_A_PAPER_TRADE.md`).
3. **The card's premise is not tested.** A quote that has not yet followed cannot be seen at hourly resolution. What is counted is overnight gaps (with the registered 06:00-to-07:00 ask proxy). Every result says so.
4. **Cost screen before stage 2, at zero requests.** `poli2_count.py cost-screen <quote files>`: the median round trip for two-sided quotes with a mid of 20c to 80c in the 79 series; if above 5c the card is CLOSED on cost and stage 2 is never sent; at or under 5c the stage 2 request count goes to the Head for a go. **Deviation, stated: the lists answer cannot supply it.** Settled (finalized) markets in a lists answer carry yes_bid 0 and yes_ask 1 (checked on all 3,000 market objects of the CFRTI_K_LISTS sample), so they hold no spread. The politics recorder's quote files (`pol-data` `polrec/*/quotes.csv.gz`, list quotes up to 11 s old, which is good enough for a spread LEVEL) are the zero-request source.
5. **Universe note.** This registration's universe stays the 79 daily, weekly or monthly Politics series from the census. Desk B's withdrawn wording used the politics recorder's 61 markets. They are not merged. The cost screen below uses the 16 series the recorder shares with the 79 (the recorder holds 20 series; 4 are not daily, weekly or monthly).

6. **No 24 hour exit, no gap (Desk B's note, coded and tested).** A market that closes within 24 hours of the 07:00 ET entry has no 24 hour time exit, so it cannot be a gap: it is excluded and the number is reported (`gaps_excluded_no_24h_exit`). `count` therefore needs the stage 1 lists folder (the market's close time). The liquidity condition (200 contracts in the 7 days before 22:00 ET) is taken from candle volume up to the entry, as Desk B asks; the list's lifetime volume is only a pull limit. Eastern clock times use `zoneinfo America/New_York` (the UTC shift on Nov 1, 2026 is handled). Desk B's request to ride a POL-i1 count on the same candles (market-days with a 15c move) is noted; I will do nothing on it until the Head asks.

**RESULT of the cost screen (computed Nov 12, 17:59Z, quotes only, no result file opened, no outcome used; `polrec` runs of 2026-11-11 19:32Z, 2026-11-12 01:51Z and 09:35Z):** 196 two-sided quotes with a mid of 20c to 80c, 39 distinct markets, 16 series; **median spread 3.0c, median round trip 6.3c, above 5c: by the Head's rule POL-i2 is CLOSED on cost and stage 2 is never sent.** Per series medians run from 3.4c (KXHORMUZMAX) to 22.5c (KXSUEZWEEKLY); only 4 of 16 series sit at or under 5c. **Caveats the Head should weigh:** the sample is 39 markets in 3 half-hour runs over 22 hours (the recorder is landing about 3 of 88 runs); it covers 16 of the 79 series (the other 63 have no quote on file); a list quote can be up to 11 s old; and the round trip is the in-and-out cost, while the card exits at the bid after 24 hours. At a mid of 50c two fees alone are 3.5c, so any series with a spread of 2c or more fails.

## AMENDMENT 4 (Nov 12, 2026, before the pull; Head of R&D's ruling of 18:01Z): a politics cost snapshot decides whether POL-i2's settled lists are ever pulled

The cost screen of Amendment 3 rests on the SAME thin recorder sample Forensics used (39 markets, 16 of the 79 series, 3 runs in 22 hours), so it is not a second measurement and POL-i2 is not closed on it alone. 79 requests on settled lists are not spent for a count that most likely dies on cost.

1. **The POL-i2 settled-lists sub-job in the bundle is REPLACED by `POLCOST`**: for the same 79 daily, weekly or monthly Politics series, the OPEN markets list (`status=open`, the same `/markets` endpoint, one request a series plus paging, 79 requests, at most 237 pages), keeping bid, ask, sizes, last price, volume, open interest and close time. Request ids carry the prefix `pc_`. Zero-try measurement: an open market has no result; nothing is scored. `POLI2_LISTS.json` stays on the branch, out of the bundle, unsent.
2. **Rule, fixed now, before the pull** (`polcost.py table`): from POLCOST compute the median round trip (the whole spread plus two taker fees of 0.07 x mid x (1 - mid), Forensics' definition) for markets with a two-sided quote and a mid of 20c to 80c, overall and per series, with the count of markets and series behind it. **If the overall median is above 5c, POL-i2 is CLOSED on cost and its settled lists are never pulled. If it is at or under 5c, the settled lists go in a later run and the Head places them.**
3. **Limit, stated:** the snapshot is taken at about 00:00Z (7 PM Eastern), not at the 07:00 ET entry hour, and the quotes are list quotes up to about 11 seconds old (good enough for a spread level). A morning snapshot would be a second request and is asked for only if the evening one is within 1c of the line (the output flags it).
4. **Standing politics cost table:** the per-series output (series, markets quoted, median spread, median round trip at 20c to 80c, median size at the touch; `--csv` writes it) goes to Desk B and Forensics; POL-i1 and every other politics card cite it.
5. **Bundle numbers unchanged:** 137 requests, 355 pages, cap 369 (the POLCOST sub-job has the same request and page counts as the POL-i2 lists it replaces); same endpoint and series, only the status filter differs (`open` instead of `settled`, and no close-time bounds).
**Fallback if Main would rather not re-review tonight:** send the bundle as it was (with the settled lists) and the Head closes POL-i2 after those lists land by the same cost rule applied to the recorder sample.

## Request count (superseded by Amendment 1 above; kept as written)

(exact for stage 0; bounded for the rest, because the series count is not known)

| Stage | Job file | Requests | Basis |
|---|---|---|---|
| 0 | `kalshi_pull_jobs/POLI2_SERIES.json` | **1** (passes `--dry-run`) | `GET /series?category=Politics` |
| 1 | built by `poli2_count.py build-s1 <stage 0 folder>` | **2 x S** (one live and one `/historical` list per series), at most 6 x S with paging; cap 400 series so at most 800, at most 2,400 with paging | S = the number of Politics series, known after stage 0 |
| 2 | built by `build-s2 <stage 1 folder>` | **at most 600** (hard cap; markets over it are dropped lowest lifetime volume first and the number dropped is reported) | live markets packed in hourly batches, older ones one request each |

So: **1 request now; the total is 1 + 2S + (up to 600).** If S is 100 to 300 (my guess, unverified) the total is about 800 to 1,200 at the cap, which is above Desk B's guess of 300 to 600 (that guess assumed one list per series and no historical list). Worst case at the cap is two to three runs of the 1,200-request runner. I would ask Main to run stage 0 alone first (1 request, under a second) so S is exact before anything is placed in the dispatch order, and to drop the `/historical` list (halving stage 1) if you rule that the count may use only markets closing after 2026-09-12.

## Risks I cannot test without a request

- The `category` parameter of `/series` may not exist or be ignored; the answer would then be the whole series list, which can pass the runner's 5 MB per answer limit and be cut and marked truncated. My builder refuses a truncated or empty stage 0 and stops. I will not retry around it.
- The batched candles endpoint with `period_interval` 60 over a long market life is unproven for politics markets; the 9,000 (hours x tickers) packing follows the rule the other builders use.

## Files (all in `kalshi-scalper/workers/testing/` and `kalshi_pull_jobs/`)

`poli2_count.py` (build-s0, build-s1, build-s2, count; reads files, sends nothing), `test_poli2.py` (made-up data: universe filter, held-out drop, liquidity, price band, the proxy, halves, the cap, and each built job passes the runner's own `check_job`), `../kalshi_pull_jobs/POLI2_SERIES.json`. Owner field `MAIN` as for WXDAYEND_A (the runner has no Testing Desk entry). Score within the hour of each stage: `python3 kalshi-scalper/workers/testing/poli2_count.py count <stage 2 folder(s)>`.
