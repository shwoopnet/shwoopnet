# NHLOT price measurement: the text to build from, the input layout, and the names of the output fields (no values)

For a second build. Everything under `nhlot/fixture_inputs_MADE_UP_DATA/` is MADE UP (invented games, tickers and prices). Case names are neutral and no expected output is given here.

## The text

There is no separate note. The measurement is defined inside `IDEA_DESK_B_WAVE3.md`, in these sections, and where they differ the LATER one is right:

1. "Card 17. NHLOT: overtime resets a hockey game to a coin flip" (the idea, the first detection rule and the kill rules);
2. "Card 17, added Nov 12 after the Head of R&D's rulings": the paragraph "The price measurement is APPROVED" with its "Three details fixed now" and "Kill rules, unchanged" (these replace the card's 4c and 96c and its pre-game underdog);
3. the amendment inside that section dated Nov 12 at 17:30Z (the "game goes to overtime" market as a cross-check only);
4. "NHLOT: dated amendment, Nov 13, 2026, 00:09Z";
5. "NHLOT: second dated amendment, Nov 13, 2026, 00:10Z" (it replaces point 2 of the one before: one price, one chance);
6. "NHLOT: clarifying line, Nov 13, 2026, 00:16Z" (the 1e-9 tolerance and which side of each line an exact value falls);
7. "NHLOT: third dated amendment, Nov 13, 2026" (the second build's readings, taken into the text: the 45 candle minutes, the cross-check, the quartiles, the manifest).

## A case

`case_NN.tar.gz` (01 to 13) holds `case_NN/games.json` and `case_NN/candles/`. Unpack each archive into its own empty folder.

- `games.json`: a list with one object a game: `game` (a name), `ml` (the two moneyline tickers), `total` (the game's total-goals strike tickers), `close_ts` (epoch seconds: when the game market closed), `ot` (the ticker of the "game goes to overtime" market, for the cross-check only). On the real data this file is built from the settled lists by `nhlot/build_candles_job.py`; here it is given.
- `candles/`: shaped like a kalshi-pull run. `manifest.json` has `status`, `job` (with `requests`, each `{id, path, params}`; `params.market_tickers` is the comma-joined tickers asked for) and `rows` (`id`, `page`, `status`, `file`). Each answer file is gzipped JSON: `{"markets": [{"market_ticker": "...", "candlesticks": [...]}]}`.
- A candle: `end_period_ts` (epoch seconds, the END of the minute), `yes_bid` and `yes_ask` objects each with `close_dollars` (a string such as `"0.4400"`). **A side may be absent** (a market that shows only a bid or only an ask). A minute may have no candle.

## How my reader is called

`measure_prices.py <candle run folder> <games.json>`.

## The names of the output fields, in the order mine prints them (no values)

1. Games in the list; games with moneyline candles; detections, and their share of the games with moneyline candles.
2. The cross-check, twice (for games the rule detected, and for games it did not): how many times the overtime market says overtime, says no overtime, is undecided, has no quote.
3. The cheaper side's ask at the detection minute: median, quartiles, lowest; then how many detections are at or under 40c, 43c, 45c and 47c.
4. The detection minute, in minutes before the game market closed: median and range.
5. Detections in the first 5 minutes of the 45 minute window.
6. Then, only if there are 30 detections or more and the fire rate is inside its range: the share of detections that are "buyable" as the second amendment of Nov 13 defines it (the registered figure), and the older best-of-two-minutes share (information only).
7. The verdict line: not enough data; closed because the rule fires too rarely or too often; closed on the price share; or survives the price measurement.

Every line also carries the hindsight label of the second amendment.
