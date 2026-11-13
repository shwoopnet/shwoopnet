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
