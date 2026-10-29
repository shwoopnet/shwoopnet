# Recorder spec R6: full-window book depth and trade tape on the five 15 minute markets the bot trades (2026-10-29, V2 worker REC5, document only)

This is a SPEC, not a recorder. Nothing here is a workflow or a script, and nothing was added under `scripts/` or `.github/`. Building it needs the owner's approval and its own pull request to `main`. It records public data only, holds no key, and changes nothing about the bot.

**Ledger check.** This is not a new idea. It is recorder R2 of `studies/RECORDER_SPECS_2026-10-29.md` (Bitcoin, Ethereum and gold, whole window), with two changes: it adds Dogecoin and XRP so all five live series are covered, and it uses Kalshi's batched order book read, which brings the request rate down to about a fifth of R2's. It replaces R2. It is not a strategy, so it spends no try.

## 1. The gap

Every maker or queue test on `KXGOLD15M`, `KXBTC15M`, `KXETH15M`, `KXDOGE15M` and `KXXRP15M` is blocked. Here is what exists today:

| Recorder | Markets | When | What |
|---|---|---|---|
| `scripts/record_quotes.py` (`record-quotes.yml`) | the five above plus Solana | last 150 s of each window | top of book only (best bid, ask and their sizes) about every 0.5 s, plus spot prices |
| `scripts/record_book.py` (`record-book.yml`) | `KXBTCD` hourly ladder only | 55 minutes before each hourly close | 5 levels a side every 3 s, plus the tape |

Nothing keeps depth, or the size ahead of a posted price, between 15 minutes and 150 seconds before a 15 minute close. MAKER4 was decided by fill bounds for exactly that reason (Q1 PF 0.00, Q0 PF 0.09 to 0.64, "the truth lies between Q1 and Q0 and depends on queue position, which is not on file"). MM1 is NOT_RUNNABLE for the middle of the window for the same reason. Gate B1 in `test/bookRecorderGates.test.js` forbids `record_book.py` from naming any 15 minute series, so R6 has to be a new script. Extending the book recorder would break that gate.

## 2. What to record

All endpoints are public, `https://external-api.kalshi.com/trade-api/v2`, plain GET, no key, no signing, no `/portfolio`, no order endpoint.

### 2a. Order book, 5 levels a side, every 2 seconds, the whole window

- **One request for all five markets:** `GET /markets/orderbooks?tickers=A&tickers=B&...`. This was measured today, without a key, from this sandbox: HTTP 200, about 0.16 s, about 11 KB for three tickers. It ignores `depth` and returns the full book, so the script keeps the best 5 YES bids and best 5 NO bids. The list is ordered worst price to best, best LAST, the same as `record_book.parse_levels`.
- **Fallback:** if the batched read fails 3 polls in a row (anything but 200, or a ticker missing from the answer), that window switches to the per-market read `GET /markets/{ticker}/orderbook?depth=5` (the one `record_book.py` uses). The switch is logged in coverage. A ticker missing from a batch answer gets no row for that poll. It never gets zeros.
- **One row per market per poll**, with columns `t_send_ms, t_recv_ms, server_date_header, ticker, series, close_time, yes_bid_px_1..5, yes_bid_sz_1..5, no_bid_px_1..5, no_bid_sz_1..5`. Prices and sizes are stored as the exchange returns them, as numbers, best first. A missing level is empty, never zero. This is the same column rule as `record_book.book_row`, plus a send time, so the round trip of each poll is known. The YES ask is 1 minus the best NO bid, and the size at the YES ask is that NO bid's size. Nothing is computed.
- **Windows:** every 15 minute window of all five series, from the window's open (900 s before its close) to its close. Each series has one live market at a time. The tickers are found at each window open with `GET /markets?series_ticker=S&status=open`, retried every 2 s for up to 30 s while the new market is not listed yet. Gold is recorded only while it trades (closed Friday 17:00 to Sunday 18:00 Central, plus the daily break). XRP is paused in the bot but still traded on Kalshi, so it is recorded anyway, because the research question does not depend on the bot trading it.

### 2b. Public trade tape, every trade of every window, de-duplicated by trade id

