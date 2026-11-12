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
