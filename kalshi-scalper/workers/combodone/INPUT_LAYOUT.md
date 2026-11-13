# COMBODONE stage 1 counter: the input layout and the names of the output fields (no values)

For a second build made from Idea Desk C's card only (`idea_desk_c/COMBODONE_CARD.md` at commit 593597e6 on `claude/idea-desk-c`, with Amendments 1 and 2). Everything under `combodone/fixture_inputs_MADE_UP_DATA/` is MADE UP: invented tickers, prices, times and leg results. Case names are neutral on purpose and no expected output is given here.

## The cases

`case_01.tar.gz` to `case_13.tar.gz`, one archive a case (a case is about 1,000 small files). Unpack each into its own empty folder; an archive holds only paths under `case_NN/`. Inside: `case_NN/combo/` (shaped like the `combo` folder of the `combo-data` branch) and `case_NN/legs/` (shaped like a kalshi-pull run of the leg pull).

## `combo/`: what the recorder writes (scripts/record_combo.py on main)

`combo/<YYYY-MM-DD>/<run folder>/` with `coverage.csv.gz`, `quotes.csv.gz`, `books.csv.gz` (and, on the real branch, `trades.csv.gz` and sometimes `results.csv.gz`, which this count does not use). The day folder is the UTC date the run started. The run folder is `HHMM` here; on the real branch it may carry more after the time, so treat it as an opaque name. Each file is a gzipped CSV with a header row; a file may hold the header only.

- `coverage.csv`: one row a run. Columns: `t_recv_ms, listed, pages, list_complete, selected, quote_rows, books, trades_read, requests, n429, stopped_early`. Used: `stopped_early` (0 or 1), `list_complete` (0 or 1).
- `quotes.csv`: one row a combo. Columns: `t_send_ms, t_recv_ms, server_date_header, ticker, event_ticker, exchange_index, open_time, close_time, yes_bid, yes_ask, no_bid, no_ask, yes_bid_size, yes_ask_size, last_price, volume, open_interest, legs, leg_tickers`. Used: `t_recv_ms` (epoch milliseconds; the receive time t), `ticker`, `close_time` (ISO, UTC), `yes_ask` and `yes_ask_size` (strings of dollars and contracts, possibly empty), `legs` (the true number of legs), `leg_tickers`.
- `leg_tickers`: the legs as `ticker:side` joined by `|`, side `yes` or `no`; a leg may appear with no `:side`. Empty on rows past the first 100 of a run. A string longer than 600 characters is cut at a whole leg and ends in `|...`.
- `books.csv`: one row a combo for the first 40 of a run. Columns: `t_recv_ms, server_date_header, ticker, close_time`, then `yes_bid_px_1..5`, `yes_bid_sz_1..5`, `no_bid_px_1..5`, `no_bid_sz_1..5` (best first; a missing level is empty, never zero). Used: `ticker`, `no_bid_px_1`, `no_bid_sz_1`.

## `legs/`: the leg pull (a kalshi-pull run folder)

- `manifest.json`: `status` (`"complete"` when the run finished), `job` (the job file as run; `job.requests` is a list of `{id, path, params}`, with `params.tickers` a comma-joined list of up to 100 leg tickers), and `rows`. A row: `id`, `page`, `status` (HTTP status; 200 is an answer), `truncated` (true if the runner cut the body; absent or false otherwise), `file` (the gzipped JSON answer in the same folder, or null).
- An answer: `{"markets": [ ... ], "cursor": ""}`. A market: `ticker`, `status`, `result` (`yes`, `no`, another word such as `scalar`, or empty), `settlement_ts` (ISO, UTC, or null). A ticker that was asked for may be absent from the answer.

## How my counter is called

`combodone.py week <combo dir>`, `combodone.py legs-job <combo dir> <out dir>`, `combodone.py count <combo dir> <legs run>`. The cases are for `count` (and `week`). Yours may be shaped differently.

## The names of the output fields, in the order mine prints them (no values)

1. Per UTC day: completed runs (of 48 scheduled).
2. Either "no full week yet" (then nothing more is printed), or the week: first day, last day, completed runs of 336 and the percentage, run folders not completed, completed runs whose combo list was whole (`list_complete`).
3. Quote rows in the week; unreadable rows left out (no receive time or no ticker); rows whose leg string is whole, and that share of all rows; empty strings; cut strings.
4. Rows with a whole leg string that are not eligible, by reason: leg unknown; a leg settled with a result other than yes or no; a leg already settled against the combo; no leg settled for the combo 60 seconds or more before; every leg settled; combo closed.
5. Eligible snapshots; with a resting ask; with none.
6. Independent combos (a still-open leg set on a UTC day); with a resting ask; with none; distinct still-open leg sets over the week; of those, with a resting ask.
7. Per day of the week: independent combos; with a resting ask.
8. The median ask (cents, two places).
9. The book figure: eligible snapshots also in that run's books file; of those, passing the book test; independent combos by that test.
10. The verdict line: CLOSED (with the count), SURVIVES THE COUNT (with the count), "the leg pull is not whole: not decided", or a refusal when the leg run is not this week's.
