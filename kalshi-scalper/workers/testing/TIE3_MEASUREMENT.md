# TIE3 measurement: reader, job builders and scorer (Testing Desk build note, Nov 12, 2026)

**Status: BUILT AGAINST SYNTHETIC DATA ONLY. Not runnable on real data until Desk B's registration text and the frozen cells file exist.** Desk B writes the registration (card 18 in `CENSUS_CARDS_NOV12.md`, `claude/idea-desk-b` 439b3ba); the Head approved a ZERO-TRY measurement first. No Kalshi request, no data opened, no job sent to Main, no try added. No live account figure.

## What the code does (`tie3.py`, tests in `test_tie3.py`, 5 groups of checks, all pass on made-up data)

1. `build-lists <cells.json>`: one live list and one `/historical` list per cell series, closes bounded above by 2026-11-13T00:00Z minus 1 s. Requests: **2 per series** (about 25 if the listing confirms about 12 series; exact after the census listing names them).
2. `events`: groups each series' markets into events; an event is kept only if it has exactly 3 settled markets with exactly one `-TIE` market (others dropped and COUNTED); nothing closing on or after 2026-11-13T00:00Z is kept (counted). **Base block** (closes before 2026-10-20T00:00Z) keeps the Tie result as a level flag. **Price block** (2026-10-20 to 2026-11-12) keeps NO result field at all (a test asserts it).
3. `build-candles`: one-minute candles around each price-block event's instant, packed by time (3 hour span, minutes x tickers at most 9,000), live endpoint only (every price-block event closes after the 2026-09-12 cutover). Expected **80 to 150 requests** (about 24 days x 1 to 3 evening kickoff slots a day); exact once the lists are reported. Only after the Head's go.
4. `measure`: per league and period cell: base events, base rate and its standard error (base block only), priced games, share with a two-sided Tie quote, median and quartiles of (base rate minus Tie ask), median spread, counts first. Cell kill rule exactly as the card: under 150 base events or under 40 priced games is "no evidence"; CLOSED "efficient, move on" unless at least one cell has median gap 8c or more with spread 4c or less; CLOSED "nothing to buy" if under half the games have a two-sided quote in every measured cell. A Tie priced over its base rate closes the card (direction fixed). Output states `tries_added: 0`, `rule_scored: false`.

## The Head's conditions and where the code enforces them

- **Base rates only from settlements strictly before the bet's day:** the base block closes before 2026-10-20 and the price block starts at 2026-10-20, and the price block carries no result field, so the measurement cannot see a priced game's own outcome.
- **Prices only from minute-end candles at a stated instant, never a list quote:** the price is the ask close of the last candle ending at or before the instant and no older than 2 minutes; a missing, one-sided or crossed minute is counted, not filled. Label: candle freshness measured on KXBTC15M only (CANDLEVSBOOK1), assumed on these series.
- **Cutoffs are date constants** in code: `BASE_END`, `HELD_OUT_FROM`, `CUTOVER`.
- **Cells fixed before data:** the cells file's sha256 must equal `CELLS_SHA256`, which is `None` until Desk B freezes the file; with `None` the code refuses to build any job.
- **No rule scored, no try added** at this stage.

## Open items I put to Desk B (message sent 17:20Z)

The frozen series and cells file (league, period, series, Tie suffix, start rule); the pre-game instant rule (Kalshi has no start field; some tickers encode a local start time, NHL looked date-only; the code supports a ticker-local rule and a market-field rule and SKIPS-and-counts any event with no derivable start); the date constants as stated; the output format above; job names TIE3_LISTS and TIE3_CANDLES.

## Not yet decided by anyone

- Whether the instant is at least an hour before the start (so the Tie quote is pre-game and not stale) or later; it changes the candle windows only.
- The Head's declined-list ruling on the word "tie" (TIECOND1 row): Desk B asked for it before any pull.