- **A closing sweep, not a live poll:** 60 s after each close, `GET /markets/trades?ticker=T&min_ts=<open>&max_ts=<close + 5 s>&limit=1000`, following `cursor` until it is empty, for each of the five markets. Why not a live poll every 15 to 30 s as `record_book.py` does: Bitcoin's 15 minute market had **46,744 trades** in one window today (13:15 to 13:30 ET) and 25,014 in a quiet one (02:45 to 03:00 ET). That is up to about 52 trades a second, so a 15 s read can reach the 1,000 row page limit, which is the truncation trap this project has hit four times. A sweep with a cursor after the close is complete by construction. The queue model needs the exchange's `created_time` (microsecond resolution), not the time we saw the trade.
- **De-duplication by trade id:** a set of every `trade_id` already written for the window is kept in memory. A repeated id, from page boundaries shifting or a retried page, is dropped and counted (`dupes_dropped`).
- **Row:** `ticker, created_time, yes_price_dollars, count_fp, taker_outcome_side`, as returned. **The trade id is used for de-duplication but not stored.** The ids are mostly random characters: measured on the book recorder's 18,115 stored trades, a row costs 26.5 bytes gzipped with the full id and 8.6 bytes without it. A 12 character id prefix would not de-duplicate safely, because the ids start with a time-ordered prefix (`0727...`), so prefixes collide. If the research session wants the ids kept, the cost is in section 3.
- **Completeness check:** after the sweep, one `GET /markets?tickers=a,b,c,d,e` reads each market's `result` and `volume_fp`. Coverage stores the sum of `count_fp` written next to `volume_fp`, so a short tape shows up as a number.

### 2c. Clock skew

- The server `Date` header (1 s resolution) is stored on every book row, as in `record_book.py`. The run's offset is the median of (Date + 0.5 s) minus the midpoint of `t_send_ms` and `t_recv_ms`. Q2B uses the same rule.
- `clock.csv`: the SNTP offset check that `record_quotes.py` already does (`t_local_ms, offset_ms`, blank when UDP is blocked), once an hour.
- Trades are compared on exchange time (`created_time`), book rows on corrected local time. Both are needed to decide whether a trade happened before or after a posted order was live.

### 2d. Coverage, one row per window per ticker

`close_time, ticker, polls, ok_polls, n429, batch_fallback (0/1), max_gap_ms (largest gap between consecutive ok polls), first_recv_ms, last_recv_ms, book_rows, tape_pages, tape_trades, dupes_dropped, tape_sum_count, volume_fp, result`. A row is written even for a window with zero ok polls, so a missed window is counted, not silent. Usable-window rules stay with each test's registration, as MM1S and Q2B already do.

## 3. Storage, measured from the files on `quote-data`

Measured on `origin/quote-data` (fetched 2026-10-29): the book recorder's first run (`book/2026-10-29/1026/`) has 12,369 book rows in 315,765 bytes gzipped (**25.5 B a row**) and 18,115 trades in 482,252 bytes (**26.5 B a trade** with the id, **8.6 B** re-encoded without it, measured). The whole branch is 22.0 MB today across 8 days of the quote recorder (about 2.6 to 4.1 MB a day) plus one book run.

Trades per window, measured today on the public tape (unique trade ids, all pages): Bitcoin 25,014 to 46,744; gold 6,986 to 8,494; Ethereum 7,771; XRP 3,957; Dogecoin 2,968. That is about 47,000 to 70,000 a window in US hours, less overnight. With 96 windows a day (gold about 92), the estimate is **about 4.5 million trades a day, range 3 to 7 million**. These are single-window samples and the recorder's coverage file will give the real figure.

| Part | Rows a day | Gzipped a day |
|---|---|---|
| Book, 5 levels, 2 s, whole window | 450 polls x (4 x 96 + 92) = 214,200 | **5.5 MB** |
| Tape, no stored id | about 4.5 M (3 to 7 M) | **39 MB** (26 to 60) |
| Coverage, clock | about 480 + 24 | under 0.1 MB |
| **Total** | | **about 45 MB a day (32 to 66)** |
| 14 days | | **about 630 MB (450 to 920)** |
| Tape WITH the full trade id, for comparison | | about 120 MB a day, 1.7 GB in 14 days: not recommended |

Each 4 hour job pushes about 7.5 MB in 3 to 4 gzipped files, well under GitHub's 100 MB file limit. Because the workflow fetches with `--depth 1`, the runner never downloads the branch's history. The branch itself grows, and 14 days takes it from 22 MB to about 650 MB. **Recommendation:** run R6 for 14 days, then stop it by deleting the workflow, unless the owner approves more after a first read. A book-only run (no tape) would be 5.5 MB a day, but it is not useful: a queue model needs the trades.

