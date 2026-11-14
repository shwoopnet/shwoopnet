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

## Amendment 3 (Nov 13, 2026, about 05:45Z, before any FOMCTEXT answer exists; Auditor B's finding, the Head's order)
The development events have MONTH-ONLY event tickers (KXFEDMENTION-26MAR), which the YYMONDD parser read as no date, so every row was treated as held out and dropped (fail closed, no leak, but no count). Now a month-only event ticker takes its decision date from a fixed map in the script, the eleven development months only: 25JAN 2025-01-29, 25MAR 2025-03-19, 25MAY 2025-05-07, 25JUN 2025-06-18, 25JUL 2025-07-30, 25SEP 2025-09-17, 25OCT 2025-10-29, 25DEC 2025-12-10, 26JAN 2026-01-28, 26MAR 2026-03-18, 26APR 2026-04-29. Checked against Idea Desk C's card (8851d822, lines 13 to 14, and Clarification 1, lines 107 to 108): the same eleven dates. A month-only ticker NOT in the map stays held out (25AUG, 26JUN and later can never be read through it). The held-out test still cuts on the date; the YYMONDD form is unchanged. Fixtures: a mapped month (kept and counted), an unmapped month and a held-out month (both dropped as held out).

## Dated line, 2026-11-14 ~01:25Z: the `events` command (the Head of R&D's order of 01:22Z; written before the code)
`events <events job.json> <events folder>...` reads a FOMCTEXT_EVENTS run (the /events lists of the four Fed mention series, with no nested markets) and prints ONLY event_ticker, series_ticker, title and date.
- **Proof first:** the run is read only through `answers()`. It must be whole against its committed job, complete, every request answered, no cursor left, sha256 and bytes matching, inside its folder, with no held-out path.
- **Date:**
  - from the event ticker by `date_of_event` (YYMONDD, or a month-only form in MONTH_ONLY);
  - only if that gives none, from the event's `strike_date` (its first 10 characters, YYYY-MM-DD), with date_source "strike_date";
  - neither gives a date: dropped, counted no_date.
- **Cut:** an event with a date on or after 2026-06-17 is dropped, counted held_out. That happens after only its ticker (and, when needed, strike_date) is read; its title is never read.
- **Also dropped:** a series not among the four Fed series (not_fed_series). Not restricted to the eleven development dates: the command exists to name events.
- **Output:** sorted by date then event ticker; drop counts go to stderr. No market, price, volume or result field exists in these answers (no nested markets) or is printed.
- **Made-up hand case (test_fomctext.py):**
  - one run with events KXFEDMENTION-25JAN29 (title "A"), KXPOWELLMENTION-26MAR (month-only, mapped), KXFEDMENTION-26JUN17 (held out), KXJPOWMENTION-XYZ with strike_date "2026-04-29T18:00:00Z" (no ticker date, so the strike_date is used), KXWARSHMENTION-ABC with no strike_date (no_date), and KXOTHER-25JAN29 (not_fed_series);
  - expected printed rows: KXFEDMENTION-25JAN29 dated 2025-01-29, KXPOWELLMENTION-26MAR dated its MONTH_ONLY date, KXJPOWMENTION-XYZ dated 2026-04-29 (source strike_date), sorted by date;
  - expected drops: held_out 1, no_date 1, not_fed_series 1;
  - a run whose embedded job differs from the given job is refused.
