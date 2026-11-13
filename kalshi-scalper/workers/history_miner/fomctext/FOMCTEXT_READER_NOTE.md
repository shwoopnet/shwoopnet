# FOMCTEXT stage 1 reader: what it is and what it is blind to (History Miner, Nov 13, 2026)

Built from Idea Desk C's card only (`claude/idea-desk-c`, `kalshi-scalper/workers/idea_desk_c/FOMCTEXT_CARD.md`, 8851d822) and its Clarification 1 (commit 28a2d63d, 02:25Z), which answers the reader's nine readings; the reader follows that text. Zero tries: a count with its CLOSE lines. Slow family, paper list at most. [research]

## What it does
- `build-candles <table.csv> <lists folder>...` reads the FOMCTEXT_LISTS answer and Desk C's hand-matched statement-word table, checks that every strike of every event the table names is in it (else it refuses), and writes the stage 2 candle job: one-minute candles, 13:55 to 14:45 US Eastern on each development decision date, one historical request per market listed by `/historical/markets`, batched requests (at most 9,000 minute-tickers, 100 tickers) for markets on the live list.
- `count <table.csv> --lists ... --candles ...` reads, for each statement-word strike, the candle ending 14:05 ET exactly, and counts the strikes with a two-sided quote (0 < bid < ask < 1) whose YES ask is at or under 87c and at least 10c under the settlement value (1 for yes, 0 for no), all with a 1e-9 tolerance. It prints the CLOSE lines: (a) under 15 such strikes, (b) from under 5 meetings, (c) under half of the statement-word strikes two-sided at 2:05 pm (exactly half does not close).
- It prints the same count for the NON-statement-word strikes of the same meetings as a placebo (Clarification 1, point 5); the placebo is never part of a CLOSE line. It lists development dates with no press-conference event in the table as "no market" (point 9).

## It READS SETTLEMENTS, by design
The measurement is a gap against settlement, so the reader joins each development strike's result. It is therefore NOT blind to outcomes on the development meetings: the count is selected on development and can close the card; it cannot support one. Everything it reports is labelled zero tries.

## What it is blind to
- **Held-out meetings:** any list row whose event ticker's date is a decision date on or after 2026-06-17 00:00 UTC is dropped on its event ticker alone, before its result or any other field is read; a table row naming such a date is refused; a folder named HELDOUT (any case) is refused.
- **Dates that are not development decision dates** (the Aug 22, 2025 notation vote, other speeches): dropped on the event ticker alone, counted.
- **The statement text:** it never matches words; Desk C's committed table decides which strikes are statement words, before any candle is read.
- **Any minute other than 14:05 ET** for the count (the job pulls 13:55 to 14:45 as the card says; the extra minutes are not read by `count`).
- **Partial pulls:** a manifest row that is not a whole HTTP 200 answer stops the reader (a refused request must not turn strikes into "no candle").

## Known limits, stated before data
- The `/historical` candle answer's price shape is not verified on a landed file; a plain `close` above 1.0 is read as cents (the same rule as scorekit). Checked on the first landed answer before `count` is run.
- A missing 14:05 candle is "not two-sided" with no carry-forward (Clarification 1, point 3). CANDLEGAP on CS2 found a missing candle meant an unchanged touch there, so this reading can understate two-sidedness and push toward CLOSE line (c).
- Matching events to meetings: the event ticker's date equals the decision date AND the title or rules text names the FOMC press conference (Clarification 1, point 1); Desk C's table names those events, the reader checks the table against the lists.

Files: `fomctext.py`, `test_fomctext.py` (three invented fixtures: a surviving set, a boundary set at 87c / 88c and exactly half two-sided, and the refusals).

## Amendment 1 (Nov 13, 2026, about 02:40Z, before any FOMCTEXT list or candle answer exists; Auditor B's NOT CLEAN on 13b73607)

All five defects fixed in the reader and the gate written down. No reading of the card changed.
1. A duplicate market_ticker in the table is refused.
2. Every development-date event in the lists that the table does NOT name is printed beside the count (count and tickers): the reader reads no title, so it cannot refuse, but a table that left an event out cannot hide.
3. Every file the reader opens must lie inside its run folder (abspath and realpath), and no path component may be a held-out name (any case).
4. A run folder is read only if PROVEN whole against its committed job file, passed on the command line: the manifest's embedded job equals it, the manifest status is "complete", every request has an answer for every page it took (a 429 followed by a good retry is fine; a final 404 is "no such market"), a list request's last page carries no cursor, and every stored file's sha256 and byte length match the manifest. Anything else stops the reader.
5. `build-candles` writes the whole job (endpoints, allowlists, max_requests, held-out line) and runs the pull runner's own `check_job` (scripts/kalshi_pull.py on main) on it before printing; the job goes to the Head by hash with its count before any run.
6. **Gate, written down:** a candle price's unit is decided by its FIELD NAME only. `close_dollars` is dollars; a plain `close` (the /historical shape, not yet seen on a landed answer) stops the reader. Once the first landed answer's shape is seen (shape only, no outcome read), the unit of a plain `close` is fixed by a dated amendment and a new hash for Auditor B, never by magnitude.
Usage is now `build-candles <table.csv> <lists job.json> <lists folder>...` and `count <table.csv> <lists job.json> <candles job.json> --lists ... --candles ...`.

## Amendment 2 (Nov 13, 2026, about 02:45Z, before any FOMCTEXT answer exists)
1. **404 (Auditor B):** a 404 is accepted as "no such market" ONLY on a `/historical/markets/<ticker>/candlesticks` request; a 404 on any other path (a list request above all) stops the reader. The count prints `candle_requests_answered_404`.
2. **`words` (the Head):** `words <lists job.json> <lists folder>...` prints, for development markets only, the market and event tickers, the decision date and the text fields known in advance (`title`, `subtitle`, `yes_sub_title`, `no_sub_title`, `custom_strike`, `rules_primary`, `rules_secondary`); NO price, volume or result field. Idea Desk C matches statement words from this print and never opens the lists run. The same whole-pull proof and held-out drop apply.
3. **Cursor:** confirmed covered since Amendment 1: a list request whose last 200 page carries a cursor stops the reader (tested).
