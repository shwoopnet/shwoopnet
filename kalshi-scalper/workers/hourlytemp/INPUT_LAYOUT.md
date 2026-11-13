# Hourly temperature measurement: the input layout a reader meets (no figures)

For a second build made from `HOURLYTEMP_MEASUREMENT_NOTE.md` only. Everything under `hourlytemp/fixture_inputs_MADE_UP_DATA/` is MADE UP (invented prices, invented rules text, an invented result string that no reader may use). Case names are neutral on purpose; no expected output is given here.

## A case

`case_NN/lists/` is shaped like the answers of the lists job (`desk_b_jobs/HOURLYTEMP_LISTS.json`); `case_NN/candles/`, where present, is shaped like the answers of the candle job. Cases 10 to 15 have lists only (they are for the step that builds the candle job).

## A run folder (both kinds)

- `manifest.json`: an object with `status` (`"complete"` when the run finished), `rows`, and, on a real run and on the candle folders here, `job` (the whole job file as run; `job.requests` is the list of requests, each with `id`, `path`, `params`).
- Each row of `rows`: `id` (the request's id), `page` (1, 2, 3 for a paged list), `status` (the HTTP status; 200 is an answer, anything else is a refusal or failure), `truncated` (true if the runner cut the body short; absent or false otherwise), `file` (the name of the gzipped JSON answer in the same folder, `0001.json.gz` and so on; null for a request with no stored answer).
- A request that was never sent has no row at all.

## A lists answer (`/markets`)

`{"markets": [ ... ], "cursor": ""}`. A non-empty `cursor` on the last page of an id means more pages existed. Request ids: `settled_<SERIES>` (settled markets of one series closing in the seven days, up to 3 pages of 1,000), `open_<SERIES>` (markets open at the pull, 1 page), `series_KXTEMPNYCHS` (one series object, not a market list).

A market object carries, among others: `ticker`, `event_ticker`, `strike_type`, `floor_strike`, `cap_strike` (on some types), `open_time` and `close_time` (ISO, UTC, ending in Z), `rules_primary`, `rules_secondary`, `yes_bid_size_fp`, `yes_ask_size_fp` (strings), and result and settlement fields. The series of a market is the part of its ticker before the first hyphen.

## A candle answer (`/markets/candlesticks`, batched)

`{"markets": [ {"market_ticker": "...", "candlesticks": [ ... ]}, ... ]}`. A candle: `end_period_ts` (epoch seconds, the END of the minute), `yes_bid` and `yes_ask` objects each with `close_dollars` (a string such as `"0.4800"`), `volume_fp` (a string). A minute in which nothing changed has no candle. A request's `params.market_tickers` is the comma-joined list of tickers it asked for, with `start_ts`, `end_ts` and `period_interval` 1.
