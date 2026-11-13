# New-series census: plan and stage 1 job (Idea Desk C, Nov 13, 2026)

For the Head of R&D's 19:50Z request: every Kalshi series CREATED in the last 30 days, metadata only. No Kalshi request has been made; the job goes to the Head, Auditor B and then Main. [research]

## What the API allows (Kalshi's public API docs, read Nov 13 by a worker; documentation only)

- **The series object has no creation time.** Its only timestamp is `last_updated_ts`, and `GET /series` takes no created filter.
- **The event object has no creation or first-open time.**
- **Only markets carry `created_time`.** `GET /markets` takes `min_created_ts` and `max_created_ts`, but only with status `unopened` or `open` (or none), newest created first.

So a series' creation date has to be inferred: it is new if its EARLIEST event is recent.

## Stage 1 (job `jobs/NEWSERIES_LISTS.json`; passes the runner's `check_job`)

- **Requests:** two `/markets` lists, `status=open` and `status=unopened`, `min_created_ts` = 2026-10-14T00:00:00Z, `mve_filter=exclude` (no combos). 1,000 a page, at most 50 pages each, cap 110 requests, 1 a second. The real count is unknown: if a list hits 50 pages, the run stops cleanly and the census says it is truncated.
- **Kept:** ticker, event_ticker, series prefix, title, created_time, open_time, close_time.
- **Dropped unread:** every price, size and volume field.
- **No settled market and no result** is in any answer.
- **Output:** the set of series with at least one market created since Oct 14.

## Stage 2 (written after stage 1 lands; one job, named requests)

- **Which series:** those from stage 1 that are absent from both older lists:
  - the Nov 12 census series lists (`CENSUS_LISTING`);
  - V2's Nov 3 sweep files.
  A series absent from both is a candidate; one present in either is old.
- **Requests:** for each candidate, one `GET /events?series_ticker=S&limit=200` (no nested markets, so no market data and no result).
- **Test:**
  - the series is NEW if every returned event's `strike_date` is on or after 2026-10-14 and there is no further page;
  - it is OLD if any is earlier;
  - it is UNDECIDED if the page is full and all are recent (then one more page, named).
- **Budget:** about one request per candidate. If there are more than 300 candidates, stage 2 is split and the Head is asked first.

## Output, for each new series

- title, category, frequency, fee type and multiplier (from the series metadata, `GET /series?category=...` already pulled on Nov 12, or one request per category if absent);
- first event date;
- **coverage:** whether any card (registry, `HELDOUT_REGISTRY.md` Table 2) or recorder (watchlists and series lists in `scripts/` and `kalshi-scalper/workers/*WATCHLIST*`) names it;
- **mechanism:** whether a non-closed mechanism plausibly applies, judged against the declined list (7e) and the closed families.

Then the top 3 with reasons, and a card only if one passes the four checks.