## 4. Branch

It writes to `quote-data` only, under its own folder `book15/<date>/<HHMM>/{book,trades,coverage,clock}.csv.gz`. It never writes to `main` and never publishes with the site (`_config.yml` excludes `.github` and `scripts`). It uses the same push loop as the other two recorders (3 tries with `pull --rebase`). Three recorders now push to one branch, but each writes only its own folder, so a rebase cannot conflict.

## 5. Public read rate

Per minute, from R6 alone:

| Stream | Calls a minute |
|---|---|
| Book: 1 batched call every 2 s | 30 |
| Discovery: 5 calls per window | 0.3 |
| Result and volume: 1 call per window | 0.07 |
| Tape sweep: about 50 to 75 pages per window (sum over the five markets), averaged | 3 to 5 |
| **Average** | **about 35 a minute (0.6 a second)** |
| Peak: the sweep minute after each close, pages paced 1.0 s apart on a second stream | about 95 a minute (1.6 a second) |
| Worst case: batched read refused, per-market fallback during a sweep | about 215 a minute (3.6 a second) |

It uses at most 2 request streams (book, and tape plus housekeeping), with at least 0.5 s between calls on each, as RULES.md asks. A 429 backs off for 2 s and the wait doubles up to 30 s. It is never asked again harder, and every refusal is counted in coverage.

**Against what is known to be safe:** Kalshi does not publish a limit for unauthenticated reads. It is not documented whether it is per address; the documented tiers (Basic about 20 reads a second) are per key, and R6 uses no key. The measured record: the book recorder's run made 12,369 polls at about 2.4 a second with **zero** 429s, and the quote recorder has made about 190,000 polls at about 2 a second with a 0.0% 429 share. R6's average is a quarter of what has run cleanly, and its peak is two thirds of it. If GitHub put all three recorders on one address, the combined peak would be about 384 a minute (6.4 a second). R6 adds 30 of those, because its sweep (the minute after a close) does not overlap the quote recorder's burst (the 150 s before it). R6 does not touch the account: no key, no secret, no `/portfolio`, no order, no write, and no relation to the bot's key or its rate budget, which lives in Cloud Functions.

## 6. GitHub Actions minutes

The same job shape as the other two: six 4 hour jobs a day, each starting 15 minutes before a boundary and stopping a minute after the next one, plus about 3 minutes for the last tape sweep and 2 minutes of setup. That is about 260 minutes a job, **about 1,560 minutes a day, about 47,000 a month**. On a public repository (this one is public), standard GitHub-hosted runners are free and not counted against a quota. On a private repository it would be about 23 times the free 2,000 minutes, and so would each existing recorder.

**Scheduling risk, observed:** scheduled starts run late or are dropped (the book recorder's 11:50 UTC job started at 17:33; the quote recorder's 03:45 and 07:45 jobs once never fired). **Recommendation:** trigger every 30 minutes (`cron: "5,35 * * * *"`) under a `concurrency` group with `cancel-in-progress: false`. GitHub keeps at most one pending run, so this adds no minutes: a run that finds the slot busy waits and starts when the running job ends. Each job stops at the cycle boundary (`cycle_stop_time`, as in both scripts), so a dropped trigger costs at most 30 minutes instead of 4 hours. A window belongs to the job that was running at its open. A job does not stop until it has finished the tape sweep of the last window it opened (boundary plus about 180 s), and the next job starts at that window's successor.

## 7. Tests the pull request must add (`test/book15RecorderGates.test.js`, mirroring B1 to B6 and Q1 to Q8)

