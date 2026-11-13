# SOCDERIV measurement: input layout for a second build (Testing Desk, Nov 13, 2026). No figures, no expected outputs.

Everything under this folder is MADE UP: invented games, prices in whole cents, an invented `result` string that no reader may use. Cases are `case_01` to `case_12`. Each case holds `lists/` (a lists run) and `candles/` (a candle run). Read the registration at `claude/idea-desk-b` (SOCDERIV_REGISTRATION.md, last change ec98d614, which carries the one-way cost amendment of c998c45e: the cost line is one-way, 4c, the round trip is information only) and `SOCDERIV_MEASUREMENT.md` here. The leagues and their two groups come from the registration's frozen series file (`SOCDERIV_SERIES.json`). Only leagues of group A appear in these cases; all other leagues are listed with no markets.

## A run folder (both kinds)
- `manifest.json`: `{"job": <the job file as run>, "status": "complete", "rows": [...]}`. Each row: `index`, `id` (the request id), `page` (1), `status` (200 = an answer), `file` (`0001.json.gz` and so on, gzipped JSON, in the same folder). A request that was never sent has no row. In these cases every request that has an answer has status 200, no row is truncated, and every lists row has an empty `cursor`.
- `job.requests[i]` has `id`, `path`, `params`. In `lists/` the ids are `live_<SERIES>` (`/markets`, `status=settled`, window params) for the 64 league series; the three fee-field reads have no row. In `candles/` the ids are `c0000`... (`/markets/candlesticks`, `params.market_tickers` comma-joined, `start_ts`, `end_ts`, `period_interval` 1).

## A lists answer (`/markets`)
`{"markets": [ ... ], "cursor": ""}`. A market object carries: `ticker`, `event_ticker`, `open_time`, `close_time`, `occurrence_datetime`, `expected_expiration_time` (ISO, UTC, ending in Z), `volume_fp` (string), `title`, `strike_type`, `floor_strike` (a number, on the total-goals and team-total markets only), `result` (made up, never read). The series of a market is the part of its ticker before the first hyphen.

## How a game's legs are named
A game is one `GAMEKEY` shared by four series of its league `LG`: 
- winner: series `KX<LG>GAME`, three markets `KX<LG>GAME-<GAMEKEY>-AAA`, `-BBB` and `-TIE`; `event_ticker` is `KX<LG>GAME-<GAMEKEY>`; team codes are the last segment (`AAA` is the lower code);
- total goals: series `KX<LG>TOTAL`, markets `KX<LG>TOTAL-<GAMEKEY>-T0.5` to `-T4.5`, the strike in `floor_strike`;
- both teams to score: series `KX<LG>BTTS`, market `KX<LG>BTTS-<GAMEKEY>-YES`;
- team total: series `KX<LG>TEAMTOTAL`, markets `KX<LG>TEAMTOTAL-<GAMEKEY>-AAA2` and `-BBB2`, `floor_strike` 1.5 (the team is the code the last segment starts with).
`occurrence_datetime` is carried by every market of the game (the winner markets' value is the one the registration uses).

## A candle answer (`/markets/candlesticks`, batched)
`{"markets": [ {"market_ticker": "...", "candlesticks": [ ... ]}, ... ]}`. A candle: `end_period_ts` (epoch seconds, the END of the minute), `yes_bid` and `yes_ask` objects with `close_dollars` (a string such as `"0.4800"`), `volume_fp`. An empty side is written as Kalshi writes it: a bid of `"0.0000"` and/or an ask of `"1.0000"`. A minute for which no candle is stored has no row. Candles are given only for the minutes the made-up cases need; a game with no candles for a leg has none of its minutes for that leg.