- **Addendum, 2026-11-14 ~01:30Z (before the code):** the reader's own `refuse_heldout` refuses only HELDOUT_-named paths, not the landed runs listed in HELDOUT_PULL_RUNS.md (now main's copy, sha256 974f2713..., PR 922). `answers()` therefore also calls `hm_guard.refuse_all([folder])` first, for every command.
  - Expected: a run folder whose name is a run listed in that file (the test uses LIVEDATA_PROBE_B's folder name from the list) is refused by every command.
  - Every other figure in the tests is unchanged.

## Dated line, 2026-11-14 ~01:40Z: the `type` column in count (card Clarification 7, the Head's ruling of 01:31Z, claude/idea-desk-c 20196129; Desk C's request); written before the code
- **load_table** reads a `type` column. Its value, stripped, must be exactly "statement-type" or "NOT STATEMENT-TYPE"; a missing column or any other value REFUSES the table. Every row, of either type, stays in the universe check, unchanged.
- **count:**
  - the kill-line arm is statement-type rows with statement_word yes;
  - the placebo is statement-type rows with statement_word no;
  - NOT STATEMENT-TYPE rows are in neither, printed as their own key `not_statement_type` = {"n": k, "line": "not statement-type, n = k"}, outside the verdict and the placebo;
  - `strikes_in_table` still counts every row.
- **build-candles and words:** unchanged (the frozen job da62610b asks for all 407).
- **Expected, by hand:**
  - **(1) every earlier test:** the test helper's tables gain type = "statement-type" for each old five-column row, and every earlier figure is unchanged (all their rows are statement-type);
  - **(2) the new made-up case:**
    - 9 strikes at one development meeting: 3 statement-type yes, 4 statement-type no, 2 NOT STATEMENT-TYPE (no);
    - expected statement_word_strikes 3, placebo strikes 4, not_statement_type n 2 with the line "not statement-type, n = 2", strikes_in_table 9;
    - the two NOT rows are still required by the universe check: a list missing one of them refuses;
  - **(3) refusals:** a table with no type column, and a table with type "statement" on one row.
- **For Desk C's real table** (claude/idea-desk-c ab6db60a, 493e6d6a..., 407 rows), the amended count prints 28, 367 and 12. That is checked only when the count runs, after Auditor B's CLEAN on the table, the job and this amendment, and the owner's yes.

## Amendment 4, 2026-11-14 ~02:30Z: the unit of a plain `close` (Auditor B, 02:27Z, after the structure check of FOMCTEXT_CANDLES 0147Z_43542605086; written before the code and before any count)
- On the landed historical candles, `yes_bid.close` and `yes_ask.close` are STRINGS of the form d.dddd on all 34,526 candles (Auditor B, shape only).
- `px()` now reads a plain `close` ONLY when it is a str matching ^\d\.\d{4}$, and takes float(...) as dollars.
- Any other form STOPS the reader, with a message that still contains "plain 'close'": a number (int or float), an integer string, or another pattern ("0.560", "56").
- `close_dollars` is read exactly as before. Everything else is byte-unchanged.
- **Expected by hand:**
  - a candle with yes_bid.close "0.5600" gives 0.56;
  - each of "56", 56, 0.56 (a float) and "0.560" stops;
  - close_dollars is unchanged;
  - every earlier test still passes (the old gate-6 case, {"close": 78}, still stops; 18, 1, 24; the type-column case 3, 4, 2).
- **Not added, noted for the record:** the pattern allows 0.0000 to 9.9999. It does not itself refuse a value above 1.0000. Auditor B's text did not ask for that bound.
- **Amendment 4 as approved by the Head of R&D (02:27Z); replaces the pattern above; written before the code:**
  - the pattern is ^[01]\.\d{4}$, so the leading digit is 0 or 1 and a value runs from 0.0000 to 1.9999 dollars;
  - px() returns float(...) in dollars;
  - two-sidedness is still decided by rule 18 in tally() (0 < bid < ask < 1, unchanged), so a value of 1.0000 or above, or of 0.0000, is never two-sided;
  - any other shape stops; close_dollars is as before.
  - **Expected, one row in each shape:**
    - "0.5600" reads 0.56;
    - "1.0000" reads 1.0, and as an ask is not two-sided;
    - "2.0000", "56", 56, 0.56 and "0.560" each stop.

## Amendment 5, 2026-11-14 ~02:50Z: the 1c and 2c haircut lines beside the RAW verdict (the Head of R&D, 02:35Z; card Clarification 8, claude/idea-desk-c 2bd8809c; written from that text and the card only, not from any other build's code; before the code and before any count)
- **The RAW verdict and every RAW field are byte-unchanged.**
- For each haircut h in {1c, 2c}, a strike of the kill arm (statement-type, feature yes) counts on that line when ALL hold:
  - two-sided at 14:05 ET at the RAW quote (0 < bid < ask < 1, as now);
  - settled YES (a NO, void or other result never counts);
  - entry = ask + h is at or under 0.87 (the card's cap, applied to the entry price);
  - 1 - entry is 10c or more (always true once the cap holds; kept as the card's wording).
- Prices are compared in whole ten-thousandths of a dollar (ask rounded to 4 places, h added as 100 or 200), so an entry of exactly 0.8700 counts and float noise cannot move a strike across the cap.
- The same CLOSE conditions are judged on each line: (a) fewer than 15 counted strikes; (b) from fewer than 5 meetings; (c) fewer than half of the kill arm two-sided at 14:05 ET. (c) is a quote fact and is the same number on every line.
- Each line prints "passes the haircut" when none holds, else "does not count: fails the haircut" with the conditions that hold.
- "could count toward the 20 to 30: yes" only when the RAW verdict is not CLOSED AND both haircut lines pass; otherwise "no".
- **Reading I took, flagged for the Head and Auditor B:** the lines apply to the kill arm only (not the placebo or the 12 NOT STATEMENT-TYPE rows); no fee and no exit haircut are applied (the card's C7 fee and bid-1c exit belong to a PF read; this stage is a count of entry prices, and the Head's text names the entry price only).
- **Expected by hand:**
  - **H1 (new):** 5 meetings x 3 kill-arm strikes, settled YES, two-sided, asks 0.85, 0.86, 0.87 (bid 2c under). RAW: 15 qualifying, 5 meetings, survives. 1c: entries 0.86, 0.87, 0.88, so 10 count, 5 meetings, fails (a). 2c: entries 0.87, 0.88, 0.89, so 5 count, 5 meetings, fails (a). Could count: no.
  - **Fixture 1 (existing, asks 0.80):** RAW 18, 6 meetings, survives. 1c and 2c: 18 count, 6 meetings, both pass. Could count: yes.
  - **Fixture 2 (existing, boundary):** RAW 1 qualifying (A87), CLOSED. 1c: A87's entry is 0.88, so 0 count, fails (a) and (b); 2c the same. Could count: no. Two-sided on every line: 2 of 6, so (c) does not hold on any line.
  - Every earlier test still passes unchanged.
- **Correction to the hand case above (2026-11-14, after the first test run, disclosed):** Fixture 2 has 3 of 6 two-sided, not 2 (A87, A88 and NOSETTLE at 0.20/0.22 are two-sided; the existing RAW test already pins 3). My hand line miscounted. The conclusion is unchanged: exactly half is not under half, so (c) holds on no line. The test asserts 3.