- **FB1, it cannot trade or sign.** Leaving out docstrings and comments, the script names only `external-api.kalshi.com/trade-api/v2`. It has no `PRIVATE|SECRET|Authorization|ACCESS_KEY|SIGNATURE`, no POST, PUT or DELETE, and no `/portfolio`, `/orders`, `order_id` or `create_order` once `/orderbook` and `/orderbooks` are stripped (B1's rule). It names exactly the five series and no other (no `KXBTCD`, `KXSOL15M`). It imports nothing from `functions/`, and nothing in `functions/` or `index.html` mentions it.
- **FB2, the workflow pushes only the data branch.** The only secret is `GITHUB_TOKEN`. It does `git push -q origin quote-data` and never pushes `main`. It does `git add book15` and nothing wider. It has `permissions: contents: write` and nothing more, `cancel-in-progress: false`, `timeout-minutes: 330`, the checkout action pinned by commit SHA as in the other two, and no `pip install` beyond pinned standard tools.
- **FB3, not published.** `_config.yml` still excludes `.github` and `scripts`. `test/pagesPublishGates.test.js` still passes.
- **FB4, book rows mean what the reader thinks.** Given a fixture batched answer: rows are best first, a missing level is empty (never zero), a full book is cut to 5 levels a side, the Date header and the send and receive times are kept, a ticker missing from the batch gets no row, and a failed read gets no row.
- **FB5, the batched-read fallback.** 3 failed batches in a row switch that window to per-market reads and set `batch_fallback` in coverage. A good batch never triggers it.
- **FB6, tape de-duplication and completeness.** The same trade id on two pages is written once and counted in `dupes_dropped`. The sweep follows `cursor` until it is empty, so a 1,000 row page never ends the read (the truncation trap). `tape_sum_count` and `volume_fp` land in coverage. No `trade_id` column is written.
- **FB7, no gaps between jobs.** `cycle_stop_time` leaves a full cycle, as B5 does. A window belongs to exactly one job. The last sweep finishes before the job's stop.
- **FB8, rate budget.** A pure function computing calls a minute from the constants returns at most 40 on average and at most 100 at peak with the batched read. There are at most 2 request streams, at least 0.5 s between calls on a stream, a 429 waits at least 2 s and doubles, and a 429 is never answered by asking again at once.
- **FB9, coverage is written for a dead window.** A window with zero ok polls still gets a coverage row.
- The existing gates B1 to B6, Q1 to Q8 and `scan.js` (security audit, workflows section) must still pass unchanged.

## 8. What it unblocks

- **MM1, gold market making (registered 2026-10-29).** The middle of the window goes from NOT_RUNNABLE to runnable with a measured queue. The last-150-seconds part gains depth. Its gate is 300 independent gold closes: about 3.5 days at full coverage (about 88 gold windows a trading day), realistically 5 to 8 days given late jobs and weekends.
- **MAKER5, a MAKER test on the five (candidate, to be registered before any R6 row is read).** This is MAKER4's card (two-sided resting quotes, flat before the close) with the queue measured instead of bounded, on all five series. It must quote only from 12 to 7 minutes left and be flat before 6.7 minutes left, or skip any window L1 trades (MAKER4's correction), so it cannot hold a position at the same time as L1. Its gate is 300 independent closes: about 3.2 days at full coverage, likely 5 to 7.
- **A queue-model L1 entry test (candidate, call it L1Q1).** It asks how often L1's entry, resting at the bid (one tick better) instead of crossing to the ask at the 6 minute (or 10 minute) look, would have filled before the decision expires, and what the missed entries were worth. CLAUDE.md's registered prediction for maker entries applies: the fills that come are disproportionately the losers, so it must report both the PF of filled entries and what the misses would have made. REGIME1's spread-2c-or-more lead and the live `depthAtLimit` log both point at this question, and only R6 can answer it with a queue.
- **Also helped, not unblocked:** Q2B's adverse-selection measurement gets a 15 minute comparison set. RECORD1 is unaffected: it keeps the quote recorder's 0.5 s cadence and spot feeds, which R6 does not replace.

## 9. Summary for the owner

The bot trades five 15 minute markets (gold, Bitcoin, Ethereum, Dogecoin, XRP), and every test of resting orders on them is stuck. Nothing records how much is already waiting at each price, or every trade, across the whole 15 minutes. The quote recorder keeps only the last 150 seconds and only the best price. R6 would fill that gap. Every 2 seconds, for the whole window, it records the best 5 prices a side with their sizes for all five markets in one public request. After each close it reads every public trade of that window, with no duplicates. It also keeps the server's clock and a coverage count per window. It uses no key, places no order, never touches the account, and writes only to the `quote-data` branch (never `main`, never the website). It costs about **45 MB a day gzipped (about 630 MB over 14 days)**, about **35 public reads a minute on average (95 at peak)**, a quarter of what the existing recorders already run with zero refusals, and about 47,000 free GitHub Actions minutes a month. It would let MM1 (gold market making), a MAKER test on all five markets and a "rest L1's entry at the bid" test run on real queue data, each after about a week of recording. **The decision needed: approve building R6 as its own pull request (a new script, workflow and gate file FB1 to FB9, set to run for 14 days and then stop), or not.**
