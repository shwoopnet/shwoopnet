# Combo trade-tape recorder (Nov 13, 2026, the owner: "Yes, nonstop recorder")

Research data only. Nothing here trades, signs or holds a key. It exists for Idea Desk C's CROWDLEG and NOTAKER cards (both paper only): CROWDLEG counts the combo trades whose taker bought YES on combos that share one leg; NOTAKER follows each combo trade whose taker bought NO. Both need EVERY combo trade, with each combo's legs.

**Why a separate, nonstop job.** A trial read of the public trade tape for one past half hour (CROWDLEG_TAPE_TRIAL, Sunday 2026-09-20 18:00 to 18:30 UTC) filled its 50 page cap: at least 50,000 trades in the half hour, at least 9,334 of them combos (18.7%), all lower bounds. The tape comes newest first and cannot be filtered to combos, so a 30 minute poll would only ever read the newest part of its window. Read every minute, the same tape is a few pages.

**What it records.** Every minute, one cycle:
1. reads `GET /markets/trades?min_ts=&max_ts=&limit=1000` (no ticker, cursor followed and percent-encoded) from the start of the last good cycle, minus 15 seconds of overlap, to now, at most 10 pages;
2. keeps only combo rows (a ticker of the safe shape `^KXMVE[A-Z0-9._-]{1,120}$`, matched end to end), each `trade_id` once a job, in `trades.csv` (`t_recv_ms, ticker, created_time, yes_price_dollars, count_fp, taker_outcome_side, trade_id`, as the exchange returns them);
3. looks up the legs of combos it sees for the first time in this job with `/markets?tickers=` (40 a request, at most 2 requests a cycle, never more than 10 requests in the cycle in all) into `legs.csv` (`t_recv_ms, ticker, event_ticker, legs, leg_tickers`, legs as `market_ticker:side` joined by `|`, capped at 600 characters); a combo the answer does not return is missing, never guessed; combos not yet asked wait for the next cycle;
4. writes a coverage row: `cycle, min_ts, max_ts, pages, complete, capped, n429, tape_rows, combo_rows, dup_dropped, new_combos, lookups, legs_found, legs_missing, queue_len, requests, t_start_ms, t_end_ms`.

**How to read it.**
- A cycle is **complete** when the cursor ran out.
- It is **capped** when it read 10 pages with a cursor left. The oldest trades of its window are then lost, and the window counts only as a lower bound.
- A cycle cut by a failed read or three refusals in a row is neither. It moves nothing, so the next cycle reads that window again.
- Windows overlap on purpose, within a job and between jobs. A reader de-duplicates by `trade_id` across all files.
- Each job writes `mark.txt` (the start of its last good cycle) after every cycle. The next job starts its tape there (digits only, at most 2 hours back, 5 minutes when unknown), so a gap between jobs is read unless it is longer than 2 hours.
- `end.txt` gives the combos whose legs were still unknown when the job ended.
- Every CROWDLEG or NOTAKER result states:
  - the share of polls or cycles that were capped or cut;
  - the share of traded combos dropped for want of legs.

**Where it goes.** Gzipped CSV on its own `combotape-data` branch under `tape/DATE/HHMM/`, pushed with the built-in token (six tries). Never main, never `combo-data` or any other data branch, never published with the site.

**Safety.**
- Public GET endpoints under `/markets` only, on one host. No key, no secret, no auth header, no POST, no order or account path, no Firestore.
- A plain User-Agent. Redirects are refused.
- One request stream, at least 6 seconds between calls. A 429 waits 5 seconds, doubling up to 60.

**Stated plainly.**

| | |
|---|---|
| Cadence | one cycle a minute, in 4 hour jobs back to back (triggered every 15 minutes under one concurrency group that never cancels a running job) |
| Requests per minute | never more than 10 (the 6 second gap); about 3 to 5 expected at the trial's rate (about 3 tape pages and up to 2 legs look-ups) |
| Requests per day | at most 14,400; about 4,300 to 7,200 expected |
| MB per day (gzipped) | an ESTIMATE: at least about 450,000 combo trades a day at the trial's lower bound, about 110 bytes a row raw, so about 50 MB raw and about 10 MB gzipped, plus a few MB of legs; about 800 MB over the whole run on its own branch (re-measure from the first files) |
| Runner minutes | continuous: about 1,440 a day, about 43,000 a month, free on a public repo, far over the Charter's 250 a month guideline; the owner approved it ("Yes, nonstop recorder", Nov 13, 2026) |
| Ends | 2027-01-31 23:59 UTC by itself (workflow and script); sooner by deleting `.github/workflows/record-combo-tape.yml` |

**Held-out line.** The CROWDLEG and NOTAKER forward windows are:
- development: the first 21 days of this recorder's rows;
- held-out: the next 21 days, read once on the Head of R&D's go.

The exact dates are written as a dated amendment to both cards the day the first rows land, before any row is read. No one reads a held-out row for price, side, size or result before then; coverage counts may be checked.

**Gates.** `test/comboTapeRecorderGates.test.js` CT1 to CT9. CT1 checks the code against a hand case written and committed before the code (`test/fixtures/comboTapeHandCase.json`).
