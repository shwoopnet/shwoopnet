# RECBOOK2: order book recorder for the Ethereum and gold hourly ladders (discovery infrastructure, N +0)

Branch `claude/v2-recorder-book2`, head `a6140dd` (pushed, nothing merged). Research only: public GETs, no key, no order, no live code, no promote verb.

## What changed (all new files plus one test)
- `scripts/record_book2.py`: a copy of `record_book.py` for `KXETHD` and `KXGOLDH` (`KXSOLD` only with `--series`). Writes `book2/` on `quote-data` with a leading `series` column on book, trades and coverage. Cadence 5 s (not 3 s); trade tape every 30 s as now. `record_book.py` and the `book/` files are untouched.
- `.github/workflows/record-book2.yml`: same six 4 hour jobs (cron `50 3,7,11,15,19,23`), own concurrency group, built-in token, pushes `quote-data` only.
- `kalshi-scalper/src/scalper/book_series.py`: `iter_polls(series)`, `iter_trades(series)` read `book/` (series from the ticker) and `book2/` from the history of `origin/quote-data` and yield `Poll(series, close, strike, t, yes_px, yes_sz, no_px, no_sz, ticker)`. `makertail1.py` is not edited (its `git log -- book/` pathspec does not match `book2/`).
- Discovery changed vs the BTC copy: the event is asked for by name (`KXETHD-26NOV0317`, close hour in US Eastern, DST handled), series list as fallback. Reason, seen live today: `GET /markets?series_ticker=KXETHD&status=open` returned 0 markets while the 17:00 ET event had 40 active ones.
- Tests: `kalshi-scalper/tests/test_book_series.py` (API faked) and gate `B7` in `test/bookRecorderGates.test.js` (B1 to B6 unchanged and passing). Live smoke: 1 minute on KXETHD gave 81 of 84 polls (3 HTTP 429), rows have the new schema.

## Series
- KXETHD: hourly ladder, 40 to 300 strikes, 22 of 40 strikes two sided at 21:15Z, event volume about 25k contracts (BTC about 208k). Recorded.
- KXGOLDH: hourly ladder, 58 strikes, event volume about 7k (16:00 ET event). No event at 17:00 ET (gold's daily break) and none at weekends, so about 16 closes a day on average. The recorder logs "no markets" and goes on. Recorded.
- KXSOLD: 75 strikes, 42 two sided, volume about 5k. Thin, so off by default; `--series KXETHD,KXGOLDH,KXSOLD` turns it on (adds 1.4 requests a second).

## Maker fee flag (COUNT)
`GET /series/{ticker}` for KXBTCD, KXETHD, KXGOLDH, KXSOLD: all four say `fee_type: "quadratic"`, `fee_multiplier: 1`. Same as Bitcoin, the series MAKERTAIL1 assumed zero maker fee on. The public market objects carry no fee or maker field, so this is the only flag; "quadratic" (not a maker fee variant) is what supports zero, but the API does not state a maker rate, so it is read from the fee_type name, not measured. A fill in the first live week is the check.

## Cadence and cost
- Requests: one loop over all picked strikes every 5 s: ETH 7 strikes = 1.4 requests/s, gold the same (2.8/s together, BTC's recorder does 2.3/s alone, and runs on its own runner). About 4,600 book polls per series-hour, about 130k requests a day for ETH, about 100k for gold (fewer closes), plus the tape (0.5/s). One 429 in 28 polls seen; the code sleeps 2 s on a 429 and the coverage file counts them.
- Three series at 3 s would be 7 requests/s from one runner: not done. If coverage shows many 429s, drop to `--series KXETHD` or raise `BOOK_EVERY_S`.
- Actions: 6 jobs a day of about 250 minutes, about 1,500 runner minutes a day (same as record-book). The repo is public, so standard runner minutes are not billed.
- Data: about 40 to 80 MB gzipped per 14 days on `quote-data`.

## How to turn off
Delete `.github/workflows/record-book2.yml` on main. `book2/` stays on the branch.

## What main must do
Merge the branch (the workflow checks out the script from main, so nothing records until it is merged; `record-book.yml` stays as is). Then run `workflow_dispatch` once. First check, two days later: `count` of orders per close and fills per day on ETH and gold from `book_series.py` (coverage.csv `n429` and `ok_polls`).

## Days to 150 fills per side (MAKERTAIL1 rate: BTC about 36 fills a day, about 1.5 per close, about 18 a side)
These are scenarios, not measurements; the real rate comes from the first two days of data.
- Bitcoin alone: about 8 to 9 days per side (the registered plan reads on 2026-11-12).
- Ethereum, same fills per close as Bitcoin (24 closes, tails fill when spot moves through the strike, which needs volatility, not volume): about 36 a day, 18 a side, **about 8 days**. If fills scale with tape volume (12% of Bitcoin): about 2 a side a day, **about 70 days**.
- Gold, same per close as Bitcoin (about 16 closes a day): about 24 a day, 12 a side, **about 13 days**. Volume scaled (3.5%): under 1 a side a day, **over 150 days**, not testable.
- Pooling Bitcoin, Ethereum and gold roughly halves the time under the parity case; under the volume case Ethereum adds little and gold nothing. Gold's side claim is the one most likely to be unreachable; treat gold as a replication of the Bitcoin result, not an independent side test, unless the first two days show at least 5 fills a day.
