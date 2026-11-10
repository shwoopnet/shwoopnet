# R6 extension, gold only (backlog row 36): decision needed before 2026-11-13 23:59 UTC

## What it does now
`record-15m-book.yml` (cron 5,35 each hour, one concurrency group, 4 hour jobs) runs `scripts/record_15m_book.py` for five series:
KXGOLD15M, KXBTC15M, KXETH15M, KXDOGE15M, KXXRP15M. Every 2 s one batched public book read (best 5 YES and 5 NO), the full trade tape after each close, a coverage row per window per series, an hourly clock check. Pushes gzipped CSV to `quote-data` under `book15r6/`. No key, no order. It exits by itself from 2026-11-13 23:59 UTC.

## The edit (not applied)
New workflow file (copy of the old one) plus a copy of the script, so the five-market set and its gates FB1 to FB11 stay intact:
- Script: line 33 `SERIES = ("KXGOLD15M",)`; line 49 `END_UTC` to 2026-12-12T00:00:00Z (28 days after the old end); update the docstring lines 4 and 15.
- Workflow: change the date in the gate step (`date -u -d '2026-11-13T23:59:00Z'`) and the header comment; change the data path `book15r6` to a new name (e.g. `book15g`) in the 4 places (mkdir, script argument, gzip, git add); new `name:` and `concurrency.group`.
- Old workflow can stay (it stops itself) or be deleted. New gate file like `test/fifteenBookRecorderGates.test.js` for the one-series set and the new end date (the existing FB tests assert five series and the old date).

## Cost, estimated (spec figures scaled, not measured)
| | all five (now) | gold only |
|---|---|---|
| public reads a minute, average | about 35 (30 book + about 5 discovery, result, tape) | about 31 (the batched book read is one call whatever the count; only tape and discovery shrink, tape about 15 pages a window) |
| storage a day, gzipped | about 45 MB | about 9 to 12 MB |
| 28 days | n/a | about 250 to 340 MB |
Read rate barely falls; storage falls about 4/5. Actions minutes about the same as now.

## What it would unblock (statuses from IDEA_BACKLOG.md, Nov 10)
- Row 14 (thin-bid skip, gold): n 40 skips per half (80); about 4 to 6 weeks forward; needs gold bids 25c to 15c at entry. Gold only serves it. 28 days is borderline.
- Row 22 (debounced 25c exit, gold): n 40 exits; R6 holds about 16 gold exits so far, gold exits run roughly 2 to 3 a week of live fills, so 40 needs the full 28 days at best and probably more. Likely still data limited.
- Row 20 (OICORE book imbalance): OICORE is Bitcoin, so a gold-only file does NOT serve it; its forward read uses logged `bidSize` and `askSize` on live orders instead (40 per half, about 60 fills a week once registered, so about 3 weeks).
- Rows 24 and 38 and the maker replay are already CLOSED (FAIL) on Nov 10; they need nothing more.

## Recommendation
Approve a gold-only extension for 28 days, but only if the owner wants rows 14 and 22 pursued. It is cheap (about 300 MB, no new reads of note, data only) and only rows 14 and 22 depend on it. If neither is a priority, let R6 lapse on Nov 13; the closed rows lose nothing. Row 20 is unaffected either way. Either way, stop reading rows 14 and 22 before 40 events per half.
